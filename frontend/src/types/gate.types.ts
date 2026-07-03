/**
 * S30 — Gate Evaluation types (read-only).
 *
 * Strict mirror of backend contract from:
 *   GET /api/v1/execution/plan/gate/{order_id}
 *
 * These types are consumed by the read-only UI visibility layer.
 * No mutation types exist here — the UI only reads.
 */

export interface GateBlocker {
  code: string;
  severity: "blocker";
  task_ref: Record<string, unknown>;
  message: string;
  details: Record<string, unknown>;
}

export interface GateWarning {
  code: string;
  severity: "warning";
  task_ref: Record<string, unknown>;
  message: string;
  details: Record<string, unknown>;
}

export interface GateMissingLink {
  link: string;
  on: Record<string, unknown>;
  expected_source: string;
  available_today: boolean;
}

export interface GateRegistryRef {
  name: string;
  endpoint: string;
  version: string;
}

export interface GateTraceSource {
  order: { id: number; code: string; snapshot_version: number | null };
  product: { product_id: string | null; source: string };
  registries_consulted: GateRegistryRef[];
  registries_unavailable: string[];
  gate_spec_version: string;
}

export interface GateEvaluation {
  order_id: number;
  order_code: string;
  snapshot_version: number | null;
  evaluated_at: string;
  can_generate: boolean;
  blockers: GateBlocker[];
  warnings: GateWarning[];
  missing_links: GateMissingLink[];
  required_next_action: string;
  trace_source: GateTraceSource;
}