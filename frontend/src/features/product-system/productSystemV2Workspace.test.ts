import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { ProductTemplateAvailabilityItem } from "@/lib/api";
import {
  isPsLegacyCatalogEnabled,
  legacyCatalogHref,
  formatModuleStructureChip,
  partitionProductModulesForDisplay,
  PS_LEGACY_QUERY_KEY,
  PS_LEGACY_QUERY_VALUE,
} from "./productSystemV2WorkspaceModel";
import { PRODUCT_SYSTEM_SPINE_STEPS } from "./productTemplateModulesVocabulary";

function sampleAvailability(): ProductTemplateAvailabilityItem {
  return {
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    display_name: "Litere volumetrice",
    composition_modules: [
      {
        role_key: "front_face",
        role_label: "Fata litera",
        module_template_code: "TPL-VOLUMETRIC-FACE_v1",
        is_required: true,
        sort_order: 10,
        status_label: "Modul intern activ",
      },
      {
        role_key: "mounting_structure",
        role_label: "Structura montaj",
        module_template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
        is_required: false,
        sort_order: 60,
        status_label: "Optional / conditionat",
      },
      {
        role_key: "acm_boxed_mounting",
        role_label: "Alucobond casetat",
        module_template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        is_required: false,
        sort_order: 65,
        status_label: "Optional / conditionat",
      },
    ],
    shared_component_contracts: [
      {
        component_key: "volumetric_face",
        display_name: "Volumetric face",
        profile_key: "letters",
        module_template_code: "TPL-VOLUMETRIC-FACE_v1",
        confidence: "PARTIAL",
        owner_decision: "NEEDS_MORE_AUDIT",
        shared_truth_fields: [],
        not_confirmed: [],
      },
    ],
  } as ProductTemplateAvailabilityItem;
}

describe("productSystemV2Workspace", () => {
  it("keeps Oferta out of the Product System spine", () => {
    expect(PRODUCT_SYSTEM_SPINE_STEPS.some((step) => step.id === "offer")).toBe(false);
  });

  it("isolates legacy catalog behind ps_legacy query", () => {
    expect(PS_LEGACY_QUERY_KEY).toBe("ps_legacy");
    expect(PS_LEGACY_QUERY_VALUE).toBe("1");
    expect(isPsLegacyCatalogEnabled(new URLSearchParams("ps_legacy=1"))).toBe(true);
    expect(isPsLegacyCatalogEnabled(new URLSearchParams(""))).toBe(false);
    expect(legacyCatalogHref("TPL-VOLUMETRIC-LETTERS_v2")).toContain("ps_legacy=1");
    expect(legacyCatalogHref("TPL-VOLUMETRIC-LETTERS_v2")).toContain(
      "template=TPL-VOLUMETRIC-LETTERS_v2",
    );
  });

  it("wires ProductSystem page to V2 primary and CanonicalCatalog as legacy fallback", () => {
    const page = readFileSync(resolve(__dirname, "../../pages/ProductSystem.tsx"), "utf8");
    expect(page).toMatch(/ProductSystemV2Workspace/);
    expect(page).toMatch(/isPsLegacyCatalogEnabled/);
    expect(page).toMatch(/useLegacyCatalog \? \(/);
    expect(page).toMatch(/ProductSystemCanonicalCatalog/);
    expect(page).toMatch(/product-system-legacy-catalog-badge/);
    expect(page).toMatch(/product-system-return-v2-link/);
  });

  it("defines present workspace without past/legacy chrome mixed in", () => {
    const v2 = readFileSync(resolve(__dirname, "ProductSystemV2Workspace.tsx"), "utf8");
    expect(v2).toMatch(/data-workspace="v2-blank"/);
    expect(v2).toMatch(/ProductSystemStructureReadonlyPanel/);
    expect(v2).toMatch(/product-system-v2-modules-optional/);
    expect(v2).toMatch(/product-system-v2-shared-contracts/);
    expect(v2).toMatch(/Laborator vechi/);

    const structure = readFileSync(
      resolve(__dirname, "ProductSystemStructureReadonlyPanel.tsx"),
      "utf8",
    );
    expect(structure).toMatch(/Structură produs/);
    expect(structure).toMatch(/TemplateConstructionStageRow/);
    expect(structure).toMatch(/ComponentTimelineWrap/);
    expect(structure).toMatch(/parseTemplateComponentsWithLegacy/);
    expect(structure).toMatch(/isHiddenLettersFinisajStructureRow/);
    expect(structure).toMatch(/Finisaj produs ascuns/);
    expect(structure).not.toMatch(/product-system-v2-letters-finishes-hint/);
    expect(v2).toMatch(/product-system-v2-compiler/);
    expect(v2).toMatch(/product-system-v2-readiness/);
    expect(v2).toMatch(/product-system-v2-admin-drawer/);
    expect(v2).toMatch(/product-system-v2-downstream/);
    expect(v2).not.toMatch(/CANONICAL_CATALOG_OPERATOR_FILTERS/);
    expect(v2).not.toMatch(/product-system-canonical-filter/);
    expect(v2).not.toMatch(/Laboratory closure/);
    expect(v2).not.toMatch(/Catalog \/ studio vechi/);
    expect(v2).not.toMatch(/product-system-v2-legacy/);
    expect(v2).not.toMatch(/blank from zero/i);
  });

  it("partitions composition into core vs optional and keeps contracts out of Module produs", () => {
    const layers = partitionProductModulesForDisplay(sampleAvailability());
    expect(layers.core.map((row) => row.moduleCode)).toEqual(["TPL-VOLUMETRIC-FACE_v1"]);
    expect(layers.optional.map((row) => row.moduleCode)).toEqual([
      "TPL-METAL-PREMOUNT-STRUCTURE_v1",
      "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    ]);
    expect(layers.contracts).toHaveLength(1);
    expect(layers.contracts[0]?.component_key).toBe("volumetric_face");
    // Contracts must never be counted as composition module rows.
    expect(layers.core.some((row) => row.roleLabel === "Volumetric face")).toBe(false);
    expect(layers.optional.some((row) => row.roleLabel === "Volumetric face")).toBe(false);
  });

  it("formats structure chips for owner scanning", () => {
    expect(formatModuleStructureChip("Fata litera")).toBe("FATA LITERA");
    expect(formatModuleStructureChip("Cant / laterale")).toBe("CANT");
  });

  it("keeps downstream channels as secondary links only", () => {
    const channels = readFileSync(
      resolve(__dirname, "ProductSystemOfferCostChannels.tsx"),
      "utf8",
    );
    expect(channels).toMatch(/product-system-channel-cost-link/);
    expect(channels).toMatch(/product-system-channel-offer-link/);
    expect(channels).toMatch(/product-system-channel-execution-link/);
    expect(channels).not.toMatch(/commercial-price-preview/);
    expect(channels).not.toMatch(/estimated-internal-cost/);
  });
});
