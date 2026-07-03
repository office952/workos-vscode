import { describe, expect, it } from "vitest";
import {
  buildSafeSvgPreview,
  buildVectorStudioInfo,
  hasLettersLayerMapped,
  humanizeLayerMappingStatus,
  humanizeVectorAnalysisStatus,
  humanizeVectorParseStatus,
  resolvePreviewUnavailableMessage,
  svgPreviewDataUrl,
  syncVectorAnalysisSummaryToSpec,
} from "@/lib/vectorStudioPreview";
import type { SvgLayerAnalysisResult } from "@/lib/svgLayerAnalysis";

const SAMPLE_ANALYSIS: SvgLayerAnalysisResult = {
  parse_status: "parsed_sanitized",
  layers: [
    {
      svg_layer_id: "1",
      svg_layer_name: "Layer_x0020_1",
      mapped_template_code: "TPL-VOLUMETRIC-LETTERS",
      mapping_status: "mapped_manual",
      suggested_template_code: null,
      human_description: "letters",
      detected_kind: "unknown",
      metrics: { metrics_confidence: "unavailable" },
      quote_input_suggestions: {},
      blockers: [],
      warnings: [],
      mapped_by: "manual",
    },
  ],
  summary: { layers_found: 1 },
  warnings: ["svg_sanitized_doctype_removed"],
  sanitization: { analysis_sanitized: true },
  preview_svg: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
};

describe("vectorStudioPreview", () => {
  it("strips script tags from preview SVG", () => {
    const raw =
      '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><rect width="10"/></svg>';
    const safe = buildSafeSvgPreview(raw);
    expect(safe).not.toContain("<script");
    expect(safe).toContain("<rect");
  });

  it("rejects DOCTYPE in preview SVG", () => {
    const raw = '<!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg"></svg>';
    expect(buildSafeSvgPreview(raw)).toBeNull();
  });

  it("builds data URL for safe preview", () => {
    const url = svgPreviewDataUrl('<svg xmlns="http://www.w3.org/2000/svg"></svg>');
    expect(url.startsWith("data:image/svg+xml")).toBe(true);
  });

  it("detects letters layer mapping", () => {
    expect(hasLettersLayerMapped({ Layer_Litere: "TPL-VOLUMETRIC-LETTERS" })).toBe(true);
    expect(hasLettersLayerMapped({ Layer_Bare: "support_bars" })).toBe(false);
  });

  it("saved mapping without analysis rows does not show layers detected 0", () => {
    const info = buildVectorStudioInfo(
      {
        vector_file_name: "litere.svg",
        vector_file_type: "svg",
        vector_analysis_status: "analyzed",
        svg_layer_mappings: { Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS" },
      },
      null
    );
    expect(info.layersDetectedValue).not.toBe("0");
    expect(info.savedMappingsCount).toBe(1);
    expect(info.savedMappingsList).toContain("Layer_x0020_1 → TPL-VOLUMETRIC-LETTERS");
    expect(info.lettersLayerLabel).toBe("mapat manual");
  });

  it("shows layer count from live analysis", () => {
    const info = buildVectorStudioInfo(
      {
        vector_file_name: "litere.svg",
        vector_file_type: "svg",
        vector_analysis_status: "analyzed",
        svg_layer_mappings: { Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS" },
      },
      SAMPLE_ANALYSIS
    );
    expect(info.layersDetectedValue).toBe("1");
    expect(info.hasLivePreview).toBe(true);
  });

  it("preview absent after refresh shows correct explanation", () => {
    const info = buildVectorStudioInfo(
      {
        vector_file_name: "litere.svg",
        vector_file_type: "svg",
        vector_analysis_status: "analyzed",
        svg_layer_mappings: { Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS" },
      },
      null
    );
    const msg = resolvePreviewUnavailableMessage(info, true, false, false);
    expect(msg).toContain("refresh");
    expect(msg).toContain("Reanalizează");
  });

  it("sync summary does not invent geometry fields", () => {
    const next = syncVectorAnalysisSummaryToSpec(
      { svg_layer_mappings: { Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS" } },
      SAMPLE_ANALYSIS
    );
    expect(next.vector_parse_status).toBe("parsed_sanitized");
    expect(next.vector_preview_available).toBe(true);
    expect(next.vector_detected_layers_summary?.length).toBe(1);
    expect(next.letter_count).toBeUndefined();
    expect(next.letter_face_area_m2).toBeUndefined();
  });

  it("support_bars mapping does not count as letters mapped", () => {
    const info = buildVectorStudioInfo(
      {
        vector_file_type: "svg",
        vector_analysis_status: "analyzed",
        svg_layer_mappings: { Layer_Bare: "support_bars" },
      },
      null
    );
    expect(info.lettersMapped).toBe(false);
    expect(info.lettersLayerLabel).toBe("lipsă");
    expect(info.savedMappingsCount).toBe(1);
  });

  it("builds studio info without invented metrics", () => {
    const info = buildVectorStudioInfo(
      {
        vector_file_name: "litere.svg",
        vector_file_type: "svg",
        vector_analysis_status: "analyzed",
        svg_layer_mappings: { Layer_Litere: "TPL-VOLUMETRIC-LETTERS" },
      },
      {
        parse_status: "parsed_sanitized",
        layers: [],
        summary: { layers_found: 2 },
        warnings: ["svg_sanitized_doctype_removed"],
        sanitization: { analysis_sanitized: true },
      }
    );
    expect(info.lettersMapped).toBe(true);
    expect(info.hasMetrics).toBe(false);
    expect(info.warnings.some((w) => w.includes("metrici"))).toBe(true);
  });

  it("does not crash for E2E WARN legacy spec with geometry estimate only", () => {
    const info = buildVectorStudioInfo(
      {
        width_mm: 4800,
        height_mm: 600,
        depth_mm: 60,
        return_depth_mm: 60,
        vector_file_name: "e2e-volumetric-letters.svg",
        vector_file_type: "svg",
        vector_analysis_status: "manual_review_approved",
        vector_manual_review_approved: true,
        vector_geometry_analyzed: true,
        vector_geometry_confidence: "high",
        geometry_source: "svg_suggestion_confirmed",
        svg_layer_mappings: { Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS" },
        vector_suggested_assembly_width_mm: 4800,
      },
      null
    );
    expect(info.lettersMapped).toBe(true);
    expect(info.warnings.some((w) => w.includes("Nu s-au extras metrici"))).toBe(false);
  });

  it("humanizes vector statuses for operator UI", () => {
    expect(humanizeVectorParseStatus("parsed_sanitized")).toBe("SVG analizat în siguranță");
    expect(humanizeVectorAnalysisStatus("manual_review_approved")).toBe(
      "Review manual confirmat"
    );
    expect(humanizeLayerMappingStatus("mapped", "manual")).toContain("manual");
  });
});
