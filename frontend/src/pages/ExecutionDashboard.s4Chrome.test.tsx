import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ExecutionDashboard from "./ExecutionDashboard";

vi.mock("@/hooks/useDashboardStats", () => ({
  useDashboardStats: () => ({
    capacity: [],
    capacityModel: {
      minutesReadiness: { tasksMissingMinutes: 2 },
      batch04Gates: {
        maintenance: { availability: "gap" },
        assignment: { truthCount: 0, needsAssignmentCount: 4 },
      },
      preMaterializeChecklist: {
        blockerCount: 4,
        summary: "DEC-009 blocked — 4 capacity/route blockers still open.",
      },
    },
    operationalTruth: {
      calendarShiftUtilAvailable: false,
      capacityBatch04: {
        assignmentTruthCount: 0,
        needsAssignmentCount: 4,
        preMaterializeBlockerCount: 4,
        preMaterializeSummary: "DEC-009 blocked",
      },
    },
  }),
}));

const getExecutionDashboard = vi.fn();

vi.mock("@/api/execution", () => ({
  executionApi: {
    getExecutionDashboard: (...args: unknown[]) => getExecutionDashboard(...args),
  },
}));

describe("ExecutionDashboard S4 planning chrome", () => {
  beforeEach(() => {
    getExecutionDashboard.mockResolvedValue({ rows: [], total: 0 });
  });

  it("keeps implementation-state chrome inside collapsed technical details", async () => {
    render(
      <MemoryRouter>
        <ExecutionDashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Execuție" })).toBeInTheDocument();
    });

    const details = screen.getByTestId(
      "execution-planning-technical-details",
    ) as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(details.querySelector("summary")).toHaveTextContent(
      "Detalii tehnice planificare",
    );
    expect(screen.getByTestId("execution-capacity-strip").closest("details")).toBe(
      details,
    );
    expect(details.textContent).toMatch(/IMPLEMENTED_INACTIVE/);
    expect(details.textContent).toMatch(/DEC-009/);
    expect(details.textContent).toMatch(/necesită atribuire/);
    expect(details.textContent).not.toMatch(/NEEDS ASSIGNMENT TRUTH/);
  });
});
