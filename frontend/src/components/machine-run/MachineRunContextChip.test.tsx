import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { MachineRunContextChip } from "./MachineRunContextChip";
import type { ActiveMachineRunByTask } from "@/api/machineRuns";

const membership: ActiveMachineRunByTask = {
  machine_run_id: 55,
  status: "RUNNING",
  machine_id: 3,
  machine_code: "CNC-1",
  machine_name: "Router CNC",
  reservation_status: "RESERVED",
  execution_plan_id: 12,
  task_key: "FACE_A",
  order_id: 100,
  participant_status: "ACTIVE",
};

describe("MachineRunContextChip", () => {
  it("renders nothing when membership is absent", () => {
    const { container } = render(
      <MemoryRouter>
        <MachineRunContextChip membership={null} />
      </MemoryRouter>,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders status copy and detail link when active", () => {
    render(
      <MemoryRouter>
        <MachineRunContextChip membership={membership} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("machine-run-context-chip-55")).toHaveTextContent(
      "În lucru pe utilaj",
    );
    expect(screen.getByTestId("machine-run-context-open-55")).toHaveAttribute(
      "href",
      "/execution/machine-runs/55",
    );
  });
});
