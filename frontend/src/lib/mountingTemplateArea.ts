import type { IntakeProductSpec } from "@/lib/intakeProductSpec";

/** Round to 2 decimal places for m² display/persistence. */
export function roundAreaM2(value: number): number {
  return Math.round(value * 100) / 100;
}

/**
 * Derive mounting template area (m²) from assembly dimensions or letter face area.
 * width_mm × height_mm / 1_000_000 when both dimensions are present.
 */
export function computeMountingTemplateAreaM2(
  spec: Pick<
    IntakeProductSpec,
    "width_mm" | "height_mm" | "letter_face_area_m2"
  >
): number | null {
  const w = spec.width_mm;
  const h = spec.height_mm;
  if (w != null && w > 0 && h != null && h > 0) {
    return roundAreaM2((w * h) / 1_000_000);
  }
  const face = spec.letter_face_area_m2;
  if (face != null && face > 0) {
    return roundAreaM2(face);
  }
  return null;
}

export function formatMountingTemplateAreaHint(
  spec: Pick<IntakeProductSpec, "width_mm" | "height_mm">
): string | null {
  const w = spec.width_mm;
  const h = spec.height_mm;
  if (w != null && w > 0 && h != null && h > 0) {
    return `Calculat automat din ${w} × ${h} mm`;
  }
  return null;
}
