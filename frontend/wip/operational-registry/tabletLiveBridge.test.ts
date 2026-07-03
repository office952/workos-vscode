/**
 * WIP — operational registry / tablet live bridge tests.
 * Kept under frontend/wip/ to avoid breaking npm run validate:frontend
 * while the operational registry build is incomplete.
 */
import { describe, expect, it } from "vitest";
import type { OperationResourceMapping } from "@/api/operationalRegistry";
import type { OperatorTask } from "@/lib/mockData";
import {
  filterLiveTasksForStation,
  mapLiveStatusToTabletStatus,
  mapOperatorTaskToTabletTask,
  normalizeOperationCode,
  taskBelongsToStation,
} from "@/lib/tabletLiveBridge";

function makeTask(overrides: Partial<OperatorTask> = {}): OperatorTask {
  return {
    id: "T-001",
    jobId: "JOB-0042",
    client: "Client Test",
    product: "Produs",
    operationCode: "print",
    operationName: "Print",
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

const mappings: OperationResourceMapping[] = [
  {
    operation_code: "colantare",
    required_skill_codes: ["SK_COLANT"],
    allowed_workcenter_codes: ["WC_VINYL_APPLICATION"],
    allowed_resource_codes: ["MCH-TOOL-VINYL"],
    notes: null,
  },
];

describe("tabletLiveBridge", () => {
  it("maps live EN statuses to RO tablet display statuses", () => {
    expect(mapLiveStatusToTabletStatus("assigned")).toBe("pregatit");
    expect(mapLiveStatusToTabletStatus("in_progress")).toBe("in_lucru");
    expect(mapLiveStatusToTabletStatus("blocked")).toBe("blocat");
    expect(mapLiveStatusToTabletStatus("done")).toBe("finalizat");
    expect(mapLiveStatusToTabletStatus("created")).toBe("in_coada");
  });

  it("normalizes operation codes for routing lookup", () => {
    expect(normalizeOperationCode("PRINT-SOLVENT")).toBe("print_solvent");
    expect(normalizeOperationCode("colantare")).toBe("colantare");
  });

  it("filters print tasks to print station via OPERATION_ROUTING", () => {
    const tasks = [makeTask({ operationCode: "print" }), makeTask({ id: "T-002", operationCode: "cnc_cutting" })];
    const filtered = filterLiveTasksForStation(tasks, "print", mappings);
    expect(filtered).toHaveLength(1);
    expect(filtered[0].id).toBe("T-001");
    expect(filtered[0].mappingConfirmed).toBe(true);
  });

  it("includes unmapped tasks with mappingConfirmed=false instead of hiding them", () => {
    const tasks = [makeTask({ operationCode: "unknown_op_xyz" })];
    const result = taskBelongsToStation(tasks[0], "print", mappings);
    expect(result.include).toBe(true);
    expect(result.mappingConfirmed).toBe(false);

    const mapped = mapOperatorTaskToTabletTask(tasks[0], mappings, "print");
    expect(mapped.mappingConfirmed).toBe(false);
    expect(mapped.routingExplanation).toContain("neconfirmat");
  });

  it("maps registry colantare to montaj_autocolant station (atelier, not field)", () => {
    const tasks = [makeTask({ operationCode: "colantare" })];
    const vinyl = filterLiveTasksForStation(tasks, "montaj_autocolant", mappings);
    const print = filterLiveTasksForStation(tasks, "print", mappings);
    expect(vinyl).toHaveLength(1);
    expect(print).toHaveLength(0);
  });

  it("maps cnc_routing canonical process type to CNC station", () => {
    const tasks = [makeTask({ operationCode: "cnc_routing", processId: "face_cnc_cut" })];
    const filtered = filterLiveTasksForStation(tasks, "cnc", mappings);
    expect(filtered).toHaveLength(1);
    expect(filtered[0].mappingConfirmed).toBe(true);
  });

  it("maps led_assembly canonical process type to LED station", () => {
    const tasks = [makeTask({ operationCode: "led_assembly", processId: "led_install_letters" })];
    const filtered = filterLiveTasksForStation(tasks, "led_electric", mappings);
    expect(filtered).toHaveLength(1);
  });

  it("preserves legacy tasks without employee_id for display", () => {
    const mapped = mapOperatorTaskToTabletTask(makeTask({ employeeId: null, employeeName: null }), mappings, "print");
    expect(mapped.employeeId).toBeNull();
    expect(mapped.employeeName).toBeNull();
    expect(mapped.assignedOperator).toBe("—");
    expect(mapped.isLive).toBe(true);
  });

  it("maps employee fields when present on live task", () => {
    const mapped = mapOperatorTaskToTabletTask(
      makeTask({ employeeId: 5, employeeName: "Octavian Test" }),
      mappings,
      "print"
    );
    expect(mapped.employeeId).toBe(5);
    expect(mapped.employeeName).toBe("Octavian Test");
    expect(mapped.assignedOperator).toBe("Octavian Test");
  });
});
