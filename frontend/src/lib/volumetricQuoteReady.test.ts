import { describe, expect, it } from "vitest";
import {
  classifyQuoteGateItems,
  deriveVolumetricCommercialReadinessStatus,
  extractQuoteReadinessFromLineItems,
  groupQuoteGateBlockers,
  humanizeQuoteBlocker,
  humanizeQuoteWarning,
  summarizeVolumetricQuoteGate,
  type VolumetricQuoteGate,
} from "@/lib/volumetricQuoteReady";

describe("volumetricQuoteReady", () => {
  it("humanizes vector blockers", () => {
    expect(humanizeQuoteBlocker("letters_vector_file_required")).toContain("vector");
    expect(humanizeQuoteBlocker("vector_layer_mapping_pending")).toContain("layer");
  });

  it("humanizes ACM separate template", () => {
    expect(
      humanizeQuoteBlocker("captured_option_requires_separate_template:mounting_system=acm_panel")
    ).toContain("ACM");
  });

  it("groups blockers by section", () => {
    const gate: VolumetricQuoteGate = {
      classified: {
        vector_blockers: ["letters_vector_file_required"],
        geometry_blockers: ["quote_input_missing:letter_count"],
        cost_blockers: ["WORKCENTER_RATE_MISSING"],
      },
    };
    const grouped = groupQuoteGateBlockers(gate);
    expect(grouped.vector).toHaveLength(1);
    expect(grouped.geometry).toHaveLength(1);
    expect(grouped.cost).toHaveLength(1);
    expect(grouped.metadata).toHaveLength(0);
  });

  it("humanizes known volumetric warnings with code preserved in classify", () => {
    expect(humanizeQuoteWarning("operations_missing")).toContain("operațiile");
    const items = classifyQuoteGateItems({
      can_create_commercial_quote: true,
      requires_acknowledgement: true,
      warnings: ["operations_missing"],
      classified: { acknowledgement_pending: ["operations_missing"] },
    });
    expect(items.some((i) => i.code === "operations_missing" && i.status === "needs_acknowledgement")).toBe(
      true
    );
  });

  it("derives readiness status taxonomy from gate", () => {
    expect(
      deriveVolumetricCommercialReadinessStatus({
        can_create_commercial_quote: true,
        requires_acknowledgement: false,
        warnings: [],
      })
    ).toBe("ready");
    expect(
      deriveVolumetricCommercialReadinessStatus({
        can_create_commercial_quote: true,
        requires_acknowledgement: true,
      })
    ).toBe("requires_acknowledgement");
    expect(
      deriveVolumetricCommercialReadinessStatus({
        can_create_commercial_quote: false,
        blockers: ["x"],
      })
    ).toBe("blocked");
  });

  it("extracts quote_gate from line_items wrapper", () => {
    const raw = JSON.stringify({
      line_items: {
        product_definition: { product_id: "TPL-VOLUMETRIC-LETTERS" },
        cost_result: { breakdown: [] },
        pricing: { margin_pct: 25 },
        price: { net: 100, gross: 119 },
      },
      readiness_result: {
        overall_status: "needs_review",
        quote_gate: {
          can_create_commercial_quote: true,
          requires_acknowledgement: false,
          warnings: ["vector_analysis_pending"],
        },
      },
    });
    const snap = extractQuoteReadinessFromLineItems(raw);
    expect(snap?.quoteGate?.can_create_commercial_quote).toBe(true);
    expect(snap?.templateCode).toBe("TPL-VOLUMETRIC-LETTERS");
  });

  it("summarizes blocker and ack counts", () => {
    const summary = summarizeVolumetricQuoteGate({
      can_create_commercial_quote: true,
      requires_acknowledgement: true,
      blockers: [],
      warnings: ["operations_missing", "vector_analysis_pending"],
      classified: { acknowledgement_pending: ["operations_missing"] },
    });
    expect(summary.blockerCount).toBe(0);
    expect(summary.acknowledgementPendingCount).toBe(1);
    expect(summary.warningCount).toBe(1);
  });
});
