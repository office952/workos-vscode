import { describe, expect, it } from "vitest";
import {
  aggregateLayerSimulations,
  layerStatusLabel,
  suggestionsToQuoteInputStrings,
  type SvgLayerAnalysisRow,
} from "./svgLayerAnalysis";

const volumetricLayer: SvgLayerAnalysisRow = {
  svg_layer_id: "l1",
  svg_layer_name: "TPL-VOLUMETRIC-LETTERS",
  mapped_template_code: "TPL-VOLUMETRIC-LETTERS",
  mapping_status: "mapped",
  suggested_template_code: null,
  human_description: "Litere volumetrice luminoase / Product 001",
  detected_kind: "volumetric_letters",
  metrics: {
    metrics_confidence: "estimated",
    path_area_m2: 2.88,
    path_perimeter_m: 18,
  },
  quote_input_suggestions: {
    letter_face_area_m2: 2.88,
    letter_perimeter_m: 18,
    letter_count: null,
    mounting_template_area_m2: 2.88,
  },
  blockers: [],
  warnings: [],
};

describe("svgLayerAnalysis", () => {
  it("labels mapped volumetric layer as calculable", () => {
    expect(layerStatusLabel(volumetricLayer)).toBe(
      "Calcul preliminar disponibil"
    );
  });

  it("labels template missing layer", () => {
    expect(
      layerStatusLabel({
        ...volumetricLayer,
        svg_layer_name: "TPL-UNKNOWN-FUTURE",
        mapped_template_code: null,
        mapping_status: "unmapped",
        blockers: ["template_missing_for_svg_layer"],
      })
    ).toBe("Template lipsă");
  });

  it("labels mapped ACM casetted layer with manual geometry", () => {
    expect(
      layerStatusLabel({
        ...volumetricLayer,
        svg_layer_name: "TPL-ACM-CASSETTED-PANEL",
        mapped_template_code: "TPL-ACM-CASSETTED-PANEL",
        detected_kind: "acm_casetted_panel",
        blockers: ["manual_geometry_required"],
      })
    ).toBe("Necesită date manuale");
  });

  it("converts suggestions to quote input strings without nulls", () => {
    expect(
      suggestionsToQuoteInputStrings(volumetricLayer.quote_input_suggestions)
    ).toEqual({
      letter_face_area_m2: "2.88",
      letter_perimeter_m: "18",
      mounting_template_area_m2: "2.88",
    });
  });

  it("aggregates partial multi-layer totals", () => {
    const agg = aggregateLayerSimulations([
      {
        layer: volumetricLayer,
        template_id: 1,
        simulation: {
          cost_result: { total_cost: 706.61 },
          status: "blocked",
        } as never,
        error: null,
      },
      {
        layer: {
          ...volumetricLayer,
          svg_layer_name: "TPL-ACM-CASSETTED-PANEL",
          mapped_template_code: null,
          mapping_status: "unmapped",
          blockers: ["template_missing_for_svg_layer"],
        },
        template_id: null,
        simulation: null,
        error: null,
      },
    ]);
    expect(agg.preliminary_total).toBe(706.61);
    expect(agg.is_partial).toBe(true);
    expect(agg.unmapped_count).toBe(1);
  });
});
