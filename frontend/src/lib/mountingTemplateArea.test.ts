import { describe, expect, it } from "vitest";
import {
  computeMountingTemplateAreaM2,
  formatMountingTemplateAreaHint,
  roundAreaM2,
} from "./mountingTemplateArea";

describe("mountingTemplateArea", () => {
  it("computes area from width and height in mm", () => {
    expect(
      computeMountingTemplateAreaM2({
        width_mm: 5000,
        height_mm: 952,
      })
    ).toBe(4.76);
  });

  it("falls back to letter_face_area_m2 when dimensions missing", () => {
    expect(
      computeMountingTemplateAreaM2({
        letter_face_area_m2: 2.88,
      })
    ).toBe(2.88);
  });

  it("returns null when geometry insufficient", () => {
    expect(computeMountingTemplateAreaM2({})).toBeNull();
  });

  it("formats dimension hint for auto-calc", () => {
    expect(
      formatMountingTemplateAreaHint({ width_mm: 5000, height_mm: 952 })
    ).toBe("Calculat automat din 5000 × 952 mm");
  });

  it("rounds area to two decimals", () => {
    expect(roundAreaM2(4.756)).toBe(4.76);
  });
});
