/**
 * UI-TRUTH-01B — Shared presentation mapping for runtime health banner.
 *
 * Terminology authority: docs/qa/.../ui_truth_01/terminology_matrix.json
 * Does not fetch health; consumes RuntimeTruthSnapshot from useRuntimeHealth.
 */

import type {
  DatabaseTruthState,
  EnvironmentTruthState,
  RuntimeCheckState,
  RuntimeHealthErrorKind,
  RuntimeTruthSnapshot,
  SessionTruthState,
} from "@/types/runtimeStatus";

export type BannerSeverity = "positive" | "neutral" | "warning" | "critical";

export interface RuntimeStatusSummaryView {
  mainText: string;
  severity: BannerSeverity;
  environmentLabel: string;
  backendLabel: string;
  databaseLabel: string;
  isLoading: boolean;
  freshnessText: string | null;
  technicalStrip: string | null;
  accessibleDescription: string;
  sessionNote: string | null;
}

export interface BuildRuntimeStatusSummaryInput {
  snapshot: RuntimeTruthSnapshot;
  isLoading?: boolean;
  sessionState?: SessionTruthState | "loading" | "auth_config_missing" | "dev_auth_enabled";
  lastError?: RuntimeHealthErrorKind | null;
  serviceVersion?: string | null;
}

/** Matrix-aligned labels (Romanian, UTF-8). */
export const RUNTIME_BANNER_LABELS = {
  local: "Local",
  staging: "Staging",
  production: "Producție",
  test: "Test",
  demoMain: "Mod demo · Date demonstrative",
  demoDetail: "Date demonstrative — nu reprezintă producție",
  mediumUnknown: "Mediu necunoscut",
  backendChecking: "Se verifică",
  backendAvailable: "Backend disponibil",
  backendWarning: "Backend cu avertisment",
  backendUnavailable: "Backend indisponibil",
  backendCritical: "Backend critic",
  backendStale: "Backend — stare învechită",
  backendUnknown: "Backend — stare necunoscută",
  dbNeverVerified: "DB neverificată",
  dbUnknown: "DB necunoscută",
  dbConfirmed: "Baza de date confirmată",
  dbWarning: "Baza de date cu avertisment",
  dbUnavailable: "Baza de date indisponibilă",
  dbChecking: "DB — se verifică",
  freshnessPrefix: "Ultima verificare",
  sessionUnauth: "Sesiune neautentificată",
  sessionExpired: "Sesiune expirată",
  sessionDev: "Sesiune dev",
  sessionAuthNeeded: "Autentificare necesară pentru API protejat",
  technicalDetails: "Detalii tehnice",
  loadingMain: "Se verifică",
} as const;

const FORBIDDEN_MAIN_PATTERNS = ["LIVE / DB", "LIVE/DB", "Sursa de date: backend live"];

export function assertNoForbiddenBannerText(text: string): void {
  for (const bad of FORBIDDEN_MAIN_PATTERNS) {
    if (text.includes(bad)) {
      throw new Error(`Forbidden banner text: ${bad}`);
    }
  }
}

function environmentLabel(state: EnvironmentTruthState): string {
  switch (state) {
    case "local":
      return RUNTIME_BANNER_LABELS.local;
    case "staging":
      return RUNTIME_BANNER_LABELS.staging;
    case "production":
      return RUNTIME_BANNER_LABELS.production;
    case "test":
      return RUNTIME_BANNER_LABELS.test;
    case "demo":
      return "Mod demo";
    default:
      return RUNTIME_BANNER_LABELS.mediumUnknown;
  }
}

function backendLabel(state: RuntimeCheckState, isLoading: boolean): string {
  if (isLoading && (state === "checking" || state === "unknown")) {
    return RUNTIME_BANNER_LABELS.backendChecking;
  }
  switch (state) {
    case "checking":
      return RUNTIME_BANNER_LABELS.backendChecking;
    case "healthy":
      return RUNTIME_BANNER_LABELS.backendAvailable;
    case "warning":
      return RUNTIME_BANNER_LABELS.backendWarning;
    case "unavailable":
      return RUNTIME_BANNER_LABELS.backendUnavailable;
    case "critical":
      return RUNTIME_BANNER_LABELS.backendCritical;
    case "stale":
      return RUNTIME_BANNER_LABELS.backendStale;
    default:
      return RUNTIME_BANNER_LABELS.backendUnknown;
  }
}

function databaseLabel(state: DatabaseTruthState, source: RuntimeTruthSnapshot["database"]["source"]): string {
  switch (state) {
    case "confirmed":
      return RUNTIME_BANNER_LABELS.dbConfirmed;
    case "warning":
      return RUNTIME_BANNER_LABELS.dbWarning;
    case "unavailable":
      return RUNTIME_BANNER_LABELS.dbUnavailable;
    case "checking":
      return RUNTIME_BANNER_LABELS.dbChecking;
    case "unknown":
    default:
      // Public health with empty checks → neverificată (matrix); else necunoscută
      return source === "none" ? RUNTIME_BANNER_LABELS.dbNeverVerified : RUNTIME_BANNER_LABELS.dbUnknown;
  }
}

function sessionNote(
  sessionState: BuildRuntimeStatusSummaryInput["sessionState"],
): string | null {
  if (!sessionState || sessionState === "authenticated" || sessionState === "loading") {
    return null;
  }
  if (sessionState === "expired") return RUNTIME_BANNER_LABELS.sessionExpired;
  if (sessionState === "dev_auth_enabled") return RUNTIME_BANNER_LABELS.sessionDev;
  if (sessionState === "unauthenticated" || sessionState === "auth_config_missing") {
    return RUNTIME_BANNER_LABELS.sessionUnauth;
  }
  return null;
}

function formatCheckedAt(iso?: string): string | null {
  if (!iso) return null;
  const ms = Date.parse(iso);
  if (Number.isNaN(ms)) return null;
  try {
    return new Intl.DateTimeFormat("ro-RO", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(new Date(ms));
  } catch {
    return iso;
  }
}

function deriveSeverity(
  snapshot: RuntimeTruthSnapshot,
  isLoading: boolean,
): BannerSeverity {
  if (isLoading && snapshot.backend.state === "checking") return "neutral";
  if (snapshot.environment.state === "demo") return "warning";

  const backend = snapshot.stale ? "stale" : snapshot.backend.state;
  if (backend === "unavailable" || backend === "critical") return "critical";
  if (backend === "warning" || backend === "stale" || backend === "unknown") return "warning";
  if (backend === "checking") return "neutral";

  // healthy backend
  if (snapshot.database.state === "confirmed") return "positive";
  // available but DB unverified/unknown — not all-clear
  return "warning";
}

function buildTechnicalStrip(input: BuildRuntimeStatusSummaryInput): string | null {
  const parts: string[] = [];
  const { snapshot, lastError, serviceVersion } = input;

  if (snapshot.backend.rawStatus) {
    parts.push(`status=${snapshot.backend.rawStatus}`);
  }
  if (lastError) {
    parts.push(`err=${lastError}`);
  }
  if (snapshot.backend.errorKind && snapshot.backend.errorKind !== lastError) {
    parts.push(`err=${snapshot.backend.errorKind}`);
  }
  if (serviceVersion) {
    parts.push(`ver=${serviceVersion}`);
  }
  if (snapshot.environment.rawValue) {
    parts.push(`env=${snapshot.environment.rawValue}`);
  }
  if (snapshot.database.source && snapshot.database.source !== "none") {
    parts.push(`db_src=${snapshot.database.source}`);
  }
  if (snapshot.stale) {
    parts.push("stale=true");
  }

  const checked = formatCheckedAt(snapshot.backend.checkedAt ?? snapshot.backend.lastSuccessfulAt);
  if (checked) {
    parts.push(`t=${checked}`);
  }

  if (parts.length === 0) return null;
  return `${RUNTIME_BANNER_LABELS.technicalDetails}: ${parts.join(" · ")}`;
}

/**
 * Pure mapper — EnvironmentBanner renders this view without business logic.
 */
export function buildRuntimeStatusSummary(
  input: BuildRuntimeStatusSummaryInput,
): RuntimeStatusSummaryView {
  const isLoading = Boolean(input.isLoading);
  const { snapshot } = input;

  if (snapshot.environment.state === "demo" || snapshot.environment.mockMode) {
    const view: RuntimeStatusSummaryView = {
      mainText: RUNTIME_BANNER_LABELS.demoMain,
      severity: "warning",
      environmentLabel: "Mod demo",
      backendLabel: RUNTIME_BANNER_LABELS.demoDetail,
      databaseLabel: "",
      isLoading: false,
      freshnessText: null,
      technicalStrip: buildTechnicalStrip(input),
      accessibleDescription: RUNTIME_BANNER_LABELS.demoMain,
      sessionNote: sessionNote(input.sessionState),
    };
    assertNoForbiddenBannerText(view.mainText);
    return view;
  }

  const env = environmentLabel(snapshot.environment.state);
  const backend = backendLabel(
    snapshot.stale && snapshot.backend.state !== "checking" ? "stale" : snapshot.backend.state,
    isLoading,
  );
  const database = databaseLabel(snapshot.database.state, snapshot.database.source);

  const mainText =
    isLoading && snapshot.backend.state === "checking"
      ? `${RUNTIME_BANNER_LABELS.loadingMain} · ${env} · ${database}`
      : `${env} · ${backend} · ${database}`;

  const checked = formatCheckedAt(snapshot.backend.checkedAt ?? snapshot.backend.lastSuccessfulAt);
  const freshnessText = checked
    ? `${RUNTIME_BANNER_LABELS.freshnessPrefix}: ${checked} — stare agregată backend`
    : null;

  const severity = deriveSeverity(snapshot, isLoading);
  const note = sessionNote(input.sessionState);

  const view: RuntimeStatusSummaryView = {
    mainText,
    severity,
    environmentLabel: env,
    backendLabel: backend,
    databaseLabel: database,
    isLoading,
    freshnessText,
    technicalStrip: buildTechnicalStrip(input),
    accessibleDescription: note ? `${mainText}. ${note}` : mainText,
    sessionNote: note,
  };

  assertNoForbiddenBannerText(view.mainText);
  return view;
}

/** Auth alone must never yield positive severity for a checking/empty snapshot. */
export function authCannotImplyHealthy(
  sessionState: BuildRuntimeStatusSummaryInput["sessionState"],
  snapshot: RuntimeTruthSnapshot = {
    backend: { state: "checking" },
    database: { state: "checking", source: "none" },
    environment: { state: "local" },
    diagnostics: { authorized: null, available: null },
    stale: false,
  },
): boolean {
  const view = buildRuntimeStatusSummary({
    snapshot,
    isLoading: true,
    sessionState: sessionState ?? "authenticated",
  });
  return view.severity !== "positive" && !view.mainText.includes("LIVE");
}
