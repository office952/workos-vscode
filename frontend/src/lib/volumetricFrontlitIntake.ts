/**
 * TPL-VOLUMETRIC-LETTERS — front-lit production rules (intake UI + PSU sizing + spec sync).
 * Warm/cold light color does not affect costing — metadata only.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { VOLUMETRIC_PSU_WATTAGE_OPTIONS } from "@/lib/volumetricQuoteInput";
import { computeLedModuleCountFromPerimeter } from "@/lib/volumetricQuoteInput";
import {
  clearIlluminationLedFields,
  isIntakeIlluminationDisabled,
} from "@/lib/volumetricIntakeSelectors";

const PSU_OPTIONS = VOLUMETRIC_PSU_WATTAGE_OPTIONS;

/** Canonical lighting system values (spec contract). */
export type CanonicalLightingSystemType = "led_modules" | "led_strip";
/** Legacy UI value — normalized to led_modules on save. */
export type LegacyLightingSystemType = "led_module";
export type LightingSystemType = CanonicalLightingSystemType | LegacyLightingSystemType;

export type LedModulePowerW = 0.72 | 1 | 1.44;
export type CanonicalStripDensity = "60_led_per_m" | "120_led_per_m";
export type LegacyStripDensity = "60_5w" | "120_10w";
export type LedStripDensity = CanonicalStripDensity | LegacyStripDensity;

export type LightColor = "warm" | "cold";
export type LegacyLightColor = "cool";
export type ReturnColor = "white" | "black";

export type PsuSizingStatus = "ok" | "pending_geometry" | "insufficient_capacity";

export const PSU_HEADROOM_RATIO = 0.15;
export const MAX_PSU_WATTS = PSU_OPTIONS[PSU_OPTIONS.length - 1];

export const LIGHTING_SYSTEM_OPTIONS: { value: CanonicalLightingSystemType; label: string }[] = [
  { value: "led_modules", label: "Module LED" },
  { value: "led_strip", label: "Bandă LED" },
];

export const LED_MODULE_POWER_OPTIONS: { value: LedModulePowerW; label: string }[] = [
  { value: 0.72, label: "0,72 W / modul" },
  { value: 1, label: "1 W / modul" },
  { value: 1.44, label: "1,44 W / modul" },
];

export const LED_STRIP_DENSITY_OPTIONS: { value: CanonicalStripDensity; label: string }[] = [
  { value: "60_led_per_m", label: "60 LED / m — 5 W/ml" },
  { value: "120_led_per_m", label: "120 LED / m — 10 W/ml" },
];

export const LIGHT_COLOR_OPTIONS: { value: LightColor; label: string }[] = [
  { value: "warm", label: "Lumină caldă" },
  { value: "cold", label: "Lumină rece" },
];

export const RETURN_COLOR_OPTIONS: { value: ReturnColor; label: string }[] = [
  { value: "white", label: "Cant aluminiu alb (stoc)" },
  { value: "black", label: "Cant aluminiu negru (stoc)" },
];

const WRAPPED_FACE_TYPES = new Set([
  "oracal_651",
  "oracal_8500",
  "printed_vinyl",
  "printed_laminated_vinyl",
]);

export interface PsuSizingResult {
  totalLedWatts: number;
  requiredPsuWatts: number;
  selectedPsuWatts: (typeof PSU_OPTIONS)[number] | undefined;
  status: PsuSizingStatus;
  warning?: string;
}

function roundWatts(n: number): number {
  return Math.round(n * 100) / 100;
}

export function normalizeLightingSystemType(
  value: string | undefined
): CanonicalLightingSystemType | undefined {
  if (value === "led_modules" || value === "led_module") return "led_modules";
  if (value === "led_strip") return "led_strip";
  return undefined;
}

export function normalizeStripDensity(
  value: string | undefined
): CanonicalStripDensity | undefined {
  if (value === "60_led_per_m" || value === "60_5w") return "60_led_per_m";
  if (value === "120_led_per_m" || value === "120_10w") return "120_led_per_m";
  return undefined;
}

export function stripDensityToWattsPerMl(density: CanonicalStripDensity | undefined): 5 | 10 {
  return density === "120_led_per_m" ? 10 : 5;
}

export function normalizeLightColor(value: string | undefined): LightColor | undefined {
  if (value === "warm") return "warm";
  if (value === "cold" || value === "cool") return "cold";
  return undefined;
}

/** Fața se colantează — canonical boolean. */
export function isFaceVinylEnabled(spec: IntakeProductSpec | null | undefined): boolean {
  if (!spec) return false;
  if (typeof spec.face_vinyl_enabled === "boolean") return spec.face_vinyl_enabled;
  if (typeof spec.face_wrap_enabled === "boolean") return spec.face_wrap_enabled;
  const face = spec.face_finish_type;
  return face != null && WRAPPED_FACE_TYPES.has(face);
}

/** @deprecated use isFaceVinylEnabled */
export const isFaceWrapEnabled = isFaceVinylEnabled;

export function resolveReturnColor(spec: IntakeProductSpec): ReturnColor {
  return spec.return_color ?? spec.return_edge_color ?? "white";
}

export function resolveLedModulePowerW(spec: IntakeProductSpec): LedModulePowerW {
  return (spec.led_module_power_w ?? spec.led_module_wattage ?? 1.44) as LedModulePowerW;
}

export function computeLedLoadWatts(spec: IntakeProductSpec): number {
  const perimeter = spec.letter_perimeter_m ?? 0;
  if (!Number.isFinite(perimeter) || perimeter <= 0) return 0;

  const system = normalizeLightingSystemType(spec.lighting_system_type);
  if (system === "led_strip") {
    const density = normalizeStripDensity(spec.led_strip_density);
    const wPerMl = spec.led_strip_power_w_per_ml ?? stripDensityToWattsPerMl(density);
    return perimeter * wPerMl;
  }

  const moduleCount = computeLedModuleCountFromPerimeter(perimeter);
  return moduleCount * resolveLedModulePowerW(spec);
}

/** Smallest PSU >= load * (1 + headroom). Undefined if none large enough. */
export function selectPsuWattsWithHeadroom(
  loadWatts: number,
  headroomRatio = PSU_HEADROOM_RATIO
): (typeof PSU_OPTIONS)[number] | undefined {
  if (!Number.isFinite(loadWatts) || loadWatts <= 0) return undefined;
  const required = loadWatts * (1 + headroomRatio);
  for (const psu of PSU_OPTIONS) {
    if (psu >= required) return psu;
  }
  return undefined;
}

export function computePsuSizing(spec: IntakeProductSpec): PsuSizingResult {
  const total = computeLedLoadWatts(spec);
  if (total <= 0) {
    return {
      totalLedWatts: 0,
      requiredPsuWatts: 0,
      selectedPsuWatts: undefined,
      status: "pending_geometry",
      warning:
        "Necesită calcul după estimarea cantității LED (perimetru litere).",
    };
  }

  const required = roundWatts(total * (1 + PSU_HEADROOM_RATIO));
  const selected = selectPsuWattsWithHeadroom(total);

  if (selected == null) {
    return {
      totalLedWatts: roundWatts(total),
      requiredPsuWatts: required,
      selectedPsuWatts: undefined,
      status: "insufficient_capacity",
      warning: `Consum LED ${roundWatts(total)} W necesită sursă ≥ ${required} W — maxim configurat ${MAX_PSU_WATTS} W. Contactează owner/operator.`,
    };
  }

  return {
    totalLedWatts: roundWatts(total),
    requiredPsuWatts: required,
    selectedPsuWatts: selected,
    status: "ok",
  };
}

/** Sync canonical + legacy fields and enforce owner production rules. */
export function applyFrontlitConstructionDefaults(
  spec: IntakeProductSpec
): IntakeProductSpec {
  if (isIntakeIlluminationDisabled(spec)) {
    const vinylEnabled = isFaceVinylEnabled(spec);
    const returnColor = resolveReturnColor(spec);
    const cleared = clearIlluminationLedFields(spec);
    return {
      ...cleared,
      visual_chamfer_included: true,
      face_miter_chamfer: true,
      volume_finish: cleared.volume_finish ?? "none",
      face_vinyl_enabled: vinylEnabled,
      face_wrap_enabled: vinylEnabled,
      return_color: returnColor,
      return_edge_color: returnColor,
      paint_tube_count: undefined,
    };
  }

  const vinylEnabled = isFaceVinylEnabled(spec);
  const returnColor = resolveReturnColor(spec);
  const system =
    normalizeLightingSystemType(spec.lighting_system_type) ?? "led_modules";
  const stripDensity =
    normalizeStripDensity(spec.led_strip_density) ?? "60_led_per_m";
  const modulePower = resolveLedModulePowerW(spec);
  const lightColor = normalizeLightColor(spec.light_color ?? spec.led_color_temperature) ?? "warm";

  const depth =
    spec.return_depth_mm != null && spec.return_depth_mm > 0
      ? spec.return_depth_mm
      : spec.depth_mm != null && spec.depth_mm > 0
        ? spec.depth_mm
        : undefined;

  const next: IntakeProductSpec = {
    ...spec,
    visual_chamfer_included: true,
    face_miter_chamfer: true,
    illumination_family: "front_lit",
    illumination_type: "frontlit",
    volume_finish: "none",
    face_vinyl_enabled: vinylEnabled,
    face_wrap_enabled: vinylEnabled,
    return_color: returnColor,
    return_edge_color: returnColor,
    lighting_system_type: system,
    led_module_power_w: modulePower,
    led_module_wattage: modulePower,
    led_strip_density: stripDensity,
    led_strip_power_w_per_ml: stripDensityToWattsPerMl(stripDensity),
    light_color: lightColor,
    led_color_temperature: lightColor === "cold" ? "cool" : "warm",
    paint_tube_count: undefined,
  };

  if (depth != null) {
    next.return_depth_mm = depth;
    next.depth_mm = depth;
  }

  if (!vinylEnabled) {
    next.face_finish_type = "none";
  }

  const psu = computePsuSizing(next);
  next.total_led_watts = psu.totalLedWatts > 0 ? psu.totalLedWatts : undefined;
  next.required_psu_watts = psu.requiredPsuWatts > 0 ? psu.requiredPsuWatts : undefined;
  next.psu_sizing_status = psu.status;
  next.psu_sizing_warning = psu.warning;

  if (psu.status === "ok" && psu.selectedPsuWatts != null) {
    const minRequired = psu.requiredPsuWatts;
    if (
      next.selected_psu_watts == null ||
      next.selected_psu_watts < minRequired - 0.01
    ) {
      next.selected_psu_watts = psu.selectedPsuWatts;
    }
  } else if (psu.status === "insufficient_capacity") {
    if (
      next.selected_psu_watts != null &&
      next.selected_psu_watts < psu.requiredPsuWatts - 0.01
    ) {
      next.selected_psu_watts = undefined;
    }
  }

  const v2Cfg = spec.psu_configuration;
  if (
    spec.psu_allocation_status === "ok" &&
    Array.isArray(v2Cfg) &&
    v2Cfg.length > 0
  ) {
    const totalCapacity =
      spec.psu_total_capacity_watts != null && spec.psu_total_capacity_watts > 0
        ? spec.psu_total_capacity_watts
        : v2Cfg.reduce((sum, w) => sum + w, 0);
    const required =
      spec.required_psu_watts != null && spec.required_psu_watts > 0
        ? spec.required_psu_watts
        : next.required_psu_watts ?? psu.requiredPsuWatts;
    next.psu_configuration = [...v2Cfg];
    next.psu_allocation_status = spec.psu_allocation_status;
    next.psu_total_capacity_watts = totalCapacity;
    if (required != null && totalCapacity >= required - 0.01) {
      next.psu_sizing_status = "ok";
      next.psu_sizing_warning = undefined;
      const maxUnit = Math.max(...v2Cfg);
      if ((PSU_OPTIONS as readonly number[]).includes(maxUnit)) {
        next.selected_psu_watts = maxUnit as (typeof PSU_OPTIONS)[number];
      }
    }
  }

  return syncFaceVinylLegacyColorFields(next);
}

/** Mirror V2 face_vinyl_code into legacy face_vinyl_color_code for QuoteWizard / CostEngine. */
export function syncFaceVinylLegacyColorFields(
  spec: IntakeProductSpec
): IntakeProductSpec {
  if (!isFaceVinylEnabled(spec)) return spec;
  const next = { ...spec };
  const code = next.face_vinyl_code?.trim();
  const series = next.face_vinyl_series;
  if (code && !next.face_vinyl_color_code?.trim()) {
    if (series === "651" || series === "8500") {
      next.face_vinyl_color_code = `${series}-${code}`;
    } else {
      next.face_vinyl_color_code = code;
    }
  }
  if (next.face_vinyl_name?.trim() && !next.face_vinyl_color_name?.trim()) {
    next.face_vinyl_color_name = next.face_vinyl_name.trim();
  }
  return next;
}

export function shouldShowFaceFinishSection(
  spec: IntakeProductSpec | null | undefined
): boolean {
  return isFaceVinylEnabled(spec);
}

export function shouldShowPaintSection(): boolean {
  return false;
}

/** Classic single PSU or V2 multi-PSU planning satisfies simulate readiness. */
export function hasValidPsuSelection(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  if (spec.selected_psu_watts != null) return true;
  const status = spec.psu_allocation_status;
  const cfg = spec.psu_configuration;
  return status === "ok" && Array.isArray(cfg) && cfg.length > 0;
}

/** Readiness / quote-prep missing items for front-lit production rules. */
export function collectFrontlitIntakeMissing(
  spec: IntakeProductSpec | null | undefined,
  mode: "simulate" | "final" = "simulate"
): string[] {
  const s = applyFrontlitConstructionDefaults(spec ?? {});
  if (isIntakeIlluminationDisabled(s)) {
    return [];
  }
  const missing: string[] = [];

  const push = (condition: boolean, msg: string) => {
    if (condition && !missing.includes(msg)) missing.push(msg);
  };

  if (!normalizeLightingSystemType(s.lighting_system_type)) {
    push(true, "Sistem iluminare — selectează module LED sau bandă LED");
  }

  const system = normalizeLightingSystemType(s.lighting_system_type);
  if (system === "led_modules") {
    push(
      s.led_module_power_w == null && s.led_module_wattage == null,
      "Putere modul LED (0,72 / 1 / 1,44 W)"
    );
  }
  if (system === "led_strip") {
    push(
      normalizeStripDensity(s.led_strip_density) == null,
      "Densitate bandă LED (60 sau 120 LED/m)"
    );
  }

  push(
    normalizeLightColor(s.light_color ?? s.led_color_temperature) == null,
    "Temperatură culoare LED (caldu/rece)"
  );

  push(s.return_color == null && s.return_edge_color == null, "Culoare cant aluminiu (alb/negru)");

  if (s.psu_sizing_status === "pending_geometry") {
    push(true, "Dimensionare sursă LED — necesită perimetru litere");
  } else if (s.psu_sizing_status === "insufficient_capacity") {
    push(true, s.psu_sizing_warning ?? "Sursă LED insuficientă — decizie owner necesară");
  } else {
    push(!hasValidPsuSelection(s), "Putere sursă LED (W)");
  }

  if (isFaceVinylEnabled(s)) {
    const face = s.face_finish_type;
    if (face === "oracal_651" || face === "oracal_8500" || face == null || face === "none") {
      if (mode === "final" && (face === "oracal_651" || face === "oracal_8500")) {
        push(!s.face_vinyl_color_code?.trim(), "Cod culoare folie Oracal");
        push(
          s.face_vinyl_roll_width_mm !== 1000 && s.face_vinyl_roll_width_mm !== 1260,
          "Lățime rolă Oracal (1000 / 1260 mm)"
        );
      }
      if (mode === "simulate" && vinylEnabledNeedsType(s)) {
        push(true, "Tip colantare față (Oracal / print)");
      }
    }
    if (face === "printed_laminated_vinyl" && mode === "final") {
      push(!s.face_vinyl_color_code?.trim(), "Detalii colantare față (print+laminare)");
    }
  }

  return missing;
}

function vinylEnabledNeedsType(spec: IntakeProductSpec): boolean {
  if (!isFaceVinylEnabled(spec)) return false;
  const face = spec.face_finish_type;
  return face == null || face === "none";
}
