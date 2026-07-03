/**
 * BUILD 4 — Frontend tests for ProductSystem template display.
 *
 * Verifies:
 * 1. All 15 canonical component types are present in PRODUCT_COMPONENT_TYPES
 * 2. ProductComponentType union accepts all BUILD 4 types
 * 3. parseTemplateComponentsWithLegacy handles BUILD 4 types correctly
 * 4. validateTemplateComponentsStrict rejects unknown types
 */
import { describe, it, expect } from "vitest";
import {
  PRODUCT_COMPONENT_TYPES,
  parseTemplateComponentsWithLegacy,
  validateTemplateComponentsStrict,
  type ProductComponentType,
  type ProductTemplateComponent,
} from "@/lib/api";

// Canonical types — MUST match backend ALLOWED_COMPONENT_TYPES
const ORIGINAL_ACP_TYPES: ProductComponentType[] = [
  "STRUCTURA",
  "FATA_ACP_ROUTATA",
  "DIFUZIE_PLEXI",
  "ILUMINARE",
  "RELIEF_PLEXI_10MM",
  "FINISAJ",
];

const BUILD4_TYPES: ProductComponentType[] = [
  "PRINT_SUBSTRATE",
  "VINYL_APPLICATION",
  "PLEXI_PANEL",
  "FRAME_PROFILE",
  "LITERE_3D",
  "ELECTRIC_LED",
  "EXTERNALIZARE",
  "TAIERE_CNC_LASER",
  "LAMINARE",
];

const ALL_CANONICAL_TYPES = [...ORIGINAL_ACP_TYPES, ...BUILD4_TYPES];

describe("ProductSystem — Component Type Vocabulary", () => {
  it("PRODUCT_COMPONENT_TYPES contains all 15 canonical types", () => {
    expect(PRODUCT_COMPONENT_TYPES).toHaveLength(15);
    for (const t of ALL_CANONICAL_TYPES) {
      expect(PRODUCT_COMPONENT_TYPES).toContain(t);
    }
  });

  it("original 6 ACP types are present", () => {
    for (const t of ORIGINAL_ACP_TYPES) {
      expect(PRODUCT_COMPONENT_TYPES).toContain(t);
    }
  });

  it("BUILD 4 advertising types are present", () => {
    for (const t of BUILD4_TYPES) {
      expect(PRODUCT_COMPONENT_TYPES).toContain(t);
    }
  });

  it("no duplicate types exist", () => {
    const unique = new Set(PRODUCT_COMPONENT_TYPES);
    expect(unique.size).toBe(PRODUCT_COMPONENT_TYPES.length);
  });
});

describe("ProductSystem — parseTemplateComponentsWithLegacy", () => {
  it("parses a BUILD 4 PRINT_SUBSTRATE component", () => {
    const componentsJson = JSON.stringify([
      {
        component_id: "comp_banner_1",
        type: "PRINT_SUBSTRATE",
        name: "Banner PVC 510g",
        operations: [
          {
            code: "PRINT_ECOSOLVENT",
            name: "Printare ecosolvent",
            workcenter: "WC-PRINT-LF",
            estimatedMinutes: 45,
            sequence: 1,
            component_ref: "comp_banner_1",
          },
        ],
        materials: [
          {
            materialCode: "MAT-BANNER-PVC-510",
            name: "Banner PVC 510g/mp",
            quantity: 1,
            unit: "mp",
            component_ref: "comp_banner_1",
          },
        ],
      },
    ]);
    const result = parseTemplateComponentsWithLegacy(componentsJson, "[]", "[]");
    expect(result).toHaveLength(1);
    expect(result[0].type).toBe("PRINT_SUBSTRATE");
    expect(result[0].name).toBe("Banner PVC 510g");
    expect(result[0].operations).toHaveLength(1);
    expect(result[0].materials).toHaveLength(1);
  });

  it("parses a BUILD 4 EXTERNALIZARE component (mesh)", () => {
    const componentsJson = JSON.stringify([
      {
        component_id: "comp_mesh_ext",
        type: "EXTERNALIZARE",
        name: "Producție externalizată mesh",
        operations: [
          {
            code: "EXT_PRINT_MOUNT",
            name: "Externalizare print + montaj",
            workcenter: "WC-EXTERN",
            estimatedMinutes: 0,
            sequence: 1,
            component_ref: "comp_mesh_ext",
          },
        ],
        materials: [
          {
            materialCode: "MAT-MESH-340",
            name: "Mesh microperforat 340g",
            quantity: 1,
            unit: "mp",
            component_ref: "comp_mesh_ext",
          },
        ],
      },
    ]);
    const result = parseTemplateComponentsWithLegacy(componentsJson, "[]", "[]");
    expect(result).toHaveLength(1);
    expect(result[0].type).toBe("EXTERNALIZARE");
  });

  it("hydrates operation name from label when name is missing (BUILD 4 seed shape)", () => {
    const componentsJson = JSON.stringify([
      {
        component_id: "comp_face_litere",
        type: "LITERE_3D",
        name: "Față litere",
        operations: [
          {
            code: "face_cnc_cut",
            label: "Tăiere CNC față litere",
            workcenter: "CNC_ROUTER",
            estimated_minutes: 0,
            sequence: 2,
            calculation_type: "formula_based",
            formula_id: "perimeter_based_time",
          },
        ],
        materials: [],
      },
    ]);
    const result = parseTemplateComponentsWithLegacy(componentsJson, "[]", "[]");
    expect(result[0].operations[0].name).toBe("Tăiere CNC față litere");
    expect(result[0].operations[0]._extras?.label).toBe("Tăiere CNC față litere");
  });

  it("hydrates component_ref on nested ops/mats when omitted (BUILD 4 seed shape)", () => {
    const componentsJson = JSON.stringify([
      {
        component_id: "comp_face_litere",
        type: "LITERE_3D",
        name: "Față litere",
        operations: [
          {
            code: "vector_prep",
            label: "Pregătire vector",
            workcenter: "PREPRESS",
            estimated_minutes: 45,
            sequence: 1,
          },
        ],
        materials: [
          {
            materialCode: "MAT-ACP-FATA-LITERE",
            quantity: 0,
            unit: "mp",
            calculation_type: "formula_based",
            formula_id: "letter_face_area",
          },
        ],
      },
    ]);
    const result = parseTemplateComponentsWithLegacy(componentsJson, "[]", "[]");
    expect(result[0].operations[0].component_ref).toBe("comp_face_litere");
    expect(result[0].materials[0].component_ref).toBe("comp_face_litere");
    expect(validateTemplateComponentsStrict(result)).toHaveLength(0);
  });

  it("prefers operation name over label when both are present", () => {
    const componentsJson = JSON.stringify([
      {
        component_id: "comp_test",
        type: "FINISAJ",
        name: "Finisaj",
        operations: [
          {
            code: "qc_letters",
            name: "Control calitate",
            label: "QC din seed",
            workcenter: "QC_INSPECTION",
            estimatedMinutes: 15,
            sequence: 1,
          },
        ],
        materials: [],
      },
    ]);
    const result = parseTemplateComponentsWithLegacy(componentsJson, "[]", "[]");
    expect(result[0].operations[0].name).toBe("Control calitate");
  });

  it("parses mixed original + BUILD 4 components", () => {
    const componentsJson = JSON.stringify([
      {
        component_id: "comp_struct",
        type: "STRUCTURA",
        name: "Cadru metalic",
        operations: [],
        materials: [],
      },
      {
        component_id: "comp_led",
        type: "ELECTRIC_LED",
        name: "Sistem LED",
        operations: [],
        materials: [],
      },
      {
        component_id: "comp_frame",
        type: "FRAME_PROFILE",
        name: "Profil aluminiu",
        operations: [],
        materials: [],
      },
    ]);
    const result = parseTemplateComponentsWithLegacy(componentsJson, "[]", "[]");
    expect(result).toHaveLength(3);
    expect(result.map((c) => c.type)).toEqual([
      "STRUCTURA",
      "ELECTRIC_LED",
      "FRAME_PROFILE",
    ]);
  });
});

describe("ProductSystem — validateTemplateComponentsStrict", () => {
  const makeComponent = (type: string): ProductTemplateComponent => ({
    component_id: "comp_test",
    type: type as ProductComponentType,
    name: `Test ${type}`,
    operations: [
      {
        code: "OP1",
        name: "Op 1",
        workcenter: "wc1",
        estimatedMinutes: 10,
        sequence: 1,
        component_ref: "comp_test",
      },
    ],
    materials: [
      {
        materialCode: "MAT-X",
        name: "Material X",
        quantity: 1,
        unit: "pcs",
        component_ref: "comp_test",
      },
    ],
  });

  it("accepts all 15 canonical types", () => {
    for (const t of ALL_CANONICAL_TYPES) {
      const errors = validateTemplateComponentsStrict([makeComponent(t)]);
      expect(errors).toHaveLength(0);
    }
  });

  it("rejects unknown type UNKNOWN_TYPE", () => {
    const errors = validateTemplateComponentsStrict([
      makeComponent("UNKNOWN_TYPE"),
    ]);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0].code).toBe("COMPONENT_TYPE_INVALID");
  });

  it("rejects free-text type 'banner'", () => {
    const errors = validateTemplateComponentsStrict([
      makeComponent("banner"),
    ]);
    expect(errors.length).toBeGreaterThan(0);
  });
});

describe("ProductSystem — volumetric letters display labels", () => {
  it("maps comp_spate_litere STRUCTURA to Capac spate", async () => {
    const { getComponentTypeDisplayLabel } = await import(
      "@/features/product-system/componentTypeDisplay"
    );
    expect(
      getComponentTypeDisplayLabel(
        {
          component_id: "comp_spate_litere",
          type: "STRUCTURA",
          name: "Spate litere — Forex 10 mm",
          operations: [],
          materials: [],
        } as ProductTemplateComponent,
        "TPL-VOLUMETRIC-LETTERS",
        "Structură Metalică"
      )
    ).toBe("Capac spate");
  });

  it("maps face LITERE_3D to Vizual față", async () => {
    const { getComponentTypeDisplayLabel } = await import(
      "@/features/product-system/componentTypeDisplay"
    );
    expect(
      getComponentTypeDisplayLabel(
        {
          component_id: "comp_face_litere",
          type: "LITERE_3D",
          name: "Față litere — plexi/acrilic (CNC/laser)",
          operations: [],
          materials: [],
        } as ProductTemplateComponent,
        "TPL-VOLUMETRIC-LETTERS",
        "Litere 3D"
      )
    ).toBe("Vizual față");
  });

  it("maps lateral LITERE_3D to Volum aluminiu", async () => {
    const { getComponentTypeDisplayLabel } = await import(
      "@/features/product-system/componentTypeDisplay"
    );
    expect(
      getComponentTypeDisplayLabel(
        {
          component_id: "comp_lateral_litere",
          type: "LITERE_3D",
          name: "Laterale litere — profil aluminiu (bordură)",
          operations: [],
          materials: [],
        } as ProductTemplateComponent,
        "TPL-VOLUMETRIC-LETTERS",
        "Litere 3D"
      )
    ).toBe("Volum aluminiu");
  });

  it("keeps Structură metalică for optional premount on volumetric template", async () => {
    const { getComponentTypeDisplayLabel } = await import(
      "@/features/product-system/componentTypeDisplay"
    );
    expect(
      getComponentTypeDisplayLabel(
        {
          component_id: "comp_premontaj_suport",
          type: "STRUCTURA",
          name: "Structură metalică premontaj",
          operations: [],
          materials: [],
        } as ProductTemplateComponent,
        "TPL-VOLUMETRIC-LETTERS",
        "Structură Metalică"
      )
    ).toBe("Structură metalică");
  });

  it("shortens long material names for picker display", async () => {
    const { formatMaterialRegistryShortName } = await import(
      "@/features/product-system/materialRegistryDisplay"
    );
    expect(
      formatMaterialRegistryShortName(
        "Forex 10 mm spate litere (cod operațional MAT-SPATE-PVC-LITERE)"
      )
    ).toBe("Forex 10 mm spate litere");
  });

  it("does not override labels for non-volumetric templates", async () => {
    const { getComponentTypeDisplayLabel } = await import(
      "@/features/product-system/componentTypeDisplay"
    );
    expect(
      getComponentTypeDisplayLabel(
        {
          component_id: "comp_structura",
          type: "STRUCTURA",
          name: "Cadru metalic",
          operations: [],
          materials: [],
        } as ProductTemplateComponent,
        "TPL-ACP-LIGHT-ROUTED",
        "Structură Metalică"
      )
    ).toBe("Structură Metalică");
  });
});