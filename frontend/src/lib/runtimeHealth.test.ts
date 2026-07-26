import { describe, expect, it } from "vitest";
import {
  DEFAULT_POLL_INTERVAL_MS,
  DEFAULT_STALE_THRESHOLD_MS,
  RUNTIME_HEALTH_URL,
  RUNTIME_VERSION_URL,
  applyStaleClassification,
  classifyFetchError,
  deriveDatabaseFromHealthChecks,
  mapRawBackendStatus,
  mapVersionEnvironmentValue,
  normalizeDiagnosticsBoundary,
  normalizeHealthPayload,
  normalizeVersionEnvironment,
} from "@/lib/runtimeHealth";
import type { RuntimeTruthSnapshot } from "@/types/runtimeStatus";

describe("runtimeHealth normalizers", () => {
  it("maps health ok to backend healthy", () => {
    const result = normalizeHealthPayload({
      status: "ok",
      generated_at: "2026-07-15T10:00:00.000Z",
      checks: {},
    });
    expect(result.backend.state).toBe("healthy");
    expect(result.database.state).toBe("unknown");
  });

  it("maps health healthy alias to backend healthy", () => {
    expect(mapRawBackendStatus("healthy")).toBe("healthy");
  });

  it("maps health warning to backend warning", () => {
    const result = normalizeHealthPayload({ status: "warning", checks: {} });
    expect(result.backend.state).toBe("warning");
    expect(result.database.state).toBe("unknown");
  });

  it("maps health fail to backend critical", () => {
    const result = normalizeHealthPayload({ status: "fail", checks: {} });
    expect(result.backend.state).toBe("critical");
  });

  it("maps health critical alias to backend critical", () => {
    expect(mapRawBackendStatus("critical")).toBe("critical");
  });

  it("empty checks produce DB unknown never confirmed", () => {
    const result = deriveDatabaseFromHealthChecks({});
    expect(result.state).toBe("unknown");
    expect(result.source).toBe("none");
  });

  it("explicit DB ok in health checks produces confirmed", () => {
    const result = deriveDatabaseFromHealthChecks({
      database: { status: "ok" },
    });
    expect(result.state).toBe("confirmed");
    expect(result.source).toBe("health");
  });

  it("explicit DB warning in health checks produces warning", () => {
    const result = deriveDatabaseFromHealthChecks({
      database: { status: "warning" },
    });
    expect(result.state).toBe("warning");
  });

  it("malformed payload never healthy", () => {
    const result = normalizeHealthPayload(null);
    expect(result.backend.state).toBe("unavailable");
    expect(result.backend.errorKind).toBe("MALFORMED_RESPONSE");
  });

  it("missing status field is malformed", () => {
    const result = normalizeHealthPayload({ checks: {} });
    expect(result.backend.state).toBe("unavailable");
  });

  it("unknown raw status maps to unknown backend", () => {
    expect(mapRawBackendStatus("mystery")).toBe("unknown");
  });

  it("normalizes version development to local", () => {
    const env = normalizeVersionEnvironment({ environment: "development" }, { devMode: true });
    expect(env.state).toBe("local");
  });

  it("normalizes version staging", () => {
    expect(mapVersionEnvironmentValue("staging")).toBe("staging");
  });

  it("normalizes version production", () => {
    expect(mapVersionEnvironmentValue("production")).toBe("production");
  });

  it("unknown environment value maps to unknown in prod mode", () => {
    const env = normalizeVersionEnvironment({ environment: "mystery" }, { devMode: false });
    expect(env.state).toBe("unknown");
  });

  it("mock mode forces demo environment without inferring backend", () => {
    const env = normalizeVersionEnvironment({ environment: "production" }, { mockMode: true });
    expect(env.state).toBe("demo");
    expect(env.mockMode).toBe(true);
  });

  it("diagnostics 403 does not mark backend unavailable", () => {
    const result = normalizeDiagnosticsBoundary(403, null);
    expect(result.diagnostics.authorized).toBe(false);
    expect(result.database.state).toBe("unknown");
  });

  it("diagnostics 401 is unauthorized boundary", () => {
    const result = normalizeDiagnosticsBoundary(401, null);
    expect(result.diagnostics.authorized).toBe(false);
  });

  it("explicit diagnostics database ok confirms DB", () => {
    const result = normalizeDiagnosticsBoundary(200, {
      checks: { database: { status: "ok" } },
    });
    expect(result.database.state).toBe("confirmed");
    expect(result.database.source).toBe("diagnostics");
    expect(result.diagnostics.authorized).toBe(true);
  });

  it("classifies timeout errors", () => {
    expect(classifyFetchError(new Error("FETCH_TIMEOUT"))).toBe("TIMEOUT");
  });

  it("classifies network errors", () => {
    expect(classifyFetchError(new Error("NETWORK_ERROR"))).toBe("NETWORK_ERROR");
  });

  it("classifies malformed response", () => {
    expect(classifyFetchError(new Error("MALFORMED_RESPONSE"))).toBe("MALFORMED_RESPONSE");
  });

  it("classifies abort as aborted", () => {
    expect(classifyFetchError(new DOMException("aborted", "AbortError"))).toBe("ABORTED");
  });

  it("applyStaleClassification marks stale after threshold", () => {
    const base: RuntimeTruthSnapshot = {
      backend: {
        state: "healthy",
        lastSuccessfulAt: "2026-07-15T10:00:00.000Z",
      },
      database: { state: "unknown", source: "none" },
      environment: { state: "local" },
      diagnostics: { authorized: null, available: null },
      stale: false,
    };
    const now = Date.parse("2026-07-15T10:00:00.000Z") + DEFAULT_STALE_THRESHOLD_MS + 1;
    const stale = applyStaleClassification(base, now, DEFAULT_STALE_THRESHOLD_MS);
    expect(stale.stale).toBe(true);
    expect(stale.backend.state).toBe("stale");
  });

  it("uses same-origin health URL constant", () => {
    expect(RUNTIME_HEALTH_URL).toBe("/api/v1/system/health");
    expect(RUNTIME_VERSION_URL).toBe("/api/v1/system/version");
    expect(RUNTIME_HEALTH_URL).not.toContain("8001");
  });

  it("default poll and stale thresholds match plan", () => {
    expect(DEFAULT_POLL_INTERVAL_MS).toBe(45_000);
    expect(DEFAULT_STALE_THRESHOLD_MS).toBe(120_000);
  });
});
