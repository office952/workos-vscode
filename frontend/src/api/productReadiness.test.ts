import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getProductReadiness, type ProductReadinessDto } from "./productReadiness";

const API_BASE = "http://localhost";
const CANONICAL_ROUTE = "/api/v1/product-readiness/blueprints/";

vi.mock("@/lib/config", () => ({
  getAPIBaseURL: () => API_BASE,
}));

describe("Product Readiness API Adapter", () => {
  const fetchMock = vi.fn();
  const globalAny = globalThis as any;

  beforeEach(() => {
    globalAny.fetch = fetchMock;
    fetchMock.mockReset();
  });

  afterEach(() => {
    fetchMock.mockReset();
  });

  it("calls canonical route with correct blueprint_id", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ source: "backend", contract_version: "2026-05-15", entity_type: "blueprint", entity_id: "bp_123", blueprint_id: "bp_123", overall_status: "blocked", ready_for_quote: false, technical_readiness: { status: "blocked", blockers: [], warnings: [] }, costengine_readiness: { status: "unknown", blockers: [], warnings: [] }, document_output_readiness: { status: "needs_review", blockers: [], warnings: [] }, visual_prompt_readiness: { status: "needs_review", blockers: [], warnings: [] }, execution_preparation_readiness: { status: "unknown", blockers: [], warnings: [] }, policy: { authority: "backend", compute_mode: "read_only", quote_gate: "enforced", order_snapshot: "quote_snapshot_frozen" } })
    });
    const id = "bp_123";
    await getProductReadiness(id as any);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(`${API_BASE}${CANONICAL_ROUTE}${id}`);
    expect(url).not.toContain("/api/v1/product_system/readiness");
  });

  it("encodes blueprint_id in URL", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    const id = "bp 123/abc";
    await getProductReadiness(id as any);
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe(`${API_BASE}${CANONICAL_ROUTE}${encodeURIComponent(id)}`);
  });

  it("returns full DTO shape", async () => {
    const mockDto: ProductReadinessDto = {
      source: "backend",
      contract_version: "2026-05-15",
      entity_type: "blueprint",
      entity_id: "bp_123",
      blueprint_id: "bp_123",
      overall_status: "blocked",
      ready_for_quote: false,
      technical_readiness: { status: "blocked", blockers: [{ code: "missing_dimensions", message: "Required dimensions model is missing.", severity: "blocker" }], warnings: [] },
      costengine_readiness: { status: "unknown", blockers: [], warnings: [] },
      document_output_readiness: { status: "needs_review", blockers: [], warnings: [] },
      visual_prompt_readiness: { status: "needs_review", blockers: [], warnings: [] },
      execution_preparation_readiness: { status: "unknown", blockers: [], warnings: [] },
      policy: { authority: "backend", compute_mode: "read_only", quote_gate: "enforced", order_snapshot: "quote_snapshot_frozen" }
    } as any;
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => mockDto });
    const result = await getProductReadiness("bp_123" as any);
    expect(result).toMatchObject({
      source: "backend",
      contract_version: expect.any(String),
      entity_type: "blueprint",
      entity_id: expect.any(String),
      blueprint_id: expect.any(String),
      overall_status: expect.any(String),
      ready_for_quote: expect.any(Boolean),
      policy: expect.any(Object),
      technical_readiness: expect.any(Object),
      costengine_readiness: expect.any(Object),
      document_output_readiness: expect.any(Object),
      visual_prompt_readiness: expect.any(Object),
      execution_preparation_readiness: expect.any(Object)
    });
  });

  it("handles warnings-only readiness", async () => {
    const mockDto = {
      source: "backend",
      contract_version: "2026-05-15",
      entity_type: "blueprint",
      entity_id: "bp_123",
      blueprint_id: "bp_123",
      overall_status: "needs_review",
      ready_for_quote: true,
      technical_readiness: { status: "ready", blockers: [], warnings: [] },
      costengine_readiness: { status: "ready", blockers: [], warnings: [] },
      document_output_readiness: { status: "needs_review", blockers: [], warnings: ["minor format"] },
      visual_prompt_readiness: { status: "ready", blockers: [], warnings: [] },
      execution_preparation_readiness: { status: "ready", blockers: [], warnings: [] },
      policy: { authority: "backend", compute_mode: "read_only", quote_gate: "enforced", order_snapshot: "quote_snapshot_frozen", requires_warning_acknowledgement: true }
    };
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => mockDto });
    const result = await getProductReadiness("bp_123" as any);
    expect(result.ready_for_quote).toBe(true);
    expect(result.overall_status).toBe("needs_review");
    expect(result.document_output_readiness.warnings.length).toBeGreaterThan(0);
    expect(result.policy.requires_warning_acknowledgement).toBe(true);
  });

  it("handles blocked readiness", async () => {
    const mockDto = {
      source: "backend",
      contract_version: "2026-05-15",
      entity_type: "blueprint",
      entity_id: "bp_123",
      blueprint_id: "bp_123",
      overall_status: "blocked",
      ready_for_quote: false,
      technical_readiness: { status: "blocked", blockers: ["missing_dimensions"], warnings: [] },
      costengine_readiness: { status: "ready", blockers: [], warnings: [] },
      document_output_readiness: { status: "ready", blockers: [], warnings: [] },
      visual_prompt_readiness: { status: "ready", blockers: [], warnings: [] },
      execution_preparation_readiness: { status: "ready", blockers: [], warnings: [] },
      policy: { authority: "backend", compute_mode: "read_only", quote_gate: "enforced", order_snapshot: "quote_snapshot_frozen" }
    };
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => mockDto });
    const result = await getProductReadiness("bp_123" as any);
    expect(result.ready_for_quote).toBe(false);
    expect(result.overall_status).toBe("blocked");
    expect(result.technical_readiness.blockers.length).toBeGreaterThan(0);
  });

  it("throws on 404 error", async () => {
    fetchMock.mockResolvedValueOnce({ ok: false, status: 404, json: async () => ({ detail: "Not found" }) });
    await expect(getProductReadiness("bp_404" as any)).rejects.toThrow("Not found");
  });

  it("throws on 500 error", async () => {
    fetchMock.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({ detail: "Internal error" }) });
    await expect(getProductReadiness("bp_500" as any)).rejects.toThrow("Internal error");
  });

  it("throws on network error", async () => {
    fetchMock.mockRejectedValueOnce(new Error("Network down"));
    await expect(getProductReadiness("bp_net" as any)).rejects.toThrow("Network down");
  });

  it("never calls legacy route by default", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    await getProductReadiness("bp_legacy" as any);
    const url = fetchMock.mock.calls[0][0];
    expect(url).not.toContain("/api/v1/product_system/readiness");
  });
});
