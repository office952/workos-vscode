import { describe, expect, it } from "vitest";
import {
  ACM_SHEET_ENVIRONMENT_OPTIONS,
  ACM_SHEET_ISSUE_ENVIRONMENT_MISSING,
  ACM_SHEET_ISSUE_MIRROR_EXTERIOR_SKU,
  ACM_SHEET_ISSUE_VARIANT_MISSING,
  ACM_SHEET_MATERIAL_SCHEMA,
  ACM_SHEET_VARIANT_OPTIONS,
  acmSheetMaterialIssues,
  emptyAcmSheetMaterialContract,
  isAcmMirrorVariant,
  normalizeAcmSheetMaterial,
  readAcmSheetMaterial,
} from "./acmSheetMaterial";

describe("acmPanel acmSheetMaterial options", () => {
  it("exposes exactly the four accepted variants with Romanian labels", () => {
    expect(ACM_SHEET_VARIANT_OPTIONS.map((o) => o.value)).toEqual([
      "standard",
      "colorat",
      "oglinda_gold",
      "oglinda_antracit",
    ]);
    expect(ACM_SHEET_VARIANT_OPTIONS.map((o) => o.labelRo)).toEqual([
      "ACM standard",
      "ACM colorat",
      "ACM oglindă gold",
      "ACM oglindă antracit",
    ]);
  });

  it("exposes exactly interior / exterior environments", () => {
    expect(ACM_SHEET_ENVIRONMENT_OPTIONS.map((o) => o.value)).toEqual([
      "interior",
      "exterior",
    ]);
    expect(ACM_SHEET_ENVIRONMENT_OPTIONS.map((o) => o.labelRo)).toEqual([
      "Interior",
      "Exterior",
    ]);
  });
});

describe("acmPanel isAcmMirrorVariant", () => {
  it("is true only for the two mirror variants", () => {
    expect(isAcmMirrorVariant("oglinda_gold")).toBe(true);
    expect(isAcmMirrorVariant("oglinda_antracit")).toBe(true);
    expect(isAcmMirrorVariant("standard")).toBe(false);
    expect(isAcmMirrorVariant("colorat")).toBe(false);
    expect(isAcmMirrorVariant(null)).toBe(false);
    expect(isAcmMirrorVariant(undefined)).toBe(false);
  });
});

describe("acmPanel normalizeAcmSheetMaterial", () => {
  it("normalizes a fully valid payload", () => {
    const n = normalizeAcmSheetMaterial({
      schema: ACM_SHEET_MATERIAL_SCHEMA,
      variant: "colorat",
      environment: "exterior",
      exterior_sku: null,
      operator_confirmed: true,
    });
    expect(n).toEqual({
      schema: ACM_SHEET_MATERIAL_SCHEMA,
      variant: "colorat",
      environment: "exterior",
      exterior_sku: null,
      operator_confirmed: true,
    });
  });

  it("keeps a proven SKU for mirror on exterior", () => {
    const n = normalizeAcmSheetMaterial({
      variant: "oglinda_gold",
      environment: "exterior",
      exterior_sku: "  SKU-EXT-001  ",
    });
    expect(n?.variant).toBe("oglinda_gold");
    expect(n?.exterior_sku).toBe("SKU-EXT-001");
  });

  it("accepts a partial payload without inventing values", () => {
    const n = normalizeAcmSheetMaterial({ variant: "standard" });
    expect(n).toEqual({
      schema: ACM_SHEET_MATERIAL_SCHEMA,
      variant: "standard",
      environment: null,
      exterior_sku: null,
      operator_confirmed: false,
    });
  });

  it("never invents operator_confirmed", () => {
    expect(normalizeAcmSheetMaterial({})?.operator_confirmed).toBe(false);
    expect(
      normalizeAcmSheetMaterial({ variant: "standard", environment: "interior" })
        ?.operator_confirmed,
    ).toBe(false);
  });

  it("maps an unknown variant token to null — never silently to standard", () => {
    const n = normalizeAcmSheetMaterial({
      variant: "acm_brushed_titanium",
      environment: "interior",
    });
    expect(n?.variant).toBeNull();
    expect(n?.environment).toBe("interior");
  });

  it("maps an unknown environment token to null", () => {
    const n = normalizeAcmSheetMaterial({ variant: "standard", environment: "semi_exterior" });
    expect(n?.environment).toBeNull();
  });

  it("accepts case-insensitive, padded tokens", () => {
    const n = normalizeAcmSheetMaterial({ variant: " Standard ", environment: "INTERIOR" });
    expect(n?.variant).toBe("standard");
    expect(n?.environment).toBe("interior");
  });

  it("returns null for unusable input", () => {
    expect(normalizeAcmSheetMaterial(null)).toBeNull();
    expect(normalizeAcmSheetMaterial(undefined)).toBeNull();
    expect(normalizeAcmSheetMaterial("oglinda_gold")).toBeNull();
    expect(normalizeAcmSheetMaterial(42)).toBeNull();
    expect(normalizeAcmSheetMaterial([{ variant: "standard" }])).toBeNull();
  });

  it("clears a stale exterior_sku when the variant is no longer a mirror", () => {
    const n = normalizeAcmSheetMaterial({
      variant: "standard",
      environment: "exterior",
      exterior_sku: "SKU-EXT-001",
    });
    expect(n?.exterior_sku).toBeNull();
  });

  it("clears a stale exterior_sku when the environment is no longer exterior", () => {
    const n = normalizeAcmSheetMaterial({
      variant: "oglinda_antracit",
      environment: "interior",
      exterior_sku: "SKU-EXT-001",
    });
    expect(n?.exterior_sku).toBeNull();
  });

  it("treats a blank SKU as absent", () => {
    const n = normalizeAcmSheetMaterial({
      variant: "oglinda_gold",
      environment: "exterior",
      exterior_sku: "   ",
    });
    expect(n?.exterior_sku).toBeNull();
  });
});

describe("acmPanel readAcmSheetMaterial", () => {
  it("reads a stored contract off the instance", () => {
    const contract = readAcmSheetMaterial({
      sheet_material: { variant: "colorat", environment: "interior" },
    });
    expect(contract.variant).toBe("colorat");
    expect(contract.environment).toBe("interior");
  });

  it("falls back to the empty contract when nothing usable is stored", () => {
    expect(readAcmSheetMaterial({})).toEqual(emptyAcmSheetMaterialContract());
    expect(readAcmSheetMaterial({ sheet_material: "standard" })).toEqual(
      emptyAcmSheetMaterialContract(),
    );
  });
});

describe("acmPanel acmSheetMaterialIssues", () => {
  it("reports both missing selections on an empty contract", () => {
    expect(acmSheetMaterialIssues(emptyAcmSheetMaterialContract())).toEqual([
      ACM_SHEET_ISSUE_VARIANT_MISSING,
      ACM_SHEET_ISSUE_ENVIRONMENT_MISSING,
    ]);
  });

  it("reports both missing selections for null / undefined", () => {
    expect(acmSheetMaterialIssues(null)).toEqual([
      ACM_SHEET_ISSUE_VARIANT_MISSING,
      ACM_SHEET_ISSUE_ENVIRONMENT_MISSING,
    ]);
    expect(acmSheetMaterialIssues(undefined)).toEqual([
      ACM_SHEET_ISSUE_VARIANT_MISSING,
      ACM_SHEET_ISSUE_ENVIRONMENT_MISSING,
    ]);
  });

  it("reports only the missing variant when the environment is set", () => {
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({ environment: "interior" }),
      ),
    ).toEqual([ACM_SHEET_ISSUE_VARIANT_MISSING]);
  });

  it("reports only the missing environment when the variant is set", () => {
    expect(
      acmSheetMaterialIssues(normalizeAcmSheetMaterial({ variant: "standard" })),
    ).toEqual([ACM_SHEET_ISSUE_ENVIRONMENT_MISSING]);
  });

  it("reports no issue for a complete non-mirror selection", () => {
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({ variant: "colorat", environment: "exterior" }),
      ),
    ).toEqual([]);
  });

  it("reports no issue for a mirror variant on interior", () => {
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({ variant: "oglinda_gold", environment: "interior" }),
      ),
    ).toEqual([]);
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({ variant: "oglinda_antracit", environment: "interior" }),
      ),
    ).toEqual([]);
  });

  it("fails closed for a mirror variant on exterior without a proven SKU", () => {
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({ variant: "oglinda_gold", environment: "exterior" }),
      ),
    ).toEqual([ACM_SHEET_ISSUE_MIRROR_EXTERIOR_SKU]);
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({
          variant: "oglinda_antracit",
          environment: "exterior",
          exterior_sku: "  ",
        }),
      ),
    ).toEqual([ACM_SHEET_ISSUE_MIRROR_EXTERIOR_SKU]);
  });

  it("clears the exterior mirror issue once a SKU is proven", () => {
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({
          variant: "oglinda_antracit",
          environment: "exterior",
          exterior_sku: "SKU-EXT-777",
        }),
      ),
    ).toEqual([]);
  });

  it("reports the unknown variant as missing — an unknown token never prices", () => {
    expect(
      acmSheetMaterialIssues(
        normalizeAcmSheetMaterial({ variant: "acm_unknown", environment: "exterior" }),
      ),
    ).toEqual([ACM_SHEET_ISSUE_VARIANT_MISSING]);
  });
});
