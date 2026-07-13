/** Product System mounting solution reference — Intake V6. */

import {
  hydrateMountingScopeFromFinishSetup,
  isMountingPreparationActive,
  type MountingScopeV1,
} from "@/lib/intakeV6/mountingScope";
import {
  ACM_BOXED_MOUNTING_QUOTE_INPUT_FIELDS,
  deriveAcmCasettedQuoteInput,
  TPL_ACM_BOXED_MOUNTING_SUPPORT,
} from "@/lib/acmQuoteInput";

export const METAL_PREMOUNT_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1";
export const ACM_BOXED_MOUNTING_TEMPLATE_CODE = TPL_ACM_BOXED_MOUNTING_SUPPORT;

export type MountingSolutionRef = {
  template_code: string;
  configuration: Record<string, unknown>;
};

export type MountingSolutionSelectorValue =
  | ""
  | typeof METAL_PREMOUNT_TEMPLATE_CODE
  | typeof ACM_BOXED_MOUNTING_TEMPLATE_CODE;

export const MOUNTING_SOLUTION_OPTIONS: ReadonlyArray<{
  value: MountingSolutionSelectorValue;
  label: string;
}> = [
  { value: "", label: "Fără soluție suplimentară" },
  {
    value: METAL_PREMOUNT_TEMPLATE_CODE,
    label: "Structură metalică pentru premontaj",
  },
  {
    value: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    label: "Suport ACM casetat (Product System)",
  },
] as const;

export const DEFAULT_METAL_MOUNTING_CONFIGURATION: Readonly<Record<string, unknown>> = {
  bar_count: 2,
  mounting_bar_profile: "30x30x1.5",
  bar_material: "steel",
};

export const DEFAULT_ACM_MOUNTING_CONFIGURATION: Readonly<Record<string, unknown>> = {
  panel_width_mm: 1000,
  panel_height_mm: 600,
  acm_thickness_mm: 3,
  return_depth_mm: 60,
  rear_lip_mm: 25,
  fold_sides: "all",
  v_groove_angle_deg: 135,
  frame_clearance_mm: 0,
};

const BAR_MOUNTING_LEGACY = new Set(["steel_bars", "aluminum_bars"]);
const ACM_PANEL_LEGACY = "acm_panel";

export function normalizeMetalMountingConfiguration(
  config: Record<string, unknown> | null | undefined,
): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...DEFAULT_METAL_MOUNTING_CONFIGURATION };
  if (config) {
    Object.assign(merged, config);
  }
  const barMaterial = String(merged.bar_material ?? "steel").trim().toLowerCase();
  merged.bar_material = barMaterial === "aluminum" ? "aluminum" : "steel";
  const profile = String(merged.mounting_bar_profile ?? "30x30x1.5").trim();
  merged.mounting_bar_profile = profile || "30x30x1.5";
  const count = Number(merged.bar_count ?? 2);
  merged.bar_count = Number.isFinite(count) && count > 0 ? Math.round(count) : 2;
  return merged;
}

export function normalizeAcmMountingConfiguration(
  config: Record<string, unknown> | null | undefined,
): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...DEFAULT_ACM_MOUNTING_CONFIGURATION };
  if (config) {
    Object.assign(merged, config);
  }
  for (const key of [
    "panel_width_mm",
    "panel_height_mm",
    "return_depth_mm",
    "rear_lip_mm",
    "frame_clearance_mm",
  ] as const) {
    const value = Number(merged[key] ?? DEFAULT_ACM_MOUNTING_CONFIGURATION[key]);
    merged[key] = Number.isFinite(value) ? value : DEFAULT_ACM_MOUNTING_CONFIGURATION[key];
  }
  const thickness = Number(merged.acm_thickness_mm ?? 3);
  merged.acm_thickness_mm = 3;
  const foldSides = String(merged.fold_sides ?? "all").trim().toLowerCase();
  merged.fold_sides = ["all", "top_bottom", "left_right"].includes(foldSides) ? foldSides : "all";
  const angle = Number(merged.v_groove_angle_deg ?? 135);
  merged.v_groove_angle_deg = Number.isFinite(angle) ? angle : 135;
  const derived = deriveAcmCasettedQuoteInput(merged);
  Object.assign(merged, derived.payload);
  return merged;
}

export function normalizeMountingSolutionConfiguration(
  templateCode: string,
  config: Record<string, unknown> | null | undefined,
): Record<string, unknown> {
  if (templateCode === METAL_PREMOUNT_TEMPLATE_CODE) {
    return normalizeMetalMountingConfiguration(config);
  }
  if (templateCode === ACM_BOXED_MOUNTING_TEMPLATE_CODE) {
    return normalizeAcmMountingConfiguration(config);
  }
  return config ? { ...config } : {};
}

export function readMountingSolution(
  setup: Record<string, unknown> | null | undefined,
): MountingSolutionRef | null {
  if (!setup) return null;
  const raw = setup.mounting_solution;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const templateCode = String((raw as MountingSolutionRef).template_code ?? "").trim();
  if (!templateCode) return null;
  const configuration =
    (raw as MountingSolutionRef).configuration &&
    typeof (raw as MountingSolutionRef).configuration === "object" &&
    !Array.isArray((raw as MountingSolutionRef).configuration)
      ? { ...(raw as MountingSolutionRef).configuration }
      : {};
  return { template_code: templateCode, configuration };
}

export function hydrateMountingSolutionFromLegacy(
  setup: Record<string, unknown>,
): MountingSolutionRef | null {
  const existing = readMountingSolution(setup);
  if (existing) return existing;
  const mountingSystem = String(setup.mounting_system ?? "").trim();
  if (mountingSystem === ACM_PANEL_LEGACY) {
    return {
      template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
      configuration: normalizeAcmMountingConfiguration({}),
    };
  }
  if (!BAR_MOUNTING_LEGACY.has(mountingSystem)) return null;
  return {
    template_code: METAL_PREMOUNT_TEMPLATE_CODE,
    configuration: normalizeMetalMountingConfiguration({
      bar_material: mountingSystem === "aluminum_bars" ? "aluminum" : "steel",
      mounting_bar_profile: setup.mounting_bar_profile,
    }),
  };
}

export function resolveEffectiveMountingSolution(
  setup: Record<string, unknown> | null | undefined,
): MountingSolutionRef | null {
  if (!setup) return null;
  return readMountingSolution(setup) ?? hydrateMountingSolutionFromLegacy(setup);
}

export function isAllowedMountingSolutionTemplate(templateCode: string): boolean {
  return (
    templateCode === METAL_PREMOUNT_TEMPLATE_CODE || templateCode === ACM_BOXED_MOUNTING_TEMPLATE_CODE
  );
}

export function isMountingSolutionCompositionActive(
  setup: Record<string, unknown> | null | undefined,
): boolean {
  if (!setup) return false;
  const { mounting_scope } = hydrateMountingScopeFromFinishSetup(setup);
  if (!isMountingPreparationActive(mounting_scope)) return false;
  const solution = resolveEffectiveMountingSolution(setup);
  return solution ? isAllowedMountingSolutionTemplate(solution.template_code) : false;
}

export function mountingSolutionSelectorValue(
  setup: Record<string, unknown> | null | undefined,
): MountingSolutionSelectorValue {
  const solution = resolveEffectiveMountingSolution(setup);
  if (!solution) return "";
  if (isAllowedMountingSolutionTemplate(solution.template_code)) {
    return solution.template_code as MountingSolutionSelectorValue;
  }
  return "";
}

export function legacyMountingSystemLabel(
  setup: Record<string, unknown> | null | undefined,
): string {
  const solution = resolveEffectiveMountingSolution(setup);
  if (solution?.template_code === METAL_PREMOUNT_TEMPLATE_CODE) {
    const config = normalizeMetalMountingConfiguration(solution.configuration);
    return config.bar_material === "aluminum" ? "aluminum_bars" : "steel_bars";
  }
  if (solution?.template_code === ACM_BOXED_MOUNTING_TEMPLATE_CODE) {
    return ACM_PANEL_LEGACY;
  }
  return String(setup?.mounting_system ?? "direct_wall");
}

export function legacyMountingBarProfile(
  setup: Record<string, unknown> | null | undefined,
): string {
  const solution = resolveEffectiveMountingSolution(setup);
  if (solution?.template_code === METAL_PREMOUNT_TEMPLATE_CODE) {
    return String(
      normalizeMetalMountingConfiguration(solution.configuration).mounting_bar_profile ?? "30x30x1.5",
    );
  }
  return String(setup?.mounting_bar_profile ?? "30x30x1.5");
}

export function buildMountingSolutionPatch(
  selectorValue: MountingSolutionSelectorValue,
  configuration?: Record<string, unknown>,
): Pick<Record<string, unknown>, "mounting_solution" | "mounting_system" | "mounting_bar_profile"> {
  if (!selectorValue) {
    return {
      mounting_solution: null,
      mounting_system: null,
      mounting_bar_profile: null,
    };
  }
  return {
    mounting_solution: {
      template_code: selectorValue,
      configuration: normalizeMountingSolutionConfiguration(selectorValue, configuration),
    },
    mounting_system: null,
    mounting_bar_profile: null,
  };
}

export function prepareMountingSolutionForSave(
  form: Record<string, unknown>,
): Record<string, unknown> {
  const next = { ...form };
  if (readMountingSolution(next)) {
    delete next.mounting_system;
    delete next.mounting_bar_profile;
  }
  return next;
}

export function isMountingSolutionSelectorDisabled(scope: MountingScopeV1): boolean {
  return !isMountingPreparationActive(scope);
}

export { ACM_BOXED_MOUNTING_QUOTE_INPUT_FIELDS };
