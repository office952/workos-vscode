import { describe, expect, it } from "vitest";
import {
  buildFaceEstimateDraftSummary,
  FACE_CNC_CUTTING_ESTIMATE_DRAFTS,
  FACE_CNC_MINIMUM_POLICY_DRAFT,
  FACE_ESTIMATE_DRAFT_AUTHORITY,
  FACE_ESTIMATE_DRAFT_SUMMARY,
  FACE_INVENTORY_PRICING_CROSS_REFERENCES,
  FACE_MATERIAL_ESTIMATE_DRAFTS,
  formatFaceEstimateDraftValue,
  getFaceEstimateDraftByKey,
} from "./componentFirstFaceEstimatedPriceDraft";

describe("componentFirstFaceEstimatedPriceDraft", () => {
  it("marks authority as OWNER_ESTIMATE_DRAFT not Pricing Registry", () => {
    expect(FACE_ESTIMATE_DRAFT_AUTHORITY.label).toBe("OWNER_ESTIMATE_DRAFT");
    expect(FACE_ESTIMATE_DRAFT_AUTHORITY.notPricingRegistryAuthority).toBe(true);
    expect(FACE_ESTIMATE_DRAFT_AUTHORITY.notActivePricing).toBe(true);
    expect(FACE_ESTIMATE_DRAFT_AUTHORITY.pricingActive).toBe(false);
    expect(FACE_ESTIMATE_DRAFT_AUTHORITY.pricingRegistryWrite).toBe(false);
  });

  it("includes owner material estimate drafts for Plexiglas 3/5/10 mm", () => {
    expect(getFaceEstimateDraftByKey("plexiglas_3mm_material")?.estimateValue).toBe(16);
    expect(getFaceEstimateDraftByKey("plexiglas_5mm_material")?.estimateValue).toBe(25);
    expect(getFaceEstimateDraftByKey("plexiglas_10mm_material")?.estimateValue).toBe(50);
    expect(FACE_MATERIAL_ESTIMATE_DRAFTS.every((e) => e.status === "owner_estimate_draft")).toBe(true);
  });

  it("includes CNC contour cutting estimate drafts", () => {
    expect(getFaceEstimateDraftByKey("plexiglas_3mm_cnc")?.estimateValue).toBe(1.0);
    expect(getFaceEstimateDraftByKey("plexiglas_5mm_cnc")?.estimateValue).toBe(1.5);
    expect(getFaceEstimateDraftByKey("plexiglas_10mm_cnc")?.estimateValue).toBe(2.5);
    expect(FACE_CNC_CUTTING_ESTIMATE_DRAFTS.every((e) => e.unit === "ml")).toBe(true);
  });

  it("includes 50 lei CNC minimum as owner commercial policy not registry", () => {
    expect(FACE_CNC_MINIMUM_POLICY_DRAFT.estimateValueLei).toBe(50);
    expect(FACE_CNC_MINIMUM_POLICY_DRAFT.notPricingRegistry).toBe(true);
    expect(FACE_CNC_MINIMUM_POLICY_DRAFT.pricingActive).toBe(false);
  });

  it("keeps readyForPricing false and pricingActiveCount zero", () => {
    expect(FACE_ESTIMATE_DRAFT_SUMMARY.readyForPricing).toBe(false);
    expect(buildFaceEstimateDraftSummary().pricingActiveCount).toBe(0);
  });

  it("cross-references MAT-ACP-FATA-LITERE without making draft registry authority", () => {
    const ref = FACE_INVENTORY_PRICING_CROSS_REFERENCES.find((r) => r.pricingKey === "MAT-ACP-FATA-LITERE");
    expect(ref).toBeDefined();
    expect(ref?.registryAuthority).toBe(false);
    expect(ref?.draftAuthority).toBe("OWNER_ESTIMATE_DRAFT");
  });

  it("formats estimate values with units", () => {
    const material = getFaceEstimateDraftByKey("plexiglas_3mm_material")!;
    const cnc = getFaceEstimateDraftByKey("plexiglas_3mm_cnc")!;
    expect(formatFaceEstimateDraftValue(material)).toBe("16.00 EUR/mp");
    expect(formatFaceEstimateDraftValue(cnc)).toBe("1.00 EUR/ml contur");
  });

  it("every draft entry forbids pricing registry write", () => {
    const all = [...FACE_MATERIAL_ESTIMATE_DRAFTS, ...FACE_CNC_CUTTING_ESTIMATE_DRAFTS];
    expect(all.every((e) => e.mustNotWritePricingRegistry && e.pricingActive === false)).toBe(true);
  });
});
