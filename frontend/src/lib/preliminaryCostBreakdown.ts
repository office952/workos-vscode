import type { CostSimulationResponse } from "@/api/costSimulation";

export interface OperationLineDisplay {
  code: string;
  workcenter: string;
  lineTotal: number;
  rateBasis?: string;
}

export interface PreliminaryCostBreakdownDisplay {
  materials: number;
  /** CostEngine v2 `total_operation_cost` — all rated operations (hourly + linear). */
  includedOperations: number;
  /** Legacy field; v2 orchestrator always maps machine/workcenter split to labour_cost. */
  machineCostReported: number;
  partialTotal: number;
  currency: string;
  isBlocked: boolean;
  isPartial: boolean;
  blockedWorkcenterCount: number;
  includedOperationLines: OperationLineDisplay[];
  excludedOperationLines: OperationLineDisplay[];
}

type ComponentBreakdownRow = {
  operations_detail?: Array<{
    code?: string;
    workcenter?: string;
    line_total?: number;
    rate_basis?: string;
  }>;
};

function countWorkcenterBlockers(reasons: string[]): number {
  return reasons.filter((r) => r.includes("WORKCENTER_RATE_MISSING")).length;
}

function operationLinesFromBreakdown(
  components: unknown[]
): { included: OperationLineDisplay[]; excluded: OperationLineDisplay[] } {
  const included: OperationLineDisplay[] = [];
  const excluded: OperationLineDisplay[] = [];

  for (const raw of components) {
    if (!raw || typeof raw !== "object") continue;
    const comp = raw as ComponentBreakdownRow;
    for (const op of comp.operations_detail ?? []) {
      const line: OperationLineDisplay = {
        code: String(op.code ?? ""),
        workcenter: String(op.workcenter ?? ""),
        lineTotal: Number(op.line_total ?? 0),
        rateBasis: op.rate_basis ? String(op.rate_basis) : undefined,
      };
      if (line.lineTotal > 0) {
        included.push(line);
      } else {
        excluded.push(line);
      }
    }
  }

  return { included, excluded };
}

/**
 * Maps simulate-cost response fields for preliminary (v2) display.
 *
 * Backend mapping (quote_orchestrator._build_cost_result_from_v2):
 *   materials_cost  <- total_material_cost
 *   labour_cost     <- total_operation_cost (all operation types; not human-only)
 *   machine_cost    <- 0 (no separate v2 figure)
 *
 * When workcenter rates are missing, CostEngine adds errors but line_total stays 0,
 * so totals exclude unrated operations even though blockers are listed.
 */
export function parsePreliminaryCostBreakdown(
  result: CostSimulationResponse
): PreliminaryCostBreakdownDisplay {
  const cost = result.cost_result ?? {};
  const materials = Number(cost.materials_cost ?? 0);
  const includedOperations = Number(cost.labour_cost ?? 0);
  const machineCostReported = Number(cost.machine_cost ?? 0);
  const partialTotal = Number(cost.total_cost ?? 0);
  const currency = String(cost.currency ?? "RON");

  const blockedReasons = result.blocked_reasons ?? [];
  const blockedWorkcenterCount = countWorkcenterBlockers(blockedReasons);
  const isBlocked = result.status === "blocked" || blockedWorkcenterCount > 0;

  const { included, excluded } = operationLinesFromBreakdown(
    result.component_breakdown ?? []
  );

  const isPartial =
    isBlocked ||
    excluded.length > 0 ||
    (isBlocked && blockedWorkcenterCount > 0);

  return {
    materials,
    includedOperations,
    machineCostReported,
    partialTotal,
    currency,
    isBlocked,
    isPartial,
    blockedWorkcenterCount,
    includedOperationLines: included,
    excludedOperationLines: excluded,
  };
}
