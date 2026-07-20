import { describe, expect, it } from "vitest";
import {
  ASSEMBLY_DIMENSION_TOLERANCE_MM,
  buildAcmPanelBlueprintReadModel,
} from "./blueprintReadModel";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "./types";

function baseInstance(overrides: Record<string, unknown> = {}) {
  return {
    schema: ACM_PANEL_INSTANCE_SCHEMA,
    component_instance_id: "acm_cc_7af1352f_ff5c35da170d",
    component_template_code: ACM_PANEL_TEMPLATE_CODE,
    intake_geometry_role_adapter: "SUPPORT_CONTOUR" as const,
    role_status: "confirmed" as const,
    association_status: "proposed" as const,
    technical_configuration_status: "proposed" as const,
    composition_status: "unconfirmed" as const,
    capabilities: {
      active: ["boxed_returns", "rear_lip", "segmented_panels"],
      inactive: [
        "internal_frame",
        "rear_closure",
        "wall_mounting",
        "structure_mounting",
        "totem_face",
        "led_system",
      ],
    },
    geometry: {
      contour_id: "cc_7af1352f",
      element_id: "el-1",
      geometry_hash: "7af1352f",
      width_mm: 1000,
      height_mm: 350,
      area_mm2: 350000,
      perimeter_mm: 2700,
      bbox: { x: 0.01, y: 0.01, width: 66, height: 23 },
      panels: [
        {
          panel_id: "panel_1",
          order: 1,
          width_mm: 1000,
          height_mm: 350,
          position: { x_mm: 0, y_mm: 0 },
          contour_element_id: "el-1",
        },
        {
          panel_id: "panel_2",
          order: 2,
          width_mm: 1000,
          height_mm: 350,
          position: { x_mm: 1000, y_mm: 0 },
          contour_element_id: "el-2",
        },
      ],
      joints: [
        {
          joint_id: "joint_panel_1_panel_2",
          left_panel_id: "panel_1",
          right_panel_id: "panel_2",
          orientation: "VERTICAL",
        },
      ],
    },
    configuration: {
      acm_thickness_mm: 3,
      fold_count: 2 as const,
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
        service_corner: "catalog_default",
      },
      field_class: {},
    },
    relations: [
      {
        relation_id: "rel_belongs_panel_1_0",
        from_component_ref: "panel_1",
        to_component_ref: "acm_cc_7af1352f_ff5c35da170d",
        relation_type: "belongs_to_assembly" as const,
        status: "proposed" as const,
        provenance: "segmented_panels_proposal",
      },
      {
        relation_id: "rel_place_pseudo:fill-e31e24",
        from_component_ref: "pseudo:fill-e31e24",
        to_component_ref: "acm_cc_7af1352f_ff5c35da170d",
        relation_type: "positioned_on" as const,
        status: "unknown" as const,
        provenance: "geometry_insufficient_for_panel_assignment",
      },
    ],
    svg_source_hash: "ff5c35da",
    updated_at: "2026-07-20T01:23:44.785Z",
    ...overrides,
  };
}

function fixtureFinish(extra: Record<string, unknown> = {}) {
  return {
    acm_panel_instance: baseInstance(),
    segmented_background: {
      schema: "acm_segmented_background_v1",
      status: "PROPOSED",
      panels: baseInstance().geometry.panels,
      joints: baseInstance().geometry.joints,
      assembly_dimensions: { width_mm: 2000, height_mm: 350 },
      element_bindings: [],
    },
    ...extra,
  };
}

describe("buildAcmPanelBlueprintReadModel", () => {
  it("multi-panel 1000+1000 → assembly 2000×350 (not envelope 1000)", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.readiness).toBe("L1-P");
    expect(model.assembly?.width_mm).toBe(2000);
    expect(model.assembly?.height_mm).toBe(350);
    expect(model.assembly?.width_mm).not.toBe(1000);
    expect(model.panels).toHaveLength(2);
  });

  it("envelope 1000 does not override assembly 2000", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.assembly?.width_mm).toBe(2000);
    expect(
      model.warnings.some((w) => w.toLowerCase().includes("envelope")),
    ).toBe(true);
  });

  it("panel bounds with offset normalize to top-left origin", () => {
    const inst = baseInstance({
      geometry: {
        ...baseInstance().geometry,
        panels: [
          {
            panel_id: "a",
            order: 1,
            width_mm: 500,
            height_mm: 200,
            position: { x_mm: 100, y_mm: 50 },
          },
          {
            panel_id: "b",
            order: 2,
            width_mm: 500,
            height_mm: 200,
            position: { x_mm: 600, y_mm: 50 },
          },
        ],
        joints: [
          {
            joint_id: "j",
            left_panel_id: "a",
            right_panel_id: "b",
            orientation: "VERTICAL",
          },
        ],
      },
    });
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: {
        acm_panel_instance: inst,
        segmented_background: {
          status: "PROPOSED",
          panels: inst.geometry.panels,
          joints: inst.geometry.joints,
          assembly_dimensions: { width_mm: 1000, height_mm: 200 },
          element_bindings: [],
        },
      },
    });
    expect(model.assembly?.width_mm).toBe(1000);
    expect(model.panels[0]?.x_mm).toBe(0);
    expect(model.panels[0]?.y_mm).toBe(0);
    expect(model.panels[1]?.x_mm).toBe(500);
  });

  it("derives vertical joint at x=1000 without inventing gap", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.joints).toHaveLength(1);
    expect(model.joints[0]?.orientation).toBe("VERTICAL");
    expect(model.joints[0]?.x1_mm).toBe(1000);
    expect(model.joints[0]?.x2_mm).toBe(1000);
    expect(model.joints[0]?.note).toBe("Rost schematic derivat");
    expect(model.joints[0]?.statusLabel).toBe("Propus");
    expect(model.callouts.every((c) => !c.label.toLowerCase().includes("gap"))).toBe(
      true,
    );
  });

  it("derives horizontal joint when orientation is HORIZONTAL", () => {
    const inst = baseInstance({
      geometry: {
        ...baseInstance().geometry,
        width_mm: 1000,
        height_mm: 700,
        panels: [
          {
            panel_id: "top",
            order: 1,
            width_mm: 1000,
            height_mm: 350,
            position: { x_mm: 0, y_mm: 0 },
          },
          {
            panel_id: "bot",
            order: 2,
            width_mm: 1000,
            height_mm: 350,
            position: { x_mm: 0, y_mm: 350 },
          },
        ],
        joints: [
          {
            joint_id: "jh",
            left_panel_id: "top",
            right_panel_id: "bot",
            orientation: "HORIZONTAL",
          },
        ],
      },
    });
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: {
        acm_panel_instance: inst,
        segmented_background: {
          status: "PROPOSED",
          panels: inst.geometry.panels,
          joints: inst.geometry.joints,
          element_bindings: [],
        },
      },
    });
    expect(model.joints[0]?.orientation).toBe("HORIZONTAL");
    expect(model.joints[0]?.y1_mm).toBe(350);
    expect(model.assembly?.height_mm).toBe(700);
  });

  it("catalog defaults → L1-P with dashed catalog construction callouts", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.readiness).toBe("L1-P");
    const thickness = model.callouts.find((c) => c.id === "construction_acm_thickness_mm");
    expect(thickness?.authority).toBe("catalog_default");
    expect(thickness?.style).toBe("dashed_catalog");
    expect(thickness?.finality).toBe("provisional");
    expect(thickness?.finality).not.toBe("final");
  });

  it("unknown letter relation omitted from placement; note present", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.letterPlacementUnknown).toBe(true);
    const place = model.relations.find((r) => r.relation_type === "positioned_on");
    expect(place?.display).toBe("note_only");
    expect(place?.note).toMatch(/necunoscut/i);
  });

  it("association proposed → no L1-C", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.readiness).not.toBe("L1-C");
  });

  it("segmented PROPOSED → no L1-C", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.provenance.segmentedStatus).toBe("PROPOSED");
    expect(model.readiness).toBe("L1-P");
  });

  it("composition inconsistent → no L1-C + warning", () => {
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: fixtureFinish(),
      payload: {
        product_composition_confirmed: { confirmed: true },
      },
    });
    expect(model.compositionInconsistency).toBe(true);
    expect(model.readiness).not.toBe("L1-C");
    expect(model.warnings.length).toBeGreaterThan(0);
  });

  it("no instance → L0", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: {} });
    expect(model.readiness).toBe("L0");
    expect(model.assembly).toBeNull();
  });

  it("contradictory panel geometry → L1-B", () => {
    const inst = baseInstance({
      geometry: {
        ...baseInstance().geometry,
        panels: [
          {
            panel_id: "bad",
            order: 1,
            width_mm: null,
            height_mm: 350,
            position: { x_mm: 0, y_mm: 0 },
          },
        ],
        joints: [],
      },
    });
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: { acm_panel_instance: inst },
    });
    expect(model.readiness).toBe("L1-B");
    expect(model.blockers.length).toBeGreaterThan(0);
  });

  it("single panel uses panel dimensions", () => {
    const inst = baseInstance({
      geometry: {
        ...baseInstance().geometry,
        width_mm: 800,
        height_mm: 400,
        panels: [
          {
            panel_id: "only",
            order: 1,
            width_mm: 800,
            height_mm: 400,
            position: { x_mm: 0, y_mm: 0 },
          },
        ],
        joints: [],
      },
    });
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: {
        acm_panel_instance: inst,
        segmented_background: { status: "SINGLE_PANEL", panels: [], joints: [], element_bindings: [] },
      },
    });
    expect(model.readiness).toBe("L1-P");
    expect(model.assembly?.width_mm).toBe(800);
    expect(model.panels).toHaveLength(1);
    expect(model.joints).toHaveLength(0);
  });

  it("does not treat SVG bbox as mm", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.assembly?.width_mm).toBe(2000);
    expect(model.assembly?.width_mm).not.toBe(66);
    expect(model.assembly?.unit).toBe("mm");
  });

  it("assembly_dimensions mismatch uses panel extent + warning", () => {
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: fixtureFinish({
        segmented_background: {
          status: "PROPOSED",
          panels: baseInstance().geometry.panels,
          joints: baseInstance().geometry.joints,
          assembly_dimensions: { width_mm: 1900, height_mm: 350 },
          element_bindings: [],
        },
      }),
    });
    expect(model.assembly?.width_mm).toBe(2000);
    expect(model.assembly?.source).toBe("panel_extent");
    expect(model.warnings.some((w) => w.includes("assembly_dimensions"))).toBe(true);
  });

  it("fold 1 + l2 present → honesty warning; l2 omitted from present construction", () => {
    const inst = baseInstance({
      configuration: {
        ...baseInstance().configuration,
        fold_count: 1,
        l2_mm: 25,
      },
    });
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: {
        acm_panel_instance: {
          ...inst,
          geometry: {
            ...inst.geometry,
            panels: [inst.geometry.panels![0]],
            joints: [],
          },
        },
      },
    });
    expect(model.constructionSection?.warnings.some((w) => w.includes("fold_count=1"))).toBe(
      true,
    );
    expect(model.constructionSection?.l2.present).toBe(false);
  });

  it("inactive rear/frame/mount omitted", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    expect(model.constructionSection?.rearClosure.present).toBe(false);
    expect(model.constructionSection?.internalFrame.present).toBe(false);
    expect(model.constructionSection?.mountingPlane.present).toBe(false);
  });

  it("tolerance constant is 1mm", () => {
    expect(ASSEMBLY_DIMENSION_TOLERANCE_MM).toBe(1);
  });

  it("L1-C only when all gates pass (synthetic)", () => {
    const inst = baseInstance({
      association_status: "confirmed",
      technical_configuration_status: "confirmed",
      composition_status: "confirmed",
      configuration: {
        ...baseInstance().configuration,
        field_authority: {
          panel_geometry: "operator_confirmed",
          fold_count: "operator_confirmed",
          l1_mm: "operator_confirmed",
          l2_mm: "operator_confirmed",
          finished_depth_mm: "operator_confirmed",
          acm_thickness_mm: "operator_confirmed",
          internal_frame: "operator_confirmed",
          service_corner: "operator_confirmed",
        },
      },
      geometry: {
        ...baseInstance().geometry,
        panels: [
          {
            panel_id: "only",
            order: 1,
            width_mm: 1000,
            height_mm: 350,
            position: { x_mm: 0, y_mm: 0 },
          },
        ],
        joints: [],
      },
      relations: [],
    });
    const model = buildAcmPanelBlueprintReadModel({
      finishSetup: {
        acm_panel_instance: inst,
        segmented_background: {
          status: "SINGLE_PANEL",
          panels: [],
          joints: [],
          element_bindings: [],
        },
      },
      payload: { product_composition_confirmed: { confirmed: true } },
    });
    expect(model.readiness).toBe("L1-C");
  });
});
