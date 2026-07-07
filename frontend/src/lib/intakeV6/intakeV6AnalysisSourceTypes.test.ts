import { describe, expect, it } from "vitest";
import {
  INTAKE_V6_ANALYSIS_SOURCES,
  canCreateIntakeV6WorkspaceFromSource,
  getIntakeV6AnalysisSourceDefinition,
} from "./intakeV6AnalysisSourceTypes";

describe("intakeV6AnalysisSourceTypes", () => {
  it("marks the SVG source definition as active", () => {
    const svgSource = getIntakeV6AnalysisSourceDefinition("svg_analyzer_intake_v6");

    expect(svgSource).toEqual(
      expect.objectContaining({
        sourceType: "svg",
        status: "active",
      }),
    );
  });

  it("allows the SVG source definition to create a workspace", () => {
    const svgSource = getIntakeV6AnalysisSourceDefinition("svg_analyzer_intake_v6");

    expect(svgSource).toBeDefined();
    expect(canCreateIntakeV6WorkspaceFromSource(svgSource!)).toBe(true);
  });

  it("includes an Image Analyzer source definition", () => {
    expect(INTAKE_V6_ANALYSIS_SOURCES).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourceType: "image",
          methodId: "image_analyzer_intake_v6_preview",
        }),
      ]),
    );
  });

  it("marks the Image Analyzer source definition as preview-only", () => {
    const imageSource = getIntakeV6AnalysisSourceDefinition("image_analyzer_intake_v6_preview");

    expect(imageSource).toEqual(
      expect.objectContaining({
        sourceType: "image",
        status: "preview_only",
      }),
    );
  });

  it("does not allow the Image Analyzer source definition to create a workspace", () => {
    const imageSource = getIntakeV6AnalysisSourceDefinition("image_analyzer_intake_v6_preview");

    expect(imageSource).toBeDefined();
    expect(canCreateIntakeV6WorkspaceFromSource(imageSource!)).toBe(false);
  });
});