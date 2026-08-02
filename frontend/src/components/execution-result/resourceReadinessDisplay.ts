/**
 * F7C — display-only mapping for Operational Resource Readiness.
 *
 * Pure functions only: no computation of readiness itself. The backend
 * (`operational_resource_readiness_service.py`) is the sole authority for
 * `status` / `resource_requirement_mode` / candidate lists — this module
 * only translates those backend-owned values into Romanian labels and a
 * visual tone for the compact read-only panel.
 */
import type { ResourceReadinessStatus } from "@/api/execution";

export type ResourceReadinessTone = "success" | "warning" | "danger" | "neutral";

const STATUS_LABELS: Record<ResourceReadinessStatus, string> = {
  ready: "Pregătit",
  ready_with_warnings: "Pregătit (cu atenționări)",
  missing_workcenter: "Punct de lucru lipsă",
  unknown_resource_policy: "Politică de resurse necunoscută",
  machine_required_but_none_compatible: "Utilaj necesar — niciunul compatibil",
  machine_optional_no_candidate: "Utilaj opțional — niciun candidat",
  workcenter_only: "Doar punct de lucru (fără utilaj)",
  machine_unavailable: "Utilaj indisponibil",
  maintenance_conflict: "Conflict mentenanță",
  ambiguous_mapping: "Mapare ambiguă",
};

export function resourceReadinessStatusLabel(status: ResourceReadinessStatus): string {
  return STATUS_LABELS[status] ?? status;
}

export function resourceReadinessStatusTone(status: ResourceReadinessStatus): ResourceReadinessTone {
  switch (status) {
    case "ready":
      return "success";
    case "ready_with_warnings":
    case "workcenter_only":
      return "warning";
    case "missing_workcenter":
    case "unknown_resource_policy":
    case "machine_required_but_none_compatible":
    case "machine_optional_no_candidate":
    case "machine_unavailable":
    case "maintenance_conflict":
    case "ambiguous_mapping":
      return "danger";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

const MODE_LABELS: Record<string, string> = {
  orr_allowlist: "Listă utilaje admise (ORR)",
  workcenter_only: "Doar punct de lucru",
  unknown_resource_policy: "Necunoscută",
};

export function resourceRequirementModeLabel(mode: string): string {
  return MODE_LABELS[mode] ?? mode;
}

const WC_STATUS_LABELS: Record<string, string> = {
  resolved: "Cod canonic",
  non_canonical: "Cod necanonic",
  missing: "Cod necunoscut",
  empty: "Lipsă",
};

export function workcenterRegistryStatusLabel(status: string): string {
  return WC_STATUS_LABELS[status] ?? status;
}
