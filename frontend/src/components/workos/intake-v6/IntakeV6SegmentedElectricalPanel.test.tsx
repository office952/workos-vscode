import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6SegmentedElectricalPanel from "./IntakeV6SegmentedElectricalPanel";

const confirmedFinish = {
  segmented_background: {
    schema: "acm_segmented_background_v1",
    status: "CONFIRMED",
    operator_confirmed: true,
    panels: [
      { panel_id: "panel_1", order: 1, width_mm: 1000, height_mm: 350, position: { x_mm: 0, y_mm: 0 } },
      { panel_id: "panel_2", order: 2, width_mm: 1000, height_mm: 350, position: { x_mm: 1000, y_mm: 0 } },
    ],
    joints: [],
    element_bindings: [],
  },
};

describe("IntakeV6SegmentedElectricalPanel", () => {
  it("renders only for confirmed multi-panel assemblies", () => {
    const { container } = render(
      <IntakeV6SegmentedElectricalPanel
        finish={{ segmented_background: { status: "PROPOSED", panels: confirmedFinish.segmented_background.panels } }}
        onPatchSegmented={vi.fn()}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows unresolved message and patches supply mode", () => {
    const onPatch = vi.fn();
    render(<IntakeV6SegmentedElectricalPanel finish={confirmedFinish} onPatchSegmented={onPatch} />);
    expect(screen.getByTestId("intake-v6-segmented-electrical-panel")).toBeTruthy();
    expect(screen.getByTestId("intake-v6-elec-unresolved-panel_1").textContent).toMatch(/nu este confirmata/i);
    fireEvent.change(screen.getByTestId("intake-v6-elec-supply-panel_1"), {
      target: { value: "DIRECT_220V" },
    });
    expect(onPatch).toHaveBeenCalled();
    const next = onPatch.mock.calls[0][0];
    expect(next.electrical_connection_management.panels[0].supply_mode).toBe("DIRECT_220V");
  });
});
