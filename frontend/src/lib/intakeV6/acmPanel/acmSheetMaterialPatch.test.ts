import { describe, expect, it } from "vitest";
import {
  buildAcmPanelConfirmPanelPatch,
  buildAcmPanelSheetMaterialPatch,
} from "./operatorPatch";
import {
  ACM_SHEET_MATERIAL_SCHEMA,
  type AcmSheetMaterialContract,
} from "./acmSheetMaterial";
import type { AcmPanelComponentInstance } from "./types";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "./types";

function instance(sheetMaterial?: unknown): AcmPanelComponentInstance {
  return {
    schema: ACM_PANEL_INSTANCE_SCHEMA,
    component_instance_id: "acm_sheet_1",
    component_template_code: ACM_PANEL_TEMPLATE_CODE,
    intake_geometry_role_adapter: "SUPPORT_CONTOUR",
    role_status: "confirmed",
    association_status: "proposed",
    technical_configuration_status: "proposed",
    composition_status: "unconfirmed",
    capabilities: { active: ["boxed_returns"], inactive: [] },
    geometry: {
      contour_id: "cc",
      element_id: "el",
      geometry_hash: "h",
      width_mm: 1000,
      height_mm: 350,
      area_mm2: 1,
      perimeter_mm: 1,
      panels: [],
      joints: [],
    },
    configuration: {
      acm_thickness_mm: 3,
      fold_count: 2,
      l1_mm: 60,
      l2_mm: 25,
      finished_depth_mm: 60,
      internal_frame_enabled: false,
      service_corner: null,
      field_authority: {},
      field_class: {},
    },
    relations: [],
    svg_source_hash: null,
    updated_at: "2026-07-20T00:00:00.000Z",
    ...(sheetMaterial === undefined ? {} : { sheet_material: sheetMaterial }),
  };
}

function finish(sheetMaterial?: unknown) {
  return {
    acm_panel_instance: instance(sheetMaterial),
    mounting_solution: {
      kind: "product_system_template",
      template_code: ACM_PANEL_TEMPLATE_CODE,
      configuration: { acm_panel_instance: instance(sheetMaterial) },
    },
    svg_support_selection: {
      status: "proposed",
      acm_panel_instance: instance(sheetMaterial),
    },
  };
}

function readSheet(patch: unknown): AcmSheetMaterialContract | undefined {
  const inst = (patch as { acm_panel_instance?: AcmPanelComponentInstance })
    ?.acm_panel_instance;
  return inst?.sheet_material as AcmSheetMaterialContract | undefined;
}

describe("buildAcmPanelSheetMaterialPatch", () => {
  it("persists the contract on the canonical instance", () => {
    const patch = buildAcmPanelSheetMaterialPatch({
      finishSetup: finish(),
      sheetMaterial: { variant: "colorat", environment: "interior" },
    });
    expect(patch?.acm_panel_domain_action).toBe("upsert");
    const sheet = readSheet(patch);
    expect(sheet).toEqual({
      schema: ACM_SHEET_MATERIAL_SCHEMA,
      variant: "colorat",
      environment: "interior",
      exterior_sku: null,
      operator_confirmed: false,
    });
  });

  it("projects the contract through the selection and mounting mirrors", () => {
    const patch = buildAcmPanelSheetMaterialPatch({
      finishSetup: finish(),
      sheetMaterial: { variant: "standard", environment: "exterior" },
    });
    const selection = patch?.svg_support_selection as {
      acm_panel_instance?: AcmPanelComponentInstance;
    };
    const mounting = patch?.mounting_solution as {
      configuration?: { acm_panel_instance?: AcmPanelComponentInstance };
    };
    expect(
      (selection?.acm_panel_instance?.sheet_material as AcmSheetMaterialContract)?.variant,
    ).toBe("standard");
    expect(
      (
        mounting?.configuration?.acm_panel_instance
          ?.sheet_material as AcmSheetMaterialContract
      )?.environment,
    ).toBe("exterior");
  });

  it("keeps a proven SKU for mirror on exterior", () => {
    const patch = buildAcmPanelSheetMaterialPatch({
      finishSetup: finish(),
      sheetMaterial: {
        variant: "oglinda_gold",
        environment: "exterior",
        exterior_sku: "SKU-EXT-001",
      },
    });
    expect(readSheet(patch)?.exterior_sku).toBe("SKU-EXT-001");
  });

  it("drops a stale exterior_sku when the variant is no longer a mirror", () => {
    const patch = buildAcmPanelSheetMaterialPatch({
      finishSetup: finish({
        variant: "oglinda_gold",
        environment: "exterior",
        exterior_sku: "SKU-EXT-001",
      }),
      sheetMaterial: {
        variant: "standard",
        environment: "exterior",
        exterior_sku: "SKU-EXT-001",
      },
    });
    expect(readSheet(patch)?.variant).toBe("standard");
    expect(readSheet(patch)?.exterior_sku).toBeNull();
  });

  it("does not invent operator_confirmed", () => {
    const patch = buildAcmPanelSheetMaterialPatch({
      finishSetup: finish(),
      sheetMaterial: {
        variant: "standard",
        environment: "interior",
        operator_confirmed: false,
      },
    });
    expect(readSheet(patch)?.operator_confirmed).toBe(false);
  });

  it("records operator_confirmed when the caller confirms", () => {
    const patch = buildAcmPanelSheetMaterialPatch({
      finishSetup: finish(),
      sheetMaterial: { variant: "standard", environment: "interior" },
      confirm: true,
    });
    expect(readSheet(patch)?.operator_confirmed).toBe(true);
  });

  it("returns null without an instance or with unusable input", () => {
    expect(
      buildAcmPanelSheetMaterialPatch({
        finishSetup: {},
        sheetMaterial: { variant: "standard" },
      }),
    ).toBeNull();
    expect(
      buildAcmPanelSheetMaterialPatch({
        finishSetup: finish(),
        sheetMaterial: [] as unknown as Record<string, unknown>,
      }),
    ).toBeNull();
  });

  it("leaves composition unconfirmed", () => {
    const patch = buildAcmPanelSheetMaterialPatch({
      finishSetup: finish(),
      sheetMaterial: { variant: "standard", environment: "interior" },
    });
    const inst = patch?.acm_panel_instance as AcmPanelComponentInstance;
    expect(inst.composition_status).toBe("unconfirmed");
  });
});

describe("confirm panel and sheet material", () => {
  it("confirms a sheet material the operator actually selected", () => {
    const patch = buildAcmPanelConfirmPanelPatch({
      finishSetup: finish({ variant: "oglinda_antracit", environment: "interior" }),
    });
    expect(readSheet(patch)?.operator_confirmed).toBe(true);
  });

  it("never confirms an incomplete sheet material", () => {
    const partial = buildAcmPanelConfirmPanelPatch({
      finishSetup: finish({ variant: "standard" }),
    });
    expect(readSheet(partial)?.variant).toBe("standard");
    expect(readSheet(partial)?.operator_confirmed).not.toBe(true);

    const absent = buildAcmPanelConfirmPanelPatch({ finishSetup: finish() });
    expect(readSheet(absent)).toBeUndefined();
  });
});
