/**
 * LetterGroupInstance authority — write SoT for volumetric letter groups.
 * Legacy letter_group_finishes is one-way projection for old consumers.
 * Operator UI must not display instance_id / provenance / drift.
 */

import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import {
  DEFAULT_RETURN_DEPTH_MM,
  deriveLetterGroupsFromAnalyzer,
  type IntakeV4LetterGroupFinish,
  letterGroupFinishesFromPayload,
  mergeLetterGroupFinishes,
  normalizeLetterGroupFaceRollWidth,
} from "./intakeV4LetterGroups";

export const LETTER_GROUP_INSTANCE_SCHEMA = "volumetric_letter_group_instance_v1" as const;
export const COMPONENT_PLACEMENT_SCHEMA = "component_placement_v1" as const;

export type LetterGroupLighting = {
  illuminated: boolean;
  lighting_system_type: string | null;
  light_color: string | null;
  led_module_count: number | null;
  selected_psu_watts: number | null;
};

export type LetterGroupInstance = {
  schema: typeof LETTER_GROUP_INSTANCE_SCHEMA;
  instance_id: string;
  group_key: string;
  layer_name: string;
  source_layer_ids: string[];
  artwork_reference: {
    layer_key: string;
    source_svg_hash: string | null;
    binding_id: string | null;
  };
  geometry: {
    face_area_m2: number | null;
    perimeter_m: number | null;
    element_count: number | null;
    source_fill_color: string | null;
  };
  construction: { return_depth_mm: number | null };
  materials: {
    face_finish_type: string;
    face_oracal_code: string | null;
    face_oracal_name: string | null;
    face_vinyl_roll_width_mm: number | null;
    return_finish_type: string;
    return_oracal_code: string | null;
    return_oracal_name: string | null;
    backing_mode: IntakeV4LetterGroupFinish["backing_mode"];
  };
  finish: {
    face_finish_type: string;
    return_finish_type: string;
    backing_mode: IntakeV4LetterGroupFinish["backing_mode"];
  };
  lighting: LetterGroupLighting;
  confirmed: boolean;
  provenance: {
    source: "instance" | "hydrated_legacy" | "analysis";
    geometry_drift: string | null;
  };
};

export type ComponentPlacement = {
  schema: typeof COMPONENT_PLACEMENT_SCHEMA;
  placement_id: string;
  source_instance_id: string;
  target_kind: "wall" | "acm_panel" | "metal_frame" | "totem_face" | "none";
  target_instance_id: string | null;
  target_face: "A" | "B" | null;
  mounting_method: string | null;
};

/** Extended finish row carrying authority fields in memory (stripped on legacy projection). */
export type LetterGroupFinishWithAuthority = IntakeV4LetterGroupFinish & {
  instance_id?: string;
  lighting?: LetterGroupLighting;
  geometry_drift?: string | null;
};

function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `lg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

function asObject(value: unknown): Record<string, unknown> | null {
  if (value != null && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

export function workspaceLightingFromFinish(finish: Record<string, unknown> | null | undefined): LetterGroupLighting {
  const f = finish ?? {};
  // Copy flags/system once; leave led_module_count unset so workspace total
  // remains the quantity fallback (avoids N× double-count on hydrate).
  return {
    illuminated: f.illuminated !== false,
    lighting_system_type: typeof f.lighting_system_type === "string" ? f.lighting_system_type : null,
    light_color: typeof f.light_color === "string" ? f.light_color : null,
    led_module_count: null,
    selected_psu_watts: typeof f.selected_psu_watts === "number" ? f.selected_psu_watts : null,
  };
}

export function readLetterGroupInstances(finish: Record<string, unknown> | null | undefined): LetterGroupInstance[] {
  const raw = finish?.letter_group_instances;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((row): row is Record<string, unknown> => row != null && typeof row === "object")
    .map((row) => row as unknown as LetterGroupInstance)
    .filter((row) => Boolean(row.instance_id && row.group_key));
}

export function projectInstanceToLegacyFinish(instance: LetterGroupInstance): IntakeV4LetterGroupFinish {
  return normalizeLetterGroupFaceRollWidth({
    group_key: instance.group_key,
    layer_name: instance.layer_name || instance.group_key,
    source_fill_color: instance.geometry.source_fill_color,
    face_area_m2: instance.geometry.face_area_m2,
    perimeter_m: instance.geometry.perimeter_m,
    element_count: instance.geometry.element_count,
    face_finish_type: instance.materials.face_finish_type,
    face_oracal_code: instance.materials.face_oracal_code,
    face_oracal_name: instance.materials.face_oracal_name,
    return_finish_type: instance.materials.return_finish_type,
    return_oracal_code: instance.materials.return_oracal_code,
    return_oracal_name: instance.materials.return_oracal_name,
    return_depth_mm: instance.construction.return_depth_mm,
    face_vinyl_roll_width_mm: instance.materials.face_vinyl_roll_width_mm,
    backing_mode: instance.materials.backing_mode,
    confirmed: instance.confirmed,
  });
}

export function legacyFinishToInstance(
  row: LetterGroupFinishWithAuthority,
  options: { finish: Record<string, unknown>; svgHash: string | null },
): LetterGroupInstance {
  const { finish, svgHash } = options;
  const groupKey = String(row.group_key || "");
  return {
    schema: LETTER_GROUP_INSTANCE_SCHEMA,
    instance_id: row.instance_id || newId(),
    group_key: groupKey,
    layer_name: row.layer_name || groupKey,
    source_layer_ids: groupKey ? [groupKey] : [],
    artwork_reference: {
      layer_key: groupKey,
      source_svg_hash: svgHash,
      binding_id: null,
    },
    geometry: {
      face_area_m2: row.face_area_m2 ?? null,
      perimeter_m: row.perimeter_m ?? null,
      element_count: row.element_count ?? null,
      source_fill_color: row.source_fill_color ?? null,
    },
    construction: { return_depth_mm: row.return_depth_mm ?? null },
    materials: {
      face_finish_type: row.face_finish_type,
      face_oracal_code: row.face_oracal_code ?? null,
      face_oracal_name: row.face_oracal_name ?? null,
      face_vinyl_roll_width_mm: row.face_vinyl_roll_width_mm ?? null,
      return_finish_type: row.return_finish_type,
      return_oracal_code: row.return_oracal_code ?? null,
      return_oracal_name: row.return_oracal_name ?? null,
      backing_mode: row.backing_mode ?? null,
    },
    finish: {
      face_finish_type: row.face_finish_type,
      return_finish_type: row.return_finish_type,
      backing_mode: row.backing_mode ?? null,
    },
    lighting: row.lighting ?? workspaceLightingFromFinish(finish),
    confirmed: row.confirmed === true,
    provenance: {
      source: row.instance_id ? "instance" : "hydrated_legacy",
      geometry_drift: row.geometry_drift ?? null,
    },
  };
}

/**
 * Merge derived analysis rows with authority (instances or legacy).
 * Preserves UUID + confirmed commercial fields across fill drift.
 */
export function mergeLetterGroupsPreservingAuthority(
  derived: IntakeV4LetterGroupFinish[],
  priorRows: LetterGroupFinishWithAuthority[],
): LetterGroupFinishWithAuthority[] {
  const priorByKey = new Map(priorRows.map((row) => [row.group_key, row]));
  const merged = derived.map((item) => {
    const prior = priorByKey.get(item.group_key);
    if (!prior) {
      return { ...item, instance_id: newId(), geometry_drift: null };
    }
    const sameFill =
      prior.source_fill_color == null ||
      item.source_fill_color == null ||
      prior.source_fill_color.trim().toLowerCase() === item.source_fill_color.trim().toLowerCase();
    const drift =
      !sameFill && prior.confirmed
        ? `source_fill_changed:${prior.source_fill_color}->${item.source_fill_color}`
        : prior.geometry_drift ?? null;
    // Confirmed commercial fields survive re-analysis / fill drift.
    const keepCommercial = prior.confirmed === true || sameFill;
    return normalizeLetterGroupFaceRollWidth({
      ...item,
      instance_id: prior.instance_id || newId(),
      face_finish_type: keepCommercial ? prior.face_finish_type ?? item.face_finish_type : item.face_finish_type,
      face_oracal_code: keepCommercial ? prior.face_oracal_code : item.face_oracal_code,
      face_oracal_name: keepCommercial ? prior.face_oracal_name : item.face_oracal_name,
      return_finish_type: keepCommercial ? prior.return_finish_type ?? item.return_finish_type : item.return_finish_type,
      return_oracal_code: keepCommercial ? prior.return_oracal_code : item.return_oracal_code,
      return_oracal_name: keepCommercial ? prior.return_oracal_name : item.return_oracal_name,
      return_depth_mm: keepCommercial ? prior.return_depth_mm ?? item.return_depth_mm : item.return_depth_mm,
      face_vinyl_roll_width_mm: keepCommercial
        ? prior.face_vinyl_roll_width_mm ?? item.face_vinyl_roll_width_mm
        : item.face_vinyl_roll_width_mm,
      backing_mode: keepCommercial ? prior.backing_mode ?? item.backing_mode : item.backing_mode,
      confirmed: keepCommercial ? prior.confirmed : false,
      lighting: prior.lighting,
      geometry_drift: drift,
    });
  });
  // Confirmed orphans (group_key left analysis) stay until operator deletes — join is by key, not index.
  const derivedKeys = new Set(derived.map((row) => row.group_key));
  const orphans = priorRows
    .filter((row) => row.confirmed && row.group_key && !derivedKeys.has(row.group_key))
    .map((row) => ({
      ...row,
      geometry_drift: row.geometry_drift ?? `orphaned_group_key:${row.group_key}`,
    }));
  return [...merged, ...orphans];
}

export function authorityRowsFromFinishSetup(
  finish: Record<string, unknown> | null | undefined,
): LetterGroupFinishWithAuthority[] {
  const instances = readLetterGroupInstances(finish);
  if (instances.length) {
    return instances.map((inst) => ({
      ...projectInstanceToLegacyFinish(inst),
      instance_id: inst.instance_id,
      lighting: inst.lighting,
      geometry_drift: inst.provenance?.geometry_drift ?? null,
    }));
  }
  const legacy = letterGroupFinishesFromPayload({ finish_setup: finish ?? {} });
  const lighting = workspaceLightingFromFinish(finish);
  return legacy.map((row) => ({
    ...row,
    instance_id: newId(),
    lighting,
    geometry_drift: null,
  }));
}

/** Resolve letter groups for Review: derive + authority merge (no new Review state). */
export function resolveLetterGroupsForReview(args: {
  report: SvgAnalysisCoreReport | null | undefined;
  confirmation: LayerRoleConfirmation | null | undefined;
  payload: Record<string, unknown> | undefined;
  defaultReturnDepthMm?: number;
}): LetterGroupFinishWithAuthority[] {
  const finish = asObject(args.payload?.finish_setup) ?? {};
  const derived = deriveLetterGroupsFromAnalyzer(
    args.report,
    args.confirmation,
    args.defaultReturnDepthMm ?? DEFAULT_RETURN_DEPTH_MM,
  );
  const prior = authorityRowsFromFinishSetup(finish);
  if (!derived.length && prior.length) {
    // Keep authority rows when analyzer not ready yet.
    return prior;
  }
  return mergeLetterGroupsPreservingAuthority(derived, prior);
}

export function buildLetterGroupInstancesFromRows(
  rows: LetterGroupFinishWithAuthority[],
  finish: Record<string, unknown>,
  svgHash: string | null,
): LetterGroupInstance[] {
  return rows
    .filter((row) => row.group_key)
    .map((row) => legacyFinishToInstance(row, { finish, svgHash }));
}

export function ensurePlacementsForInstances(
  instances: LetterGroupInstance[],
  finish: Record<string, unknown>,
  existingPlacements?: ComponentPlacement[] | null,
): ComponentPlacement[] {
  if (existingPlacements?.length) return existingPlacements;
  const acm = asObject(finish.acm_panel_instance);
  const acmId = acm && typeof acm.component_instance_id === "string" ? acm.component_instance_id : null;
  return instances.map((inst) => ({
    schema: COMPONENT_PLACEMENT_SCHEMA,
    placement_id: newId(),
    source_instance_id: inst.instance_id,
    target_kind: acmId ? "acm_panel" : "none",
    target_instance_id: acmId,
    target_face: null,
    mounting_method: null,
  }));
}

/**
 * Attach authority arrays onto a finish body for autosave.
 * Projects legacy letter_group_finishes without authority-only keys.
 */
export function attachLetterAuthorityToFinishBody<T extends Record<string, unknown>>(
  finishBody: T,
  letterGroups: LetterGroupFinishWithAuthority[],
  payload?: Record<string, unknown>,
): T & {
  letter_group_instances: LetterGroupInstance[];
  letter_group_finishes: IntakeV4LetterGroupFinish[];
  component_placements: ComponentPlacement[];
} {
  const svgSource = asObject(payload?.svg_source);
  const svgHash = typeof svgSource?.file_hash === "string" ? svgSource.file_hash : null;
  const existingFinish = asObject(payload?.finish_setup) ?? {};
  const priorInstances = readLetterGroupInstances(existingFinish);
  const priorByKey = new Map(priorInstances.map((i) => [i.group_key, i]));

  const rows = letterGroups.map((row) => {
    const prior = priorByKey.get(row.group_key);
    return {
      ...row,
      instance_id: row.instance_id || prior?.instance_id || newId(),
      lighting: row.lighting ?? prior?.lighting ?? workspaceLightingFromFinish(finishBody),
    };
  });

  const instances = buildLetterGroupInstancesFromRows(rows, finishBody, svgHash);
  const existingPlacements = Array.isArray(existingFinish.component_placements)
    ? (existingFinish.component_placements as ComponentPlacement[])
    : null;
  const placements = ensurePlacementsForInstances(instances, finishBody, existingPlacements);
  const legacy = instances.map(projectInstanceToLegacyFinish);

  return {
    ...finishBody,
    letter_group_instances: instances,
    letter_group_finishes: legacy,
    component_placements: placements,
  };
}

/** @deprecated Prefer resolveLetterGroupsForReview — kept for call-site clarity. */
export function mergeLetterGroupFinishesCompat(
  derived: IntakeV4LetterGroupFinish[],
  saved: IntakeV4LetterGroupFinish[] | undefined,
): IntakeV4LetterGroupFinish[] {
  return mergeLetterGroupFinishes(derived, saved);
}
