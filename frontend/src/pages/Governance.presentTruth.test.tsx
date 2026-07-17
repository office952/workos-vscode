import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import Governance from "@/pages/Governance";
import { CANONICAL_SPINE_LABELS_RO } from "@/lib/currentTruthControlCenter";

vi.mock("@/api/documentationIndex", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/documentationIndex")>();
  return {
    ...actual,
    fetchDocumentationIndex: vi.fn(async () => ({
      state: "ok" as const,
      data: {
        index_version: "workos_documentation_index/v1",
        count: 0,
        items: [],
      },
    })),
    fetchDocumentationDetail: vi.fn(async () => ({
      state: "ok" as const,
      data: {
        technical_id: "x",
        reason_for_inclusion: "fixture",
        file_exists: true,
        content_markdown: "# x",
        index_version: "workos_documentation_index/v1",
        document: {
          document_id: "x",
          title: "x",
          path: "docs/x.md",
          category: "CONTRACTS",
          authority: "SUPPORTING_CURRENT",
          status: "CURRENT",
        },
      },
    })),
  };
});

describe("Governance present-truth control center", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("ownership includes Intake V6 and matches present statuses", () => {
    render(<Governance />);
    expect(screen.getByTestId("ownership-intake_v6")).toHaveTextContent("Intake V6");
    expect(screen.getByTestId("ownership-quote_snapshot")).toHaveTextContent("CONFIRMAT");
    expect(screen.getByTestId("ownership-post_job")).toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("ownership-active_scope_sold_scope")).toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("ownership-product_definition")).toHaveTextContent("PARTIAL");
  });

  it("publishes documentation hierarchy, registration law, readiness law", () => {
    render(<Governance />);
    expect(screen.getByTestId("governance-official-routes")).toHaveTextContent("/modules");
    expect(screen.getByTestId("governance-official-routes")).toHaveTextContent("/governance");
    expect(screen.getByTestId("unregistered-system-id")).toHaveTextContent("UNREGISTERED_SYSTEM");
    expect(screen.getByTestId("governance-active-scope-status")).toHaveTextContent(
      "PARTIAL / CONFLICTED"
    );
    expect(screen.getByTestId("readiness-law-binding")).toHaveTextContent("modulele active");
    expect(screen.getByTestId("inactive-module-rules")).toHaveTextContent("nu creează warnings");
    expect(screen.getByTestId("dependency-class-composition_only")).toHaveTextContent(
      "Composition-only"
    );
    expect(screen.getByTestId("hybrid-model-status")).toHaveTextContent("HYBRID");
    expect(screen.getByTestId("governance-full-template-coupling")).toHaveTextContent(
      "FULL_TEMPLATE_COUPLING"
    );
    expect(screen.getByTestId("active-scope-owns-product_definition")).toHaveTextContent(
      "active-scope readiness"
    );
  });

  it("boundaries follow canonical spine and drop Quotes-calculează", () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-boundaries"));
    const panel = screen.getByTestId("governance-panel-boundaries");
    expect(within(panel).getByTestId("governance-canonical-spine")).toHaveTextContent(
      CANONICAL_SPINE_LABELS_RO.join(" → ")
    );
    expect(within(panel).getByTestId("boundary-b.quote")).toHaveTextContent("Quote Snapshot");
    expect(within(panel).getByTestId("boundary-b.quote")).toHaveTextContent("Îngheață");
    expect(within(panel).getByTestId("boundary-b.pricing")).toHaveTextContent(
      "UI-ul nu calculează valori comerciale autoritare"
    );
    expect(within(panel).queryByTestId("boundary-b.quote")).not.toHaveTextContent("calculează în contextul firmei");
  });

  it("owner gates replace historical Blueprint readiness model", () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-gates"));
    const panel = screen.getByTestId("governance-panel-gates");
    expect(panel).toHaveTextContent("Owner gates");
    expect(panel).toHaveTextContent("POLITICA OWNER");
    expect(within(panel).getByTestId("owner-gate-g.owner_pricing")).toBeInTheDocument();
    expect(within(panel).queryByText(/Ready for Quotes/i)).not.toBeInTheDocument();
  });

  it("rewrites G01 and retains G13 with partial enforcement", () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-guardrails"));
    const panel = screen.getByTestId("governance-panel-guardrails");
    expect(within(panel).getByTestId("guardrail-G01")).toHaveTextContent(
      "CPP 7G calculează banii"
    );
    expect(within(panel).getByTestId("guardrail-G01")).toHaveTextContent(
      "măsurători non-monetare"
    );
    expect(within(panel).getByTestId("guardrail-G01")).not.toHaveTextContent("Quotes calculează");
    expect(within(panel).getByTestId("guardrail-G13")).toHaveTextContent(
      "UTF-8 end-to-end pentru textul operator"
    );
    expect(within(panel).getByTestId("guardrail-G13")).toHaveTextContent("PARTIAL APLICAT");
    expect(within(panel).getByTestId("guardrail-G14")).toHaveTextContent("module active");
    expect(within(panel).getByTestId("guardrail-G15")).toHaveTextContent("APLICAT");
    expect(within(panel).getByTestId("guardrail-G16")).toHaveTextContent("UNREGISTERED_SYSTEM");
  });

  it("keeps active-scope runtime owner gate as STOP policy", () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-gates"));
    const panel = screen.getByTestId("governance-panel-gates");
    expect(within(panel).getByTestId("owner-gate-g.owner_active_scope_runtime")).toHaveTextContent(
      "STOP"
    );
  });

  it("labels agents as non-enforcement reference", () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-agents"));
    expect(screen.getByTestId("governance-tab-honesty-agents")).toHaveTextContent(
      "fără autoritate operațională"
    );
  });
});
