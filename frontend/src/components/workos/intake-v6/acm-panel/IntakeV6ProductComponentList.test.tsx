import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ProductComponentList, {
  buildProductComponentListItems,
} from "./IntakeV6ProductComponentList";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "@/lib/intakeV6/acmPanel/types";

describe("IntakeV6ProductComponentList", () => {
  it("builds sibling rows and selects AcmPanel without writing payload", () => {
    const finishSetup = {
      acm_panel_instance: {
        schema: ACM_PANEL_INSTANCE_SCHEMA,
        component_instance_id: "acm_1",
        component_template_code: ACM_PANEL_TEMPLATE_CODE,
        intake_geometry_role_adapter: "SUPPORT_CONTOUR",
        role_status: "confirmed",
        association_status: "proposed",
        technical_configuration_status: "proposed",
        composition_status: "unconfirmed",
        capabilities: { active: [], inactive: [] },
        geometry: {
          contour_id: "c",
          element_id: "e",
          geometry_hash: "h",
          width_mm: 1000,
          height_mm: 350,
          area_mm2: 1,
          perimeter_mm: 1,
          panels: [{ panel_id: "p1", order: 1, width_mm: 1000, height_mm: 350, position: { x_mm: 0, y_mm: 0 } }],
        },
        configuration: {
          acm_thickness_mm: 3,
          fold_count: 2,
          l1_mm: 60,
          l2_mm: 25,
          finished_depth_mm: 60,
          internal_frame_enabled: false,
          service_corner: null,
          field_authority: { fold_count: "catalog_default" },
          field_class: {},
        },
        relations: [],
        svg_source_hash: null,
        updated_at: "2026-07-20T00:00:00.000Z",
      },
    };
    const items = buildProductComponentListItems({
      payload: {},
      finishSetup,
      hasLetters: true,
      hasLogo: false,
    });
    expect(items.map((i) => i.id)).toEqual(["letters", "acm_panel"]);
    expect(items.find((i) => i.id === "acm_panel")?.title).toBe("Panou Alucobond casetat");

    const onSelect = vi.fn();
    render(
      <IntakeV6ProductComponentList items={items} selectedId={null} onSelect={onSelect} />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-product-component-row-acm_panel"));
    expect(onSelect).toHaveBeenCalledWith("acm_panel");
  });
});
