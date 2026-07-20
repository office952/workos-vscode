import { describe, expect, it } from "vitest";
import { buildAcmPanelUiReadModel, authorityToOperator, lifecycleToOperator } from "./uiReadModel";
import type { AcmPanelComponentInstance } from "./types";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "./types";

function baseInstance(
  overrides: Partial<AcmPanelComponentInstance> = {},
): AcmPanelComponentInstance {
  return {
    schema: ACM_PANEL_INSTANCE_SCHEMA,
    component_instance_id: "acm_test_1",
    component_template_code: ACM_PANEL_TEMPLATE_CODE,
    intake_geometry_role_adapter: "SUPPORT_CONTOUR",
    role_status: "confirmed",
    association_status: "proposed",
    technical_configuration_status: "proposed",
    composition_status: "unconfirmed",
    capabilities: { active: ["boxed_returns", "segmented_panels"], inactive: ["totem_face"] },
    geometry: {
      contour_id: "cc_1",
      element_id: "el-1",
      geometry_hash: "abc",
      width_mm: 1000,
      height_mm: 350,
      area_mm2: 350000,
      perimeter_mm: 2700,
      panels: [
        {
          panel_id: "panel_1",
          order: 1,
          width_mm: 1000,
          height_mm: 350,
          position: { x_mm: 0, y_mm: 0 },
        },
        {
          panel_id: "panel_2",
          order: 2,
          width_mm: 1000,
          height_mm: 350,
          position: { x_mm: 1000, y_mm: 0 },
        },
      ],
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
        finished_depth_mm: "catalog_default",
        acm_thickness_mm: "catalog_default",
        internal_frame: "catalog_default",
      },
      field_class: {
        panel_geometry: "critical",
        fold_count: "critical",
        l1_mm: "critical",
        l2_mm: "critical",
        acm_thickness_mm: "critical",
        finished_depth_mm: "critical",
      },
    },
    relations: [
      {
        relation_id: "r1",
        from_component_ref: "panel_1",
        to_component_ref: "acm_test_1",
        relation_type: "belongs_to_assembly",
        status: "proposed",
        provenance: "test",
      },
    ],
    svg_source_hash: "hash",
    updated_at: "2026-07-20T00:00:00.000Z",
    ...overrides,
  };
}

describe("acmPanel uiReadModel", () => {
  it("no instance → Neaplicabil", () => {
    const model = buildAcmPanelUiReadModel({ finishSetup: {}, payload: {} });
    expect(model.exists).toBe(false);
    expect(model.primaryStatus.label).toBe("Neaplicabil");
  });

  it("catalog defaults are never Confirmat de operator", () => {
    expect(authorityToOperator("catalog_default").label).toBe("Propunere din catalog");
    expect(lifecycleToOperator("proposed").label).toBe("Propus");
    const model = buildAcmPanelUiReadModel({
      finishSetup: {
        acm_panel_instance: baseInstance(),
        segmented_background: { status: "PROPOSED", panels: [{}, {}] },
      },
      payload: {
        product_composition_recommendation: {
          status: "ready",
          composition_items: [
            { component_role: "volumetric_letters" },
            { component_role: "support_panel", template_code: ACM_PANEL_TEMPLATE_CODE },
          ],
        },
        product_composition_confirmed: { confirmed: false },
      },
    });
    expect(model.fieldAuthority.fold_count).toBe("catalog_default");
    expect(authorityToOperator(model.fieldAuthority.fold_count).label).toBe(
      "Propunere din catalog",
    );
    expect(model.compositionHonesty.productBadgeLabel).toBe("Compoziție propusă");
    expect(model.compositionHonesty.showConfirmCta).toBe(true);
    expect(model.issues.some((i) => i.id.startsWith("auth-"))).toBe(true);
  });

  it("product Confirmed + instance composition unconfirmed → inconsistency, not Confirmată", () => {
    const model = buildAcmPanelUiReadModel({
      finishSetup: { acm_panel_instance: baseInstance({ composition_status: "unconfirmed" }) },
      payload: {
        product_composition_recommendation: {
          composition_items: [
            { component_role: "support_panel", template_code: ACM_PANEL_TEMPLATE_CODE },
          ],
        },
        product_composition_confirmed: { confirmed: true },
      },
    });
    expect(model.compositionHonesty.productBadgeLabel).toBe("Inconsistență stare");
    expect(model.compositionHonesty.productBadgeTone).toBe("blocker");
    expect(model.compositionHonesty.inconsistency).toBe(true);
  });

  it("composition confirmed correctly when instance composition confirmed", () => {
    const model = buildAcmPanelUiReadModel({
      finishSetup: { acm_panel_instance: baseInstance({ composition_status: "confirmed" }) },
      payload: {
        product_composition_recommendation: {
          composition_items: [
            { component_role: "support_panel", template_code: ACM_PANEL_TEMPLATE_CODE },
          ],
        },
        product_composition_confirmed: { confirmed: true },
      },
    });
    expect(model.compositionHonesty.productBadgeLabel).toBe("Confirmată de operator");
    expect(model.compositionHonesty.inconsistency).toBe(false);
  });

  it("coalesces mounting nest when top-level missing", () => {
    const model = buildAcmPanelUiReadModel({
      finishSetup: {
        mounting_solution: {
          template_code: ACM_PANEL_TEMPLATE_CODE,
          configuration: { acm_panel_instance: baseInstance() },
        },
      },
      payload: {},
    });
    expect(model.exists).toBe(true);
    expect(model.source).toBe("mounting_solution.configuration.acm_panel_instance");
    expect(model.inconsistentProjection).toBe(true);
  });

  it("technical confirmed without critical authorities is not technicalReady", () => {
    const model = buildAcmPanelUiReadModel({
      finishSetup: {
        acm_panel_instance: baseInstance({
          technical_configuration_status: "confirmed",
        }),
        segmented_background: { status: "CONFIRMED", panels: [] },
      },
      payload: {},
    });
    expect(model.criticalFieldsOperatorConfirmed).toBe(false);
    expect(model.technicalReady).toBe(false);
  });

  it("separates geometry vs mounting relations", () => {
    const model = buildAcmPanelUiReadModel({
      finishSetup: {
        acm_panel_instance: baseInstance({
          relations: [
            {
              relation_id: "g1",
              from_component_ref: "a",
              to_component_ref: "b",
              relation_type: "positioned_on",
              status: "unknown",
              provenance: "geo",
            },
            {
              relation_id: "m1",
              from_component_ref: "a",
              to_component_ref: "wall",
              relation_type: "mounts_on",
              status: "proposed",
              provenance: "op",
            },
          ],
        }),
      },
      payload: {},
    });
    expect(model.geometryRelations).toHaveLength(1);
    expect(model.mountingRelations).toHaveLength(1);
  });
});
