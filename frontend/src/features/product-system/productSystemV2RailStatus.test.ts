import { describe, expect, it } from "vitest";
import {
  ACM_BOXED_TEMPLATE_CODE,
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
} from "@/lib/productSystemModularityTruth";
import {
  PRODUCT_SYSTEM_V2_RAIL_TITLE_RO,
  productSystemV2MissingTemplateCopy,
  productSystemV2RailStatus,
} from "./productSystemV2RailStatus";

describe("productSystemV2RailStatus", () => {
  it("does not title the mixed-status rail as uniformly active", () => {
    expect(PRODUCT_SYSTEM_V2_RAIL_TITLE_RO).toBe("Produse");
    expect(PRODUCT_SYSTEM_V2_RAIL_TITLE_RO.toLowerCase()).not.toContain("active");
  });

  it("keeps Letters as live/runtime vocabulary without component-first", () => {
    const status = productSystemV2RailStatus(LETTERS_TEMPLATE_CODE);
    expect(status?.kind).toBe("active");
    expect(status?.labelRo).toBe("Rădăcină folosită azi");
    expect(status?.labelRo.toLowerCase()).not.toMatch(/component-first|candidat|blocat/);
  });

  it("keeps ACM present as PARTIAL / montaj, not fully ready", () => {
    const status = productSystemV2RailStatus(ACM_BOXED_TEMPLATE_CODE);
    expect(status?.kind).toBe("partial");
    expect(status?.labelRo).toBe("Montaj ACM · parțial");
  });

  it("exposes Logo blocked / not-offerable truth when the code is requested", () => {
    const upper = productSystemV2MissingTemplateCopy("TPL-VOLUMETRIC-LOGO_V1");
    expect(upper.status?.kind).toBe("blocked");
    expect(upper.headlineRo).toMatch(/rădăcină blocată/i);
    expect(upper.detailRo).toMatch(/nu este ofertabilă/i);
    expect(productSystemV2RailStatus(LOGO_TEMPLATE_CODE)?.kind).toBe("blocked");
  });
});
