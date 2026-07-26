/**
 * UI-TRUTH-01 — Canonical runtime truth types.
 *
 * Separated segments for future EnvironmentBanner (UI-TRUTH-01B).
 * Session truth remains owned by AuthContext; not embedded in RuntimeTruthSnapshot.
 */

export type RuntimeCheckState =
  | "checking"
  | "healthy"
  | "warning"
  | "critical"
  | "unavailable"
  | "unknown"
  | "stale";

export type SessionTruthState =
  | "authenticated"
  | "unauthenticated"
  | "expired"
  | "unknown";

export type DatabaseTruthState =
  | "confirmed"
  | "warning"
  | "unavailable"
  | "unknown"
  | "checking";

export type EnvironmentTruthState =
  | "local"
  | "test"
  | "staging"
  | "production"
  | "demo"
  | "unknown";

export type RuntimeHealthErrorKind =
  | "NETWORK_ERROR"
  | "TIMEOUT"
  | "HTTP_ERROR"
  | "MALFORMED_RESPONSE"
  | "UNAUTHORIZED_DIAGNOSTICS"
  | "ABORTED"
  | "UNKNOWN";

export type DatabaseTruthSource = "diagnostics" | "health" | "none";

export interface RuntimeTruthSnapshot {
  backend: {
    state: RuntimeCheckState;
    rawStatus?: string;
    checkedAt?: string;
    lastSuccessfulAt?: string;
    errorKind?: RuntimeHealthErrorKind;
  };
  database: {
    state: DatabaseTruthState;
    source: DatabaseTruthSource;
  };
  environment: {
    state: EnvironmentTruthState;
    rawValue?: string;
    mockMode?: boolean;
    serviceVersion?: string | null;
  };
  diagnostics: {
    authorized: boolean | null;
    available: boolean | null;
    /** HTTP status from last diagnostics probe when known (e.g. 403). */
    httpStatus?: number | null;
  };
  stale: boolean;
}

export const EMPTY_RUNTIME_TRUTH_SNAPSHOT: RuntimeTruthSnapshot = {
  backend: { state: "checking" },
  database: { state: "checking", source: "none" },
  environment: { state: "unknown" },
  diagnostics: { authorized: null, available: null },
  stale: false,
};
