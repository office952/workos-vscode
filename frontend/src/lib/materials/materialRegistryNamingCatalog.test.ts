import { describe, expect, it } from "vitest";
import { getCatalogEntry, MATERIAL_NAMING_CATALOG } from "./materialRegistryNamingCatalog";

describe("materialRegistryNamingCatalog", () => {
  it("documents premount steel without usage in canonical name", () => {
    const entry = getCatalogEntry("MAT-PREMOUNT-BAR-STEEL");
    expect(entry?.canonicalName).toContain("Țeavă pătrată oțel");
    expect(entry?.canonicalName.toLowerCase()).not.toContain("premontaj");
  });

  it("flags MAT_ORACAL vs MAT-ORACAL namespace risk", () => {
    const dash = getCatalogEntry("MAT-ORACAL-651");
    const underscore = getCatalogEntry("MAT_ORACAL_651");
    expect(dash?.canonicalName).toContain("Oracal 651");
    expect(underscore?.legacyRisk).toMatch(/namespace/i);
  });

  it("catalog is non-empty", () => {
    expect(MATERIAL_NAMING_CATALOG.length).toBeGreaterThan(5);
  });
});
