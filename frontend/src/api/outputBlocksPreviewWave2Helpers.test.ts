import { describe, expect, it } from "vitest";

import type { CanonicalOutputBlockPreviewResponse } from "./canonicalOutputBlockPreview";
import type { RenderPreviewRequest, RenderPreviewResponse } from "./outputBlocksPreview";
import {
  OUTPUTBLOCK_CANONICAL_PREVIEW_FLAG,
  isLegacyRequestEligibleForCanonical,
  mapLegacyRequestToCanonicalPayload,
  normalizeCanonicalResponseToLegacySkeleton,
  normalizeOutputBlocksPreviewResponseSkeleton,
  resolveOutputBlockCanonicalPreviewFlag,
  selectOutputBlocksPreviewRoute,
} from "./outputBlocksPreviewWave2Helpers";

describe("outputBlocksPreviewWave2Helpers", () => {
  it("exports expected feature flag key", () => {
    expect(OUTPUTBLOCK_CANONICAL_PREVIEW_FLAG).toBe(
      "VITE_FEATURE_OUTPUTBLOCK_CANONICAL_PREVIEW"
    );
  });

  it("resolves feature flag with runtime precedence over env", () => {
    expect(
      resolveOutputBlockCanonicalPreviewFlag({ runtimeValue: true, envValue: "false" })
    ).toBe(true);

    expect(
      resolveOutputBlockCanonicalPreviewFlag({ runtimeValue: "false", envValue: "true" })
    ).toBe(false);

    expect(resolveOutputBlockCanonicalPreviewFlag({ envValue: "true" })).toBe(true);
    expect(resolveOutputBlockCanonicalPreviewFlag({ envValue: "1" })).toBe(true);
    expect(resolveOutputBlockCanonicalPreviewFlag({ envValue: "off" })).toBe(false);
    expect(resolveOutputBlockCanonicalPreviewFlag({})).toBe(false);
  });

  it("maps legacy request into canonical payload", () => {
    const request: RenderPreviewRequest = {
      template_id: 77,
      dossier_id: 13,
      document_type: "offer",
      audience: "client",
      block_types: ["offer_short_description"],
      quote_context: {
        client_name: "Client preview",
        quantity: 3,
        dimensions: {
          width_mm: 1000,
          height_mm: 500,
        },
      },
      render_mode: "preview",
    };

    const mapped = mapLegacyRequestToCanonicalPayload(request);

    expect(mapped.context).toBe("quote_preview");
    expect(mapped.block_types).toEqual(["offer_short_description"]);

    expect(mapped.source_payload).toEqual({
      preview: {
        document_type: "offer",
        audience: "client",
        render_mode: "preview",
      },
      quote: {
        client_name: "Client preview",
        quantity: 3,
      },
      dimensions: {
        width_mm: 1000,
        height_mm: 500,
        depth_mm: undefined,
      },
      selection: {
        block_types: ["offer_short_description"],
      },
      legacy_reference: {
        template_id: 77,
        dossier_id: 13,
      },
    });
  });

  it("normalizes mapper defaults safely", () => {
    const mapped = mapLegacyRequestToCanonicalPayload({
      template_id: 9,
      block_types: [],
      quote_context: { quantity: 0 },
    });

    expect(mapped.block_types).toBeUndefined();
    expect(mapped.source_payload).toMatchObject({
      preview: {
        document_type: "offer",
        audience: "client",
        render_mode: "preview",
      },
      quote: {
        quantity: 1,
      },
      legacy_reference: {
        template_id: 9,
        dossier_id: null,
      },
    });
  });

  it("computes canonical eligibility from legacy request", () => {
    expect(
      isLegacyRequestEligibleForCanonical({ template_id: 1, block_types: ["x"] })
    ).toBe(true);

    expect(
      isLegacyRequestEligibleForCanonical({ template_id: 1, block_types: [] })
    ).toBe(false);

    expect(
      isLegacyRequestEligibleForCanonical({ template_id: null, block_types: ["x"] })
    ).toBe(false);
  });

  it("selects legacy when flag is disabled", () => {
    const selection = selectOutputBlocksPreviewRoute(
      { template_id: 1, block_types: ["offer_short_description"] },
      false
    );

    expect(selection).toEqual({
      target: "legacy",
      reason: "feature_flag_disabled",
    });
  });

  it("selects legacy for ineligible request even when flag is enabled", () => {
    const missingBlockTypes = selectOutputBlocksPreviewRoute(
      { template_id: 1, block_types: [] },
      true
    );
    expect(missingBlockTypes).toEqual({
      target: "legacy",
      reason: "missing_block_types",
    });

    const invalidTemplate = selectOutputBlocksPreviewRoute(
      { template_id: 0, block_types: ["offer_short_description"] },
      true
    );
    expect(invalidTemplate).toEqual({
      target: "legacy",
      reason: "invalid_template_id",
    });
  });

  it("selects canonical only when flag is enabled and request is eligible", () => {
    const selection = selectOutputBlocksPreviewRoute(
      { template_id: 42, block_types: ["offer_short_description"] },
      true
    );

    expect(selection).toEqual({
      target: "canonical",
      reason: "eligible",
    });
  });

  it("normalizes canonical response into legacy response skeleton", () => {
    const canonical: CanonicalOutputBlockPreviewResponse = {
      preview_only: true,
      context: "quote_preview",
      rendered_blocks: [
        {
          block_id: "block-1",
          block_type: "offer_short_description",
          title: "Offer Short Description",
          approval_status: "approved",
          rendered_text: "Text",
          variables_used: { product_name: "Panel" },
          source_fields_used: ["identity.product_name"],
          skipped: false,
          skip_reason: null,
          warnings: [{ code: "warn", message: "warning message" }],
          blockers: [{ code: "blocker" }],
        },
      ],
      warnings: [{ message: "top warning" }],
      blockers: [{ code: "top_blocker" }],
    };

    const request: RenderPreviewRequest = {
      template_id: 11,
      dossier_id: 2,
      document_type: "offer",
      audience: "client",
      render_mode: "preview",
    };

    const normalized = normalizeCanonicalResponseToLegacySkeleton(canonical, request);

    expect(normalized.persisted).toBe(false);
    expect(normalized.trace).toEqual({
      source: "canonical_output_blocks_preview",
      no_persist: true,
      changed_entities: [],
      live_changes_affect_accepted_orders: false,
    });
    expect(normalized.blocks).toHaveLength(1);
    expect(normalized.blocks[0].variables_used[0]).toEqual({
      name: "product_name",
      source_field: "",
      value: "Panel",
      resolved: true,
    });
    expect(normalized.warnings).toEqual(["top warning"]);
    expect(normalized.blockers).toEqual(["top_blocker"]);
  });

  it("normalization wrapper returns legacy response untouched for legacy target", () => {
    const legacy: RenderPreviewResponse = {
      persisted: false,
      template_id: 1,
      dossier_id: null,
      document_type: "offer",
      audience: "client",
      render_mode: "preview",
      blocks: [],
      warnings: [],
      blockers: [],
      trace: {
        source: "legacy",
        no_persist: true,
        changed_entities: [],
        live_changes_affect_accepted_orders: false,
      },
    };

    const result = normalizeOutputBlocksPreviewResponseSkeleton({
      target: "legacy",
      request: { template_id: 1, block_types: ["a"] },
      legacyResponse: legacy,
    });

    expect(result).toBe(legacy);
  });

  it("normalization wrapper throws when required response is missing", () => {
    expect(() =>
      normalizeOutputBlocksPreviewResponseSkeleton({
        target: "legacy",
        request: { template_id: 1 },
      })
    ).toThrow(/legacyResponse is required/);

    expect(() =>
      normalizeOutputBlocksPreviewResponseSkeleton({
        target: "canonical",
        request: { template_id: 1, block_types: ["x"] },
      })
    ).toThrow(/canonicalResponse is required/);
  });
});
