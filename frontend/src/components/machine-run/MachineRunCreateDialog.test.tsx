import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { MachineRunCreateDialog } from "./MachineRunCreateDialog";

const listMachinesForPicker = vi.fn();
const listMachineRunCreateCandidates = vi.fn();
const createMachineRun = vi.fn();
const navigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom",
  );
  return {
    ...actual,
    useNavigate: () => navigate,
  };
});

vi.mock("@/api/machineRuns", () => ({
  listMachinesForPicker: (...a: unknown[]) => listMachinesForPicker(...a),
  listMachineRunCreateCandidates: (...a: unknown[]) =>
    listMachineRunCreateCandidates(...a),
  createMachineRun: (...a: unknown[]) => createMachineRun(...a),
  MachineRunRequestError: class MachineRunRequestError extends Error {
    code: string;
    httpStatus = 409;
    constructor(payload: { code: string; message: string }) {
      super(payload.message);
      this.code = payload.code;
    }
  },
}));

describe("MachineRunCreateDialog", () => {
  beforeEach(() => {
    listMachinesForPicker.mockReset();
    listMachineRunCreateCandidates.mockReset();
    createMachineRun.mockReset();
    navigate.mockReset();
    listMachinesForPicker.mockResolvedValue([
      {
        id: 3,
        machine_code: "CNC-1",
        name: "Router CNC",
        is_active: true,
        is_available: true,
        operational_status: "idle",
      },
    ]);
  });

  it("loads candidates after machine select; blocks submit under min 2", async () => {
    listMachineRunCreateCandidates.mockResolvedValue({
      context: "create",
      machine_id: 3,
      machine_run_id: null,
      machine_code: "CNC-1",
      machine_name: "Router CNC",
      required_capability: "cnc_cut",
      mutation_allowed: true,
      reason_code: null,
      message: null,
      count: 2,
      items: [
        {
          execution_plan_id: 21,
          task_key: "FACE_A",
          order_id: 100,
          operation_code: "CNC",
          workcenter: "CNC",
          resource_mode: "MACHINE_BOUND",
          machine_capability_code: "cnc_cut",
          batch_eligible: true,
          task_label: "Față A",
        },
        {
          execution_plan_id: 22,
          task_key: "FACE_B",
          order_id: 101,
          operation_code: "CNC",
          workcenter: "CNC",
          resource_mode: "MACHINE_BOUND",
          machine_capability_code: "cnc_cut",
          batch_eligible: true,
          task_label: "Față B",
        },
      ],
    });

    render(
      <MemoryRouter>
        <MachineRunCreateDialog open onOpenChange={() => undefined} />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("machine-run-create-machine")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("machine-run-create-machine"), {
      target: { value: "3" },
    });
    await waitFor(() => {
      expect(listMachineRunCreateCandidates).toHaveBeenCalledWith({ machine_id: 3 });
    });
    expect(screen.getByText("Comandă 100 · Plan 21")).toBeInTheDocument();
    expect(screen.getByText("Comandă 101 · Plan 22")).toBeInTheDocument();

    const submit = screen.getByTestId("machine-run-create-submit");
    expect(submit).toBeDisabled();

    fireEvent.click(screen.getByText("Față A"));
    expect(submit).toBeDisabled();
    fireEvent.click(screen.getByText("Față B"));
    expect(submit).not.toBeDisabled();
  });

  it("shows honest empty candidate state", async () => {
    listMachineRunCreateCandidates.mockResolvedValue({
      context: "create",
      machine_id: 3,
      machine_run_id: null,
      machine_code: "CNC-1",
      machine_name: "Router CNC",
      required_capability: null,
      mutation_allowed: true,
      reason_code: null,
      message: null,
      count: 0,
      items: [],
    });
    render(
      <MemoryRouter>
        <MachineRunCreateDialog open onOpenChange={() => undefined} />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-create-machine")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("machine-run-create-machine"), {
      target: { value: "3" },
    });
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-create-candidates-empty")).toHaveTextContent(
        "Nu există taskuri eligibile pentru acest utilaj.",
      );
    });
  });

  it("navigates to created run after successful POST", async () => {
    listMachineRunCreateCandidates.mockResolvedValue({
      context: "create",
      machine_id: 3,
      machine_run_id: null,
      machine_code: "CNC-1",
      machine_name: "Router CNC",
      required_capability: null,
      mutation_allowed: true,
      reason_code: null,
      message: null,
      count: 2,
      items: [
        {
          execution_plan_id: 21,
          task_key: "A",
          order_id: 1,
          operation_code: "CNC",
          workcenter: null,
          resource_mode: "MACHINE_BOUND",
          machine_capability_code: "cnc_cut",
          batch_eligible: true,
          task_label: "Task A",
        },
        {
          execution_plan_id: 22,
          task_key: "B",
          order_id: 2,
          operation_code: "CNC",
          workcenter: null,
          resource_mode: "MACHINE_BOUND",
          machine_capability_code: "cnc_cut",
          batch_eligible: true,
          task_label: "Task B",
        },
      ],
    });
    createMachineRun.mockResolvedValue({ machine_run_id: 99, status: "HELD", version: 1 });

    render(
      <MemoryRouter>
        <MachineRunCreateDialog open onOpenChange={() => undefined} />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-create-machine")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("machine-run-create-machine"), {
      target: { value: "3" },
    });
    await waitFor(() => expect(screen.getByText("Task A")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Task A"));
    fireEvent.click(screen.getByText("Task B"));
    fireEvent.click(screen.getByTestId("machine-run-create-submit"));
    await waitFor(() => {
      expect(createMachineRun).toHaveBeenCalledTimes(1);
      expect(navigate).toHaveBeenCalledWith("/execution/machine-runs/99");
    });
  });
});
