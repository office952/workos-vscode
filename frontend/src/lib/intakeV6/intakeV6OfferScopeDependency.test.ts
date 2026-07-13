import { describe, expect, it } from "vitest";

import {
  CODE_ELECTRICAL_LOAD_NOT_SOLD,
  CODE_LED_MOUNT_SURFACE_NOT_SOLD,
  isOfferScopeDependencyReady,
  previewSoldScopeDependencyValidation,
  readDependencyConfirmations,
  readPersistedDependencyValidation,
} from "./intakeV6OfferScopeDependency";

describe("intakeV6OfferScopeDependency", () => {
  it("skips dependency rules for full_product", () => {
    const result = previewSoldScopeDependencyValidation({
      mode: "full_product",
      soldModules: [],
    });
    expect(result.valid_for_confirmation).toBe(true);
    expect(result.confirmations_required).toEqual([]);
  });

  it("blocks empty subset", () => {
    const result = previewSoldScopeDependencyValidation({
      mode: "component_subset",
      soldModules: [],
    });
    expect(result.valid_for_save).toBe(false);
    expect(result.blockers[0]?.code).toBe("SOLD_MODULES_EMPTY");
  });

  it("requires LED mount confirmation for LIGHTING-only", () => {
    const result = previewSoldScopeDependencyValidation({
      mode: "component_subset",
      soldModules: ["LIGHTING"],
    });
    expect(result.missing_capabilities).toContain("LED_MOUNT_SURFACE");
    expect(result.confirmations_required.map((issue) => issue.code)).toEqual([
      CODE_LED_MOUNT_SURFACE_NOT_SOLD,
    ]);
    expect(result.valid_for_save).toBe(true);
    expect(result.valid_for_confirmation).toBe(false);
  });

  it("clears mount requirement when BACK is sold", () => {
    const result = previewSoldScopeDependencyValidation({
      mode: "component_subset",
      soldModules: ["BACK", "LIGHTING"],
    });
    expect(result.satisfied_capabilities).toContain("LED_MOUNT_SURFACE");
    expect(result.confirmations_required).toEqual([]);
    expect(result.valid_for_confirmation).toBe(true);
  });

  it("clears mount requirement when FACE+RETURN-CANT bundle is sold", () => {
    const result = previewSoldScopeDependencyValidation({
      mode: "component_subset",
      soldModules: ["FACE", "RETURN-CANT", "LIGHTING"],
    });
    expect(result.satisfied_capabilities).toContain("LED_MOUNT_SURFACE");
    expect(result.confirmations_required).toEqual([]);
  });

  it("requires electrical load confirmation when ELECTRICAL without LIGHTING", () => {
    const result = previewSoldScopeDependencyValidation({
      mode: "component_subset",
      soldModules: ["ELECTRICAL"],
    });
    expect(result.confirmations_required.map((issue) => issue.code)).toEqual([
      CODE_ELECTRICAL_LOAD_NOT_SOLD,
    ]);
    expect(result.warnings.some((issue) => issue.code === CODE_ELECTRICAL_LOAD_NOT_SOLD)).toBe(true);
  });

  it("accepts confirmed dependency codes from payload", () => {
    const payload = {
      offer_scope_confirmed: {
        dependency_confirmations: [CODE_LED_MOUNT_SURFACE_NOT_SOLD],
      },
      offer_scope_dependency_validation: {
        valid: true,
        valid_for_save: true,
        valid_for_confirmation: true,
        blockers: [],
        confirmations_required: [],
        warnings: [],
        satisfied_capabilities: [],
        missing_capabilities: [],
        resolved_calc_modules: [],
      },
    };
    expect(readDependencyConfirmations(payload)).toEqual(new Set([CODE_LED_MOUNT_SURFACE_NOT_SOLD]));
    expect(readPersistedDependencyValidation(payload)?.valid_for_confirmation).toBe(true);
    expect(isOfferScopeDependencyReady(payload)).toBe(true);
  });

  it("clears mount confirmation after operator acknowledges code", () => {
    const result = previewSoldScopeDependencyValidation({
      mode: "component_subset",
      soldModules: ["LIGHTING"],
      dependencyConfirmations: new Set([CODE_LED_MOUNT_SURFACE_NOT_SOLD]),
    });
    expect(result.confirmations_required).toEqual([]);
    expect(result.valid_for_confirmation).toBe(true);
  });
});
