import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6AcmShellFinishPanel from "./IntakeV6AcmShellFinishPanel";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "@/lib/intakeV6/acmPanel/types";
import {
  ACM_SHEET_ISSUE_ENVIRONMENT_MISSING,
  ACM_SHEET_ISSUE_MIRROR_EXTERIOR_SKU,
  ACM_SHEET_ISSUE_VARIANT_MISSING,
  type AcmSheetMaterialContract,
} from "@/lib/intakeV6/acmPanel/acmSheetMaterial";

function finishWithSheet(sheetMaterial?: Record<string, unknown>) {
  return {
    acm_panel_instance: {
      schema: ACM_PANEL_INSTANCE_SCHEMA,
      component_instance_id: "acm_sheet_ui",
      component_template_code: ACM_PANEL_TEMPLATE_CODE,
      intake_geometry_role_adapter: "SUPPORT_CONTOUR" as const,
      role_status: "confirmed" as const,
      association_status: "confirmed" as const,
      technical_configuration_status: "confirmed" as const,
      composition_status: "confirmed" as const,
      capabilities: { active: [], inactive: [] },
      geometry: {
        contour_id: "c",
        element_id: "e",
        geometry_hash: "h",
        width_mm: 2000,
        height_mm: 500,
        area_mm2: 1,
        perimeter_mm: 1,
        panels: [],
        joints: [],
      },
      configuration: {
        acm_thickness_mm: 3,
        fold_count: 2 as const,
        l1_mm: 50,
        l2_mm: 25,
        finished_depth_mm: 50,
        internal_frame_enabled: false,
        service_corner: null,
        field_authority: {},
        field_class: {},
      },
      relations: [],
      svg_source_hash: "x",
      updated_at: "2026-08-03T00:00:00.000Z",
      ...(sheetMaterial ? { sheet_material: sheetMaterial } : {}),
    },
  };
}

function lastSheetPatch(onApply: ReturnType<typeof vi.fn>): AcmSheetMaterialContract {
  const patch = onApply.mock.calls.at(-1)?.[0] as {
    acm_panel_instance?: { sheet_material?: AcmSheetMaterialContract };
  };
  return patch?.acm_panel_instance?.sheet_material as AcmSheetMaterialContract;
}

describe("Intake V6 ACM sheet material capture", () => {
  it("shows both selects and the missing-selection issues on an unconfigured panel", () => {
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithSheet()}
        onApplyFinishPatch={vi.fn()}
      />,
    );

    expect(screen.getByTestId("intake-v6-acm-sheet-variant")).toHaveValue("");
    expect(screen.getByTestId("intake-v6-acm-sheet-environment")).toHaveValue("");
    expect(screen.queryByTestId("intake-v6-acm-sheet-exterior-sku")).toBeNull();
    const issues = screen.getByTestId("intake-v6-acm-sheet-issues");
    expect(issues).toHaveTextContent(ACM_SHEET_ISSUE_VARIANT_MISSING);
    expect(issues).toHaveTextContent(ACM_SHEET_ISSUE_ENVIRONMENT_MISSING);
  });

  it("hydrates a persisted contract and shows no issue when complete", () => {
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithSheet({ variant: "colorat", environment: "exterior" })}
        onApplyFinishPatch={vi.fn()}
      />,
    );

    expect(screen.getByTestId("intake-v6-acm-sheet-variant")).toHaveValue("colorat");
    expect(screen.getByTestId("intake-v6-acm-sheet-environment")).toHaveValue("exterior");
    expect(screen.queryByTestId("intake-v6-acm-sheet-issues")).toBeNull();
  });

  it("persists the selected variant through a finish patch", () => {
    const onApply = vi.fn();
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithSheet()}
        onApplyFinishPatch={onApply}
      />,
    );

    fireEvent.change(screen.getByTestId("intake-v6-acm-sheet-variant"), {
      target: { value: "oglinda_gold" },
    });

    expect(onApply).toHaveBeenCalled();
    expect(lastSheetPatch(onApply).variant).toBe("oglinda_gold");
    expect(lastSheetPatch(onApply).operator_confirmed).toBe(false);
  });

  it("reveals the supplier SKU input only for mirror on exterior and warns until it is filled", () => {
    const onApply = vi.fn();
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithSheet({ variant: "oglinda_antracit", environment: "interior" })}
        onApplyFinishPatch={onApply}
      />,
    );

    expect(screen.queryByTestId("intake-v6-acm-sheet-exterior-sku")).toBeNull();

    fireEvent.change(screen.getByTestId("intake-v6-acm-sheet-environment"), {
      target: { value: "exterior" },
    });

    expect(screen.getByTestId("intake-v6-acm-sheet-exterior-sku")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-acm-sheet-issues")).toHaveTextContent(
      ACM_SHEET_ISSUE_MIRROR_EXTERIOR_SKU,
    );

    fireEvent.change(screen.getByTestId("intake-v6-acm-sheet-exterior-sku"), {
      target: { value: "SKU-EXT-42" },
    });

    expect(lastSheetPatch(onApply).exterior_sku).toBe("SKU-EXT-42");
    expect(screen.queryByTestId("intake-v6-acm-sheet-issues")).toBeNull();
  });

  it("clears a stale exterior SKU when the operator leaves the mirror variant", () => {
    const onApply = vi.fn();
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithSheet({
          variant: "oglinda_gold",
          environment: "exterior",
          exterior_sku: "SKU-EXT-42",
        })}
        onApplyFinishPatch={onApply}
      />,
    );

    expect(screen.getByTestId("intake-v6-acm-sheet-exterior-sku")).toHaveValue("SKU-EXT-42");

    fireEvent.change(screen.getByTestId("intake-v6-acm-sheet-variant"), {
      target: { value: "standard" },
    });

    expect(lastSheetPatch(onApply).variant).toBe("standard");
    expect(lastSheetPatch(onApply).exterior_sku).toBeNull();
    expect(screen.queryByTestId("intake-v6-acm-sheet-exterior-sku")).toBeNull();
  });

  it("clears a stale exterior SKU when the operator switches to interior", () => {
    const onApply = vi.fn();
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithSheet({
          variant: "oglinda_gold",
          environment: "exterior",
          exterior_sku: "SKU-EXT-42",
        })}
        onApplyFinishPatch={onApply}
      />,
    );

    fireEvent.change(screen.getByTestId("intake-v6-acm-sheet-environment"), {
      target: { value: "interior" },
    });

    expect(lastSheetPatch(onApply).environment).toBe("interior");
    expect(lastSheetPatch(onApply).exterior_sku).toBeNull();
    expect(screen.queryByTestId("intake-v6-acm-sheet-exterior-sku")).toBeNull();
  });

  it("keeps the material capture free of prices", () => {
    const { container } = render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithSheet({ variant: "oglinda_gold", environment: "exterior" })}
        onApplyFinishPatch={vi.fn()}
      />,
    );

    expect(container.textContent ?? "").not.toMatch(/EUR|RON|€|lei|preț|pret/i);
  });
});
