import { describe, expect, it } from "vitest";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import {
  applyFrontlitConstructionDefaults,
  collectFrontlitIntakeMissing,
  hasValidPsuSelection,
  computeLedLoadWatts,
  computePsuSizing,
  isFaceVinylEnabled,
  selectPsuWattsWithHeadroom,
} from "@/lib/volumetricFrontlitIntake";

describe("volumetricFrontlitIntake", () => {
  it("always enables visual chamfer and front-lit family", () => {
    const next = applyFrontlitConstructionDefaults({});
    expect(next.visual_chamfer_included).toBe(true);
    expect(next.face_miter_chamfer).toBe(true);
    expect(next.illumination_family).toBe("front_lit");
    expect(next.illumination_type).toBe("frontlit");
    expect(next.volume_finish).toBe("none");
    expect(next.paint_tube_count).toBeUndefined();
  });

  it("computes module LED load from perimeter", () => {
    const load = computeLedLoadWatts({
      lighting_system_type: "led_modules",
      led_module_power_w: 1.44,
      letter_perimeter_m: 18,
    });
    expect(load).toBe(1.44 * Math.ceil((18 * 1000) / 100));
  });

  it("computes strip LED load as watts per ml", () => {
    expect(
      computeLedLoadWatts({
        lighting_system_type: "led_strip",
        led_strip_density: "120_led_per_m",
        led_strip_power_w_per_ml: 10,
        letter_perimeter_m: 10,
      })
    ).toBe(100);
  });

  it("PSU sizing examples with 15% reserve", () => {
    expect(selectPsuWattsWithHeadroom(50)).toBe(60);
    expect(selectPsuWattsWithHeadroom(52)).toBe(60);
    expect(selectPsuWattsWithHeadroom(90)).toBe(160);
    expect(selectPsuWattsWithHeadroom(170)).toBe(200);
    expect(selectPsuWattsWithHeadroom(190)).toBeUndefined();
  });

  it("PSU test cases from build spec", () => {
    expect(computePsuSizing({ letter_perimeter_m: 0 }).status).toBe("pending_geometry");

    const fifty = computePsuSizing({
      lighting_system_type: "led_strip",
      led_strip_density: "60_led_per_m",
      letter_perimeter_m: 10,
    });
    expect(fifty.totalLedWatts).toBe(50);
    expect(fifty.requiredPsuWatts).toBe(57.5);
    expect(fifty.selectedPsuWatts).toBe(60);

    const overload = computePsuSizing({
      lighting_system_type: "led_strip",
      led_strip_density: "120_led_per_m",
      letter_perimeter_m: 19,
    });
    expect(overload.totalLedWatts).toBe(190);
    expect(overload.requiredPsuWatts).toBe(218.5);
    expect(overload.status).toBe("insufficient_capacity");
    expect(overload.selectedPsuWatts).toBeUndefined();
  });

  it("face vinyl toggle controls downstream assumptions", () => {
    expect(isFaceVinylEnabled({ face_vinyl_enabled: false })).toBe(false);
    expect(isFaceVinylEnabled({ face_vinyl_enabled: true })).toBe(true);
    expect(
      collectFrontlitIntakeMissing({ face_vinyl_enabled: false, face_finish_type: "oracal_651" }, "final")
    ).not.toContain("Cod culoare folie Oracal");
  });

  it("syncs face_vinyl_color_code from V2 Oracal selection for quote handoff", () => {
    const synced = applyFrontlitConstructionDefaults({
      face_vinyl_enabled: true,
      face_vinyl_series: "651",
      face_vinyl_code: "070",
      face_vinyl_name: "Black",
      face_finish_type: "oracal_651",
      face_vinyl_roll_width_mm: 1260,
    });
    expect(synced.face_vinyl_color_code).toBe("651-070");
    expect(synced.face_vinyl_color_name).toBe("Black");
    expect(
      collectFrontlitIntakeMissing(synced, "final")
    ).not.toContain("Cod culoare folie Oracal");
  });

  it("accepts V2 psu_configuration when allocation status is ok", () => {
    expect(
      hasValidPsuSelection({
        psu_allocation_status: "ok",
        psu_configuration: [100, 60],
      })
    ).toBe(true);
    expect(hasValidPsuSelection({ selected_psu_watts: 100 })).toBe(true);
    expect(
      hasValidPsuSelection({
        psu_allocation_status: "underpowered",
        psu_configuration: [60],
      })
    ).toBe(false);
    expect(
      collectFrontlitIntakeMissing({
        psu_allocation_status: "ok",
        psu_configuration: [100],
        lighting_system_type: "led_modules",
        led_module_power_w: 0.72,
        light_color: "warm",
        return_color: "white",
      })
    ).not.toContain("Putere sursă LED (W)");
  });

  it("persists computed watt fields on normalize", () => {
    const next = applyFrontlitConstructionDefaults({
      lighting_system_type: "led_modules",
      led_module_power_w: 0.72,
      letter_perimeter_m: 10,
    });
    expect(next.total_led_watts).toBeGreaterThan(0);
    expect(next.required_psu_watts).toBeGreaterThan(next.total_led_watts!);
    expect(next.psu_sizing_status).toBe("ok");
    expect(next.selected_psu_watts).toBeGreaterThanOrEqual(next.required_psu_watts!);
  });

  it("syncs return_depth_mm and depth_mm on construction defaults", () => {
    const next = applyFrontlitConstructionDefaults({
      depth_mm: 80,
    });
    expect(next.return_depth_mm).toBe(80);
    expect(next.depth_mm).toBe(80);
  });

  it("preserves V2 multi-PSU planning when total capacity meets required load", () => {
    const spec: IntakeProductSpec = {
      lighting_system_type: "led_modules",
      led_module_power_w: 1.44,
      letter_perimeter_m: 185,
      total_led_watts: 321.12,
      required_psu_watts: 369.29,
      light_color: "warm",
      return_color: "white",
      psu_allocation_status: "ok",
      psu_configuration: [200, 200],
      psu_total_capacity_watts: 400,
      selected_psu_watts: 200,
    };
    const next = applyFrontlitConstructionDefaults(spec);
    expect(next.psu_sizing_status).toBe("ok");
    expect(next.psu_configuration).toEqual([200, 200]);
    expect(next.selected_psu_watts).toBe(200);
    expect(
      collectFrontlitIntakeMissing(spec).some((m) =>
        m.includes("sursă") || m.includes("Putere sursă")
      )
    ).toBe(false);
  });
});
