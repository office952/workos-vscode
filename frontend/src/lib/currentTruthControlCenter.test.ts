import { describe, expect, it } from "vitest";
import {
  CANONICAL_SPINE_LABELS_RO,
  PRESENT_BOUNDARIES,
  PRESENT_EVIDENCE,
  PRESENT_GATES,
  PRESENT_GUARDRAILS,
  PRESENT_HANDOFFS,
  PRESENT_OWNERSHIP_ROWS,
  PRESENT_SYSTEMS,
  assertNoMojibake,
  ownershipForSystem,
} from "@/lib/currentTruthControlCenter";

describe("Current Truth Control Center shared projection", () => {
  it("defines one canonical active spine", () => {
    expect(CANONICAL_SPINE_LABELS_RO).toEqual([
      "Catalog produse",
      "Intake V6",
      "ProductDefinition",
      "ProductAggregate",
      "Pricing / Commercial",
      "Quote Snapshot",
      "Order Snapshot",
      "ExecutionPlan",
      "Execution Reality",
      "Post-Job",
    ]);
    expect(PRESENT_SYSTEMS.map((s) => s.spineOrder)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  });

  it("scopes Letters canonical slice without global Product System overclaim", () => {
    const ps = PRESENT_SYSTEMS.find((s) => s.id === "product_system");
    expect(ps?.status).toBe("PARTIAL");
    expect(ps?.limitationRo).toMatch(/review_labels/);
    expect(ps?.limitationRo).toMatch(/MIXED/);
    expect(ps?.limitationRo).toMatch(/Nu deține tarife/);

    const intake = PRESENT_SYSTEMS.find((s) => s.id === "intake_v6");
    expect(intake?.limitationRo).toMatch(/review_labels/);
    expect(intake?.limitationRo).toMatch(/MIXED/);

    const handoffs = PRESENT_HANDOFFS.map((h) => h.id);
    expect(handoffs).toContain("h.ps_intake");
    expect(handoffs).toContain("h.pa_cpp");
    expect(handoffs).toContain("h.pa_plan");

    const psIntake = PRESENT_HANDOFFS.find((h) => h.id === "h.ps_intake");
    expect(psIntake?.status).toBe("PARTIAL");
    expect(psIntake?.outputContractRo).toMatch(/nu generare completă/i);

    const paCpp = PRESENT_HANDOFFS.find((h) => h.id === "h.pa_cpp");
    expect(paCpp?.status).toBe("PARTIAL");
    expect(paCpp?.outputContractRo).toMatch(/non-monetare/);
    expect(paCpp?.outputContractRo).toMatch(/fallback/i);
    expect(paCpp?.outputContractRo).toMatch(/fără minute/i);

    const paPlan = PRESENT_HANDOFFS.find((h) => h.id === "h.pa_plan");
    expect(paPlan?.outputContractRo).toMatch(/minute planificate/);
  });

  it("keeps ownership aligned with spine system ids", () => {
    for (const system of PRESENT_SYSTEMS) {
      const row = ownershipForSystem(system.id);
      expect(row, system.id).toBeTruthy();
      expect(row!.owner).toBeTruthy();
      expect(row!.status).toMatch(/CONFIRMAT|PARTIAL|BLOCAT|INACTIV|NEVERIFICAT/);
    }
  });

  it("does not encode legacy OC→TK as active handoffs", () => {
    const blob = PRESENT_HANDOFFS.map((h) => `${h.producerRo}->${h.consumerRo}`).join(" ");
    expect(blob).not.toMatch(/\bOC\b/);
    expect(blob).not.toMatch(/\bCostEngine\b/);
    expect(blob).not.toMatch(/\bWorkOS\b.*\bTasks\b/);
  });

  it("relocates PROVEN_V1 and legacy chain to evidence, not primary status", () => {
    expect(PRESENT_SYSTEMS.every((s) => s.status !== ("PROVEN_V1" as never))).toBe(true);
    expect(PRESENT_EVIDENCE.some((e) => e.title.includes("PROVEN_V1"))).toBe(true);
    expect(PRESENT_EVIDENCE.some((e) => e.id === "ev.legacy_oc_tk")).toBe(true);
    expect(PRESENT_EVIDENCE.find((e) => e.id === "ev.legacy_oc_tk")?.stillCurrentRuntime).toBe(false);
  });

  it("rewrites boundaries away from Quotes-calculează / isCalculable", () => {
    const text = JSON.stringify(PRESENT_BOUNDARIES);
    expect(text).not.toMatch(/Quotes calculează/i);
    expect(text).not.toMatch(/isCalculable/);
    expect(PRESENT_BOUNDARIES.some((b) => b.id === "b.quote")).toBe(true);
    expect(PRESENT_BOUNDARIES.find((b) => b.id === "b.quote")?.forbiddenRo.join(" ")).toMatch(
      /Nu recalculează|Nu inventează/
    );
  });

  it("keeps G01 rewritten and G13 present with enforcement class", () => {
    const g01 = PRESENT_GUARDRAILS.find((g) => g.id === "G01");
    const g13 = PRESENT_GUARDRAILS.find((g) => g.id === "G13");
    expect(g01?.requirementRo).toMatch(/CPP 7G calculează banii/);
    expect(g01?.requirementRo).toMatch(/măsurători non-monetare/);
    expect(g01?.requirementRo).toMatch(/minute operaționale/);
    expect(g01?.requirementRo).not.toMatch(/Quotes calculează/);
    expect(g13?.titleRo).toBe("UTF-8 end-to-end pentru textul operator");
    expect(g13?.status).toBe("PARTIAL APLICAT");
  });

  it("marks owner gates as policy, not fake readiness engine", () => {
    expect(PRESENT_GATES.every((g) => g.status === "POLITICA OWNER" || g.status === "PARTIAL APLICAT")).toBe(
      true
    );
    expect(JSON.stringify(PRESENT_GATES)).not.toMatch(/isCalculable/);
  });

  it("rejects mojibake in operator-visible Romanian content", () => {
    const texts = [
      ...PRESENT_SYSTEMS.flatMap((s) => [
        s.labelRo,
        s.purposeRo,
        s.limitationRo,
        s.inputRo,
        s.outputRo,
        s.consumerRo,
      ]),
      ...PRESENT_BOUNDARIES.flatMap((b) => [b.nameRo, b.truthControlledRo, ...b.allowedRo, ...b.forbiddenRo]),
      ...PRESENT_GUARDRAILS.flatMap((g) => [g.titleRo, g.requirementRo]),
      ...PRESENT_OWNERSHIP_ROWS.map((r) => r.domainRo),
    ];
    for (const t of texts) {
      expect(assertNoMojibake(t), t).toBe(true);
    }
  });
});
