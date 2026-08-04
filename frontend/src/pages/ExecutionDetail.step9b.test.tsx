import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ExecutionDetail from "./ExecutionDetail";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { role: "admin" } }),
}));

vi.mock("@/hooks/useExecutionPlanV2Truth", () => ({
  useExecutionPlanV2Truth: () => ({
    preview: {
      status: "ready_for_owner_review",
      order_id: 880811,
      persist_status: "not_persisted",
      planned_tasks: [
        {
          task_key: "task:face_cnc",
          label: "Debitare",
          canonical_task_type: "CNC",
          source_operation_code: "face_cnc",
          estimated_minutes: null,
          depends_on_task_keys: [],
          warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
          machine_requirement: { workcenter: null },
        },
      ],
      planned_operations: [{ operation_code: "face_cnc", workcenter: null, priced: true }],
      dependencies: [],
      warnings: [],
      blockers: [],
    },
    audit: {
      mode: "audit_only",
      order_id: 880811,
      execution_plan_id: 22,
      materialization_status: "not_materialized",
      dry_run_status: "ready_with_warnings",
      planned_task_count: 1,
      operation_count: 1,
      operational_tasks_in_envelope_count: 0,
      materializable_task_candidates: [],
      non_operational_items: [],
      blockers: [],
      warnings: [],
      guards: { post_materialize_allowed: false, writes_database: false },
    },
    loading: false,
    previewError: null,
    auditError: null,
    refresh: vi.fn(),
  }),
}));

const getObservability = vi.fn();
const getAlerts = vi.fn();
const getExecutionPlan = vi.fn();
const getReality = vi.fn();

vi.mock("@/api/execution", () => ({
  executionApi: {
    getObservability: (...args: unknown[]) => getObservability(...args),
    getAlerts: (...args: unknown[]) => getAlerts(...args),
    getExecutionPlan: (...args: unknown[]) => getExecutionPlan(...args),
    getReality: (...args: unknown[]) => getReality(...args),
    generatePlan: vi.fn(),
    startTask: vi.fn(),
    endTask: vi.fn(),
  },
  PlanGenerationError: class PlanGenerationError extends Error {
    code: string;
    constructor(code: string) {
      super(code);
      this.code = code;
    }
  },
  RealityActionError: class RealityActionError extends Error {},
}));

vi.mock("@/components/execution/ExecutionClosurePanel", () => ({
  ExecutionClosurePanel: () => null,
}));
vi.mock("@/components/execution/PostJobTruthPanel", () => ({
  PostJobTruthPanel: () => null,
}));
vi.mock("@/components/execution-result/ResourceReadinessPanel", () => ({
  ResourceReadinessPanel: () => null,
}));
vi.mock("@/components/execution-result/EmployeeEligibilityPanel", () => ({
  EmployeeEligibilityPanel: () => null,
}));
vi.mock("@/components/execution-result/TechnicalDetails", () => ({
  TechnicalDetails: () => null,
}));
vi.mock("@/components/execution-result/CostsCompletenessPanel", () => ({
  CostsCompletenessPanel: () => null,
}));
vi.mock("@/components/execution-result/FinalResultPanel", () => ({
  FinalResultPanel: () => null,
}));
vi.mock("@/components/workos/ExecutionFlowStrip", () => ({
  default: () => null,
}));
vi.mock("@/components/workos/ExecutionFlowNextStep", () => ({
  default: () => null,
}));

describe("ExecutionDetail Step 9B", () => {
  beforeEach(() => {
    getObservability.mockResolvedValue({
      order_id: 880811,
      order_code: "ORD-880811",
      status: "WARNING",
      reasons: [],
      has_order: true,
      has_plan: true,
      has_reality: false,
      plan_total_estimated_minutes: null,
      reality_total_actual_minutes: null,
      delta_minutes: null,
      delta_pct: null,
      thresholds: {
        warning_time_delta_pct: null,
        critical_time_delta_pct: null,
        warning_time_delta_minutes: null,
        critical_time_delta_minutes: null,
        is_active: false,
        source: "test",
      },
      observed_at: new Date().toISOString(),
    });
    getAlerts.mockResolvedValue({ alerts: [] });
    getExecutionPlan.mockResolvedValue({
      id: 22,
      order_id: 880811,
      order_code: "ORD-880811",
      tasks: [{ task_id: "t1", name: "Draft task", estimated_time_minutes: null }],
      total_estimated_time_minutes: null,
    });
    getReality.mockResolvedValue(null);
  });

  it("mounts V2 truth panel and hides session Start when not materialized", async () => {
    render(
      <MemoryRouter initialEntries={["/execution/880811"]}>
        <Routes>
          <Route path="/execution/:order_id" element={<ExecutionDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("execution-plan-v2-truth-panel")).toBeInTheDocument();
    });
    expect(screen.getByTestId("execution-plan-v2-draft-badge")).toHaveTextContent(/DRAFT|AUDIT_ONLY/);
    expect(screen.getByTestId("execution-work-panel-sessions-blocked")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Start/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /Materializează/i })).toBeNull();
  });
});
