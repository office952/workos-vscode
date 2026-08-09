import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import MachineRunDetailPage from "./MachineRunDetailPage";
import type { MachineRunDetail } from "@/api/machineRuns";

const getMachineRun = vi.fn();
const startMachineRun = vi.fn();
const canMock = vi.fn();

function heldDetail(overrides: Partial<MachineRunDetail> = {}): MachineRunDetail {
  return {
    machine_run_id: 12,
    status: "HELD",
    version: 1,
    timezone: "Europe/Bucharest",
    started_at: null,
    completed_at: null,
    actual_runtime_seconds: null,
    created_at: "2026-08-09T07:00:00Z",
    updated_at: "2026-08-09T07:00:00Z",
    created_by: "admin",
    updated_by: "admin",
    machine: {
      machine_id: 3,
      machine_code: "CNC-1",
      name: "Router CNC",
      is_active: true,
      is_available: true,
      operational_status: "idle",
      capabilities: ["cnc_cut"],
    },
    reservation: {
      reservation_id: 9,
      status: "HELD",
      version: 1,
      machine_id: 3,
      reservation_start: "2026-08-09T08:00:00Z",
      reservation_end: "2026-08-09T10:00:00Z",
      timezone: "Europe/Bucharest",
    },
    participants: [
      {
        participant_id: 1,
        status: "ACTIVE",
        execution_plan_id: 21,
        task_key: "FACE_A",
        order_id: 100,
        operation_code: "CNC",
        workcenter: "CNC",
        machine_capability_code: "cnc_cut",
        batch_eligible: true,
        added_at: null,
        added_by: null,
        removed_at: null,
        removed_by: null,
      },
      {
        participant_id: 2,
        status: "ACTIVE",
        execution_plan_id: 22,
        task_key: "FACE_B",
        order_id: 101,
        operation_code: "CNC",
        workcenter: "CNC",
        machine_capability_code: "cnc_cut",
        batch_eligible: true,
        added_at: null,
        added_by: null,
        removed_at: null,
        removed_by: null,
      },
    ],
    execution_plan_ids: [21, 22],
    order_ids: [100, 101],
    active_participant_count: 2,
    total_participant_count: 2,
    ...overrides,
  };
}

vi.mock("@/api/machineRuns", async () => {
  const actual = await vi.importActual<typeof import("@/api/machineRuns")>(
    "@/api/machineRuns",
  );
  return {
    ...actual,
    getMachineRun: (...args: unknown[]) => getMachineRun(...args),
    startMachineRun: (...args: unknown[]) => startMachineRun(...args),
    confirmMachineRun: vi.fn(),
    completeMachineRun: vi.fn(),
    releaseMachineRun: vi.fn(),
    cancelMachineRun: vi.fn(),
    rescheduleMachineRun: vi.fn(),
    removeMachineRunParticipant: vi.fn(),
    listMachineRunAddCandidates: vi.fn().mockResolvedValue({
      context: "add",
      machine_id: 3,
      machine_run_id: 12,
      machine_code: "CNC-1",
      machine_name: "Router CNC",
      required_capability: null,
      mutation_allowed: true,
      reason_code: null,
      message: null,
      items: [],
      count: 0,
    }),
    addMachineRunParticipant: vi.fn(),
  };
});

vi.mock("@/components/machine-run/MachineRunAddParticipantPanel", () => ({
  MachineRunAddParticipantPanel: ({
    visible,
  }: {
    visible: boolean;
  }) =>
    visible ? <div data-testid="machine-run-add-panel" /> : null,
}));

vi.mock("@/hooks/useCurrentPermissions", () => ({
  useCurrentPermissions: () => ({
    role: "manager",
    can: (perm: string) => canMock(perm),
  }),
}));

function renderDetail(id = "12") {
  return render(
    <MemoryRouter initialEntries={[`/execution/machine-runs/${id}`]}>
      <Routes>
        <Route path="/execution/machine-runs/:machineRunId" element={<MachineRunDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("MachineRunDetailPage", () => {
  beforeEach(() => {
    getMachineRun.mockReset();
    startMachineRun.mockReset();
    canMock.mockReset();
    canMock.mockImplementation(() => true);
  });

  it("renders HELD detail with Confirmă and ADD panel for manage", async () => {
    getMachineRun.mockResolvedValue(heldDetail());
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-status")).toHaveTextContent("Grupare");
    });
    expect(screen.getByTestId("machine-run-action-confirm")).toHaveTextContent(
      "Confirmă rularea",
    );
    expect(screen.getByTestId("machine-run-add-panel")).toBeInTheDocument();
    expect(screen.getByText("Mai multe comenzi")).toBeInTheDocument();
  });

  it("hides ADD panel when manage permission is absent", async () => {
    canMock.mockImplementation(
      (p: string) => p === "execution.machine_run.read" || p === "execution.machine_run.execute",
    );
    getMachineRun.mockResolvedValue(heldDetail());
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-status")).toHaveTextContent("Grupare");
    });
    expect(screen.queryByTestId("machine-run-add-panel")).not.toBeInTheDocument();
  });

  it("COMPLETED shows release primary + reservation hint", async () => {
    getMachineRun.mockResolvedValue(
      heldDetail({
        status: "COMPLETED",
        version: 4,
        reservation: {
          reservation_id: 9,
          status: "RESERVED",
          version: 2,
          machine_id: 3,
          reservation_start: "2026-08-09T08:00:00Z",
          reservation_end: "2026-08-09T10:00:00Z",
          timezone: "Europe/Bucharest",
        },
        started_at: "2026-08-09T08:05:00Z",
        completed_at: "2026-08-09T09:00:00Z",
        actual_runtime_seconds: 3300,
      }),
    );
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-status")).toHaveTextContent(
        "Lucru utilaj finalizat",
      );
    });
    expect(screen.getByTestId("machine-run-action-release")).toBeInTheDocument();
    expect(screen.getByTestId("machine-run-complete-release-hint")).toHaveTextContent(
      "rămâne rezervat",
    );
  });

  it("command path waits for server then refetches detail", async () => {
    getMachineRun
      .mockResolvedValueOnce(
        heldDetail({
          status: "RESERVED",
          version: 2,
          reservation: {
            reservation_id: 9,
            status: "RESERVED",
            version: 2,
            machine_id: 3,
            reservation_start: "2026-08-09T08:00:00Z",
            reservation_end: "2026-08-09T10:00:00Z",
            timezone: "Europe/Bucharest",
          },
        }),
      )
      .mockResolvedValueOnce(
        heldDetail({
          status: "RUNNING",
          version: 3,
          started_at: "2026-08-09T08:10:00Z",
          reservation: {
            reservation_id: 9,
            status: "RESERVED",
            version: 2,
            machine_id: 3,
            reservation_start: "2026-08-09T08:00:00Z",
            reservation_end: "2026-08-09T10:00:00Z",
            timezone: "Europe/Bucharest",
          },
        }),
      );
    startMachineRun.mockResolvedValue({ machine_run_id: 12, status: "RUNNING", version: 3 });

    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-action-start")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("machine-run-action-start"));
    await waitFor(() => {
      expect(startMachineRun).toHaveBeenCalledWith(12, 2);
      expect(getMachineRun).toHaveBeenCalledTimes(2);
    });
    expect(screen.getByTestId("machine-run-status")).toHaveTextContent("În lucru pe utilaj");
  });

  it("cas_stale shows operator message and refetches", async () => {
    const { MachineRunRequestError } = await import("@/api/machineRuns");
    getMachineRun
      .mockResolvedValueOnce(
        heldDetail({
          status: "RESERVED",
          version: 2,
          reservation: {
            reservation_id: 9,
            status: "RESERVED",
            version: 2,
            machine_id: 3,
            reservation_start: "2026-08-09T08:00:00Z",
            reservation_end: "2026-08-09T10:00:00Z",
            timezone: "Europe/Bucharest",
          },
        }),
      )
      .mockResolvedValueOnce(
        heldDetail({
          status: "RUNNING",
          version: 3,
          reservation: {
            reservation_id: 9,
            status: "RESERVED",
            version: 2,
            machine_id: 3,
            reservation_start: "2026-08-09T08:00:00Z",
            reservation_end: "2026-08-09T10:00:00Z",
            timezone: "Europe/Bucharest",
          },
        }),
      );
    startMachineRun.mockRejectedValue(
      new MachineRunRequestError({
        code: "cas_stale",
        message: "stale",
        httpStatus: 409,
      }),
    );

    renderDetail();
    await waitFor(() => screen.getByTestId("machine-run-action-start"));
    fireEvent.click(screen.getByTestId("machine-run-action-start"));
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-error")).toHaveTextContent(
        "modificată între timp",
      );
    });
    expect(getMachineRun).toHaveBeenCalledTimes(2);
  });
});
