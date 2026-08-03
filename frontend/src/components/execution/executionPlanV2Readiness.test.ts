import { describe, expect, it } from "vitest";
import {
  allowExecutionSessionActions,
  countMissingMinutes,
  countMissingWorkcenters,
  deriveOrphanOperations,
  hasOperationalTasksInEnvelope,
  planLifecycleLabel,
} from "./executionPlanV2Readiness";

describe("executionPlanV2Readiness", () => {
  it("derives orphan operations without inventing zeros for missing codes", () => {
    const orphans = deriveOrphanOperations(
      [
        { operation_code: "face_cnc" },
        { operation_code: "painting" },
        { operation_code: "readiness_gate" },
      ],
      [
        { source_operation_code: "face_cnc" },
        { source_operation_code: null },
      ],
    );
    expect(orphans.map((op) => op.operation_code)).toEqual(["painting", "readiness_gate"]);
  });

  it("counts missing workcenters and minutes honestly", () => {
    const tasks = [
      { machine_requirement: { workcenter: "CNC" }, estimated_minutes: 12 },
      { machine_requirement: { workcenter: null }, estimated_minutes: null },
      { machine_requirement: undefined, estimated_minutes: undefined },
    ];
    expect(countMissingWorkcenters(tasks)).toBe(2);
    expect(countMissingMinutes(tasks)).toBe(2);
  });

  it("labels draft / not materialized when envelope has no operational tasks", () => {
    expect(hasOperationalTasksInEnvelope({ operational_tasks_in_envelope_count: 0 })).toBe(false);
    const labels = planLifecycleLabel({
      hasPreview: true,
      audit: { execution_plan_id: 22, operational_tasks_in_envelope_count: 0 },
      persistStatus: "not_persisted",
    });
    expect(labels.draftLabel).toContain("draft");
    expect(labels.materializationLabel).toBe("NOT_MATERIALIZED");
    expect(labels.nextStepLabel).toContain("nu au fost create");
  });

  it("keeps sessions frozen when ops exist but post_materialize_allowed is false", () => {
    expect(
      allowExecutionSessionActions({
        operational_tasks_in_envelope_count: 5,
        guards: { post_materialize_allowed: false },
      }),
    ).toBe(false);
    expect(
      allowExecutionSessionActions({
        operational_tasks_in_envelope_count: 5,
        guards: { post_materialize_allowed: true },
      }),
    ).toBe(true);
  });
});
