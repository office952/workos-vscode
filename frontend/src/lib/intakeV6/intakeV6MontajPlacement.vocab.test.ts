/**
 * Placement/vocabulary guards for Intake V6 Page 2 residual cleanup.
 * Source-level: commercial site content must live inside commercial accordion;
 * OWNER_GATE must not be primary visible copy in ReviewStep / ACP panel.
 */
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { operatorReadinessLabelRo } from "./intakeV6OperatorVocabulary";

const reviewStepPath = path.resolve(
  __dirname,
  "../../components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx",
);
const acpPanelPath = path.resolve(
  __dirname,
  "../../components/workos/intake-v6/IntakeV6AcpLocalFaceModulesPanel.tsx",
);

describe("intakeV6 Montaj placement + vocabulary guards", () => {
  it("keeps mounting-site-section inside montaj-commercial-cluster", () => {
    const src = fs.readFileSync(reviewStepPath, "utf8");
    const commercialOpen = src.indexOf('testId="intake-v6-montaj-commercial-cluster"');
    const commercialClose = src.indexOf("</IntakeV6TechnicalDetailsAccordion>", commercialOpen);
    const siteSection = src.indexOf('data-testid="intake-v6-mounting-site-section"');
    expect(commercialOpen).toBeGreaterThan(-1);
    expect(siteSection).toBeGreaterThan(commercialOpen);
    expect(siteSection).toBeLessThan(commercialClose);
  });

  it("does not render raw OWNER_GATE as primary ReviewStep copy", () => {
    const src = fs.readFileSync(reviewStepPath, "utf8");
    expect(src).not.toMatch(/PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED/);
    expect(src).not.toMatch(/MANUAL_CONFIRMATION_REQUIRED —/);
    expect(src).not.toMatch(/>\s*OWNER_GATE/);
  });

  it("ACP panel maps readiness via vocabulary helper", () => {
    const src = fs.readFileSync(acpPanelPath, "utf8");
    expect(src).toContain("operatorReadinessLabelRo");
    expect(src).toContain("intake-v6-acp-module-advanced");
    expect(src).not.toMatch(/Owner gates/);
    expect(src).not.toMatch(/Readiness:\s*\{/);
  });

  it("maps shared electrical enums for primary UI", () => {
    expect(operatorReadinessLabelRo("SHARED_FROM_PANEL")).toBe("Alimentare din alt panou");
    expect(operatorReadinessLabelRo("DIRECT_220V")).toBe("Alimentare directă 220V");
    expect(operatorReadinessLabelRo("UNCONFIRMED")).toBe("Neconfirmat");
  });
});
