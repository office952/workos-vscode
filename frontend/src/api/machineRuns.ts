/**
 * MachineRun operator read + lifecycle command client.
 * Server is authority — no optimistic lifecycle mutation.
 */
import { getAPIBaseURL } from "@/lib/config";

const BASE = () => `${getAPIBaseURL()}/api/v1/execution/resource-state/machine-runs`;

export type MachineRunStatus =
  | "HELD"
  | "RESERVED"
  | "RUNNING"
  | "COMPLETED"
  | "CANCELLED"
  | "RELEASED"
  | "SUPERSEDED";

export type ReservationStatus =
  | "HELD"
  | "RESERVED"
  | "CANCELLED"
  | "RELEASED"
  | "SUPERSEDED";

export type ParticipantStatus = "ACTIVE" | "REMOVED";

export type MachineRunListItem = {
  machine_run_id: number;
  status: MachineRunStatus;
  version: number;
  machine_id: number;
  machine_code: string | null;
  machine_name: string | null;
  reservation_id: number;
  reservation_status: ReservationStatus;
  reservation_version: number;
  reservation_start: string;
  reservation_end: string;
  timezone: string;
  active_participant_count: number;
  total_participant_count: number;
  execution_plan_ids: number[];
  order_ids: number[];
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type MachineRunListResult = {
  items: MachineRunListItem[];
  count: number;
};

export type MachineRunMachineProjection = {
  machine_id: number;
  machine_code: string;
  name: string;
  is_active: boolean;
  is_available: boolean;
  operational_status: string | null;
  capabilities: string[];
};

export type MachineRunReservationProjection = {
  reservation_id: number;
  status: ReservationStatus;
  version: number;
  machine_id: number;
  reservation_start: string;
  reservation_end: string;
  timezone: string;
};

export type MachineRunParticipantRead = {
  participant_id: number;
  status: ParticipantStatus;
  execution_plan_id: number;
  task_key: string;
  order_id: number;
  operation_code: string | null;
  workcenter: string | null;
  machine_capability_code: string | null;
  batch_eligible: boolean | null;
  added_at: string | null;
  added_by: string | null;
  removed_at: string | null;
  removed_by: string | null;
};

export type MachineRunDetail = {
  machine_run_id: number;
  status: MachineRunStatus;
  version: number;
  timezone: string;
  started_at: string | null;
  completed_at: string | null;
  actual_runtime_seconds: number | null;
  created_at: string;
  updated_at: string;
  created_by: string | null;
  updated_by: string | null;
  machine: MachineRunMachineProjection;
  reservation: MachineRunReservationProjection;
  participants: MachineRunParticipantRead[];
  execution_plan_ids: number[];
  order_ids: number[];
  active_participant_count: number;
  total_participant_count: number;
};

export type MachineRunCommandResult = {
  machine_run_id: number;
  status: MachineRunStatus;
  version: number;
  reservation_id: number;
  reservation_status: ReservationStatus;
  reservation_version: number;
  machine_id: number;
  reservation_start: string;
  reservation_end: string;
  timezone: string;
  operation: string;
  transition_id: string;
  reservation_transition_id: string;
  already_applied: boolean;
  previous_status: MachineRunStatus | null;
  previous_version: number | null;
  started_at: string | null;
  completed_at: string | null;
};

export type MachineRunApiError = {
  code: string;
  message: string;
  httpStatus: number;
};

export class MachineRunRequestError extends Error {
  readonly code: string;
  readonly httpStatus: number;

  constructor(err: MachineRunApiError) {
    super(err.message);
    this.name = "MachineRunRequestError";
    this.code = err.code;
    this.httpStatus = err.httpStatus;
  }
}

async function parseApiError(res: Response): Promise<MachineRunApiError> {
  try {
    const body = (await res.json()) as {
      detail?: { error?: string; message?: string } | string;
    };
    if (typeof body.detail === "string") {
      return { code: "request_failed", message: body.detail, httpStatus: res.status };
    }
    if (body.detail && typeof body.detail === "object") {
      return {
        code: String(body.detail.error ?? "request_failed"),
        message: String(body.detail.message ?? body.detail.error ?? `http_${res.status}`),
        httpStatus: res.status,
      };
    }
  } catch {
    /* ignore */
  }
  if (res.status === 403) {
    return {
      code: "permission_denied",
      message: "Nu ai dreptul pentru această acțiune.",
      httpStatus: 403,
    };
  }
  return { code: "request_failed", message: `http_${res.status}`, httpStatus: res.status };
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) throw new MachineRunRequestError(await parseApiError(res));
  return (await res.json()) as T;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new MachineRunRequestError(await parseApiError(res));
  return (await res.json()) as T;
}

function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `mr-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export type ListMachineRunsParams = {
  open_only?: boolean;
  status?: MachineRunStatus;
  machine_id?: number;
  execution_plan_id?: number;
  order_id?: number;
};

export async function listMachineRuns(
  params: ListMachineRunsParams = {},
): Promise<MachineRunListResult> {
  const qs = new URLSearchParams();
  if (params.open_only !== undefined) qs.set("open_only", String(params.open_only));
  if (params.status) qs.set("status", params.status);
  if (params.machine_id != null) qs.set("machine_id", String(params.machine_id));
  if (params.execution_plan_id != null) {
    qs.set("execution_plan_id", String(params.execution_plan_id));
  }
  if (params.order_id != null) qs.set("order_id", String(params.order_id));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return getJson<MachineRunListResult>(`${BASE()}${suffix}`);
}

export async function getMachineRun(machineRunId: number): Promise<MachineRunDetail> {
  return getJson<MachineRunDetail>(`${BASE()}/${machineRunId}`);
}

type VersionCommand = {
  expected_version: number;
  reason_code?: string;
  reason_note?: string | null;
};

function withCommandMeta(payload: VersionCommand & Record<string, unknown>) {
  return {
    ...payload,
    idempotency_key: newIdempotencyKey(),
  };
}

export async function confirmMachineRun(
  id: number,
  expected_version: number,
): Promise<MachineRunCommandResult> {
  return postJson(
    `${BASE()}/${id}/confirm`,
    withCommandMeta({ expected_version, reason_code: "machine_run_confirm" }),
  );
}

export async function startMachineRun(
  id: number,
  expected_version: number,
): Promise<MachineRunCommandResult> {
  return postJson(
    `${BASE()}/${id}/start`,
    withCommandMeta({ expected_version, reason_code: "machine_run_start" }),
  );
}

export async function completeMachineRun(
  id: number,
  expected_version: number,
): Promise<MachineRunCommandResult> {
  return postJson(
    `${BASE()}/${id}/complete`,
    withCommandMeta({ expected_version, reason_code: "machine_run_complete" }),
  );
}

export async function releaseMachineRun(
  id: number,
  expected_version: number,
): Promise<MachineRunCommandResult> {
  return postJson(
    `${BASE()}/${id}/release`,
    withCommandMeta({ expected_version, reason_code: "machine_run_release" }),
  );
}

export async function cancelMachineRun(
  id: number,
  expected_version: number,
): Promise<MachineRunCommandResult> {
  return postJson(
    `${BASE()}/${id}/cancel`,
    withCommandMeta({ expected_version, reason_code: "machine_run_cancel" }),
  );
}

export async function rescheduleMachineRun(
  id: number,
  args: {
    expected_version: number;
    reservation_start: string;
    reservation_end: string;
    timezone: string;
  },
): Promise<MachineRunCommandResult> {
  return postJson(
    `${BASE()}/${id}/reschedule`,
    withCommandMeta({
      expected_version: args.expected_version,
      reservation_start: args.reservation_start,
      reservation_end: args.reservation_end,
      timezone: args.timezone,
      reason_code: "machine_run_reschedule",
    }),
  );
}

export async function removeMachineRunParticipant(
  id: number,
  args: {
    expected_version: number;
    execution_plan_id: number;
    task_key: string;
  },
): Promise<MachineRunCommandResult> {
  return postJson(
    `${BASE()}/${id}/remove-participant`,
    withCommandMeta({
      expected_version: args.expected_version,
      execution_plan_id: args.execution_plan_id,
      task_key: args.task_key,
      reason_code: "machine_run_remove_participant",
    }),
  );
}
