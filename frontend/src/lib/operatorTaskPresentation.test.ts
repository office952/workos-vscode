import { describe, expect, it } from "vitest";
import type { OperatorTaskTruthTask, TaskIdentityTruth } from "@/api/operatorTaskTruth";
import {
  COMPONENT_ROLE_LABEL_FALLBACK,
  componentLabelFromBackend,
  diagnosticTaskKey,
  firstReadinessMessage,
  indexOperatorTaskTruth,
  isLegacyTaskIdentity,
  isPartialLogoIdentity,
  taskPrimaryLabel,
  taskTruthReadinessFromRuntime,
} from "./operatorTaskPresentation";

function identity(overrides: Partial<TaskIdentityTruth>): TaskIdentityTruth {
  return {
    task_id: "task-1",
    display_label: "Fallback label",
    identity_source: "frozen_task_identity/v1",
    ...overrides,
  };
}

function task(overrides: Partial<OperatorTaskTruthTask> = {}): OperatorTaskTruthTask {
  return {
    identity: identity({ display_label: "Vector Prep", component_role: "root_product" }),
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
    },
    authority: {
      operational_source: "execution_reality",
      readiness_source: "task_readiness_service",
      production_release_source: "execution_owner_decision_production_release_service",
      legacy_fallback_active: false,
    },
    ...overrides,
  };
}

describe("operatorTaskPresentation", () => {
  it("prefers backend component_label over frontend fallback", () => {
    const label = componentLabelFromBackend(
      identity({ component_label: "Panou montaj", component_role: "mounting_panel" }),
    );
    expect(label).toBe("Panou montaj");
  });

  it("maps root_product to Produs principal when backend omits label", () => {
    expect(
      componentLabelFromBackend(identity({ component_role: "root_product", component_label: null })),
    ).toBe(COMPONENT_ROLE_LABEL_FALLBACK.root_product);
  });

  it("maps mounting_panel fallback to Panou suport", () => {
    expect(
      componentLabelFromBackend(
        identity({ component_role: "mounting_panel", component_label: null }),
      ),
    ).toBe("Panou suport");
  });

  it("maps premount_structure distinctly", () => {
    expect(
      componentLabelFromBackend(
        identity({ component_role: "premount_structure", component_label: null }),
      ),
    ).toBe("Structură premontaj");
  });

  it("maps volum_aluminum fallback", () => {
    expect(
      componentLabelFromBackend(
        identity({ component_role: "volum_aluminum", component_label: null }),
      ),
    ).toBe("Cant / volum aluminiu");
  });

  it("detects partial logo identity via segment key", () => {
    const id = identity({
      component_role: "linked_segment",
      component_label: "Logo segment (logo_instance_001)",
      logo_segment_key: "logo_instance_001",
    });
    expect(isPartialLogoIdentity(id)).toBe(true);
    expect(componentLabelFromBackend(id)).toContain("Logo");
  });

  it("marks legacy identity explicitly", () => {
    const legacy = identity({
      identity_source: "legacy_plan_task",
      identity_classification: "LEGACY_NAME_BASED_IDENTITY",
      component_role: null,
    });
    expect(isLegacyTaskIdentity(legacy)).toBe(true);
    expect(componentLabelFromBackend(legacy)).toBe("Componentă legacy");
  });

  it("uses display_label as primary label, not deterministic key", () => {
    const id = identity({
      task_id: "node:root_product:TPL:vector_prep",
      deterministic_task_key: "node:root_product:TPL:vector_prep",
      display_label: "Vector Prep",
    });
    expect(taskPrimaryLabel(id)).toBe("Vector Prep");
    expect(taskPrimaryLabel(id)).not.toBe(diagnosticTaskKey(id));
  });

  it("indexes tasks by backend task_id for mutations", () => {
    const tasks = [
      task({
        identity: identity({ task_id: "node:root:op1", display_label: "Root op" }),
      }),
      task({
        identity: identity({
          task_id: "node:mount:op2",
          display_label: "Mount op",
          component_role: "mounting_panel",
          component_template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        }),
      }),
    ];
    const indexed = indexOperatorTaskTruth(tasks);
    expect(indexed["node:root:op1"].identity.display_label).toBe("Root op");
    expect(indexed["node:mount:op2"].identity.component_template_code).toBe(
      "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    );
  });

  it("derives readiness from backend runtime without inference", () => {
    const blocked = task({
      runtime: {
        current_status: "assigned",
        is_startable: false,
        is_completeable: false,
        is_blocked: true,
        readiness_label: "Așteaptă predecesor",
        readiness_reasons: [{ code: "predecessor", message: "Depinde de CNC" }],
        blocking_reasons: [],
        blocking_task_ids: ["prev"],
        blocking_tasks: [],
        production_release_blocked: false,
        production_release_status: "RELEASE_ALLOWED",
        production_release_scope: "ORDER_SCOPE",
        blocking_owner_decision_codes: [],
      },
    });
    const readiness = taskTruthReadinessFromRuntime(blocked.runtime);
    expect(readiness.is_startable).toBe(false);
    expect(firstReadinessMessage(readiness)).toBe("Depinde de CNC");
  });

  it("does not parse task names for identity", () => {
    const misleading = identity({
      display_label: "root_product mounting_panel",
      component_role: "mounting_panel",
      component_label: "Panou montaj",
      task_id: "friendly-name-only",
    });
    expect(componentLabelFromBackend(misleading)).toBe("Panou montaj");
    expect(taskPrimaryLabel(misleading)).toBe("root_product mounting_panel");
  });
});
