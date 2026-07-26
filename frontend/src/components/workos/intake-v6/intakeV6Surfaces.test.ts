import { describe, expect, it } from "vitest";
import {
  IV6_SURFACE_INSET,
  IV6_SURFACE_INPUT,
  IV6_SURFACE_PANEL,
  IV6_SURFACE_QUIET,
} from "./intakeV6Surfaces";
import { v6, v6Pilot } from "./atoms/intakeV6Presentation";

describe("intakeV6Surfaces (R7)", () => {
  it("uses wo-* semantic surface tokens", () => {
    expect(IV6_SURFACE_PANEL).toContain("bg-wo-surface-raised");
    expect(IV6_SURFACE_INSET).toContain("bg-wo-surface-inset");
    expect(IV6_SURFACE_INPUT).toContain("bg-wo-surface-input");
    expect(IV6_SURFACE_QUIET).toContain("bg-wo-surface-inset");
  });

  it("v6 presentation page/card/input are Day-honest wo-* tokens", () => {
    expect(v6.page).toContain("bg-wo-surface-inset");
    expect(v6.page).toContain("text-wo-text-primary");
    expect(v6.card).toContain("bg-wo-surface-raised");
    expect(v6.card).toContain("border-wo-border-strong");
    expect(v6.input).toContain("bg-wo-surface-input");
    expect(v6.page).not.toMatch(/#0A0F1A|#111827|#2A3548/);
    expect(v6Pilot.select).toContain("bg-wo-surface-input");
    expect(v6Pilot.resultPanel).toContain("bg-wo-surface-inset");
  });
});
