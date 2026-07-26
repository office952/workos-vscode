import { describe, expect, it } from "vitest";
import {
  buildFinishEstimateDraftSummary,
  FINISH_DRAFT_EXCLUDED_KEYS,
  FINISH_ESTIMATE_DRAFT_AUTHORITY,
  FINISH_ESTIMATE_DRAFT_SUMMARY,
  FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES,
  FINISH_EVIDENCE_REFERENCE_RATES,
  FINISH_LEGACY_RUNTIME_EVIDENCE,
  FINISH_OWNER_PRICE_VALUES_DECISION,
  getFinishEstimateDraftByKey,
} from "./candidateModuleProdusFinishEstimatedPriceDraft";

describe("candidateModuleProdusFinishEstimatedPriceDraft", () => {
  it("marks authority as EVIDENCE_DRAFT_READONLY not Pricing Registry", () => {
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.label).toBe("EVIDENCE_DRAFT_READONLY");
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.notPricingRegistryAuthority).toBe(true);
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.notActivePricing).toBe(true);
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.estimatedPriceDraftOnly).toBe(true);
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.pricingActive).toBe(false);
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.pricingRegistryWrite).toBe(false);
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.productTruthLiveWrite).toBe(false);
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.productDefinitionBridge).toBe(false);
    expect(FINISH_ESTIMATE_DRAFT_AUTHORITY.readyForPricing).toBe(false);
  });

  it("includes Oracal face draft rows with mp_face_area and evidence rates", () => {
    const row641 = getFinishEstimateDraftByKey("face_oracal_641_draft");
    expect(row641?.quantityBasis).toBe("mp_face_area");
    expect(row641?.materialEvidenceKeys).toContain("MAT-ORACAL-641");
    expect(row641?.evidenceMaterialEurMp).toBe(FINISH_EVIDENCE_REFERENCE_RATES.MAT_ORACAL_641);
    expect(row641?.draftValueStatus).toBe("evidence_only");
    expect(getFinishEstimateDraftByKey("face_oracal_651_draft")?.evidenceMaterialEurMp).toBe(9.0);
    expect(getFinishEstimateDraftByKey("face_oracal_8500_draft")?.evidenceMaterialEurMp).toBe(20.0);
  });

  it("includes print/laminate face rows with combined and split evidence", () => {
    const combined = getFinishEstimateDraftByKey("face_print_laminate_combined_draft");
    expect(combined?.evidenceCombinedEurMp).toBe(10.0);
    expect(combined?.materialEvidenceKeys).toContain("MAT-VINYL-PRINT-LAMINATED");
    const split = getFinishEstimateDraftByKey("face_print_laminate_split_draft");
    expect(split?.serviceEvidenceKeys).toEqual(expect.arrayContaining(["LARGE_FORMAT_PRINT", "LAMINATION"]));
  });

  it("marks artwork print+lam as evidence_only after owner price values decision", () => {
    const printLam = getFinishEstimateDraftByKey("artwork_print_laminate_draft");
    expect(printLam?.draftValueStatus).toBe("evidence_only");
    expect(printLam?.materialEvidenceKeys).toEqual(
      expect.arrayContaining(["MAT-VINYL-PRINT", "MAT-VINYL-PRINT-LAMINATED"]),
    );
    expect(printLam?.laborEvidenceKeys).toContain("FACE_VINYL_APPLICATION_LABOR");
    expect(printLam?.quantityBasis).toBe("mp_artwork_area");
  });

  it("keeps artwork print only blocked with runtime audit flag", () => {
    const printOnly = getFinishEstimateDraftByKey("artwork_print_only_draft");
    expect(printOnly?.draftValueStatus).toBe("source_inventory_audit_required");
    expect(printOnly?.displayValueRo).toMatch(/BLOCKED/i);
    expect(printOnly?.activationStatus).toBe("blocked_from_activation");
  });

  it("records owner price values decision metadata without activating pricing", () => {
    expect(FINISH_OWNER_PRICE_VALUES_DECISION.status).toBe("OWNER_ACCEPTED");
    expect(FINISH_OWNER_PRICE_VALUES_DECISION.faceLaborKey).toBe("FACE_VINYL_APPLICATION_LABOR");
    expect(FINISH_LEGACY_RUNTIME_EVIDENCE.key).toBe("WC_VINYL_APPLICATION");
    expect(FINISH_OWNER_PRICE_VALUES_DECISION.pricingActive).toBe(false);
  });

  it("marks artwork none/raw plexi as not_applicable without FACE material confusion", () => {
    const none = getFinishEstimateDraftByKey("artwork_none_raw_plexi_draft");
    expect(none?.draftValueStatus).toBe("not_applicable");
    expect(none?.materialEvidenceKeys).toHaveLength(0);
    expect(none?.displayValueRo).toMatch(/0 EUR/i);
  });

  it("excludes RETURN-CANT labor and FACE base material from FINISH draft", () => {
    const returnCant = FINISH_DRAFT_EXCLUDED_KEYS.find((k) => k.pricingKey === "RETURN_CANT_VINYL_APPLICATION_LABOR");
    expect(returnCant?.ownerComponent).toBe("RETURN-CANT");
    const faceMat = FINISH_DRAFT_EXCLUDED_KEYS.find((k) => k.pricingKey === "MAT-ACP-FATA-LITERE");
    expect(faceMat?.ownerComponent).toBe("FACE");
  });

  it("keeps readyForPricing false and pricingActiveCount zero", () => {
    expect(FINISH_ESTIMATE_DRAFT_SUMMARY.readyForPricing).toBe(false);
    expect(buildFinishEstimateDraftSummary().pricingActiveCount).toBe(0);
    expect(FINISH_ESTIMATE_DRAFT_SUMMARY.draftEntryCount).toBe(FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES.length);
  });

  it("every draft entry forbids pricing registry write and blocks activation", () => {
    expect(
      FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES.every(
        (e) => e.mustNotWritePricingRegistry && e.pricingActive === false && e.activationStatus === "blocked_from_activation",
      ),
    ).toBe(true);
  });

  it("never uses forbidden pricing authority labels on entries", () => {
    const forbidden = ["active", "pricing_ready", "registry_authority", "live_price", "product_truth_write_ready"];
    for (const entry of FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES) {
      expect(forbidden).not.toContain(entry.draftValueStatus);
      expect(forbidden).not.toContain(entry.activationStatus);
    }
  });
});
