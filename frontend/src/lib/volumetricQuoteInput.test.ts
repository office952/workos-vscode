import { describe, expect, it } from "vitest";
import {
  applyVolumetricQuoteInputDefaults,
  buildVolumetricQuoteInputPayload,
  computeLedModuleCountFromPerimeter,
  describeVolumetricIntakePrefill,
  estimatePaintTubeCount,
  isCantRalPaintEnabled,
  mapIntakeFaceFinishToQuoteType,
  mapIntakeMountingTemplateEnabled,
  mapIntakeMountingToQuoteSystem,
  mapProductSpecToVolumetricQuotePrefill,
  volumetricQuoteInputStepValid,
} from "./volumetricQuoteInput";

describe("volumetricQuoteInput", () => {
  it("computes LED modules from perimeter pitch 100mm", () => {
    expect(computeLedModuleCountFromPerimeter(18)).toBe(180);
    expect(computeLedModuleCountFromPerimeter(0)).toBe(0);
  });

  it("maps intake face_finish and mounting to quote contract", () => {
    expect(mapIntakeFaceFinishToQuoteType("plexi")).toBe("none");
    expect(mapIntakeFaceFinishToQuoteType("oracal_651")).toBe("oracal_651");
    expect(mapIntakeFaceFinishToQuoteType("print_laminated")).toBe(
      "printed_laminated_vinyl"
    );
    expect(
      mapIntakeMountingToQuoteSystem({
        mounting_type: "direct_wall",
      })
    ).toBe("direct_wall");
    expect(
      mapIntakeMountingToQuoteSystem({
        mounting_type: "premounted",
        premounting_type: "none",
      })
    ).toBe("direct_wall");
    expect(
      mapIntakeMountingTemplateEnabled({
        mounting_type: "premounted",
        premounting_type: "none",
      })
    ).toBe(true);
    expect(
      mapIntakeMountingToQuoteSystem({
        mounting_type: "premounted",
        premounting_type: "metal_structure",
      })
    ).toBe("steel_bars");
    expect(
      mapIntakeMountingToQuoteSystem({
        mounting_type: "premounted",
        premounting_type: "acm_casetted_panel",
      })
    ).toBe("acm_panel");
  });

  it("prefills aluminum bars from premount_bar_material legacy", () => {
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        mounting_type: "premounted",
        premounting_type: "metal_structure",
        premount_bar_material: "aluminum",
        mounting_bar_profile: "30x30x1.5",
      })
    ).toMatchObject({
      mounting_system: "aluminum_bars",
      mounting_bar_profile: "30x30x1.5",
    });
  });

  it("does not prefill stale SVG geometry after vector file change", () => {
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        vector_file_name: "lleexxaa.svg",
        geometry_stale: true,
        geometry_confirmed_for_file_name: "hotel_lexa.svg",
        vector_metrics_source: "svg_analysis",
        width_mm: 40000,
        height_mm: 5000,
        letter_perimeter_m: 185.797,
        letter_face_area_m2: 101.8419,
        letter_count: 11,
        return_depth_mm: 80,
      })
    ).toEqual({
      return_depth_mm: "80",
      depth_mm: "80",
      mounting_template_enabled: "false",
      mounting_template_material_type: "none",
      illumination_type: "frontlit",
      lighting_system_type: "led_modules",
    });
  });

  it("maps only safe fields from product_spec_json", () => {
    expect(mapProductSpecToVolumetricQuotePrefill(null)).toEqual({});
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        return_depth_mm: 60,
        text: "BT",
        letter_height_mm: 600,
      })
    ).toEqual({
      return_depth_mm: "60",
      depth_mm: "60",
      height_mm: "600",
      mounting_template_enabled: "false",
      mounting_template_material_type: "none",
      illumination_type: "frontlit",
      lighting_system_type: "led_modules",
    });
    expect(
      mapProductSpecToVolumetricQuotePrefill({ return_depth_mm: 70 })
    ).toEqual({
      mounting_template_enabled: "false",
      mounting_template_material_type: "none",
      illumination_type: "frontlit",
      lighting_system_type: "led_modules",
    });
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        return_depth_mm: 60,
        backing_chamfer: true,
        face_finish: "oracal_651",
        mounting_type: "premounted",
        premounting_type: "metal_structure",
      })
    ).toEqual({
      return_depth_mm: "60",
      depth_mm: "60",
      back_bevel_enabled: "true",
      face_finish_type: "oracal_651",
      mounting_system: "steel_bars",
      mounting_template_enabled: "false",
      mounting_template_material_type: "none",
      illumination_type: "frontlit",
      lighting_system_type: "led_modules",
    });
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        return_depth_mm: 60,
        mounting_type: "premounted",
        premounting_type: "none",
      })
    ).toEqual({
      return_depth_mm: "60",
      depth_mm: "60",
      mounting_system: "direct_wall",
      mounting_template_enabled: "true",
      mounting_template_material_type: "forex",
      illumination_type: "frontlit",
      lighting_system_type: "led_modules",
    });
  });

  it("prefills selected_psu_watts from V2 psu_configuration when classic field missing", () => {
    expect(
      mapProductSpecToVolumetricQuotePrefill({
        psu_allocation_status: "ok",
        psu_configuration: [200, 200],
      }).selected_psu_watts
    ).toBe("200");
  });

  it("applies enum defaults for face finish and mounting", () => {
    expect(applyVolumetricQuoteInputDefaults({})).toMatchObject({
      face_finish_type: "none",
      mounting_system: "direct_wall",
      mounting_template_enabled: "true",
      mounting_bar_profile: "30x30x1.5",
      mounting_bar_count: "2",
    });
    expect(
      applyVolumetricQuoteInputDefaults({ mounting_system: "forex_template" })
    ).toMatchObject({
      mounting_system: "direct_wall",
      mounting_template_enabled: "true",
    });
  });

  it("describes intake prefill vs manual geometry fields", () => {
    const summary = describeVolumetricIntakePrefill({
      return_depth_mm: 60,
      text: "BT",
    });
    expect(summary.prefilledFields).toEqual(
      expect.arrayContaining([
        { key: "return_depth_mm", label: "Adâncime cant / profil", value: "60" },
        { key: "depth_mm", label: "depth_mm", value: "60" },
        { key: "mounting_template_material_type", label: "mounting_template_material_type", value: "none" },
        { key: "illumination_type", label: "illumination_type", value: "frontlit" },
        { key: "lighting_system_type", label: "lighting_system_type", value: "led_modules" },
      ])
    );
    expect(summary.manualGeometryFields.map((f) => f.key)).toEqual([
      "letter_face_area_m2",
      "letter_perimeter_m",
      "mounting_template_area_m2",
    ]);
    expect(summary.manualOtherFields.map((f) => f.key)).toEqual([
      "letter_count",
      "face_finish_type",
      "mounting_system",
      "selected_psu_watts",
    ]);
    expect(summary.warnings).toEqual([]);
  });

  it("does not warn RAL for stock cant with stale paint_tube_count", () => {
    const summary = describeVolumetricIntakePrefill({
      return_color: "white",
      volume_finish: "none",
      paint_tube_count: 3,
    });
    expect(summary.warnings.some((w) => w.includes("RAL"))).toBe(false);
  });

  const fullVolumetricValues = {
    letter_face_area_m2: "2.88",
    letter_perimeter_m: "18",
    letter_count: "9",
    return_depth_mm: "60",
    face_finish_type: "none",
    mounting_system: "direct_wall",
    mounting_template_enabled: "true",
    selected_psu_watts: "100",
    mounting_template_area_m2: "2.88",
    paint_tube_count: "3",
  };

  it("builds payload with enum fields and mounting template enabled", () => {
    const payload = buildVolumetricQuoteInputPayload(fullVolumetricValues);
    expect(payload.letter_perimeter_m).toBe(18);
    expect(payload.led_module_count).toBe(180);
    expect(payload.selected_psu_watts).toBe(100);
    expect(payload.psu_watts).toBe(100);
    expect(payload.paint_tube_count).toBe(3);
    expect(payload.back_bevel_enabled).toBe(false);
    expect(payload.face_finish_type).toBe("none");
    expect(payload.mounting_system).toBe("direct_wall");
    expect(payload.mounting_template_enabled).toBe(true);
  });

  it("includes face finish and bar length in payload", () => {
    const payload = buildVolumetricQuoteInputPayload({
      ...fullVolumetricValues,
      face_finish_type: "oracal_651",
      mounting_system: "steel_bars",
      mounting_bar_length_m: "5",
      mounting_bar_profile: "30x30x1.5",
    });
    expect(payload.face_finish_type).toBe("oracal_651");
    expect(payload.mounting_system).toBe("steel_bars");
    expect(payload.mounting_bar_length_m).toBe(5);
    expect(payload.mounting_bar_profile).toBe("30x30x1.5");
    expect(payload.mounting_bar_count).toBe(2);
  });

  it("sets back_bevel_enabled true when checkbox checked", () => {
    const payload = buildVolumetricQuoteInputPayload({
      ...fullVolumetricValues,
      back_bevel_enabled: "true",
    });
    expect(payload.back_bevel_enabled).toBe(true);
  });

  it("includes fractional paint_tube_count in payload for backend ceil", () => {
    const payload = buildVolumetricQuoteInputPayload({
      ...fullVolumetricValues,
      paint_tube_count: "3.2",
    });
    expect(payload.paint_tube_count).toBe(3.2);
    expect(payload.led_module_count).toBe(180);
  });

  it("skips paint_tube_count when cant is stock color (no RAL paint)", () => {
    expect(isCantRalPaintEnabled({ volume_finish: "none" })).toBe(false);
    expect(
      volumetricQuoteInputStepValid(
        { ...fullVolumetricValues, paint_tube_count: "" },
        { cantRalPaintEnabled: false }
      )
    ).toBe(true);
  });

  it("auto-estimates paint tubes from perimeter when RAL cant paint enabled", () => {
    expect(estimatePaintTubeCount({ letter_perimeter_m: 18 })).toBe(3);
    const enriched = applyVolumetricQuoteInputDefaults(
      { letter_perimeter_m: "18", letter_count: "9" },
      { volume_finish: "paint_after_face_miter_bond" }
    );
    expect(enriched.paint_tube_count).toBe("3");
  });

  it("validates required volumetric fields including paint_tube_count when RAL paint", () => {
    const paintContext = { cantRalPaintEnabled: true };
    expect(volumetricQuoteInputStepValid(fullVolumetricValues, paintContext)).toBe(true);
    expect(
      volumetricQuoteInputStepValid(
        {
          ...fullVolumetricValues,
          paint_tube_count: "3.2",
        },
        paintContext
      )
    ).toBe(true);
    expect(
      volumetricQuoteInputStepValid(
        {
          ...fullVolumetricValues,
          paint_tube_count: "",
        },
        paintContext
      )
    ).toBe(false);
    expect(
      volumetricQuoteInputStepValid({
        letter_face_area_m2: "2.88",
        letter_perimeter_m: "18",
        letter_count: "9",
        return_depth_mm: "70",
        face_finish_type: "none",
        mounting_system: "direct_wall",
        mounting_template_enabled: "true",
        selected_psu_watts: "100",
        mounting_template_area_m2: "2.88",
        paint_tube_count: "3",
      })
    ).toBe(false);
  });

  it("requires mounting template area only when template enabled", () => {
    expect(
      volumetricQuoteInputStepValid({
        ...fullVolumetricValues,
        mounting_template_enabled: "false",
        mounting_template_area_m2: "",
      })
    ).toBe(true);
    expect(
      volumetricQuoteInputStepValid({
        ...fullVolumetricValues,
        mounting_template_enabled: "true",
        mounting_template_area_m2: "",
      })
    ).toBe(false);
  });

  it("allows steel bars without override when width_mm is available", () => {
    expect(
      volumetricQuoteInputStepValid(
        {
          ...fullVolumetricValues,
          mounting_system: "steel_bars",
          mounting_bar_length_m: "",
        },
        { widthMm: 4800 }
      )
    ).toBe(true);
    expect(
      volumetricQuoteInputStepValid(
        {
          ...fullVolumetricValues,
          mounting_system: "steel_bars",
          mounting_bar_length_m: "5",
        },
        { widthMm: 4800 }
      )
    ).toBe(true);
    expect(
      volumetricQuoteInputStepValid(
        {
          ...fullVolumetricValues,
          mounting_system: "steel_bars",
          mounting_bar_length_m: "",
        },
        {}
      )
    ).toBe(false);
    expect(
      volumetricQuoteInputStepValid({
        ...fullVolumetricValues,
        mounting_system: "direct_wall",
        mounting_bar_length_m: "",
      })
    ).toBe(true);
    expect(
      volumetricQuoteInputStepValid({
        ...fullVolumetricValues,
        mounting_system: "acm_panel",
        mounting_bar_length_m: "",
      })
    ).toBe(true);
  });
});
