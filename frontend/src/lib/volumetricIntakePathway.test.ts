import { describe, expect, it } from "vitest";
import {
  derivePathwayFromSpec,
  isIntakeSectionVisible,
  needsManualGeometryFallback,
  pathwayToCalculationMethod,
} from "@/lib/volumetricIntakePathway";

describe("volumetricIntakePathway", () => {
  it("derives stored pathway when present", () => {
    expect(
      derivePathwayFromSpec({ intake_input_pathway: "quick_estimate" })
    ).toBe("quick_estimate");
  });

  it("infers vector from file metadata", () => {
    expect(
      derivePathwayFromSpec({
        vector_file_name: "logo.svg",
      })
    ).toBe("vector");
  });

  it("prefers vector over stale manual when vector file is present", () => {
    expect(
      derivePathwayFromSpec({
        intake_input_pathway: "manual",
        vector_file_name: "logo.svg",
      })
    ).toBe("vector");
  });

  it("keeps explicit manual when no vector hints exist", () => {
    expect(
      derivePathwayFromSpec({
        intake_input_pathway: "manual",
        depth_mm: 60,
      })
    ).toBe("manual");
  });

  it("hides vector studio on manual pathway", () => {
    expect(isIntakeSectionVisible("manual", 9)).toBe(false);
    expect(isIntakeSectionVisible("manual", 3)).toBe(true);
  });

  it("hides vector studio section 9 on vector pathway (single surface above)", () => {
    expect(isIntakeSectionVisible("vector", 9)).toBe(false);
    expect(isIntakeSectionVisible("vector", 1)).toBe(true);
    expect(isIntakeSectionVisible("vector", 4)).toBe(true);
  });

  it("shows only sections 1-2 on quick estimate", () => {
    expect(isIntakeSectionVisible("quick_estimate", 1)).toBe(true);
    expect(isIntakeSectionVisible("quick_estimate", 2)).toBe(true);
    expect(isIntakeSectionVisible("quick_estimate", 9)).toBe(false);
    expect(isIntakeSectionVisible("quick_estimate", 4)).toBe(false);
  });

  it("shows geometry fallback on vector when metrics missing", () => {
    expect(isIntakeSectionVisible("vector", 3, {})).toBe(true);
    expect(
      isIntakeSectionVisible("vector", 3, {
        letter_face_area_m2: 2.88,
        letter_perimeter_m: 18,
        letter_count: 9,
      })
    ).toBe(false);
  });

  it("hides face finish section when wrap disabled", () => {
    expect(isIntakeSectionVisible("manual", 5, { face_vinyl_enabled: false })).toBe(false);
    expect(
      isIntakeSectionVisible("manual", 5, { face_vinyl_enabled: true, face_finish_type: "oracal_651" })
    ).toBe(true);
  });

  it("hides RAL paint section on frontlit template", () => {
    expect(isIntakeSectionVisible("manual", 6, {})).toBe(false);
  });

  it("maps pathway to quote calculation method", () => {
    expect(pathwayToCalculationMethod("vector")).toBe("vector_first");
    expect(pathwayToCalculationMethod("manual")).toBe("manual_geometry");
    expect(pathwayToCalculationMethod("quick_estimate")).toBe("quick_estimate");
  });

  it("detects manual geometry fallback need", () => {
    expect(needsManualGeometryFallback({})).toBe(true);
    expect(
      needsManualGeometryFallback({
        letter_face_area_m2: 1,
        letter_perimeter_m: 2,
        letter_count: 3,
      })
    ).toBe(false);
  });
});
