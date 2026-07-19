import { describe, expect, it } from "vitest";
import {
  buildConfirmElectricalPatch,
  electricalConfirmBlocked,
  emptyPanelElectrical,
  ensureElectricalForPanels,
  ELECTRICAL_MESSAGES_RO,
} from "./segmentedElectrical";

describe("segmentedElectrical", () => {
  it("ensures a row per panel defaulting to UNCONFIRMED", () => {
    const elec = ensureElectricalForPanels(["panel_1", "panel_2"], null);
    expect(elec.panels).toHaveLength(2);
    expect(elec.panels.every((p) => p.supply_mode === "UNCONFIRMED")).toBe(true);
  });

  it("blocks confirm while any panel is UNCONFIRMED", () => {
    const elec = ensureElectricalForPanels(["panel_1", "panel_2"], null);
    expect(electricalConfirmBlocked(elec)).toContain(ELECTRICAL_MESSAGES_RO.unconfirmed);
  });

  it("allows confirm for direct per-panel 220V", () => {
    const elec = ensureElectricalForPanels(["panel_1", "panel_2"], null);
    elec.panels[0] = {
      ...emptyPanelElectrical("panel_1"),
      supply_mode: "DIRECT_220V",
      service_point_position: "TOP_RIGHT",
    };
    elec.panels[1] = {
      ...emptyPanelElectrical("panel_2"),
      supply_mode: "DIRECT_220V",
      service_point_position: "TOP_LEFT",
    };
    expect(electricalConfirmBlocked(elec)).toEqual([]);
    const confirmed = buildConfirmElectricalPatch(elec);
    expect(confirmed.status).toBe("CONFIRMED");
    expect(confirmed.operator_confirmed).toBe(true);
  });

  it("blocks self-shared supply", () => {
    const elec = ensureElectricalForPanels(["panel_1", "panel_2"], null);
    elec.panels[0].supply_mode = "DIRECT_220V";
    elec.panels[0].service_point_position = "TOP_RIGHT";
    elec.panels[1].supply_mode = "SHARED_FROM_PANEL";
    elec.panels[1].shared_from_panel_id = "panel_2";
    expect(electricalConfirmBlocked(elec).some((m) => /el insusi/i.test(m))).toBe(true);
  });
});
