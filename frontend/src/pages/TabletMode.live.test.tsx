import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { TabletStationQueue, TabletTaskDetail } from "@/pages/TabletMode";
import type { OperatorTask } from "@/lib/mockData";
import type { OperatorEmployeeOption } from "@/lib/operatorEmployeeEligibility";

const mockPerformAction = vi.fn().mockResolvedValue(true);

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

vi.mock("@/hooks/useTabletStationData", () => ({
  useTabletStationData: vi.fn(),
}));

import { useTabletStationData } from "@/hooks/useTabletStationData";

function mockLiveStationData(overrides: Partial<ReturnType<typeof useTabletStationData>> = {}) {
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
    performAction: mockPerformAction,
    isLive: true,
    registryEmployees: [registryEmployee],
    registrySource: "db",
    registryError: null,
    getStationLiveTasks: vi.fn().mockReturnValue([]),
    ...overrides,
  });
}

describe("TabletMode live wiring", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders live badge and registry employee without salary fields", () => {
    mockLiveStationData();
    render(
      <MemoryRouter initialEntries={["/tablet/print"]}>
        <Routes>
          <Route path="/tablet/:stationId" element={<TabletStationQueue />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Live DB")).toBeInTheDocument();
    expect(screen.getByText("Calin Cimpean")).toBeInTheDocument();
    expect(screen.queryByText(/RON/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/salariu/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Ion Popescu")).not.toBeInTheDocument();
  });

  it("shows live empty state without demo operators when queue is empty", () => {
    mockLiveStationData({
      tasks: [],
      source: "empty",
      operatorSource: "empty",
      registryEmployees: [
        {
          id: 4,
          name: "Putaru Sandu",
          role: "Lăcătuș",
          skillCodes: ["SK_ASSEMBLY"],
          workcenterCodes: ["WC_ASSEMBLY"],
          resourceCodes: [],
          eligibility: "unverified",
          eligibilityLabel: "Neconfirmat",
        },
      ],
    });
    render(
      <MemoryRouter initialEntries={["/tablet/asamblare_lipire"]}>
        <Routes>
          <Route path="/tablet/:stationId" element={<TabletStationQueue />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Live DB \(gol\)/i)).toBeInTheDocument();
    expect(screen.queryByText(/Demo fallback/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Ion Popescu")).not.toBeInTheDocument();
    expect(screen.getByText("Putaru Sandu")).toBeInTheDocument();
    expect(
      screen.getByText(/Nu există taskuri în coadă pentru această stație/i)
    ).toBeInTheDocument();
  });

  it("uses demo fallback operators only when not live", () => {
    mockLiveStationData({
      isLive: false,
      source: "demo",
      operatorSource: "mock",
      registryEmployees: [],
      tasks: [],
    });
    render(
      <MemoryRouter initialEntries={["/tablet/print"]}>
        <Routes>
          <Route path="/tablet/:stationId" element={<TabletStationQueue />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Demo fallback/i)).toBeInTheDocument();
    expect(screen.getByText("Ion Popescu")).toBeInTheDocument();
  });

  it("shows mapping neconfirmat badge for unconfirmed tasks", () => {
    mockLiveStationData({
      tasks: [
        {
          id: "TSK-UNMAPPED",
          orderId: "1",
          orderCode: "ORD-0001",
          client: "X",
          product: "Y",
          operationType: "unknown",
          operationName: "Unknown",
          workstationId: "print",
          requiredSkill: "—",
          skillLabel: "—",
          status: "in_coada",
          priority: "normal",
          deadline: "—",
          routingExplanation: "Mapping neconfirmat",
          dimensions: "—",
          material: "—",
          color: "—",
          quantity: 1,
          observations: "",
          attachments: [],
          isLive: true,
          mappingConfirmed: false,
        },
      ],
    });

    render(
      <MemoryRouter initialEntries={["/tablet/print"]}>
        <Routes>
          <Route path="/tablet/:stationId" element={<TabletStationQueue />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getAllByText("Mapping neconfirmat").length).toBeGreaterThan(0);
  });

  it("task detail exposes live Start action wired to performAction with employee_id", () => {
    mockLiveStationData();

    render(
      <MemoryRouter initialEntries={["/tablet/print/TSK-LIVE-1"]}>
        <Routes>
          <Route path="/tablet/:stationId/:taskId" element={<TabletTaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Client Live/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Calin Cimpean"));
    fireEvent.click(screen.getByRole("button", { name: /Start/i }));

    expect(mockPerformAction).toHaveBeenCalledWith(
      99,
      "TSK-LIVE-1",
      "start",
      undefined,
      7,
      "Calin Cimpean"
    );
  });

  it("displays legacy task without employee_id", () => {
    mockLiveStationData();
    render(
      <MemoryRouter initialEntries={["/tablet/print/TSK-LIVE-1"]}>
        <Routes>
          <Route path="/tablet/:stationId/:taskId" element={<TabletTaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Resursă \/ utilaj/i)).toBeInTheDocument();
    expect(screen.getByText("Epson SC-60800")).toBeInTheDocument();
  });
});
