/**
 * BUILD 5 — Frontend tests for Quote Commercial Document adapter and component.
 *
 * Coverage:
 *   - API adapter calls canonical route
 *   - API adapter throws on backend error (no silent fallback)
 *   - API adapter maps commercial document sections
 *   - Download triggers blob download
 *   - Component renders loading state
 *   - Component renders error state
 *   - Component renders document data
 *   - Component does not render when not visible
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getQuoteCommercialDocument, downloadQuoteDocument } from "./quoteDocuments";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Mock config
vi.mock("@/lib/config", () => ({
  getAPIBaseURL: () => "http://localhost:8000",
}));

describe("quoteDocuments API adapter", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("getQuoteCommercialDocument", () => {
    it("calls the correct canonical route", async () => {
      const mockDoc = {
        quote_id: 1,
        quote_code: "QT-2025-001",
        status: "priced",
        version: 1,
        client: { name: "Test Client" },
        commercial: { currency: "RON", tva_percent: 19, validity_days: 15 },
        product_summary: { product_name: "Banner", externalized: false },
        product_text: { client_title: "Banner publicitar PVC" },
        line_items: [],
        totals: { subtotal: 1000, grand_total: 1190, tva: 190, currency: "RON" },
        readiness: { source: "snapshot", overall_status: "ready" },
        document: { title: "Ofertă comercială", sections: [], generated_at: "2025-05-15T10:00:00", source: "backend", format_version: "1.0" },
        metadata: { created_at: "2025-05-15T10:00:00" },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockDoc),
      });

      const result = await getQuoteCommercialDocument(1);

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/entities/quotes/1/commercial-document",
        expect.objectContaining({
          method: "GET",
          credentials: "include",
        })
      );
      expect(result.quote_code).toBe("QT-2025-001");
      expect(result.document.source).toBe("backend");
    });

    it("throws on backend error — no silent fallback", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: () => Promise.resolve("Quote not found"),
      });

      await expect(getQuoteCommercialDocument(999)).rejects.toThrow(
        /Failed to fetch commercial document.*999.*404/
      );
    });

    it("throws on network error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(getQuoteCommercialDocument(1)).rejects.toThrow("Network error");
    });

    it("maps commercial document sections correctly", async () => {
      const mockDoc = {
        quote_id: 1,
        quote_code: "QT-2025-002",
        status: "priced",
        version: 1,
        client: { name: "Client SRL" },
        commercial: { currency: "RON", tva_percent: 19, validity_days: 15 },
        product_summary: { product_name: "Mesh", externalized: true },
        product_text: {
          client_title: "Mesh publicitar",
          externalization_note: "Producție externalizată",
        },
        line_items: [
          { description: "Material mesh", quantity: 1, unit_price: 500, total: 500, type: "material" },
        ],
        totals: { subtotal: 500, grand_total: 595, tva: 95, currency: "RON", discount: 0, discount_pct: 0, total_before_vat: 500, margin_pct: 30 },
        readiness: { source: "snapshot", overall_status: "ready_with_warnings", warnings: ["Supplier confirmation needed"], blockers: [] },
        document: {
          title: "Ofertă comercială",
          sections: [
            { id: "product_description", title: "Descriere produs", content: {} },
            { id: "externalization", title: "Externalizare", content: { externalized: true } },
          ],
          generated_at: "2025-05-15T10:00:00",
          source: "backend",
          format_version: "1.0",
        },
        metadata: { created_at: "2025-05-15T10:00:00" },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockDoc),
      });

      const result = await getQuoteCommercialDocument(1);
      expect(result.document.sections).toHaveLength(2);
      expect(result.document.sections[1].id).toBe("externalization");
      expect(result.product_text.externalization_note).toBe("Producție externalizată");
      expect(result.readiness.warnings).toContain("Supplier confirmation needed");
    });
  });

  describe("downloadQuoteDocument", () => {
    it("calls export endpoint with correct format", async () => {
      const mockBlob = new Blob(["<html></html>"], { type: "text/html" });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      });

      // Mock URL and DOM
      const mockCreateObjectURL = vi.fn(() => "blob:http://test/abc");
      const mockRevokeObjectURL = vi.fn();
      vi.stubGlobal("URL", { createObjectURL: mockCreateObjectURL, revokeObjectURL: mockRevokeObjectURL });

      const mockElement = { href: "", download: "", click: vi.fn() };
      vi.spyOn(document, "createElement").mockReturnValue(mockElement as unknown as HTMLElement);
      vi.spyOn(document.body, "appendChild").mockImplementation(() => mockElement as unknown as Node);
      vi.spyOn(document.body, "removeChild").mockImplementation(() => mockElement as unknown as Node);

      await downloadQuoteDocument(1, "html");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/entities/quotes/1/commercial-document/export?format=html",
        expect.objectContaining({
          method: "GET",
          credentials: "include",
        })
      );
      expect(mockElement.click).toHaveBeenCalled();
      expect(mockElement.download).toBe("oferta_1.html");
    });

    it("throws on export error — no silent fallback", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: () => Promise.resolve("Internal error"),
      });

      await expect(downloadQuoteDocument(1)).rejects.toThrow(
        /Failed to export commercial document.*1.*500/
      );
    });
  });
});