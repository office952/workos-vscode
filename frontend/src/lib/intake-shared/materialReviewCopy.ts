export const SHEET_QUOTE_SELECTED_QUANTITY_EXPLANATION =
  "Cantitatea selectată este floor-ul ariei eligibile. Candidații de nesting sunt disponibili în review intern. Nu este aplicat la ofertă finală.";

export const SHEET_QUOTE_MANUAL_REVIEW_CTA_STEPS = [
  "Verifică layout-ul în Corel.",
  "Măsoară footprint-ul ocupat pe placă.",
  'Introdu lățime × înălțime în câmpul "Footprint manual Corel".',
] as const;

export function formatSqmDisplay(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(4)} m²`;
}

export function formatSheetQuoteSourceLabel(source: string | null | undefined): string {
  if (source === "eligible_area_floor") return "Floor arie eligibilă (politică curentă)";
  if (source === "placement_footprint_face") return "Footprint placement face";
  if (source === "operator_manual_footprint") return "Footprint manual operator";
  return source ?? "—";
}

/** Operator-facing footprint source — no internal policy keys in main UI. */
export function formatOperatorFootprintSourceLabel(source: string | null | undefined): string {
  if (source === "eligible_area_floor") return "Aria pieselor eligibile";
  if (source === "placement_footprint_face") return "Placement face";
  if (source === "operator_manual_footprint") return "Manual Corel";
  if (source === "face_union_bbox") return "Face union bbox";
  if (source === "layout_occupied_area") return "Layout auto shelf";
  if (source === "full_sheet_allocation") return "Placă fizică";
  return "Măsurare automată din sistem";
}
