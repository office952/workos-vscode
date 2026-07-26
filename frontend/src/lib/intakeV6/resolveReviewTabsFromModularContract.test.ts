import { describe, expect, it } from "vitest";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";
import {
  contractCompositionProvenance,
  resolveReviewTabsFromModularContract,
} from "./resolveReviewTabsFromModularContract";

function makeContract(
  overrides: Partial<IntakeV6ModularFormContractResponse> = {},
): IntakeV6ModularFormContractResponse {
  return {
    summary: {
      template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      composition_authority: true,
      runtime_authority: false,
    },
    modules: [],
    field_bindings: [],
    trigger_alignments: [],
    render_sections: [
      {
        section_key: "finisaje_fields",
        title_ro: "Finisaje",
        order: 10,
        ui_tab_id: "finisaje",
        drives_review_tab: true,
        tab_label_ro: "Finisaje",
        tab_hint_ro: "Față · cant · Vector Logo",
        module_codes: ["debitare_fata"],
        component_owners: ["FACE", "CANT"],
      },
      {
        section_key: "iluminare",
        title_ro: "Iluminare",
        order: 20,
        ui_tab_id: "iluminare",
        drives_review_tab: true,
        tab_label_ro: "Iluminare",
        module_codes: ["sistem_led"],
        component_owners: ["LIGHTING"],
      },
      {
        section_key: "montaj_template",
        title_ro: "Șablon montaj",
        order: 30,
        ui_tab_id: "montaj",
        drives_review_tab: true,
        tab_label_ro: "Montaj",
        module_codes: ["sablon_montaj"],
        component_owners: ["INSTALLATION_TEMPLATE"],
      },
      {
        section_key: "interface_face_cant",
        title_ro: "Interfață",
        order: 50,
        renderer: "metadata_only",
        drives_review_tab: false,
        component_owners: ["INTERFACE_FACE_CANT"],
      },
    ],
    full_product_composition: {
      mode: "full_product_only",
      composition_authority: true,
      subset_activation_enabled: false,
      component_owners: ["FACE", "CANT", "LIGHTING"],
    },
    ...overrides,
  };
}

describe("resolveReviewTabsFromModularContract", () => {
  it("composes golden tab order from contract when composition_authority is true", () => {
    const tabs = resolveReviewTabsFromModularContract(makeContract());
    expect(tabs?.map((tab) => tab.id)).toEqual(["finisaje", "iluminare", "montaj"]);
    expect(tabs?.[0]?.label).toBe("Finisaje");
    expect(tabs?.[1]?.label).toBe("Iluminare și surse");
    expect(tabs?.[0]?.moduleCodes).toEqual(expect.arrayContaining(["FACE", "CANT"]));
  });

  it("returns null without composition_authority (plugin fallback)", () => {
    expect(
      resolveReviewTabsFromModularContract(
        makeContract({ summary: { template_code: "TPL-VOLUMETRIC-LETTERS_v2", composition_authority: false } }),
      ),
    ).toBeNull();
  });

  it("rejects subset/extra tab drift that would break golden UI", () => {
    const contract = makeContract();
    contract.render_sections = [
      ...(contract.render_sections ?? []),
      {
        section_key: "extra",
        title_ro: "Extra",
        order: 15,
        ui_tab_id: "finisaje",
        drives_review_tab: true,
      },
    ];
    // Duplicate finisaje is collapsed; still three unique tabs in golden order.
    expect(resolveReviewTabsFromModularContract(contract)?.map((t) => t.id)).toEqual([
      "finisaje",
      "iluminare",
      "montaj",
    ]);
  });

  it("exposes composition provenance without enabling subsets", () => {
    const provenance = contractCompositionProvenance(makeContract());
    expect(provenance.compositionAuthority).toBe(true);
    expect(provenance.subsetActivationEnabled).toBe(false);
    expect(provenance.sectionKeys).toContain("interface_face_cant");
  });
});
