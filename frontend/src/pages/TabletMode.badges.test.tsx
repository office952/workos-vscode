import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { TabletStationQueue } from "@/pages/TabletMode";
import type { OperatorTask } from "@/lib/mockData";
import type { OperatorEmployeeOption } from "@/lib/operatorEmployeeEligibility";

vi.mock("@/hooks/useTabletStationData", () => ({
  useTabletStationData: vi.fn(),
}));

import { useTabletStationData } from "@/hooks/useTabletStationData";

const liveOperatorTask: OperatorTask = {
  id: "TSK-LIVE-1",
  jobId: "JOB-0099",
  client: "Client Live",
  product: "Litere volumetrice",
  operationCode: "print",
  operationName: "Print",
  machineName: "Epson SC-60800",
  status: "assigned",
  assignee: "—",
  employeeId: null,
  employeeName: null,
  plannedDurationMin: 45,
  actualDurationMin: null,
  startedAt: null,
  targetEndAt: null,
  instructions: "Print conform plan",
  inputDependencies: [],
  expectedOutput: "Print OK",
  sequenceIndex: 1,
};

const registryEmployee: OperatorEmployeeOption = {
  id: 7,
  name: "Calin Cimpean",
  role: "Operator print",
  skillCodes: ["SK_PRINT"],
  workcenterCodes: ["WC_PRINT"],
  resourceCodes: ["MCH-EPSON-60800"],
  eligibility: "authorized",
  eligibilityLabel: "Autorizat",
};

function mockStationData(overrides: Partial<ReturnType<typeof useTabletStationData>> = {}) {
  vi.mocked(useTabletStationData).mockReturnValue({
    tasks: [
      {
        id: "TSK-LIVE-1",
        orderId: "99",
        orderCode: "ORD-0099",
        client: "Client Live",
        product: "Litere volumetrice",
        operationType: "print",
        operationName: "Print",
        workstationId: "print",
        requiredSkill: "print_operator",
        skillLabel: "Operator print",
        status: "pregatit",
        priority: "normal",
        deadline: "45 min plan",
        routingExplanation: "Operație print → stație print",
        dimensions: "—",
        material: "—",
        color: "—",
        quantity: 1,
        observations: "",
        attachments: [],
        isLive: true,
        mappingConfirmed: true,
        liveStatus: "assigned",
        employeeId: null,
        employeeName: null,
        machineName: "Epson SC-60800",
        orderIdNum: 99,
        instructions: "Print conform plan",
      },
    ],
    operatorTasks: [liveOperatorTask],
    source: "live",
    operatorSource: "db",
    loading: false,
    error: null,
    operationMappings: [],
    refresh: vi.fn(),
    performAction: vi.fn(),
    isLive: true,
    registryEmployees: [registryEmployee],
    registrySource: "db",
    registryError: null,
    getStationLiveTasks: vi.fn().mockReturnValue([]),
    ...overrides,
  });
}

function renderStationQueue(path = "/tablet/print") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/tablet/:stationId" element={<TabletStationQueue />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("TabletMode design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders SourceBadge with Live DB on live fixture", () => {
    mockStationData();
    renderStationQueue();

    const badge = document.querySelector('[data-source="db"]');
    expect(badge).toBeTruthy();
    expect(badge?.textContent).toMatch(/Live DB/i);
    expect(badge?.textContent).not.toMatch(/Mock Data|Demo/i);
  });

  it("renders SourceBadge with Live DB (gol) on empty live fixture", () => {
    mockStationData({
      tasks: [],
      source: "empty",
      operatorSource: "empty",
    });
    renderStationQueue("/tablet/asamblare_lipire");

    const badge = document.querySelector('[data-source="empty"]');
    expect(badge).toBeTruthy();
    expect(badge?.textContent).toMatch(/Live DB \(gol\)/i);
    expect(screen.queryByText(/Demo fallback/i)).not.toBeInTheDocument();
  });

  it("renders SourceBadge with Demo fallback on mock fixture", () => {
    mockStationData({
      isLive: false,
      source: "demo",
      operatorSource: "mock",
      registryEmployees: [],
      tasks: [],
    });
    renderStationQueue();

    const badge = document.querySelector('[data-source="mock"]');
    expect(badge).toBeTruthy();
    expect(badge?.textContent).toMatch(/Demo fallback/i);
  });

  it("renders executionTask StatusBadge for assigned task with preserved RO label", () => {
    mockStationData();
    renderStationQueue();

    const statusBadge = screen
      .getAllByText("Pregătit")
      .find((el) => el.getAttribute("data-status-domain") === "executionTask");
    expect(statusBadge).toBeTruthy();
    expect(statusBadge).toHaveAttribute("data-status", "assigned");
    expect(statusBadge).toHaveAttribute("data-status-tone", "blue");
  });

  it("renders executionTask StatusBadge for blocked task", () => {
    mockStationData({
      tasks: [
        {
          id: "TSK-BLOCKED",
          orderId: "2",
          orderCode: "ORD-0002",
          client: "Client",
          product: "Produs",
          operationType: "print",
          operationName: "Print blocat",
          workstationId: "print",
          requiredSkill: "print_operator",
          skillLabel: "Operator print",
          status: "blocat",
          priority: "normal",
          deadline: "—",
          routingExplanation: "Test",
          dimensions: "—",
          material: "—",
          color: "—",
          quantity: 1,
          observations: "Blocat test",
          attachments: [],
          isLive: true,
          mappingConfirmed: true,
          liveStatus: "blocked",
        },
      ],
      operatorTasks: [{ ...liveOperatorTask, id: "TSK-BLOCKED", status: "blocked" }],
    });
    renderStationQueue();

    const statusBadge = screen
      .getAllByText("Blocat")
      .find((el) => el.getAttribute("data-status-domain") === "executionTask");
    expect(statusBadge).toBeTruthy();
    expect(statusBadge).toHaveAttribute("data-status", "blocked");
    expect(statusBadge).toHaveAttribute("data-status-tone", "red");
  });

  it("keeps queue empty warning visible on live empty fixture", () => {
    mockStationData({
      tasks: [],
      source: "empty",
      operatorSource: "empty",
    });
    renderStationQueue("/tablet/asamblare_lipire");

    expect(
      screen.getByText(/Nu există taskuri în coadă pentru această stație/i),
    ).toBeInTheDocument();
  });
});
