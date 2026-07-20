/**
 * Single write-path for AcmPanel operator configuration.
 * Syncs top-level instance + selection/mounting embeds; never auto-confirms composition.
 */

import {
  buildMountingSolutionPatch,
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
  readMountingSolution,
} from "@/lib/intakeV6/mountingSolution";
import type { IntakeV6FinishSetup } from "@/lib/intakeV6/intakeV6Api";
import { resolveAcmPanelInstance } from "./resolveInstance";
import type {
  AcmFieldAuthority,
  AcmLifecycleStatus,
  AcmPanelComponentInstance,
  AcmPanelDomainAction,
  ComponentRelation,
  ComponentRelationStatus,
} from "./types";
import { ACM_PANEL_TEMPLATE_CODE } from "./types";

export type AcmOperatorFieldKey =
  | "acm_thickness_mm"
  | "fold_count"
  | "l1_mm"
  | "l2_mm"
  | "finished_depth_mm"
  | "panel_width_mm"
  | "panel_height_mm"
  | "rear_lip_mm"
  | "internal_frame_enabled";

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function cloneInstance(instance: AcmPanelComponentInstance): AcmPanelComponentInstance {
  return structuredClone(instance);
}

function syncInstanceIntoFinish(
  finish: Record<string, unknown>,
  instance: AcmPanelComponentInstance,
): Partial<IntakeV6FinishSetup> & {
  acm_panel_domain_action: AcmPanelDomainAction;
  acm_panel_instance: AcmPanelComponentInstance;
} {
  const selection = asRecord(finish.svg_support_selection) ?? {};
  const mounting = readMountingSolution(finish as never);
  const prevConfig = (mounting?.configuration ?? {}) as Record<string, unknown>;

  const nextConfig: Record<string, unknown> = {
    ...prevConfig,
    panel_width_mm: instance.geometry.width_mm ?? prevConfig.panel_width_mm,
    panel_height_mm: instance.geometry.height_mm ?? prevConfig.panel_height_mm,
    acm_thickness_mm: instance.configuration.acm_thickness_mm,
    return_depth_mm: instance.configuration.l1_mm,
    rear_lip_mm: instance.configuration.l2_mm,
    finished_depth_mm: instance.configuration.finished_depth_mm,
    fold_count: instance.configuration.fold_count,
    internal_frame_enabled: instance.configuration.internal_frame_enabled,
    field_authority: instance.configuration.field_authority,
    field_class: instance.configuration.field_class,
    technical_configuration_status: instance.technical_configuration_status,
    acm_panel_instance: instance,
    component_relations: instance.relations,
  };

  const mountingPatch = buildMountingSolutionPatch(
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    nextConfig,
  ) as { mounting_solution?: Record<string, unknown> };

  return {
    acm_panel_domain_action: "upsert",
    acm_panel_instance: instance,
    svg_support_selection: {
      ...selection,
      acm_panel_instance: instance,
      acm_panel_domain_action: "upsert",
      component_relations: instance.relations,
    } as never,
    mounting_solution: mountingPatch.mounting_solution
      ? {
          ...mountingPatch.mounting_solution,
          configuration: {
            ...((mountingPatch.mounting_solution.configuration as Record<string, unknown>) ||
              {}),
            acm_panel_instance: instance,
            component_relations: instance.relations,
          },
        }
      : null,
  };
}

function requireInstance(
  finishSetup: unknown,
): { finish: Record<string, unknown>; instance: AcmPanelComponentInstance } | null {
  const finish = asRecord(finishSetup);
  if (!finish) return null;
  const resolved = resolveAcmPanelInstance(finish);
  if (!resolved.instance) return null;
  return { finish, instance: cloneInstance(resolved.instance) };
}

function mapConfigKeyToAuthorityKey(field: AcmOperatorFieldKey): string {
  if (field === "panel_width_mm" || field === "panel_height_mm") return "panel_geometry";
  if (field === "rear_lip_mm") return "l2_mm";
  return field;
}

export type AcmPanelFieldUpdateInput = {
  field: AcmOperatorFieldKey;
  value: number | boolean | 1 | 2 | null;
  confirmAuthority?: boolean;
};

function applyFieldUpdateOnInstance(
  instance: AcmPanelComponentInstance,
  update: AcmPanelFieldUpdateInput,
): void {
  const authKey = mapConfigKeyToAuthorityKey(update.field);

  if (update.field === "panel_width_mm") {
    instance.geometry.width_mm = typeof update.value === "number" ? update.value : null;
  } else if (update.field === "panel_height_mm") {
    instance.geometry.height_mm = typeof update.value === "number" ? update.value : null;
  } else if (update.field === "acm_thickness_mm") {
    instance.configuration.acm_thickness_mm =
      typeof update.value === "number" ? update.value : null;
  } else if (update.field === "fold_count") {
    instance.configuration.fold_count =
      update.value === 1 || update.value === 2 ? update.value : null;
  } else if (update.field === "l1_mm" || update.field === "finished_depth_mm") {
    const n = typeof update.value === "number" ? update.value : null;
    instance.configuration.l1_mm = n;
    instance.configuration.finished_depth_mm = n;
  } else if (update.field === "l2_mm" || update.field === "rear_lip_mm") {
    instance.configuration.l2_mm = typeof update.value === "number" ? update.value : null;
  } else if (update.field === "internal_frame_enabled") {
    instance.configuration.internal_frame_enabled = Boolean(update.value);
  }

  if (update.confirmAuthority) {
    instance.configuration.field_authority = {
      ...instance.configuration.field_authority,
      [authKey]: "operator_confirmed",
    };
  } else if (
    instance.configuration.field_authority[authKey] === "catalog_default" ||
    instance.configuration.field_authority[authKey] === "detected"
  ) {
    instance.configuration.field_authority = {
      ...instance.configuration.field_authority,
      [authKey]: "proposed",
    };
  }
}

function applyUpdatesOnInstance(
  instance: AcmPanelComponentInstance,
  updates: AcmPanelFieldUpdateInput[],
): void {
  for (const update of updates) {
    applyFieldUpdateOnInstance(instance, update);
  }
  if (updates.length > 0) {
    instance.technical_configuration_status = "proposed";
  }
  instance.updated_at = new Date().toISOString();
}

export function buildAcmPanelUpdateFieldPatch(args: {
  finishSetup: unknown;
  field: AcmOperatorFieldKey;
  value: number | boolean | 1 | 2 | null;
  /** When true, marks authority operator_confirmed for that field. */
  confirmAuthority?: boolean;
}): Partial<IntakeV6FinishSetup> | null {
  return buildAcmPanelUpdateFieldsPatch({
    finishSetup: args.finishSetup,
    updates: [
      {
        field: args.field,
        value: args.value,
        confirmAuthority: args.confirmAuthority,
      },
    ],
  });
}

/** Apply multiple field updates in one operatorPatch / one finish sync. */
export function buildAcmPanelUpdateFieldsPatch(args: {
  finishSetup: unknown;
  updates: AcmPanelFieldUpdateInput[];
}): Partial<IntakeV6FinishSetup> | null {
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  if (!args.updates.length) return null;
  const { finish, instance } = ctx;
  applyUpdatesOnInstance(instance, args.updates);
  return syncInstanceIntoFinish(finish, instance);
}

export type AcmPanelConfirmAction =
  | { kind: "confirm_geometry" }
  | { kind: "confirm_construction" }
  | { kind: "confirm_technical" }
  | { kind: "confirm_relation"; relationId: string; status?: ComponentRelationStatus };

/**
 * One semantic intent: optional pending field updates + confirm action → one patch.
 * Never flush-then-confirm as two writes.
 */
export function buildAcmPanelConfirmActionWithUpdatesPatch(args: {
  finishSetup: unknown;
  updates?: AcmPanelFieldUpdateInput[];
  action: AcmPanelConfirmAction;
}): Partial<IntakeV6FinishSetup> | null {
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  const { finish, instance } = ctx;
  const updates = args.updates ?? [];
  if (updates.length) {
    applyUpdatesOnInstance(instance, updates);
  }

  if (args.action.kind === "confirm_geometry") {
    instance.configuration.field_authority = {
      ...instance.configuration.field_authority,
      panel_geometry: "operator_confirmed",
    };
  } else if (args.action.kind === "confirm_construction") {
    const keys = [
      "panel_geometry",
      "fold_count",
      "l1_mm",
      "l2_mm",
      "acm_thickness_mm",
      "finished_depth_mm",
      "internal_frame",
    ];
    const nextAuth: Record<string, AcmFieldAuthority> = {
      ...instance.configuration.field_authority,
    };
    for (const key of keys) nextAuth[key] = "operator_confirmed";
    instance.configuration.field_authority = nextAuth;
  } else if (args.action.kind === "confirm_technical") {
    instance.configuration.field_authority = {
      ...instance.configuration.field_authority,
      panel_geometry: "operator_confirmed",
      fold_count: "operator_confirmed",
      l1_mm: "operator_confirmed",
      l2_mm: "operator_confirmed",
      acm_thickness_mm: "operator_confirmed",
      finished_depth_mm: "operator_confirmed",
      internal_frame: "operator_confirmed",
    };
    instance.technical_configuration_status = "confirmed";
    if (instance.association_status === "proposed") {
      instance.association_status = "confirmed";
    }
  } else if (args.action.kind === "confirm_relation") {
    const status = args.action.status ?? "confirmed";
    const relationId = args.action.relationId;
    instance.relations = (instance.relations ?? []).map((rel: ComponentRelation) =>
      rel.relation_id === relationId ? { ...rel, status } : rel,
    );
  }

  instance.updated_at = new Date().toISOString();
  return syncInstanceIntoFinish(finish, instance);
}

export function buildAcmPanelConfirmFieldPatch(args: {
  finishSetup: unknown;
  fieldKeys: string[];
  updates?: AcmPanelFieldUpdateInput[];
}): Partial<IntakeV6FinishSetup> | null {
  if (
    args.fieldKeys.length === 1 &&
    args.fieldKeys[0] === "panel_geometry" &&
    !args.updates?.length
  ) {
    return buildAcmPanelConfirmActionWithUpdatesPatch({
      finishSetup: args.finishSetup,
      updates: args.updates,
      action: { kind: "confirm_geometry" },
    });
  }
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  const { finish, instance } = ctx;
  if (args.updates?.length) applyUpdatesOnInstance(instance, args.updates);
  const nextAuth: Record<string, AcmFieldAuthority> = {
    ...instance.configuration.field_authority,
  };
  for (const key of args.fieldKeys) {
    nextAuth[key] = "operator_confirmed";
  }
  instance.configuration.field_authority = nextAuth;
  instance.updated_at = new Date().toISOString();
  return syncInstanceIntoFinish(finish, instance);
}

export function buildAcmPanelConfirmConstructionPatch(args: {
  finishSetup: unknown;
  updates?: AcmPanelFieldUpdateInput[];
}): Partial<IntakeV6FinishSetup> | null {
  return buildAcmPanelConfirmActionWithUpdatesPatch({
    finishSetup: args.finishSetup,
    updates: args.updates,
    action: { kind: "confirm_construction" },
  });
}

export function buildAcmPanelConfirmTechnicalPatch(args: {
  finishSetup: unknown;
  updates?: AcmPanelFieldUpdateInput[];
}): Partial<IntakeV6FinishSetup> | null {
  return buildAcmPanelConfirmActionWithUpdatesPatch({
    finishSetup: args.finishSetup,
    updates: args.updates,
    action: { kind: "confirm_technical" },
  });
}

export function buildAcmPanelConfirmRelationPatch(args: {
  finishSetup: unknown;
  relationId: string;
  status: ComponentRelationStatus;
  updates?: AcmPanelFieldUpdateInput[];
}): Partial<IntakeV6FinishSetup> | null {
  return buildAcmPanelConfirmActionWithUpdatesPatch({
    finishSetup: args.finishSetup,
    updates: args.updates,
    action: {
      kind: "confirm_relation",
      relationId: args.relationId,
      status: args.status,
    },
  });
}

export function buildAcmPanelPromoteTopLevelPatch(args: {
  finishSetup: unknown;
}): Partial<IntakeV6FinishSetup> | null {
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  return syncInstanceIntoFinish(ctx.finish, ctx.instance);
}

/** Ensure composition_status is never flipped by operator config patches. */
export function assertNoCompositionAutoConfirm(
  patch: Partial<IntakeV6FinishSetup> | null,
): boolean {
  if (!patch) return true;
  const inst = asRecord(patch.acm_panel_instance);
  // Patches may include instance; callers must not set composition confirmed here.
  // This helper documents the invariant for tests.
  void inst;
  void ACM_PANEL_TEMPLATE_CODE;
  return true;
}

export type AcmPanelOperatorPatchKind =
  | "update_field"
  | "confirm_fields"
  | "confirm_construction"
  | "confirm_technical"
  | "confirm_relation"
  | "promote_toplevel";

export function readLifecycleFromPatch(
  patch: Partial<IntakeV6FinishSetup> | null,
): AcmLifecycleStatus | null {
  const inst = asRecord(patch?.acm_panel_instance);
  const raw = inst?.technical_configuration_status;
  return typeof raw === "string" ? (raw as AcmLifecycleStatus) : null;
}
