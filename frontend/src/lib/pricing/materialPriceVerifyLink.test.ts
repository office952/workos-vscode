import { describe, expect, it } from "vitest";
import {
  buildMaterialPriceVerifyHref,
  MATERIAL_PRICE_VERIFY_LABEL_RO,
} from "./materialPriceVerifyLink";

describe("materialPriceVerifyLink", () => {
  it("builds pricing registry href with material code", () => {
    expect(MATERIAL_PRICE_VERIFY_LABEL_RO).toBe("Verifică preț material");
    expect(buildMaterialPriceVerifyHref("MAT-ORACAL-8500")).toBe(
      "/inventory/pricing?code=MAT-ORACAL-8500",
    );
    expect(buildMaterialPriceVerifyHref("MAT-ACP-FATA-LITERE")).toBe(
      "/inventory/pricing?code=MAT-ACP-FATA-LITERE",
    );
  });
});
