import { describe, expect, it } from "vitest";
import {
  buildVolumetricQuotePrepSummary,
  deriveGeometrySourceLabel,
} from "./volumetricIntakeFormPrep";

describe("volumetricIntakeFormPrep", () => {
  it("reports incomplete geometry when metrics missing", () => {
    expect(deriveGeometrySourceLabel({})).toBe("Necompletat");
    expect(deriveGeometrySourceLabel({ vector_file_name: "litere.svg" })).toContain(
      "Necompletat"
    );
  });

  it("reports manual geometry source", () => {
    expect(
      deriveGeometrySourceLabel({
        letter_perimeter_m: 18,
        letter_count: 9,
        vector_metrics_source: "manual",
      })
    ).toBe("Introduse manual");
  });

  it("lists missing simulate fields", () => {
    const summary = buildVolumetricQuotePrepSummary({
      width_mm: 4800,
      face_finish_type: "none",
    });
    expect(summary.missingForSimulate).toContain("Aria față litere (m²)");
    expect(summary.missingForSimulate).toContain("Perimetru litere (ml)");
    expect(summary.ledModuleCountEstimate).toBeNull();
  });

  it("estimates LED modules from perimeter", () => {
    const summary = buildVolumetricQuotePrepSummary({
      letter_perimeter_m: 18,
    });
    expect(summary.ledModuleCountEstimate).toBeGreaterThan(0);
  });

  it("flags vector and Oracal gaps for final quote hints", () => {
    const summary = buildVolumetricQuotePrepSummary({
      face_finish_type: "oracal_651",
      volume_finish: "paint_after_face_miter_bond",
      paint_tube_count: 3,
    });
    expect(summary.missingForFinalQuote.some((m) => m.includes("vector"))).toBe(true);
    expect(summary.missingForFinalQuote.some((m) => m.includes("Oracal"))).toBe(true);
    expect(summary.missingForFinalQuote.some((m) => m.includes("RAL"))).toBe(true);
  });

  it("does not require RAL for stock cant with stale paint_tube_count", () => {
    const summary = buildVolumetricQuotePrepSummary({
      return_color: "white",
      volume_finish: "none",
      paint_tube_count: 3,
      letter_face_area_m2: 1,
      letter_perimeter_m: 10,
      letter_count: 5,
      return_depth_mm: 60,
      lighting_system_type: "led_modules",
      led_module_power_w: 0.72,
      light_color: "warm",
      selected_psu_watts: 100,
    });
    expect(summary.missingForFinalQuote.some((m) => m.includes("RAL"))).toBe(false);
    expect(summary.missingForSimulate.some((m) => m.includes("RAL"))).toBe(false);
  });

  it("accepts depth_mm alias for return depth readiness", () => {
    const summary = buildVolumetricQuotePrepSummary({
      depth_mm: 80,
      letter_face_area_m2: 1,
      letter_perimeter_m: 10,
      letter_count: 5,
      lighting_system_type: "led_modules",
      led_module_power_w: 0.72,
      light_color: "warm",
      return_color: "black",
      selected_psu_watts: 100,
    });
    expect(
      summary.missingForSimulate.some((m) => m.includes("Adâncime cant / retur"))
    ).toBe(false);
  });
});
