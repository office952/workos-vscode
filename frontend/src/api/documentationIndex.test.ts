import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  fetchDocumentationDetail,
  fetchDocumentationIndex,
  isAttentionStatus,
} from "@/api/documentationIndex";

vi.mock("@/lib/config", () => ({
  getAPIBaseURL: () => "",
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("fetchDocumentationIndex", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("maps list success to ok with items", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        index_version: "workos_documentation_index/v1",
        count: 1,
        items: [
          {
            document_id: "doc.a",
            title: "A",
            path: "docs/architecture/a.md",
            category: "CONTRACTS",
            authority: "SUPPORTING",
            status: "CURRENT",
            last_validated_at: null,
            drift_status: "ALIGNED",
            related_systems: [],
            related_pages: [],
            technical_id: "doc.a",
          },
        ],
      })
    );
    const result = await fetchDocumentationIndex();
    expect(result.state).toBe("ok");
    if (result.state === "ok") {
      expect(result.data.items).toHaveLength(1);
    }
  });

  it("maps 403 to forbidden", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ detail: "forbidden" }, 403));
    const result = await fetchDocumentationIndex();
    expect(result.state).toBe("forbidden");
  });

  it("maps network failure to unavailable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));
    const result = await fetchDocumentationIndex();
    expect(result.state).toBe("unavailable");
  });

  it("maps empty items to empty", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ index_version: "workos_documentation_index/v1", count: 0, items: [] })
    );
    const result = await fetchDocumentationIndex();
    expect(result.state).toBe("empty");
  });
});

describe("fetchDocumentationDetail", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("requests by document_id with include_content", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        technical_id: "doc.a",
        reason_for_inclusion: "test",
        file_exists: true,
        content_markdown: "# Hello",
        index_version: "workos_documentation_index/v1",
        document: {
          document_id: "doc.a",
          title: "A",
          path: "docs/architecture/a.md",
          category: "CONTRACTS",
          authority: "SUPPORTING",
          status: "CURRENT",
        },
      })
    );
    const result = await fetchDocumentationDetail("doc.a", true);
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/v1/system/documentation/doc.a?include_content=true",
      expect.objectContaining({ method: "GET", credentials: "include" })
    );
    expect(result.state).toBe("ok");
  });

  it("maps 404 to not_found", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ detail: "missing" }, 404));
    const result = await fetchDocumentationDetail("doc.missing", true);
    expect(result.state).toBe("not_found");
  });
});

describe("isAttentionStatus", () => {
  it("flags stale, superseded, and owner review", () => {
    expect(isAttentionStatus("STALE", "SUPPORTING", "ALIGNED").stale).toBe(true);
    expect(isAttentionStatus("CURRENT", "SUPPORTING", "DOCUMENTATION_DRIFT").stale).toBe(true);
    expect(isAttentionStatus("SUPERSEDED", "HISTORICAL", "ALIGNED").superseded).toBe(true);
    expect(isAttentionStatus("OWNER_REVIEW_REQUIRED", "OWNER_REVIEW_REQUIRED", "NOT_VALIDATED").ownerReview).toBe(
      true
    );
  });
});
