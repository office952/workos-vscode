import { allocatePSUCombination, computeRequiredPsuWatts } from "@/lib/psuAllocation";
import { normalizeLightingSystemType, stripDensityToWattsPerMl, normalizeStripDensity } from "@/lib/volumetricFrontlitIntake";

/** V4 material preview pitch — matches backend MATERIAL_BREAKDOWN_LED_PITCH_MM (250 mm). */
export const INTAKE_V4_LED_PITCH_MM = 250;

/** PSU reserve for Intake V4 previews — matches backend DEFAULT_RESERVE_PERCENT (30%). */
export const INTAKE_V4_PSU_RESERVE_RATIO = 0.3;

export const DEFAULT_INTAKE_V4_LED_MODULE_WATTAGE = 0.75;
export const DEFAULT_INTAKE_V4_LED_STRIP_POWER_W_PER_ML = 5;

export const INTAKE_V4_LED_MODULE_WATTAGE_OPTIONS = [
  { value: 0.75, label: "0.75 W / modul" },
  { value: 1, label: "1.00 W / modul" },
  { value: 1.44, label: "1.44 W / modul" },
] as const;

export type IntakeV4LedModuleWattage = (typeof INTAKE_V4_LED_MODULE_WATTAGE_OPTIONS)[number]["value"];

export function normalizeIntakeV4LedModuleWattage(value: number | null | undefined): IntakeV4LedModuleWattage {
  if (value == null || !Number.isFinite(value) || value <= 0) {
    return DEFAULT_INTAKE_V4_LED_MODULE_WATTAGE;
  }
  for (const option of INTAKE_V4_LED_MODULE_WATTAGE_OPTIONS) {
    if (Math.abs(value - option.value) < 0.02) {
      return option.value;
    }
  }
  if (Math.abs(value - 0.72) < 0.02) {
    return 0.75;
  }
  return DEFAULT_INTAKE_V4_LED_MODULE_WATTAGE;
}

export function computeIntakeV4LedModuleCount(letterPerimeterM: number | null | undefined): number | null {
  if (letterPerimeterM == null || !Number.isFinite(letterPerimeterM) || letterPerimeterM <= 0) {
    return null;
  }
  return Math.ceil((letterPerimeterM * 1000) / INTAKE_V4_LED_PITCH_MM);
}

export function computeIntakeV4LedLoadWatts(args: {
  letterPerimeterM: number | null | undefined;
  modulePowerW: number;
  lightingSystemType?: string | null;
  ledStripDensity?: string | null;
  ledStripPowerWPerMl?: number | null;
  ledStripLengthM?: number | null;
}): number {
  const system = normalizeLightingSystemType(args.lightingSystemType ?? "led_modules");
  if (system === "led_strip") {
    const lengthM = args.ledStripLengthM ?? args.letterPerimeterM ?? 0;
    if (!Number.isFinite(lengthM) || lengthM <= 0) return 0;
    const density = normalizeStripDensity(args.ledStripDensity ?? undefined);
    const wPerMl = args.ledStripPowerWPerMl ?? stripDensityToWattsPerMl(density);
    return Math.round(lengthM * wPerMl * 100) / 100;
  }

  const perimeter = args.letterPerimeterM ?? 0;
  if (!Number.isFinite(perimeter) || perimeter <= 0) return 0;
  const moduleCount = computeIntakeV4LedModuleCount(perimeter);
  if (!moduleCount) return 0;
  const power = normalizeIntakeV4LedModuleWattage(args.modulePowerW);
  return Math.round(moduleCount * power * 100) / 100;
}

export function proposeIntakeV4PsuConfiguration(totalLedWatts: number): {
  requiredPsuWatts: number;
  psuConfiguration: number[];
  psuAllocationStatus: string;
} {
  if (totalLedWatts <= 0) {
    return { requiredPsuWatts: 0, psuConfiguration: [], psuAllocationStatus: "manual_review" };
  }
  const required = computeRequiredPsuWatts(totalLedWatts, INTAKE_V4_PSU_RESERVE_RATIO);
  const allocation = allocatePSUCombination(required);
  return {
    requiredPsuWatts: required,
    psuConfiguration: allocation?.configuration ?? [],
    psuAllocationStatus: allocation?.status ?? "impossible",
  };
}
