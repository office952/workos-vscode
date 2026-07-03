/**
 * Operator-facing labels for intake product_family values.
 * Empty / whitespace product_family means quick-start generic — not a real registry family.
 */

export const UNRESOLVED_INTAKE_PRODUCT_FAMILY = "";

export const UNRESOLVED_INTAKE_PRODUCT_FAMILY_LABEL = "Nespecificat";

export function isUnresolvedIntakeProductFamily(
  productFamily: string | null | undefined
): boolean {
  return !(productFamily ?? "").trim();
}

export function formatIntakeProductFamilyLabel(
  productFamily: string | null | undefined
): string {
  if (isUnresolvedIntakeProductFamily(productFamily)) {
    return UNRESOLVED_INTAKE_PRODUCT_FAMILY_LABEL;
  }
  return (productFamily ?? "").trim();
}
