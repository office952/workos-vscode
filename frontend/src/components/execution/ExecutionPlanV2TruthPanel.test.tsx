import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ExecutionPlanV2TruthPanel } from "./ExecutionPlanV2TruthPanel";
import type {
  ExecutionPlanV2MaterializationAuditResponse,
  ExecutionPlanV2PreviewResponse,
} from "@/api/execution";

const preview: ExecutionPlanV2PreviewResponse = {
  status: "partial_missing_planning_minutes",
  order_id: 880811,
  persist_status: "not_persisted",
  planned_tasks: [
    {
      task_key: "task:face_cnc",
      label: "Debitare față",
      canonical_task_type: "CNC",
      source_operation_code: "face_cnc",
      estimated_minutes: null,
      depends_on_task_keys: [],
      warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
      machine_requirement: { workcenter: null },
    },
  ],
  planned_operations: [
    { operation_code: "face_cnc", label: "Față", workcenter: null, priced: true },
    { operation_code: "orphan_op", label: "Orphan", workcenter: "CNC", priced: true },
  ],
  dependencies: [],
  warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
  blockers: [],
};

const audit: ExecutionPlanV2MaterializationAuditResponse = {
  mode: "audit_only",
  order_id: 880811,
  execution_plan_id: 22,
  materialization_status: "not_materialized",
  dry_run_status: "ready_with_warnings",
  planned_task_count: 1,
  operation_count: 2,
  operational_tasks_in_envelope_count: 0,
  materializable_task_candidates: [],
  non_operational_items: [],
  blockers: [],
  warnings: [],
  guards: {
    post_materialize_allowed: false,
    writes_database: false,
  },
};

describe("ExecutionPlanV2TruthPanel", () => {
  it("renders draft / not-materialized honesty and gap badges without materialize actions", () => {
    const { container } = render(
      <ExecutionPlanV2TruthPanel preview={preview} audit={audit} auditError={null} loading={false} />,
    );

    expect(screen.getByTestId("execution-plan-v2-truth-panel")).toBeInTheDocument();
    expect(screen.getByTestId("execution-plan-v2-draft-badge")).toHaveTextContent("DRAFT");
    expect(screen.getByTestId("execution-plan-v2-not-materialized-badge")).toHaveTextContent("NOT_MATERIALIZED");
    expect(screen.getByTestId("execution-plan-v2-lifecycle-banner")).toHaveTextContent("nu au fost create");
    expect(screen.getByTestId("execution-plan-v2-gap-badges")).toHaveTextContent("MISSING_WORKCENTER");
    expect(screen.getByTestId("execution-plan-v2-gap-badges")).toHaveTextContent("MISSING_ESTIMATED_MINUTES");
    expect(screen.getByTestId("execution-plan-v2-orphan-ops")).toHaveTextContent("orphan_op");
    expect(screen.getByText(/Audit Only \/ Read-Only/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Materializează/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /Asignează/i })).toBeNull();
    expect(container.querySelector("button[data-testid='execution-plan-materialize']")).toBeNull();
    expect(container.querySelectorAll("button").length).toBeGreaterThan(0); // expand toggles only
  });
});
