import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import OperatorView from "./OperatorView";

const mockUseOperatorData = vi.fn();

vi.mock("@/hooks/useOperatorData", () => ({
  useOperatorData: () => mockUseOperatorData(),
}));

vi.mock("@/hooks/useOperatorEmployees", () => ({
  useOperatorEmployees: () => ({
    employees: [],
    loading: false,
    error: null,
    source: "db",
    getMappingForTask: () => null,
    refresh: vi.fn(),
  }),
}));

vi.mock("@/hooks/useMaterialsCapture", () => ({
  useMaterialsCapture: () => ({
    materials: [],
    fetchMaterials: vi.fn(),
    addMaterials: vi.fn(),
    updateMaterial: vi.fn(),
    removeMaterial: vi.fn(),
  }),
}));

vi.mock("@/features/operational-registry/OperationPoolPreviewPanel", () => ({
  OperationPoolPreviewPanel: () => null,
}));

function mockOperatorSource(
  source: "db" | "mock" | "empty" | "error" | "loading",
  tasks: unknown[] = []
) {
  mockUseOperatorData.mockReturnValue({
    tasks,
    loading: false,
    error: source === "error" ? "HTTP 500" : null,
    source,
    refresh: vi.fn(),
    performAction: vi.fn(),
  });
}

describe("OperatorView live-empty wiring", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("treats source=empty as live — no MOCK DATA banner", () => {
    mockOperatorSource("empty", []);
    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>
    );

    expect(screen.queryByText(/Mock Data/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/nu există conexiune la backend/i)
    ).not.toBeInTheDocument();
    expect(screen.getByText(/Live DB \(gol\)/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Nu aveți task-uri asignate momentan/i)
    ).toBeInTheDocument();
  });

  it("shows mock warning only for source=mock", () => {
    mockOperatorSource("mock", []);
    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/Mock Data/i);
    expect(alert).toHaveTextContent(/nu există conexiune la backend/i);
  });

  it("treats source=db as wired with Live DB badge", () => {
    mockOperatorSource("db", [
      {
        id: "task-1",
        jobId: "JOB-0001",
        client: "Client",
        product: "Produs",
        operationCode: "print",
        operationName: "Print",
        machineName: "Epson",
        status: "assigned",
        assignee: "—",
        plannedDurationMin: 30,
        actualDurationMin: null,
        startedAt: null,
        targetEndAt: null,
        instructions: "",
        inputDependencies: [],
        expectedOutput: "",
        sequenceIndex: 1,
      },
    ]);
    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>
    );

    expect(screen.getByText("Live DB")).toBeInTheDocument();
    expect(screen.queryByText(/Mock Data/i)).not.toBeInTheDocument();
    expect(screen.getByText("Angajat activ (registry)")).toBeInTheDocument();
  });
});
