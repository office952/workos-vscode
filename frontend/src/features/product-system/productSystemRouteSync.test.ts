import { describe, expect, it } from "vitest";
import { TPL_ACM_BOXED_MOUNTING_SUPPORT } from "@/lib/acmQuoteInput";
import {
  normalizeTemplateCode,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
} from "@/lib/activeTemplateScope";
import {
  buildProductSystemProductDetailPath,
  parseProductSystemTemplateRouteParam,
  productSystemShellNavIdForPath,
  resolveRequestedTemplateCode,
} from "@/features/product-system/productSystemRouteSync";

describe("productSystemRouteSync", () => {
  it("normalizes path and query template codes", () => {
    expect(parseProductSystemTemplateRouteParam("tpl-volumetric-letters_v2")).toBe(
      "TPL-VOLUMETRIC-LETTERS_V2",
    );
    expect(
      resolveRequestedTemplateCode({
        pathTemplateCode: TPL_ACM_BOXED_MOUNTING_SUPPORT,
        queryTemplateCode: OWNER_VALID_ACTIVE_TEMPLATE_CODE,
      }),
    ).toBe(normalizeTemplateCode(TPL_ACM_BOXED_MOUNTING_SUPPORT));
  });

  it("prefers path param over query param", () => {
    expect(
      resolveRequestedTemplateCode({
        pathTemplateCode: null,
        queryTemplateCode: OWNER_VALID_ACTIVE_TEMPLATE_CODE,
      }),
    ).toBe(normalizeTemplateCode(OWNER_VALID_ACTIVE_TEMPLATE_CODE));
  });

  it("builds canonical product detail paths", () => {
    expect(buildProductSystemProductDetailPath(TPL_ACM_BOXED_MOUNTING_SUPPORT)).toBe(
      `/product-system/products/${encodeURIComponent(TPL_ACM_BOXED_MOUNTING_SUPPORT)}`,
    );
  });

  it("maps shell nav ids from pathname", () => {
    expect(productSystemShellNavIdForPath("/product-system/products")).toBe("products");
    expect(
      productSystemShellNavIdForPath(
        `/product-system/products/${encodeURIComponent(TPL_ACM_BOXED_MOUNTING_SUPPORT)}`,
      ),
    ).toBe("products");
    expect(productSystemShellNavIdForPath("/product-system/validation")).toBe("validation");
    expect(productSystemShellNavIdForPath("/product-system/advanced")).toBe("advanced");
  });
});
