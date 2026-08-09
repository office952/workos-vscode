import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MachineRunAddParticipantPanel } from "./MachineRunAddParticipantPanel";

const listMachineRunAddCandidates = vi.fn();
const addMachineRunParticipant = vi.fn();
const onAdded = vi.fn();

vi.mock("@/api/machineRuns", () => ({
  listMachineRunAddCandidates: (...a: unknown[]) => listMachineRunAddCandidates(...a),
  addMachineRunParticipant: (...a: unknown[]) => addMachineRunParticipant(...a),
  MachineRunRequestError: class MachineRunRequestError extends Error {
    code: string;
    httpStatus = 409;
    constructor(payload: { code: string; message: string }) {
      super(payload.message);
      this.code = payload.code;
    }
  },
}));

describe("MachineRunAddParticipantPanel", () => {
  beforeEach(() => {
    listMachineRunAddCandidates.mockReset();
    addMachineRunParticipant.mockReset();
    onAdded.mockReset();
  });

  it("does not render when not visible", () => {
    const { container } = render(
      <MachineRunAddParticipantPanel
        machineRunId={12}
        expectedVersion={1}
        visible={false}
        onAdded={onAdded}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("loads candidates and posts single add then refetches", async () => {
    listMachineRunAddCandidates.mockResolvedValue({
      context: "add",
      machine_id: 3,
      machine_run_id: 12,
      machine_code: "CNC-1",
      machine_name: "Router",
      required_capability: null,
      mutation_allowed: true,
      reason_code: null,
      message: null,
      count: 1,
      items: [
        {
          execution_plan_id: 30,
          task_key: "FACE_C",
          order_id: 200,
          operation_code: "CNC",
          workcenter: "CNC",
          resource_mode: "MACHINE_BOUND",
          machine_capability_code: "cnc_cut",
          batch_eligible: true,
          task_label: "Față C",
        },
      ],
    });
    addMachineRunParticipant.mockResolvedValue({ machine_run_id: 12, version: 2 });

    render(
      <MachineRunAddParticipantPanel
        machineRunId={12}
        expectedVersion={1}
        visible
        onAdded={onAdded}
      />,
    );
    fireEvent.click(screen.getByTestId("machine-run-add-open"));
    await waitFor(() => {
      expect(listMachineRunAddCandidates).toHaveBeenCalledWith(12);
    });
    fireEvent.click(screen.getByText("Față C"));
    fireEvent.click(screen.getByTestId("machine-run-add-submit"));
    await waitFor(() => {
      expect(addMachineRunParticipant).toHaveBeenCalledWith(12, {
        expected_version: 1,
        execution_plan_id: 30,
        task_key: "FACE_C",
      });
      expect(onAdded).toHaveBeenCalled();
    });
  });

  it("hides actionable selector when mutation_allowed is false", async () => {
    listMachineRunAddCandidates.mockResolvedValue({
      context: "add",
      machine_id: 3,
      machine_run_id: 12,
      machine_code: "CNC-1",
      machine_name: "Router",
      required_capability: null,
      mutation_allowed: false,
      reason_code: "invalid_transition",
      message: "Doar HELD permite ADD.",
      count: 0,
      items: [],
    });
    render(
      <MachineRunAddParticipantPanel
        machineRunId={12}
        expectedVersion={2}
        visible
        onAdded={onAdded}
      />,
    );
    fireEvent.click(screen.getByTestId("machine-run-add-open"));
    await waitFor(() => {
      expect(screen.getByTestId("machine-run-add-blocked")).toHaveTextContent(
        "Doar HELD permite ADD.",
      );
    });
    expect(screen.queryByTestId("machine-run-add-submit")).not.toBeInTheDocument();
  });
});
