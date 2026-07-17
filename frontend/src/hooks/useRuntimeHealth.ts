import { useCallback, useEffect, useRef, useState } from "react";
import {
  DEFAULT_FETCH_TIMEOUT_MS,
  DEFAULT_POLL_INTERVAL_MS,
  DEFAULT_STALE_THRESHOLD_MS,
  applyStaleClassification,
  classifyFetchError,
  fetchDiagnosticsBoundary,
  fetchPublicHealth,
  fetchPublicVersion,
  mergeRuntimeTruthSnapshot,
} from "@/lib/runtimeHealth";
import {
  EMPTY_RUNTIME_TRUTH_SNAPSHOT,
  type RuntimeHealthErrorKind,
  type RuntimeTruthSnapshot,
} from "@/types/runtimeStatus";

export interface UseRuntimeHealthOptions {
  pollIntervalMs?: number;
  staleThresholdMs?: number;
  timeoutMs?: number;
  /** When true, attempts diagnostics fetch for DB segment (gated by server auth). */
  fetchDiagnostics?: boolean;
  enabled?: boolean;
  /** Test seams — never pass direct backend URLs. */
  fetchFn?: typeof fetch;
  now?: () => number;
  devMode?: boolean;
  mockMode?: boolean;
}

export interface UseRuntimeHealthResult {
  snapshot: RuntimeTruthSnapshot;
  isLoading: boolean;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
  lastError: RuntimeHealthErrorKind | null;
}

export function useRuntimeHealth(options: UseRuntimeHealthOptions = {}): UseRuntimeHealthResult {
  const pollIntervalMs = options.pollIntervalMs ?? DEFAULT_POLL_INTERVAL_MS;
  const staleThresholdMs = options.staleThresholdMs ?? DEFAULT_STALE_THRESHOLD_MS;
  const timeoutMs = options.timeoutMs ?? DEFAULT_FETCH_TIMEOUT_MS;
  const enabled = options.enabled ?? true;
  const fetchDiagnostics = options.fetchDiagnostics ?? false;

  const fetchFn = options.fetchFn;
  const nowFn = options.now ?? (() => Date.now());

  const [snapshot, setSnapshot] = useState<RuntimeTruthSnapshot>(EMPTY_RUNTIME_TRUTH_SNAPSHOT);
  const [isLoading, setIsLoading] = useState(enabled);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastError, setLastError] = useState<RuntimeHealthErrorKind | null>(null);

  const snapshotRef = useRef(snapshot);
  snapshotRef.current = snapshot;

  const requestGenerationRef = useRef(0);
  const inFlightRef = useRef(false);
  const mountedRef = useRef(true);
  const abortRef = useRef<AbortController | null>(null);
  const versionLoadedRef = useRef(false);
  /** After 401/403, stop re-hitting diagnostics on every poll (no forbidden loop). */
  const diagnosticsForbiddenRef = useRef(false);

  const applySnapshot = useCallback(
    (updater: (current: RuntimeTruthSnapshot) => RuntimeTruthSnapshot) => {
      if (!mountedRef.current) return;
      setSnapshot((current) => {
        const next = applyStaleClassification(
          updater(current),
          nowFn(),
          staleThresholdMs,
        );
        snapshotRef.current = next;
        return next;
      });
    },
    [nowFn, staleThresholdMs],
  );

  const runProbe = useCallback(
    async (mode: "initial" | "refresh") => {
      if (!enabled) return;
      if (inFlightRef.current) return;

      inFlightRef.current = true;
      const generation = ++requestGenerationRef.current;

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      if (mode === "initial") {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }

      const fetchOptions = {
        timeoutMs,
        signal: controller.signal,
        fetchFn,
      };

      try {
        const healthPart = await fetchPublicHealth(fetchOptions);

        if (!mountedRef.current || generation !== requestGenerationRef.current) return;

        const successfulAt = healthPart.backend.checkedAt ?? new Date(nowFn()).toISOString();

        let nextSnapshot = mergeRuntimeTruthSnapshot(snapshotRef.current, {
          backend: {
            ...healthPart.backend,
            lastSuccessfulAt: successfulAt,
            errorKind: undefined,
          },
          database: healthPart.database,
        });

        if (!versionLoadedRef.current) {
          const environment = await fetchPublicVersion({
            ...fetchOptions,
            devMode: options.devMode,
            mockMode: options.mockMode,
          });
          if (!mountedRef.current || generation !== requestGenerationRef.current) return;
          nextSnapshot = mergeRuntimeTruthSnapshot(nextSnapshot, { environment });
          versionLoadedRef.current = true;
        }

        if (fetchDiagnostics && !diagnosticsForbiddenRef.current) {
          const diagnosticsPart = await fetchDiagnosticsBoundary(fetchOptions);
          if (!mountedRef.current || generation !== requestGenerationRef.current) return;
          if (diagnosticsPart.diagnostics.authorized === false) {
            diagnosticsForbiddenRef.current = true;
            // 403 must not overwrite public-health DB segment or appear as backend failure.
            nextSnapshot = mergeRuntimeTruthSnapshot(nextSnapshot, {
              diagnostics: diagnosticsPart.diagnostics,
            });
          } else if (diagnosticsPart.diagnostics.available === false && diagnosticsPart.diagnostics.authorized == null) {
            nextSnapshot = mergeRuntimeTruthSnapshot(nextSnapshot, {
              diagnostics: diagnosticsPart.diagnostics,
            });
          } else {
            nextSnapshot = mergeRuntimeTruthSnapshot(nextSnapshot, diagnosticsPart);
          }
        } else if (fetchDiagnostics && diagnosticsForbiddenRef.current) {
          nextSnapshot = mergeRuntimeTruthSnapshot(nextSnapshot, {
            diagnostics: {
              authorized: false,
              available: false,
              httpStatus: snapshotRef.current.diagnostics.httpStatus ?? 403,
            },
          });
        }

        applySnapshot(() => nextSnapshot);
        setLastError(null);
      } catch (error) {
        if (!mountedRef.current || generation !== requestGenerationRef.current) return;

        const aborted =
          (error instanceof DOMException && error.name === "AbortError") ||
          (error instanceof Error && error.message === "ABORTED");

        if (aborted) return;

        const errorKind = classifyFetchError(error);
        setLastError(errorKind);

        applySnapshot((current) =>
          mergeRuntimeTruthSnapshot(current, {
            backend: {
              state: "unavailable",
              checkedAt: new Date(nowFn()).toISOString(),
              lastSuccessfulAt: current.backend.lastSuccessfulAt,
              errorKind,
            },
            database: { state: "unknown", source: "none" },
          }),
        );

        if (!versionLoadedRef.current) {
          const environment = await fetchPublicVersion({
            timeoutMs,
            signal: controller.signal,
            fetchFn,
            devMode: options.devMode,
            mockMode: options.mockMode,
          });
          if (!mountedRef.current || generation !== requestGenerationRef.current) return;
          versionLoadedRef.current = true;
          applySnapshot((current) => mergeRuntimeTruthSnapshot(current, { environment }));
        }
      } finally {
        if (mountedRef.current && generation === requestGenerationRef.current) {
          inFlightRef.current = false;
          setIsLoading(false);
          setIsRefreshing(false);
        }
      }
    },
    [
      applySnapshot,
      enabled,
      fetchDiagnostics,
      fetchFn,
      nowFn,
      options.devMode,
      options.mockMode,
      timeoutMs,
    ],
  );

  const runProbeRef = useRef(runProbe);
  runProbeRef.current = runProbe;

  const nowFnRef = useRef(nowFn);
  nowFnRef.current = nowFn;

  const refresh = useCallback(async () => {
    await runProbeRef.current("refresh");
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (!enabled) {
      setIsLoading(false);
      return () => {
        mountedRef.current = false;
        abortRef.current?.abort();
      };
    }

    void runProbeRef.current("initial");

    const intervalId = window.setInterval(() => {
      void runProbeRef.current("refresh");
    }, pollIntervalMs);

    const onVisibilityChange = () => {
      if (document.visibilityState !== "visible") return;
      const current = snapshotRef.current;
      const lastOk = current.backend.lastSuccessfulAt;
      const lastOkMs = lastOk ? Date.parse(lastOk) : Number.NaN;
      const ageMs = Number.isNaN(lastOkMs) ? Number.POSITIVE_INFINITY : nowFnRef.current() - lastOkMs;
      if (current.stale || ageMs >= pollIntervalMs) {
        void runProbeRef.current("refresh");
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      mountedRef.current = false;
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      abortRef.current?.abort();
    };
  }, [enabled, pollIntervalMs]);

  return {
    snapshot,
    isLoading,
    isRefreshing,
    refresh,
    lastError,
  };
}
