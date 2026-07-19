/**
 * Finisaje ownership presentation guards — raw SURFACE_FINISH must not sit in
 * primary accordion chrome (title/hint); technical tokens stay under disclosure.
 */
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  finishOwnershipTechnicalHintRo,
  finishOwnershipTechnicalTitleRo,
  operatorFinishOwnershipDomainLabelRo,
} from "./intakeV6OperatorVocabulary";

const reviewStepPath = path.resolve(
  __dirname,
  "../../components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx",
);

describe("intakeV6 Finisaje ownership vocabulary", () => {
  it("maps finish ownership domains to Romanian without inventing unknowns", () => {
    expect(operatorFinishOwnershipDomainLabelRo("SURFACE_FINISH")).toBe("Finisaj suprafață");
    expect(operatorFinishOwnershipDomainLabelRo("RETURN-CANT")).toBe("Finisaj cant");
    expect(operatorFinishOwnershipDomainLabelRo("WORKSPACE")).toBe("Valori din workspace");
    expect(operatorFinishOwnershipDomainLabelRo("UNKNOWN_XYZ")).toBe("Necesită verificare");
  });

  it("uses RO technical title/hint without raw SURFACE_FINISH", () => {
    expect(finishOwnershipTechnicalTitleRo()).toMatch(/Detalii tehnice despre finisaj/i);
    expect(finishOwnershipTechnicalHintRo()).not.toMatch(/SURFACE_FINISH|RETURN-CANT|OWNER_GATE/);
    expect(finishOwnershipTechnicalHintRo()).toMatch(/sursă de adevăr|mapări interne/i);
  });

  it("keeps finish ownership note after Finisaje pe layer controls", () => {
    const src = fs.readFileSync(reviewStepPath, "utf8");
    const faceSection = src.indexOf('testId="intake-v6-review-section-face-letters"');
    const ownership = src.indexOf('testId="intake-v6-finish-ownership-note"');
    expect(faceSection).toBeGreaterThan(-1);
    expect(ownership).toBeGreaterThan(faceSection);
  });

  it("does not put SURFACE_FINISH in accordion title/hint props", () => {
    const src = fs.readFileSync(reviewStepPath, "utf8");
    expect(src).toContain("finishOwnershipTechnicalTitleRo");
    expect(src).toContain("finishOwnershipTechnicalHintRo");
    expect(src).not.toMatch(/title="Detalii ownership finisaje"/);
    expect(src).not.toMatch(/hint="[^"]*SURFACE_FINISH/);
    expect(src).toContain('data-testid="intake-v6-finish-ownership-technical-tokens"');
  });
});
