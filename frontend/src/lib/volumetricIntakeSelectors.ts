/**
 * WorkIntake V2 / Product001 — mounting template + illumination selector mapping.
 * Aligns intake spec with backend quote_input / policy helpers.
 */

import type { IntakeProductSpec } from "./intakeProductSpec";
import { resolveIntakeMountingTemplateEnabled } from "./intakeVolumetricSpec";

export type MountingTemplateMode = "none" | "paper" | "forex";
export type IlluminationMode = "non_illuminated" | "led_modules" | "led_strip";

export const MOUNTING_TEMPLATE_MODE_OPTIONS: {
  value: MountingTemplateMode;
  label: string;
  helper: string;
}[] = [
  {
    value: "none",
    label: "Fără șablon",
    helper: "Nu se calculează material sau operații de șablon montaj.",
  },
  {
    value: "paper",
    label: "Șablon hârtie",
    helper: "Pentru poziționare/montaj — cost pe mp, fără debitare CNC șablon.",
  },
  {
    value: "forex",
    label: "Șablon Forex",
    helper: "Șablon rigid — poate necesita debitare CNC când aria este validă.",
  },
];

export const ILLUMINATION_MODE_OPTIONS: {
  value: IlluminationMode;
  label: string;
}[] = [
  { value: "non_illuminated", label: "Neluminat" },
  { value: "led_modules", label: "Iluminat cu module LED" },
  { value: "led_strip", label: "Iluminat cu bandă LED" },
];

export function resolveMountingTemplateMode(
  spec: IntakeProductSpec | null | undefined
): MountingTemplateMode {
  const raw = spec?.mounting_template_material_type;
  if (raw === "none" || raw === "paper" || raw === "forex") {
    return raw;
  }
  if (spec?.mounting_template_enabled === false) {
    return "none";
  }
  if (spec?.mounting_template_enabled === true) {
    return "forex";
  }
  if (resolveIntakeMountingTemplateEnabled(spec ?? {}) === true) {
    return "forex";
  }
  return "none";
}

export function applyMountingTemplateMode(
  spec: IntakeProductSpec,
  mode: MountingTemplateMode
): IntakeProductSpec {
  if (mode === "none") {
    return {
      ...spec,
      mounting_template_enabled: false,
      mounting_template_material_type: "none",
    };
  }
  return {
    ...spec,
    mounting_template_enabled: true,
    mounting_template_material_type: mode,
  };
}

export function isExplicitNonIlluminatedSpec(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  const illumination = spec.illumination_type as string | undefined;
  if (illumination === "non_illuminated" || illumination === "none") return true;
  if (spec.lighting_system_type === "none") return true;
  return false;
}

export function isIntakeIlluminationDisabled(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  return isExplicitNonIlluminatedSpec(spec);
}

export function resolveIlluminationMode(
  spec: IntakeProductSpec | null | undefined
): IlluminationMode {
  if (!spec) return "led_modules";
  if (isExplicitNonIlluminatedSpec(spec)) return "non_illuminated";
  if (spec.lighting_system_type === "led_strip") return "led_strip";
  return "led_modules";
}

export function clearIlluminationLedFields(spec: IntakeProductSpec): IntakeProductSpec {
  return {
    ...spec,
    illumination_type: "non_illuminated",
    illumination_family: undefined,
    lighting_system_type: undefined,
    led_module_power_w: undefined,
    led_module_wattage: undefined,
    led_strip_density: undefined,
    led_strip_power_w_per_ml: undefined,
    total_led_watts: undefined,
    required_psu_watts: undefined,
    selected_psu_watts: undefined,
    psu_configuration: [],
    psu_total_capacity_watts: undefined,
    psu_reserve_margin_watts: undefined,
    psu_allocation_status: undefined,
    psu_allocation_warning: undefined,
    psu_sizing_status: undefined,
    psu_sizing_warning: undefined,
    psu_selection_mode: undefined,
    psu_override_reason: undefined,
    light_color: undefined,
    led_color_temperature: undefined,
  };
}

export function applyIlluminationMode(
  spec: IntakeProductSpec,
  mode: IlluminationMode
): IntakeProductSpec {
  if (mode === "non_illuminated") {
    return clearIlluminationLedFields(spec);
  }
  const next: IntakeProductSpec = {
    ...spec,
    illumination_type: "frontlit",
    illumination_family: "front_lit",
    lighting_system_type: mode === "led_strip" ? "led_strip" : "led_modules",
  };
  return next;
}

export function mountingTemplateModeRequiresArea(mode: MountingTemplateMode): boolean {
  return mode === "paper" || mode === "forex";
}
