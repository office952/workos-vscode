import { normalizeTemplateCode } from "@/lib/activeTemplateScope";
import { PRODUCT_SYSTEM_PRODUCTS_PATH } from "./productSystemShellConfig";

export function parseProductSystemTemplateRouteParam(
  raw: string | null | undefined,
): string | null {
  if (!raw) return null;
  try {
    const decoded = decodeURIComponent(raw);
    const normalized = normalizeTemplateCode(decoded);
    return normalized.length > 0 ? normalized : null;
  } catch {
    return null;
  }
}

export function resolveRequestedTemplateCode(input: {
  pathTemplateCode?: string | null;
  queryTemplateCode?: string | null;
}): string | null {
  const fromPath = parseProductSystemTemplateRouteParam(input.pathTemplateCode);
  if (fromPath) return fromPath;
  const fromQuery = parseProductSystemTemplateRouteParam(input.queryTemplateCode);
  return fromQuery;
}

export function buildProductSystemProductDetailPath(templateCode: string): string {
  return `${PRODUCT_SYSTEM_PRODUCTS_PATH}/${encodeURIComponent(templateCode)}`;
}

/** Structure-step detail pages nest under the product detail path. */
export function isProductSystemProductStructureDetailPath(pathname: string): boolean {
  return /^\/product-system\/products\/[^/]+\/structure\//.test(pathname);
}

export function buildProductSystemProductsPathWithQuery(templateCode: string): string {
  return `${PRODUCT_SYSTEM_PRODUCTS_PATH}?template=${encodeURIComponent(templateCode)}`;
}

export function isProductSystemShellPath(pathname: string): boolean {
  return pathname === PRODUCT_SYSTEM_PRODUCTS_PATH || pathname.startsWith(`${PRODUCT_SYSTEM_PRODUCTS_PATH}/`) ||
    pathname.startsWith(`${PRODUCT_SYSTEM_PRODUCTS_PATH}?`) ||
    pathname.startsWith("/product-system/");
}

export function productSystemShellNavIdForPath(pathname: string): string | null {
  if (pathname === PRODUCT_SYSTEM_PRODUCTS_PATH || pathname.startsWith(`${PRODUCT_SYSTEM_PRODUCTS_PATH}/`)) {
    return "products";
  }
  if (pathname.startsWith("/product-system/components")) return "components";
  if (pathname.startsWith("/product-system/resources")) return "resources";
  if (pathname.startsWith("/product-system/operations")) return "operations";
  if (pathname.startsWith("/product-system/dependencies")) return "dependencies";
  if (pathname.startsWith("/product-system/validation")) return "validation";
  if (pathname.startsWith("/product-system/advanced")) return "advanced";
  return null;
}
