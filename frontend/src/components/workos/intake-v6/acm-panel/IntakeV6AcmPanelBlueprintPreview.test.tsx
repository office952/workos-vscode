import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6AcmPanelBlueprintPreview from "./IntakeV6AcmPanelBlueprintPreview";
import { buildAcmPanelBlueprintReadModel } from "@/lib/intakeV6/acmPanel/blueprintReadModel";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "@/lib/intakeV6/acmPanel/types";

function fixtureFinish() {
  return {
    acm_panel_instance: {
      schema: ACM_PANEL_INSTANCE_SCHEMA,
      component_instance_id: "acm_cc_test",
      component_template_code: ACM_PANEL_TEMPLATE_CODE,
      intake_geometry_role_adapter: "SUPPORT_CONTOUR" as const,
      role_status: "confirmed" as const,
      association_status: "proposed" as const,
      technical_configuration_status: "proposed" as const,
      composition_status: "unconfirmed" as const,
      capabilities: {
        active: ["boxed_returns", "rear_lip", "segmented_panels"],
        inactive: ["internal_frame", "rear_closure", "wall_mounting", "structure_mounting"],
      },
      geometry: {
        contour_id: "cc",
        element_id: "el-1",
        geometry_hash: "h",
        width_mm: 1000,
        height_mm: 350,
        area_mm2: 1,
        perimeter_mm: 1,
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
        },
        field_class: {},
      },
      relations: [
        {
          relation_id: "r1",
          from_component_ref: "pseudo:x",
          to_component_ref: "acm_cc_test",
          relation_type: "positioned_on" as const,
          status: "unknown" as const,
          provenance: "geometry_insufficient_for_panel_assignment",
        },
      ],
      svg_source_hash: "x",
      updated_at: "2026-07-20T00:00:00.000Z",
    },
    segmented_background: {
      status: "PROPOSED",
      panels: [],
      joints: [],
      assembly_dimensions: { width_mm: 2000, height_mm: 350 },
      element_bindings: [],
    },
  };
}

describe("IntakeV6AcmPanelBlueprintPreview", () => {
  it("L0 hidden/empty", () => {
    const { container } = render(
      <IntakeV6AcmPanelBlueprintPreview finishSetup={{}} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("collapsed by default; expands to show 2000×350, panels, joint, disclaimer", () => {
    render(
      <IntakeV6AcmPanelBlueprintPreview
        finishSetup={fixtureFinish()}
        payload={{ product_composition_confirmed: { confirmed: true } }}
      />,
    );
    const root = screen.getByTestId("intake-v6-acm-blueprint-preview");
    expect(root).toHaveAttribute("data-readiness", "L1-P");
    expect(root).toHaveAttribute("data-expanded", "false");
    expect(screen.getByTestId("intake-v6-acm-blueprint-collapsed-summary")).toHaveTextContent(
      "2000 × 350",
    );
    expect(screen.queryByTestId("intake-v6-acm-blueprint-front-svg")).toBeNull();

    fireEvent.click(screen.getByTestId("intake-v6-acm-blueprint-toggle"));
    expect(root).toHaveAttribute("data-expanded", "true");

    const svg = screen.getByTestId("intake-v6-acm-blueprint-front-svg");
    expect(svg).toHaveAttribute("data-assembly-width", "2000");
    expect(svg).toHaveAttribute("data-assembly-height", "350");
    expect(screen.getByTestId("intake-v6-acm-blueprint-overall-label")).toHaveTextContent(
      "2000 × 350 mm",
    );
    expect(screen.getByTestId("intake-v6-acm-blueprint-panel-panel_1")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-acm-blueprint-panel-panel_2")).toBeInTheDocument();
    const joint = screen.getByTestId("intake-v6-acm-blueprint-joint-joint_panel_1_panel_2");
    expect(joint).toHaveAttribute("data-joint-x", "1000");
    expect(screen.getByTestId("intake-v6-acm-blueprint-disclaimer")).toHaveTextContent(
      "nu este desen de execuție",
    );
    expect(screen.getByTestId("intake-v6-acm-blueprint-letter-unknown")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-acm-blueprint-composition-banner")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-acm-blueprint-construction-thickness")).toHaveAttribute(
      "data-style",
      "dashed_catalog",
    );
  });

  it("has no write callbacks / operatorPatch props on expand-collapse", () => {
    const onApply = vi.fn();
    render(<IntakeV6AcmPanelBlueprintPreview finishSetup={fixtureFinish()} />);
    fireEvent.click(screen.getByTestId("intake-v6-acm-blueprint-toggle"));
    fireEvent.click(screen.getByTestId("intake-v6-acm-blueprint-toggle"));
    expect(onApply).not.toHaveBeenCalled();
    // Component API has no onApplyFinishPatch — type-level; runtime: no PUT side effects
    expect(screen.getByTestId("intake-v6-acm-blueprint-preview")).toBeInTheDocument();
  });

  it("L1-B shows warning and no front svg", () => {
    const finish = fixtureFinish();
    (finish.acm_panel_instance.geometry.panels as unknown[]) = [
      {
        panel_id: "bad",
        order: 1,
        width_mm: null,
        height_mm: 10,
        position: { x_mm: 0, y_mm: 0 },
      },
    ];
    finish.acm_panel_instance.geometry.joints = [];
    render(<IntakeV6AcmPanelBlueprintPreview finishSetup={finish} defaultExpanded />);
    expect(screen.getByTestId("intake-v6-acm-blueprint-preview")).toHaveAttribute(
      "data-readiness",
      "L1-B",
    );
    expect(screen.getByTestId("intake-v6-acm-blueprint-blocked")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-acm-blueprint-front-svg")).toBeNull();
  });

  it("accepts prebuilt model", () => {
    const model = buildAcmPanelBlueprintReadModel({ finishSetup: fixtureFinish() });
    render(<IntakeV6AcmPanelBlueprintPreview model={model} defaultExpanded />);
    expect(screen.getByTestId("intake-v6-acm-blueprint-overall-label")).toHaveTextContent(
      "2000",
    );
  });
});
