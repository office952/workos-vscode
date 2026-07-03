/** Operator-facing labels for Intake V4 quantity_basis tokens (internal keys unchanged). */

export const INTAKE_V4_QUANTITY_BASIS_LABELS: Record<string, string> = {
  roll_nesting_quote_estimate: "Nesting rolă — estimare ofertă",
  sheet_nesting_quote_estimate: "Nesting placă — estimare ofertă",
  sheet_nesting_role_split_quote_estimate: "Nesting placă — estimare ofertă",
  sheet_nesting_part_kind_quote_estimate: "Nesting placă — estimare ofertă",
  sheet_nesting_prorated_fallback: "Nesting placă — fallback pro-rata",
  area_with_waste_fallback: "Fallback arie + pierdere material",
  perimeter_with_waste: "Cant / volum pentru preț (+20% pierdere)",
  print_area_quote_estimate: "Arie print artwork — estimare ofertă",
  laminate_area_quote_estimate: "Arie laminare — estimare ofertă",
  led_modules_perimeter_pitch_estimate: "Module LED — estimare după perimetru",
  led_modules_count_x_module_wattage: "Consum LED total (module × putere)",
  psu_configuration_quote_estimate: "Sursă LED — estimare ofertă",
  adhesive_return_to_face_ml_per_ml_cant: "Adeziv — 2 ml / ml cant (litere)",
  adhesive_led_modules_ml_per_module: "Adeziv LED — 0.2 ml / modul",
  wire_letters_myyup_2x075_per_segment: "Cablu MYYUP 2×0.75 — 1 ml / literă",
  wire_supply_myyup_2x15_per_job: "Cablu MYYUP 2×1.5 — alimentare set",
};

export const INTAKE_V4_CONFIDENCE_LABELS: Record<string, string> = {
  estimate_from_nesting_high: "Nesting — precizie ridicată",
  estimate_from_nesting_medium: "Nesting — precizie medie",
  estimate_fallback_area: "Fallback arie",
  estimate_fallback_perimeter: "Perimetru geometric (fallback)",
  estimate_formula: "Formula inginerie",
  estimate_missing_metadata: "Metadata lipsă",
  estimate_for_quote: "Estimare ofertă",
};

/** Shown when sheet nesting footprint was below eligible part area and quantity was floored. */
export const INTAKE_V4_SHEET_NESTING_FLOOR_CONFIDENCE_LABEL =
  "Estimare arie piese — floor arie eligibilă";

export const INTAKE_V4_SHEET_NESTING_FLOOR_HINT =
  "Footprint-ul nesting era sub aria pieselor; cantitatea a fost ridicată la aria eligibilă pentru a evita subestimarea.";

const SHEET_NESTING_CONFIDENCE_TOKENS = new Set([
  "estimate_from_nesting_high",
  "estimate_from_nesting_medium",
]);

export function isSheetNestingQuoteMaterialRow(options: {
  quantityBasis?: string | null;
  quantitySource?: string | null;
  materialKey?: string | null;
}): boolean {
  const basis = options.quantityBasis ?? "";
  const source = options.quantitySource ?? "";
  const key = options.materialKey ?? "";
  if (basis.startsWith("sheet_nesting")) return true;
  if (source.includes("nesting")) return true;
  return key === "plexiglas_face" || key === "forex_backing";
}

export function shouldUseSheetNestingFloorConfidenceLabel(options: {
  sheetNestingFloorApplied?: boolean;
  confidence?: string | null;
  quantityBasis?: string | null;
  quantitySource?: string | null;
  materialKey?: string | null;
}): boolean {
  if (!options.sheetNestingFloorApplied) return false;
  if (!options.confidence || !SHEET_NESTING_CONFIDENCE_TOKENS.has(options.confidence)) {
    return false;
  }
  return isSheetNestingQuoteMaterialRow(options);
}

export function formatIntakeV4QuantityBasisLabel(basis: string | null | undefined): string {
  if (!basis) return "";
  const mapped = INTAKE_V4_QUANTITY_BASIS_LABELS[basis];
  if (mapped) return mapped;
  if (basis.endsWith("_quote_estimate")) return "Estimare ofertă";
  return "Estimare ofertă";
}

export function formatIntakeV4ConfidenceLabel(confidence: string | null | undefined): string {
  if (!confidence) return "";
  return INTAKE_V4_CONFIDENCE_LABELS[confidence] ?? confidence;
}

export function formatIntakeV4MaterialRowConfidenceLabel(
  confidence: string | null | undefined,
  options?: {
    sheetNestingFloorApplied?: boolean;
    quantityBasis?: string | null;
    quantitySource?: string | null;
    materialKey?: string | null;
  },
): string {
  if (
    shouldUseSheetNestingFloorConfidenceLabel({
      sheetNestingFloorApplied: options?.sheetNestingFloorApplied,
      confidence,
      quantityBasis: options?.quantityBasis,
      quantitySource: options?.quantitySource,
      materialKey: options?.materialKey,
    })
  ) {
    return INTAKE_V4_SHEET_NESTING_FLOOR_CONFIDENCE_LABEL;
  }
  return formatIntakeV4ConfidenceLabel(confidence);
}
