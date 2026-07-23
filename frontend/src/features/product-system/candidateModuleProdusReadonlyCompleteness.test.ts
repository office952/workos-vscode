import { describe, expect, it } from "vitest";
import {
  CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
  CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES,
  CANDIDATE_MODULE_EXPECTED_ROW_COUNT,
  CANDIDATE_MODULE_FALLBACK_CONTRACT_FIXTURE,
  assessCandidateModuleProdusContractDrift,
  assessCandidateModuleProdusLiveCompleteness,
  validateCandidateModuleProdusFallbackContract,
  type CandidateModuleProdusFallbackContractRow,
  type CandidateModuleProdusLiveTemplateRow,
} from "./candidateModuleProdusReadonlyCompleteness";
import {
  CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE,
  assessCandidateModuleProdusDossierAlignment,
  validateCandidateModuleProdusDossierContract,
} from "./candidateModuleProdusReadonlyDossierAlignment";
import {
  buildCandidateModuleProdusOwnerSummary,
  CANDIDATE_MODULE_OWNER_FORBIDDEN_WORDING,
} from "./candidateModuleProdusReadonlyOwnerSummary";
import {
  assessCandidateModuleProdusFormSystemReadiness,
  CANDIDATE_MODULE_FORM_SYSTEM_READINESS_CONTRACT,
  getCandidateModuleProdusFormReadinessEntry,
  validateCandidateModuleProdusFormSystemReadinessContract,
} from "./candidateModuleProdusReadonlyFormSystemReadiness";
import {
  assessCandidateModuleProdusProductTruthMapping,
  CANDIDATE_MODULE_EXPECTED_MAPPING_ENTRY_COUNT,
  CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT,
  getCandidateModuleProdusProductTruthMappingsForRole,
  validateCandidateModuleProdusProductTruthMappingContract,
  type CandidateModuleProdusProductTruthMappingEntry,
} from "./candidateModuleProdusReadonlyProductTruthMapping";
import {
  assessCandidateModuleProdusProductDefinitionReadiness,
  CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT,
  CANDIDATE_MODULE_PRODUCT_DEFINITION_FORBIDDEN_OUTPUT,
  CANDIDATE_MODULE_PRODUCT_DEFINITION_FORBIDDEN_VALUE_STATES,
  CANDIDATE_MODULE_PRODUCT_DEFINITION_REQUIRED_PATHS_COUNT,
  getCandidateModuleProdusProductDefinitionEntry,
  getCandidateModuleProdusProductDefinitionPathsForRole,
  validateCandidateModuleProdusProductDefinitionConsumptionContract,
  type CandidateModuleProdusProductDefinitionConsumptionEntry,
} from "./candidateModuleProdusReadonlyProductDefinitionReadiness";

function liveRow(
  templateCode: string,
  overrides: Partial<CandidateModuleProdusLiveTemplateRow> = {}
): CandidateModuleProdusLiveTemplateRow {
  return {
    template_code: templateCode,
    active: false,
    family_id: "litere_component_first_candidate",
    family_name: "Litere candidate-module candidate",
    ...overrides,
  };
}

function matchingLiveSet(): CandidateModuleProdusLiveTemplateRow[] {
  return [
    liveRow(CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE, {
      components_json: JSON.stringify(
        CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES.map((componentTemplateCode, index) => ({
          component_id: `comp_${index}`,
          component_template_code: componentTemplateCode,
          role: "face",
          kind: "structural",
        }))
      ),
      notes: JSON.stringify({ template_kind: "product_composer", readiness: "planned" }),
    }),
    ...CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES.map((templateCode, index) => {
      const fixture = CANDIDATE_MODULE_FALLBACK_CONTRACT_FIXTURE.find((row) => row.templateCode === templateCode);
      return liveRow(templateCode, {
        components_json: JSON.stringify([
          {
            component_id: fixture?.componentId,
            role: fixture?.role,
            component_kind: fixture?.componentKind,
            target_product_truth_path: fixture?.targetProductTruthPath,
          },
        ]),
        notes: JSON.stringify({ template_kind: "component_template", readiness: "planned" }),
      });
    }),
  ];
}

describe("candidateModuleProdusReadonlyCompleteness fixture comparison", () => {
  it("fallback contract has exactly 7 expected rows", () => {
    const validation = validateCandidateModuleProdusFallbackContract();
    expect(CANDIDATE_MODULE_FALLBACK_CONTRACT_FIXTURE).toHaveLength(CANDIDATE_MODULE_EXPECTED_ROW_COUNT);
    expect(validation.valid).toBe(true);
    expect(validation.issues).toEqual([]);
  });

  it("fallback contract has composer + 6 components", () => {
    const composerRows = CANDIDATE_MODULE_FALLBACK_CONTRACT_FIXTURE.filter((row) => row.rowKind === "composer");
    const componentRows = CANDIDATE_MODULE_FALLBACK_CONTRACT_FIXTURE.filter((row) => row.rowKind === "component");
    expect(composerRows).toHaveLength(1);
    expect(componentRows).toHaveLength(6);
    expect(composerRows[0]?.templateCode).toBe(CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE);
  });

  it("detects duplicate expected code as fallback contract drift", () => {
    const brokenFixture: CandidateModuleProdusFallbackContractRow[] = [
      ...CANDIDATE_MODULE_FALLBACK_CONTRACT_FIXTURE,
      { ...CANDIDATE_MODULE_FALLBACK_CONTRACT_FIXTURE[1] },
    ];
    const validation = validateCandidateModuleProdusFallbackContract(brokenFixture);
    expect(validation.valid).toBe(false);
    expect(validation.issues.some((issue) => issue.includes("duplicate"))).toBe(true);

    const drift = assessCandidateModuleProdusContractDrift([], brokenFixture);
    expect(drift.driftState).toBe("FALLBACK_CONTRACT_DRIFT");
  });

  it("reports NO_DRIFT for 7/7 live inactive rows matching expected contract", () => {
    const drift = assessCandidateModuleProdusContractDrift(matchingLiveSet());
    expect(drift.driftState).toBe("NO_DRIFT");
    expect(drift.contractCheckStatus).toBe("OK");
    expect(drift.completeness.sourceMode).toBe("live_seeded_inactive");
  });

  it("reports partial live rows without claiming live complete", () => {
    const partial = matchingLiveSet().slice(0, 3);
    const completeness = assessCandidateModuleProdusLiveCompleteness(partial);
    const drift = assessCandidateModuleProdusContractDrift(partial);

    expect(completeness.foundRowCount).toBe(3);
    expect(completeness.sourceMode).toBe("partial_live_inactive");
    expect(drift.completeness.missingTemplateCodes.length).toBeGreaterThan(0);
    expect(drift.driftState).toBe("NO_DRIFT");
  });

  it("reports BLOCKED_INVALID_LIVE_STATE when any expected row is active", () => {
    const rows = matchingLiveSet();
    rows[0] = { ...rows[0], active: true };
    const drift = assessCandidateModuleProdusContractDrift(rows);

    expect(drift.driftState).toBe("BLOCKED_INVALID_LIVE_STATE");
    expect(drift.contractCheckStatus).toBe("BLOCKED");
  });

  it("does not invent truth when metadata is unavailable", () => {
    const rows = matchingLiveSet().map((row) => ({
      ...row,
      family_id: undefined,
      family_name: undefined,
      notes: undefined,
      components_json: undefined,
    }));
    const drift = assessCandidateModuleProdusContractDrift(rows);

    expect(drift.metadataUnavailableWarnings.length).toBeGreaterThan(0);
    expect(drift.liveRowDriftIssues).toEqual([]);
    expect(drift.driftState).toBe("NO_DRIFT");
    expect(drift.contractCheckStatus).toBe("WARNING");
  });

  it("detects extra expected-family live rows", () => {
    const rows = [
      ...matchingLiveSet(),
      liveRow("TPL-COMP-LETTER-EXTRA_v1", {
        notes: JSON.stringify({ template_kind: "component_template", readiness: "planned" }),
      }),
    ];
    const drift = assessCandidateModuleProdusContractDrift(rows);
    expect(drift.liveExtraFamilyRows).toContain("TPL-COMP-LETTER-EXTRA_v1");
    expect(drift.driftState).toBe("LIVE_EXTRA_EXPECTED_FAMILY_ROW");
  });
});

describe("candidateModuleProdusReadonlyDossierAlignment", () => {
  it("dossier alignment contract has exactly 7 entries", () => {
    const validation = validateCandidateModuleProdusDossierContract();
    expect(CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE).toHaveLength(CANDIDATE_MODULE_EXPECTED_ROW_COUNT);
    expect(validation.valid).toBe(true);
    expect(validation.issues).toEqual([]);
  });

  it("composer is product_composer / composer_orchestration", () => {
    const composer = CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE.find(
      (entry) => entry.templateCode === CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE
    );
    expect(composer?.expectedKind).toBe("product_composer");
    expect(composer?.expectedDossierRole).toBe("composer_orchestration");
    expect(composer?.expectedTruthOwner).toBe("product_composer");
  });

  it("all 6 component templates are component_template / component-owned truth", () => {
    const componentEntries = CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE.filter(
      (entry) => entry.expectedKind === "component_template"
    );
    expect(componentEntries).toHaveLength(6);
    expect(componentEntries.every((entry) => entry.expectedTruthOwner === "component_owned_truth")).toBe(true);
    expect(componentEntries.map((entry) => entry.templateCode)).toEqual(CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES);
  });

  it("7/7 live inactive + 7/7 dossier contract => READONLY_ALIGNED", () => {
    const assessment = assessCandidateModuleProdusDossierAlignment(matchingLiveSet());
    expect(assessment.dossierContractCount).toBe(7);
    expect(assessment.liveFoundCount).toBe(7);
    expect(assessment.overallAlignmentState).toBe("READONLY_ALIGNED");
    expect(assessment.dossierRuntimeLinkState).toBe("NOT_LINKED_YET");
  });

  it("0/7 live + 7/7 dossier contract => READONLY_FALLBACK_ONLY", () => {
    const assessment = assessCandidateModuleProdusDossierAlignment([]);
    expect(assessment.dossierContractCount).toBe(7);
    expect(assessment.liveFoundCount).toBe(0);
    expect(assessment.overallAlignmentState).toBe("READONLY_FALLBACK_ONLY");
    expect(assessment.dossierRuntimeLinkState).toBe("READONLY_CONTRACT_ONLY");
  });

  it("partial live + 7/7 dossier contract => READONLY_PARTIAL", () => {
    const assessment = assessCandidateModuleProdusDossierAlignment(matchingLiveSet().slice(0, 3));
    expect(assessment.dossierContractCount).toBe(7);
    expect(assessment.liveFoundCount).toBe(3);
    expect(assessment.overallAlignmentState).toBe("READONLY_PARTIAL");
    expect(assessment.dossierRuntimeLinkState).toBe("PARTIAL_RUNTIME_LINK");
  });

  it("any active expected row => BLOCKED_INVALID_LIVE_STATE", () => {
    const rows = matchingLiveSet();
    rows[0] = { ...rows[0], active: true };
    const assessment = assessCandidateModuleProdusDossierAlignment(rows);
    expect(assessment.overallAlignmentState).toBe("BLOCKED_INVALID_LIVE_STATE");
  });

  it("runtime dossier not linked yet is readonly contract readiness, not failure", () => {
    const assessment = assessCandidateModuleProdusDossierAlignment([]);
    expect(assessment.dossierRuntimeLinkState).toBe("READONLY_CONTRACT_ONLY");
    expect(assessment.overallAlignmentState).toBe("READONLY_FALLBACK_ONLY");
    expect(assessment.runtimeActivationLeakIssues).toEqual([]);
  });

  it("detects dossier activation leak signals from live rows", () => {
    const rows = matchingLiveSet();
    rows[1] = {
      ...rows[1],
      notes: JSON.stringify({ task_materialization: true, quote_mode: "active" }),
      operations_json: JSON.stringify([{ op: "cut" }]),
    };
    const assessment = assessCandidateModuleProdusDossierAlignment(rows);
    expect(assessment.overallAlignmentState).toBe("BLOCKED_DOSSIER_ACTIVATION_LEAK");
    expect(assessment.dossierRuntimeLinkState).toBe("BLOCKED_RUNTIME_ACTIVATION_LEAK");
    expect(assessment.runtimeActivationLeakIssues.length).toBeGreaterThan(0);
  });
});

function ownerSummaryFor(liveRows: CandidateModuleProdusLiveTemplateRow[]) {
  const drift = assessCandidateModuleProdusContractDrift(liveRows);
  const dossier = assessCandidateModuleProdusDossierAlignment(liveRows, { drift });
  return buildCandidateModuleProdusOwnerSummary(drift.completeness, drift, dossier);
}

describe("candidateModuleProdusReadonlyOwnerSummary", () => {
  it("at 0/7 live says readonly, not exposed, no pricing/quote/order/execution", () => {
    const summary = ownerSummaryFor([]);
    expect(summary.statusLevel).toBe("NEEDS_LIVE_ROWS");
    expect(summary.statusTitle).toContain("Safe readonly contract");
    expect(summary.canBeUsedInWorkIntake).toBe(false);
    expect(summary.canPrice).toBe(false);
    expect(summary.canCreateQuote).toBe(false);
    expect(summary.canCreateOrder).toBe(false);
    expect(summary.canMaterializeTasks).toBe(false);
    expect(summary.ownerVisibleChecks.find((c) => c.label === "Work Intake exposure")?.value).toBe("no");
    expect(summary.ownerVisibleChecks.find((c) => c.label === "Pricing / Quote / Order / Execution")?.value).toBe("no");
    expect(summary.ownerVisibleChecks.find((c) => c.label === "Live seeded rows")?.value).toBe("0/7");
  });

  it("at 7/7 inactive says complete but still not offerable", () => {
    const summary = ownerSummaryFor(matchingLiveSet());
    expect(summary.statusLevel).toBe("SAFE_READONLY");
    expect(summary.statusTitle.toLowerCase()).toContain("not offerable");
    expect(summary.canCreateQuote).toBe(false);
    expect(summary.canPrice).toBe(false);
    expect(summary.ownerVisibleChecks.find((c) => c.label === "Live seeded rows")?.value).toBe("7/7");
  });

  it("at partial live says partial and not complete", () => {
    const summary = ownerSummaryFor(matchingLiveSet().slice(0, 3));
    expect(summary.statusLevel).toBe("PARTIAL_LIVE_ROWS");
    expect(summary.oneSentenceSummary.toLowerCase()).toContain("partial");
    expect(summary.oneSentenceSummary.toLowerCase()).toContain("not treat as complete");
  });

  it("at blocked says blocked", () => {
    const rows = matchingLiveSet();
    rows[0] = { ...rows[0], active: true };
    const summary = ownerSummaryFor(rows);
    expect(summary.statusLevel).toBe("BLOCKED");
    expect(summary.statusTitle.toLowerCase()).toContain("blocked");
  });

  it("does not use dangerous commercial wording", () => {
    const scenarios = [[], matchingLiveSet(), matchingLiveSet().slice(0, 3)];
    for (const rows of scenarios) {
      const summary = ownerSummaryFor(rows);
      const text = JSON.stringify(summary).toLowerCase();
      const withoutNegatedOfferable = text.replace(/not offerable/g, "");
      for (const forbidden of CANDIDATE_MODULE_OWNER_FORBIDDEN_WORDING) {
        if (forbidden === "offerable") {
          expect(withoutNegatedOfferable).not.toContain("offerable");
          continue;
        }
        expect(text).not.toContain(forbidden.toLowerCase());
      }
    }
  });
});

function formReadinessFor(liveRows: CandidateModuleProdusLiveTemplateRow[]) {
  const drift = assessCandidateModuleProdusContractDrift(liveRows);
  const dossier = assessCandidateModuleProdusDossierAlignment(liveRows, { drift });
  const owner = buildCandidateModuleProdusOwnerSummary(drift.completeness, drift, dossier);
  return assessCandidateModuleProdusFormSystemReadiness(drift.completeness, dossier, owner, {
    drift,
    liveTemplates: liveRows,
  });
}

describe("candidateModuleProdusReadonlyFormSystemReadiness", () => {
  it("Form System readiness contract has exactly 7 entries", () => {
    const validation = validateCandidateModuleProdusFormSystemReadinessContract();
    expect(CANDIDATE_MODULE_FORM_SYSTEM_READINESS_CONTRACT).toHaveLength(CANDIDATE_MODULE_EXPECTED_ROW_COUNT);
    expect(validation.valid).toBe(true);
    expect(validation.issues).toEqual([]);
  });

  it("composer coordinates sections only and owns_truth=false", () => {
    const composer = getCandidateModuleProdusFormReadinessEntry(CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE);
    expect(composer?.role).toBe("product_composer");
    if (composer?.role === "product_composer") {
      expect(composer.ownsTruth).toBe(false);
      expect(composer.formSystemRole).toBe("compose_component_sections");
      expect(composer.coordinates).toContain("selected components");
    }
  });

  it("all 6 components own future fields", () => {
    const componentEntries = CANDIDATE_MODULE_FORM_SYSTEM_READINESS_CONTRACT.filter(
      (entry) => entry.role === "component_template"
    );
    expect(componentEntries).toHaveLength(6);
    expect(componentEntries.every((entry) => entry.ownsTruth === true)).toBe(true);
    expect(componentEntries.every((entry) => entry.fieldGroups.length > 0)).toBe(true);
  });

  it("face includes material/thickness/finish target", () => {
    const face = getCandidateModuleProdusFormReadinessEntry("TPL-COMP-LETTER-FACE_v1");
    expect(face?.role).toBe("component_template");
    if (face?.role === "component_template") {
      expect(face.fieldGroups).toEqual(
        expect.arrayContaining(["face_material", "face_thickness", "face_finish_target"])
      );
    }
  });

  it("return_cant includes material/depth/finish", () => {
    const returnCant = getCandidateModuleProdusFormReadinessEntry("TPL-COMP-LETTER-RETURN-CANT_v1");
    if (returnCant?.role === "component_template") {
      expect(returnCant.fieldGroups).toEqual(
        expect.arrayContaining(["return_material", "return_depth", "return_finish"])
      );
    }
  });

  it("led includes illumination/led density/power supply", () => {
    const led = getCandidateModuleProdusFormReadinessEntry("TPL-COMP-LETTER-LED_v1");
    if (led?.role === "component_template") {
      expect(led.fieldGroups).toEqual(
        expect.arrayContaining(["illumination_mode", "led_density", "power_supply_policy"])
      );
    }
  });

  it("finish includes stock/oracal/ral/print policy", () => {
    const finish = getCandidateModuleProdusFormReadinessEntry("TPL-COMP-LETTER-FINISH_v1");
    if (finish?.role === "component_template") {
      expect(finish.fieldGroups).toEqual(
        expect.arrayContaining(["stock_color", "oracal_code", "ral_code", "print_lamination_policy"])
      );
    }
  });

  it("mounting includes surface/spacer/drilling/site notes", () => {
    const mounting = getCandidateModuleProdusFormReadinessEntry("TPL-COMP-LETTER-MOUNTING_v1");
    if (mounting?.role === "component_template") {
      expect(mounting.fieldGroups).toEqual(
        expect.arrayContaining(["mounting_surface", "spacer_policy", "template_drilling_policy", "site_installation_notes"])
      );
    }
  });

  it("0/7 live => READONLY_FALLBACK_ONLY", () => {
    const assessment = formReadinessFor([]);
    expect(assessment.overallFormReadinessState).toBe("READONLY_FALLBACK_ONLY");
    expect(assessment.runtimeFormSystemLinkState).toBe("READONLY_CONTRACT_ONLY");
  });

  it("7/7 inactive => READONLY_READY_FOR_MAPPING", () => {
    const assessment = formReadinessFor(matchingLiveSet());
    expect(assessment.overallFormReadinessState).toBe("READONLY_READY_FOR_MAPPING");
    expect(assessment.readinessContractEntries).toBe(7);
  });

  it("partial => READONLY_PARTIAL_LIVE_ROWS", () => {
    const assessment = formReadinessFor(matchingLiveSet().slice(0, 3));
    expect(assessment.overallFormReadinessState).toBe("READONLY_PARTIAL_LIVE_ROWS");
  });

  it("active row => BLOCKED_INVALID_LIVE_STATE", () => {
    const rows = matchingLiveSet();
    rows[0] = { ...rows[0], active: true };
    const assessment = formReadinessFor(rows);
    expect(assessment.overallFormReadinessState).toBe("BLOCKED_INVALID_LIVE_STATE");
  });

  it("form activation leak => BLOCKED_FORM_ACTIVATION_LEAK", () => {
    const rows = matchingLiveSet();
    rows[1] = {
      ...rows[1],
      notes: JSON.stringify({ form_system_active: true, work_intake_exposed: true }),
    };
    const assessment = formReadinessFor(rows);
    expect(assessment.overallFormReadinessState).toBe("BLOCKED_FORM_ACTIVATION_LEAK");
    expect(assessment.runtimeFormSystemLinkState).toBe("BLOCKED_RUNTIME_FORM_ACTIVATION_LEAK");
    expect(assessment.unsafeSignals.length).toBeGreaterThan(0);
  });
});

function productTruthMappingFor(liveRows: CandidateModuleProdusLiveTemplateRow[]) {
  const drift = assessCandidateModuleProdusContractDrift(liveRows);
  const dossier = assessCandidateModuleProdusDossierAlignment(liveRows, { drift });
  const owner = buildCandidateModuleProdusOwnerSummary(drift.completeness, drift, dossier);
  const formReadiness = assessCandidateModuleProdusFormSystemReadiness(drift.completeness, dossier, owner, {
    drift,
    liveTemplates: liveRows,
  });
  return assessCandidateModuleProdusProductTruthMapping(formReadiness, owner);
}

describe("candidateModuleProdusReadonlyProductTruthMapping", () => {
  it("mapping contract includes expected entries for composer + 6 components", () => {
    const validation = validateCandidateModuleProdusProductTruthMappingContract();
    expect(CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.length).toBe(CANDIDATE_MODULE_EXPECTED_MAPPING_ENTRY_COUNT);
    expect(validation.valid).toBe(true);
    expect(CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.some((e) => e.templateCode === CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE)).toBe(true);
    const componentTemplates = new Set(
      CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.filter((e) => e.truthOwner === "component_owned_truth").map((e) => e.templateCode)
    );
    expect(componentTemplates.size).toBe(6);
  });

  it("all entries have may_write_now=false", () => {
    expect(CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.every((entry) => entry.mayWriteNow === false)).toBe(true);
    expect(CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.every((entry) => entry.writePolicy === "readonly_mapping_only")).toBe(true);
  });

  it("suggested is not confirmed", () => {
    for (const entry of CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT) {
      expect(entry.allowedValueStates).toContain("suggested");
      expect(entry.allowedValueStates).toContain("confirmed_later");
      expect(entry.allowedValueStates.indexOf("suggested")).not.toBe(entry.allowedValueStates.indexOf("confirmed_later"));
    }
  });

  it("fallback/hydrated are not confirmed", () => {
    for (const entry of CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT) {
      expect(entry.allowedValueStates).toContain("fallback_readonly");
      expect(entry.allowedValueStates).toContain("hydrated_readonly");
      expect(entry.allowedValueStates).not.toEqual(["confirmed_later"]);
    }
  });

  it("FACE paths map to product.components.face.*", () => {
    const faceMappings = getCandidateModuleProdusProductTruthMappingsForRole("product.components.face.");
    expect(faceMappings.length).toBeGreaterThanOrEqual(4);
    expect(faceMappings.every((entry) => entry.futureProductTruthPath.startsWith("product.components.face."))).toBe(true);
  });

  it("RETURN/CANT paths map to product.components.return_cant.*", () => {
    const mappings = getCandidateModuleProdusProductTruthMappingsForRole("product.components.return_cant.");
    expect(mappings.length).toBe(4);
    expect(mappings.map((e) => e.fieldGroup)).toEqual(
      expect.arrayContaining(["return_material", "return_depth", "return_finish"])
    );
  });

  it("LED paths map to product.components.led.*", () => {
    const mappings = getCandidateModuleProdusProductTruthMappingsForRole("product.components.led.");
    expect(mappings.length).toBe(5);
    expect(mappings.map((e) => e.fieldGroup)).toEqual(
      expect.arrayContaining(["illumination_mode", "led_density", "power_supply_policy"])
    );
  });

  it("FINISH paths map to product.components.finish.*", () => {
    const mappings = getCandidateModuleProdusProductTruthMappingsForRole("product.components.finish.");
    expect(mappings.length).toBe(5);
    expect(mappings.map((e) => e.fieldGroup)).toEqual(
      expect.arrayContaining(["stock_color", "oracal_code", "ral_code", "print_lamination_policy"])
    );
  });

  it("MOUNTING paths map to product.components.mounting.*", () => {
    const mappings = getCandidateModuleProdusProductTruthMappingsForRole("product.components.mounting.");
    expect(mappings.length).toBe(4);
    expect(mappings.map((e) => e.fieldGroup)).toEqual(
      expect.arrayContaining(["mounting_surface", "spacer_policy", "template_drilling_policy", "site_installation_notes"])
    );
  });

  it("0/7 live => READONLY_MAPPING_FALLBACK_ONLY", () => {
    const assessment = productTruthMappingFor([]);
    expect(assessment.overallMappingState).toBe("READONLY_MAPPING_FALLBACK_ONLY");
    expect(assessment.runtimeProductTruthLinkState).toBe("READONLY_MAPPING_ONLY");
  });

  it("7/7 inactive => READONLY_MAPPING_READY", () => {
    const assessment = productTruthMappingFor(matchingLiveSet());
    expect(assessment.overallMappingState).toBe("READONLY_MAPPING_READY");
    expect(assessment.mappingContractEntriesCount).toBe(CANDIDATE_MODULE_EXPECTED_MAPPING_ENTRY_COUNT);
  });

  it("any write-enabled entry => BLOCKED_PRODUCT_TRUTH_WRITE_LEAK", () => {
    const brokenContract = CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.map((entry, index) =>
      index === 0 ? ({ ...entry, mayWriteNow: true } as CandidateModuleProdusProductTruthMappingEntry) : entry
    );
    const drift = assessCandidateModuleProdusContractDrift([]);
    const dossier = assessCandidateModuleProdusDossierAlignment([], { drift });
    const owner = buildCandidateModuleProdusOwnerSummary(drift.completeness, drift, dossier);
    const formReadiness = assessCandidateModuleProdusFormSystemReadiness(drift.completeness, dossier, owner);
    const assessment = assessCandidateModuleProdusProductTruthMapping(formReadiness, owner, brokenContract);
    expect(assessment.overallMappingState).toBe("BLOCKED_PRODUCT_TRUTH_WRITE_LEAK");
    expect(assessment.writeEnabledEntries.length).toBeGreaterThan(0);
  });

  it("unsafe state policy treating suggested as confirmed => BLOCKED_PRODUCT_TRUTH_WRITE_LEAK", () => {
    const brokenContract: CandidateModuleProdusProductTruthMappingEntry[] = CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.map(
      (entry, index) =>
        index === 3
          ? { ...entry, allowedValueStates: ["confirmed_later"] }
          : entry
    );
    const drift = assessCandidateModuleProdusContractDrift([]);
    const dossier = assessCandidateModuleProdusDossierAlignment([], { drift });
    const owner = buildCandidateModuleProdusOwnerSummary(drift.completeness, drift, dossier);
    const formReadiness = assessCandidateModuleProdusFormSystemReadiness(drift.completeness, dossier, owner);
    const assessment = assessCandidateModuleProdusProductTruthMapping(formReadiness, owner, brokenContract);
    expect(assessment.overallMappingState).toBe("BLOCKED_PRODUCT_TRUTH_WRITE_LEAK");
    expect(assessment.unsafeStatePolicyEntries.length).toBeGreaterThan(0);
  });
});

function productDefinitionReadinessFor(
  liveRows: CandidateModuleProdusLiveTemplateRow[],
  options?: {
    productTruthContract?: readonly CandidateModuleProdusProductTruthMappingEntry[];
    productDefinitionContract?: readonly CandidateModuleProdusProductDefinitionConsumptionEntry[];
  }
) {
  const drift = assessCandidateModuleProdusContractDrift(liveRows);
  const dossier = assessCandidateModuleProdusDossierAlignment(liveRows, { drift });
  const owner = buildCandidateModuleProdusOwnerSummary(drift.completeness, drift, dossier);
  const formReadiness = assessCandidateModuleProdusFormSystemReadiness(drift.completeness, dossier, owner, {
    drift,
    liveTemplates: liveRows,
  });
  const productTruthMapping = assessCandidateModuleProdusProductTruthMapping(formReadiness, owner, options?.productTruthContract);
  return assessCandidateModuleProdusProductDefinitionReadiness(productTruthMapping, formReadiness, owner, {
    liveTemplates: liveRows,
    contract: options?.productDefinitionContract,
  });
}

describe("candidateModuleProdusReadonlyProductDefinitionReadiness", () => {
  it("ProductDefinition readiness contract includes expected component paths", () => {
    const validation = validateCandidateModuleProdusProductDefinitionConsumptionContract();
    expect(CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT).toHaveLength(7);
    expect(validation.valid).toBe(true);
    expect(CANDIDATE_MODULE_PRODUCT_DEFINITION_REQUIRED_PATHS_COUNT).toBe(29);
  });

  it("all entries have may_activate_product_definition_now=false", () => {
    expect(
      CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT.every(
        (entry) => entry.mayActivateProductDefinitionNow === false
      )
    ).toBe(true);
  });

  it("suggested/fallback/hydrated/manual_draft are forbidden states", () => {
    for (const entry of CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT) {
      expect(entry.forbiddenValueStates).toEqual(
        expect.arrayContaining(["suggested", "fallback_readonly", "hydrated_readonly", "manual_draft"])
      );
      expect(entry.allowedFutureValueState).toBe("confirmed_later");
    }
  });

  it("missing truth behavior includes do_not_invent and report_missing_truth", () => {
    for (const entry of CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT) {
      expect(entry.missingTruthBehavior).toContain("do_not_invent");
      expect(entry.missingTruthBehavior).toContain("report_missing_truth");
      expect(entry.missingTruthBehavior).toContain("do_not_price");
      expect(entry.missingTruthBehavior).toContain("do_not_create_aggregate");
    }
  });

  it("ProductDefinition forbidden output includes price/quote/order/ProductAggregate/TaskGraph/ExecutionPlan/task materialization", () => {
    expect(CANDIDATE_MODULE_PRODUCT_DEFINITION_FORBIDDEN_OUTPUT).toEqual(
      expect.arrayContaining([
        "price",
        "quote",
        "order",
        "ProductAggregate",
        "TaskGraph",
        "ExecutionPlan",
        "task_materialization",
      ])
    );
    for (const entry of CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT) {
      expect(entry.productDefinitionForbiddenOutput).toEqual(
        expect.arrayContaining(["price", "quote", "order", "ProductAggregate", "TaskGraph", "ExecutionPlan"])
      );
    }
  });

  it("FACE required paths match Product Truth mapping", () => {
    const facePaths = getCandidateModuleProdusProductDefinitionPathsForRole("face");
    expect(facePaths).toEqual(
      expect.arrayContaining([
        "product.components.face.material",
        "product.components.face.thickness",
        "product.components.face.finish_target",
      ])
    );
    const faceEntry = getCandidateModuleProdusProductDefinitionEntry("TPL-COMP-LETTER-FACE_v1");
    expect(faceEntry?.requiredProductTruthPaths).toHaveLength(4);
  });

  it("LED required paths match Product Truth mapping", () => {
    const ledPaths = getCandidateModuleProdusProductDefinitionPathsForRole("led");
    expect(ledPaths).toEqual(
      expect.arrayContaining([
        "product.components.led.illumination_mode",
        "product.components.led.density",
        "product.components.led.power_supply_policy",
      ])
    );
  });

  it("FINISH required paths match Product Truth mapping", () => {
    const finishPaths = getCandidateModuleProdusProductDefinitionPathsForRole("finish");
    expect(finishPaths).toEqual(
      expect.arrayContaining(["product.components.finish.oracal_code", "product.components.finish.ral_code"])
    );
  });

  it("MOUNTING required paths match Product Truth mapping", () => {
    const mountingPaths = getCandidateModuleProdusProductDefinitionPathsForRole("mounting");
    expect(mountingPaths).toEqual(
      expect.arrayContaining([
        "product.components.mounting.surface",
        "product.components.mounting.spacer_policy",
        "product.components.mounting.template_drilling_policy",
      ])
    );
  });

  it("0/7 live => READONLY_CONSUMPTION_FALLBACK_ONLY", () => {
    const assessment = productDefinitionReadinessFor([]);
    expect(assessment.overallProductDefinitionReadinessState).toBe("READONLY_CONSUMPTION_FALLBACK_ONLY");
    expect(assessment.runtimeProductDefinitionLinkState).toBe("READONLY_CONSUMPTION_CONTRACT_ONLY");
    expect(assessment.mappedPathsCount).toBe(29);
  });

  it("7/7 inactive => READONLY_CONSUMPTION_READY", () => {
    const assessment = productDefinitionReadinessFor(matchingLiveSet());
    expect(assessment.overallProductDefinitionReadinessState).toBe("READONLY_CONSUMPTION_READY");
    expect(assessment.requiredPathsCount).toBe(29);
  });

  it("Product Truth write leak blocks ProductDefinition readiness", () => {
    const brokenMapping = CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.map((entry, index) =>
      index === 0 ? ({ ...entry, mayWriteNow: true } as CandidateModuleProdusProductTruthMappingEntry) : entry
    );
    const assessment = productDefinitionReadinessFor([], { productTruthContract: brokenMapping });
    expect(assessment.overallProductDefinitionReadinessState).toBe("BLOCKED_PRODUCT_TRUTH_WRITE_LEAK");
  });

  it("runtime ProductDefinition leak blocks readiness", () => {
    const rows = matchingLiveSet();
    rows[0] = {
      ...rows[0],
      notes: JSON.stringify({ product_definition_active: true, pricing_active: true }),
    };
    const assessment = productDefinitionReadinessFor(rows);
    expect(assessment.overallProductDefinitionReadinessState).toBe("BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK");
    expect(assessment.runtimeProductDefinitionLinkState).toBe("BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK");
  });

  it("activation-enabled contract entry blocks readiness", () => {
    const brokenContract = CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT.map((entry, index) =>
      index === 0 ? ({ ...entry, mayActivateProductDefinitionNow: true } as CandidateModuleProdusProductDefinitionConsumptionEntry) : entry
    );
    const assessment = productDefinitionReadinessFor([], { productDefinitionContract: brokenContract });
    expect(assessment.overallProductDefinitionReadinessState).toBe("BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK");
  });
});
