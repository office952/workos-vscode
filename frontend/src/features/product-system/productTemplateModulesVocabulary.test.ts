import { describe, expect, it } from "vitest";
import { CANDIDATE_MODULE_SEMANTIC_LABEL } from "./candidateModuleProdusReadonlyUiShared";
import { CANONICAL_CONCEPTS } from "@/lib/productSystemCanonicalModel";
import {
  EXECUTION_PLAN_DRAFT_STATE_LABEL,
  EXECUTION_PLAN_OPERATIONAL_STATE_LABEL,
  EXECUTION_PLAN_PREVIEW_STATE_LABEL,
  INSTANCE_SCHEMA_ID_DISPLAY_LABEL,
  MINI_MODULE_OPERATIONAL_LABEL,
  MODULE_PRODUS_CODE_LABEL,
  MODULE_PRODUS_LABEL,
  MODULE_PRODUS_SHARED_LABEL,
  MODULE_PRODUS_SHARED_SINGULAR_LABEL,
  PRODUCT_COMPILER_LABEL,
  PRODUCT_MODULES_SEMANTIC_LABEL,
  PRODUCT_TEMPLATE_LABEL,
  PRODUCT_TEMPLATE_MODULE_LINKS_DISPLAY_LABEL,
  USAGE_MODE_DISPLAY_LABEL,
  displayModuleSourceTypeLabel,
  displayModuleTemplateWireLabel,
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

  it("exposes Product Compiler and Execution Plan three-state display vocabulary", () => {
    expect(PRODUCT_COMPILER_LABEL).toBe("Product Compiler");
    expect(EXECUTION_PLAN_PREVIEW_STATE_LABEL).toBe("Preview");
    expect(EXECUTION_PLAN_DRAFT_STATE_LABEL).toBe("Draft Plan");
    expect(EXECUTION_PLAN_OPERATIONAL_STATE_LABEL).toBe("Operational Plan");
  });

  it("adapts module_template_* wire keys to Module produs display labels without renaming contracts", () => {
    expect(displayModuleTemplateWireLabel("module_template_code")).toBe(MODULE_PRODUS_CODE_LABEL);
    expect(displayModuleTemplateWireLabel("shared_module_template_code")).toBe(MODULE_PRODUS_CODE_LABEL);
    expect(displayModuleTemplateWireLabel("component_template_code")).toBe(MODULE_PRODUS_CODE_LABEL);
    expect(displayModuleTemplateWireLabel("module_template_id")).toBe("Module produs id");
    expect(displayModuleTemplateWireLabel("product_template_module_links")).toBe(
      PRODUCT_TEMPLATE_MODULE_LINKS_DISPLAY_LABEL,
    );
    expect(displayModuleTemplateWireLabel("usage_mode")).toBe(USAGE_MODE_DISPLAY_LABEL);
    expect(displayModuleTemplateWireLabel("instance_schema_id")).toBe(INSTANCE_SCHEMA_ID_DISPLAY_LABEL);
    expect(displayModuleTemplateWireLabel("unrelated_field")).toBe("unrelated_field");
    expect(displayModuleTemplateWireLabel("instance_id")).toBe("instance_id");
  });

  it("exposes shared Module produs chrome constants for admin tables", () => {
    expect(MODULE_PRODUS_SHARED_LABEL).toBe("Module produs partajate");
    expect(MODULE_PRODUS_SHARED_SINGULAR_LABEL).toBe("Module produs partajat");
    expect(MODULE_PRODUS_SHARED_LABEL).not.toMatch(/Shared module/i);
  });
});
