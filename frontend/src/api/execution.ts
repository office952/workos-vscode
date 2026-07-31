/**
 * Execution API client — Sprint #12 (observability, read-only) +
 * Sprint #30 (explicit plan generation gate).
 *
 * Observability is READ-ONLY: GET-only methods, no computation in the UI.
 * Plan generation (Sprint #30) exposes exactly ONE write endpoint —
 * `POST /api/v1/execution/plan/from-order/{order_id}` — and surfaces the
 * backend's structured error codes verbatim so the UI never hides WHY
 * generation fails on a given order.
 *
 * The dashboard reflects backend truth; it does NOT compute, predict, or
 * invent values. Missing fields from the backend remain `null` / `undefined`
 * and MUST be rendered as "UNCONFIRMED" / "—" by the UI — never as 0.
 *
 * Types are derived strictly from the backend contract defined in:
 *   docs/spec/spec__execution_observability_v1.md
 *   app/backend/routers/execution.py (POST /plan/from-order/{id})
 * If a field is not promised by those contracts, it is not in these types.
 */

import { getAPIBaseURL } from '../lib/config';

const getAPIBase = () => `${getAPIBaseURL()}/api/v1`;

// ---------------------------------------------------------------------------
// Types — mirror backend contract exactly.
// ---------------------------------------------------------------------------

export type ExecutionStatus = 'OK' | 'WARNING' | 'CRITICAL' | 'UNCONFIRMED';
export type PresenceStatus = 'present' | 'absent';
export type AlertSeverity = 'WARNING' | 'CRITICAL';

/**
 * One row in the dashboard read-model.
 * Backend guarantees: any of {planned_time, actual_time, delta_time,
 * alert_severity} may be `null` — surface them as "UNCONFIRMED"/"—" in UI.
 */
export interface DashboardRow {
  order_id: number;
  order_code: string;
  plan_status: PresenceStatus;
  reality_status: PresenceStatus;
  divergence_status: ExecutionStatus;
  alert_severity: AlertSeverity | null;
  planned_time: number | null;
  actual_time: number | null;
  delta_time: number | null;
}

export interface DashboardResponse {
  total: number;
  rows: DashboardRow[];
}

export interface ObservabilityThresholds {
  warning_time_delta_pct: number | null;
  critical_time_delta_pct: number | null;
  warning_time_delta_minutes: number | null;
  critical_time_delta_minutes: number | null;
  is_active: boolean;
  source: string;
}

export interface ObservabilityReport {
  order_id: number;
  order_code: string;
  status: ExecutionStatus;
  reasons: string[];
  has_order: boolean;
  has_plan: boolean;
  has_reality: boolean;
  plan_total_estimated_minutes: number | null;
  reality_total_actual_minutes: number | null;
  delta_minutes: number | null;
  delta_pct: number | null;
  thresholds: ObservabilityThresholds;
  observed_at: string;
}

export interface ExecutionAlert {
  order_id: number;
  order_code: string;
  severity: AlertSeverity;
  reason: string;
  reasons_all: string[];
  metric: string;
  expected_value: number | null;
  actual_value: number | null;
  delta: number | null;
  created_at: string;
}

export interface AlertsResponse {
  order_id: number;
  order_code: string;
  status: ExecutionStatus;
  alerts: ExecutionAlert[];
}

// ---------------------------------------------------------------------------
// Client — GET only. Any failure bubbles up as a thrown Error so callers
// render an explicit error state (never a fake OK).
// ---------------------------------------------------------------------------

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${getAPIBase()}${path}`, {
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

// ---------------------------------------------------------------------------
// Plan generation types — strictly mirror the backend response contract of
// `POST /api/v1/execution/plan/from-order/{order_id}`.
//
// Success (HTTP 201) returns the persisted ExecutionPlan row shape:
//   { id, order_id, order_code, snapshot_version, tasks, total_estimated_time_minutes }
//
// Structured failures the UI must handle distinctly:
//   - HTTP 404 { error: "order_not_found" }
//   - HTTP 409 { error: "plan_already_exists", plan_id: number }
//   - HTTP 422 { error: "snapshot_incomplete", field: "<dotted.path>", message }
// ---------------------------------------------------------------------------

/** Batch 17 Track B — null / presence honesty for ops-graph RO display. */
export type OpsGraphNullClassification =
  | 'present'
  | 'unknown'
  | 'not_required'
  | 'owner_accepted_risk'
  | 'blocked_pending_owner_truth';

export interface OpsGraphFieldHonesty {
  value: unknown;
  classification: OpsGraphNullClassification;
  role: string;
  note?: string;
  owner_lock?: string;
}

export interface OpsGraphTaskReadClarity {
  version: string;
  identity: {
    task_id?: string | null;
    short_code?: string | null;
    label?: string | null;
    technical_name?: string | null;
    source_operation_code?: string | null;
    source_task_rule_code?: string | null;
    process_type?: string | null;
    sequence_index?: number | null;
    deterministic_task_key?: string | null;
  };
  lifecycle: {
    value: string | null;
    classification: OpsGraphNullClassification;
    role: string;
    display_label: string;
    note?: string;
    source_field: string;
  };
  quantity: OpsGraphFieldHonesty;
  unit: OpsGraphFieldHonesty;
  depends_on: {
    task_ids: string[];
    short_codes: string[];
    classification: OpsGraphNullClassification;
    note?: string;
  };
  machine_code: OpsGraphFieldHonesty;
  machine_type: OpsGraphFieldHonesty;
  workcenter: OpsGraphFieldHonesty;
  estimated_time_minutes: OpsGraphFieldHonesty;
  planning_minutes_source: OpsGraphFieldHonesty;
  assigned_employee_id: OpsGraphFieldHonesty;
  warnings: {
    raw_warnings: string[];
    accepted_gap_codes: string[];
    active_warnings: string[];
  };
  display_hints: {
    machine_column: string;
    machine_code_column: string;
    status_column: string;
    collapse_accepted_gaps: boolean;
    do_not_coalesce_machine_code_from_machine_type: boolean;
  };
}

export interface OpsGraphPlanReadClarity {
  version: string;
  operational_tasks_count: number;
  sequence: {
    observed_indices: number[];
    gaps: number[];
    classification: OpsGraphNullClassification | string;
    note?: string;
    display_order_basis?: string;
  };
  null_policy?: Record<string, string>;
  identity_rules?: Record<string, string>;
  counts_guard?: {
    note?: string;
    input_count: number;
    output_count: number;
  };
}

export interface PlannedTaskRow {
  task_id: string;
  name: string;
  layer_id: string;
  process_type: string;
  machine_type: string;
  /** Null when planning source is absent — never coerce to 0 in UI. */
  estimated_time_minutes: number | null;
  quantity: number;
  /** Present on V2 operational_tasks — never invent when absent. */
  display_name?: string | null;
  technical_name?: string | null;
  machine_code?: string | null;
  workcenter?: string | null;
  planning_minutes_source?: string | null;
  assigned_employee_id?: string | null;
  operational_status?: string | null;
  sequence_index?: number | null;
  warnings?: string[] | null;
  depends_on_task_ids?: string[] | null;
  execution_plan_id?: number | null;
  order_id?: number | null;
  source_operation_code?: string | null;
  /**
   * Batch 17 Track B — GET /execution/plan display-only honesty metadata.
   * Prefer this over coalescing machine_code from machine_type.
   */
  read_clarity?: OpsGraphTaskReadClarity | null;
}

export interface ExecutionPlanResponse {
  id: number;
  order_id: number;
  order_code: string;
  snapshot_version: number;
  tasks: PlannedTaskRow[];
  total_estimated_time_minutes: number;
  prepared_by_user_id?: string | null;
  operational_readiness_status?: string;
  operational_tasks_count?: number;
  operational_readiness_blockers?: string[];
  operational_readiness_next_action?: string | null;
  operational_tasks_materialized?: boolean;
  plan_format?: string;
  execution_tasks_created?: boolean;
  /** Batch 17 Track B — plan-level sequence/null policy for ops-graph RO. */
  ops_graph_read_clarity?: OpsGraphPlanReadClarity | null;
}

/** GET /execution/plan-v2/from-order/{id}/materialization-audit — read-only. */
export interface MaterializationAuditGuards {
  mode?: string;
  creates_execution_tasks?: boolean;
  creates_sessions?: boolean;
  writes_database?: boolean;
  uses_cost_engine?: boolean;
  uses_price_endpoint?: boolean;
  uses_quote_orchestrator?: boolean;
  employee_mobile_scope?: boolean;
  post_materialize_allowed?: boolean;
}

export interface MaterializableTaskCandidatePreview {
  task_key: string;
  label?: string | null;
  canonical_task_type?: string | null;
  source_operation_code?: string | null;
  sequence_index?: number | null;
  operational_status_preview?: string;
  estimated_minutes?: number | null;
  warnings?: string[];
  machine_requirement?: { workcenter?: string | null } | null;
}

export interface NonOperationalItemPreview {
  task_name: string;
  task_type: string;
  reason: string;
  excluded_from?: string;
}

/** GET /execution/plan-v2/preview/{id} — read-only preview (orphaned panel contract). */
export interface ExecutionPlanV2PreviewResponse {
  status: string;
  source_snapshot_code?: string | null;
  planned_tasks: Array<{
    task_key: string;
    label?: string | null;
    canonical_task_type?: string | null;
    source_operation_code?: string | null;
    estimated_minutes?: number | null;
    warnings: string[];
    machine_requirement?: { workcenter?: string | null } | null;
  }>;
  planned_operations: Array<{
    operation_code: string;
    label?: string | null;
    source_template_code?: string | null;
    workcenter?: string | null;
    sequence_index?: number | null;
    priced?: boolean;
  }>;
  warnings: string[];
  blockers: string[];
}

export interface ExecutionPlanV2MaterializationAuditResponse {
  mode: "audit_only";
  order_id: number;
  order_code?: string | null;
  execution_plan_id: number;
  source_quote_snapshot_v2_id?: number | null;
  source_snapshot_code?: string | null;
  plan_source?: string | null;
  template_code?: string | null;
  materialization_status: string;
  dry_run_status: string;
  planned_task_count: number;
  operation_count: number;
  operational_tasks_in_envelope_count: number;
  materializable_task_candidates: MaterializableTaskCandidatePreview[];
  non_operational_items?: NonOperationalItemPreview[];
  blockers: string[];
  warnings: string[];
  activation_hash_preview?: string | null;
  guards: MaterializationAuditGuards;
  contract_notes?: string[];
  message?: string | null;
}

// ---------------------------------------------------------------------------
// Execution Reality types (Sprint #36) — strict mirror of backend contract
// from routers/execution.py + services/execution_reality_service.py.
//
// The reality row is a write-log of operator observations: each task has its
// own started_at / ended_at timestamps. `ended_at=null` means in_progress.
//
// The UI MUST NOT fabricate these values and MUST NOT apply optimistic
// updates — every write call is followed by a refetch of backend truth.
// ---------------------------------------------------------------------------

export interface RealityTaskRow {
  task_id: string;
  started_at: string;
  ended_at: string | null;
}

export interface ExecutionRealityResponse {
  id: number;
  order_id: number;
  order_code: string;
  tasks: RealityTaskRow[];
  total_actual_time_minutes: number;
}

/**
 * Typed error class for `POST /reality/start-task` and `/reality/end-task`.
 * Preserves the backend error code so the UI can render a precise,
 * actionable message without guessing.
 *
 * Known backend codes (services/execution_reality_service.py):
 *   - order_id_invalid, order_code_invalid, task_id_invalid
 *   - timestamp_missing, timestamp_invalid, timestamp_before_start
 *   - tasks_json_invalid, tasks_json_not_list
 *   - task_already_started, task_already_ended
 *   - reality_not_initialised, task_not_started, task_missing_start
 *   - order_not_found (surfaced by the router)
 * Any unknown code is preserved verbatim and surfaced as 'unknown' for
 * labelling while keeping the raw code in `rawCode`.
 */
export type RealityActionErrorCode =
  | 'order_id_invalid'
  | 'order_code_invalid'
  | 'task_id_invalid'
  | 'timestamp_missing'
  | 'timestamp_invalid'
  | 'timestamp_before_start'
  | 'tasks_json_invalid'
  | 'tasks_json_not_list'
  | 'task_already_started'
  | 'task_already_ended'
  | 'reality_not_initialised'
  | 'task_not_started'
  | 'task_missing_start'
  | 'order_not_found'
  | 'task_not_ready'
  | 'production_release_blocked'
  | 'ORDER_SNAPSHOT_V2_MISSING'
  | 'ORDER_SNAPSHOT_V2_CORRUPT'
  | 'unknown';

export class RealityActionError extends Error {
  code: RealityActionErrorCode;
  rawCode: string;
  httpStatus: number;
  detail: string | null;
  raw: unknown;
  blockers: Array<Record<string, unknown>>;
  readinessLabel: string | null;

  constructor(
    code: RealityActionErrorCode,
    rawCode: string,
    httpStatus: number,
    message: string,
    detail: string | null,
    raw: unknown,
    blockers: Array<Record<string, unknown>> = [],
    readinessLabel: string | null = null,
  ) {
    super(message);
    this.name = 'RealityActionError';
    this.code = code;
    this.rawCode = rawCode;
    this.httpStatus = httpStatus;
    this.detail = detail;
    this.raw = raw;
    this.blockers = blockers;
    this.readinessLabel = readinessLabel;
  }
}

const KNOWN_REALITY_CODES: RealityActionErrorCode[] = [
  'order_id_invalid',
  'order_code_invalid',
  'task_id_invalid',
  'timestamp_missing',
  'timestamp_invalid',
  'timestamp_before_start',
  'tasks_json_invalid',
  'tasks_json_not_list',
  'task_already_started',
  'task_already_ended',
  'reality_not_initialised',
  'task_not_started',
  'task_missing_start',
  'order_not_found',
  'task_not_ready',
  'production_release_blocked',
  'ORDER_SNAPSHOT_V2_MISSING',
  'ORDER_SNAPSHOT_V2_CORRUPT',
];

async function parseRealityActionError(
  res: Response,
  op: string,
): Promise<RealityActionError> {
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    // body stays null
  }
  const envelope =
    body && typeof body === 'object' && 'detail' in body
      ? (body as { detail: unknown }).detail
      : body;

  let rawCode = 'unknown';
  let code: RealityActionErrorCode = 'unknown';
  let detail: string | null = null;
  let message = `POST ${op} failed: ${res.status} ${res.statusText}`;
  let blockers: Array<Record<string, unknown>> = [];
  let readinessLabel: string | null = null;

  if (envelope && typeof envelope === 'object') {
    const rec = envelope as Record<string, unknown>;
    const err = typeof rec.error === 'string' ? rec.error : null;
    const innerCode = typeof rec.code === 'string' ? rec.code : null;
    const candidate =
      err === 'reality_input_invalid' && innerCode ? innerCode : innerCode || err;
    if (candidate) {
      rawCode = candidate;
      if ((KNOWN_REALITY_CODES as string[]).includes(candidate)) {
        code = candidate as RealityActionErrorCode;
      }
    }
    if (typeof rec.detail === 'string') {
      detail = rec.detail;
    }
    if (typeof rec.message === 'string') {
      message = rec.message;
    }
    if (Array.isArray(rec.blockers)) {
      blockers = rec.blockers.filter((b) => b && typeof b === 'object') as Array<
        Record<string, unknown>
      >;
    }
    if (typeof rec.readiness_label === 'string') {
      readinessLabel = rec.readiness_label;
    }
  }

  return new RealityActionError(
    code,
    rawCode,
    res.status,
    message,
    detail,
    body,
    blockers,
    readinessLabel,
  );
}

/**
 * Typed error class for `POST /plan/from-order/{id}`. Preserves the backend
 * error code (snapshot_incomplete | plan_already_exists | order_not_found |
 * unknown) so the UI can render a precise, actionable message without
 * guessing or hiding the reason. NEVER downgrade a failure to a silent
 * success at call-sites.
 */
export type PlanGenerationErrorCode =
  | 'order_not_found'
  | 'plan_already_exists'
  | 'snapshot_incomplete'
  | 'plan_persist_failed'
  | 'unknown';

export class PlanGenerationError extends Error {
  code: PlanGenerationErrorCode;
  httpStatus: number;
  field: string | null;
  existingPlanId: number | null;
  raw: unknown;

  constructor(
    code: PlanGenerationErrorCode,
    httpStatus: number,
    message: string,
    field: string | null,
    existingPlanId: number | null,
    raw: unknown,
  ) {
    super(message);
    this.name = 'PlanGenerationError';
    this.code = code;
    this.httpStatus = httpStatus;
    this.field = field;
    this.existingPlanId = existingPlanId;
    this.raw = raw;
  }
}

async function parsePlanGenerationError(res: Response): Promise<PlanGenerationError> {
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    // body stays null — still raise a typed error below.
  }
  // FastAPI wraps errors in { detail: {...} }. Accept both shapes so that
  // any future refactor of the error envelope still surfaces a code.
  const envelope =
    body && typeof body === 'object' && 'detail' in body
      ? (body as { detail: unknown }).detail
      : body;

  let code: PlanGenerationErrorCode = 'unknown';
  let field: string | null = null;
  let existingPlanId: number | null = null;
  let message = `POST /plan/from-order failed: ${res.status} ${res.statusText}`;

  if (envelope && typeof envelope === 'object') {
    const rec = envelope as Record<string, unknown>;
    const rawCode = typeof rec.error === 'string' ? rec.error : null;
    if (
      rawCode === 'order_not_found' ||
      rawCode === 'plan_already_exists' ||
      rawCode === 'snapshot_incomplete' ||
      rawCode === 'plan_persist_failed'
    ) {
      code = rawCode;
    }
    if (typeof rec.field === 'string') {
      field = rec.field;
    }
    if (typeof rec.plan_id === 'number') {
      existingPlanId = rec.plan_id;
    }
    if (typeof rec.message === 'string') {
      message = rec.message;
    }
  }

  return new PlanGenerationError(code, res.status, message, field, existingPlanId, body);
}

export const executionApi = {
  getExecutionDashboard(): Promise<DashboardResponse> {
    return getJson<DashboardResponse>('/execution/dashboard');
  },

  getObservability(orderId: number): Promise<ObservabilityReport> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      return Promise.reject(new Error('order_id_invalid'));
    }
    return getJson<ObservabilityReport>(`/execution/observability/${orderId}`);
  },

  getAlerts(orderId: number): Promise<AlertsResponse> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      return Promise.reject(new Error('order_id_invalid'));
    }
    return getJson<AlertsResponse>(`/execution/alerts/${orderId}`);
  },

  /**
   * Fetch the persisted execution plan for an order (Sprint #36 helper).
   * 404 is thrown as a regular error — callers should only invoke this
   * when observability confirms `has_plan=true`.
   */
  getExecutionPlan(orderId: number): Promise<ExecutionPlanResponse> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      return Promise.reject(new Error('order_id_invalid'));
    }
    return getJson<ExecutionPlanResponse>(`/execution/plan/${orderId}`);
  },

  /**
   * Read-only V2 plan preview for an order.
   * GET-only — never persists or materializes.
   */
  getExecutionPlanV2Preview(orderId: number): Promise<ExecutionPlanV2PreviewResponse> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      return Promise.reject(new Error('order_id_invalid'));
    }
    return getJson<ExecutionPlanV2PreviewResponse>(
      `/execution/plan-v2/preview/${orderId}`,
    );
  },

  /**
   * Read-only materialization audit for an order's persisted V2 plan.
   * GET-only — never triggers POST materialize.
   */
  getExecutionPlanV2MaterializationAudit(
    orderId: number,
  ): Promise<ExecutionPlanV2MaterializationAuditResponse> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      return Promise.reject(new Error('order_id_invalid'));
    }
    return getJson<ExecutionPlanV2MaterializationAuditResponse>(
      `/execution/plan-v2/from-order/${orderId}/materialization-audit`,
    );
  },

  /**
   * Trigger backend plan generation for an order.
   *
   * The UI MUST only offer this when observability reports `has_plan=false`.
   * The backend is the sole authority: it validates the snapshot shape and
   * rejects legacy/incomplete orders with `snapshot_incomplete` + a dotted
   * `field` path. The UI surfaces those failures as-is — it does NOT retry
   * silently, patch missing fields, or fall back to a coarse plan.
   *
   * Defensive timeout: the request is bounded by an AbortController at
   * 45 seconds. If the upstream (or a mis-pointed dev proxy) never
   * responds, the fetch is aborted and we throw a typed
   * `PlanGenerationError(code='unknown', httpStatus=0, message='timeout')`
   * so the UI can exit its loading state and show an explicit failure
   * instead of spinning forever. This is purely a UI liveness guard —
   * it does NOT fabricate a plan or hide backend errors.
   */
  async generatePlan(orderId: number): Promise<ExecutionPlanResponse> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      throw new PlanGenerationError(
        'unknown',
        0,
        'order_id_invalid',
        null,
        null,
        null,
      );
    }
    const controller = new AbortController();
    const timeoutMs = 45_000;
    const timeoutHandle = setTimeout(() => controller.abort(), timeoutMs);
    let res: Response;
    try {
      res = await fetch(
        `${getAPIBase()}/execution/plan/from-order/${orderId}`,
        {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
        },
      );
    } catch (e) {
      clearTimeout(timeoutHandle);
      // AbortError => client-side timeout. Any other error
      // (TypeError: Failed to fetch, network error, DNS failure) => network
      // failure. Both are surfaced as a typed PlanGenerationError so the UI
      // exits loading and renders a structured message instead of hanging.
      const isAbort =
        (e instanceof DOMException && e.name === 'AbortError') ||
        (e instanceof Error && e.name === 'AbortError');
      const msg = isAbort
        ? `plan_generation_client_timeout_after_${timeoutMs}ms`
        : e instanceof Error
          ? `network_error: ${e.message}`
          : 'network_error: unknown';
      throw new PlanGenerationError('unknown', 0, msg, null, null, null);
    }
    clearTimeout(timeoutHandle);
    if (!res.ok) {
      throw await parsePlanGenerationError(res);
    }
    return (await res.json()) as ExecutionPlanResponse;
  },

  /**
   * Fetch the current execution reality row for an order.
   *
   * Returns null when the backend responds 404 with `reality_not_found`
   * (the canonical "no reality captured yet" state — NOT an error). Any
   * other non-2xx response is thrown so the caller renders an explicit
   * failure state. NEVER fabricate a row when backend says missing.
   */
  async getReality(orderId: number): Promise<ExecutionRealityResponse | null> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      throw new Error('order_id_invalid');
    }
    const res = await fetch(
      `${getAPIBase()}/execution/reality/${orderId}`,
      { credentials: 'include' },
    );
    if (res.status === 404) {
      // Distinguish "reality_not_found" (canonical missing state) from other
      // 404s. Only the canonical missing state is returned as `null`.
      let body: unknown = null;
      try {
        body = await res.json();
      } catch {
        // fall through
      }
      const envelope =
        body && typeof body === 'object' && 'detail' in body
          ? (body as { detail: unknown }).detail
          : body;
      const err =
        envelope &&
        typeof envelope === 'object' &&
        typeof (envelope as Record<string, unknown>).error === 'string'
          ? ((envelope as Record<string, unknown>).error as string)
          : null;
      if (err === 'reality_not_found') {
        return null;
      }
      throw new Error(`GET /execution/reality/${orderId} failed: 404`);
    }
    if (!res.ok) {
      throw new Error(
        `GET /execution/reality/${orderId} failed: ${res.status} ${res.statusText}`,
      );
    }
    return (await res.json()) as ExecutionRealityResponse;
  },

  /**
   * Start a task (`POST /api/v1/execution/reality/start-task`).
   *
   * The backend is the sole authority:
   *   - refuses unknown task_id (not in plan contract — enforced by UI)
   *   - refuses duplicate start for an in_progress task
   *   - refuses start on an order that lacks a plan (enforced upstream by
   *     the UI: the button is only shown after `has_plan=true`)
   *
   * The UI MUST refetch backend truth after this call — no optimistic
   * updates, no fake success on error.
   */
  async startTask(
    orderId: number,
    taskId: string,
    timestamp: string,
    options?: { overrideReadiness?: boolean; overrideReason?: string },
  ): Promise<ExecutionRealityResponse> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      throw new RealityActionError(
        'order_id_invalid',
        'order_id_invalid',
        0,
        'order_id_invalid',
        null,
        null,
      );
    }
    if (!taskId) {
      throw new RealityActionError(
        'task_id_invalid',
        'task_id_invalid',
        0,
        'task_id_invalid',
        null,
        null,
      );
    }
    let res: Response;
    try {
      res = await fetch(`${getAPIBase()}/execution/reality/start-task`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          task_id: taskId,
          timestamp,
          override_readiness: options?.overrideReadiness === true,
          override_reason: options?.overrideReason || undefined,
        }),
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'unknown';
      throw new RealityActionError(
        'unknown',
        'network_error',
        0,
        `network_error: ${msg}`,
        null,
        null,
      );
    }
    if (!res.ok) {
      throw await parseRealityActionError(res, '/reality/start-task');
    }
    return (await res.json()) as ExecutionRealityResponse;
  },

  /**
   * Complete a task (`POST /api/v1/execution/reality/end-task`).
   *
   * Canonical endpoint name on the backend is `end-task`. It maps to the
   * sprint's "complete task" action semantically: it sets `ended_at`,
   * which in turn makes `actual_minutes = ended_at - started_at` derivable.
   *
   * The backend refuses:
   *   - end on a task that was not started
   *   - end on a task that was already ended
   *   - end with a timestamp before the task's start
   */
  async endTask(
    orderId: number,
    taskId: string,
    timestamp: string,
  ): Promise<ExecutionRealityResponse> {
    if (!Number.isInteger(orderId) || orderId <= 0) {
      throw new RealityActionError(
        'order_id_invalid',
        'order_id_invalid',
        0,
        'order_id_invalid',
        null,
        null,
      );
    }
    if (!taskId) {
      throw new RealityActionError(
        'task_id_invalid',
        'task_id_invalid',
        0,
        'task_id_invalid',
        null,
        null,
      );
    }
    let res: Response;
    try {
      res = await fetch(`${getAPIBase()}/execution/reality/end-task`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          task_id: taskId,
          timestamp,
        }),
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'unknown';
      throw new RealityActionError(
        'unknown',
        'network_error',
        0,
        `network_error: ${msg}`,
        null,
        null,
      );
    }
    if (!res.ok) {
      throw await parseRealityActionError(res, '/reality/end-task');
    }
    return (await res.json()) as ExecutionRealityResponse;
  },
};