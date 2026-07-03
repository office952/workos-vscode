import { describe, expect, it } from "vitest";
import { LAYER_ROLE_OPTIONS } from "@/lib/svgAnalyzer";
import { INTAKE_V6_LAYER_ROLE_OPTIONS } from "./intakeV6LayerRoleOptions";

describe("INTAKE_V6_LAYER_ROLE_OPTIONS compat contract", () => {
  it("renames return layer role to Cant / volum for operators", () => {
    const returnOpt = INTAKE_V6_LAYER_ROLE_OPTIONS.find((opt) => opt.value === "return");
    expect(returnOpt?.label).toBe("Cant / volum");
    expect(returnOpt?.label).not.toContain("Return");
  });

  it("does not expose Return / cant in any option label", () => {
    for (const option of INTAKE_V6_LAYER_ROLE_OPTIONS) {
      expect(option.label).not.toMatch(/Return\s*\/\s*cant/i);
    }
  });

  it("keeps the same role values as the shared catalog", () => {
    expect(INTAKE_V6_LAYER_ROLE_OPTIONS.map((option) => option.value)).toEqual(
      LAYER_ROLE_OPTIONS.map((option) => option.value),
    );
  });
});