import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6AcmShellFinishPanel from "./IntakeV6AcmShellFinishPanel";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "@/lib/intakeV6/acmPanel/types";

function finishWithShell(shell?: Record<string, unknown>) {
  return {
    acm_panel_instance: {
      schema: ACM_PANEL_INSTANCE_SCHEMA,
      component_instance_id: "acm_shell_ui",
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
      updated_at: "2026-07-24T00:00:00.000Z",
      ...(shell ? { shell_finish: shell } : {}),
    },
  };
}

describe("IntakeV6AcmShellFinishPanel simplified operator UI", () => {
  it("shows apply mode + față/cant checkboxes; hides workshop fields by default", () => {
    const onApply = vi.fn();
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithShell({
          face: { kind: "oracal_651", color_code: "021", roll_width_mm: 1000 },
          volume: { kind: "oracal_651", color_code: "", roll_width_mm: 1000 },
          foil_strategy: {
            mode: "face_multi_piece",
            piece_count: 2,
            client_informed: true,
          },
        })}
        onApplyFinishPatch={onApply}
      />,
    );

    expect(screen.getByTestId("intake-v6-acm-shell-apply-mode")).toHaveValue("after_frame");
    expect(screen.getByTestId("intake-v6-acm-shell-apply-face")).toBeChecked();
    expect(screen.getByTestId("intake-v6-acm-shell-apply-volume")).toBeChecked();
    expect(screen.queryByText(/Nu 641\/8500\/RAL/i)).toBeNull();
    expect(screen.queryByTestId("intake-v6-acm-shell-oracal-code")).toBeNull();
    expect(screen.queryByTestId("intake-v6-acm-shell-foil-strategy")).toBeNull();
    expect(screen.getByTestId("intake-v6-acm-shell-atelier-details")).not.toHaveAttribute(
      "open",
    );
    expect(screen.getByTestId("intake-v6-acm-shell-finish-summary")).toHaveTextContent(
      /Colant față \+ cant · după cadru/i,
    );
  });

  it("unchecking both zones switches to fără colant", () => {
    const onApply = vi.fn();
    render(
      <IntakeV6AcmShellFinishPanel
        finishSetup={finishWithShell({
          face: { kind: "oracal_651", color_code: "", roll_width_mm: 1000 },
          volume: { kind: "stock_plate" },
        })}
        onApplyFinishPatch={onApply}
      />,
    );

    fireEvent.click(screen.getByTestId("intake-v6-acm-shell-apply-face"));
    expect(onApply).toHaveBeenCalled();
    const patch = onApply.mock.calls.at(-1)?.[0] as {
      acm_panel_instance?: { shell_finish?: { face?: { kind?: string } } };
    };
    expect(patch?.acm_panel_instance?.shell_finish?.face?.kind).toBe("stock_plate");
  });
});
