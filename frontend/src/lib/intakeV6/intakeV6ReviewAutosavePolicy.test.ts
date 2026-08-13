import { describe, expect, it } from "vitest";
import {
  INTAKE_V6_COMMERCIAL_INPUTS_AUTOSAVE_MS,
  INTAKE_V6_SELECTOR_AUTOSAVE_LONG_MS,
  INTAKE_V6_SELECTOR_AUTOSAVE_SHORT_MS,
  resolveIntakeV6ReviewAutosaveDebounceMs,
} from "./intakeV6ReviewAutosavePolicy";

describe("intakeV6ReviewAutosavePolicy", () => {
  it("keeps discrete selector debounce under 200ms (legacy 700 floor removed)", () => {
    expect(INTAKE_V6_SELECTOR_AUTOSAVE_SHORT_MS).toBeLessThanOrEqual(150);
    expect(INTAKE_V6_SELECTOR_AUTOSAVE_SHORT_MS).toBeLessThan(200);
    expect(resolveIntakeV6ReviewAutosaveDebounceMs("short")).toBe(
      INTAKE_V6_SELECTOR_AUTOSAVE_SHORT_MS,
    );
  });

  it("keeps continuous numeric debounce in the safe 500–800ms band", () => {
    expect(INTAKE_V6_SELECTOR_AUTOSAVE_LONG_MS).toBeGreaterThanOrEqual(500);
    expect(INTAKE_V6_SELECTOR_AUTOSAVE_LONG_MS).toBeLessThanOrEqual(800);
    expect(resolveIntakeV6ReviewAutosaveDebounceMs("long")).toBe(
      INTAKE_V6_SELECTOR_AUTOSAVE_LONG_MS,
    );
  });

  it("keeps commercial slider debounce sensible (not per-keystroke)", () => {
    expect(INTAKE_V6_COMMERCIAL_INPUTS_AUTOSAVE_MS).toBeGreaterThanOrEqual(500);
    expect(INTAKE_V6_COMMERCIAL_INPUTS_AUTOSAVE_MS).toBeLessThanOrEqual(800);
  });

  it("does not reuse the legacy 700/1400 discrete floors", () => {
    expect(INTAKE_V6_SELECTOR_AUTOSAVE_SHORT_MS).not.toBe(700);
    expect(INTAKE_V6_SELECTOR_AUTOSAVE_LONG_MS).not.toBe(1400);
  });
});
