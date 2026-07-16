import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
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

describe("ModuleChain honesty baseline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Romanian title with secondary technical alias", () => {
    render(<ModuleChain />);
    expect(screen.getByRole("heading", { name: "Harta sistemelor" })).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-alias")).toHaveTextContent("Module Chain");
  });

  it("keeps architecture and runtime sections separate with partial banner", () => {
    render(<ModuleChain />);
    expect(screen.getByTestId("module-chain-honesty-banner")).toHaveTextContent(
      /proiecție read-only|acoperirea este parțială/i
    );
    expect(screen.getByTestId("module-chain-architecture")).toHaveTextContent("Structura sistemelor");
    expect(screen.getByTestId("module-chain-runtime")).toHaveTextContent("Stare runtime");
    expect(screen.getByTestId("arch-node-work_intake")).toHaveTextContent("Preluare lucrare");
    expect(screen.getByText("INDISPONIBIL")).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-runtime-error")).toBeInTheDocument();
    expect(screen.getByText("Neverificat")).toBeInTheDocument();
  });

  it("shows sourced handoffs and does not claim Live Health as architecture truth", () => {
    render(<ModuleChain />);
    expect(screen.getByTestId("handoff-work_intake-product_system")).toHaveTextContent("Sursă:");
    expect(screen.queryByText("Live Health")).not.toBeInTheDocument();
  });
});
