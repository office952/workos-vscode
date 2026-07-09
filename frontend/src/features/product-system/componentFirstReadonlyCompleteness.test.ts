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
