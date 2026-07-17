import { describe, expect, it } from "vitest";
import {
  RUNTIME_BANNER_LABELS,
  authCannotImplyHealthy,
  buildRuntimeStatusSummary,
} from "@/components/workos/RuntimeStatusSummary";
import type { RuntimeTruthSnapshot } from "@/types/runtimeStatus";
import { EMPTY_RUNTIME_TRUTH_SNAPSHOT } from "@/types/runtimeStatus";

function snap(partial: Partial<RuntimeTruthSnapshot>): RuntimeTruthSnapshot {
  return {
    ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
    ...partial,
    backend: { ...EMPTY_RUNTIME_TRUTH_SNAPSHOT.backend, ...partial.backend },
    database: { ...EMPTY_RUNTIME_TRUTH_SNAPSHOT.database, ...partial.database },
    environment: { ...EMPTY_RUNTIME_TRUTH_SNAPSHOT.environment, ...partial.environment },
    diagnostics: { ...EMPTY_RUNTIME_TRUTH_SNAPSHOT.diagnostics, ...partial.diagnostics },
  };
}

describe("buildRuntimeStatusSummary", () => {
  it("loading does not claim healthy backend or LIVE/DB", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "checking" },
        database: { state: "checking", source: "none" },
        environment: { state: "local" },
      }),
      isLoading: true,
      sessionState: "authenticated",
    });
    expect(view.severity).toBe("neutral");
    expect(view.mainText).toContain(RUNTIME_BANNER_LABELS.loadingMain);
    expect(view.mainText).not.toMatch(/LIVE/);
    expect(view.mainText).not.toContain("Backend disponibil");
  });

  it("backend healthy + DB confirmed → positive, matrix wording", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "healthy", rawStatus: "ok", checkedAt: "2026-07-17T04:00:00.000Z" },
        database: { state: "confirmed", source: "diagnostics" },
        environment: { state: "local", rawValue: "development" },
      }),
      sessionState: "authenticated",
    });
    expect(view.severity).toBe("positive");
    expect(view.mainText).toBe("Local · Backend disponibil · Baza de date confirmată");
    expect(view.mainText).toContain("ă"); // diacritics
    expect(view.technicalStrip).toContain("Detalii tehnice");
  });

  it("backend available + DB unverified → warning, not all-clear", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "healthy", rawStatus: "ok" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
      }),
    });
    expect(view.severity).toBe("warning");
    expect(view.mainText).toBe("Local · Backend disponibil · DB neverificată");
    expect(view.mainText).not.toMatch(/LIVE/);
  });

  it("backend degraded/warning uses matrix wording", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "warning", rawStatus: "warning" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
      }),
    });
    expect(view.severity).toBe("warning");
    expect(view.mainText).toBe("Local · Backend cu avertisment · DB neverificată");
    expect(view.technicalStrip).toContain("status=warning");
  });

  it("stale snapshot is warning with Stare învechită, never positive", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: {
          state: "stale",
          rawStatus: "ok",
          lastSuccessfulAt: "2026-07-17T03:00:00.000Z",
        },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
        stale: true,
      }),
    });
    expect(view.severity).toBe("warning");
    expect(view.staleLabel).toBe("Stare învechită");
    expect(view.isStale).toBe(true);
    expect(view.mainText).toContain("stare învechită");
  });

  it("403 diagnostics message is distinct from backend unavailable", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "healthy", rawStatus: "ok" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
        diagnostics: { authorized: false, available: false, httpStatus: 403 },
      }),
    });
    expect(view.severity).not.toBe("critical");
    expect(view.diagnosticsMessage).toContain("Nu ai permisiune pentru diagnostice detaliate");
    expect(view.mainText).toContain("Backend disponibil");
    expect(view.showRetry).toBe(false);
  });

  it("backend unavailable → critical, no DB verified claim", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "unavailable", errorKind: "NETWORK_ERROR" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
      }),
      lastError: "NETWORK_ERROR",
    });
    expect(view.severity).toBe("critical");
    expect(view.mainText).toContain("Backend indisponibil");
    expect(view.mainText).not.toContain("Baza de date confirmată");
    expect(view.technicalStrip).toContain("NETWORK_ERROR");
  });

  it("unknown backend stays warning/neutral — never positive", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "unknown" },
        database: { state: "unknown", source: "none" },
        environment: { state: "unknown" },
      }),
    });
    expect(view.severity).not.toBe("positive");
    expect(view.mainText).toContain("stare necunoscută");
  });

  it("stale backend is warning", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "healthy", lastSuccessfulAt: "2026-07-17T00:00:00.000Z" },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
        stale: true,
      }),
    });
    expect(view.severity).toBe("warning");
    expect(view.mainText).toContain("învechită");
    expect(view.technicalStrip).toContain("stale=true");
  });

  it("demo mode uses matrix demo wording", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        environment: { state: "demo", mockMode: true },
      }),
    });
    expect(view.mainText).toBe("Mod demo · Date demonstrative");
    expect(view.severity).toBe("warning");
  });

  it("omits technical strip when no technical details", () => {
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "checking" },
        database: { state: "checking", source: "none" },
        environment: { state: "local" },
      }),
      isLoading: true,
    });
    expect(view.technicalStrip).toBeNull();
  });

  it("never emits LIVE / DB", () => {
    const cases: RuntimeTruthSnapshot[] = [
      snap({ backend: { state: "healthy" }, database: { state: "unknown", source: "none" }, environment: { state: "local" } }),
      snap({ backend: { state: "warning", rawStatus: "warning" }, database: { state: "unknown", source: "none" }, environment: { state: "local" } }),
      snap({ backend: { state: "unavailable" }, environment: { state: "production" } }),
    ];
    for (const snapshot of cases) {
      const view = buildRuntimeStatusSummary({ snapshot, sessionState: "authenticated" });
      expect(view.mainText).not.toMatch(/LIVE\s*\/\s*DB/);
      expect(view.mainText).not.toContain("backend live");
    }
  });

  it("UTF-8 Romanian diacritics present in representative labels", () => {
    const withDiacritics = [
      RUNTIME_BANNER_LABELS.dbConfirmed, // confirmată
      RUNTIME_BANNER_LABELS.dbNeverVerified, // neverificată
      RUNTIME_BANNER_LABELS.backendWarning, // avertisment — no diacritic required
      RUNTIME_BANNER_LABELS.loadingMain, // verifică
    ];
    expect(RUNTIME_BANNER_LABELS.dbConfirmed).toContain("ă");
    expect(RUNTIME_BANNER_LABELS.dbNeverVerified).toContain("ă");
    expect(RUNTIME_BANNER_LABELS.loadingMain).toContain("ă");
    for (const label of withDiacritics) {
      expect(label).not.toMatch(/Ã.|â€|Äƒ|È/);
    }
    expect(RUNTIME_BANNER_LABELS.backendUnavailable).toBe("Backend indisponibil");
  });
});

describe("authCannotImplyHealthy", () => {
  it("authenticated session alone cannot produce positive runtime state", () => {
    expect(authCannotImplyHealthy("authenticated")).toBe(true);
  });
});

describe("modules health wording consistency", () => {
  it("same health fixture maps banner warning without contradicting ok wording", () => {
    // ModuleChain surfaces raw health status; banner must not claim Backend disponibil for warning
    const healthFixtureStatus = "warning";
    const view = buildRuntimeStatusSummary({
      snapshot: snap({
        backend: { state: "warning", rawStatus: healthFixtureStatus },
        database: { state: "unknown", source: "none" },
        environment: { state: "local" },
      }),
    });
    expect(view.mainText).toContain("Backend cu avertisment");
    expect(view.mainText).not.toContain("Backend disponibil");
    expect(view.technicalStrip).toContain(`status=${healthFixtureStatus}`);
  });
});
