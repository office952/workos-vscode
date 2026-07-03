import { describe, expect, it } from "vitest";
import type { SvgVectorDetectedLayer } from "@/lib/svgVectorAnalysis";
import {
  applySuggestedLayerRoles,
  buildVectorIntakeRepairMissing,
  confirmPrimaryLettersLayer,
  deriveSvgParseUiStatus,
  hasGeometryEstimateInSpec,
  parseStatusLabel,
  scoreLettersLayerCandidate,
  suggestPrimaryLettersLayer,
  filterVectorReviewWarningsForLocalParse,
  isFilenameOnlyWithoutSvgParse,
} from "./svgIntakeFlow";

function layer(
  partial: Partial<SvgVectorDetectedLayer> & Pick<SvgVectorDetectedLayer, "id" | "label">
): SvgVectorDetectedLayer {
  return {
    element_count: 1,
    suggested_role: "unknown",
    confirmed_role: "unknown",
    is_inkscape_layer: false,
    ...partial,
  };
}

describe("svgIntakeFlow", () => {
  it("deriveSvgParseUiStatus covers selection and parse outcomes", () => {
    expect(deriveSvgParseUiStatus({})).toBe("not_selected");
    expect(deriveSvgParseUiStatus({ fileName: "a.svg", analyzing: true })).toBe("parsing");
    expect(deriveSvgParseUiStatus({ fileName: "a.svg", parseOk: true })).toBe("parsed");
    expect(
      deriveSvgParseUiStatus({ fileName: "a.svg", parseOk: true, warningCount: 2 })
    ).toBe("parsed_with_warnings");
    expect(
      deriveSvgParseUiStatus({ fileName: "a.svg", parseOk: false, parseError: "bad" })
    ).toBe("failed");
  });

  it("parseStatusLabel returns Romanian labels", () => {
    expect(parseStatusLabel("parsed")).toMatch(/succes/i);
    expect(parseStatusLabel("failed")).toMatch(/eșuat/i);
  });

  it("suggestPrimaryLettersLayer prefers LITERE over DIBOND/CADRU", () => {
    const layers = [
      layer({ id: "cadru", label: "CADRU", element_count: 5 }),
      layer({ id: "litere", label: "LITERE", element_count: 12, suggested_role: "volumetric_letters" }),
      layer({ id: "dibond", label: "DIBOND", element_count: 8, suggested_role: "support_panel" }),
    ];
    const suggestion = suggestPrimaryLettersLayer(layers);
    expect(suggestion?.layerId).toBe("litere");
    expect(suggestion?.confidence).not.toBe("low");
  });

  it("suggestPrimaryLettersLayer prefers LITERE over Emblema even when Emblema has more elements", () => {
    const layers = [
      layer({ id: "cadru", label: "CADRU", element_count: 10, suggested_role: "metal_frame" }),
      layer({
        id: "litere",
        label: "Litere_x0020_volumetrice",
        element_count: 2,
        suggested_role: "volumetric_letters",
      }),
      layer({ id: "emblema", label: "Emblema", element_count: 510, suggested_role: "unknown" }),
    ];
    const suggestion = suggestPrimaryLettersLayer(layers);
    expect(suggestion?.layerId).toBe("litere");
    expect(suggestion?.confidence).not.toBe("low");
  });

  it("suggestPrimaryLettersLayer uses inkscape-style names", () => {
    const layers = [
      layer({ id: "l1", label: "Support panel", element_count: 3 }),
      layer({ id: "l2", label: "Letters face", element_count: 7 }),
    ];
    expect(scoreLettersLayerCandidate(layers[1]!)).toBeGreaterThan(
      scoreLettersLayerCandidate(layers[0]!)
    );
    expect(suggestPrimaryLettersLayer(layers)?.layerId).toBe("l2");
  });

  it("suggestPrimaryLettersLayer falls back by element count", () => {
    const layers = [
      layer({ id: "a", label: "Layer A", element_count: 2 }),
      layer({ id: "b", label: "Layer B", element_count: 9 }),
    ];
    const suggestion = suggestPrimaryLettersLayer(layers);
    expect(suggestion?.layerId).toBe("b");
    expect(suggestion?.confidence).toBe("low");
  });

  it("applySuggestedLayerRoles and confirmPrimaryLettersLayer update roles", () => {
    const raw = [layer({ id: "LITERE", label: "LITERE", element_count: 4 })];
    const withRoles = applySuggestedLayerRoles(raw);
    expect(withRoles[0]?.confirmed_role).not.toBe("unknown");
    const confirmed = confirmPrimaryLettersLayer(withRoles, "LITERE");
    expect(confirmed[0]?.confirmed_role).toBe("volumetric_letters");
  });

  it("buildVectorIntakeRepairMissing lists vector pathway gaps", () => {
    expect(buildVectorIntakeRepairMissing({ intake_input_pathway: "manual" })).toEqual([]);
    expect(buildVectorIntakeRepairMissing({ intake_input_pathway: "vector" })).toContain(
      "Încarcă/selectează SVG"
    );
    const withFile = {
      intake_input_pathway: "vector" as const,
      vector_file_name: "logo.svg",
      vector_svg_analyzed: true,
      vector_detected_layer_count: 2,
    };
    const missing = buildVectorIntakeRepairMissing(withFile);
    expect(missing).toContain("Confirmă layerul principal pentru litere");
    expect(missing).toContain("Confirmă maparea layerelor SVG");
  });

  it("hasGeometryEstimateInSpec detects saved geometry fields", () => {
    expect(hasGeometryEstimateInSpec(null)).toBe(false);
    expect(
      hasGeometryEstimateInSpec({
        vector_geometry_analyzed: true,
        vector_suggested_assembly_width_mm: 200,
      })
    ).toBe(true);
  });

  it("isFilenameOnlyWithoutSvgParse detects typed name without pick", () => {
    expect(
      isFilenameOnlyWithoutSvgParse({ fileName: "a.svg", hasFilePickMetadata: false })
    ).toBe(true);
    expect(
      isFilenameOnlyWithoutSvgParse({
        fileName: "a.svg",
        hasFilePickMetadata: true,
        parseOk: true,
      })
    ).toBe(false);
  });

  it("filterVectorReviewWarningsForLocalParse hides stale nemapat when layers mapped", () => {
    const filtered = filterVectorReviewWarningsForLocalParse(
      ["Layer principal litere nemapat.", "Alt mesaj"],
      {
        detectedLayers: [
          {
            id: "LITERE",
            label: "LITERE",
            element_count: 2,
            suggested_role: "volumetric_letters",
            confirmed_role: "volumetric_letters",
            is_inkscape_layer: true,
          },
        ],
      }
    );
    expect(filtered).not.toContain("Layer principal litere nemapat.");
    expect(filtered).toContain("Alt mesaj");
  });
});
