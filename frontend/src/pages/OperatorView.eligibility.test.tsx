import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import OperatorView from "./OperatorView";

vi.mock("@/hooks/useOperatorData", () => ({
  useOperatorData: () => ({
    tasks: [
      {
        id: "task-assembly-1",
        jobId: "JOB-0009",
        client: "MOL",
        product: "Litere",
        operationCode: "volumetric_letter_assembly",
        operationName: "Asamblare litere",
        machineName: "WA-ASSEMBLY-01",
        status: "assigned",
        assignee: "—",
        plannedDurationMin: 60,
        actualDurationMin: null,
        startedAt: null,
        targetEndAt: null,
        instructions: "",
        inputDependencies: [],
        expectedOutput: "",
        sequenceIndex: 1,
      },
    ],
    loading: false,
    error: null,
    source: "db",
    refresh: vi.fn(),
    performAction: vi.fn(),
  }),
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
  OperationPoolPreviewPanel: ({ operationCode }: { operationCode?: string | null }) => (
    <div data-testid="operation-pool-preview">
      Operație: {operationCode} → assembly · mode: hybrid · 4 eligibili
    </div>
  ),
}));

describe("OperatorView eligibility bridge", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("passes volumetric_letter_assembly to pool preview for start candidate", async () => {
    render(
      <MemoryRouter>
        <OperatorView />
      </MemoryRouter>
    );

    expect(await screen.findByTestId("operation-pool-preview")).toHaveTextContent(
      "volumetric_letter_assembly → assembly"
    );
    expect(screen.getByText(/4 eligibili/)).toBeInTheDocument();
  });
});
