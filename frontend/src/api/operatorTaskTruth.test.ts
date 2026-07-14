import { describe, expect, it } from "vitest";
import {
  OPERATOR_TASK_TRUTH_VERSION,
  type OperatorTaskTruthResponse,
  taskTruthStartableFromBackend,
} from "./operatorTaskTruth";

describe("operatorTaskTruth contract", () => {
  it("exposes frozen identity fields on task shape", () => {
    const sample: OperatorTaskTruthResponse = {
      contract_version: OPERATOR_TASK_TRUTH_VERSION,
      order_id: 23099,
      readiness_authority: "FROZEN_ORDER_SNAPSHOT_V2",
      production_release_policy: "ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED",
      production_release_status: "RELEASE_ALLOWED",
      production_release_blocked: false,
      owner_decisions_summary: [],
      role_capabilities: {
        can_resolve_owner_decisions: false,
        can_view_internal_cost: false,
        can_view_owner_decision_notes: false,
      },
      tasks: [
        {
          identity: {
            task_id: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
            display_label: "Vector Prep",
            component_role: "root_product",
            component_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
            identity_source: "frozen_task_identity/v1",
          },
          runtime: {
            current_status: "in_progress",
            is_startable: false,
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
          },
          authority: {
            operational_source: "execution_reality",
            readiness_source: "task_readiness_service",
            production_release_source: "execution_owner_decision_production_release_service",
            legacy_fallback_active: false,
          },
        },
      ],
      generated_at: "2026-07-15T00:00:00Z",
      legacy_order: false,
    };

    expect(sample.tasks[0].identity.component_role).toBe("root_product");
    expect(sample.tasks[0].identity.identity_source).toBe("frozen_task_identity/v1");
    expect(taskTruthStartableFromBackend(sample.tasks[0])).toBe(false);
  });

  it("does not infer startability from task name", () => {
    const task = {
      identity: {
        task_id: "looks-startable",
        display_label: "Startable Label",
        identity_source: "legacy_plan_task" as const,
      },
      runtime: {
        current_status: "assigned",
        is_startable: false,
        is_completeable: false,
        is_blocked: true,
        readiness_reasons: [],
        blocking_reasons: [{ code: "predecessor_not_done" }],
        blocking_task_ids: ["prev"],
        blocking_tasks: [],
        production_release_blocked: false,
        production_release_status: "RELEASE_ALLOWED",
        production_release_scope: "ORDER_SCOPE",
        blocking_owner_decision_codes: [],
      },
      authority: {
        operational_source: "execution_reality",
        readiness_source: "task_readiness_service",
        production_release_source: "execution_owner_decision_production_release_service",
        legacy_fallback_active: true,
      },
    };
    expect(taskTruthStartableFromBackend(task)).toBe(false);
  });
});
