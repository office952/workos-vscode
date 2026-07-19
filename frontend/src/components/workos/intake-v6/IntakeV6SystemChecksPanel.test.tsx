import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import IntakeV6SystemChecksPanel, { resolveIntakeV6SystemChecksSummary } from "./IntakeV6SystemChecksPanel";

describe("resolveIntakeV6SystemChecksSummary", () => {
  it("returns Pregătit when there are no mentions", () => {
    expect(resolveIntakeV6SystemChecksSummary({ warningCount: 0, criticalCount: 0 })).toEqual(
      expect.objectContaining({
        mentionCount: 0,
        severity: "ok",
        label: "Verificări sistem: Pregătit",
        badgeLabel: "Pregătit",
      }),
    );
  });

  it("returns warning or critical labels when mentions exist", () => {
    expect(resolveIntakeV6SystemChecksSummary({ warningCount: 4, criticalCount: 0 })).toEqual(
      expect.objectContaining({
        mentionCount: 4,
        severity: "warning",
        label: "Verificări sistem: 4 mențiuni de rezolvat",
        badgeLabel: "Avertizare",
      }),
    );

    expect(resolveIntakeV6SystemChecksSummary({ warningCount: 2, criticalCount: 1 })).toEqual(
      expect.objectContaining({
        mentionCount: 3,
        severity: "critical",
        badgeLabel: "Blocant",
      }),
    );
  });
});

describe("IntakeV6SystemChecksPanel", () => {
  it("renders collapsed by default with the summary visible", () => {
    render(
      <IntakeV6SystemChecksPanel warningCount={2} criticalCount={0}>
        <div>detalii</div>
      </IntakeV6SystemChecksPanel>,
    );

    expect(screen.getByText("Verificări sistem: 2 mențiuni de rezolvat")).toBeInTheDocument();
    expect(screen.queryByText("detalii")).not.toBeInTheDocument();
  });
});
