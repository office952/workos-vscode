import { describe, expect, it } from "vitest";
import type { OperationResourceMapping } from "@/api/operationalRegistry";
import {
  formatOperationResolutionLabel,
  resolveMappingFromList,
  resolveOperationFromPool,
} from "./operationResolution";

const assemblyMapping: OperationResourceMapping = {
  operation_code: "assembly",
  required_skill_codes: ["SK_ASSEMBLY"],
  allowed_workcenter_codes: ["WC_ASSEMBLY"],
  allowed_resource_codes: ["WA-ASSEMBLY-01"],
  authorization_mode: "hybrid",
  default_resource_code: null,
  product_system_aliases: [
    "assembly_letters",
    "volumetric_letter_assembly",
    "painting",
  ],
  authorized_employee_ids: [9, 10, 11, 12],
  notes: null,
};

describe("operationResolution", () => {
  it("resolves volumetric_letter_assembly alias to assembly", () => {
    const result = resolveMappingFromList("volumetric_letter_assembly", [
      assemblyMapping,
    ]);
    expect(result.resolution).toBe("alias");
    expect(result.resolvedOperationCode).toBe("assembly");
    expect(result.matchedAlias).toBe("volumetric_letter_assembly");
    expect(result.mapping?.operation_code).toBe("assembly");
  });

  it("resolves face_cnc_cut alias to cnc_cutting mapping", () => {
    const cnc: OperationResourceMapping = {
      ...assemblyMapping,
      operation_code: "cnc_cutting",
      product_system_aliases: ["face_cnc_cut", "back_cut"],
    };
    const result = resolveMappingFromList("face_cnc_cut", [cnc]);
    expect(result.resolution).toBe("alias");
    expect(result.resolvedOperationCode).toBe("cnc_cutting");
  });

  it("returns missing for unknown operation code", () => {
    const result = resolveMappingFromList("unknown_op_xyz", [assemblyMapping]);
    expect(result.resolution).toBe("missing");
    expect(result.mapping).toBeNull();
    expect(result.warning).toMatch(/Mapping registry lipsă/);
  });

  it("formats label with arrow for alias resolution", () => {
    const label = formatOperationResolutionLabel({
      originalOperationCode: "volumetric_letter_assembly",
      resolvedOperationCode: "assembly",
      authorizationMode: "hybrid",
      eligibleCount: 4,
    });
    expect(label).toContain("volumetric_letter_assembly → assembly");
    expect(label).toContain("4 eligibili");
  });

  it("parses eligible pool not_found as missing soft", () => {
    const result = resolveOperationFromPool({
      operation_code: "unknown_op",
      resolved_operation_code: null,
      authorization_mode: "hybrid",
      resolution: "not_found",
      required_skill_codes: [],
      allowed_workcenter_codes: [],
      allowed_resource_codes: [],
      default_resource_code: null,
      authorized_employee_ids: [],
      items: [],
      total: 0,
    });
    expect(result.resolution).toBe("missing");
    expect(result.warning).toMatch(/guard soft/);
  });
});
