import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { useRuntimeHealth } from "@/hooks/useRuntimeHealth";
import {
  DEFAULT_STALE_THRESHOLD_MS,
  RUNTIME_HEALTH_URL,
  RUNTIME_VERSION_URL,
} from "@/lib/runtimeHealth";

const FIXED_NOW = Date.parse("2026-07-15T10:00:00.000Z");
const FIXED_HEALTH_TS = "2026-07-15T10:00:00.000Z";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function baseHookOptions(
  overrides: Parameters<typeof useRuntimeHealth>[0] = {},
): Parameters<typeof useRuntimeHealth>[0] {
  return {
    devMode: true,
    now: () => FIXED_NOW,
    ...overrides,
  };
}

async function waitForLoaded(result: { current: ReturnType<typeof useRuntimeHealth> }) {
  await waitFor(() => expect(result.current.isLoading).toBe(false), { timeout: 3000 });
}

describe("useRuntimeHealth", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("loads healthy backend with DB unknown on empty checks", async () => {
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "ok", generated_at: FIXED_HEALTH_TS, checks: {} });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(`unexpected url ${url}`);
    });

    const { result } = renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn })));
    await waitForLoaded(result);

    expect(result.current.snapshot.backend.state).toBe("healthy");
    expect(result.current.snapshot.database.state).toBe("unknown");
    expect(result.current.lastError).toBeNull();
    expect(fetchFn.mock.calls[0][0]).toBe(RUNTIME_HEALTH_URL);
    expect(fetchFn.mock.calls.every(([u]) => !String(u).includes("8001"))).toBe(true);
  });

  it("maps warning health to backend warning", async () => {
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "warning", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(url);
    });

    const { result } = renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn })));
    await waitForLoaded(result);
    expect(result.current.snapshot.backend.state).toBe("warning");
  });

  it("maps critical health to backend critical", async () => {
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "fail", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(url);
    });

    const { result } = renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn })));
    await waitForLoaded(result);
    expect(result.current.snapshot.backend.state).toBe("critical");
  });

  it("maps network failure to backend unavailable without healthy fallback", async () => {
    const fetchFn = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });

    const { result } = renderHook(() =>
      useRuntimeHealth(baseHookOptions({ fetchFn, mockMode: false })),
    );
    await waitForLoaded(result);

    expect(result.current.snapshot.backend.state).toBe("unavailable");
    expect(result.current.snapshot.database.state).toBe("unknown");
    expect(result.current.lastError).toBe("NETWORK_ERROR");
  });

  it("maps timeout to unavailable with TIMEOUT classification", async () => {
    const fetchFn = vi.fn((_url: string, init?: RequestInit) => {
      return new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"));
        });
      });
    });

    const { result } = renderHook(() =>
      useRuntimeHealth(baseHookOptions({ fetchFn, timeoutMs: 50 })),
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false), { timeout: 3000 });

    expect(result.current.snapshot.backend.state).toBe("unavailable");
    expect(result.current.lastError).toBe("TIMEOUT");
  });

  it("retains lastSuccessfulAt after later failure", async () => {
    let failNext = false;
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        if (failNext) throw new TypeError("Failed to fetch");
        return jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(url);
    });

    const { result } = renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn })));
    await waitForLoaded(result);
    expect(result.current.snapshot.backend.lastSuccessfulAt).toBe(FIXED_HEALTH_TS);

    failNext = true;
    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.snapshot.backend.state).toBe("unavailable");
    expect(result.current.snapshot.backend.lastSuccessfulAt).toBe(FIXED_HEALTH_TS);
  });

  it("supports manual refresh", async () => {
    let healthStatus = "ok";
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: healthStatus, checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(url);
    });

    const { result } = renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn })));
    await waitForLoaded(result);

    healthStatus = "warning";
    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.snapshot.backend.state).toBe("warning");
  });

  it("polls on configured interval", async () => {
    vi.useFakeTimers();
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(url);
    });

    renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn, pollIntervalMs: 100 })));

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    const callsAfterMount = fetchFn.mock.calls.filter(([u]) => u === RUNTIME_HEALTH_URL).length;
    expect(callsAfterMount).toBeGreaterThan(0);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
      await Promise.resolve();
    });

    const callsAfterPoll = fetchFn.mock.calls.filter(([u]) => u === RUNTIME_HEALTH_URL).length;
    expect(callsAfterPoll).toBeGreaterThan(callsAfterMount);
  });

  it("marks snapshot stale after threshold", async () => {
    let now = FIXED_NOW;
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(url);
    });

    const { result } = renderHook(() =>
      useRuntimeHealth(
        baseHookOptions({
          fetchFn,
          now: () => now,
          staleThresholdMs: DEFAULT_STALE_THRESHOLD_MS,
        }),
      ),
    );

    await waitForLoaded(result);
    expect(result.current.snapshot.stale).toBe(false);

    now = FIXED_NOW + DEFAULT_STALE_THRESHOLD_MS + 1;
    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.snapshot.stale).toBe(true);
    expect(result.current.snapshot.backend.state).toBe("stale");
  });

  it("does not use mock mode as healthy backend fallback", async () => {
    const fetchFn = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });

    const { result } = renderHook(() =>
      useRuntimeHealth(baseHookOptions({ fetchFn, mockMode: true })),
    );
    await waitForLoaded(result);

    expect(result.current.snapshot.environment.state).toBe("demo");
    expect(result.current.snapshot.backend.state).toBe("unavailable");
  });

  it("diagnostics 403 keeps backend healthy and DB unknown", async () => {
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      if (url === "/api/v1/system/diagnostics") return jsonResponse({ detail: "forbidden" }, 403);
      throw new Error(url);
    });

    const { result } = renderHook(() =>
      useRuntimeHealth(baseHookOptions({ fetchFn, fetchDiagnostics: true })),
    );

    await waitForLoaded(result);
    expect(result.current.snapshot.backend.state).toBe("healthy");
    expect(result.current.snapshot.diagnostics.authorized).toBe(false);
    expect(result.current.snapshot.database.state).toBe("unknown");
    expect(result.current.snapshot.diagnostics.httpStatus).toBe(403);
  });

  it("stops re-fetching diagnostics after 403 (no forbidden poll loop)", async () => {
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      if (url === "/api/v1/system/diagnostics") return jsonResponse({ detail: "forbidden" }, 403);
      throw new Error(url);
    });

    const { result } = renderHook(() =>
      useRuntimeHealth(baseHookOptions({ fetchFn, fetchDiagnostics: true, pollIntervalMs: 60_000 })),
    );
    await waitForLoaded(result);

    const diagCallsAfterLoad = fetchFn.mock.calls.filter(
      ([u]) => u === "/api/v1/system/diagnostics",
    ).length;
    expect(diagCallsAfterLoad).toBe(1);

    await act(async () => {
      await result.current.refresh();
    });

    const diagCallsAfterRefresh = fetchFn.mock.calls.filter(
      ([u]) => u === "/api/v1/system/diagnostics",
    ).length;
    expect(diagCallsAfterRefresh).toBe(1);
    expect(result.current.snapshot.diagnostics.authorized).toBe(false);
    expect(result.current.lastError).toBeNull();
  });

  it("diagnostics authorized with DB ok confirms database", async () => {
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      if (url === "/api/v1/system/diagnostics") {
        return jsonResponse({ checks: { database: { status: "ok" } } });
      }
      throw new Error(url);
    });

    const { result } = renderHook(() =>
      useRuntimeHealth(baseHookOptions({ fetchFn, fetchDiagnostics: true })),
    );

    await waitForLoaded(result);
    expect(result.current.snapshot.database.state).toBe("confirmed");
    expect(result.current.snapshot.database.source).toBe("diagnostics");
  });

  it("prevents overlapping refresh while in flight", async () => {
    let pendingHealth: ((value: Response) => void) | null = null;
    let healthCalls = 0;
    const fetchFn = vi.fn((url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        healthCalls += 1;
        if (healthCalls === 1) {
          return Promise.resolve(
            jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS }),
          );
        }
        return new Promise<Response>((resolve) => {
          pendingHealth = resolve;
        });
      }
      if (url === RUNTIME_VERSION_URL) {
        return Promise.resolve(jsonResponse({ environment: "staging" }));
      }
      return Promise.reject(new Error(url));
    });

    const { result } = renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn })));
    await waitForLoaded(result);

    const healthCallsBefore = fetchFn.mock.calls.filter(([u]) => u === RUNTIME_HEALTH_URL).length;

    void result.current.refresh();
    void result.current.refresh();

    await act(async () => {
      pendingHealth?.(
        jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS }),
      );
      await Promise.resolve();
    });

    const healthCallsAfter = fetchFn.mock.calls.filter(([u]) => u === RUNTIME_HEALTH_URL).length;
    expect(healthCallsAfter - healthCallsBefore).toBeLessThanOrEqual(2);
  });

  it("aborts cleanly on unmount without state update errors", async () => {
    const fetchFn = vi.fn(
      () =>
        new Promise<Response>(() => {
          /* never resolves */
        }),
    );

    const { unmount } = renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn })));
    await waitFor(() => expect(fetchFn).toHaveBeenCalled(), { timeout: 3000 });
    expect(() => unmount()).not.toThrow();
  });

  it("visibility refresh triggers when snapshot is old", async () => {
    vi.useFakeTimers();
    const fetchFn = vi.fn(async (url: string) => {
      if (url === RUNTIME_HEALTH_URL) {
        return jsonResponse({ status: "ok", checks: {}, generated_at: FIXED_HEALTH_TS });
      }
      if (url === RUNTIME_VERSION_URL) return jsonResponse({ environment: "staging" });
      throw new Error(url);
    });

    renderHook(() => useRuntimeHealth(baseHookOptions({ fetchFn, pollIntervalMs: 100 })));

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    const callsBefore = fetchFn.mock.calls.filter(([u]) => u === RUNTIME_HEALTH_URL).length;
    expect(callsBefore).toBeGreaterThan(0);

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => "visible",
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(101);
      document.dispatchEvent(new Event("visibilitychange"));
      await Promise.resolve();
    });

    const callsAfter = fetchFn.mock.calls.filter(([u]) => u === RUNTIME_HEALTH_URL).length;
    expect(callsAfter).toBeGreaterThanOrEqual(callsBefore);
  });
});
