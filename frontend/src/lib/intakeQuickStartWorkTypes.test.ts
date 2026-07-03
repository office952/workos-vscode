import { describe, expect, it } from "vitest";
import {
  formatMissingRequirementsMessage,
  getQuickStartMissingRequirements,
  resolveWorkTypeFamilyId,
} from "./intakeQuickStartWorkTypes";
import { UNRESOLVED_INTAKE_PRODUCT_FAMILY } from "./intakeProductFamilyDisplay";

const REGISTRY = [
  { id: 1, family_id: "litere_volumetrice", label: "Litere volumetrice", active: true },
  { id: 2, family_id: "servicii_montaj", label: "Servicii montaj", active: true },
];

describe("intakeQuickStartWorkTypes", () => {
  it("resolves volumetric family from work type id", () => {
    expect(resolveWorkTypeFamilyId("volumetric", REGISTRY)).toBe("litere_volumetrice");
  });

  it("resolves generic work type to empty unresolved product_family", () => {
    expect(resolveWorkTypeFamilyId("generic", REGISTRY)).toBe(UNRESOLVED_INTAKE_PRODUCT_FAMILY);
    expect(resolveWorkTypeFamilyId("generic", REGISTRY)).not.toBe("servicii_montaj");
  });

  it("accepts generic selection without requiring a registry family slug", () => {
    const missing = getQuickStartMissingRequirements({
      workTypeId: "generic",
      description: "Draft generic",
      channel: "email",
      registry: REGISTRY,
      registryLoading: false,
      registryError: null,
    });
    expect(missing).toEqual([]);
  });

  it("formats missing requirements for disabled create CTA", () => {
    const missing = getQuickStartMissingRequirements({
      workTypeId: null,
      description: "",
      channel: "email",
      registry: REGISTRY,
      registryLoading: false,
      registryError: null,
    });
    expect(formatMissingRequirementsMessage(missing)).toBe(
      "Completează: tip lucrare, descriere."
    );
  });
});
