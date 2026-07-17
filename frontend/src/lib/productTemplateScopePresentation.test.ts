import { describe, expect, it } from "vitest";
import type { ProductTemplateAvailabilityItem } from "@/lib/api";
import {
  getAnalyzerFirstScopePresentation,
  getProductTemplateScopePresentation,
} from "@/lib/productTemplateScopePresentation";

function makeAvailability(
  overrides: Partial<ProductTemplateAvailabilityItem>,
): ProductTemplateAvailabilityItem {
  return {
    template_id: 1,
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    description: "Fixture",
    db_active: true,
    quote_offerable: false,
    runtime_module: false,
    is_parent: true,
    has_modules: true,
    parent_codes: [],
    module_codes: [],
    status: "fixture",
    status_reason: "fixture",
    product_system_role: "candidate_product",
    display_group: "candidate_products",
    importance_rank: 20,
    owner_decision_required: true,
    readiness_reason: "Fixture",
    ui_label: "Produs in pregatire",
    ui_description: "Nu apare in Work Intake pana la GO owner.",
    parent_product_codes: [],
    child_module_codes: [],
    shared_with_product_codes: [],
    composition_modules: [],
    shared_component_contracts: [],
    ...overrides,
  };
}

describe("productTemplateScopePresentation", () => {
  it("maps Letters to the active direct-root Product Template contract", () => {
    const presentation = getProductTemplateScopePresentation(
      makeAvailability({
        template_code: "TPL-VOLUMETRIC-LETTERS_v2",
        quote_offerable: true,
        product_system_role: "offerable_product",
        display_group: "active_products",
        owner_decision_required: false,
        ui_label: "Produs activ pentru ofertare",
      }),
    );

    expect(presentation.isProductTemplate).toBe(true);
    expect(presentation.workIntakeLabel).toBe("Work Intake DA");
    expect(presentation.rootDirectLabel).toBe("Ofertabil ca rădăcină");
    expect(presentation.statusLabel).toBe("Rădăcină folosită azi");
    expect(presentation.catalogStatusLabel).toBe("Rădăcină folosită azi");
    expect(presentation.isDirectRootAllowed).toBe(true);
    expect(presentation.isCandidateComposition).toBe(false);
    expect(presentation.forbiddenReason).toBeNull();
    expect(presentation.catalogStatusLabel).not.toMatch(/^(ACTIVE|CONFIRMAT|PARTIAL)$/);
  });

  it("maps Logo to candidate composition and blocks direct root", () => {
    const presentation = getProductTemplateScopePresentation(
      makeAvailability({
        template_id: 15,
        template_code: "TPL-VOLUMETRIC-LOGO_v1",
        quote_offerable: false,
        product_system_role: "candidate_product",
        display_group: "candidate_products",
        owner_decision_required: true,
      }),
    );

    expect(presentation.isProductTemplate).toBe(true);
    expect(presentation.workIntakeLabel).toBe("Work Intake NU");
    expect(presentation.rootDirectLabel).toMatch(/Blocat ca rădăcină/i);
    expect(presentation.statusLabel).toBe("Candidat · rădăcină blocată");
    expect(presentation.catalogStatusLabel).toBe("Candidat · rădăcină blocată");
    expect(presentation.isDirectRootAllowed).toBe(false);
    expect(presentation.isCandidateComposition).toBe(true);
    expect(presentation.usageModeLabel).toMatch(/copil legat/i);
    expect(presentation.forbiddenReason).toMatch(/Necesită GO owner/i);
  });

  it("keeps Logo out of direct root and component-root classifications", () => {
    const presentation = getProductTemplateScopePresentation(
      makeAvailability({
        template_id: 15,
        template_code: "TPL-VOLUMETRIC-LOGO_v1",
        product_system_role: "candidate_product",
        display_group: "candidate_products",
      }),
    );

    expect(presentation.isDirectRootAllowed).toBe(false);
    expect(presentation.isProductTemplate).toBe(true);
    expect(presentation.usageModeLabel).not.toBe("component root");
  });

  it("keeps analyzer-first outside Product Template classification", () => {
    const analyzerFirst = getAnalyzerFirstScopePresentation();

    expect(analyzerFirst.isProductTemplate).toBe(false);
    expect(analyzerFirst.statusLabel).toBe("Recomandat");
    expect(analyzerFirst.shortDescription).toMatch(/SVG-ul decide compoziția/i);
  });
});