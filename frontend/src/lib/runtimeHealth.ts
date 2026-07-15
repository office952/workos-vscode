/**
 * UI-TRUTH-01A — Runtime health normalizers and same-origin fetch helpers.
 *
 * All operator-facing probes use same-origin `/api` (Vite proxy path).
 * Never hardcode direct backend host URLs here.
 */

import { isMockEnabled } from "@/lib/mockGuard";
import type {
  DatabaseTruthSource,
  DatabaseTruthState,
  EnvironmentTruthState,
  RuntimeCheckState,
  RuntimeHealthErrorKind,
  RuntimeTruthSnapshot,
} from "@/types/runtimeStatus";

// ---------------------------------------------------------------------------
// Same-origin contract (browser → proxy → backend)
// ---------------------------------------------------------------------------

export const RUNTIME_HEALTH_URL = "/api/v1/system/health";
export const RUNTIME_VERSION_URL = "/api/v1/system/version";
export const RUNTIME_DIAGNOSTICS_URL = "/api/v1/system/diagnostics";

export const DEFAULT_POLL_INTERVAL_MS = 45_000;
export const DEFAULT_STALE_THRESHOLD_MS = 120_000;
export const DEFAULT_FETCH_TIMEOUT_MS = 6_000;

// ---------------------------------------------------------------------------
// Raw API shapes (minimal — no secrets stored in React state)
// ---------------------------------------------------------------------------

export interface PublicHealthPayload {
  status?: string;
  service?: string;
  generated_at?: string;
  checks?: Record<string, { status?: string; details?: Record<string, unknown> }>;
}

export interface VersionPayload {
  environment?: string | null;
  app_name?: string | null;
  release_version?: string | null;
}

export interface DiagnosticsCheckPayload {
  status?: string;
}

export interface DiagnosticsPayload {
  status?: string;
  generated_at?: string;
  checks?: Record<string, DiagnosticsCheckPayload>;
}

// ---------------------------------------------------------------------------
// Error classification
// ---------------------------------------------------------------------------

export function classifyFetchError(
  error: unknown,
  httpStatus?: number,
): RuntimeHealthErrorKind {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "ABORTED";
  }
  if (error instanceof Error) {
    if (error.message === "FETCH_TIMEOUT") return "TIMEOUT";
    if (error.message.startsWith("HTTP_")) return "HTTP_ERROR";
    if (error.message === "MALFORMED_RESPONSE") return "MALFORMED_RESPONSE";
    if (error.message === "NETWORK_ERROR") return "NETWORK_ERROR";
  }
  if (httpStatus === 401 || httpStatus === 403) return "UNAUTHORIZED_DIAGNOSTICS";
  return "UNKNOWN";
}

// ---------------------------------------------------------------------------
// Pure normalizers
// ---------------------------------------------------------------------------

export function mapRawBackendStatus(raw: string | undefined | null): RuntimeCheckState {
  const value = (raw ?? "").trim().toLowerCase();
  if (!value) return "unknown";
  if (value === "ok" || value === "healthy") return "healthy";
  if (value === "warning" || value === "degraded") return "warning";
  if (value === "fail" || value === "critical" || value === "error" || value === "unhealthy") {
    return "critical";
  }
  return "unknown";
}

export function mapRawDatabaseCheckStatus(raw: string | undefined | null): DatabaseTruthState {
  const value = (raw ?? "").trim().toLowerCase();
  if (!value) return "unknown";
  if (value === "ok" || value === "healthy") return "confirmed";
  if (value === "warning" || value === "unknown" || value === "degraded") return "warning";
  if (value === "fail" || value === "critical" || value === "error" || value === "unhealthy") {
    return "unavailable";
  }
  return "unknown";
}

export function deriveDatabaseFromHealthChecks(
  checks: PublicHealthPayload["checks"],
): { state: DatabaseTruthState; source: DatabaseTruthSource } {
  if (!checks || Object.keys(checks).length === 0) {
    return { state: "unknown", source: "none" };
  }
  const databaseCheck = checks.database;
  if (!databaseCheck || databaseCheck.status == null) {
    return { state: "unknown", source: "health" };
  }
  return {
    state: mapRawDatabaseCheckStatus(databaseCheck.status),
    source: "health",
  };
}

export function normalizeHealthPayload(
  payload: unknown,
  checkedAt?: string,
): Pick<RuntimeTruthSnapshot, "backend" | "database"> {
  if (!payload || typeof payload !== "object") {
    return {
      backend: {
        state: "unavailable",
        errorKind: "MALFORMED_RESPONSE",
        checkedAt,
      },
      database: { state: "unknown", source: "none" },
    };
  }

  const body = payload as PublicHealthPayload;
  if (typeof body.status !== "string" || body.status.trim() === "") {
    return {
      backend: {
        state: "unavailable",
        errorKind: "MALFORMED_RESPONSE",
        checkedAt,
      },
      database: { state: "unknown", source: "none" },
    };
  }

  const backendState = mapRawBackendStatus(body.status);
  const database = deriveDatabaseFromHealthChecks(body.checks);

  return {
    backend: {
      state: backendState,
      rawStatus: body.status,
      checkedAt: body.generated_at ?? checkedAt,
    },
    database,
  };
}

export function normalizeVersionEnvironment(
  payload: unknown,
  options?: { devMode?: boolean; mockMode?: boolean },
): RuntimeTruthSnapshot["environment"] {
  const mockMode = options?.mockMode ?? isMockEnabled();
  if (mockMode) {
    return { state: "demo", rawValue: "mock", mockMode: true };
  }

  if (options?.devMode ?? import.meta.env.DEV) {
    if (!payload || typeof payload !== "object") {
      return { state: "local", rawValue: "development" };
    }
    const envRaw = (payload as VersionPayload).environment;
    if (envRaw == null || String(envRaw).trim() === "") {
      return { state: "local", rawValue: "development" };
    }
    const mapped = mapVersionEnvironmentValue(String(envRaw));
    if (mapped === "unknown") {
      return { state: "local", rawValue: String(envRaw) };
    }
    return { state: mapped, rawValue: String(envRaw) };
  }

  if (!payload || typeof payload !== "object") {
    return { state: "unknown" };
  }

  const envRaw = (payload as VersionPayload).environment;
  if (envRaw == null || String(envRaw).trim() === "") {
    return { state: "unknown" };
  }

  return {
    state: mapVersionEnvironmentValue(String(envRaw)),
    rawValue: String(envRaw),
  };
}

export function mapVersionEnvironmentValue(raw: string): EnvironmentTruthState {
  const value = raw.trim().toLowerCase();
  if (value === "local" || value === "development" || value === "dev") return "local";
  if (value === "test" || value === "testing") return "test";
  if (value === "staging" || value === "stage") return "staging";
  if (value === "production" || value === "prod") return "production";
  if (value === "demo" || value === "mock") return "demo";
  return "unknown";
}

export function normalizeDiagnosticsBoundary(
  httpStatus: number | null,
  payload: unknown,
): Pick<RuntimeTruthSnapshot, "database" | "diagnostics"> {
  if (httpStatus === 401 || httpStatus === 403) {
    return {
      database: { state: "unknown", source: "none" },
      diagnostics: { authorized: false, available: false },
    };
  }

  if (httpStatus == null || httpStatus < 200 || httpStatus >= 300) {
    return {
      database: { state: "unknown", source: "none" },
      diagnostics: { authorized: null, available: false },
    };
  }

  if (!payload || typeof payload !== "object") {
    return {
      database: { state: "unknown", source: "none" },
      diagnostics: { authorized: true, available: false },
    };
  }

  const body = payload as DiagnosticsPayload;
  const databaseCheck = body.checks?.database;
  if (!databaseCheck?.status) {
    return {
      database: { state: "unknown", source: "diagnostics" },
      diagnostics: { authorized: true, available: true },
    };
  }

  return {
    database: {
      state: mapRawDatabaseCheckStatus(databaseCheck.status),
      source: "diagnostics",
    },
    diagnostics: { authorized: true, available: true },
  };
}

export function applyStaleClassification(
  snapshot: RuntimeTruthSnapshot,
  nowMs: number,
  staleThresholdMs: number,
): RuntimeTruthSnapshot {
  const lastOk = snapshot.backend.lastSuccessfulAt;
  if (!lastOk) return { ...snapshot, stale: false };

  const lastOkMs = Date.parse(lastOk);
  if (Number.isNaN(lastOkMs)) return { ...snapshot, stale: false };

  const isStale = nowMs - lastOkMs > staleThresholdMs;
  if (!isStale) return { ...snapshot, stale: false };

  const backendState: RuntimeCheckState =
    snapshot.backend.state === "checking" ? "checking" : "stale";

  return {
    ...snapshot,
    stale: true,
    backend: {
      ...snapshot.backend,
      state: backendState,
    },
  };
}

export function mergeRuntimeTruthSnapshot(
  base: RuntimeTruthSnapshot,
  patch: Partial<RuntimeTruthSnapshot>,
): RuntimeTruthSnapshot {
  return {
    backend: { ...base.backend, ...patch.backend },
    database: { ...base.database, ...patch.database },
    environment: { ...base.environment, ...patch.environment },
    diagnostics: { ...base.diagnostics, ...patch.diagnostics },
    stale: patch.stale ?? base.stale,
  };
}

// ---------------------------------------------------------------------------
// Fetch helpers (same-origin only)
// ---------------------------------------------------------------------------

export async function fetchJsonWithTimeout(
  url: string,
  options: {
    timeoutMs?: number;
    signal?: AbortSignal;
    fetchFn?: typeof fetch;
  } = {},
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const fetchFn = options.fetchFn ?? fetch;
  const timeoutMs = options.timeoutMs ?? DEFAULT_FETCH_TIMEOUT_MS;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const onExternalAbort = () => controller.abort();
  options.signal?.addEventListener("abort", onExternalAbort, { once: true });

  try {
    const response = await fetchFn(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "same-origin",
      signal: controller.signal,
    });

    const text = await response.text();
    let data: unknown = null;
    if (text) {
      try {
        data = JSON.parse(text) as unknown;
      } catch {
        throw new Error("MALFORMED_RESPONSE");
      }
    } else {
      throw new Error("MALFORMED_RESPONSE");
    }

    return { ok: response.ok, status: response.status, data };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      if (options.signal?.aborted) throw error;
      throw new Error("FETCH_TIMEOUT");
    }
    if (error instanceof TypeError) {
      throw new Error("NETWORK_ERROR");
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    options.signal?.removeEventListener("abort", onExternalAbort);
  }
}

export async function fetchPublicHealth(
  options: {
    timeoutMs?: number;
    signal?: AbortSignal;
    fetchFn?: typeof fetch;
  } = {},
): Promise<Pick<RuntimeTruthSnapshot, "backend" | "database">> {
  const result = await fetchJsonWithTimeout(RUNTIME_HEALTH_URL, options);
  if (!result.ok) {
    throw new Error(`HTTP_${result.status}`);
  }
  return normalizeHealthPayload(result.data, new Date().toISOString());
}

export async function fetchPublicVersion(
  options: {
    timeoutMs?: number;
    signal?: AbortSignal;
    fetchFn?: typeof fetch;
    devMode?: boolean;
    mockMode?: boolean;
  } = {},
): Promise<RuntimeTruthSnapshot["environment"]> {
  try {
    const result = await fetchJsonWithTimeout(RUNTIME_VERSION_URL, options);
    if (!result.ok) {
      return normalizeVersionEnvironment(null, {
        devMode: options.devMode,
        mockMode: options.mockMode,
      });
    }
    return normalizeVersionEnvironment(result.data, {
      devMode: options.devMode,
      mockMode: options.mockMode,
    });
  } catch {
    return normalizeVersionEnvironment(null, {
      devMode: options.devMode,
      mockMode: options.mockMode,
    });
  }
}

export async function fetchDiagnosticsBoundary(
  options: {
    timeoutMs?: number;
    signal?: AbortSignal;
    fetchFn?: typeof fetch;
  } = {},
): Promise<Pick<RuntimeTruthSnapshot, "database" | "diagnostics">> {
  try {
    const result = await fetchJsonWithTimeout(RUNTIME_DIAGNOSTICS_URL, options);
    return normalizeDiagnosticsBoundary(result.status, result.data);
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("HTTP_")) {
      const status = Number.parseInt(error.message.replace("HTTP_", ""), 10);
      return normalizeDiagnosticsBoundary(status, null);
    }
    return {
      database: { state: "unknown", source: "none" },
      diagnostics: { authorized: null, available: false },
    };
  }
}
