import { describe, expect, it } from "vitest";
import {
  CANONICAL_FINISH_ENUM_MAP,
  CANONICAL_FINISH_RETIRED_PATHS,
  getCanonicalFinishEntriesByOwner,
  getCanonicalFinishEntriesBySurface,
  getCanonicalFinishEntry,
  isRetiredFinishTruthPath,
} from "./canonicalFinishEnumMap";

const REQUIRED_CANONICAL_IDS = [
  "cant_stock_color",
  "cant_oracal_wrap",
  "cant_ral_paint",
  "cant_ral_minimum_policy",
  "face_oracal_641",
  "face_oracal_651",
  "face_oracal_8500",
  "face_print_laminate",
  "artwork_print_laminate",
  "artwork_print_only",
  "artwork_cut_vinyl",
  "artwork_translucent_vinyl",
] as const;

describe("canonicalFinishEnumMap", () => {
  it("includes all required canonical IDs", () => {
    for (const id of REQUIRED_CANONICAL_IDS) {
      expect(getCanonicalFinishEntry(id)).not.toBeNull();
    }
    expect(CANONICAL_FINISH_ENUM_MAP.length).toBeGreaterThanOrEqual(REQUIRED_CANONICAL_IDS.length);
  });

  it("assigns cant entries to RETURN-CANT and forbids FINISH", () => {
    const cantEntries = getCanonicalFinishEntriesBySurface("cant");
    expect(cantEntries.length).toBeGreaterThanOrEqual(4);
    for (const entry of cantEntries) {
      expect(entry.ownerComponent).toBe("RETURN-CANT");
      expect(entry.forbiddenOwners).toContain("FINISH");
    }
  });

  it("assigns face/artwork application entries to FINISH and forbids RETURN-CANT", () => {
    const finishOwned = getCanonicalFinishEntriesByOwner("FINISH");
    expect(finishOwned.length).toBeGreaterThan(0);
    for (const entry of finishOwned) {
      expect(entry.forbiddenOwners).toContain("RETURN-CANT");
    }
  });

  it("assigns face_none_or_material_default to FACE only", () => {
    const faceNone = getCanonicalFinishEntry("face_none_or_material_default");
    expect(faceNone?.ownerComponent).toBe("FACE");
    expect(faceNone?.activationStatus).toBe("blocked");
  });

  it("defines RAL minimum as owner policy not Pricing Registry", () => {
    const minimum = getCanonicalFinishEntry("cant_ral_minimum_policy")!;
    expect(minimum.pricingSource).toBeNull();
    expect(minimum.commercialPolicySource).toBe("cpp_owner_policy");
    expect(minimum.quantityBasis).toBe("owner_policy");
    expect(minimum.forbiddenOwners).toContain("FINISH");
    expect(minimum.notesRo).toMatch(/NOT Pricing Registry/i);
    expect(minimum.notesRo).toMatch(/fără conversie automată/i);
  });

  it("defines cant RAL paint with depth-scoped material keys and cant labor", () => {
    const ral = getCanonicalFinishEntry("cant_ral_paint")!;
    expect(ral.ownerComponent).toBe("RETURN-CANT");
    expect(ral.pricingMaterialKeys).toEqual([
      "MAT-VOPSEA-RAL-CANT-30MM",
      "MAT-VOPSEA-RAL-CANT-60MM",
      "MAT-VOPSEA-RAL-CANT-80MM",
      "MAT-VOPSEA-RAL-CANT-100MM",
    ]);
    expect(ral.pricingLaborKeys).toEqual(["RETURN_CANT_RAL_PAINT_LABOR"]);
  });

  it("defines face Oracal entries with FACE_VINYL labor and mp_face_area", () => {
    for (const id of ["face_oracal_641", "face_oracal_651", "face_oracal_8500"] as const) {
      const entry = getCanonicalFinishEntry(id)!;
      expect(entry.ownerComponent).toBe("FINISH");
      expect(entry.quantityBasis).toBe("mp_face_area");
      expect(entry.pricingLaborKeys).toEqual(["FACE_VINYL_APPLICATION_LABOR"]);
    }
    expect(getCanonicalFinishEntry("face_oracal_641")?.pricingMaterialKeys).toEqual(["MAT-ORACAL-641"]);
    expect(getCanonicalFinishEntry("face_oracal_651")?.pricingMaterialKeys).toEqual(["MAT-ORACAL-651"]);
    expect(getCanonicalFinishEntry("face_oracal_8500")?.pricingMaterialKeys).toEqual(["MAT-ORACAL-8500"]);
  });

  it("defines cant Oracal wrap with cant vinyl labor and ml_perimeter_x_width", () => {
    const cantOracal = getCanonicalFinishEntry("cant_oracal_wrap")!;
    expect(cantOracal.ownerComponent).toBe("RETURN-CANT");
    expect(cantOracal.pricingMaterialKeys).toEqual(["MAT-ORACAL-641", "MAT-ORACAL-651"]);
    expect(cantOracal.pricingLaborKeys).toEqual(["RETURN_CANT_VINYL_APPLICATION_LABOR"]);
    expect(cantOracal.quantityBasis).toBe("ml_perimeter_x_width");
  });

  it("does not use generic finish paths as canonical truth path prefixes", () => {
    const retiredPrefixes = [
      "product.components.finish.oracal_code",
      "product.components.finish.ral_code",
      "product.components.finish.stock_color",
      "product.components.finish.type",
    ];
    for (const entry of CANONICAL_FINISH_ENUM_MAP) {
      for (const retired of retiredPrefixes) {
        expect(entry.truthPathPrefix).not.toBe(retired);
        expect(entry.truthPathPrefix.startsWith(`${retired}.`)).toBe(false);
      }
    }
  });

  it("lists four retired generic paths with replacements", () => {
    expect(CANONICAL_FINISH_RETIRED_PATHS).toHaveLength(4);
    const paths = CANONICAL_FINISH_RETIRED_PATHS.map((e) => e.retiredPath);
    expect(paths).toContain("product.components.finish.oracal_code");
    expect(paths).toContain("product.components.finish.ral_code");
    expect(paths).toContain("product.components.finish.stock_color");
    expect(paths).toContain("product.components.finish.type");
    for (const retired of CANONICAL_FINISH_RETIRED_PATHS) {
      expect(retired.replacementPaths.length).toBeGreaterThan(0);
      expect(retired.retirementStatus).toBe("deprecated_conceptual");
    }
  });

  it("detects retired paths via isRetiredFinishTruthPath", () => {
    expect(isRetiredFinishTruthPath("product.components.finish.oracal_code")).toBe(true);
    expect(isRetiredFinishTruthPath("product.components.return_cant.finish.vinyl")).toBe(false);
  });
});
