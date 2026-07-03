import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "./intakeV6LayerRoleBridge";
import { ARTWORK_ONLY_REQUIRES_DECISION_CODE } from "./intakeV6ArtworkOnlyGuard";
import { mapAnalyzerReportToModuleDetectionResult } from "./mapAnalyzerReportToModuleDetectionResult";
import { MODULE_DETECTION_RESULT_SCHEMA_VERSION } from "./moduleDetectionResult";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "../../../..");
const fixtureDir = join(repoRoot, "fisiere-teste");

function analyzeFixture(path: string) {
  const svg = readFileSync(path, "utf8");
  return analyzeSvgString(svg, path, svg.length).report;
}

function mapFixture(path: string) {
  const report = analyzeFixture(path);
  return { report, result: mapAnalyzerReportToModuleDetectionResult(report) };
}

describe("ModuleDetectionResult contract mapper", () => {
  it("regression-v6-1layer-letters produces coherent letter module and layers", () => {
    const { result } = mapFixture(join(fixtureDir, "regression-v6-1layer-letters.svg"));

    expect(result.schema_version).toBe(MODULE_DETECTION_RESULT_SCHEMA_VERSION);
    expect(result.source).toBe("svg_analyzer");
    expect(result.detected_layers.length).toBeGreaterThan(0);
    expect(result.detected_layers.some((layer) => layer.has_letter_path_geometry)).toBe(true);

    const lettersModule = result.detected_modules.find((module) => module.module_kind === "volumetric_letters");
    expect(lettersModule).toBeDefined();
    expect(lettersModule?.source_layer_keys.length).toBeGreaterThan(0);
    expect(result.requires_operator_confirmation).toBe(true);
  });

  it("pbl-layere includes printed_artwork module and preserves policromie layer name", () => {
    const { result } = mapFixture(join(fixtureDir, "pbl-layere.svg"));

    const policromieLayer = result.detected_layers.find(
      (layer) => layer.layer_name === "Layer_x0020_3" || layer.layer_id.includes("Layer"),
    );
    expect(policromieLayer).toBeDefined();
    expect(result.detected_layers.some((layer) => layer.layer_name === "unassigned")).toBe(false);

    const artworkModule = result.detected_modules.find(
      (module) => module.module_kind === "printed_artwork" || module.module_kind === "logo",
    );
    expect(artworkModule).toBeDefined();

    const lettersModule = result.detected_modules.find((module) => module.module_kind === "volumetric_letters");
    expect(lettersModule).toBeDefined();
    expect(lettersModule?.source_layer_keys.length).toBeGreaterThan(0);

    const printedLayer = result.detected_layers.find((layer) => layer.auto_role === "printed_artwork");
    expect(printedLayer).toBeDefined();
  });

  it("regression-v6-policromie-only requires operator confirmation and omits false letter module", () => {
    const report = analyzeFixture(join(fixtureDir, "regression-v6-policromie-only.svg"));
    const result = mapAnalyzerReportToModuleDetectionResult(report);

    expect(result.requires_operator_confirmation).toBe(true);
    expect(result.blockers.some((blocker) => blocker.code === ARTWORK_ONLY_REQUIRES_DECISION_CODE)).toBe(true);
    expect(result.detected_modules.some((module) => module.module_kind === "volumetric_letters")).toBe(false);

    const artworkModule = result.detected_modules.find((module) => module.module_kind === "printed_artwork");
    expect(artworkModule).toBeDefined();

    const policromieLayer = result.detected_layers.find((layer) => layer.layer_name === "artwork-policromie");
    expect(policromieLayer).toBeDefined();
    expect(policromieLayer?.auto_role).toBe("printed_artwork");
    expect(policromieLayer?.paint_evidence.paintKind).toBe("policromie");

    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    const confirmedResult = mapAnalyzerReportToModuleDetectionResult(report, {
      layerRoleConfirmation: confirmed,
    });
    expect(confirmedResult.detected_modules.some((module) => module.module_kind === "volumetric_letters")).toBe(
      false,
    );
    expect(confirmedResult.raw_analyzer_summary?.confirmation_status).toBe("complete");
  });

  it("non-path artwork-policromie group stays semantic layer, not unassigned", () => {
    const svg = readFileSync(join(fixtureDir, "regression-v6-policromie-only.svg"), "utf8");
    const { report } = analyzeSvgString(svg, "regression-v6-policromie-only.svg", svg.length);
    const result = mapAnalyzerReportToModuleDetectionResult(report);

    expect(result.detected_layers.some((layer) => layer.layer_name === "unassigned")).toBe(false);
    expect(result.detected_layers.some((layer) => layer.layer_name === "artwork-policromie")).toBe(true);
  });

  it("pbl.svg produces two letter source layers in volumetric module", () => {
    const { result } = mapFixture(join(fixtureDir, "pbl.svg"));

    const lettersModule = result.detected_modules.find((module) => module.module_kind === "volumetric_letters");
    expect(lettersModule).toBeDefined();
    expect(lettersModule?.source_layer_keys.length).toBeGreaterThanOrEqual(2);
  });

  it("mapper is pure — repeated calls produce identical output", () => {
    const report = analyzeFixture(join(fixtureDir, "regression-v6-1layer-letters.svg"));
    const first = mapAnalyzerReportToModuleDetectionResult(report, { analysisHash: "abc123" });
    const second = mapAnalyzerReportToModuleDetectionResult(report, { analysisHash: "abc123" });
    expect(second).toEqual(first);
    expect(second.recommended_forms).toEqual([]);
    expect(second.recommended_templates).toEqual([]);
  });
});
