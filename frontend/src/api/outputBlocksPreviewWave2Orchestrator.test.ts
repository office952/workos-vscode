import { describe, expect, it, vi } from "vitest";

import type { CanonicalOutputBlockPreviewResponse } from "./canonicalOutputBlockPreview";
import type { RenderPreviewRequest, RenderPreviewResponse } from "./outputBlocksPreview";
import { mapLegacyRequestToCanonicalPayload } from "./outputBlocksPreviewWave2Helpers";
import { renderOutputBlocksPreviewWave2 } from "./outputBlocksPreviewWave2Orchestrator";

function makeLegacyResponse(): RenderPreviewResponse {
  return {
    persisted: false,
    template_id: 10,
    dossier_id: null,
    document_type: "offer",
    audience: "client",
    render_mode: "preview",
    blocks: [],
    warnings: [],
    blockers: [],
    trace: {
      source: "legacy_render_preview",
      no_persist: true,
      changed_entities: [],
      live_changes_affect_accepted_orders: false,
    },
  };
}

function makeCanonicalResponse(): CanonicalOutputBlockPreviewResponse {
  return {
    preview_only: true,
    context: "quote_preview",
    rendered_blocks: [
      {
        block_id: "block-1",
        block_type: "offer_short_description",
        title: "Offer",
        approval_status: "approved",
        rendered_text: "normalized",
        variables_used: { product_name: "Panel" },
        source_fields_used: ["identity.product_name"],
        skipped: false,
        skip_reason: null,
        warnings: [],
        blockers: [],
      },
    ],
    warnings: [],
    blockers: [],
  };
}

function makeEligibleRequest(): RenderPreviewRequest {
  return {
    template_id: 10,
    dossier_id: null,
    document_type: "offer",
    audience: "client",
    block_types: ["offer_short_description"],
    quote_context: {
      client_name: "Client",
      quantity: 1,
    },
    render_mode: "preview",
  };
}

describe("outputBlocksPreviewWave2Orchestrator", () => {
  it("uses legacy when flag defaults to false", async () => {
    const legacyRenderPreview = vi.fn().mockResolvedValue(makeLegacyResponse());
    const canonicalPreview = vi.fn().mockResolvedValue(makeCanonicalResponse());

    const response = await renderOutputBlocksPreviewWave2(makeEligibleRequest(), {
      envFlagValue: undefined,
      deps: { legacyRenderPreview, canonicalPreview },
    });

    expect(legacyRenderPreview).toHaveBeenCalledTimes(1);
    expect(canonicalPreview).not.toHaveBeenCalled();
    expect(response.trace.source).toBe("legacy_render_preview");
  });

  it("uses legacy when env flag is false", async () => {
    const legacyRenderPreview = vi.fn().mockResolvedValue(makeLegacyResponse());
    const canonicalPreview = vi.fn().mockResolvedValue(makeCanonicalResponse());

    await renderOutputBlocksPreviewWave2(makeEligibleRequest(), {
      envFlagValue: "false",
      deps: { legacyRenderPreview, canonicalPreview },
    });

    expect(legacyRenderPreview).toHaveBeenCalledTimes(1);
    expect(canonicalPreview).not.toHaveBeenCalled();
  });

  it("uses canonical when flag is true and request is eligible", async () => {
    const request = makeEligibleRequest();
    const legacyRenderPreview = vi.fn().mockResolvedValue(makeLegacyResponse());
    const canonicalPreview = vi.fn().mockResolvedValue(makeCanonicalResponse());

    const response = await renderOutputBlocksPreviewWave2(request, {
      envFlagValue: "true",
      deps: { legacyRenderPreview, canonicalPreview },
    });

    const expectedPayload = mapLegacyRequestToCanonicalPayload(request);
    expect(canonicalPreview).toHaveBeenCalledTimes(1);
    expect(canonicalPreview).toHaveBeenCalledWith(expectedPayload);
    expect(legacyRenderPreview).not.toHaveBeenCalled();
    expect(response.trace.source).toBe("canonical_output_blocks_preview");
  });

  it("uses legacy when flag is true but block_types is empty", async () => {
    const legacyRenderPreview = vi.fn().mockResolvedValue(makeLegacyResponse());
    const canonicalPreview = vi.fn().mockResolvedValue(makeCanonicalResponse());

    await renderOutputBlocksPreviewWave2(
      {
        ...makeEligibleRequest(),
        block_types: [],
      },
      {
        envFlagValue: "true",
        deps: { legacyRenderPreview, canonicalPreview },
      }
    );

    expect(legacyRenderPreview).toHaveBeenCalledTimes(1);
    expect(canonicalPreview).not.toHaveBeenCalled();
  });

  it("uses legacy when flag is true but template_id is invalid", async () => {
    const legacyRenderPreview = vi.fn().mockResolvedValue(makeLegacyResponse());
    const canonicalPreview = vi.fn().mockResolvedValue(makeCanonicalResponse());

    await renderOutputBlocksPreviewWave2(
      {
        ...makeEligibleRequest(),
        template_id: 0,
      },
      {
        envFlagValue: "true",
        deps: { legacyRenderPreview, canonicalPreview },
      }
    );

    expect(legacyRenderPreview).toHaveBeenCalledTimes(1);
    expect(canonicalPreview).not.toHaveBeenCalled();
  });

  it("falls back once to legacy when canonical throws", async () => {
    const legacyRenderPreview = vi.fn().mockResolvedValue(makeLegacyResponse());
    const canonicalPreview = vi.fn().mockRejectedValue(new Error("canonical_failed"));

    const response = await renderOutputBlocksPreviewWave2(makeEligibleRequest(), {
      envFlagValue: "true",
      deps: { legacyRenderPreview, canonicalPreview },
    });

    expect(canonicalPreview).toHaveBeenCalledTimes(1);
    expect(legacyRenderPreview).toHaveBeenCalledTimes(1);
    expect(response.trace.source).toContain("canonical_fallback");
    expect(response.warnings.join(" ")).toContain("wave2_canonical_fallback_to_legacy");
  });

  it("does not touch Build 9 or Build 5 adapter surfaces", async () => {
    const legacyRenderPreview = vi.fn().mockResolvedValue(makeLegacyResponse());
    const canonicalPreview = vi.fn().mockResolvedValue(makeCanonicalResponse());

    await renderOutputBlocksPreviewWave2(makeEligibleRequest(), {
      envFlagValue: "true",
      deps: { legacyRenderPreview, canonicalPreview },
    });

    expect(canonicalPreview).toHaveBeenCalledTimes(1);
    expect(legacyRenderPreview).not.toHaveBeenCalled();
  });
});
