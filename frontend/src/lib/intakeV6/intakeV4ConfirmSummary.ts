import type {
  IntakeV4FinishSetup,
  IntakeV4MaterialBreakdownResponse,
  IntakeV4NestingPreviewResponse,
} from "./intakeV4Api";
import { syncIntakeV4FinishLightingForLayerState } from "./intakeV4FinishLighting";
import {
  backingModeLabel,
  normalizeEmblemLightingMode,
  normalizeIntakeV4BackingMode,
} from "./intakeV4BackingMode";
import type { IntakeV4QuoteGeometry } from "./intakeV4QuoteGeometry";
import { readQuoteGeometryFromPayload } from "./intakeV4QuoteGeometry";
import { SVG_ARTWORK_EXECUTION_OPTIONS } from "@/lib/svgArtworkContracts";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { formatIntakeV6ReturnFinishLabel as formatIntakeV4ReturnFinishLabel } from "./intakeV6ReturnFinishOptions";
import {
  buildIntakeV4EdgeCantLayerBreakdown,
  buildIntakeV4EdgeCantViewModel,
  normalizeIntakeV4EdgeCantGroupsToTotal,
  resolveIntakeV4EffectiveReturnPerimeterM,
  type IntakeV4EdgeCantGroupedRow,
} from "./intakeV4EdgeCantDisplay";

export interface IntakeV4ConfirmSummaryViewModel {
  structure: {
    layerCount: number;
    childPartsCount: number | null;
    realLettersCount: number | null;
    artworkCount: number | null;
    innerHolesCount: number | null;
  };
  finish: {
    letterFaceLabel: string;
    letterReturnLabel: string;
    letterRows: Array<{
      groupKey: string;
      layerName: string;
      faceLabel: string;
      faceRollWidthMm: number | null;
      returnLabel: string;
      returnDepthMm: number | null;
      perimeterM: number | null;
    }>;
    artworkRows: Array<{
      layerKey: string;
      layerName: string;
      executionLabel: string;
      printTransparencyLabel: string;
      returnLabel: string;
      returnDepthMm: number | null;
      areaM2: number | null;
    }>;
    vinylFace: string;
    printLaminate: string;
    backingForex: string;
    faceBevelMandatory: string;
    backBevelLabel: string;
  };
  geometry: {
    grossFaceAreaM2: number | null;
    quoteablePlexiglasM2: number | null;
    ledPerimeterM: number | null;
    cncPerimeterM: number | null;
    returnPerimeterM: number | null;
  };
  edgeCant: {
    finishLabel: string;
    realPerimeterM: number | null;
    calculatedCantM: number | null;
    pricedCantM: number | null;
    wastePercent: number | null;
    adhesiveMl: number | null;
    oracalAreaM2: number | null;
    oracalCost: number | null;
    oracalCurrency: string;
    groups: IntakeV4EdgeCantGroupedRow[];
    operations: Array<{ key: string; label: string; quantity: number; unit: string }>;
  };
  lighting: {
    letterLedModules: number | null;
    emblemLedModules: number | null;
    emblemLightingLabel: string;
    emblemOutboxAreaM2: number | null;
    totalLedModules: number | null;
    moduleCount: number | null;
    moduleWattageW: number | null;
    totalLedWatts: number | null;
    requiredPsuWatts: number | null;
    psuConfiguration: number[];
    illuminated: boolean;
  };
  nesting: {
    previewOnly: boolean;
    activeLayout: boolean;
    nestableParts: number | null;
    artworkParts: number | null;
    stockConsumed: boolean;
  };
  warnings: Array<{ code: string; message: string }>;
}

function fmtM(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value.toFixed(2)} m`;
}

function fmtM2(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value.toFixed(4)} m²`;
}

export function formatConfirmSummaryM(value: number | null | undefined): string {
  return fmtM(value);
}

export function formatConfirmSummaryM2(value: number | null | undefined): string {
  return fmtM2(value);
}

function faceFinishLabel(
  code: string | null | undefined,
  oracalCode?: string | null,
  oracalName?: string | null,
): string {
  const token = String(code ?? "").trim().toLowerCase();
  if (!token || token === "none") return "Fără finisaj — plexiglas brut";
  if (token === "oracal_8500") return "Oracal 8500 translucent";
  if (token === "oracal_651") {
    const color = oracalName || oracalCode;
    return color ? `Oracal 651 ${color}` : "Oracal 651";
  }
  if (token === "oracal_641") {
    const color = oracalName || oracalCode;
    return color ? `Oracal 641 ${color}` : "Oracal 641";
  }
  if (token === "ral_spray") return "RAL spray";
  if (token === "policromie") return "Policromie";
  if (token === "colored_plexiglas") return "plexiglas colorat";
  if (token === "print_laminate") return "Print + laminare";
  if (token === "print_translucent") return "print translucid";
  if (token === "printed_vinyl_on_face") return "vinil printat pe față";
  return code ?? "—";
}

function artworkExecutionLabel(execution: string | null | undefined): string {
  const token = String(execution ?? "needs_decision").trim();
  const match = SVG_ARTWORK_EXECUTION_OPTIONS.find((opt) => opt.value === token);
  if (match) return match.label;
  if (token === "needs_decision") return "needs_decision / policromie pending";
  return token;
}

function printTransparencyLabel(value: string | null | undefined): string {
  const token = String(value ?? "standard").trim().toLowerCase();
  if (token === "transparent") return "print transparent";
  if (token === "translucent") return "print translucent";
  return "print standard";
}

function readFinishSetup(payload: Record<string, unknown> | undefined): IntakeV4FinishSetup {
  const raw = payload?.finish_setup;
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return {};
  return raw as IntakeV4FinishSetup;
}

function resolveLetterFaceLabel(finish: IntakeV4FinishSetup): string {
  const groups = finish.letter_group_finishes;
  let finishPart: string;
  if (Array.isArray(groups) && groups.length > 0) {
    const labels = groups.map((g) =>
      faceFinishLabel(g.face_finish_type ?? finish.face_finish_type, g.face_oracal_code, g.face_oracal_name),
    );
    const unique = [...new Set(labels)];
    finishPart = unique.join(" · ");
  } else {
    finishPart = faceFinishLabel(finish.face_finish_type);
  }
  return `Plexiglas 3 mm / față litere · ${finishPart}`;
}

function resolveBackingForexLabel(
  finish: IntakeV4FinishSetup,
  materialBreakdown: IntakeV4MaterialBreakdownResponse | null | undefined,
): string {
  if (finish.backing_mode != null && finish.backing_mode !== undefined) {
    const mode = normalizeIntakeV4BackingMode(finish.backing_mode);
    if (mode === "none") return "absent";
    return backingModeLabel(mode);
  }
  const backingPresent = hasMaterialKey(materialBreakdown, ["forex_backing", "backing", "forex"]);
  return backingPresent ? "present" : "absent";
}

function resolveBackBevelLabel(finish: IntakeV4FinishSetup): string {
  const mode = normalizeIntakeV4BackingMode(finish.backing_mode);
  if (mode === "none") return "n/a";
  if (mode === "forex_10_with_bevel") return "da";
  if (mode === "forex_10_no_bevel") return "nu";
  return "—";
}

function resolveEmblemLightingLabel(mode: string | null | undefined): string {
  const normalized = normalizeEmblemLightingMode(mode);
  if (normalized === "area_lit") return "emblemă luminoasă";
  if (normalized === "excluded") return "emblemă neluminoasă";
  return "decizie iluminare emblemă";
}

function resolveLetterReturnLabel(finish: IntakeV4FinishSetup): string {
  const groups = finish.letter_group_finishes;
  if (Array.isArray(groups) && groups.length > 0) {
    const labels = groups.map((g) =>
      formatIntakeV4ReturnFinishLabel({
        finishType: g.return_finish_type ?? finish.return_finish_type,
        colorCode: g.return_oracal_code,
        colorName: g.return_oracal_name,
      }),
    );
    const unique = [...new Set(labels)];
    return unique.join(" · ");
  }
  return formatIntakeV4ReturnFinishLabel({
    finishType: finish.return_finish_type,
    colorCode: finish.return_oracal_code,
    colorName: finish.return_oracal_name,
  });
}

function findPlexiglasQuoteableArea(
  breakdown: IntakeV4MaterialBreakdownResponse | null | undefined,
): number | null {
  if (!breakdown) return null;
  const row =
    breakdown.material_rows.find((item) => item.material_key === "plexiglas_face") ??
    breakdown.nesting_rows.find((item) => item.material_key.includes("plexiglas"));
  if (!row) return null;
  const qty = "priced_quantity" in row && row.priced_quantity != null ? row.priced_quantity : row.quantity;
  return typeof qty === "number" && qty > 0 ? qty : null;
}

function readAnalyzerReport(payload: Record<string, unknown> | undefined): SvgAnalysisCoreReport | null {
  const raw = payload?.svg_analysis_json;
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return null;
  return Array.isArray((raw as Record<string, unknown>).layers) ? (raw as SvgAnalysisCoreReport) : null;
}

function findMaterialBaseQuantity(
  breakdown: IntakeV4MaterialBreakdownResponse | null | undefined,
  materialKey: string,
): number | null {
  const row = breakdown?.material_rows.find((item) => item.material_key === materialKey);
  const qty = row?.base_quantity ?? row?.quantity;
  return typeof qty === "number" && qty > 0 ? qty : null;
}

function findCncPerimeterFromBreakdown(
  breakdown: IntakeV4MaterialBreakdownResponse | null | undefined,
): number | null {
  const row = (breakdown?.operation_rows ?? []).find(
    (item) =>
      item.unit === "ml" &&
      item.quantity > 0 &&
      (item.key.includes("cnc_face_cutting") || item.operation_type === "cnc_cutting"),
  );
  return typeof row?.quantity === "number" && row.quantity > 0 ? row.quantity : null;
}

function hasMaterialKey(
  breakdown: IntakeV4MaterialBreakdownResponse | null | undefined,
  keys: string[],
): boolean {
  if (!breakdown) return false;
  const all = [...breakdown.material_rows, ...breakdown.consumable_rows, ...breakdown.nesting_rows];
  return all.some((row) => keys.some((key) => row.material_key === key || row.material_key.includes(key)));
}

export interface IntakeV4OperatorWorkSummaryCounts {
  productionParts: number | null;
  artworkCount: number | null;
  innerHoles: number | null;
  layoutPartsCount: number | null;
}

export function buildIntakeV4OperatorWorkSummaryCounts(args: {
  geometry: IntakeV4QuoteGeometry | null;
  nestingPreview: IntakeV4NestingPreviewResponse | null | undefined;
  finish?: IntakeV4FinishSetup;
}): IntakeV4OperatorWorkSummaryCounts {
  return {
    productionParts: args.geometry?.real_letters_count ?? args.geometry?.letter_count ?? null,
    artworkCount: resolveArtworkCount(args.geometry, args.nestingPreview, args.finish ?? {}),
    innerHoles: args.geometry?.inner_holes_count ?? null,
    layoutPartsCount: resolveChildPartsCount(args.geometry, args.nestingPreview),
  };
}

export type IntakeV6OperatorWorkSummaryCounts = IntakeV4OperatorWorkSummaryCounts;
export const buildIntakeV6OperatorWorkSummaryCounts = buildIntakeV4OperatorWorkSummaryCounts;

function resolveChildPartsCount(
  geometry: IntakeV4QuoteGeometry | null,
  nesting: IntakeV4NestingPreviewResponse | null | undefined,
): number | null {
  if (nesting?.summary) {
    const total = (nesting.summary.nestable_parts ?? 0) + (nesting.summary.artwork_parts ?? 0);
    if (total > 0) return total;
  }
  const letters = geometry?.real_letters_count ?? geometry?.letter_count;
  const artwork = geometry?.artwork_piece_count;
  if (letters != null && artwork != null) return letters + artwork;
  if (letters != null) return letters;
  return geometry?.material_piece_count ?? null;
}

function resolveArtworkCount(
  geometry: IntakeV4QuoteGeometry | null,
  nesting: IntakeV4NestingPreviewResponse | null | undefined,
  finish: IntakeV4FinishSetup,
): number | null {
  if (nesting?.summary?.artwork_parts != null && nesting.summary.artwork_parts > 0) {
    return nesting.summary.artwork_parts;
  }
  if (geometry?.artwork_piece_count != null && geometry.artwork_piece_count > 0) {
    return geometry.artwork_piece_count;
  }
  const artworkFinishes = finish.artwork_finishes;
  if (Array.isArray(artworkFinishes) && artworkFinishes.length > 0) {
    return artworkFinishes.length;
  }
  return null;
}

export function buildIntakeV4ConfirmSummary(args: {
  payload: Record<string, unknown> | undefined;
  layerCount: number;
  materialBreakdown: IntakeV4MaterialBreakdownResponse | null;
  nestingPreview: IntakeV4NestingPreviewResponse | null;
  handoffBlockers?: string[] | null;
}): IntakeV4ConfirmSummaryViewModel {
  const finish = readFinishSetup(args.payload);
  const geometry = readQuoteGeometryFromPayload(args.payload);
  const letterPerimeterM = geometry?.letter_perimeter_m ?? geometry?.led_perimeter_ml ?? null;

  const emblemOutboxAreaM2 = geometry?.artwork_area_m2 ?? null;

  const syncedLighting =
    finish.illuminated === false
      ? finish
      : syncIntakeV4FinishLightingForLayerState({
          finish,
          letterPerimeterM,
          emblemAreaM2: emblemOutboxAreaM2,
          artworkBoxes: geometry?.artwork_boxes ?? [],
          letterGroups: finish.letter_group_finishes ?? [],
          artworkFinishes: finish.artwork_finishes ?? [],
          fallbackDepthMm: finish.return_depth_mm ?? null,
        });

  const artworkRows = (finish.artwork_finishes ?? []).map((row) => ({
    layerKey: row.layer_key,
    layerName: row.layer_name ?? row.layer_key,
    executionLabel: artworkExecutionLabel(row.execution_type),
    printTransparencyLabel: printTransparencyLabel(row.print_transparency),
    returnLabel: formatIntakeV4ReturnFinishLabel({
      finishType: row.return_finish_type ?? finish.return_finish_type,
      colorCode: row.return_oracal_code,
      colorName: row.return_oracal_name,
    }),
    returnDepthMm: row.return_depth_mm ?? finish.return_depth_mm ?? null,
    areaM2: row.estimated_area_m2 ?? null,
  }));
  const letterRows = (finish.letter_group_finishes ?? []).map((group) => ({
    groupKey: group.group_key,
    layerName: group.layer_name ?? group.group_key,
    faceLabel: faceFinishLabel(
      group.face_finish_type ?? finish.face_finish_type,
      group.face_oracal_code,
      group.face_oracal_name,
    ),
    faceRollWidthMm: group.face_vinyl_roll_width_mm ?? finish.face_vinyl_roll_width_mm ?? null,
    returnLabel: formatIntakeV4ReturnFinishLabel({
      finishType: group.return_finish_type ?? finish.return_finish_type,
      colorCode: group.return_oracal_code,
      colorName: group.return_oracal_name,
    }),
    returnDepthMm: group.return_depth_mm ?? finish.return_depth_mm ?? null,
    perimeterM: group.perimeter_m ?? null,
  }));

  const vinylPresent = hasMaterialKey(args.materialBreakdown, [
    "face_vinyl",
    "face_vinyl_641",
    "face_vinyl_651",
    "oracal",
  ]);
  const printPresent = hasMaterialKey(args.materialBreakdown, ["print", "laminate", "policromie"]);

  const warnings: IntakeV4ConfirmSummaryViewModel["warnings"] = [];
  for (const code of args.handoffBlockers ?? []) {
    if (code.startsWith("artwork_execution_undecided:")) {
      const layerKey = code.split(":")[1] ?? "artwork";
      warnings.push({
        code,
        message: `Warning: artwork execution undecided on ${layerKey}. Draft quote policy: currently blocked until this is resolved. Order/producție: blocked.`,
      });
    }
  }
  for (const warning of args.materialBreakdown?.warnings ?? []) {
    if (
      warning.code === "artwork_execution_pending" ||
      warning.code === "unclassified_vector_artwork_requires_decision"
    ) {
      warnings.push({
        code: warning.code,
        message: warning.message ?? "Artwork/vector execution pending decision.",
      });
    }
  }
  const artworkDecisionPending =
    (finish.artwork_finishes ?? []).some((row) => {
      const token = String(row.execution_type ?? "needs_decision").trim().toLowerCase();
      return !token || token === "needs_decision";
    }) ||
    warnings.some((warning) =>
      warning.code.includes("artwork_execution_undecided") ||
      warning.code === "artwork_execution_pending" ||
      warning.code === "unclassified_vector_artwork_requires_decision",
    );
  const printLaminateLabel = printPresent
    ? artworkDecisionPending
      ? "present (pending artwork decision)"
      : "present"
    : artworkDecisionPending
      ? "absent până la decizie artwork"
      : "absent";

  const nestingSummary = args.nestingPreview?.summary;
  const nestingBoundary = args.nestingPreview?.boundary;

  const edgeCantModel = buildIntakeV4EdgeCantViewModel({
    finish,
    breakdown: args.materialBreakdown,
    geometryReturnPerimeterM: geometry?.return_material_perimeter_ml ?? null,
  });
  const edgeCantLayerBreakdown = buildIntakeV4EdgeCantLayerBreakdown({
    letterGroups: finish.letter_group_finishes ?? [],
    artworkFinishes: finish.artwork_finishes ?? [],
    report: readAnalyzerReport(args.payload),
  });
  const effectiveCncPerimeterM =
    findCncPerimeterFromBreakdown(args.materialBreakdown) ??
    geometry?.face_cutting_perimeter_ml ??
    geometry?.cutting_perimeter_ml ??
    null;
  const effectiveReturnPerimeterM = resolveIntakeV4EffectiveReturnPerimeterM({
    breakdown: args.materialBreakdown,
    geometryReturnPerimeterM:
      geometry?.return_material_perimeter_ml ??
      findMaterialBaseQuantity(args.materialBreakdown, "return_material") ??
      null,
  });
  const edgeCantGroups = normalizeIntakeV4EdgeCantGroupsToTotal({
    groups: edgeCantLayerBreakdown.groups,
    targetTotalM: effectiveReturnPerimeterM,
  }).groups;

  return {
    structure: {
      layerCount: args.layerCount,
      childPartsCount: resolveChildPartsCount(geometry, args.nestingPreview),
      realLettersCount: geometry?.real_letters_count ?? geometry?.letter_count ?? null,
      artworkCount: resolveArtworkCount(geometry, args.nestingPreview, finish),
      innerHolesCount: geometry?.inner_holes_count ?? null,
    },
    finish: {
      letterFaceLabel: resolveLetterFaceLabel(finish),
      letterReturnLabel: resolveLetterReturnLabel(finish),
      letterRows,
      artworkRows,
      vinylFace: vinylPresent ? "present" : "absent",
      printLaminate: printLaminateLabel,
      backingForex: resolveBackingForexLabel(finish, args.materialBreakdown),
      faceBevelMandatory: "da, obligatoriu",
      backBevelLabel: resolveBackBevelLabel(finish),
    },
    geometry: {
      grossFaceAreaM2: geometry?.face_area_m2 ?? null,
      quoteablePlexiglasM2: findPlexiglasQuoteableArea(args.materialBreakdown),
      ledPerimeterM: geometry?.led_perimeter_ml ?? geometry?.letter_perimeter_m ?? null,
      cncPerimeterM: effectiveCncPerimeterM,
      returnPerimeterM: effectiveReturnPerimeterM,
    },
    edgeCant: {
      finishLabel: edgeCantModel.finishLabel,
      realPerimeterM: effectiveReturnPerimeterM,
      calculatedCantM: edgeCantModel.calculatedCantM,
      pricedCantM: edgeCantModel.pricedCantM,
      wastePercent: edgeCantModel.wastePercent,
      adhesiveMl: edgeCantModel.adhesiveMl,
      oracalAreaM2: edgeCantModel.oracal651.present ? edgeCantModel.oracal651.areaM2 : null,
      oracalCost:
        edgeCantModel.oracal651.present && !edgeCantModel.oracal651.pricingMissing
          ? edgeCantModel.oracal651.estimatedCost
          : null,
      oracalCurrency: edgeCantModel.oracal651.currency,
      groups: edgeCantGroups,
      operations: edgeCantModel.operations.map((op) => ({
        key: op.key,
        label: op.label,
        quantity: op.quantity,
        unit: op.unit,
      })),
    },
    lighting: {
      letterLedModules: syncedLighting.letter_led_module_count ?? null,
      emblemLedModules: syncedLighting.emblem_led_module_count ?? null,
      emblemLightingLabel: resolveEmblemLightingLabel(finish.emblem_lighting_mode),
      emblemOutboxAreaM2: emblemOutboxAreaM2,
      totalLedModules:
        syncedLighting.total_led_module_count ?? syncedLighting.led_module_count ?? null,
      moduleCount: syncedLighting.led_module_count ?? null,
      moduleWattageW: syncedLighting.led_module_power_w ?? null,
      totalLedWatts: syncedLighting.estimated_led_watts ?? null,
      requiredPsuWatts: syncedLighting.required_psu_watts ?? null,
      psuConfiguration: syncedLighting.psu_configuration ?? [],
      illuminated: finish.illuminated !== false,
    },
    nesting: {
      previewOnly: args.nestingPreview?.preview_only !== false,
      activeLayout: (nestingSummary?.active_sheet_layouts ?? 0) > 0 || (nestingSummary?.sheet_layouts ?? 0) > 0,
      nestableParts: nestingSummary?.nestable_parts ?? null,
      artworkParts: nestingSummary?.artwork_parts ?? null,
      stockConsumed: nestingBoundary?.consumes_stock === true || args.materialBreakdown?.stock_consumption === true,
    },
    warnings,
  };
}
