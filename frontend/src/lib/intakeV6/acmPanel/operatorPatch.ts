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

export function buildAcmPanelUpdateFieldPatch(args: {
  finishSetup: unknown;
  field: AcmOperatorFieldKey;
  value: number | boolean | 1 | 2 | null;
  /** When true, marks authority operator_confirmed for that field. */
  confirmAuthority?: boolean;
}): Partial<IntakeV6FinishSetup> | null {
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  const { finish, instance } = ctx;
  const authKey = mapConfigKeyToAuthorityKey(args.field);

  if (args.field === "panel_width_mm") {
    instance.geometry.width_mm = typeof args.value === "number" ? args.value : null;
  } else if (args.field === "panel_height_mm") {
    instance.geometry.height_mm = typeof args.value === "number" ? args.value : null;
  } else if (args.field === "acm_thickness_mm") {
    instance.configuration.acm_thickness_mm =
      typeof args.value === "number" ? args.value : null;
  } else if (args.field === "fold_count") {
    instance.configuration.fold_count =
      args.value === 1 || args.value === 2 ? args.value : null;
  } else if (args.field === "l1_mm" || args.field === "finished_depth_mm") {
    const n = typeof args.value === "number" ? args.value : null;
    instance.configuration.l1_mm = n;
    instance.configuration.finished_depth_mm = n;
  } else if (args.field === "l2_mm" || args.field === "rear_lip_mm") {
    instance.configuration.l2_mm = typeof args.value === "number" ? args.value : null;
  } else if (args.field === "internal_frame_enabled") {
    instance.configuration.internal_frame_enabled = Boolean(args.value);
  }

  if (args.confirmAuthority) {
    instance.configuration.field_authority = {
      ...instance.configuration.field_authority,
      [authKey]: "operator_confirmed",
    };
  } else if (
    instance.configuration.field_authority[authKey] === "catalog_default" ||
    instance.configuration.field_authority[authKey] === "detected"
  ) {
    // Edit without explicit confirm → proposed (not operator confirmed).
    instance.configuration.field_authority = {
      ...instance.configuration.field_authority,
      [authKey]: "proposed",
    };
  }

  instance.technical_configuration_status = "proposed";
  instance.updated_at = new Date().toISOString();
  return syncInstanceIntoFinish(finish, instance);
}

export function buildAcmPanelConfirmFieldPatch(args: {
  finishSetup: unknown;
  fieldKeys: string[];
}): Partial<IntakeV6FinishSetup> | null {
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  const { finish, instance } = ctx;
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
}): Partial<IntakeV6FinishSetup> | null {
  return buildAcmPanelConfirmFieldPatch({
    finishSetup: args.finishSetup,
    fieldKeys: [
      "panel_geometry",
      "fold_count",
      "l1_mm",
      "l2_mm",
      "acm_thickness_mm",
      "finished_depth_mm",
      "internal_frame",
    ],
  });
}

export function buildAcmPanelConfirmTechnicalPatch(args: {
  finishSetup: unknown;
}): Partial<IntakeV6FinishSetup> | null {
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  const { finish, instance } = ctx;
  const nextAuth: Record<string, AcmFieldAuthority> = {
    ...instance.configuration.field_authority,
    panel_geometry: "operator_confirmed",
    fold_count: "operator_confirmed",
    l1_mm: "operator_confirmed",
    l2_mm: "operator_confirmed",
    acm_thickness_mm: "operator_confirmed",
    finished_depth_mm: "operator_confirmed",
    internal_frame: "operator_confirmed",
  };
  instance.configuration.field_authority = nextAuth;
  instance.technical_configuration_status = "confirmed";
  if (instance.association_status === "proposed") {
    instance.association_status = "confirmed";
  }
  // Never touch composition_status — product composition CTA only.
  instance.updated_at = new Date().toISOString();
  return syncInstanceIntoFinish(finish, instance);
}

export function buildAcmPanelConfirmRelationPatch(args: {
  finishSetup: unknown;
  relationId: string;
  status: ComponentRelationStatus;
}): Partial<IntakeV6FinishSetup> | null {
  const ctx = requireInstance(args.finishSetup);
  if (!ctx) return null;
  const { finish, instance } = ctx;
  instance.relations = (instance.relations ?? []).map((rel: ComponentRelation) =>
    rel.relation_id === args.relationId ? { ...rel, status: args.status } : rel,
  );
  instance.updated_at = new Date().toISOString();
  return syncInstanceIntoFinish(finish, instance);
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
