import { describe, expect, it } from "vitest";
import {
  hydrateMountingScopeFromFinishSetup,
  isMountingPreparationActive,
  isSiteInstallationSectionActive,
  mapLegacyMountingScope,
  normalizeMountingScope,
} from "./mountingScope";

describe("mountingScope foundation", () => {
  it("maps legacy no_mounting to none", () => {
    expect(mapLegacyMountingScope("no_mounting")).toBe("none");
  });

  it("maps legacy mounting_included to preparation_and_site_installation", () => {
    expect(mapLegacyMountingScope("mounting_included")).toBe("preparation_and_site_installation");
  });

  it("maps legacy mounting_external to preparation_only", () => {
    expect(mapLegacyMountingScope("mounting_external")).toBe("preparation_only");
  });

  it("hydrates missing scope from prep signals", () => {
    expect(
      normalizeMountingScope(null, {
        mounting_template_enabled: true,
        mounting_template_area_m2: 3,
      }),
    ).toBe("preparation_only");
  });

  it("hydrates missing scope without prep to none", () => {
    expect(normalizeMountingScope(null, {})).toBe("none");
  });

  it("activates prep only for prep scopes", () => {
    expect(isMountingPreparationActive("none")).toBe(false);
    expect(isMountingPreparationActive("preparation_only")).toBe(true);
    expect(isMountingPreparationActive("preparation_and_site_installation")).toBe(true);
  });

  it("activates site section only for full scope", () => {
    expect(isSiteInstallationSectionActive("preparation_only")).toBe(false);
    expect(isSiteInstallationSectionActive("preparation_and_site_installation")).toBe(true);
  });

  it("hydrates legacy mounting_included with site flag", () => {
    expect(
      hydrateMountingScopeFromFinishSetup({ mounting_scope: "mounting_included" }),
    ).toEqual({
      mounting_scope: "preparation_and_site_installation",
      site_installation_included: true,
    });
  });
});
