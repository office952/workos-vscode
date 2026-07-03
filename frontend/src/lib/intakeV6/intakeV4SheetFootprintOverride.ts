export interface IntakeV4SheetFootprintOverride {
  enabled?: boolean;
  source?: string;
  selectedFootprintSource?: string;
  selected_footprint_source?: string;
  width_cm?: number;
  widthCm?: number;
  height_cm?: number;
  heightCm?: number;
  area_sqm?: number;
  areaSqm?: number;
  reason?: string;
  applies_to?: string[];
  appliesTo?: string[];
  use_for_quote_estimate?: boolean;
  useForQuoteEstimate?: boolean;
}

export function readSheetFootprintOverrideWidthCm(
  override: IntakeV4SheetFootprintOverride | null | undefined,
): number | null {
  const value = override?.widthCm ?? override?.width_cm;
  return typeof value === "number" && value > 0 ? value : null;
}

export function readSheetFootprintOverrideHeightCm(
  override: IntakeV4SheetFootprintOverride | null | undefined,
): number | null {
  const value = override?.heightCm ?? override?.height_cm;
  return typeof value === "number" && value > 0 ? value : null;
}

export function computeOperatorSheetFootprintAreaSqm(widthCm: number, heightCm: number): number {
  return Math.round((widthCm * heightCm) / 10_000 * 10_000) / 10_000;
}

export function formatSheetFootprintSqm(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(4)} m²`;
}

export interface SheetFootprintValidationInput {
  widthCm: number;
  heightCm: number;
  reason: string;
  useForQuoteEstimate: boolean;
  eligibleFaceAreaSqm?: number | null;
  fullSheetSqm?: number | null;
}

export function validateSheetFootprintOverrideInput(
  input: SheetFootprintValidationInput,
): { ok: true; areaSqm: number; warnings: string[] } | { ok: false; error: string } {
  const { widthCm, heightCm, reason, useForQuoteEstimate, eligibleFaceAreaSqm, fullSheetSqm } = input;
  if (!Number.isFinite(widthCm) || !Number.isFinite(heightCm) || widthCm <= 0 || heightCm <= 0) {
    return { ok: false, error: "Introduce lățime și înălțime valide (cm)." };
  }
  if (!reason.trim()) {
    return { ok: false, error: "Notă operator obligatorie (ex. Măsurat în Corel: 192.67 × 143.389 cm)." };
  }
  const areaSqm = computeOperatorSheetFootprintAreaSqm(widthCm, heightCm);
  const warnings: string[] = [];
  if (
    useForQuoteEstimate &&
    eligibleFaceAreaSqm != null &&
    areaSqm < eligibleFaceAreaSqm - 1e-9
  ) {
    return {
      ok: false,
      error: "Footprint manual este sub aria pieselor eligibile — nu poate fi folosit ca preview selectat.",
    };
  }
  if (fullSheetSqm != null && areaSqm > fullSheetSqm + 1e-9) {
    warnings.push("Footprint manual depășește aria plăcii disponibile (6.000 m²).");
  }
  return { ok: true, areaSqm, warnings };
}
