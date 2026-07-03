import { describe, expect, it } from "vitest";
import {
  normalizeIntakeDimensionsText,
  parseIntakeDimensionNumbers,
  parseIntakeDimensionsStruct,
} from "./intakeDetailDimensions";

describe("intakeDetailDimensions", () => {
  it("normalizes null/empty dimensions to em dash", () => {
    expect(normalizeIntakeDimensionsText(null)).toBe("—");
    expect(normalizeIntakeDimensionsText("")).toBe("—");
    expect(normalizeIntakeDimensionsText("  ")).toBe("—");
  });

  it("parses numbers without throwing on null", () => {
    expect(parseIntakeDimensionNumbers(null)).toEqual([]);
    expect(parseIntakeDimensionNumbers("3000x1000x150mm")).toEqual([
      3000, 1000, 150,
    ]);
  });

  it("returns null struct for missing dimensions", () => {
    expect(parseIntakeDimensionsStruct(null)).toBeNull();
    expect(parseIntakeDimensionsStruct("4800x600x60")).toMatchObject({
      width: 4800,
      height: 600,
      depth: 60,
    });
  });
});
