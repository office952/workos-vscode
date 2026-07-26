import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ImportantDocumentsSection } from "@/components/workos/ImportantDocumentsSection";
import type { DocumentationIndexFetchResult } from "@/api/documentationIndex";

vi.mock("@/api/documentationIndex", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/documentationIndex")>();
  return {
    ...actual,
    fetchDocumentationDetail: vi.fn(),
  };
});

describe("ImportantDocumentsSection", () => {
  it("shows loading when docsResult is null", () => {
    render(<ImportantDocumentsSection docsResult={null} />);
    expect(screen.getByTestId("important-docs-loading")).toBeInTheDocument();
  });

  it("shows forbidden state", () => {
    render(<ImportantDocumentsSection docsResult={{ state: "forbidden" }} />);
    expect(screen.getByTestId("important-docs-forbidden")).toBeInTheDocument();
  });

  it("shows unavailable state", () => {
    const result: DocumentationIndexFetchResult = {
      state: "unavailable",
      message: "HTTP 503",
    };
    render(<ImportantDocumentsSection docsResult={result} />);
    expect(screen.getByTestId("important-docs-unavailable")).toHaveTextContent("HTTP 503");
  });

  it("shows empty state", () => {
    render(<ImportantDocumentsSection docsResult={{ state: "empty" }} />);
    expect(screen.getByTestId("important-docs-empty")).toBeInTheDocument();
  });

  it("renders allowlisted list fields without inventing canonical badges", () => {
    const result: DocumentationIndexFetchResult = {
      state: "ok",
      data: {
        index_version: "workos_documentation_index/v1",
        count: 1,
        items: [
          {
            document_id: "doc.sample",
            title: "Sample Doc",
            path: "docs/architecture/sample.md",
            category: "CONTRACTS",
            authority: "SUPPORTING_CURRENT",
            status: "CURRENT",
            last_validated_at: "2026-07-16T12:00:00Z",
            drift_status: "ALIGNED",
            related_systems: ["wave0"],
            related_pages: ["/governance"],
            technical_id: "doc.sample",
            display: {
              display_label_ro: "Document exemplu",
              description_ro: "Descriere simplă",
            },
          },
        ],
      },
    };
    render(<ImportantDocumentsSection docsResult={result} />);
    const card = screen.getByTestId("important-doc-doc.sample");
    expect(card).toHaveTextContent("Sample Doc");
    expect(card).toHaveTextContent("Descriere simplă");
    expect(card).toHaveTextContent("doc.sample");
    expect(card).toHaveTextContent("CONTRACTS");
    expect(card).toHaveTextContent("SUPPORTING_CURRENT");
    expect(card).toHaveTextContent("docs/architecture/sample.md");
    expect(card).toHaveTextContent("wave0");
    expect(card).toHaveTextContent("/governance");
    expect(screen.queryByText(/canonical/i)).not.toBeInTheDocument();
  });
});
