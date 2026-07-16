import { describe, expect, it, vi, beforeEach } from "vitest";
import { fetchDocumentationIndex } from "@/api/documentationIndex";

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
            authority: "SUPPORTING",
            status: "CURRENT",
            last_validated_at: null,
            drift_status: "ALIGNED",
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
});
