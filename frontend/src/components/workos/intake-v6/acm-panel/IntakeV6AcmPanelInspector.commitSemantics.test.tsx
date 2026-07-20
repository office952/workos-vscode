import { fireEvent, render, screen, act } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import IntakeV6AcmPanelInspector from "./IntakeV6AcmPanelInspector";
import type { AcmPanelUiReadModel } from "@/lib/intakeV6/acmPanel/uiReadModel";
import { ACM_PANEL_INSTANCE_SCHEMA, ACM_PANEL_TEMPLATE_CODE } from "@/lib/intakeV6/acmPanel/types";
import { ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS } from "@/lib/intakeV6/acmPanel/commitSemantics";

vi.mock("../IntakeV6SegmentedBackgroundPanel", () => ({
  default: () => <div data-testid="segmented-stub" />,
}));

function model(): AcmPanelUiReadModel {
  const instance = {
    schema: ACM_PANEL_INSTANCE_SCHEMA,
    component_instance_id: "acm_test",
    component_template_code: ACM_PANEL_TEMPLATE_CODE,
    intake_geometry_role_adapter: "SUPPORT_CONTOUR" as const,
    role_status: "confirmed" as const,
    association_status: "proposed" as const,
    technical_configuration_status: "proposed" as const,
    composition_status: "unconfirmed" as const,
    capabilities: { active: ["boxed_returns"], inactive: [] },
    geometry: {
      contour_id: "c",
      element_id: "e",
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
      fold_count: 2 as const,
      l1_mm: 60,
      l2_mm: 25,
      finished_depth_mm: 60,
      internal_frame_enabled: false,
      service_corner: null,
      field_authority: {
        panel_geometry: "detected" as const,
        fold_count: "catalog_default" as const,
        l1_mm: "catalog_default" as const,
        l2_mm: "catalog_default" as const,
        acm_thickness_mm: "catalog_default" as const,
        finished_depth_mm: "catalog_default" as const,
      },
      field_class: {},
    },
    relations: [],
    svg_source_hash: null,
    updated_at: "2026-07-20T00:00:00.000Z",
  };
  return {
    exists: true,
    instance,
    source: "finish_setup.acm_panel_instance",
    primaryStatus: { code: "blocked", label: "Blocat", tone: "danger" },
    association: { code: "proposed", label: "Propus", tone: "warning" },
    technical: { code: "proposed", label: "Propus", tone: "warning" },
    composition: { code: "unconfirmed", label: "Necesită confirmare", tone: "warning" },
    compositionHonesty: {
      code: "inconsistent",
      label: "Inconsistență stare",
      tone: "danger",
      detail: "x",
    },
    dimensionsSummary: "1000 × 350 mm",
    segmentCount: 2,
    segmentedLabel: "Propus",
    unresolvedConfirmations: [],
    activeCapabilities: ["boxed_returns"],
    geometryRelations: [],
    mountingRelations: [],
    issues: [],
    inconsistencyNotes: [],
    fieldAuthority: {
      panel_geometry: "detected",
      fold_count: "catalog_default",
      l1_mm: "catalog_default",
      l2_mm: "catalog_default",
      acm_thickness_mm: "catalog_default",
      finished_depth_mm: "catalog_default",
    },
  } as unknown as AcmPanelUiReadModel;
}

describe("IntakeV6AcmPanelInspector commit semantics", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("pending L1 + Confirm construction → exactly one apply with update+confirm", () => {
    const onApplyFinishPatch = vi.fn();
    render(
      <IntakeV6AcmPanelInspector
        model={model()}
        finishSetup={{ acm_panel_instance: model().instance }}
        actions={{ onApplyFinishPatch, onSegmentedPatch: vi.fn() }}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-acm-section-construction").querySelector("button")!);
    const l1 = screen.getByTestId("intake-v6-acm-field-l1_mm");
    fireEvent.change(l1, { target: { value: "70" } });
    fireEvent.click(screen.getByTestId("intake-v6-acm-confirm-construction"));
    expect(onApplyFinishPatch).toHaveBeenCalledTimes(1);
    const patch = onApplyFinishPatch.mock.calls[0]![0];
    expect(patch.acm_panel_instance.configuration.l1_mm).toBe(70);
    expect(patch.acm_panel_instance.configuration.field_authority.l1_mm).toBe(
      "operator_confirmed",
    );
  });

  it("two pending fields + Confirm technical → exactly one apply", () => {
    const onApplyFinishPatch = vi.fn();
    render(
      <IntakeV6AcmPanelInspector
        model={model()}
        finishSetup={{ acm_panel_instance: model().instance }}
        actions={{ onApplyFinishPatch, onSegmentedPatch: vi.fn() }}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-acm-section-construction").querySelector("button")!);
    fireEvent.change(screen.getByTestId("intake-v6-acm-field-l1_mm"), {
      target: { value: "62" },
    });
    fireEvent.change(screen.getByTestId("intake-v6-acm-field-l2_mm"), {
      target: { value: "27" },
    });
    fireEvent.click(screen.getByTestId("intake-v6-acm-confirm-technical"));
    expect(onApplyFinishPatch).toHaveBeenCalledTimes(1);
    const inst = onApplyFinishPatch.mock.calls[0]![0].acm_panel_instance;
    expect(inst.configuration.l1_mm).toBe(62);
    expect(inst.configuration.l2_mm).toBe(27);
    expect(inst.technical_configuration_status).toBe("confirmed");
  });

  it("invalid pending + Confirm → zero apply", () => {
    const onApplyFinishPatch = vi.fn();
    render(
      <IntakeV6AcmPanelInspector
        model={model()}
        finishSetup={{ acm_panel_instance: model().instance }}
        actions={{ onApplyFinishPatch, onSegmentedPatch: vi.fn() }}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-acm-section-construction").querySelector("button")!);
    fireEvent.change(screen.getByTestId("intake-v6-acm-field-fold_count"), {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByTestId("intake-v6-acm-confirm-construction"));
    expect(onApplyFinishPatch).not.toHaveBeenCalled();
  });

  it("typing then debounce → one apply for field commit", () => {
    const onApplyFinishPatch = vi.fn();
    render(
      <IntakeV6AcmPanelInspector
        model={model()}
        finishSetup={{ acm_panel_instance: model().instance }}
        actions={{ onApplyFinishPatch, onSegmentedPatch: vi.fn() }}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-acm-section-construction").querySelector("button")!);
    const l1 = screen.getByTestId("intake-v6-acm-field-l1_mm");
    fireEvent.change(l1, { target: { value: "6" } });
    fireEvent.change(l1, { target: { value: "60" } });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 20);
    });
    // 60 equals canonical — zero commit; use 65
    fireEvent.change(l1, { target: { value: "65" } });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 20);
    });
    expect(onApplyFinishPatch).toHaveBeenCalledTimes(1);
    expect(onApplyFinishPatch.mock.calls[0]![0].acm_panel_instance.configuration.l1_mm).toBe(65);
  });

  it("section switch flushes pending before toggle", () => {
    const onApplyFinishPatch = vi.fn();
    render(
      <IntakeV6AcmPanelInspector
        model={model()}
        finishSetup={{ acm_panel_instance: model().instance }}
        actions={{ onApplyFinishPatch, onSegmentedPatch: vi.fn() }}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-acm-section-construction").querySelector("button")!);
    fireEvent.change(screen.getByTestId("intake-v6-acm-field-l1_mm"), {
      target: { value: "68" },
    });
    // switch to geometry — should flush construction draft first
    fireEvent.click(screen.getByTestId("intake-v6-acm-section-geometry").querySelector("button")!);
    expect(onApplyFinishPatch).toHaveBeenCalledTimes(1);
    expect(onApplyFinishPatch.mock.calls[0]![0].acm_panel_instance.configuration.l1_mm).toBe(68);
  });
});
