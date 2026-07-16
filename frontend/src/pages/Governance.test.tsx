import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import Governance from "@/pages/Governance";

vi.mock("@/api/documentationIndex", () => ({
  fetchDocumentationIndex: vi.fn(async () => ({
    state: "ok" as const,
    data: {
      index_version: "workos_documentation_index/v1",
      count: 2,
      items: [
        {
          document_id: "doc.page_completion_foundation",
          title: "Page Completion Foundation",
          authority: "SUPPORTING_CURRENT",
          status: "CURRENT",
          last_validated_at: null,
          drift_status: "ALIGNED",
          technical_id: "doc.page_completion_foundation",
        },
        {
          document_id: "doc.truth_metadata",
          title: "Truth Metadata Contract",
          authority: "SUPPORTING_CURRENT",
          status: "CURRENT",
          last_validated_at: null,
          drift_status: "NOT_VALIDATED",
          technical_id: "doc.truth_metadata",
        },
      ],
    },
  })),
}));

const TAB_IDS = [
  "ownership",
  "boundaries",
  "status-flows",
  "agents",
  "truth",
  "gates",
  "guardrails",
  "products",
  "ui-rules",
] as const;

describe("Governance tab completion", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("keeps title, route identity labels, and removes unsupported canonical count", () => {
    render(<Governance />);
    expect(screen.getByRole("heading", { name: "Guvernanța sistemului" })).toBeInTheDocument();
    expect(screen.getByTestId("governance-alias")).toHaveTextContent("System Governance");
    expect(screen.queryByText("25 canonical docs")).not.toBeInTheDocument();
  });

  it("discovers every real tab by stable technical id and can select each", () => {
    render(<Governance />);
    for (const id of TAB_IDS) {
      const tab = screen.getByTestId(`governance-tab-${id}`);
      expect(tab).toBeInTheDocument();
      fireEvent.click(tab);
      expect(tab).toHaveAttribute("aria-selected", "true");
      expect(screen.getByTestId(`governance-tab-honesty-${id}`)).toBeInTheDocument();
    }
  });

  it("marks Ready for Quotes tab as reference, not live readiness", () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-gates"));
    const panel = screen.getByTestId("governance-panel-gates");
    expect(within(panel).getByTestId("governance-tab-honesty-gates")).toHaveTextContent("REFERINȚĂ");
    expect(panel).toHaveTextContent(/Nu este readiness operațional live/i);
  });

  it("marks Product Catalog as reference and status-flows conflict visible", () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-products"));
    expect(screen.getByTestId("governance-tab-honesty-products")).toHaveTextContent("REFERINȚĂ");
    expect(screen.getByTestId("governance-panel-products")).toHaveTextContent(/Nu înlocuiește Catalog produse/i);

    fireEvent.click(screen.getByTestId("governance-tab-status-flows"));
    expect(screen.getByTestId("governance-tab-honesty-status-flows")).toHaveTextContent("STALE_HINT");
  });

  it("remains read-only", () => {
    render(<Governance />);
    expect(screen.queryByRole("button", { name: /salvează|edit|save|approve/i })).not.toBeInTheDocument();
  });

  it("keeps ownership baseline content on default tab", async () => {
    render(<Governance />);
    expect(screen.getByTestId("governance-ownership")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("governance-docs-ok")).toHaveTextContent("2 documente indexate");
    });
  });
});
