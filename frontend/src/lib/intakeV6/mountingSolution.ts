/** Product System mounting solution reference — Intake V6. */

import {
  hydrateMountingScopeFromFinishSetup,
  isMountingPreparationActive,
  type MountingScopeV1,
} from "@/lib/intakeV6/mountingScope";

export const METAL_PREMOUNT_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1";

export type MountingSolutionRef = {
  template_code: string;
  configuration: Record<string, unknown>;
};

export type MountingSolutionSelectorValue = "" | typeof METAL_PREMOUNT_TEMPLATE_CODE;

export const MOUNTING_SOLUTION_OPTIONS: ReadonlyArray<{
  value: MountingSolutionSelectorValue;
  label: string;
}> = [
  { value: "", label: "Fără soluție suplimentară" },
  {
    value: METAL_PREMOUNT_TEMPLATE_CODE,
    label: "Structură metalică pentru premontaj",
  },
] as const;

export const DEFAULT_METAL_MOUNTING_CONFIGURATION: Readonly<Record<string, unknown>> = {
  bar_count: 2,
  mounting_bar_profile: "30x30x1.5",
  bar_material: "steel",
};

const BAR_MOUNTING_LEGACY = new Set(["steel_bars", "aluminum_bars"]);

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

export function isMountingSolutionCompositionActive(
  setup: Record<string, unknown> | null | undefined,
): boolean {
  if (!setup) return false;
  const { mounting_scope } = hydrateMountingScopeFromFinishSetup(setup);
  if (!isMountingPreparationActive(mounting_scope)) return false;
  const solution = resolveEffectiveMountingSolution(setup);
  return solution?.template_code === METAL_PREMOUNT_TEMPLATE_CODE;
}

export function mountingSolutionSelectorValue(
  setup: Record<string, unknown> | null | undefined,
): MountingSolutionSelectorValue {
  const solution = resolveEffectiveMountingSolution(setup);
  if (!solution) return "";
  if (solution.template_code === METAL_PREMOUNT_TEMPLATE_CODE) {
    return METAL_PREMOUNT_TEMPLATE_CODE;
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
      configuration: normalizeMetalMountingConfiguration(configuration),
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
