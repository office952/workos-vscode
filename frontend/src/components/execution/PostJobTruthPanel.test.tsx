/**
 * PostJobTruthPanel — render backend presence honestly.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { PostJobTruthPanel } from "@/components/execution/PostJobTruthPanel";
import { formatPresenceValue } from "@/api/postJobTruth";
import type { PostJobTruthResponse } from "@/api/postJobTruth";

const mockFetch = vi.fn();

vi.mock("@/api/postJobTruth", async () => {
  const actual = await vi.importActual<typeof import("@/api/postJobTruth")>(
    "@/api/postJobTruth",
  );
  return {
    ...actual,
    fetchPostJobTruth: (...args: unknown[]) => mockFetch(...args),
  };
});

function sampleTruth(
  overrides: Partial<PostJobTruthResponse> = {},
): PostJobTruthResponse {
  const base: PostJobTruthResponse = {
    contract_version: "post_job_truth_v1",
    order_id: 23099,
    order_code: "ORD-23099",
    baseline: {
      revenue_net: {
        value: 1500,
        presence: "present",
        unit: "RON",
        source: "order_snapshot_v2",
      },
      planned_internal_cost: {
        value: 620,
        presence: "present",
        unit: "RON",
      },
      currency: "RON",
      revenue_source: "order_snapshot_v2",
      has_snapshot_v2: true,
      snapshot_version: 1,
    },
    labor: {
      closed_minutes_total: { value: 90, presence: "present", unit: "min" },
      open_session_count: 0,
      session_count: 1,
      planned_minutes_total: { value: 40, presence: "present", unit: "min" },
      variance_minutes: { value: 50, presence: "present", unit: "min" },
      sessions: [
        {
          session_id: "ws-1",
          task_id: "t1",
          employee_id: 1,
          employee_name: "Ana",
          role: "primary",
          actual_minutes: 90,
          status: "ended",
          completeness: "complete",
        },
      ],
      monetary_cost: { value: null, presence: "excluded" },
      completeness: "complete",
    },
    materials: {
      lines: [
        {
          material_id: 9,
          material_name: "ACM",
          actual_deducted_quantity: {
            value: 2,
            presence: "present",
            unit: "sheet",
          },
          actual_known_internal_cost: {
            value: 25,
            presence: "present",
          },
          source: "stock_movements.consumption",
          completeness: "complete",
          valuation_method: "inventory_materials.unit_cost_at_read",
        },
      ],
      observed_row_count: 1,
      deducted_movement_count: 1,
      known_actual_cost_total: { value: 25, presence: "present" },
      valuation_method: "inventory_materials.unit_cost_at_read",
      completeness: "complete",
    },
    machines: {
      items: [
        {
          task_id: "t1",
          planned_machine_type: "cnc",
          status: "not_captured",
          note: "plan only",
        },
      ],
      completeness: "not_captured",
      note: "machine_usage_not_logged",
    },
    quantity: {
      tasks_planned: { value: 1, presence: "present" },
      tasks_completed: { value: 1, presence: "present" },
      progress_percent: { value: 100, presence: "present", unit: "%" },
      completed_quantity: { value: null, presence: "not_captured" },
      completeness: "partial",
    },
    reconciliation: {
      variances: [
        {
          dimension: "labor_minutes",
          planned_value: 40,
          actual_value: 90,
          absolute_variance: 50,
          percentage_variance: 125,
          unit: "min",
          status: "present",
          explanation_code: "minutes_plan_vs_closed_sessions",
        },
      ],
      operations: [
        {
          task_id: "t1",
          task_name: "CNC Face",
          planned_status: "planned",
          planned_minutes: { value: 40, presence: "present", unit: "min" },
          actual_minutes: { value: 90, presence: "present", unit: "min" },
          variance_minutes: { value: 50, presence: "present", unit: "min" },
          planned_quantity: { value: null, presence: "not_captured" },
          actual_quantity: { value: null, presence: "not_captured" },
          quantity_variance: { value: null, presence: "not_captured" },
          actual_status: "done",
          reconciliation_state: "variance",
          completeness: "present",
        },
        {
          task_id: "t2",
          task_name: "Prep",
          planned_status: "planned",
          planned_minutes: { value: 20, presence: "present", unit: "min" },
          actual_minutes: { value: null, presence: "not_captured" },
          variance_minutes: { value: null, presence: "not_captured" },
          planned_quantity: { value: null, presence: "not_captured" },
          actual_quantity: { value: null, presence: "not_captured" },
          quantity_variance: { value: null, presence: "not_captured" },
          actual_status: "assigned",
          reconciliation_state: "missing_actual",
          completeness: "not_captured",
        },
      ],
      summary: {
        matched_count: 0,
        partial_count: 0,
        missing_actual_count: 1,
        variance_count: 1,
        operations_total: 2,
      },
    },
    profitability: {
      revenue_net: { value: 1500, presence: "present" },
      planned_internal_cost: { value: 620, presence: "present" },
      known_actual_cost: { value: 25, presence: "present" },
      known_actual_margin: { value: 1475, presence: "present" },
      known_actual_margin_percent: { value: 98.3333, presence: "present" },
      cost_coverage_status: "PARTIAL",
      profitability_status: "PARTIAL",
      included_cost_components: ["materials"],
      excluded_cost_components: ["labor_money", "machine_money"],
      missing_actual_components: ["labor_money"],
      wording: [
        "Known actual cost includes materials only",
        "Partial profitability — labor monetary cost not included",
      ],
      false_final_profit_forbidden: true,
    },
    missing_data: [
      {
        code: "labor_money_excluded",
        dimension: "labor",
        message: "Labor monetary cost excluded",
        blocking_for_complete_profitability: true,
      },
    ],
    sources: {},
    retroactive_change_allowed: false,
    write_back_performed: false,
  };
  return { ...base, ...overrides };
}

describe("formatPresenceValue", () => {
  it("does not render missing as zero", () => {
    expect(
      formatPresenceValue({ value: null, presence: "missing" }),
    ).toBe("missing");
    expect(
      formatPresenceValue({ value: null, presence: "not_captured" }),
    ).toBe("not captured");
    expect(
      formatPresenceValue({ value: null, presence: "excluded" }),
    ).toBe("excluded");
    expect(
      formatPresenceValue({ value: 0, presence: "zero" }),
    ).toBe("0");
  });
});

describe("PostJobTruthPanel", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renders coverage, materials, minutes, and profitability warnings", async () => {
    mockFetch.mockResolvedValue(sampleTruth());
    render(<PostJobTruthPanel orderId={23099} />);

    await waitFor(() => {
      expect(screen.getByTestId("post-job-coverage-status")).toHaveTextContent(
        "PARTIAL",
      );
    });
    expect(screen.getByTestId("post-job-labor-minutes")).toHaveTextContent("90");
    expect(screen.getByTestId("post-job-material-cost")).toHaveTextContent("25.00");
    expect(screen.getByTestId("post-job-known-margin")).toHaveTextContent(
      "1475.00",
    );
    expect(screen.getByTestId("post-job-profit-status")).toHaveTextContent(
      "PARTIAL",
    );
    expect(screen.getByText(/labor monetary cost not included/i)).toBeTruthy();
    expect(screen.getByTestId("post-job-machines")).toHaveTextContent(
      "not_captured",
    );
    expect(screen.getByTestId("post-job-operations")).toHaveTextContent(
      "Plan vs execuție",
    );
    expect(screen.getByTestId("post-job-operations-summary")).toHaveTextContent(
      "varianță: 1",
    );
    expect(screen.getByTestId("post-job-op-state-t1")).toHaveTextContent("varianță");
    expect(screen.getByTestId("post-job-op-t2")).toHaveTextContent("neînregistrat");
    expect(screen.getByTestId("post-job-op-state-t2")).toHaveTextContent(
      "fără actual",
    );
  });

  it("shows loading then error states", async () => {
    mockFetch.mockRejectedValue(new Error("boom"));
    render(<PostJobTruthPanel orderId={1} />);
    expect(screen.getByTestId("post-job-loading")).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByTestId("post-job-error")).toHaveTextContent("boom");
    });
  });

  it("shows empty materials honestly when not captured", async () => {
    mockFetch.mockResolvedValue(
      sampleTruth({
        materials: {
          lines: [],
          observed_row_count: 0,
          deducted_movement_count: 0,
          known_actual_cost_total: { value: null, presence: "not_captured" },
          valuation_method: null,
          completeness: "not_captured",
        },
      }),
    );
    render(<PostJobTruthPanel orderId={2} />);
    await waitFor(() => {
      expect(screen.getByTestId("post-job-material-cost")).toHaveTextContent(
        "not captured",
      );
    });
  });
});
