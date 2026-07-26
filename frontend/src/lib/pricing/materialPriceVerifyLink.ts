/**
 * Product System / docs must not duplicate registry unit costs.
 * Operator verifies live price in Pricing Registry.
 */

export const MATERIAL_PRICE_VERIFY_LABEL_RO = "Verifică preț material";
export const MATERIAL_PRICE_VERIFY_BASE_PATH = "/inventory/pricing";

export function buildMaterialPriceVerifyHref(materialCode: string): string {
  const code = String(materialCode || "").trim();
  if (!code) return MATERIAL_PRICE_VERIFY_BASE_PATH;
  const params = new URLSearchParams({ code });
  return `${MATERIAL_PRICE_VERIFY_BASE_PATH}?${params.toString()}`;
}
