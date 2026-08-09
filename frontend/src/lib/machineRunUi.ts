/**
 * MachineRun shop-floor UI helpers — display copy + action matrix + error UX.
 * Backend enums and transition rules remain authority.
 */
import type { MachineRunStatus } from "@/api/machineRuns";
import type { Permission, Role } from "@/lib/rbac";
import { can } from "@/lib/rbac";

export const MACHINE_RUN_STATUS_LABEL: Record<MachineRunStatus, string> = {
  HELD: "Grupare",
  RESERVED: "Rezervat",
  RUNNING: "În lucru pe utilaj",
  COMPLETED: "Lucru utilaj finalizat",
  RELEASED: "Eliberat",
  CANCELLED: "Anulat",
  SUPERSEDED: "Înlocuit",
};

export type MachineRunAction =
  | "confirm"
  | "start"
  | "complete"
  | "release"
  | "reschedule"
  | "cancel"
  | "remove_participant";

export type MachineRunActionDef = {
  action: MachineRunAction;
  label: string;
  kind: "primary" | "secondary" | "danger";
  permission: Permission;
};

const ACTION_DEFS: Record<MachineRunAction, Omit<MachineRunActionDef, "action">> = {
  confirm: {
    label: "Confirmă rularea",
    kind: "primary",
    permission: "execution.machine_run.manage",
  },
  start: {
    label: "Pornește utilajul",
    kind: "primary",
    permission: "execution.machine_run.execute",
  },
  complete: {
    label: "Finalizează lucrul pe utilaj",
    kind: "primary",
    permission: "execution.machine_run.execute",
  },
  release: {
    label: "Eliberează utilajul",
    kind: "primary",
    permission: "execution.machine_run.manage",
  },
  reschedule: {
    label: "Reprogramează",
    kind: "secondary",
    permission: "execution.machine_run.manage",
  },
  cancel: {
    label: "Anulează",
    kind: "danger",
    permission: "execution.machine_run.manage",
  },
  remove_participant: {
    label: "Elimină participant",
    kind: "secondary",
    permission: "execution.machine_run.manage",
  },
};

/** Status → lifecycle actions. CREATE/ADD are separate manage-gated dialogs, not status matrix rows. */
export function actionsForStatus(status: MachineRunStatus): MachineRunAction[] {
  switch (status) {
    case "HELD":
      return ["confirm", "reschedule", "remove_participant", "cancel"];
    case "RESERVED":
      return ["start", "reschedule", "release", "cancel"];
    case "RUNNING":
      return ["complete"];
    case "COMPLETED":
      return ["release"];
    case "RELEASED":
    case "CANCELLED":
    case "SUPERSEDED":
      return [];
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

export function visibleActionsForRole(
  status: MachineRunStatus,
  role: Role,
): MachineRunActionDef[] {
  return actionsForStatus(status)
    .filter((action) => can(role, ACTION_DEFS[action].permission))
    .map((action) => {
      const base = ACTION_DEFS[action];
      // RELEASE is primary after COMPLETE; secondary (skip-run) while still RESERVED.
      if (action === "release" && status === "RESERVED") {
        return { action, ...base, kind: "secondary" as const };
      }
      return { action, ...base };
    });
}

export function primaryActionLabel(
  status: MachineRunStatus,
  role: Role,
): string | null {
  const primary = visibleActionsForRole(status, role).find((a) => a.kind === "primary");
  return primary?.label ?? null;
}

export function statusBadgeClass(status: MachineRunStatus): string {
  switch (status) {
    case "HELD":
      return "bg-wo-surface-inset text-wo-text-primary border-wo-border-strong";
    case "RESERVED":
      return "bg-wo-info-muted text-wo-info border-wo-info/35";
    case "RUNNING":
      return "bg-wo-warning-muted text-wo-warning border-wo-warning/35";
    case "COMPLETED":
      return "bg-wo-success-muted text-wo-success border-wo-success/35";
    case "RELEASED":
      return "bg-wo-surface-inset text-wo-text-muted border-wo-border";
    case "CANCELLED":
    case "SUPERSEDED":
      return "bg-wo-error-muted text-wo-error border-wo-error/35";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

export type OperatorErrorUx = {
  message: string;
  nextAction: string;
  isCasStale: boolean;
};

export function mapMachineRunError(code: string, fallbackMessage?: string): OperatorErrorUx {
  switch (code) {
    case "cas_stale":
    case "cas_stale_or_missing":
      return {
        message: "Rularea a fost modificată între timp. Am reîncărcat datele actuale.",
        nextAction: "Verifică starea și reîncearcă acțiunea.",
        isCasStale: true,
      };
    case "invalid_transition":
      return {
        message: "Această acțiune nu e permisă în starea actuală.",
        nextAction: "Reîncarcă și verifică statusul.",
        isCasStale: false,
      };
    case "overlap_conflict":
      return {
        message: "Intervalul se suprapune cu altă rezervare pe utilaj.",
        nextAction: "Alege alt interval (Reprogramează).",
        isCasStale: false,
      };
    case "minimum_participants_violation":
      return {
        message: "Trebuie cel puțin doi participanți activi pentru această operație.",
        nextAction: "Nu elimina ultimul participant necesar.",
        isCasStale: false,
      };
    case "task_already_in_active_machine_run":
      return {
        message: "Taskul este deja într-o rulare activă.",
        nextAction: "Deschide rularea existentă.",
        isCasStale: false,
      };
    case "participant_capability_mismatch":
    case "machine_capability_mismatch":
    case "machine_compatibility_failure":
      return {
        message: "Taskul nu se potrivește cu capabilitatea utilajului.",
        nextAction: "Alege alt task sau alt utilaj.",
        isCasStale: false,
      };
    case "participant_already_exists":
      return {
        message: "Participantul este deja în această rulare.",
        nextAction: "Reîncarcă lista de candidați.",
        isCasStale: false,
      };
    case "domain_disabled":
      return {
        message: "Rezervările pe utilaj sunt dezactivate.",
        nextAction: "Contactează administratorul.",
        isCasStale: false,
      };
    case "permission_denied":
      return {
        message: "Nu ai dreptul pentru această acțiune.",
        nextAction: "Cere acces manage/execute după rol.",
        isCasStale: false,
      };
    case "run_reservation_state_mismatch":
      return {
        message: "Datele run/rezervare nu coincid.",
        nextAction: "Reîncarcă; nu continua pe date vechi.",
        isCasStale: false,
      };
    case "idempotency_payload_conflict":
      return {
        message: "Cererea conflictă cu una anterioară.",
        nextAction: "Reîncearcă cu o acțiune nouă.",
        isCasStale: false,
      };
    default:
      return {
        message: fallbackMessage?.trim() || "Acțiunea nu a putut fi finalizată.",
        nextAction: "Reîncarcă și încearcă din nou.",
        isCasStale: false,
      };
  }
}

export function formatReservationWindow(
  startIso: string,
  endIso: string,
  timeZone?: string,
): string {
  const opts: Intl.DateTimeFormatOptions = {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };
  if (timeZone) opts.timeZone = timeZone;
  const start = new Date(startIso);
  const end = new Date(endIso);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return `${startIso} → ${endIso}`;
  }
  const fmt = new Intl.DateTimeFormat("ro-RO", opts);
  return `${fmt.format(start)} → ${fmt.format(end)}`;
}

export function formatRuntimeSeconds(seconds: number | null | undefined): string | null {
  if (seconds == null || !Number.isFinite(seconds) || seconds < 0) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function planOrderSummary(orderIds: number[], planIds: number[]): string {
  const orders =
    orderIds.length === 0
      ? "fără comenzi"
      : orderIds.length === 1
        ? `Comandă ${orderIds[0]}`
        : `${orderIds.length} comenzi`;
  const plans =
    planIds.length === 0
      ? "fără planuri"
      : planIds.length === 1
        ? `Plan ${planIds[0]}`
        : `${planIds.length} planuri`;
  return `${orders} · ${plans}`;
}

/** Backend candidate + by-task APIs are PASS; UI closure wires them. */
export const CANDIDATE_DISCOVERY_API = "PRESENT" as const;
export const CREATE_UI = "IMPLEMENTED" as const;
export const ADD_UI = "IMPLEMENTED" as const;
export const SECONDARY_CONTEXT_LINKS = "IMPLEMENTED" as const;
export const MIN_CREATE_PARTICIPANTS = 2;
export const DEFAULT_MACHINE_RUN_TIMEZONE = "Europe/Bucharest";

export function candidateSelectionKey(
  execution_plan_id: number,
  task_key: string,
): string {
  return `${execution_plan_id}::${task_key}`;
}

export function candidateDisplayLabel(c: {
  task_label?: string | null;
  operation_code?: string | null;
  task_key: string;
}): string {
  if (c.task_label?.trim()) return c.task_label.trim();
  if (c.operation_code?.trim()) return c.operation_code.trim();
  const key = c.task_key;
  const short = key.includes(":") ? key.split(":").pop() || key : key;
  return short.length > 48 ? `${short.slice(0, 45)}…` : short;
}
