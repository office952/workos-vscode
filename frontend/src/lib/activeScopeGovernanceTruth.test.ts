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

  it("registers Active Scope as PARTIAL/CONFLICTED — not COMPLETE", () => {
    expect(ACTIVE_SCOPE_SYSTEM.canonicalSystemId).toBe("active_scope_sold_scope");
    expect(ACTIVE_SCOPE_SYSTEM.runtimeStatus).toBe("PARTIAL");
    expect(ACTIVE_SCOPE_SYSTEM.boundariesRo).toMatch(/PARTIAL|CONFLICTED|NOT/);
    expect(ACTIVE_SCOPE_SYSTEM.ownerGatesRo).toMatch(/STOP/);
    expect(ACTIVE_SCOPE_SYSTEM.owner).toMatch(/ProductDefinition/);
    expect(ACTIVE_SCOPE_TARGET_NOTE_RO).toMatch(/nu implementat|Nu afișa/i);

    const support = PRESENT_SUPPORT_SYSTEMS.find((s) => s.id === "active_scope_sold_scope");
    expect(support?.status).toBe("PARTIAL");
    expect(support?.limitationRo).toMatch(/STOP|CONFLICTED|NOT CONSUMED/);
  });

  it("keeps active-scope handoffs honest (PD failed, CPP conflicted, exec guarded)", () => {
    const byId = Object.fromEntries(ACTIVE_SCOPE_HANDOFFS.map((h) => [h.id, h]));
    expect(byId["as.intake_offer_scope"]?.status).toBe("CONFIRMED");
    expect(byId["as.offer_scope_fe"]?.status).toBe("CONFIRMED");
    expect(byId["as.offer_scope_pd"]?.status).toBe("FAILED / NOT CONSUMED");
    expect(byId["as.aggregate_cpp"]?.status).toBe("CONFLICTED");
    expect(byId["as.frozen_exec"]?.status).toBe("CONFIRMED_WITH_GUARDS");
    expect(ACTIVE_SCOPE_HANDOFFS.every((h) => h.status !== ("COMPLETE" as never))).toBe(true);
  });

  it("documents readiness law, dependency classes, hybrid intake", () => {
    expect(ACTIVE_SCOPE_READINESS_LAW.inactiveMustNotRo.join(" ")).toMatch(/warnings|linii comerciale|task/);
    expect(ACTIVE_SCOPE_READINESS_LAW.ownerLawRo.join(" ")).toMatch(/NEALES|SUSTINA|CAPTIVE/);
    expect(DEPENDENCY_CLASSES.map((c) => c.id)).toEqual([
      "hard_technical",
      "conditional",
      "composition_only",
      "commercial",
      "execution",
    ]);
    expect(HYBRID_INTAKE_MODEL.approvedModel).toBe("HYBRID");
    expect(HYBRID_INTAKE_MODEL.downstreamStatus).toBe("NOT YET PROVEN");
    expect(HYBRID_INTAKE_MODEL.noteRo).toMatch(/NOT YET PROVEN/);
    expect(HYBRID_INTAKE_MODEL.noteRo).not.toMatch(/\bCOMPLETE\b/);
  });

  it("keeps product independence statuses honest", () => {
    const letters = MODULE_INDEPENDENCE_PRODUCT_STATUS.find((p) => p.id === "letters");
    const logo = MODULE_INDEPENDENCE_PRODUCT_STATUS.find((p) => p.id === "logo");
    const acm = MODULE_INDEPENDENCE_PRODUCT_STATUS.find((p) => p.id === "acm");
    expect(letters && "moduleIndependence" in letters && letters.moduleIndependence).toBe("PARTIAL");
    expect(letters && "modeledReturn" in letters && letters.modeledReturn.final).toBe("PARTIAL");
    expect(letters && "modeledReturn" in letters && letters.modeledReturn.pdActiveScope).toBe("FAILED");
    expect(logo && "componentIndependence" in logo && logo.componentIndependence).toBe("BLOCKED");
    expect(logo && "rootOfferability" in logo && logo.rootOfferability).toBe("BLOCKED");
    expect(acm && "componentIndependence" in acm && acm.componentIndependence).toBe("PARTIAL");
  });

  it("groups FULL_TEMPLATE_COUPLING and blocks runtime implementation", () => {
    expect(FULL_TEMPLATE_COUPLING_DEFECT.id).toBe("FULL_TEMPLATE_COUPLING");
    expect(FULL_TEMPLATE_COUPLING_DEFECT.runtimeImplementation).toBe("STOP");
    expect(FULL_TEMPLATE_COUPLING_DEFECT.includesRo.join(" ")).toMatch(/always-on|live-calc|FACE-only/);
    expect(PRESENT_GATES.some((g) => g.id === "g.owner_active_scope_runtime")).toBe(true);
    expect(PRESENT_GUARDRAILS.some((g) => g.id === "G14")).toBe(true);
    expect(PRESENT_GUARDRAILS.find((g) => g.id === "G14")?.status).toBe("NEAPLICAT");
    expect(PRESENT_GUARDRAILS.find((g) => g.id === "G15")?.status).toBe("APLICAT");
    expect(PRESENT_GUARDRAILS.find((g) => g.id === "G16")?.status).toBe("APLICAT");
  });

  it("links evidence without promoting audit to Level-1 status", () => {
    const audit = PRESENT_EVIDENCE.find((e) => e.id === "ev.module_independence_audit");
    expect(audit?.source).toMatch(/module_independence_e2e_audit/);
    expect(audit?.provesRo).toMatch(/Level-3|nu override/i);
    expect(PRESENT_EVIDENCE.find((e) => e.id === "ev.module_independence_worklog")?.stillCurrentRuntime).toBe(
      false
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

  it("keeps Active Scope ownership row and PD as PARTIAL", () => {
    expect(ownershipForSystem("active_scope_sold_scope")?.status).toBe("PARTIAL");
    expect(ownershipForSystem("product_definition")?.status).toBe("PARTIAL");
    expect(ownershipForSystem("product_definition")?.enforcementRo).toMatch(/NOT CONSUMED|REWORK/);
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
