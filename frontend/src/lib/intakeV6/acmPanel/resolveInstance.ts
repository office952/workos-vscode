/**
 * Coalesce AcmPanelComponentInstance from finish_setup projections.
 * Canonical order matches ProductDefinition builder.
 */

import type { AcmPanelComponentInstance } from "./types";
import { ACM_PANEL_INSTANCE_SCHEMA } from "./types";

export type AcmPanelInstanceSource =
  | "finish_setup.acm_panel_instance"
  | "svg_support_selection.acm_panel_instance"
  | "mounting_solution.configuration.acm_panel_instance"
  | "none";

export type ResolveAcmPanelInstanceResult = {
  instance: AcmPanelComponentInstance | null;
  source: AcmPanelInstanceSource;
  /** True when multiple projections exist and disagree on identity or status axes. */
  inconsistent: boolean;
  inconsistencyNotes: string[];
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function readFinish(finishSetup: unknown): Record<string, unknown> | null {
  return asRecord(finishSetup);
}

export function isAcmPanelComponentInstance(
  value: unknown,
): value is AcmPanelComponentInstance {
  const rec = asRecord(value);
  if (!rec) return false;
  if (String(rec.schema ?? "") !== ACM_PANEL_INSTANCE_SCHEMA) return false;
  if (!String(rec.component_instance_id ?? "").trim()) return false;
  return true;
}

function axisSnapshot(inst: AcmPanelComponentInstance): string {
  return [
    inst.component_instance_id,
    inst.role_status,
    inst.association_status,
    inst.technical_configuration_status,
    inst.composition_status,
  ].join("|");
}

/**
 * Resolve instance with controlled fallback. Never invents confirmed state.
 */
export function resolveAcmPanelInstance(
  finishSetup: unknown,
): ResolveAcmPanelInstanceResult {
  const finish = readFinish(finishSetup);
  if (!finish) {
    return {
      instance: null,
      source: "none",
      inconsistent: false,
      inconsistencyNotes: [],
    };
  }

  const top = isAcmPanelComponentInstance(finish.acm_panel_instance)
    ? finish.acm_panel_instance
    : null;

  const selection = asRecord(finish.svg_support_selection);
  const selectionInst = isAcmPanelComponentInstance(selection?.acm_panel_instance)
    ? selection.acm_panel_instance
    : null;

  const mounting = asRecord(finish.mounting_solution);
  const mountingConfig = asRecord(mounting?.configuration);
  const mountingInst = isAcmPanelComponentInstance(mountingConfig?.acm_panel_instance)
    ? mountingConfig.acm_panel_instance
    : null;

  const notes: string[] = [];
  const present = [
    top ? ("top" as const) : null,
    selectionInst ? ("selection" as const) : null,
    mountingInst ? ("mounting" as const) : null,
  ].filter(Boolean) as Array<"top" | "selection" | "mounting">;

  if (present.length > 1) {
    const snaps = [
      top ? axisSnapshot(top) : null,
      selectionInst ? axisSnapshot(selectionInst) : null,
      mountingInst ? axisSnapshot(mountingInst) : null,
    ].filter(Boolean) as string[];
    const unique = new Set(snaps);
    if (unique.size > 1) {
      notes.push(
        "Multiple AcmPanel projections disagree on identity or status axes — using canonical coalesce order; not inventing Confirmed.",
      );
    }
  }

  if (top) {
    return {
      instance: top,
      source: "finish_setup.acm_panel_instance",
      inconsistent: notes.length > 0,
      inconsistencyNotes: notes,
    };
  }
  if (selectionInst) {
    return {
      instance: selectionInst,
      source: "svg_support_selection.acm_panel_instance",
      inconsistent: notes.length > 0 || Boolean(mountingInst),
      inconsistencyNotes: notes.length
        ? notes
        : mountingInst
          ? ["Top-level instance missing; using selection embed (mounting also has embed)."]
          : ["Top-level instance missing; using selection embed."],
    };
  }
  if (mountingInst) {
    return {
      instance: mountingInst,
      source: "mounting_solution.configuration.acm_panel_instance",
      inconsistent: true,
      inconsistencyNotes: [
        "Top-level and selection instance missing; using mounting nest only.",
      ],
    };
  }

  return {
    instance: null,
    source: "none",
    inconsistent: false,
    inconsistencyNotes: [],
  };
}
