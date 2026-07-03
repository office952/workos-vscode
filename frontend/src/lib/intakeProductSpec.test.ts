import { describe, expect, it } from "vitest";
import {
  isLitereVolumetriceFamily,
  normalizeIntakeProductSpecForSave,
  parseIntakeProductSpec,
} from "./intakeProductSpec";
import {
  getFaceOracalApplicationTiming,
  isFaceOracalFinish,
} from "@/features/product-system/volumetricLettersProduction";

describe("intakeProductSpec", () => {
  it("detects litere volumetrice family slug and legacy label", () => {
    expect(isLitereVolumetriceFamily("litere_volumetrice")).toBe(true);
    expect(isLitereVolumetriceFamily("Litere Volumetrice")).toBe(true);
    expect(isLitereVolumetriceFamily("print_large_format")).toBe(false);
  });

  it("parses JSON string spec", () => {
    const parsed = parseIntakeProductSpec('{"text":"BT","letter_height_mm":600}');
    expect(parsed?.text).toBe("BT");
    expect(parsed?.letter_height_mm).toBe(600);
  });

  it("normalizes empty fields out before save", () => {
    expect(normalizeIntakeProductSpecForSave({ text: "  ", notes: "" })).toBeNull();
    expect(
      normalizeIntakeProductSpecForSave({
        text: "DEDEMAN",
        illumination_type: "halo",
        backing_chamfer: false,
      })
    ).toEqual({
      text: "DEDEMAN",
      illumination_type: "halo",
      backing_chamfer: false,
    });
  });

  it("face oracal timing depends on premount", () => {
    expect(isFaceOracalFinish("oracal_651")).toBe(true);
    expect(
      getFaceOracalApplicationTiming({
        mounting_type: "premounted",
        premounting_type: "metal_structure",
      })
    ).toContain("după premontarea");
    expect(
      getFaceOracalApplicationTiming({
        mounting_type: "direct_wall",
        premounting_type: "none",
      })
    ).toContain("înainte de montajul pe perete");
  });

  it("persists volume_finish and face_miter_chamfer", () => {
    expect(
      normalizeIntakeProductSpecForSave({
        volume_finish: "oracal_651_before_forming",
        face_miter_chamfer: true,
      })
    ).toEqual({
      volume_finish: "oracal_651_before_forming",
      face_miter_chamfer: true,
    });
  });
});
