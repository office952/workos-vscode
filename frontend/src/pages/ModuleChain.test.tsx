import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import ModuleChain from "@/pages/ModuleChain";

vi.mock("@/hooks/useModuleChainData", () => ({
  useModuleChainData: () => ({
    modules: [
      {
        id: "wi",
        name: "Work Intake",
        shortName: "WI",
        description: "Pregătire cerere",
        truthOwns: "Cerințe",
        status: "idle",
        activeCount: 0,
        statusCounts: { ok: 0, warning: 0, error: 0 },
      },
    ],
    contractHandoffs: [
      {
        from: "WI",
        to: "PS",
        payloadSummary: "product_family",
        forbidden: ["cost"],
        lastEvent: "WI_READY_FOR_QUOTE",
        lastEventTime: "—",
      },
    ],
    health: null,
    aggregateStatus: "unknown",
    generatedAt: null,
    loading: false,
    error: "network down",
    isLive: false,
    refetch: vi.fn(),
  }),
}));

describe("ModuleChain tab completion", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Romanian title with secondary technical alias", () => {
    render(<ModuleChain />);
    expect(screen.getByRole("heading", { name: "Harta sistemelor" })).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-alias")).toHaveTextContent("Module Chain");
  });

  it("renders expected technical tab set", () => {
    render(<ModuleChain />);
    expect(screen.getByTestId("module-chain-tab-system_map")).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-tab-handoffs")).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-tab-runtime")).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-tab-evidence")).toBeInTheDocument();
  });

  it("keeps map separate from runtime and shows neverified on runtime tab", () => {
    render(<ModuleChain />);
    expect(screen.getByTestId("module-chain-architecture")).toBeInTheDocument();
    expect(screen.queryByTestId("module-chain-runtime")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("module-chain-tab-runtime"));
    expect(screen.getByTestId("module-chain-runtime")).toHaveTextContent("Stare runtime");
    expect(screen.queryByTestId("module-chain-architecture")).not.toBeInTheDocument();
    expect(screen.getByText("INDISPONIBIL")).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-runtime-error")).toBeInTheDocument();
    expect(screen.getByText("Neverificat")).toBeInTheDocument();
  });

  it("separates handoffs and evidence from the map tab", () => {
    render(<ModuleChain />);
    expect(screen.queryByTestId("module-chain-handoffs")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("module-chain-tab-handoffs"));
    expect(screen.getByTestId("handoff-work_intake-product_system")).toHaveTextContent("Sursă:");
    expect(screen.getByText("REFERINȚĂ")).toBeInTheDocument();
    expect(screen.getByTestId("handoff-orders-execution_plan")).toHaveTextContent("PROVEN_V1");
    expect(screen.getByTestId("handoff-product_definition-product_aggregate")).toHaveTextContent(
      "task_contract"
    );

    fireEvent.click(screen.getByTestId("module-chain-tab-evidence"));
    expect(screen.getByTestId("module-chain-evidence")).toHaveTextContent("Surse și dovezi");
    expect(screen.getByTestId("evidence-ev.health")).toBeInTheDocument();
    expect(screen.getByTestId("evidence-ev.same_scenario_build1")).toHaveTextContent(
      "Same-scenario E2E PROVEN_V1"
    );
    expect(screen.queryByText("Live Health")).not.toBeInTheDocument();
  });
});
