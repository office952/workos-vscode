import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
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

describe("Governance honesty baseline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Romanian title with secondary alias and removes unsupported canonical count", async () => {
    render(<Governance />);
    expect(screen.getByRole("heading", { name: "Guvernanța sistemului" })).toBeInTheDocument();
    expect(screen.getByTestId("governance-alias")).toHaveTextContent("System Governance");
    expect(screen.queryByText("25 canonical docs")).not.toBeInTheDocument();
    expect(screen.getByTestId("governance-honesty-banner")).toHaveTextContent(
      /nu permite modificarea politicilor/i
    );
  });

  it("shows ownership, rules, owner gates, and review uncertainty", async () => {
    render(<Governance />);
    expect(screen.getByTestId("governance-ownership")).toHaveTextContent("Cine deține adevărul");
    expect(screen.getByTestId("governance-rules")).toHaveTextContent("Reguli de separare");
    expect(screen.getByTestId("governance-owner-gates")).toHaveTextContent("Owner gates");
    expect(screen.getByTestId("governance-open-questions")).toHaveTextContent("OWNER REVIEW REQUIRED");
    expect(screen.getByText(/UI-ul nu calculează costul comercial/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("governance-docs-ok")).toHaveTextContent("2 documente indexate");
    });
  });

  it("remains read-only (no edit/save controls on honesty baseline)", () => {
    render(<Governance />);
    expect(screen.queryByRole("button", { name: /salvează|edit|save|approve/i })).not.toBeInTheDocument();
  });
});
