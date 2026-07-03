import { describe, expect, it } from "vitest";
import { buildModuleActivationPreview } from "./intakeV6ModuleActivationPreview";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";

const SAMPLE_CONTRACT: IntakeV6ModularFormContractResponse = {
  summary: {
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    active_module_count: 7,
    field_binding_count: 22,
    warnings: [],
  },
  modules: [
    {
      module_code: "geometry_svg",
      module_name: "Analiză SVG și geometrie",
      operational_status: "ACTIVE_OPERATIONAL",
      activation_kind: "always_on",
      required_form_fields: ["vector_file"],
    },
    {
      module_code: "debitare_fata",
      module_name: "Debitare față litere",
      operational_status: "ACTIVE_OPERATIONAL",
      activation_kind: "always_on",
      required_form_fields: ["face_finish_type"],
    },
    {
      module_code: "modelare_cant",
      module_name: "Volum aluminiu — cant/lateral",
      operational_status: "ACTIVE_OPERATIONAL",
      activation_kind: "required_module",
    },
    {
      module_code: "debitare_spate",
      module_name: "Debitare spate litere",
      operational_status: "ACTIVE_OPERATIONAL",
      activation_kind: "always_on",
    },
    {
      module_code: "finisaje",
      module_name: "Finisaj, sablon montaj, ambalare",
      operational_status: "ACTIVE_OPERATIONAL",
      activation_kind: "conditional_gate",
    },
    {
      module_code: "structura_suport",
      module_name: "Structură metalică premontaj",
      operational_status: "ACTIVE_OPERATIONAL",
      activation_kind: "optional_addon",
      required_form_fields: [],
      intake_trigger_fields: ["mounting_system"],
    },
    {
      module_code: "sistem_led",
      module_name: "Sistem LED litere",
      operational_status: "ACTIVE_OPERATIONAL",
      activation_kind: "conditional_gate",
      required_form_fields: ["lighting_system_type"],
    },
  ],
  field_bindings: [],
  trigger_alignments: [
    {
      module_code: "structura_suport",
      module_link_trigger_field: "metal_support_required",
      canonical_intake_field: "finish_setup.mounting_system",
      derived_quote_input_key: "metal_support_required",
      warning_code: "TRIGGER_FIELD_MISMATCH",
      backwards_compatible: true,
    },
  ],
};

const READY_INPUT = {
  analysisReady: true,
  svgSource: { file_name: "test.svg" },
  quoteGeometry: { letter_count: 5 },
};

describe("buildModuleActivationPreview", () => {
  it("returns null when contract is missing", () => {
    expect(buildModuleActivationPreview(null, { analysisReady: true })).toBeNull();
  });

  it("places geometry in status and technical, not in product ready list", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: { mounting_system: "direct_wall", illuminated: false },
    });
    expect(preview).not.toBeNull();
    expect(preview!.operatorView.geometryStatus?.label).toBe("Fișier SVG analizat");
    expect(preview!.operatorView.productReady.some((l) => l.key === "geometry_svg")).toBe(false);
    expect(preview!.operatorView.technical.some((l) => l.key === "geometry_svg")).toBe(true);
  });

  it("uses operator-friendly labels for core product lines", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: { mounting_system: "direct_wall", illuminated: false },
    });
    const labels = preview!.operatorView.productReady.map((l) => l.label);
    expect(labels).toContain("Față litere");
    expect(labels).toContain("Laterale / cant");
    expect(labels).toContain("Spate litere");
    expect(labels).toContain("Iluminare LED");
    expect(labels).toContain("Finisaje");
  });

  it("excludes structura_suport from product and mounting when direct_wall", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: { mounting_system: "direct_wall", illuminated: false },
    });
    expect(preview!.operatorView.productReady.some((l) => l.key === "structura_suport")).toBe(false);
    expect(preview!.operatorView.mounting).toHaveLength(0);
    expect(preview!.operatorView.mountingNotApplicableNote).toContain("nu se aplică");
  });

  it("includes structura_suport in mounting section for bar mounting", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: {
        mounting_system: "steel_bars",
        illuminated: false,
      },
    });
    expect(preview!.operatorView.mounting.some((l) => l.key === "structura_suport")).toBe(true);
    expect(preview!.operatorView.mountingNotApplicableNote).toBeNull();
    expect(preview!.structuraSuportDerived).toBe(true);
  });

  it("marks LED module pending when illuminated but lighting not set", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: { illuminated: true, mounting_system: "direct_wall" },
    });
    const led = preview!.operatorView.productReady.find((l) => l.key === "sistem_led");
    expect(led?.state).toBe("pending");
    expect(led?.hint).toContain("completare");
  });

  it("does not mark face module as included when required face_finish_type is missing", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: { mounting_system: "direct_wall", illuminated: false },
    });
    const face = preview!.operatorView.productReady.find((l) => l.key === "debitare_fata");
    expect(face?.state).toBe("pending");
    expect(face?.missingFields).toContain("face_finish_type");
  });

  it("marks face module included when required fields are present", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: {
        mounting_system: "direct_wall",
        illuminated: false,
        face_finish_type: "ral",
      },
    });
    const face = preview!.operatorView.productReady.find((l) => l.key === "debitare_fata");
    expect(face?.state).toBe("always_on");
  });

  it("shows sablon hint on finisaje when mounting template enabled", () => {
    const preview = buildModuleActivationPreview(SAMPLE_CONTRACT, {
      ...READY_INPUT,
      finishSetup: {
        mounting_system: "direct_wall",
        illuminated: false,
        mounting_template_enabled: true,
      },
    });
    const finisaje = preview!.operatorView.productReady.find((l) => l.key === "finisaje");
    expect(finisaje?.hint).toContain("Șablon montaj activ");
  });
});
