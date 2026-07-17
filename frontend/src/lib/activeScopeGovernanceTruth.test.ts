import { describe, expect, it } from "vitest";
import {
  ACTIVE_SCOPE_HANDOFFS,
  ACTIVE_SCOPE_READINESS_LAW,
  ACTIVE_SCOPE_SYSTEM,
  ACTIVE_SCOPE_TARGET_NOTE_RO,
  DEPENDENCY_CLASSES,
  DOCUMENTATION_HIERARCHY,
  FULL_TEMPLATE_COUPLING_DEFECT,
  HYBRID_INTAKE_MODEL,
  MODULE_INDEPENDENCE_PRODUCT_STATUS,
  OFFICIAL_CURRENT_TRUTH_ROUTES,
  SYSTEM_REGISTRATION_REQUIRED_FIELDS,
  UNREGISTERED_SYSTEM_POLICY,
} from "@/lib/activeScopeGovernanceTruth";
import { CANONICAL_ROUTES } from "@/lib/productSystemCanonicalModel";
import {
  PRESENT_EVIDENCE,
  PRESENT_GATES,
  PRESENT_GUARDRAILS,
  PRESENT_SUPPORT_SYSTEMS,
  PRESENT_SYSTEMS,
  assertNoMojibake,
  ownershipForSystem,
} from "@/lib/currentTruthControlCenter";

describe("Active-scope governance registration", () => {
  it("declares /modules + /governance as official Level-1 current truth", () => {
    expect(OFFICIAL_CURRENT_TRUTH_ROUTES.modules).toBe("/modules");
    expect(OFFICIAL_CURRENT_TRUTH_ROUTES.governance).toBe("/governance");
    expect(DOCUMENTATION_HIERARCHY[0]?.level).toBe(1);
    expect(DOCUMENTATION_HIERARCHY[0]?.surfacesRo).toMatch(/\/modules/);
    expect(DOCUMENTATION_HIERARCHY[0]?.surfacesRo).toMatch(/\/governance/);
    expect(DOCUMENTATION_HIERARCHY.some((l) => l.id === "evidence")).toBe(true);
    expect(DOCUMENTATION_HIERARCHY.some((l) => l.id === "history")).toBe(true);
  });

  it("defines UNREGISTERED_SYSTEM policy and required registration fields", () => {
    expect(UNREGISTERED_SYSTEM_POLICY.id).toBe("UNREGISTERED_SYSTEM");
    expect(UNREGISTERED_SYSTEM_POLICY.status).toBe("ACTIVE");
    expect(UNREGISTERED_SYSTEM_POLICY.mayNotRo.join(" ")).toMatch(/sursă de adevăr|production-ready|E2E/);
    for (const field of [
      "canonicalSystemId",
      "owner",
      "runtimeStatus",
      "uiApiLinks",
      "supportingEvidence",
    ]) {
      expect(SYSTEM_REGISTRATION_REQUIRED_FIELDS).toContain(field);
    }
    for (const field of SYSTEM_REGISTRATION_REQUIRED_FIELDS) {
      expect(ACTIVE_SCOPE_SYSTEM[field], field).toBeTruthy();
    }
  });

  it("registers Active Scope as PARTIAL / PROVEN FOR LETTERS SLICE 1", () => {
    expect(ACTIVE_SCOPE_SYSTEM.canonicalSystemId).toBe("active_scope_sold_scope");
    expect(ACTIVE_SCOPE_SYSTEM.runtimeStatus).toBe("PARTIAL");
    expect(ACTIVE_SCOPE_SYSTEM.boundariesRo).toMatch(/PROVEN FOR LETTERS SLICE 1/);
    expect(ACTIVE_SCOPE_SYSTEM.ownerGatesRo).toMatch(/Logo BLOCKED|ACM PARTIAL/);
    expect(ACTIVE_SCOPE_SYSTEM.owner).toMatch(/ProductDefinition/);
    expect(ACTIVE_SCOPE_TARGET_NOTE_RO).toMatch(/proven|Slice 1/i);

    const support = PRESENT_SUPPORT_SYSTEMS.find((s) => s.id === "active_scope_sold_scope");
    expect(support?.status).toBe("PARTIAL");
    expect(support?.limitationRo).toMatch(/PROVEN FOR LETTERS SLICE 1/);
  });

  it("marks Slice 1 handoffs proven (PD/Aggregate/CPP/exec)", () => {
    const byId = Object.fromEntries(ACTIVE_SCOPE_HANDOFFS.map((h) => [h.id, h]));
    expect(byId["as.intake_offer_scope"]?.status).toBe("CONFIRMED");
    expect(byId["as.offer_scope_fe"]?.status).toBe("CONFIRMED");
    expect(byId["as.offer_scope_pd"]?.status).toBe("PROVEN");
    expect(byId["as.pd_aggregate"]?.status).toBe("PROVEN");
    expect(byId["as.aggregate_cpp"]?.status).toBe("PROVEN");
    expect(byId["as.frozen_exec"]?.status).toBe("PROVEN");
    expect(byId["as.scope_snapshot"]?.status).toBe("PARTIAL");
  });

  it("documents readiness law, dependency classes, hybrid intake", () => {
    expect(ACTIVE_SCOPE_READINESS_LAW.inactiveMustNotRo.join(" ")).toMatch(/warnings|linii comerciale|task/);
    expect(ACTIVE_SCOPE_READINESS_LAW.ownerLawRo.join(" ")).toMatch(/NEALES|SUSTINA|CAPTIVE/);
    expect(ACTIVE_SCOPE_READINESS_LAW.status).toMatch(/PROVEN FOR LETTERS SLICE 1/);
    expect(DEPENDENCY_CLASSES.map((c) => c.id)).toEqual([
      "hard_technical",
      "conditional",
      "composition_only",
      "commercial",
      "execution",
    ]);
    expect(HYBRID_INTAKE_MODEL.approvedModel).toBe("HYBRID");
    expect(HYBRID_INTAKE_MODEL.downstreamStatus).toBe("PROVEN FOR LETTERS SLICE 1");
    expect(HYBRID_INTAKE_MODEL.noteRo).toMatch(/PROVEN SLICE 1/);
  });

  it("keeps product independence statuses honest", () => {
    const letters = MODULE_INDEPENDENCE_PRODUCT_STATUS.find((p) => p.id === "letters");
    const logo = MODULE_INDEPENDENCE_PRODUCT_STATUS.find((p) => p.id === "logo");
    const acm = MODULE_INDEPENDENCE_PRODUCT_STATUS.find((p) => p.id === "acm");
    expect(letters && "moduleIndependence" in letters && letters.moduleIndependence).toMatch(
      /PARTIAL|PROVEN FOR SLICE 1/
    );
    expect(letters && "modeledReturn" in letters && letters.modeledReturn.final).toBe("READY");
    expect(letters && "modeledReturn" in letters && letters.modeledReturn.pdActiveScope).toBe("READY");
    expect(logo && "componentIndependence" in logo && logo.componentIndependence).toBe("BLOCKED");
    expect(logo && "rootOfferability" in logo && logo.rootOfferability).toBe("BLOCKED");
    expect(acm && "componentIndependence" in acm && acm.componentIndependence).toBe("PARTIAL");
  });

  it("records FULL_TEMPLATE_COUPLING remediation on Letters Slice 1", () => {
    expect(FULL_TEMPLATE_COUPLING_DEFECT.id).toBe("FULL_TEMPLATE_COUPLING");
    expect(FULL_TEMPLATE_COUPLING_DEFECT.runtimeImplementation).toBe("PROVEN FOR LETTERS SLICE 1");
    expect(FULL_TEMPLATE_COUPLING_DEFECT.includesRo.join(" ")).toMatch(/active_scope|selected graph|FACE-only/);
    expect(PRESENT_GATES.some((g) => g.id === "g.owner_active_scope_runtime")).toBe(true);
    expect(PRESENT_GUARDRAILS.some((g) => g.id === "G14")).toBe(true);
    expect(PRESENT_GUARDRAILS.find((g) => g.id === "G14")?.status).toBe("PARTIAL APLICAT");
    expect(PRESENT_GUARDRAILS.find((g) => g.id === "G15")?.status).toBe("APLICAT");
    expect(PRESENT_GUARDRAILS.find((g) => g.id === "G16")?.status).toBe("APLICAT");
  });

  it("links evidence without promoting audit to Level-1 status", () => {
    const audit = PRESENT_EVIDENCE.find((e) => e.id === "ev.module_independence_audit");
    expect(audit?.source).toMatch(/module_independence_e2e_audit/);
    expect(audit?.stillCurrentRuntime).toBe(false);
    expect(PRESENT_EVIDENCE.find((e) => e.id === "ev.active_scope_v1_worklog")?.stillCurrentRuntime).toBe(
      true
    );
  });

  it("keeps canonical Inventory / Pricing / Dossier routes exact", () => {
    expect(CANONICAL_ROUTES.inventory).toBe("/inventory");
    expect(CANONICAL_ROUTES.pricing).toBe("/inventory/pricing");
    expect(CANONICAL_ROUTES.dossier).toBe("/product-system/blueprint-dossier");
    expect(PRESENT_SYSTEMS.find((s) => s.id === "pricing_commercial")?.verifyRoute).toBe(
      "/inventory/pricing"
    );
    expect(PRESENT_SUPPORT_SYSTEMS.find((s) => s.id === "inventory")?.verifyRoute).toBe("/inventory");
    expect(PRESENT_SUPPORT_SYSTEMS.find((s) => s.id === "dossier")?.verifyRoute).toBe(
      "/product-system/blueprint-dossier"
    );
  });

  it("keeps Active Scope ownership row and PD as PARTIAL (slice-proven)", () => {
    expect(ownershipForSystem("active_scope_sold_scope")?.status).toBe("PARTIAL");
    expect(ownershipForSystem("product_definition")?.status).toBe("PARTIAL");
    expect(ownershipForSystem("product_definition")?.enforcementRo).toMatch(/PROVEN|Slice 1/);
    expect(PRESENT_SYSTEMS.find((s) => s.id === "product_definition")?.status).toBe("PARTIAL");
  });

  it("rejects mojibake in active-scope Romanian strings", () => {
    const texts = [
      ACTIVE_SCOPE_SYSTEM.roleRo,
      ACTIVE_SCOPE_READINESS_LAW.bindingRo,
      ...ACTIVE_SCOPE_READINESS_LAW.ownerLawRo,
      ...DEPENDENCY_CLASSES.map((c) => c.definitionRo),
      FULL_TEMPLATE_COUPLING_DEFECT.doNotRo,
    ];
    for (const t of texts) {
      expect(assertNoMojibake(t), t).toBe(true);
    }
  });
});
