/** Product System mounting solution reference — Intake V6. */

import {
  hydrateMountingScopeFromFinishSetup,
  isMountingPreparationActive,
  type MountingScopeV1,
} from "@/lib/intakeV6/mountingScope";
import {
  ACM_BOXED_MOUNTING_QUOTE_INPUT_FIELDS,
  ACM_BOXED_MOUNTING_SUPPORTED_THICKNESS_MM,
  deriveAcmCasettedQuoteInput,
  TPL_ACM_BOXED_MOUNTING_SUPPORT,
} from "@/lib/acmQuoteInput";

export const METAL_PREMOUNT_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1";
export const ACM_BOXED_MOUNTING_TEMPLATE_CODE = TPL_ACM_BOXED_MOUNTING_SUPPORT;
export const INSTALLATION_TEMPLATE_KIND = "installation_template" as const;
export const PRODUCT_SYSTEM_TEMPLATE_KIND = "product_system_template" as const;

export type MountingSolutionRef =
  | {
      kind?: typeof PRODUCT_SYSTEM_TEMPLATE_KIND;
      template_code: string;
      configuration: Record<string, unknown>;
    }
  | {
      kind: typeof INSTALLATION_TEMPLATE_KIND;
      template_code: null;
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
  { value: "", label: "Fără soluție suplimentară (șablon montaj)" },
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

export function isInstallationTemplateSolution(
  solution: MountingSolutionRef | Record<string, unknown> | null | undefined,
): boolean {
  if (!solution || typeof solution !== "object") return false;
  return String((solution as { kind?: unknown }).kind ?? "").trim() === INSTALLATION_TEMPLATE_KIND;
}

export function isMountingTemplateFieldsComplete(
  setup: Record<string, unknown> | null | undefined,
): boolean {
  if (!setup) return false;
  if (setup.mounting_template_enabled !== true) return false;
  const area = Number(setup.mounting_template_area_m2);
  if (!Number.isFinite(area) || area <= 0) return false;
  const material = String(setup.mounting_template_material_type ?? "")
    .trim()
    .toLowerCase();
  return material === "forex" || material === "paper";
}

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
  const thickness = Math.round(Number(merged.acm_thickness_mm ?? 3));
  if (
    Number.isFinite(thickness) &&
    ACM_BOXED_MOUNTING_SUPPORTED_THICKNESS_MM.includes(
      thickness as (typeof ACM_BOXED_MOUNTING_SUPPORTED_THICKNESS_MM)[number],
    )
  ) {
    merged.acm_thickness_mm = thickness;
  } else {
    merged.acm_thickness_mm = Number.isFinite(thickness) ? thickness : 3;
  }
  const foldSides = String(merged.fold_sides ?? "all").trim().toLowerCase();
  merged.fold_sides = ["all", "top_bottom", "left_right"].includes(foldSides) ? foldSides : "all";
  const angle = Number(merged.v_groove_angle_deg ?? 135);
  merged.v_groove_angle_deg = Number.isFinite(angle) ? angle : 135;
  if ("internal_frame_enabled" in merged) {
    merged.internal_frame_enabled = Boolean(merged.internal_frame_enabled);
  }
  // Preserve nested internal_frame; do not invent profile codes client-side.
  if (merged.internal_frame && typeof merged.internal_frame === "object") {
    merged.internal_frame = { ...(merged.internal_frame as Record<string, unknown>) };
    merged.internal_frame_enabled = Boolean(
      (merged.internal_frame as { enabled?: unknown }).enabled ?? merged.internal_frame_enabled,
    );
  } else if (merged.internal_frame_enabled) {
    merged.internal_frame = { enabled: true };
  } else {
    merged.internal_frame = { enabled: false };
    merged.internal_frame_enabled = false;
  }
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
  const record = raw as Record<string, unknown>;
  if (String(record.kind ?? "").trim() === INSTALLATION_TEMPLATE_KIND) {
    return {
      kind: INSTALLATION_TEMPLATE_KIND,
      template_code: null,
      configuration:
        record.configuration &&
        typeof record.configuration === "object" &&
        !Array.isArray(record.configuration)
          ? { ...(record.configuration as Record<string, unknown>) }
          : {},
    };
  }
  const templateCode = String(record.template_code ?? "").trim();
  if (!templateCode) return null;
  const configuration =
    record.configuration &&
    typeof record.configuration === "object" &&
    !Array.isArray(record.configuration)
      ? { ...(record.configuration as Record<string, unknown>) }
      : {};
  return {
    kind: PRODUCT_SYSTEM_TEMPLATE_KIND,
    template_code: templateCode,
    configuration,
  };
}

export function hydrateMountingSolutionFromLegacy(
  setup: Record<string, unknown>,
): MountingSolutionRef | null {
  const existing = readMountingSolution(setup);
  if (existing) return existing;
  const mountingSystem = String(setup.mounting_system ?? "").trim();
  if (mountingSystem === ACM_PANEL_LEGACY) {
    return {
      kind: PRODUCT_SYSTEM_TEMPLATE_KIND,
      template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
      configuration: normalizeAcmMountingConfiguration({}),
    };
  }
  if (!BAR_MOUNTING_LEGACY.has(mountingSystem)) return null;
  return {
    kind: PRODUCT_SYSTEM_TEMPLATE_KIND,
    template_code: METAL_PREMOUNT_TEMPLATE_CODE,
    configuration: normalizeMetalMountingConfiguration({
      bar_material: mountingSystem === "aluminum_bars" ? "aluminum" : "steel",
      mounting_bar_profile: setup.mounting_bar_profile,
    }),
  };
}

/**
 * Prefer SVG-confirmed panel geometry over hardcoded ACM defaults (1000×600).
 * Authority: finish_setup.svg_support_selection.panel_geometry / mounting_solution from Step 1.
 */
export function hydrateAcmMountingFromSvgSupport(
  setup: Record<string, unknown> | null | undefined,
): MountingSolutionRef | null {
  if (!setup) return null;
  // Lazy import avoided — read support selection shape directly to keep mountingSolution free of analyzer cycles.
  const raw = setup.svg_support_selection;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const selection = raw as Record<string, unknown>;
  if (String(selection.status ?? "") !== "confirmed") return null;
  if (String(selection.role ?? "") !== "ALUCOBOND_CASED_PANEL") return null;
  const panel = selection.panel_geometry;
  if (!panel || typeof panel !== "object" || Array.isArray(panel)) return null;
  const panelRec = panel as Record<string, unknown>;
  const width = Number(panelRec.width_mm);
  const height = Number(panelRec.height_mm);
  if (!(width > 0) || !(height > 0)) return null;

  const existing = readMountingSolution(setup);
  const existingConfig =
    existing?.template_code === ACM_BOXED_MOUNTING_TEMPLATE_CODE
      ? normalizeAcmMountingConfiguration(existing.configuration)
      : {};
  const existingW = Number(existingConfig.panel_width_mm);
  const existingH = Number(existingConfig.panel_height_mm);
  const looksLikeDefault =
    !existing ||
    existing.template_code !== ACM_BOXED_MOUNTING_TEMPLATE_CODE ||
    (existingW === DEFAULT_ACM_MOUNTING_CONFIGURATION.panel_width_mm &&
      existingH === DEFAULT_ACM_MOUNTING_CONFIGURATION.panel_height_mm);

  if (!looksLikeDefault && existing?.template_code === ACM_BOXED_MOUNTING_TEMPLATE_CODE) {
    // Keep operator overrides when they differ from defaults and from SVG (operator edited).
    const matchesSvg =
      Math.abs(existingW - width) < 0.05 && Math.abs(existingH - height) < 0.05;
    if (!matchesSvg && existingW > 0 && existingH > 0) {
      return existing;
    }
  }

  const casing = selection.casing_profile;
  const casingRec =
    casing && typeof casing === "object" && !Array.isArray(casing)
      ? (casing as Record<string, unknown>)
      : {};
  const fold = Number(casingRec.fold_count ?? existingConfig.fold_count ?? 2) === 1 ? 1 : 2;
  const l1 = Number(casingRec.l1_mm ?? existingConfig.return_depth_mm ?? 60);
  const l2 = Number(casingRec.l2_mm ?? existingConfig.rear_lip_mm ?? 25);

  return {
    kind: PRODUCT_SYSTEM_TEMPLATE_KIND,
    template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    configuration: normalizeAcmMountingConfiguration({
      ...existingConfig,
      panel_width_mm: width,
      panel_height_mm: height,
      return_depth_mm: l1,
      rear_lip_mm: fold === 2 ? l2 : 0,
      fold_count: fold,
      finished_depth_mm: Number(casingRec.finished_depth_mm ?? l1),
      svg_support_element_id: selection.svg_support_element_id ?? null,
      geometry_hash: selection.geometry_hash ?? null,
      contour_id: selection.contour_id ?? null,
      panel_area_mm2: panelRec.area_mm2 ?? null,
      panel_perimeter_mm: panelRec.perimeter_mm ?? null,
      unit_ambiguity: Boolean(selection.unit_ambiguity),
      dimension_source: "svg_support_selection",
      svg_source_hash: selection.svg_source_hash ?? null,
    }),
  };
}

export function resolveEffectiveMountingSolution(
  setup: Record<string, unknown> | null | undefined,
): MountingSolutionRef | null {
  if (!setup) return null;
  const fromSvg = hydrateAcmMountingFromSvgSupport(setup);
  const existing = readMountingSolution(setup);
  if (fromSvg) {
    // Prefer SVG-hydrated ACM when support is confirmed.
    if (!existing || existing.template_code === ACM_BOXED_MOUNTING_TEMPLATE_CODE) {
      return fromSvg;
    }
  }
  return existing ?? hydrateMountingSolutionFromLegacy(setup) ?? fromSvg;
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
  if (!solution || isInstallationTemplateSolution(solution)) return false;
  return isAllowedMountingSolutionTemplate(solution.template_code);
}

export function mountingSolutionSelectorValue(
  setup: Record<string, unknown> | null | undefined,
): MountingSolutionSelectorValue {
  const solution = resolveEffectiveMountingSolution(setup);
  if (!solution) return "";
  if (isInstallationTemplateSolution(solution)) return "";
  if (isAllowedMountingSolutionTemplate(solution.template_code)) {
    return solution.template_code as MountingSolutionSelectorValue;
  }
  return "";
}

export function legacyMountingSystemLabel(
  setup: Record<string, unknown> | null | undefined,
): string {
  const solution = resolveEffectiveMountingSolution(setup);
  if (isInstallationTemplateSolution(solution)) {
    return "direct_wall";
  }
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
  if (solution && !isInstallationTemplateSolution(solution) && solution.template_code === METAL_PREMOUNT_TEMPLATE_CODE) {
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
      mounting_solution: {
        kind: INSTALLATION_TEMPLATE_KIND,
        template_code: null,
        configuration: {},
      },
      mounting_system: null,
      mounting_bar_profile: null,
    };
  }
  return {
    mounting_solution: {
      kind: PRODUCT_SYSTEM_TEMPLATE_KIND,
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
