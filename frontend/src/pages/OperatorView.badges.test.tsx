import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import OperatorView from "./OperatorView";
import type { OperatorTask } from "@/lib/mockData";

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

function baseTask(overrides: Partial<OperatorTask> = {}): OperatorTask {
  return {
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
    ...overrides,
  };
}

describe("OperatorView design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders SourceBadge for live db tasks", () => {
    mockUseOperatorData.mockReturnValue({
      tasks: [baseTask()],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>,
    );

    expect(screen.getByText("Live DB")).toHaveAttribute("data-source", "db");
  });

  it("live empty state shows Live DB (gol), not mock/disconnected", () => {
    mockUseOperatorData.mockReturnValue({
      tasks: [],
      loading: false,
      error: null,
      source: "empty",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>,
    );

    expect(screen.getByText(/Live DB \(gol\)/i)).toHaveAttribute("data-source", "empty");
    expect(screen.queryByText(/^Mock Data$/)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/nu există conexiune la backend/i),
    ).not.toBeInTheDocument();
  });

  it("does not show mock source badge on live fixture", () => {
    mockUseOperatorData.mockReturnValue({
      tasks: [baseTask({ status: "in_progress" })],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>,
    );

    const header = screen.getByText("Operator View").closest("div");
    expect(header).toBeTruthy();
    expect(screen.getByText("Live DB")).toBeInTheDocument();
    expect(screen.queryByText(/^Mock Data$/)).not.toBeInTheDocument();
  });

  it("renders executionTask status badge via design-system", () => {
    mockUseOperatorData.mockReturnValue({
      tasks: [baseTask({ id: "task-assigned", status: "assigned" })],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>,
    );

    const badges = document.querySelectorAll(
      '[data-status="assigned"][data-status-domain="executionTask"]',
    );
    expect(badges.length).toBeGreaterThan(0);
    expect(badges[0]).toHaveAttribute("data-status-tone", "blue");
    expect(badges[0]).toHaveTextContent("Alocat");
  });

  it("keeps operator actions visible for in_progress task", () => {
    mockUseOperatorData.mockReturnValue({
      tasks: [baseTask({ id: "task-run", status: "in_progress" })],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: /^Pause$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Complete$/i })).toBeInTheDocument();
    const badge = document.querySelector(
      '[data-status="in_progress"][data-status-domain="executionTask"]',
    );
    expect(badge).toBeTruthy();
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
  });

  it("shows mock warning only when source is mock", () => {
    mockUseOperatorData.mockReturnValue({
      tasks: [],
      loading: false,
      error: null,
      source: "mock",
      refresh: vi.fn(),
      performAction: vi.fn(),
    });

    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>,
    );

    const alert = screen.getByRole("alert");
    expect(within(alert).getByText(/Mock Data/i)).toBeInTheDocument();
    expect(screen.queryByText(/^Live DB$/)).not.toBeInTheDocument();
  });
});
