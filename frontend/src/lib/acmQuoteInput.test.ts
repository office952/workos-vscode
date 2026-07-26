import { describe, expect, it } from "vitest";
import {
  ACM_BOXED_MOUNTING_SUPPORTED_THICKNESS_MM,
  buildAcmCasettedQuoteInputPayload,
  buildCutAcmQuoteInputPayload,
  isAcmTemplateCode,
  rearLipWarning,
  TPL_ACM_BOXED_MOUNTING_SUPPORT,
} from "./acmQuoteInput";

describe("acmQuoteInput", () => {
  it("derives panel area and fold length for casetted panel", () => {
    const qi = buildAcmCasettedQuoteInputPayload({
      panel_width_mm: "2880",
      panel_height_mm: "1000",
      acm_thickness_mm: "3",
      return_depth_mm: "60",
      rear_lip_mm: "25",
      fold_sides: "all",
      v_groove_angle_deg: "135",
    });
    expect(qi.panel_area_m2).toBeCloseTo(2.88, 2);
    expect(qi.fold_length_m).toBeCloseTo(7.76, 2);
    expect(qi.return_strip_area_m2).toBeCloseTo(0.4656, 3);
    expect(qi.acm_thickness_mm).toBe(3);
  });

  it("warns when rear lip below 25mm", () => {
    expect(rearLipWarning(20)).toContain("25");
    expect(rearLipWarning(30)).toBeNull();
  });

  it("builds cut ACM quote input", () => {
    const qi = buildCutAcmQuoteInputPayload({
      cut_area_m2: "0.1",
      cut_perimeter_m: "12",
      acm_thickness_mm: "3",
    });
    expect(qi.cut_area_m2).toBe(0.1);
    expect(qi.cut_perimeter_m).toBe(12);
  });

  it("recognizes boxed mounting standalone root template code", () => {
    expect(isAcmTemplateCode(TPL_ACM_BOXED_MOUNTING_SUPPORT)).toBe(true);
    expect(ACM_BOXED_MOUNTING_SUPPORTED_THICKNESS_MM).toEqual([3]);
  });

  it("boxed mounting standalone payload uses 3mm-only thickness options", () => {
    const qi = buildAcmCasettedQuoteInputPayload({
      panel_width_mm: "1200",
      panel_height_mm: "800",
      acm_thickness_mm: "3",
      return_depth_mm: "60",
      fold_sides: "all",
    });
    expect(qi.acm_thickness_mm).toBe(3);
    expect(qi.panel_area_m2).toBeCloseTo(0.96, 2);
  });
});
