import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ModuleChain from "@/pages/ModuleChain";
import { CANONICAL_SPINE_LABELS_RO } from "@/lib/currentTruthControlCenter";

function renderModuleChain() {
  return render(
    <MemoryRouter>
      <ModuleChain />
    </MemoryRouter>
  );
}

vi.mock("@/hooks/useModuleChainData", () => ({
  useModuleChainData: () => ({
    modules: [
      {
        id: "intake_v6",
        name: "Intake V6",
        shortName: "Intake",
        description: "Preluare cerere",
        truthOwns: "Workspace",
        status: "idle",
        activeCount: 0,
        statusCounts: { ok: 0, warning: 0, error: 0 },
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

describe("ModuleChain present-truth control center", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Romanian title with secondary technical alias", () => {
    renderModuleChain();
    expect(screen.getByRole("heading", { name: "Harta sistemelor" })).toBeInTheDocument();
    expect(screen.getByTestId("module-chain-alias")).toHaveTextContent("Module Chain");
  });

  it("renders one canonical spine and demotes legacy OC→TK", () => {
    renderModuleChain();
    expect(screen.getByTestId("canonical-spine-label")).toHaveTextContent(
      CANONICAL_SPINE_LABELS_RO.join(" → ")
    );
    expect(screen.getByTestId("arch-node-product_system")).toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("arch-node-product_system")).toHaveTextContent("Letters");
    expect(screen.getByTestId("arch-node-intake_v6")).toHaveTextContent("CONFIRMAT");
    expect(screen.getByTestId("arch-node-post_job")).toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("legacy-spine-notice")).toHaveTextContent(
      "nu reprezintă fluxul activ"
    );
    expect(screen.queryByText("PROVEN_V1")).not.toBeInTheDocument();
    expect(screen.queryByText("Operational Core")).not.toBeInTheDocument();
  });

  it("distinguishes concepts and canonical Inventory/Pricing/Dossier routes", () => {
    renderModuleChain();
    expect(screen.getByTestId("concept-node-product_family")).toHaveTextContent("Product Family");
    expect(screen.getByTestId("concept-node-component_template")).toHaveTextContent("STORAGE_MIXED");
    expect(screen.getByTestId("concept-node-mini_module")).toHaveTextContent("Mini-Module");
    expect(screen.getByTestId("concept-node-capability")).toHaveTextContent("interacțiune UI");
    expect(screen.getByTestId("stabilization-letters")).toBeInTheDocument();
    expect(screen.getByTestId("stabilization-logo")).toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("stabilization-acm")).toBeInTheDocument();
    expect(screen.queryByTestId("stabilization-banner")).not.toBeInTheDocument();
    const routes = screen.getByTestId("canonical-route-links");
    expect(routes).toHaveTextContent("/inventory");
    expect(routes).toHaveTextContent("/inventory/pricing");
    expect(routes).toHaveTextContent("/product-system/blueprint-dossier");
    expect(routes).not.toHaveTextContent("/product-system/dossier-completion");
  });

  it("keeps handoffs present-only and evidence historical", () => {
    renderModuleChain();
    fireEvent.click(screen.getByTestId("module-chain-tab-handoffs"));
    expect(screen.getByTestId("handoff-intake_v6-product_definition")).toBeInTheDocument();
    expect(screen.getByTestId("handoff-execution_reality-post_job")).toBeInTheDocument();
    expect(screen.queryByText("REFERINȚĂ")).not.toBeInTheDocument();
    expect(screen.queryByText("PROVEN_V1")).not.toBeInTheDocument();
    expect(screen.queryByText(/\bOC\b.*\bWI\b/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("module-chain-tab-evidence"));
    expect(screen.getByTestId("evidence-ev.legacy_oc_tk")).toHaveTextContent("Referință arhitecturală");
    expect(screen.getByTestId("evidence-ev.same_scenario")).toHaveTextContent("PROVEN_V1");
    expect(screen.getByTestId("evidence-ev.same_scenario")).toHaveTextContent(
      "Istoric / nu status runtime"
    );
    expect(screen.queryByText("Live Health")).not.toBeInTheDocument();
  });

  it("shows honest runtime unavailable without LIVE claim", () => {
    renderModuleChain();
    fireEvent.click(screen.getByTestId("module-chain-tab-runtime"));
    expect(screen.getByTestId("module-chain-runtime")).toHaveTextContent("Stare runtime");
    expect(screen.getByTestId("module-chain-runtime-aggregate")).toHaveTextContent("INDISPONIBIL");
    expect(screen.getByTestId("module-chain-runtime-error")).toBeInTheDocument();
    expect(screen.getByText("Neverificat")).toBeInTheDocument();
    expect(screen.getByText("DB neverificată")).toBeInTheDocument();
    expect(screen.queryByText("LIVE")).not.toBeInTheDocument();
  });
});
