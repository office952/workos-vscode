import type { IntakeV4FinishSetup } from "./intakeV4Api";
import type { IntakeV4ArtworkFinish } from "./intakeV4ArtworkFinish";
import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";
import {
  calculateLedModulesForAreaLitBoxes,
  calculateLedStripLengthByArea,
  type LedAreaLitBox,
} from "./sharedLedLightingDensity";
import {
  computeIntakeV4LedLoadWatts,
  computeIntakeV4LedModuleCount,
  DEFAULT_INTAKE_V4_LED_STRIP_POWER_W_PER_ML,
  normalizeIntakeV4LedModuleWattage,
  proposeIntakeV4PsuConfiguration,
} from "./intakeV4LedLighting";
import { normalizeEmblemLightingMode } from "./intakeV4BackingMode";
import { readLetterPerimeterMFromSources } from "./intakeV4QuoteGeometry";
import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import type { IntakeV4QuoteGeometry } from "./intakeV4QuoteGeometry";

export { readLetterPerimeterMFromSources };

export interface IntakeV4EmblemLightingGeometry {
  areaM2?: number | null;
  boxes?: LedAreaLitBox[] | null;
  depthMm?: number | null;
}

function round3(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function positiveNumber(value: number | null | undefined): number | null {
  return value != null && Number.isFinite(value) && value > 0 ? value : null;
}

function maxDepth(values: Array<number | null | undefined>): number | null {
  const depths = values
    .map(positiveNumber)
    .filter((value): value is number => value != null);
  return depths.length > 0 ? Math.max(...depths) : null;
}

export function resolveIntakeV4EmblemLightingDepthMm(args: {
  finish: IntakeV4FinishSetup;
  artworkFinishes?: IntakeV4ArtworkFinish[] | null;
  letterGroups?: IntakeV4LetterGroupFinish[] | null;
  fallbackDepthMm?: number | null;
}): number | null {
  const artworkDepth = maxDepth((args.artworkFinishes ?? []).map((row) => row.return_depth_mm));
  if (artworkDepth != null) return artworkDepth;

  const letterDepth = maxDepth((args.letterGroups ?? []).map((group) => group.return_depth_mm));
  if (letterDepth != null) return letterDepth;

  return (
    positiveNumber(args.finish.return_depth_mm) ??
    positiveNumber(args.fallbackDepthMm) ??
    null
  );
}

export function applyIntakeV4ArtworkDepthsToLedBoxes(
  boxes: LedAreaLitBox[] | null | undefined,
  artworkFinishes: IntakeV4ArtworkFinish[] | null | undefined,
  fallbackDepthMm: number | null | undefined,
): LedAreaLitBox[] {
  const depthByKey = new Map<string, number>();
  for (const row of artworkFinishes ?? []) {
    const depth = positiveNumber(row.return_depth_mm);
    if (depth == null) continue;
    if (row.layer_key) depthByKey.set(row.layer_key, depth);
    if (row.layer_name) depthByKey.set(row.layer_name, depth);
  }
  const fallbackDepth = positiveNumber(fallbackDepthMm);
  return (boxes ?? []).map((box) => {
    const keyedBox = box as LedAreaLitBox & {
      layer_key?: string | null;
      layer_name?: string | null;
    };
    const layerDepth =
      (keyedBox.layer_key ? depthByKey.get(keyedBox.layer_key) : undefined) ??
      (keyedBox.layer_name ? depthByKey.get(keyedBox.layer_name) : undefined);
    return {
      ...box,
      depth_mm: layerDepth ?? positiveNumber(box.depth_mm) ?? fallbackDepth,
    };
  });
}

function normalizeEmblemGeometry(
  input: IntakeV4EmblemLightingGeometry | number | null | undefined,
  form: IntakeV4FinishSetup,
): Required<IntakeV4EmblemLightingGeometry> {
  if (typeof input === "number") {
    return {
      areaM2: input,
      boxes: [],
      depthMm: form.return_depth_mm ?? null,
    };
  }
  return {
    areaM2: input?.areaM2 ?? null,
    boxes: input?.boxes ?? [],
    depthMm: input?.depthMm ?? form.return_depth_mm ?? null,
  };
}

export function syncIntakeV4FinishLightingForLayerState(args: {
  finish: IntakeV4FinishSetup;
  letterPerimeterM: number | null;
  emblemAreaM2?: number | null;
  artworkBoxes?: LedAreaLitBox[] | null;
  letterGroups?: IntakeV4LetterGroupFinish[] | null;
  artworkFinishes?: IntakeV4ArtworkFinish[] | null;
  fallbackDepthMm?: number | null;
}): IntakeV4FinishSetup {
  const depthMm = resolveIntakeV4EmblemLightingDepthMm({
    finish: args.finish,
    artworkFinishes: args.artworkFinishes,
    letterGroups: args.letterGroups,
    fallbackDepthMm: args.fallbackDepthMm,
  });
  return syncIntakeV4FinishLighting(args.finish, args.letterPerimeterM, {
    areaM2: args.emblemAreaM2 ?? null,
    boxes: applyIntakeV4ArtworkDepthsToLedBoxes(
      args.artworkBoxes,
      args.artworkFinishes,
      depthMm,
    ),
    depthMm,
  });
}

/** Sync LED watts + PSU proposal from geometry - mirrors V2 `syncLightingPlanning` at job level. */
export function syncIntakeV4FinishLighting(
  form: IntakeV4FinishSetup,
  letterPerimeterM: number | null,
  emblemGeometryInput?: IntakeV4EmblemLightingGeometry | number | null,
): IntakeV4FinishSetup {
  if (form.illuminated === false) {
    return {
      ...form,
      letter_led_module_count: null,
      emblem_led_module_count: null,
      total_led_module_count: null,
      led_module_count: null,
      letter_led_strip_length_m: null,
      emblem_led_strip_length_m: null,
      total_led_strip_length_m: null,
      estimated_led_watts: null,
      required_psu_watts: null,
      psu_configuration: [],
      psu_allocation_status: null,
      selected_psu_watts: null,
    };
  }

  const lightingSystemType = form.lighting_system_type ?? "led_modules";
  const isLedStrip = lightingSystemType === "led_strip";
  const modulePowerW = normalizeIntakeV4LedModuleWattage(form.led_module_power_w);
  const stripPowerWPerMl =
    typeof form.led_strip_power_w_per_ml === "number" && Number.isFinite(form.led_strip_power_w_per_ml)
      ? form.led_strip_power_w_per_ml
      : DEFAULT_INTAKE_V4_LED_STRIP_POWER_W_PER_ML;
  const emblemMode = normalizeEmblemLightingMode(form.emblem_lighting_mode);
  const emblemGeometry = normalizeEmblemGeometry(emblemGeometryInput, form);

  if (isLedStrip) {
    const letterStripLengthM =
      letterPerimeterM != null && Number.isFinite(letterPerimeterM) && letterPerimeterM > 0
        ? round3(letterPerimeterM)
        : null;
    const emblemStripLengthM =
      emblemMode === "area_lit"
        ? calculateLedStripLengthByArea(emblemGeometry.areaM2)
        : emblemMode === "excluded"
          ? 0
          : null;
    const totalStripLengthM =
      letterStripLengthM != null || emblemStripLengthM != null
        ? round3((letterStripLengthM ?? 0) + (emblemStripLengthM ?? 0))
        : null;
    const totalLedWatts = computeIntakeV4LedLoadWatts({
      letterPerimeterM,
      modulePowerW,
      lightingSystemType,
      ledStripLengthM: totalStripLengthM,
      ledStripPowerWPerMl: stripPowerWPerMl,
    });

    if (totalLedWatts <= 0) {
      return {
        ...form,
        lighting_system_type: lightingSystemType,
        led_module_power_w: modulePowerW,
        led_strip_power_w_per_ml: stripPowerWPerMl,
        letter_led_module_count: null,
        emblem_led_module_count: null,
        led_module_count: null,
        total_led_module_count: null,
        letter_led_strip_length_m: letterStripLengthM,
        emblem_led_strip_length_m: emblemStripLengthM,
        total_led_strip_length_m: totalStripLengthM,
        estimated_led_watts: null,
        required_psu_watts: null,
        psu_configuration: [],
        psu_allocation_status: "manual_review",
        selected_psu_watts: null,
      };
    }

    const psu = proposeIntakeV4PsuConfiguration(totalLedWatts);
    return {
      ...form,
      lighting_system_type: lightingSystemType,
      led_module_power_w: modulePowerW,
      led_strip_power_w_per_ml: stripPowerWPerMl,
      letter_led_module_count: null,
      emblem_led_module_count: null,
      led_module_count: null,
      total_led_module_count: null,
      letter_led_strip_length_m: letterStripLengthM,
      emblem_led_strip_length_m: emblemStripLengthM,
      total_led_strip_length_m: totalStripLengthM,
      estimated_led_watts: totalLedWatts,
      required_psu_watts: psu.requiredPsuWatts,
      psu_configuration: psu.psuConfiguration,
      psu_allocation_status: psu.psuAllocationStatus,
      selected_psu_watts: psu.psuConfiguration.length > 0 ? Math.max(...psu.psuConfiguration) : null,
    };
  }

  const letterModuleCount = computeIntakeV4LedModuleCount(letterPerimeterM);
  const emblemModuleCount =
    emblemMode === "area_lit"
      ? calculateLedModulesForAreaLitBoxes(
          emblemGeometry.boxes,
          emblemGeometry.areaM2,
          emblemGeometry.depthMm,
        )
      : emblemMode === "excluded"
        ? 0
        : null;

  let totalModuleCount: number | null = null;
  if (letterModuleCount != null) {
    totalModuleCount = letterModuleCount + (emblemModuleCount ?? 0);
  }

  const totalLedWatts =
    totalModuleCount != null && totalModuleCount > 0
      ? Math.round(totalModuleCount * modulePowerW * 100) / 100
      : computeIntakeV4LedLoadWatts({
          letterPerimeterM,
          modulePowerW,
          lightingSystemType,
        });

  if (totalLedWatts <= 0) {
    return {
      ...form,
      lighting_system_type: lightingSystemType,
      led_module_power_w: modulePowerW,
      led_strip_power_w_per_ml: stripPowerWPerMl,
      letter_led_module_count: letterModuleCount,
      emblem_led_module_count: emblemModuleCount,
      led_module_count: totalModuleCount ?? letterModuleCount,
      total_led_module_count: totalModuleCount ?? letterModuleCount,
      letter_led_strip_length_m: null,
      emblem_led_strip_length_m: null,
      total_led_strip_length_m: null,
      estimated_led_watts: null,
      required_psu_watts: null,
      psu_configuration: [],
      psu_allocation_status: "manual_review",
      selected_psu_watts: null,
    };
  }

  const psu = proposeIntakeV4PsuConfiguration(totalLedWatts);
  const selectedPsuWatts =
    typeof form.selected_psu_watts === "number" && Number.isFinite(form.selected_psu_watts)
      ? form.selected_psu_watts
      : psu.psuConfiguration.length > 0
        ? Math.max(...psu.psuConfiguration)
        : null;

  return {
    ...form,
    lighting_system_type: lightingSystemType,
    led_module_power_w: modulePowerW,
    led_strip_power_w_per_ml: stripPowerWPerMl,
    letter_led_module_count: letterModuleCount,
    emblem_led_module_count: emblemModuleCount,
    led_module_count: totalModuleCount ?? letterModuleCount,
    total_led_module_count: totalModuleCount ?? letterModuleCount,
    letter_led_strip_length_m: null,
    emblem_led_strip_length_m: null,
    total_led_strip_length_m: null,
    estimated_led_watts: totalLedWatts,
    required_psu_watts: psu.requiredPsuWatts,
    psu_configuration: psu.psuConfiguration,
    psu_allocation_status: psu.psuAllocationStatus,
    selected_psu_watts: selectedPsuWatts,
  };
}

export function resolveLetterPerimeterForFinish(
  pathGeometry: Record<string, unknown> | undefined,
  quoteGeometry: IntakeV4QuoteGeometry | null,
  analyzerReport: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): number | null {
  return readLetterPerimeterMFromSources(
    pathGeometry,
    quoteGeometry,
    analyzerReport,
    confirmation,
  );
}
