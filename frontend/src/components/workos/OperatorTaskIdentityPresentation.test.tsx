import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { OperatorTaskTruthTask } from "@/api/operatorTaskTruth";
import { OperatorTaskIdentityPresentation } from "./OperatorTaskIdentityPresentation";

function buildTask(partial: Partial<OperatorTaskTruthTask["identity"]> & {
  runtime?: Partial<OperatorTaskTruthTask["runtime"]>;
}): OperatorTaskTruthTask {
  const { runtime: runtimePartial, ...identityPartial } = partial;
  return {
    identity: {
      task_id: "node:root_product:TPL:vector_prep",
      display_label: "Vector Prep",
      identity_source: "frozen_task_identity/v1",
      ...identityPartial,
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
      ...runtimePartial,
    },
    authority: {
      operational_source: "execution_reality",
      readiness_source: "task_readiness_service",
      production_release_source: "execution_owner_decision_production_release_service",
      legacy_fallback_active: false,
    },
  };
}

describe("OperatorTaskIdentityPresentation", () => {
  it("renders root task friendly label, not raw key", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          component_role: "root_product",
          component_label: "Produs principal",
          deterministic_task_key: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
        })}
      />,
    );
    expect(screen.getByTestId("operator-task-primary-label")).toHaveTextContent("Vector Prep");
    expect(screen.getByTestId("operator-task-component-label")).toHaveTextContent(
      "Produs principal",
    );
    expect(screen.queryByText(/node:root_product/)).toBeNull();
  });

  it("renders mounting Panou suport from backend label", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          display_label: "Montaj panou",
          component_role: "mounting_panel",
          component_label: "Panou montaj",
          component_template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
          source_operation_code: "mounting_assembly",
          task_id: "node:mounting:op",
          deterministic_task_key: "node:mounting:op",
        })}
      />,
    );
    expect(screen.getByTestId("operator-task-component-label")).toHaveTextContent("Panou montaj");
    expect(screen.getByTestId("operator-task-technical-details")).toBeTruthy();
    expect(screen.getByText(/mounting_assembly/)).toBeTruthy();
  });

  it("renders premount distinct label", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          display_label: "Premontaj structură",
          component_role: "premount_structure",
          component_label: "Structură premontaj",
        })}
      />,
    );
    expect(screen.getByTestId("operator-task-component-label")).toHaveTextContent(
      "Structură premontaj",
    );
  });

  it("renders volum/cant canonical label", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          display_label: "Cant aluminiu",
          component_role: "volum_aluminum",
          component_label: "Cant / volum aluminiu",
        })}
      />,
    );
    expect(screen.getByTestId("operator-task-component-label")).toHaveTextContent(
      "Cant / volum aluminiu",
    );
  });

  it("renders logo friendly label with segment detail", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          display_label: "Logo print",
          component_role: "linked_segment",
          component_label: "Logo segment (logo_instance_001)",
          logo_segment_key: "logo_instance_001",
        })}
      />,
    );
    expect(screen.getByTestId("operator-task-component-label")).toHaveTextContent(/Logo/);
    expect(screen.getByTestId("operator-task-logo-segment")).toHaveTextContent(
      "logo_instance_001",
    );
    expect(screen.queryByText("logo_instance_001", { selector: "[data-testid='operator-task-primary-label']" })).toBeNull();
  });

  it("marks legacy tasks explicitly", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          display_label: "Task vechi",
          identity_source: "legacy_plan_task",
          identity_classification: "LEGACY_NAME_BASED_IDENTITY",
          component_role: null,
          component_label: null,
        })}
      />,
    );
    expect(screen.getByText("Legacy")).toBeTruthy();
  });

  it("exposes raw key only in diagnostics", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          deterministic_task_key: "node:root_product:RAW",
        })}
        showDiagnostics
      />,
    );
    expect(screen.getByTestId("operator-task-primary-label")).toHaveTextContent("Vector Prep");
    expect(screen.getByTestId("operator-task-diagnostic-key")).toHaveTextContent(
      "node:root_product:RAW",
    );
  });

  it("uses backend is_startable for badge state", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          runtime: {
            is_startable: false,
            is_blocked: false,
            readiness_label: "Așteaptă materiale",
            readiness_reasons: [{ message: "Materiale lipsă" }],
          },
        })}
      />,
    );
    expect(screen.getByText("Nepregatit")).toBeTruthy();
    expect(screen.getByTestId("operator-task-readiness-reason")).toHaveTextContent(
      "Materiale lipsă",
    );
  });

  it("falls back without fabricating component role when truth absent", () => {
    render(
      <OperatorTaskIdentityPresentation
        fallbackOperationName="Operație necunoscută"
        fallbackTaskId="legacy-task-id"
      />,
    );
    expect(screen.getByText("Operație necunoscută")).toBeTruthy();
    expect(screen.getByTestId("operator-task-diagnostic-key")).toHaveTextContent(
      "legacy-task-id",
    );
  });

  it("shows production block badge separately from operational readiness", () => {
    render(
      <OperatorTaskIdentityPresentation
        truth={buildTask({
          runtime: {
            is_startable: false,
            is_blocked: false,
            production_release_blocked: true,
            blocking_owner_decision_codes: [
              "INTERNAL_SABLON_FOREX_COST",
              "INTERNAL_MONTAJ_RULE",
            ],
            readiness_reasons: [{ message: "Depinde de CNC" }],
          },
        })}
      />,
    );
    expect(screen.getByTestId("operator-task-production-blocked-badge")).toHaveTextContent(
      /Blocat pentru productie/i,
    );
    expect(screen.queryByTestId("operator-task-readiness-reason")).toBeNull();
  });
});
