import { describe, expect, it } from "vitest";
import {
  ADD_UI,
  CANDIDATE_DISCOVERY_API,
  CREATE_UI,
  MACHINE_RUN_STATUS_LABEL,
  SECONDARY_CONTEXT_LINKS,
  actionsForStatus,
  mapMachineRunError,
  planOrderSummary,
  primaryActionLabel,
  visibleActionsForRole,
} from "./machineRunUi";

describe("machineRunUi — status copy + action matrix", () => {
  it("maps approved Romanian status labels", () => {
    expect(MACHINE_RUN_STATUS_LABEL.HELD).toBe("Grupare");
    expect(MACHINE_RUN_STATUS_LABEL.RESERVED).toBe("Rezervat");
    expect(MACHINE_RUN_STATUS_LABEL.RUNNING).toBe("În lucru pe utilaj");
    expect(MACHINE_RUN_STATUS_LABEL.COMPLETED).toBe("Lucru utilaj finalizat");
    expect(MACHINE_RUN_STATUS_LABEL.RELEASED).toBe("Eliberat");
    expect(MACHINE_RUN_STATUS_LABEL.CANCELLED).toBe("Anulat");
  });

  it("HELD matrix includes confirm/reschedule/remove/cancel — not start/complete", () => {
    const actions = actionsForStatus("HELD");
    expect(actions).toContain("confirm");
    expect(actions).toContain("reschedule");
    expect(actions).toContain("remove_participant");
    expect(actions).toContain("cancel");
    expect(actions).not.toContain("start");
    expect(actions).not.toContain("complete");
  });

  it("RESERVED primary for execute role is Pornește utilajul", () => {
    expect(primaryActionLabel("RESERVED", "operator")).toBe("Pornește utilajul");
    expect(visibleActionsForRole("RESERVED", "operator").map((a) => a.action)).toEqual([
      "start",
    ]);
    expect(visibleActionsForRole("RESERVED", "manager").map((a) => a.action)).toEqual([
      "start",
      "reschedule",
      "release",
      "cancel",
    ]);
  });

  it("RUNNING allows only complete; terminal is read-only", () => {
    expect(actionsForStatus("RUNNING")).toEqual(["complete"]);
    expect(actionsForStatus("RELEASED")).toEqual([]);
    expect(actionsForStatus("CANCELLED")).toEqual([]);
    expect(primaryActionLabel("COMPLETED", "manager")).toBe("Eliberează utilajul");
  });

  it("operator never sees manage-only actions", () => {
    const held = visibleActionsForRole("HELD", "operator");
    expect(held).toEqual([]);
    const completed = visibleActionsForRole("COMPLETED", "operator");
    expect(completed).toEqual([]);
  });

  it("maps cas_stale for operator UX", () => {
    const ux = mapMachineRunError("cas_stale");
    expect(ux.isCasStale).toBe(true);
    expect(ux.message).toContain("modificată între timp");
  });

  it("summarizes multi-plan / multi-order without inventing ownership", () => {
    expect(planOrderSummary([10, 11], [1, 2])).toBe("2 comenzi · 2 planuri");
    expect(planOrderSummary([10], [1])).toBe("Comandă 10 · Plan 1");
  });

  it("defers CREATE/ADD and secondary links when discovery/reverse APIs are missing", () => {
    expect(CANDIDATE_DISCOVERY_API).toBe("MISSING");
    expect(CREATE_UI).toBe("DEFERRED");
    expect(ADD_UI).toBe("DEFERRED");
    expect(SECONDARY_CONTEXT_LINKS).toBe("DEFERRED");
  });
});
