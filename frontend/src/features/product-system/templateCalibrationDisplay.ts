import type {
  ProductTemplateMaterial,
  ProductTemplateOperation,
} from "@/lib/api";

export const CALIBRATION_DURATION_TOOLTIP =
  "Timp intern pentru planificare/calibrare, nu bază de ofertare.";

export const UNIT_PRICING_NOTE =
  "Prețurile se calculează din unități (mp, ml, buc, set, operație), nu din ore.";

export function hasFormulaLineMetadata(
  row: Pick<
    ProductTemplateOperation | ProductTemplateMaterial,
    | "calculation_type"
    | "formula_id"
    | "formula_params"
    | "requires_quote_input"
    | "_extras"
  >
): boolean {
  if (row.calculation_type === "formula_based") return true;
  if (row.calculation_type && row.calculation_type !== "static") return true;
  if ((row.formula_id || "").trim().length > 0) return true;
  const params = row.formula_params;
  if (params && typeof params === "object" && Object.keys(params).length > 0) return true;
  const quoteInput = row.requires_quote_input;
  if (Array.isArray(quoteInput) && quoteInput.length > 0) return true;
  const extras = row._extras;
  if (extras && typeof extras === "object" && Object.keys(extras).length > 0) return true;
  return false;
}

/** Display-only: QC is internal verification, not a priced service line. */
export function formatComponentDisplayName(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) return trimmed;
  let n = trimmed.replace(/,?\s*QC\b/gi, "");
  n = n.replace(/,\s*,/g, ",").replace(/,\s*$/g, "").trim();
  return n || trimmed;
}

export function formatOperationCalibrationLabel(
  op: Pick<ProductTemplateOperation, "estimatedMinutes" | "calculation_type" | "formula_id" | "formula_params" | "requires_quote_input" | "_extras">
): string {
  const dynamic = hasFormulaLineMetadata(op);
  const mins = op.estimatedMinutes ?? 0;
  if (dynamic && mins <= 0) return "calculată la ofertare";
  if (dynamic) return `durată internă de calibrare: ${mins} min`;
  if (mins <= 0) return "din formulă";
  return `durată internă de calibrare: ${mins} min`;
}

export function formatMaterialQuantityLabel(
  m: Pick<ProductTemplateMaterial, "quantity" | "unit" | "calculation_type" | "formula_id" | "formula_params" | "requires_quote_input" | "_extras">
): string {
  const dynamic = hasFormulaLineMetadata(m);
  const qty = m.quantity ?? 0;
  const unit = (m.unit || "").trim();
  if (dynamic && qty <= 0) return "calculată la ofertare";
  if (dynamic) return `${qty} ${unit}`.trim();
  if (qty <= 0 && dynamic) return "din formulă";
  return unit ? `${qty} ${unit}` : String(qty);
}

export function formatInternalComponentMinutes(totalMinutes: number): string | null {
  if (totalMinutes <= 0) return null;
  return `timp intern orientativ: ${totalMinutes} min`;
}

export function formatInternalTemplateHours(hours: number): string | null {
  if (hours <= 0) return null;
  return `${hours}h`;
}
