/**
 * EnvironmentBanner — Global runtime health strip (UI-TRUTH-01B + 01C).
 *
 * Driven by useRuntimeHealth + RuntimeStatusSummary + RuntimeStatusDetails.
 * Auth/session is a separate note — never implies LIVE/DB health.
 */

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  Loader2,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useRuntimeHealth } from "@/hooks/useRuntimeHealth";
import {
  buildRuntimeStatusSummary,
  type BannerSeverity,
  type RuntimeStatusSummaryView,
} from "@/components/workos/RuntimeStatusSummary";
import { RuntimeStatusDetails } from "@/components/workos/RuntimeStatusDetails";
import type { SessionTruthState } from "@/types/runtimeStatus";

function mapAuthToSession(
  authState: ReturnType<typeof useAuth>["authState"],
): SessionTruthState | "loading" | "auth_config_missing" | "dev_auth_enabled" {
  if (authState === "authenticated") return "authenticated";
  if (authState === "unauthenticated") return "unauthenticated";
  if (authState === "dev_auth_enabled") return "dev_auth_enabled";
  if (authState === "auth_config_missing") return "auth_config_missing";
  if (authState === "loading") return "loading";
  return "unknown";
}

function severityClasses(severity: BannerSeverity): string {
  switch (severity) {
    case "positive":
      return "bg-emerald-950/30 border-emerald-900/30 text-emerald-400";
    case "warning":
      return "bg-amber-950/30 border-amber-900/30 text-amber-400";
    case "critical":
      return "bg-red-950/35 border-red-900/40 text-red-400";
    case "neutral":
    default:
      return "bg-slate-800/50 border-slate-700/30 text-slate-300";
  }
}

function SeverityIcon({
  severity,
  isLoading,
}: {
  severity: BannerSeverity;
  isLoading: boolean;
}) {
  if (isLoading) {
    return <Loader2 className="w-3 h-3 shrink-0 animate-spin" aria-hidden />;
  }
  switch (severity) {
    case "positive":
      return <CheckCircle2 className="w-3 h-3 shrink-0" aria-hidden />;
    case "warning":
      return <AlertTriangle className="w-3 h-3 shrink-0" aria-hidden />;
    case "critical":
      return <XCircle className="w-3 h-3 shrink-0" aria-hidden />;
    default:
      return <HelpCircle className="w-3 h-3 shrink-0" aria-hidden />;
  }
}

function ariaLivePolitely(severity: BannerSeverity, isLoading: boolean): "polite" | "off" {
  if (isLoading) return "polite";
  if (severity === "critical") return "polite";
  return "off";
}

export function EnvironmentBannerView({
  view,
  isRefreshing = false,
  onRefresh,
  detailsOpen = false,
  onToggleDetails,
  details,
}: {
  view: RuntimeStatusSummaryView;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  detailsOpen?: boolean;
  onToggleDetails?: () => void;
  details?: React.ReactNode;
}) {
  const muted =
    view.severity === "positive"
      ? "text-emerald-500/70"
      : view.severity === "warning"
        ? "text-amber-500/70"
        : view.severity === "critical"
          ? "text-red-400/70"
          : "text-slate-500";

  const busy = view.isLoading || isRefreshing;

  return (
    <div
      className={`flex flex-col gap-0 px-4 py-1.5 border-b text-[11px] ${severityClasses(view.severity)}`}
      role="status"
      aria-live={ariaLivePolitely(view.severity, busy)}
      aria-label={view.accessibleDescription}
      data-testid="environment-banner"
      data-severity={view.severity}
      data-stale={view.isStale ? "true" : "false"}
    >
      <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
        <SeverityIcon severity={view.severity} isLoading={busy} />
        <span className="font-medium" data-testid="environment-banner-main">
          {view.mainText}
        </span>
        {view.staleLabel ? (
          <span
            className="px-1.5 py-0.5 rounded border border-current/30 text-[10px] font-semibold"
            data-testid="environment-banner-stale"
          >
            {view.staleLabel}
          </span>
        ) : null}
        {view.freshnessText ? (
          <span className={muted} data-testid="environment-banner-freshness">
            — {view.freshnessText}
          </span>
        ) : null}
        {view.lastKnownText ? (
          <span className={muted} data-testid="environment-banner-last-known">
            — {view.lastKnownText}
          </span>
        ) : null}

        <div className="ml-auto flex items-center gap-1.5">
          {view.sessionNote ? (
            <span className={muted} data-testid="environment-banner-session">
              {view.sessionNote}
            </span>
          ) : null}
          {onToggleDetails ? (
            <button
              type="button"
              onClick={onToggleDetails}
              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded hover:bg-black/20 transition-colors"
              aria-expanded={detailsOpen}
              aria-controls="runtime-status-details-panel"
              data-testid="environment-banner-details-toggle"
            >
              {detailsOpen ? (
                <ChevronDown className="w-3 h-3" aria-hidden />
              ) : (
                <ChevronRight className="w-3 h-3" aria-hidden />
              )}
              <span>{view.detailsTitle}</span>
            </button>
          ) : null}
          {onRefresh ? (
            <button
              type="button"
              onClick={onRefresh}
              disabled={busy}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-black/20 transition-colors disabled:opacity-50"
              aria-label={view.showRetry ? view.retryLabel : view.refreshLabel}
              data-testid="environment-banner-refresh"
            >
              <RefreshCw className={`w-3 h-3 ${busy ? "animate-spin" : ""}`} aria-hidden />
              <span>{view.showRetry ? view.retryLabel : view.refreshLabel}</span>
            </button>
          ) : null}
        </div>
      </div>

      {view.technicalStrip && !detailsOpen ? (
        <span
          className={`basis-full w-full font-mono text-[10px] opacity-70 ${muted}`}
          data-testid="environment-banner-tech"
        >
          {view.technicalStrip}
        </span>
      ) : null}

      {detailsOpen && details ? (
        <div id="runtime-status-details-panel">{details}</div>
      ) : null}
    </div>
  );
}

export default function EnvironmentBanner() {
  const { authState } = useAuth();
  const { snapshot, isLoading, isRefreshing, refresh, lastError } = useRuntimeHealth({
    fetchDiagnostics: true,
  });
  const [detailsOpen, setDetailsOpen] = useState(false);

  const view = buildRuntimeStatusSummary({
    snapshot,
    isLoading: isLoading || isRefreshing,
    sessionState: mapAuthToSession(authState),
    lastError,
    serviceVersion: snapshot.environment.serviceVersion,
  });

  return (
    <EnvironmentBannerView
      view={view}
      isRefreshing={isRefreshing}
      onRefresh={() => {
        void refresh();
      }}
      detailsOpen={detailsOpen}
      onToggleDetails={() => setDetailsOpen((open) => !open)}
      details={
        <RuntimeStatusDetails
          snapshot={snapshot}
          view={view}
          isLoading={isLoading}
          isRefreshing={isRefreshing}
          lastError={lastError}
        />
      }
    />
  );
}
