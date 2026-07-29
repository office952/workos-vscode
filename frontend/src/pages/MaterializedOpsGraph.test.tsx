import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import MaterializedOpsGraph, { FIX_DEC009_MAT_01_ORDER_ID } from "./MaterializedOpsGraph";

vi.mock("@/hooks/useDashboardStats", () => ({
  useDashboardStats: () => ({
    capacityModel: {
      materialize: "BLOCKED",
      preMaterializeChecklist: {
        materialize: "BLOCKED",
        dec009: "A",
        summary: "DEC-009 blocked — capacity checklist (fixture visibility).",
        blockerCount: 1,
      },
    },
    operationalTruth: {
      calendarShiftUtilAvailable: false,
      capacityBatch04: {
        materialize: "BLOCKED",
        dec009: "A",
        preMaterializeSummary: "DEC-009 blocked",
      },
    },
    capacity: [],
  }),
}));

const getExecutionPlan = vi.fn();
const getExecutionPlanV2MaterializationAudit = vi.fn();
const getReality = vi.fn();

vi.mock("@/api/execution", () => ({
  executionApi: {
    getExecutionPlan: (...args: unknown[]) => getExecutionPlan(...args),
    getExecutionPlanV2MaterializationAudit: (...args: unknown[]) =>
      getExecutionPlanV2MaterializationAudit(...args),
    getReality: (...args: unknown[]) => getReality(...args),
  },
}));

function renderPage(path = "/execution/ops-graph") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/execution/ops-graph" element={<MaterializedOpsGraph />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("MaterializedOpsGraph", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getExecutionPlan.mockResolvedValue({
      id: 12,
      order_id: FIX_DEC009_MAT_01_ORDER_ID,
      order_code: "ORD-FIX-DEC009-MAT-01",
      snapshot_version: 1,
      total_estimated_time_minutes: 0,
      operational_tasks_count: 12,
      operational_tasks_materialized: true,
      plan_format: "v2_envelope",
      tasks: [
        {
          task_id: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
          name: "Pregatire vector",
          display_name: "Pregatire vector",
          layer_id: "v2",
          process_type: "file_preparation",
          machine_type: "PREPRESS",
          machine_code: null,
          workcenter: null,
          estimated_time_minutes: null,
          planning_minutes_source: null,
          assigned_employee_id: null,
          quantity: 1,
          sequence_index: 1,
          warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
          depends_on_task_ids: [],
          source_operation_code: "vector_prep",
        },
        {
          task_id: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:cnc_face_cut",
          name: "Taiere CNC",
          display_name: "Taiere CNC",
          layer_id: "v2",
          process_type: "cnc_routing",
          machine_type: "CNC",
          machine_code: null,
          workcenter: null,
          estimated_time_minutes: null,
          planning_minutes_source: null,
          assigned_employee_id: null,
          quantity: 1,
          sequence_index: 2,
          warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
          depends_on_task_ids: [
            "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
          ],
          source_operation_code: "face_cnc_cut",
        },
      ],
    });
    getExecutionPlanV2MaterializationAudit.mockResolvedValue({
      mode: "audit_only",
      order_id: FIX_DEC009_MAT_01_ORDER_ID,
      order_code: "ORD-FIX-DEC009-MAT-01",
      execution_plan_id: 12,
      source_snapshot_code: "OSN2-FIX-DEC009-MAT-01-973010",
      materialization_status: "already_materialized_in_envelope",
      dry_run_status: "already_materialized",
      planned_task_count: 12,
      operation_count: 23,
      operational_tasks_in_envelope_count: 12,
      materializable_task_candidates: [],
      blockers: [],
      warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
      activation_hash_preview: "15bde334c5c6eb4ad1c5cd6adceac1bb",
      guards: {
        mode: "audit_only",
        creates_sessions: false,
        employee_mobile_scope: false,
        post_materialize_allowed: false,
      },
    });
    getReality.mockResolvedValue(null);
  });

  it("loads fixture 973010 by default and shows read-only ops metrics", async () => {
    renderPage();

    await waitFor(() => {
      expect(getExecutionPlan).toHaveBeenCalledWith(FIX_DEC009_MAT_01_ORDER_ID);
    });

    expect(screen.getByTestId("materialized-ops-graph-page")).toBeInTheDocument();
    expect(screen.getByTestId("ops-graph-fixture-identity")).toHaveTextContent(
      "FIX-DEC009-MAT-01",
    );
    expect(screen.getByTestId("ops-graph-fixture-identity")).toHaveTextContent("973010");
    expect(screen.getByTestId("ops-graph-fixture-identity")).toHaveTextContent("plan_id=12");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("Operational tasks");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("12");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("Sessions");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("0");
    expect(screen.getByTestId("ops-graph-dec009-state")).toHaveTextContent("DEC-009=A");
    expect(screen.getByTestId("ops-graph-task-list")).toBeInTheDocument();
    expect(screen.getAllByText(/workcenter=null/i).length).toBeGreaterThan(0);
    expect(screen.getByTestId("ops-graph-readonly-footer")).toHaveTextContent(/Read-only/i);
    expect(screen.queryByRole("button", { name: /start/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /stop/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /assign/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /complete/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /materialize/i })).not.toBeInTheDocument();
    expect(screen.getByTestId("ops-graph-capacity-strip")).toHaveTextContent(
      /Employee Mobile:\s*out of scope/i,
    );
    expect(screen.queryByText(/Employee Mobile.*active/i)).not.toBeInTheDocument();
  });

  it("renders error state when plan GET fails", async () => {
    getExecutionPlan.mockRejectedValue(new Error("GET /execution/plan/973010 failed: 404"));
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("ops-graph-error")).toBeInTheDocument();
    });
    expect(screen.getByTestId("ops-graph-error")).toHaveTextContent(/404/);
  });
});
