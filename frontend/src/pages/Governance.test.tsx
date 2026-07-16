import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import Governance from "@/pages/Governance";

const mockIndexItems = [
  {
    document_id: "doc.page_completion_foundation",
    title: "Page Completion Foundation",
    path: "docs/architecture/WORKOS_PAGE_COMPLETION_FOUNDATION.md",
    category: "CONTRACTS",
    authority: "SUPPORTING_CURRENT",
    status: "CURRENT",
    last_validated_at: null,
    drift_status: "ALIGNED",
    related_systems: ["wave0_foundation"],
    related_pages: ["/governance"],
    technical_id: "doc.page_completion_foundation",
    display: {
      display_label_ro: "Fundamente completare pagină",
      description_ro: "Contract de completare a paginilor de adevăr.",
    },
  },
  {
    document_id: "doc.truth_metadata",
    title: "Truth Metadata Contract",
    path: "docs/architecture/WORKOS_TRUTH_METADATA_CONTRACT.md",
    category: "CONTRACTS",
    authority: "SUPPORTING_CURRENT",
    status: "STALE",
    last_validated_at: null,
    drift_status: "DOCUMENTATION_DRIFT",
    related_systems: ["wave0_foundation"],
    related_pages: [],
    technical_id: "doc.truth_metadata",
  },
  {
    document_id: "doc.superseded_example",
    title: "Superseded Example",
    path: "docs/plans/example-superseded.md",
    category: "PLAN",
    authority: "HISTORICAL",
    status: "SUPERSEDED",
    last_validated_at: "2026-01-01T00:00:00Z",
    drift_status: "ALIGNED",
    related_systems: [],
    related_pages: [],
    technical_id: "doc.superseded_example",
  },
  {
    document_id: "doc.owner_review",
    title: "Owner Review Doc",
    path: "docs/architecture/OWNER_REVIEW.md",
    category: "POLICY",
    authority: "OWNER_REVIEW_REQUIRED",
    status: "OWNER_REVIEW_REQUIRED",
    last_validated_at: null,
    drift_status: "NOT_VALIDATED",
    related_systems: ["governance"],
    related_pages: ["/governance"],
    technical_id: "doc.owner_review",
  },
];

vi.mock("@/api/documentationIndex", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/documentationIndex")>();
  return {
    ...actual,
    fetchDocumentationIndex: vi.fn(async () => ({
      state: "ok" as const,
      data: {
        index_version: "workos_documentation_index/v1",
        count: mockIndexItems.length,
        items: mockIndexItems,
      },
    })),
    fetchDocumentationDetail: vi.fn(async (documentId: string) => ({
      state: "ok" as const,
      data: {
        technical_id: documentId,
        reason_for_inclusion: "Allowlisted for Governance slice",
        file_exists: true,
        content_markdown: `# ${documentId}\n\nRead-only fixture content.`,
        index_version: "workos_documentation_index/v1",
        document: {
          document_id: documentId,
          title: documentId,
          path: "docs/architecture/fixture.md",
          category: "CONTRACTS",
          authority: "SUPPORTING_CURRENT",
          status: "CURRENT",
        },
      },
    })),
  };
});

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
      expect(screen.getByTestId("governance-docs-ok")).toHaveTextContent("4 documente indexate");
    });
  });

  it("shows Important Documents section from B2 index on Surse de adevăr", async () => {
    render(<Governance />);
    fireEvent.click(screen.getByTestId("governance-tab-truth"));
    const section = await screen.findByTestId("governance-important-documents");
    expect(section).toBeInTheDocument();
    expect(within(section).getByTestId("important-docs-list")).toBeInTheDocument();
    expect(within(section).getByTestId("important-doc-doc.page_completion_foundation")).toBeInTheDocument();
    expect(within(section).getByTestId("doc-flag-stale")).toBeInTheDocument();
    expect(within(section).getByTestId("doc-flag-superseded")).toBeInTheDocument();
    expect(within(section).getByTestId("doc-flag-owner-review")).toBeInTheDocument();
    expect(within(section).getAllByText("SUPPORTING_CURRENT").length).toBeGreaterThan(0);
    expect(within(section).getByText(/docs\/architecture\/WORKOS_PAGE_COMPLETION_FOUNDATION\.md/)).toBeInTheDocument();

    fireEvent.click(within(section).getByTestId("important-doc-open-doc.page_completion_foundation"));
    const reader = await screen.findByTestId("important-docs-reader");
    await waitFor(() => {
      expect(reader).toHaveTextContent("Read-only fixture content");
    });
    expect(reader).toHaveTextContent(/Fără editare/);
  });
});
