import { describe, expect, it } from "vitest";
import {
  buildClientAnalyzerStateFromSvgSourceText,
  needsClientAnalyzerHydrationFromServerUpload,
  readSvgSourceMetaFromPayload,
} from "./intakeV6ServerUploadHydrationBridge";

const SAMPLE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="40mm" viewBox="0 0 100 40">
  <rect width="100" height="40" fill="#C5C6C6"/>
  <path fill="#E31E24" d="M10 10 h20 v20 h-20 z M40 10 h15 v20 h-15 z M70 10 h20 v20 h-20 z"/>
</svg>`;

describe("server upload hydration bridge", () => {
  it("needs hydration when source text exists without client analysis report", () => {
    expect(
      needsClientAnalyzerHydrationFromServerUpload(
        {
          svg_source_text: SAMPLE_SVG,
          svg_source: { file_name: "x.svg", file_size_bytes: 10 },
          svg_analysis_json: null,
        },
        false,
      ),
    ).toBe(true);
  });

  it("does not hydrate when local analyzer already ready", () => {
    expect(
      needsClientAnalyzerHydrationFromServerUpload(
        { svg_source_text: SAMPLE_SVG, svg_analysis_json: null },
        true,
      ),
    ).toBe(false);
  });

  it("does not hydrate when nest2 analysis already has layerRoleConfirmation", () => {
    expect(
      needsClientAnalyzerHydrationFromServerUpload(
        {
          svg_source_text: SAMPLE_SVG,
          svg_analysis_json: { layerRoleConfirmation: { layers: [] } },
        },
        false,
      ),
    ).toBe(false);
  });

  it("builds Page 1 analyzer state from svg_source_text via client analyzer", () => {
    const meta = readSvgSourceMetaFromPayload({
      svg_source_text: SAMPLE_SVG,
      svg_source: { file_name: "bridge.svg", file_size_bytes: SAMPLE_SVG.length },
    });
    expect(meta).toBeTruthy();
    const hydrated = buildClientAnalyzerStateFromSvgSourceText({
      svgText: meta!.svgText,
      fileName: meta!.fileName,
      fileSizeBytes: meta!.fileSizeBytes,
    });
    expect(hydrated.analyzerReport.layers.length).toBeGreaterThan(0);
    expect(hydrated.layerRoleConfirmation.layers.length).toBeGreaterThan(0);
    expect(hydrated.svgSource).toContain("<svg");
    expect(hydrated.layerRoleConfirmation.layers.every((l) => l.confirmationState === "pending")).toBe(
      true,
    );
  });
});
