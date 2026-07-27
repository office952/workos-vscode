import { describe, expect, it } from "vitest";
import { resolveExecutionNextAction } from "./executionNextAction";
import type { OperatorTaskTruthTask } from "@/api/operatorTaskTruth";
import type { PlannedTaskRow } from "@/api/execution";

function planTask(id: string, name: string): PlannedTaskRow {
  return {
    task_id: id,
    name,
    layer_id: "layer-1",
    process_type: "cut",
    machine_type: "cnc",
    estimated_time_minutes: 10,
    quantity: 1,
  };
}

function truth(
  id: string,
  label: string,
  runtime: Partial<OperatorTaskTruthTask["runtime"]>,
): OperatorTaskTruthTask {
  return {
    identity: {
      task_id: id,
      display_label: label,
      identity_source: "frozen_task_identity/v1",
    },
    runtime: {
      current_status: "assigned",
      is_startable: true,
      is_completeable: true,
      is_blocked: false,
      readiness_reasons: [],
      blocking_reasons: [],
      blocking_task_ids: [],
      blocking_tasks: [],
      production_release_blocked: false,
      production_release_status: "RELEASE_ALLOWED",
      production_release_scope: "ORDER_SCOPE",
      blocking_owner_decision_codes: [],
      ...runtime,
    },
    authority: {
      operational_source: "execution_reality",
      readiness_source: "task_readiness_service",
      production_release_source: "execution_owner_decision_production_release_service",
      legacy_fallback_active: false,
    },
  };
}

describe("resolveExecutionNextAction", () => {
  it("prefers in-progress Complete", () => {
    const action = resolveExecutionNextAction(
      [planTask("t1", "A"), planTask("t2", "B")],
      {
        tasks: [
          { task_id: "t1", started_at: "2026-01-01T00:00:00Z", ended_at: null },
        ],
      },
      {
        t1: truth("t1", "Vector Prep", {}),
      },
    );
    expect(action.kind).toBe("complete");
    if (action.kind === "complete") {
      expect(action.label).toBe("Vector Prep");
    }
  });

  it("surfaces next startable Start", () => {
    const action = resolveExecutionNextAction(
      [planTask("t1", "A"), planTask("t2", "B")],
      { tasks: [] },
      {
        t1: truth("t1", "Vector Prep", { is_startable: true }),
      },
    );
    expect(action.kind).toBe("start");
  });

  it("surfaces blocked-by when next task is blocked", () => {
    const action = resolveExecutionNextAction(
      [planTask("t1", "A")],
      { tasks: [] },
      {
        t1: truth("t1", "Montaj", {
          is_startable: false,
          is_blocked: true,
          blocking_tasks: [{ task_id: "t0", name: "Debitare" }],
        }),
      },
    );
    expect(action.kind).toBe("blocked");
    if (action.kind === "blocked") {
      expect(action.blockedBy).toContain("Debitare");
    }
  });
});
