import { describe, expect, it } from "vitest";
import type { IntakeProductSpec } from "./intakeProductSpec";
import {
  applyIlluminationMode,
  applyMountingTemplateMode,
  isIntakeIlluminationDisabled,
  resolveIlluminationMode,
  resolveMountingTemplateMode,
} from "./volumetricIntakeSelectors";
import { mapProductSpecToVolumetricQuotePrefill } from "./volumetricQuoteInput";

describe("volumetricIntakeSelectors", () => {
  it("maps mounting template none", () => {
    const spec = applyMountingTemplateMode({} as IntakeProductSpec, "none");
    expect(spec.mounting_template_enabled).toBe(false);
    expect(spec.mounting_template_material_type).toBe("none");
    expect(resolveMountingTemplateMode(spec)).toBe("none");
  });

  it("maps mounting template paper", () => {
    const spec = applyMountingTemplateMode({} as IntakeProductSpec, "paper");
    expect(spec.mounting_template_enabled).toBe(true);
    expect(spec.mounting_template_material_type).toBe("paper");
  });

  it("maps mounting template forex", () => {
    const spec = applyMountingTemplateMode({} as IntakeProductSpec, "forex");
    expect(spec.mounting_template_enabled).toBe(true);
    expect(spec.mounting_template_material_type).toBe("forex");
  });

  it("legacy enabled without material type resolves to forex", () => {
    expect(
      resolveMountingTemplateMode({ mounting_template_enabled: true } as IntakeProductSpec)
    ).toBe("forex");
  });

  it("legacy premounted without premounting resolves to forex template", () => {
    expect(
      resolveMountingTemplateMode({
        mounting_type: "premounted",
        premounting_type: "none",
      } as IntakeProductSpec)
    ).toBe("forex");
  });

  it("legacy illumination none maps to non_illuminated", () => {
    expect(
      resolveIlluminationMode({
        illumination_type: "none" as IntakeProductSpec["illumination_type"],
        lighting_system_type: "none",
      } as IntakeProductSpec)
    ).toBe("non_illuminated");
    expect(
      isIntakeIlluminationDisabled({
        illumination_type: "none" as IntakeProductSpec["illumination_type"],
        lighting_system_type: "none",
      } as IntakeProductSpec)
    ).toBe(true);
  });

  it("non_illuminated with lighting none maps to non_illuminated", () => {
    expect(
      resolveIlluminationMode({
        illumination_type: "non_illuminated",
        lighting_system_type: "none",
      } as IntakeProductSpec)
    ).toBe("non_illuminated");
  });

  it("illuminated frontlit led_modules and led_strip", () => {
    expect(
      resolveIlluminationMode({
        illumination_type: "frontlit",
        lighting_system_type: "led_modules",
      } as IntakeProductSpec)
    ).toBe("led_modules");
    expect(
      resolveIlluminationMode({
        illumination_type: "frontlit",
        lighting_system_type: "led_strip",
      } as IntakeProductSpec)
    ).toBe("led_strip");
  });

  it("missing illumination fields default to led_modules for legacy compat", () => {
    expect(resolveIlluminationMode({} as IntakeProductSpec)).toBe("led_modules");
    expect(isIntakeIlluminationDisabled({} as IntakeProductSpec)).toBe(false);
  });

  it("non-illuminated clears LED fields and quote prefill", () => {
    const spec = applyIlluminationMode(
      {
        illumination_type: "frontlit",
        lighting_system_type: "led_modules",
        selected_psu_watts: 100,
        led_module_power_w: 1.44,
      } as IntakeProductSpec,
      "non_illuminated"
    );
    expect(isIntakeIlluminationDisabled(spec)).toBe(true);
    expect(spec.lighting_system_type).toBeUndefined();
    expect(spec.selected_psu_watts).toBeUndefined();

    const prefill = mapProductSpecToVolumetricQuotePrefill(spec);
    expect(prefill.illumination_type).toBe("non_illuminated");
    expect(prefill.lighting_system_type).toBe("none");
    expect(prefill.selected_psu_watts).toBeUndefined();
  });

  it("illuminated modules preserve LED prefill path", () => {
    const spec = applyIlluminationMode(
      {
        lighting_system_type: "led_modules",
        selected_psu_watts: 100,
        letter_perimeter_m: 18,
      } as IntakeProductSpec,
      "led_modules"
    );
    expect(resolveIlluminationMode(spec)).toBe("led_modules");
    expect(isIntakeIlluminationDisabled(spec)).toBe(false);
    const prefill = mapProductSpecToVolumetricQuotePrefill(spec);
    expect(prefill.lighting_system_type).toBe("led_modules");
    expect(prefill.selected_psu_watts).toBe("100");
  });
});
