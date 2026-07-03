import { describe, expect, it } from "vitest";
import type { CostSimulationResponse } from "@/api/costSimulation";
import { parsePreliminaryCostBreakdown } from "./preliminaryCostBreakdown";

function mockResult(
  overrides: Partial<CostSimulationResponse> = {}
): CostSimulationResponse {
  return {
    simulation_id: null,
    persisted: false,
    template_id: 1,
    template_code: "TPL-VOLUMETRIC-LETTERS",
    cost_engine_version: "v2",
    readiness: { ready_for_quote: false, blockers: [], warnings: [] },
    cost_result: {
      materials_cost: 490.61,
      labour_cost: 216,
      machine_cost: 0,
      total_cost: 706.61,
      currency: "RON",
      is_valid: false,
    },
    component_breakdown: [
      {
        operations_detail: [
          {
            code: "return_profile_forming",
            workcenter: "RETURN_PROFILE_MACHINE_FORMING",
            line_total: 90,
            rate_basis: "per_linear_meter",
          },
          {
            code: "return_profile_bonding",
            workcenter: "RETURN_PROFILE_FACE_BONDING",
            line_total: 126,
            rate_basis: "per_linear_meter",
          },
          {
            code: "mounting_template_cnc_cut",
            workcenter: "CNC_ROUTER",
            line_total: 0,
            rate_basis: "per_hour",
          },
        ],
      },
    ],
    warnings: [],
    blockers: [],
    status: "blocked",
    blocked_reasons: [
      "cost_invalid:WORKCENTER_RATE_MISSING@components[0].operations[1]:no rate configuration for workcenter='CNC_ROUTER'",
    ],
    trace: {
      source: "product-system-cost-simulation",
      no_persist: true,
      used_template_snapshot: true,
      used_costengine_formulas: true,
      changed_entities: [],
    },
    ...overrides,
  };
}

describe("parsePreliminaryCostBreakdown", () => {
  it("maps v2 labour_cost to included operations total", () => {
    const display = parsePreliminaryCostBreakdown(mockResult());
    expect(display.includedOperations).toBe(216);
    expect(display.materials).toBe(490.61);
    expect(display.partialTotal).toBe(706.61);
    expect(display.machineCostReported).toBe(0);
  });

  it("marks partial when workcenter blockers exist", () => {
    const display = parsePreliminaryCostBreakdown(mockResult());
    expect(display.isBlocked).toBe(true);
    expect(display.isPartial).toBe(true);
    expect(display.blockedWorkcenterCount).toBe(1);
    expect(display.includedOperationLines).toHaveLength(2);
    expect(display.excludedOperationLines).toHaveLength(1);
    expect(display.excludedOperationLines[0].workcenter).toBe("CNC_ROUTER");
  });
});
