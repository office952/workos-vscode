import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import MachineRunsListPage from "./MachineRunsListPage";

const listMachineRuns = vi.fn();
const canMock = vi.fn();

vi.mock("@/api/machineRuns", () => ({
  listMachineRuns: (...args: unknown[]) => listMachineRuns(...args),
  MachineRunRequestError: class MachineRunRequestError extends Error {
    code = "request_failed";
    httpStatus = 500;
  },
}));

vi.mock("@/hooks/useCurrentPermissions", () => ({
  useCurrentPermissions: () => ({
    role: "admin",
    can: (perm: string) => canMock(perm),
  }),
}));

describe("MachineRunsListPage", () => {
  beforeEach(() => {
    listMachineRuns.mockReset();
    canMock.mockReset();
    canMock.mockImplementation((p: string) => p === "execution.machine_run.read");
  });

  it("loads open_only list by default and shows empty state", async () => {
    listMachineRuns.mockResolvedValue({ items: [], count: 0 });
    render(
      <MemoryRouter>
        <MachineRunsListPage />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("machine-runs-list-page")).toBeInTheDocument();
    await waitFor(() => {
      expect(listMachineRuns).toHaveBeenCalledWith({ open_only: true });
    });
    expect(screen.getByTestId("machine-runs-empty")).toHaveTextContent(
      "Nu există rulări de utilaj active.",
    );
    expect(screen.getByTestId("machine-runs-create-deferred")).toBeInTheDocument();
  });

  it("renders list rows with status copy and multi-order badge", async () => {
    listMachineRuns.mockResolvedValue({
      count: 1,
      items: [
        {
          machine_run_id: 7,
          status: "RESERVED",
          version: 2,
          machine_id: 3,
          machine_code: "CNC-1",
          machine_name: "Router CNC",
          reservation_id: 9,
          reservation_status: "RESERVED",
          reservation_version: 2,
          reservation_start: "2026-08-09T08:00:00Z",
          reservation_end: "2026-08-09T10:00:00Z",
          timezone: "Europe/Bucharest",
          active_participant_count: 2,
          total_participant_count: 2,
          execution_plan_ids: [1, 2],
          order_ids: [100, 101],
          started_at: null,
          completed_at: null,
          created_at: "2026-08-09T07:00:00Z",
          updated_at: "2026-08-09T07:00:00Z",
        },
      ],
    });

    render(
      <MemoryRouter>
        <MachineRunsListPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("machine-run-row-7")).toBeInTheDocument();
    });
    expect(screen.getByText("Rezervat")).toBeInTheDocument();
    expect(screen.getByText("Router CNC")).toBeInTheDocument();
    expect(screen.getByText("Mai multe comenzi")).toBeInTheDocument();
    expect(screen.getByText("Pornește utilajul")).toBeInTheDocument();
  });
});
