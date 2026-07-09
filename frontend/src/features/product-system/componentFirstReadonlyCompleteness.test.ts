import { describe, expect, it } from "vitest";
import {
  COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES,
  COMPONENT_FIRST_EXPECTED_ROW_COUNT,
  COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE,
  assessComponentFirstContractDrift,
  assessComponentFirstLiveCompleteness,
  validateComponentFirstFallbackContract,
  type ComponentFirstFallbackContractRow,
  type ComponentFirstLiveTemplateRow,
} from "./componentFirstReadonlyCompleteness";
import {
  COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE,
  assessComponentFirstDossierAlignment,
  validateComponentFirstDossierContract,
} from "./componentFirstReadonlyDossierAlignment";
import {
  buildComponentFirstOwnerSummary,
  COMPONENT_FIRST_OWNER_FORBIDDEN_WORDING,
} from "./componentFirstReadonlyOwnerSummary";
import {
  assessComponentFirstFormSystemReadiness,
  COMPONENT_FIRST_FORM_SYSTEM_READINESS_CONTRACT,
  getComponentFirstFormReadinessEntry,
  validateComponentFirstFormSystemReadinessContract,
} from "./componentFirstReadonlyFormSystemReadiness";

function liveRow(
  templateCode: string,
  overrides: Partial<ComponentFirstLiveTemplateRow> = {}
): ComponentFirstLiveTemplateRow {
  return {
    template_code: templateCode,
    active: false,
    family_id: "litere_component_first_candidate",
    family_name: "Litere component-first candidate",
    ...overrides,
  };
}

function matchingLiveSet(): ComponentFirstLiveTemplateRow[] {
  return [
    liveRow(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE, {
      components_json: JSON.stringify(
        COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES.map((componentTemplateCode, index) => ({
          component_id: `comp_${index}`,
          component_template_code: componentTemplateCode,
          role: "face",
          kind: "structural",
        }))
      ),
      notes: JSON.stringify({ template_kind: "product_composer", readiness: "planned" }),
    }),
    ...COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES.map((templateCode, index) => {
      const fixture = COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE.find((row) => row.templateCode === templateCode);
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

describe("componentFirstReadonlyCompleteness fixture comparison", () => {
  it("fallback contract has exactly 7 expected rows", () => {
    const validation = validateComponentFirstFallbackContract();
    expect(COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE).toHaveLength(COMPONENT_FIRST_EXPECTED_ROW_COUNT);
    expect(validation.valid).toBe(true);
    expect(validation.issues).toEqual([]);
  });

  it("fallback contract has composer + 6 components", () => {
    const composerRows = COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE.filter((row) => row.rowKind === "composer");
    const componentRows = COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE.filter((row) => row.rowKind === "component");
    expect(composerRows).toHaveLength(1);
    expect(componentRows).toHaveLength(6);
    expect(composerRows[0]?.templateCode).toBe(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE);
  });

  it("detects duplicate expected code as fallback contract drift", () => {
    const brokenFixture: ComponentFirstFallbackContractRow[] = [
      ...COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE,
      { ...COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE[1] },
    ];
    const validation = validateComponentFirstFallbackContract(brokenFixture);
    expect(validation.valid).toBe(false);
    expect(validation.issues.some((issue) => issue.includes("duplicate"))).toBe(true);

    const drift = assessComponentFirstContractDrift([], brokenFixture);
    expect(drift.driftState).toBe("FALLBACK_CONTRACT_DRIFT");
  });

  it("reports NO_DRIFT for 7/7 live inactive rows matching expected contract", () => {
    const drift = assessComponentFirstContractDrift(matchingLiveSet());
    expect(drift.driftState).toBe("NO_DRIFT");
    expect(drift.contractCheckStatus).toBe("OK");
    expect(drift.completeness.sourceMode).toBe("live_seeded_inactive");
  });

  it("reports partial live rows without claiming live complete", () => {
    const partial = matchingLiveSet().slice(0, 3);
    const completeness = assessComponentFirstLiveCompleteness(partial);
    const drift = assessComponentFirstContractDrift(partial);

    expect(completeness.foundRowCount).toBe(3);
    expect(completeness.sourceMode).toBe("partial_live_inactive");
    expect(drift.completeness.missingTemplateCodes.length).toBeGreaterThan(0);
    expect(drift.driftState).toBe("NO_DRIFT");
  });

  it("reports BLOCKED_INVALID_LIVE_STATE when any expected row is active", () => {
    const rows = matchingLiveSet();
    rows[0] = { ...rows[0], active: true };
    const drift = assessComponentFirstContractDrift(rows);

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
    const drift = assessComponentFirstContractDrift(rows);

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
    const drift = assessComponentFirstContractDrift(rows);
    expect(drift.liveExtraFamilyRows).toContain("TPL-COMP-LETTER-EXTRA_v1");
    expect(drift.driftState).toBe("LIVE_EXTRA_EXPECTED_FAMILY_ROW");
  });
});

describe("componentFirstReadonlyDossierAlignment", () => {
  it("dossier alignment contract has exactly 7 entries", () => {
    const validation = validateComponentFirstDossierContract();
    expect(COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE).toHaveLength(COMPONENT_FIRST_EXPECTED_ROW_COUNT);
    expect(validation.valid).toBe(true);
    expect(validation.issues).toEqual([]);
  });

  it("composer is product_composer / composer_orchestration", () => {
    const composer = COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE.find(
      (entry) => entry.templateCode === COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE
    );
    expect(composer?.expectedKind).toBe("product_composer");
    expect(composer?.expectedDossierRole).toBe("composer_orchestration");
    expect(composer?.expectedTruthOwner).toBe("product_composer");
  });

  it("all 6 component templates are component_template / component-owned truth", () => {
    const componentEntries = COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE.filter(
      (entry) => entry.expectedKind === "component_template"
    );
    expect(componentEntries).toHaveLength(6);
    expect(componentEntries.every((entry) => entry.expectedTruthOwner === "component_owned_truth")).toBe(true);
    expect(componentEntries.map((entry) => entry.templateCode)).toEqual(COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES);
  });

  it("7/7 live inactive + 7/7 dossier contract => READONLY_ALIGNED", () => {
    const assessment = assessComponentFirstDossierAlignment(matchingLiveSet());
    expect(assessment.dossierContractCount).toBe(7);
    expect(assessment.liveFoundCount).toBe(7);
    expect(assessment.overallAlignmentState).toBe("READONLY_ALIGNED");
    expect(assessment.dossierRuntimeLinkState).toBe("NOT_LINKED_YET");
  });

  it("0/7 live + 7/7 dossier contract => READONLY_FALLBACK_ONLY", () => {
    const assessment = assessComponentFirstDossierAlignment([]);
    expect(assessment.dossierContractCount).toBe(7);
    expect(assessment.liveFoundCount).toBe(0);
    expect(assessment.overallAlignmentState).toBe("READONLY_FALLBACK_ONLY");
    expect(assessment.dossierRuntimeLinkState).toBe("READONLY_CONTRACT_ONLY");
  });

  it("partial live + 7/7 dossier contract => READONLY_PARTIAL", () => {
    const assessment = assessComponentFirstDossierAlignment(matchingLiveSet().slice(0, 3));
    expect(assessment.dossierContractCount).toBe(7);
    expect(assessment.liveFoundCount).toBe(3);
    expect(assessment.overallAlignmentState).toBe("READONLY_PARTIAL");
    expect(assessment.dossierRuntimeLinkState).toBe("PARTIAL_RUNTIME_LINK");
  });

  it("any active expected row => BLOCKED_INVALID_LIVE_STATE", () => {
    const rows = matchingLiveSet();
    rows[0] = { ...rows[0], active: true };
    const assessment = assessComponentFirstDossierAlignment(rows);
    expect(assessment.overallAlignmentState).toBe("BLOCKED_INVALID_LIVE_STATE");
  });

  it("runtime dossier not linked yet is readonly contract readiness, not failure", () => {
    const assessment = assessComponentFirstDossierAlignment([]);
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
    const assessment = assessComponentFirstDossierAlignment(rows);
    expect(assessment.overallAlignmentState).toBe("BLOCKED_DOSSIER_ACTIVATION_LEAK");
    expect(assessment.dossierRuntimeLinkState).toBe("BLOCKED_RUNTIME_ACTIVATION_LEAK");
    expect(assessment.runtimeActivationLeakIssues.length).toBeGreaterThan(0);
  });
});

function ownerSummaryFor(liveRows: ComponentFirstLiveTemplateRow[]) {
  const drift = assessComponentFirstContractDrift(liveRows);
  const dossier = assessComponentFirstDossierAlignment(liveRows, { drift });
  return buildComponentFirstOwnerSummary(drift.completeness, drift, dossier);
}

describe("componentFirstReadonlyOwnerSummary", () => {
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
      for (const forbidden of COMPONENT_FIRST_OWNER_FORBIDDEN_WORDING) {
        if (forbidden === "offerable") {
          expect(withoutNegatedOfferable).not.toContain("offerable");
          continue;
        }
        expect(text).not.toContain(forbidden.toLowerCase());
      }
    }
  });
});

function formReadinessFor(liveRows: ComponentFirstLiveTemplateRow[]) {
  const drift = assessComponentFirstContractDrift(liveRows);
  const dossier = assessComponentFirstDossierAlignment(liveRows, { drift });
  const owner = buildComponentFirstOwnerSummary(drift.completeness, drift, dossier);
  return assessComponentFirstFormSystemReadiness(drift.completeness, dossier, owner, {
    drift,
    liveTemplates: liveRows,
  });
}

describe("componentFirstReadonlyFormSystemReadiness", () => {
  it("Form System readiness contract has exactly 7 entries", () => {
    const validation = validateComponentFirstFormSystemReadinessContract();
    expect(COMPONENT_FIRST_FORM_SYSTEM_READINESS_CONTRACT).toHaveLength(COMPONENT_FIRST_EXPECTED_ROW_COUNT);
    expect(validation.valid).toBe(true);
    expect(validation.issues).toEqual([]);
  });

  it("composer coordinates sections only and owns_truth=false", () => {
    const composer = getComponentFirstFormReadinessEntry(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE);
    expect(composer?.role).toBe("product_composer");
    if (composer?.role === "product_composer") {
      expect(composer.ownsTruth).toBe(false);
      expect(composer.formSystemRole).toBe("compose_component_sections");
      expect(composer.coordinates).toContain("selected components");
    }
  });

  it("all 6 components own future fields", () => {
    const componentEntries = COMPONENT_FIRST_FORM_SYSTEM_READINESS_CONTRACT.filter(
      (entry) => entry.role === "component_template"
    );
    expect(componentEntries).toHaveLength(6);
    expect(componentEntries.every((entry) => entry.ownsTruth === true)).toBe(true);
    expect(componentEntries.every((entry) => entry.fieldGroups.length > 0)).toBe(true);
  });

  it("face includes material/thickness/finish target", () => {
    const face = getComponentFirstFormReadinessEntry("TPL-COMP-LETTER-FACE_v1");
    expect(face?.role).toBe("component_template");
    if (face?.role === "component_template") {
      expect(face.fieldGroups).toEqual(
        expect.arrayContaining(["face_material", "face_thickness", "face_finish_target"])
      );
    }
  });

  it("return_cant includes material/depth/finish", () => {
    const returnCant = getComponentFirstFormReadinessEntry("TPL-COMP-LETTER-RETURN-CANT_v1");
    if (returnCant?.role === "component_template") {
      expect(returnCant.fieldGroups).toEqual(
        expect.arrayContaining(["return_material", "return_depth", "return_finish"])
      );
    }
  });

  it("led includes illumination/led density/power supply", () => {
    const led = getComponentFirstFormReadinessEntry("TPL-COMP-LETTER-LED_v1");
    if (led?.role === "component_template") {
      expect(led.fieldGroups).toEqual(
        expect.arrayContaining(["illumination_mode", "led_density", "power_supply_policy"])
      );
    }
  });

  it("finish includes stock/oracal/ral/print policy", () => {
    const finish = getComponentFirstFormReadinessEntry("TPL-COMP-LETTER-FINISH_v1");
    if (finish?.role === "component_template") {
      expect(finish.fieldGroups).toEqual(
        expect.arrayContaining(["stock_color", "oracal_code", "ral_code", "print_lamination_policy"])
      );
    }
  });

  it("mounting includes surface/spacer/drilling/site notes", () => {
    const mounting = getComponentFirstFormReadinessEntry("TPL-COMP-LETTER-MOUNTING_v1");
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
