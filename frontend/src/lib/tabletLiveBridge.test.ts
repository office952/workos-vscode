import { describe, expect, it } from "vitest";
import type { OperationResourceMapping } from "@/api/operationalRegistry";
import type { OperatorTask } from "@/lib/mockData";
import { mapOperatorTaskToTabletTask } from "@/lib/tabletLiveBridge";

function makeTask(overrides: Partial<OperatorTask> = {}): OperatorTask {
  return {
    id: "T-001",
    jobId: "JOB-0042",
    client: "Client Test",
    product: "Produs",
    operationCode: "print",
    operationName: "Print solvent",
    machineName: "Epson",
    status: "assigned",
    assignee: "—",
    plannedDurationMin: 30,
    actualDurationMin: null,
    startedAt: null,
    targetEndAt: null,
    instructions: "Instrucțiuni",
    inputDependencies: [],
    expectedOutput: "OK",
    sequenceIndex: 1,
    ...overrides,
  };
}

const mappings: OperationResourceMapping[] = [];

describe("tabletLiveBridge routing presentation", () => {
  it("uses human operation and station names, not process_type or station id", () => {
    const mapped = mapOperatorTaskToTabletTask(makeTask(), mappings, "print");
    expect(mapped.mappingConfirmed).toBe(true);
    expect(mapped.routingExplanation).toBe("Operație Print solvent → Print");
    expect(mapped.routingExplanation).not.toMatch(/print_solvent|process_type|WC_/);
    expect(mapped.operationType).toBe("print");
  });

  it("keeps unconfirmed routing operational without exposing the raw code", () => {
    const mapped = mapOperatorTaskToTabletTask(
      makeTask({ operationCode: "unknown_op_xyz", operationName: "Pregătire" }),
      mappings,
      "print",
    );
    expect(mapped.mappingConfirmed).toBe(false);
    expect(mapped.routingExplanation).toBe("Rutare neconfirmată pentru Pregătire");
    expect(mapped.routingExplanation).not.toContain("unknown_op_xyz");
  });
});
