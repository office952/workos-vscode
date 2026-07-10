import { describe, expect, it } from "vitest";
import { buildIntakeV6FooterIssuesDisplay } from "./intakeV6FooterIssuesDisplay";

describe("buildIntakeV6FooterIssuesDisplay", () => {
  it("groups warnings and technical entries separately", () => {
    const display = buildIntakeV6FooterIssuesDisplay({
      reviewWarnings: ["Verifică lățimea cantului.", "artwork_execution_undecided:Layer_1"],
      secondaryWarnings: ["2 straturi propuse ca Vector Litere — confirmă rolurile."],
      statusActions: [{ id: "jump-layers", label: "Mergi la straturi" }],
    });

    expect(display.totalCount).toBeGreaterThan(0);
    expect(display.groups.find((group) => group.id === "warnings")).toBeTruthy();
    expect(display.groups.find((group) => group.id === "technical")).toBeTruthy();
    expect(display.groups.find((group) => group.id === "actions")).toBeTruthy();
  });

  it("keeps primary action reason out of grouped entries when passed separately", () => {
    const display = buildIntakeV6FooterIssuesDisplay({
      primaryActionReason: "Confirmă rolul pentru toate straturile.",
    });

    expect(display.primaryActionReason).toBe("Confirmă rolul pentru toate straturile.");
    expect(display.groups.flatMap((group) => group.entries).some((entry) => /Confirmă rolul/i.test(entry.title))).toBe(
      true,
    );
  });
});
