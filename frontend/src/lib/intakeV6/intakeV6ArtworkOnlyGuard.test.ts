import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "./intakeV6LayerRoleBridge";
import { deriveArtworkFinishesFromAnalyzer } from "./intakeV4ArtworkFinish";
import { deriveLetterGroupsFromAnalyzer } from "./intakeV4LetterGroups";
import {
  ARTWORK_ONLY_REQUIRES_DECISION_CODE,
  ARTWORK_ONLY_STEP1_MESSAGE,
  detectArtworkOnlyRequiresDecision,
  resolveArtworkOnlyFatalBlockers,
} from "./intakeV6ArtworkOnlyGuard";
import { formatQuoteHandoffBlocker } from "./intakeV4QuoteHandoffReadiness";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "../../../..");
const fixtureDir = join(repoRoot, "fisiere-teste");
const analyzerFixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../svgAnalyzer/fixtures");

function analyzeFixture(path: string) {
  const svg = readFileSync(path, "utf8");
  return analyzeSvgString(svg, path, svg.length).report;
}

describe("intakeV6ArtworkOnlyGuard", () => {
  it("detects policromie-only SVG as artwork-only requiring decision", () => {
    const report = analyzeFixture(join(fixtureDir, "regression-v6-policromie-only.svg"));
    expect(detectArtworkOnlyRequiresDecision(report, report.layerRoleConfirmation)).toBe(true);

    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(confirmed.confirmationStatus).toBe("complete");
    expect(confirmed.layers.some((layer) => layer.confirmedRole === "face")).toBe(false);
    expect(confirmed.layers.some((layer) => layer.confirmedRole === "printed_artwork")).toBe(true);

    const letterGroups = deriveLetterGroupsFromAnalyzer(report, confirmed);
    expect(letterGroups).toEqual([]);

    const artworkFinishes = deriveArtworkFinishesFromAnalyzer(report, confirmed);
    expect(artworkFinishes.length).toBeGreaterThan(0);
  });

  it("does not classify one-layer letters fixture as artwork-only", () => {
    const report = analyzeFixture(join(fixtureDir, "regression-v6-1layer-letters.svg"));
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(detectArtworkOnlyRequiresDecision(report, confirmed)).toBe(false);
    expect(deriveLetterGroupsFromAnalyzer(report, confirmed).length).toBeGreaterThan(0);
  });

  it("does not classify two-layer letters fixture as artwork-only", () => {
    const report = analyzeFixture(join(fixtureDir, "pbl.svg"));
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(detectArtworkOnlyRequiresDecision(report, confirmed)).toBe(false);
    expect(deriveLetterGroupsFromAnalyzer(report, confirmed).length).toBe(2);
  });

  it("does not classify mixed letters + artwork as artwork-only", () => {
    const report = analyzeFixture(join(fixtureDir, "pbl-layere.svg"));
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(detectArtworkOnlyRequiresDecision(report, confirmed)).toBe(false);
    expect(deriveLetterGroupsFromAnalyzer(report, confirmed).length).toBeGreaterThan(0);
    expect(deriveArtworkFinishesFromAnalyzer(report, confirmed).length).toBeGreaterThan(0);
  });

  it("maps artwork-only blocker to clear Confirm message", () => {
    expect(formatQuoteHandoffBlocker(ARTWORK_ONLY_REQUIRES_DECISION_CODE)).toContain(
      "Nu există straturi de litere volumetrice confirmate",
    );
    expect(formatQuoteHandoffBlocker(ARTWORK_ONLY_REQUIRES_DECISION_CODE)).not.toContain("Oracal");
  });

  it("replaces missing face oracal blocker when artwork-only", () => {
    const report = analyzeFixture(join(fixtureDir, "regression-v6-policromie-only.svg"));
    const blockers = resolveArtworkOnlyFatalBlockers(report, report.layerRoleConfirmation, [
      "missing_face_oracal_color:artwork-policromie",
    ]);
    expect(blockers).toContain(ARTWORK_ONLY_REQUIRES_DECISION_CODE);
    expect(blockers.some((code) => code.startsWith("missing_face_oracal_color:"))).toBe(false);
  });

  it("exposes Step 1 operator message constant", () => {
    expect(ARTWORK_ONLY_STEP1_MESSAGE).toMatch(/logo\/vector constructiv/i);
  });

  it("preserves semantic letter fixture confirm-all behavior", () => {
    const svg = readFileSync(join(analyzerFixtureDir, "ana-maria-gradinita-fara-layere.svg"), "utf8");
    const { report } = analyzeSvgString(svg, "ana-maria-gradinita-fara-layere.svg", svg.length);
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(confirmed.confirmationStatus).toBe("complete");
  });
});
