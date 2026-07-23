import { describe, expect, it } from "vitest";
import { CANDIDATE_MODULE_SEMANTIC_LABEL } from "./candidateModuleProdusReadonlyUiShared";
import { CANONICAL_CONCEPTS } from "@/lib/productSystemCanonicalModel";
import {
  MINI_MODULE_OPERATIONAL_LABEL,
  MODULE_PRODUS_LABEL,
  PRODUCT_MODULES_SEMANTIC_LABEL,
  PRODUCT_TEMPLATE_LABEL,
  displayModuleSourceTypeLabel,
  equalModulesHintRo,
} from "./productTemplateModulesVocabulary";

describe("productTemplateModulesVocabulary (Nivel 1 labels)", () => {
  it("exposes Product Template → Module produs semantic label", () => {
    expect(PRODUCT_TEMPLATE_LABEL).toBe("Product Template");
    expect(MODULE_PRODUS_LABEL).toBe("Module produs");
    expect(PRODUCT_MODULES_SEMANTIC_LABEL).toContain("Product Template");
    expect(PRODUCT_MODULES_SEMANTIC_LABEL).toContain("Module produs");
    expect(PRODUCT_MODULES_SEMANTIC_LABEL).not.toMatch(/Component Template/i);
    expect(PRODUCT_MODULES_SEMANTIC_LABEL).not.toMatch(/Module Template/i);
    expect(PRODUCT_MODULES_SEMANTIC_LABEL).not.toMatch(/candidate-module/i);
  });

  it("aliases candidate-module semantic label to Module produs vocabulary", () => {
    expect(CANDIDATE_MODULE_SEMANTIC_LABEL).toBe(PRODUCT_MODULES_SEMANTIC_LABEL);
  });

  it("keeps mini-module labeled as operational, not product module", () => {
    expect(MINI_MODULE_OPERATIONAL_LABEL).toMatch(/operațional/i);
    expect(MINI_MODULE_OPERATIONAL_LABEL).not.toBe(MODULE_PRODUS_LABEL);
  });

  it("maps legacy source-type tokens for display", () => {
    expect(displayModuleSourceTypeLabel("component template / registry")).toBe("module / registry");
    expect(displayModuleSourceTypeLabel("component template")).toBe("module produs");
    expect(displayModuleSourceTypeLabel("module produs")).toBe("module produs");
  });

  it("states face/cant/back as equal modules", () => {
    expect(equalModulesHintRo()).toMatch(/egale/i);
    expect(equalModulesHintRo()).toMatch(/Față/i);
  });

  it("updates canonical dictionary away from Component Template as a separate type", () => {
    const moduleConcept = CANONICAL_CONCEPTS.find((c) => c.id === "component_template");
    const mini = CANONICAL_CONCEPTS.find((c) => c.id === "mini_module");
    expect(moduleConcept?.nameRo).toBe("Module produs");
    expect(moduleConcept?.technicalName).toBe("Module (product)");
    expect(moduleConcept?.technicalName).not.toMatch(/Component Template/i);
    expect(mini?.nameRo).toBe("Mini-modul operațional");
  });
});
