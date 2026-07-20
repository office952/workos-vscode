import { describe, expect, it } from "vitest";
import {
  buildAcmPanelConfirmTechnicalPatch,
  buildAcmPanelConfirmConstructionPatch,
  buildAcmPanelUpdateFieldPatch,
  assertNoCompositionAutoConfirm,
} from "./operatorPatch";
import type { AcmPanelComponentInstance } from "./types";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "./types";

function instance(): AcmPanelComponentInstance {
  return {
    schema: ACM_PANEL_INSTANCE_SCHEMA,
    component_instance_id: "acm_op_1",
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
      field_authority: {
        panel_geometry: "detected",
        fold_count: "catalog_default",
        l1_mm: "catalog_default",
        l2_mm: "catalog_default",
        acm_thickness_mm: "catalog_default",
        finished_depth_mm: "catalog_default",
      },
      field_class: {},
    },
    relations: [],
    svg_source_hash: null,
    updated_at: "2026-07-20T00:00:00.000Z",
  };
}

function finish() {
  return {
    acm_panel_instance: instance(),
    mounting_solution: {
      kind: "product_system_template",
      template_code: ACM_PANEL_TEMPLATE_CODE,
      configuration: { acm_panel_instance: instance() },
    },
    svg_support_selection: { status: "proposed", acm_panel_instance: instance() },
  };
}

describe("acmPanel operatorPatch", () => {
  it("update field without confirmAuthority marks proposed, not operator_confirmed", () => {
    const patch = buildAcmPanelUpdateFieldPatch({
      finishSetup: finish(),
      field: "acm_thickness_mm",
      value: 4,
    });
    expect(patch?.acm_panel_domain_action).toBe("upsert");
    const inst = patch?.acm_panel_instance as AcmPanelComponentInstance;
    expect(inst.configuration.acm_thickness_mm).toBe(4);
    expect(inst.configuration.field_authority.acm_thickness_mm).toBe("proposed");
    expect(inst.composition_status).toBe("unconfirmed");
    expect(assertNoCompositionAutoConfirm(patch)).toBe(true);
  });

  it("confirm construction sets operator_confirmed authorities without composition confirm", () => {
    const patch = buildAcmPanelConfirmConstructionPatch({ finishSetup: finish() });
    const inst = patch?.acm_panel_instance as AcmPanelComponentInstance;
    expect(inst.configuration.field_authority.fold_count).toBe("operator_confirmed");
    expect(inst.composition_status).toBe("unconfirmed");
  });

  it("confirm technical does not auto-confirm composition", () => {
    const patch = buildAcmPanelConfirmTechnicalPatch({ finishSetup: finish() });
    const inst = patch?.acm_panel_instance as AcmPanelComponentInstance;
    expect(inst.technical_configuration_status).toBe("confirmed");
    expect(inst.association_status).toBe("confirmed");
    expect(inst.composition_status).toBe("unconfirmed");
    expect(patch?.acm_panel_instance).toBeTruthy();
    expect(
      (patch?.mounting_solution as { configuration?: { acm_panel_instance?: unknown } })
        ?.configuration?.acm_panel_instance,
    ).toBeTruthy();
  });

  it("syncs top-level instance from nest-only finish", () => {
    const nestOnly = {
      mounting_solution: {
        kind: "product_system_template",
        template_code: ACM_PANEL_TEMPLATE_CODE,
        configuration: { acm_panel_instance: instance() },
      },
    };
    const patch = buildAcmPanelConfirmTechnicalPatch({ finishSetup: nestOnly });
    expect(patch?.acm_panel_instance).toBeTruthy();
    expect((patch?.acm_panel_instance as AcmPanelComponentInstance).composition_status).toBe(
      "unconfirmed",
    );
  });
});
