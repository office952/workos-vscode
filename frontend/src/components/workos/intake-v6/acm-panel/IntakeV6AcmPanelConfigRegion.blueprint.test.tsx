import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import IntakeV6AcmPanelConfigRegion from "./IntakeV6AcmPanelConfigRegion";
import { AcmPanelDraftFlushProvider } from "./AcmPanelDraftFlushContext";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "@/lib/intakeV6/acmPanel/types";

vi.mock("../IntakeV6SegmentedBackgroundPanel", () => ({
  default: () => <div data-testid="segmented-mock" />,
}));

function acmFinish() {
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
        inactive: ["internal_frame", "rear_closure", "wall_mounting"],
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
      relations: [],
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
    mounting_solution: {
      kind: "product_system_template",
      template_code: ACM_PANEL_TEMPLATE_CODE,
      configuration: {},
    },
  };
}

describe("IntakeV6AcmPanelConfigRegion blueprint slot", () => {
  it("shows sticky blueprint when AcmPanel selected; hidden for letters-only selection without acm", () => {
    const onApply = vi.fn();
    render(
      <AcmPanelDraftFlushProvider>
        <IntakeV6AcmPanelConfigRegion
          payload={{
            product_composition_recommendation: {
              composition_items: [
                { component_role: "support_panel", template_code: ACM_PANEL_TEMPLATE_CODE },
              ],
            },
          }}
          finishSetup={acmFinish()}
          hasLetters
          hasLogo={false}
          selectedId="acm_panel"
          onSelect={vi.fn()}
          onApplyFinishPatch={onApply}
          onNavigateLetters={vi.fn()}
          onNavigateLogo={vi.fn()}
        />
      </AcmPanelDraftFlushProvider>,
    );
    expect(screen.getByTestId("intake-v6-acm-blueprint-preview")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-acm-blueprint-preview")).toHaveAttribute(
      "data-expanded",
      "false",
    );
    expect(onApply).not.toHaveBeenCalled();
  });

  it("letters-only list does not invent blueprint without instance", () => {
    render(
      <AcmPanelDraftFlushProvider>
        <IntakeV6AcmPanelConfigRegion
          payload={{}}
          finishSetup={{}}
          hasLetters
          hasLogo={false}
          selectedId="letters"
          onSelect={vi.fn()}
          onApplyFinishPatch={vi.fn()}
          onNavigateLetters={vi.fn()}
          onNavigateLogo={vi.fn()}
        />
      </AcmPanelDraftFlushProvider>,
    );
    expect(screen.queryByTestId("intake-v6-acm-blueprint-preview")).toBeNull();
  });

  it("workbench variant renders flat inspector without component list chrome", () => {
    const onSelect = vi.fn();
    render(
      <AcmPanelDraftFlushProvider>
        <IntakeV6AcmPanelConfigRegion
          variant="workbench"
          payload={{
            product_composition_recommendation: {
              composition_items: [
                { component_role: "support_panel", template_code: ACM_PANEL_TEMPLATE_CODE },
              ],
            },
          }}
          finishSetup={acmFinish()}
          hasLetters={false}
          hasLogo={false}
          selectedId={null}
          onSelect={onSelect}
          onApplyFinishPatch={vi.fn()}
          onNavigateLetters={vi.fn()}
          onNavigateLogo={vi.fn()}
        />
      </AcmPanelDraftFlushProvider>,
    );

    expect(screen.getByTestId("intake-v6-acm-panel-config-region")).toHaveAttribute(
      "data-acm-layout",
      "workbench",
    );
    expect(screen.getByTestId("intake-v6-acm-panel-inspector")).toHaveAttribute(
      "data-presentation",
      "flat",
    );
    expect(screen.getByTestId("intake-v6-acm-section-geometry")).toHaveAttribute(
      "data-presentation",
      "flat",
    );
    expect(screen.getByTestId("intake-v6-acm-field-fold_count")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-product-component-list")).toBeNull();
    expect(onSelect).toHaveBeenCalledWith("acm_panel");
  });

  it("workbench merges blueprint + validation into one tech strip without badges", () => {
    render(
      <AcmPanelDraftFlushProvider>
        <IntakeV6AcmPanelConfigRegion
          variant="workbench"
          payload={{
            product_composition_recommendation: {
              composition_items: [
                { component_role: "support_panel", template_code: ACM_PANEL_TEMPLATE_CODE },
              ],
            },
          }}
          finishSetup={acmFinish()}
          hasLetters={false}
          hasLogo={false}
          selectedId="acm_panel"
          onSelect={vi.fn()}
          onApplyFinishPatch={vi.fn()}
          onNavigateLetters={vi.fn()}
          onNavigateLogo={vi.fn()}
        />
      </AcmPanelDraftFlushProvider>,
    );

    const strip = screen.getByTestId("intake-v6-acm-tech-status-strip");
    expect(strip).toContainElement(screen.getByTestId("intake-v6-acm-blueprint-preview"));
    expect(strip).toContainElement(screen.getByTestId("intake-v6-acm-validation-rail"));
    expect(screen.getByTestId("intake-v6-acm-blueprint-preview")).toHaveAttribute(
      "data-chrome",
      "embedded",
    );
    expect(screen.getByTestId("intake-v6-acm-validation-rail")).toHaveAttribute(
      "data-density",
      "inline",
    );
    expect(screen.queryByTestId("intake-v6-acm-blueprint-readiness-badge")).toBeNull();
    expect(screen.queryByTestId("intake-v6-acm-workbench-status")).toBeNull();
    expect(screen.queryByTestId("intake-v6-acm-authority-panel_geometry")).toBeNull();
    expect(screen.getByTestId("intake-v6-acm-panel-config-region").textContent).not.toMatch(
      /Confirmat de operator|Neaplicabil|Nivel L1/,
    );
    expect(screen.getByTestId("intake-v6-acm-confirm-panel")).toBeInTheDocument();
    // Fixture may surface issues; when present they stay inside the shared strip.
    expect(strip).toHaveTextContent(/Validare/i);
  });
});
