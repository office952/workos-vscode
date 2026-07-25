import { describe, expect, it } from "vitest";
import {
  CNC_PROCESSABLE_BADGE_CODE,
  CNC_PROCESSABLE_BADGE_LABEL,
  carrierHasCncProcessableBadge,
  machineCarriesCncProcessableBadge,
  materialCarriesCncProcessableBadge,
} from "./cncProcessableBadge";

describe("cncProcessableBadge", () => {
  it("keeps a stable badge identifier", () => {
    expect(CNC_PROCESSABLE_BADGE_CODE).toBe("BADGE-CNC-PROCESSABLE");
    expect(CNC_PROCESSABLE_BADGE_LABEL).toBe("CNC");
  });

  it("marks letter-face plexi stock as CNC-processable", () => {
    expect(materialCarriesCncProcessableBadge("MAT-ACP-FATA-LITERE")).toBe(true);
    expect(materialCarriesCncProcessableBadge("MAT-ORACAL-651")).toBe(false);
  });

  it("marks only CNC 4020 — not generic cnc_router or polystyrene", () => {
    expect(machineCarriesCncProcessableBadge({ id: "MCH-CNC-4020" })).toBe(true);
    expect(machineCarriesCncProcessableBadge({ name: "CNC 4020" })).toBe(true);
    expect(machineCarriesCncProcessableBadge({ type: "cnc_router" })).toBe(false);
    expect(machineCarriesCncProcessableBadge({ workcenterCode: "CNC_ROUTER" })).toBe(false);
    expect(
      machineCarriesCncProcessableBadge({
        type: "cnc_router",
        name: "CNC Polistiren",
        workcenterCode: "WC_CNC_ROUTING",
      }),
    ).toBe(false);
    expect(machineCarriesCncProcessableBadge({ type: "printer" })).toBe(false);
  });

  it("does not treat workcenter alone as a carrier", () => {
    expect(carrierHasCncProcessableBadge({ kind: "workcenter", code: "CNC_ROUTER" })).toBe(false);
    expect(carrierHasCncProcessableBadge({ kind: "machine", id: "MCH-CNC-4020" })).toBe(true);
  });
});
