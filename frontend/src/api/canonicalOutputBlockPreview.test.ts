import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  previewCanonicalOutputBlocks,
  type CanonicalOutputBlockPreviewRequest,
} from "./canonicalOutputBlockPreview";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

vi.mock("@/lib/config", () => ({
  getAPIBaseURL: () => "http://localhost:8000",
}));

describe("canonicalOutputBlockPreview adapter", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("calls canonical preview endpoint with POST", async () => {
    const request: CanonicalOutputBlockPreviewRequest = {
      block_ids: ["STAGING_TEST_BUILD_27_06A_OUTPUTBLOCK"],
      context: "quote_preview",
      source_payload: {
        identity: { product_name: "Placa plexiglass test" },
        materials: { main_material: "plexiglass transparent" },
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          preview_only: true,
          context: "quote_preview",
          rendered_blocks: [],
          warnings: [],
          blockers: [],
        }),
    });

    await previewCanonicalOutputBlocks(request);

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/product-system/output-blocks/preview",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      })
    );

    const callArgs = mockFetch.mock.calls[0];
    const init = callArgs[1] as RequestInit;
    expect(JSON.parse(String(init.body))).toEqual(request);
  });

  it("returns preview_only response shape", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          preview_only: true,
          context: "quote_preview",
          rendered_blocks: [
            {
              block_id: "STAGING_TEST_BUILD_27_06A_OUTPUTBLOCK",
              block_type: "offer_short_description",
              approval_status: "approved",
              rendered_text:
                "Placa plexiglass test realizat din plexiglass transparent, conform configuratiei aprobate.",
              variables_used: {
                product_name: "Placa plexiglass test",
                main_material: "plexiglass transparent",
              },
              source_fields_used: ["identity.product_name", "materials.main_material"],
              skipped: false,
              skip_reason: null,
              warnings: [],
              blockers: [],
            },
          ],
          warnings: [],
          blockers: [],
        }),
    });

    const result = await previewCanonicalOutputBlocks({
      block_types: ["offer_short_description"],
      context: "quote_preview",
      source_payload: {
        identity: { product_name: "Placa plexiglass test" },
        materials: { main_material: "plexiglass transparent" },
      },
    });

    expect(result.preview_only).toBe(true);
    expect(result.context).toBe("quote_preview");
    expect(Array.isArray(result.rendered_blocks)).toBe(true);
    expect(Array.isArray(result.warnings)).toBe(true);
    expect(Array.isArray(result.blockers)).toBe(true);
  });

  it("does not target legacy endpoint strings", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          preview_only: true,
          context: "quote_preview",
          rendered_blocks: [],
          warnings: [],
          blockers: [],
        }),
    });

    await previewCanonicalOutputBlocks({
      context: "quote_preview",
      source_payload: {},
    });

    const calledUrl = String(mockFetch.mock.calls[0][0]);
    expect(calledUrl).not.toContain("render-preview");
    expect(calledUrl).toContain("/api/v1/product-system/output-blocks/preview");
  });

  it("throws on backend error with status", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      text: () => Promise.resolve('{"error":"output_block_preview_validation_error"}'),
    });

    await expect(
      previewCanonicalOutputBlocks({
        context: "quote_preview",
        source_payload: {},
      })
    ).rejects.toThrow(/Failed to preview canonical output blocks: 422/);
  });
});
