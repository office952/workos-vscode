import { describe, expect, it } from "vitest";
import {
  collectPipelineLegendMarkers,
  getPipelineDependencyWarningShort,
  getPipelineLegendLabel,
  getPipelineRowContextLine,
  pipelineMarkerToRowState,
  resolveEmployeeMobileV2PipelineMarkerPresentation,
  resolvePipelineRowVisualState,
  resolveEmployeeMobileV2StatusPresentation,
} from "@/lib/employeeMobileV2Status";

describe("employeeMobileV2Status", () => {
  it("shortens waiting predecessor status with detail line", () => {
    const presentation = resolveEmployeeMobileV2StatusPresentation({
      task_id: "T-1",
      order_id: 1,
      status: "assigned",
      readiness_status: "waiting_predecessor",
      is_startable: false,
      blocking_tasks: [{ name: "Modelare canturi" }],
    } as never);

    expect(presentation.shortLabel).toBe("Așteaptă");
    expect(presentation.detailLine).toBeTruthy();
    expect(presentation.shortLabel).not.toBe("Așteaptă task anterior");
  });

  it("maps in-progress to compact label", () => {
    const presentation = resolveEmployeeMobileV2StatusPresentation({
      task_id: "T-2",
      order_id: 1,
      status: "in_progress",
      is_startable: false,
    } as never);

    expect(presentation.shortLabel).toBe("În lucru");
  });

  it("maps pipeline waiting marker without long badge text", () => {
    const presentation = resolveEmployeeMobileV2PipelineMarkerPresentation(
      "asteapta",
      "Așteaptă task anterior",
      false,
    );
    expect(presentation?.shortLabel).toBe("Așteaptă");
    expect(presentation?.detailLine).toBe("task anterior");
    expect(presentation?.shortLabel).not.toBe("Așteaptă task anterior");
  });

  it("marks alt post pipeline context as muted", () => {
    const presentation = resolveEmployeeMobileV2PipelineMarkerPresentation(
      "alt_post",
      "Alt post",
      false,
    );
    expect(presentation?.shortLabel).toBe("Alt post");
    expect(presentation?.muted).toBe(true);
  });

  it("marks finalized pipeline marker as completed", () => {
    const presentation = resolveEmployeeMobileV2PipelineMarkerPresentation(
      "finalizat",
      null,
      false,
    );
    expect(presentation?.shortLabel).toBe("Finalizat");
    expect(presentation?.completed).toBe(true);
  });

  it("shortens pipeline dependency warning for current step", () => {
    expect(
      getPipelineDependencyWarningShort("A pornit înainte de finalizarea dependențelor"),
    ).toBe("Atenție: dependențe active");
  });

  it("builds waiting context line for pipeline center zone", () => {
    expect(getPipelineRowContextLine("asteapta", "Așteaptă task anterior", "Debitare spate Forex")).toBe(
      "Așteaptă: Debitare spate Forex",
    );
  });

  it("collects pipeline legend markers without duplicates", () => {
    expect(
      collectPipelineLegendMarkers(["acum", "asteapta", "alt_post", "neatribuit", "finalizat"]),
    ).toEqual(["acum", "asteapta", "finalizat", "alt_post"]);
  });

  it("resolves pipeline row visual states for timeline list", () => {
    expect(resolvePipelineRowVisualState({ isCurrent: true, marker: "acum" })).toBe("current");
    expect(resolvePipelineRowVisualState({ isCurrent: false, marker: "finalizat" })).toBe(
      "completed",
    );
    expect(resolvePipelineRowVisualState({ isCurrent: false, marker: "blocat" })).toBe("blocked");
    expect(resolvePipelineRowVisualState({ isCurrent: false, marker: "asteapta" })).toBe("waiting");
    expect(resolvePipelineRowVisualState({ isCurrent: false, marker: "urmeaza" })).toBe("upcoming");
    expect(resolvePipelineRowVisualState({ isCurrent: false, marker: "alt_post" })).toBe("alt-post");
  });

  it("maps blocked pipeline marker presentation", () => {
    const presentation = resolveEmployeeMobileV2PipelineMarkerPresentation(
      "blocat",
      "Blocat: Material lipsă",
      false,
    );
    expect(presentation?.shortLabel).toBe("Blocat");
    expect(presentation?.tone).toBe("warning");
  });

  it("builds blocked context line with reason", () => {
    expect(
      getPipelineRowContextLine("blocat", "Blocat", null, "Material lipsă"),
    ).toBe("Blocat: Material lipsă");
  });

  it("maps pipeline markers to vertical axis row states", () => {
    expect(pipelineMarkerToRowState("acum")).toBe("current");
    expect(pipelineMarkerToRowState("finalizat")).toBe("completed");
    expect(pipelineMarkerToRowState("blocat")).toBe("blocked");
    expect(pipelineMarkerToRowState("asteapta")).toBe("waiting");
    expect(pipelineMarkerToRowState("urmeaza")).toBe("upcoming");
    expect(pipelineMarkerToRowState("alt_post")).toBe("alt-post");
  });

  it("uses semantic legend labels for vertical pipeline", () => {
    expect(getPipelineLegendLabel("acum")).toBe("În lucru acum");
    expect(getPipelineLegendLabel("finalizat")).toBe("Finalizat");
    expect(getPipelineLegendLabel("blocat")).toBe("Blocat");
  });
});
