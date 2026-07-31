import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import MaterializedOpsGraph, { FIX_DEC009_MAT_01_ORDER_ID } from "./MaterializedOpsGraph";
import type { OpsGraphTaskReadClarity } from "@/api/execution";

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

function clarityStub(overrides: Partial<OpsGraphTaskReadClarity["identity"]> & {
  status?: string;
  machineType?: string;
}): OpsGraphTaskReadClarity {
  return {
    version: "ops_graph_read_clarity/v1",
    identity: {
      task_id: "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
      short_code: "vector_prep",
      label: "Pregatire vector",
      ops_display_label: "Pregatire vector",
      label_clarity: {
        classification: "present",
        artifact_kind: "process_label",
        role: "template_provenance_not_client_price_not_capacity_unit",
        commercial_unit_phrasing_present: false,
        softened_for_ops_graph: false,
        note: "Process label from template/envelope provenance.",
      },
      process_type: "file_preparation",
      sequence_index: 1,
      ...overrides,
    },
    lifecycle: {
      value: overrides.status ?? "pending",
      classification: "present",
      role: "plan_lifecycle",
      display_label: "materialized_pending_execution",
      note: "plan lifecycle only",
      source_field: "operational_status",
    },
    quantity: { value: 1, classification: "present", role: "qty" },
    unit: {
      value: null,
      classification: "unknown",
      role: "unit",
      note: "unit null",
    },
    depends_on: {
      task_ids: [],
      short_codes: [],
      classification: "present",
    },
    machine_code: {
      value: null,
      classification: "owner_accepted_risk",
      role: "instance",
      owner_lock: "CAP-012",
    },
    machine_type: {
      value: overrides.machineType ?? "PREPRESS",
      classification: "present",
      role: "planning_requirement_class",
    },
    workcenter: {
      value: null,
      classification: "owner_accepted_risk",
      role: "wc",
      owner_lock: "F7_OD1",
    },
    estimated_time_minutes: {
      value: null,
      classification: "owner_accepted_risk",
      role: "minutes",
      owner_lock: "CAP-004",
    },
    planning_minutes_source: {
      value: null,
      classification: "owner_accepted_risk",
      role: "planning_source",
    },
    assigned_employee_id: {
      value: null,
      classification: "owner_accepted_risk",
      role: "assignee",
      owner_lock: "HR_OUT_OF_STAGE",
    },
    warnings: {
      raw_warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
      accepted_gap_codes: ["CAP-004", "CAP-012", "F7_OD1"],
      active_warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
    },
    display_hints: {
      machine_column: "machine_type class",
      machine_code_column: "machine_code instance",
      status_column: "lifecycle",
      collapse_accepted_gaps: true,
      do_not_coalesce_machine_code_from_machine_type: true,
      prefer_ops_display_label: true,
      label_column: "template_provenance_label",
    },
  };
}

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
      ops_graph_read_clarity: {
        version: "ops_graph_read_clarity/v1",
        operational_tasks_count: 12,
        sequence: {
          observed_indices: [1, 2],
          gaps: [],
          classification: "contiguous",
          note: "sequence_index 1, 2 (contiguous)",
        },
        counts_guard: { input_count: 12, output_count: 12 },
      },
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
          operational_status: "pending",
          quantity: 1,
          sequence_index: 1,
          warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
          depends_on_task_ids: [],
          source_operation_code: "vector_prep",
          read_clarity: clarityStub({}),
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
          operational_status: "pending",
          quantity: 1,
          sequence_index: 2,
          warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
          depends_on_task_ids: [
            "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
          ],
          source_operation_code: "face_cnc_cut",
          read_clarity: {
            ...clarityStub({
              short_code: "cnc_face_cut",
              label: "Taiere CNC",
              process_type: "cnc_routing",
              sequence_index: 2,
              machineType: "CNC",
            }),
            depends_on: {
              task_ids: [
                "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
              ],
              short_codes: ["vector_prep"],
              classification: "present",
            },
            identity: {
              ...clarityStub({}).identity,
              task_id:
                "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:cnc_face_cut",
              short_code: "cnc_face_cut",
              label: "Taiere CNC",
              process_type: "cnc_routing",
              sequence_index: 2,
            },
            machine_type: {
              value: "CNC",
              classification: "present",
              role: "planning_requirement_class",
            },
          },
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
    expect(screen.getByTestId("ops-graph-fixture-identity")).toHaveTextContent(
      /execution=not active/i,
    );
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("Ops tasks");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("12");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("Sessions");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("0");
    expect(screen.getByTestId("ops-graph-metrics")).toHaveTextContent("Actuals");
    expect(screen.getByTestId("ops-graph-dec009-state")).toHaveTextContent("DEC-009=A");
    expect(screen.getByTestId("ops-graph-dec009-state")).toHaveTextContent(
      /further POST blocked/i,
    );
    expect(screen.getByTestId("ops-graph-dec009-state")).toHaveTextContent(
      /already materialized/i,
    );
    expect(screen.getByTestId("ops-graph-task-list")).toBeInTheDocument();
    expect(screen.getByTestId("ops-graph-task-list")).toHaveTextContent(
      "materialized_pending_execution",
    );
    expect(screen.getByTestId("ops-graph-task-list")).toHaveTextContent("PREPRESS");
    expect(
      screen.getByTestId(
        "ops-graph-machine-code-node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep",
      ),
    ).toHaveTextContent("—");
    expect(screen.getByTestId("ops-graph-accepted-risks")).toHaveTextContent(
      /Accepted risks/i,
    );
    expect(screen.getByTestId("ops-graph-accepted-risks")).toHaveTextContent(
      /Track B read_clarity/i,
    );
    expect(screen.getByTestId("ops-graph-readonly-footer")).toHaveTextContent(/Read-only/i);
    expect(screen.queryByRole("button", { name: /start/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /stop/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /assign/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /complete/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /materialize/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/Employee Mobile/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Producție/i)).not.toBeInTheDocument();
  });

  it("renders error state when plan GET fails", async () => {
    getExecutionPlan.mockRejectedValue(new Error("GET /execution/plan/973010 failed: 404"));
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("ops-graph-error")).toBeInTheDocument();
    });
    expect(screen.getByTestId("ops-graph-error")).toHaveTextContent(/404/);
  });

  it("notes sequence gaps without inventing missing indexes", async () => {
    getExecutionPlan.mockResolvedValue({
      id: 12,
      order_id: FIX_DEC009_MAT_01_ORDER_ID,
      order_code: "ORD-FIX-DEC009-MAT-01",
      snapshot_version: 1,
      total_estimated_time_minutes: 0,
      operational_tasks_count: 2,
      operational_tasks_materialized: true,
      plan_format: "v2_envelope",
      ops_graph_read_clarity: {
        version: "ops_graph_read_clarity/v1",
        operational_tasks_count: 2,
        sequence: {
          observed_indices: [10, 13],
          gaps: [11, 12],
          classification: "gapped",
          note: "sequence_index 10, 13 · gaps 11, 12 absent (not invented)",
        },
      },
      tasks: [
        {
          task_id: "a:t1",
          name: "One",
          display_name: "One",
          layer_id: "v2",
          process_type: "x",
          machine_type: "M",
          machine_code: null,
          workcenter: null,
          estimated_time_minutes: null,
          planning_minutes_source: null,
          assigned_employee_id: null,
          operational_status: "pending",
          quantity: 1,
          sequence_index: 10,
          warnings: [],
          depends_on_task_ids: [],
          source_operation_code: "t1",
        },
        {
          task_id: "a:t2",
          name: "Two",
          display_name: "Two",
          layer_id: "v2",
          process_type: "x",
          machine_type: "M",
          machine_code: null,
          workcenter: null,
          estimated_time_minutes: null,
          planning_minutes_source: null,
          assigned_employee_id: null,
          operational_status: "pending",
          quantity: 1,
          sequence_index: 13,
          warnings: [],
          depends_on_task_ids: ["a:t1"],
          source_operation_code: "t2",
        },
      ],
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("ops-graph-sequence-note")).toBeInTheDocument();
    });
    expect(screen.getByTestId("ops-graph-sequence-note")).toHaveTextContent(/gaps 11, 12/);
    expect(screen.getByTestId("ops-graph-sequence-note")).toHaveTextContent(/not invented/);
  });

  it("OR-09 softens EUR/ml commercial phrasing without inventing unit or price", async () => {
    const commercialLabel = "Modelare cant profil — utilaj (EUR/ml serviciu)";
    const softLabel = "Modelare cant profil — utilaj";
    getExecutionPlan.mockResolvedValue({
      id: 12,
      order_id: FIX_DEC009_MAT_01_ORDER_ID,
      order_code: "ORD-FIX-DEC009-MAT-01",
      snapshot_version: 1,
      total_estimated_time_minutes: 0,
      operational_tasks_count: 1,
      operational_tasks_materialized: true,
      plan_format: "v2_envelope",
      ops_graph_read_clarity: {
        version: "ops_graph_read_clarity/v1",
        operational_tasks_count: 1,
        sequence: {
          observed_indices: [4],
          gaps: [],
          classification: "contiguous",
        },
        label_policy: {
          commercial_unit_phrasing_task_count: 1,
          note: "OR-09 display soften only",
        },
        counts_guard: { input_count: 1, output_count: 1 },
      },
      tasks: [
        {
          task_id:
            "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:return_profile_forming",
          name: commercialLabel,
          display_name: commercialLabel,
          layer_id: "v2",
          process_type: "edge_bending",
          machine_type: "RETURN_PROFILE_MACHINE_FORMING",
          machine_code: null,
          workcenter: null,
          estimated_time_minutes: null,
          planning_minutes_source: null,
          assigned_employee_id: null,
          operational_status: "pending",
          quantity: 1,
          sequence_index: 4,
          warnings: ["PLANNING_MINUTES_SOURCE_REQUIRED"],
          depends_on_task_ids: [],
          source_operation_code: "return_profile_forming",
          read_clarity: {
            ...clarityStub({
              short_code: "return_profile_forming",
              label: commercialLabel,
              ops_display_label: softLabel,
              label_clarity: {
                classification: "owner_accepted_risk",
                artifact_kind: "misleading_commercial_unit_phrasing",
                role: "template_provenance_not_client_price_not_capacity_unit",
                commercial_unit_phrasing_present: true,
                softened_for_ops_graph: true,
                note: "OR-09: template display_name embeds commercial unit phrasing",
                owner_lock: "PRODUCT_SYSTEM_TEMPLATE_LABEL",
              },
              process_type: "edge_bending",
              sequence_index: 4,
              machineType: "RETURN_PROFILE_MACHINE_FORMING",
            }),
          },
        },
      ],
    });

    renderPage();

    await waitFor(() => {
      expect(
        screen.getByTestId(
          "ops-graph-task-label-node:root_product:TPL-VOLUMETRIC-LETTERS_v2:return_profile_forming",
        ),
      ).toBeInTheDocument();
    });
    const labelEl = screen.getByTestId(
      "ops-graph-task-label-node:root_product:TPL-VOLUMETRIC-LETTERS_v2:return_profile_forming",
    );
    expect(labelEl).toHaveTextContent(softLabel);
    expect(labelEl).not.toHaveTextContent("EUR/ml");
    expect(labelEl).toHaveAttribute("data-label-provenance", commercialLabel);
    expect(screen.getByTestId("ops-graph-or09-label-note")).toHaveTextContent(/OR-09/);
    expect(screen.getByTestId("ops-graph-or09-label-note")).toHaveTextContent(
      /not client price/i,
    );
  });
});
