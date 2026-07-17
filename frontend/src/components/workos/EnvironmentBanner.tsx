/**
 * EnvironmentBanner — Global runtime health (UI-TRUTH-01B + 01C).
 *
 * Build 3 operator UI closeout: compact header chip by default.
 * Full-width persistent strip removed for staging/informational severity.
 * Critical backend failures keep a thin dismissible one-line alert + expandable details.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
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
      return "bg-emerald-950/40 border-emerald-800/50 text-emerald-300";
    case "warning":
      return "bg-amber-950/40 border-amber-800/50 text-amber-300";
    case "critical":
      return "bg-red-950/45 border-red-800/55 text-red-300";
    case "neutral":
    default:
      return "bg-slate-800/70 border-slate-600/50 text-slate-300";
  }
}

function criticalStripClasses(): string {
  return "bg-red-950/40 border-red-900/45 text-red-300";
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

function compactChipLabel(view: RuntimeStatusSummaryView): string {
  if (view.isLoading) return "Se verifică";
  if (view.severity === "critical") return "Stare sistem";
  return view.environmentLabel || "Stare sistem";
}

export function EnvironmentBannerView({
  view,
  isRefreshing = false,
  onRefresh,
  detailsOpen = false,
  onToggleDetails,
  details,
  criticalStripDismissed = false,
  onDismissCriticalStrip,
}: {
  view: RuntimeStatusSummaryView;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  detailsOpen?: boolean;
  onToggleDetails?: () => void;
  details?: React.ReactNode;
  criticalStripDismissed?: boolean;
  onDismissCriticalStrip?: () => void;
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
  const showCriticalStrip = view.severity === "critical" && !criticalStripDismissed;
  const chipLabel = compactChipLabel(view);

  return (
    <div
      className="relative flex items-center gap-1"
      role="status"
      aria-live={ariaLivePolitely(view.severity, busy)}
      aria-label={view.accessibleDescription}
      data-testid="environment-banner"
      data-presentation="compact"
      data-severity={view.severity}
      data-stale={view.isStale ? "true" : "false"}
      data-critical-strip={showCriticalStrip ? "true" : "false"}
      data-details-open={detailsOpen ? "true" : "false"}
    >
      <button
        type="button"
        onClick={onToggleDetails}
        title={view.accessibleDescription}
        aria-expanded={detailsOpen}
        aria-controls="runtime-status-details-panel"
        className={`inline-flex max-w-[220px] items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-medium transition-colors hover:brightness-110 ${severityClasses(view.severity)}`}
        data-testid="environment-banner-details-toggle"
      >
        <SeverityIcon severity={view.severity} isLoading={busy} />
        <span className="truncate" data-testid="environment-banner-main">
          {chipLabel}
        </span>
        {view.staleLabel ? (
          <span
            className="rounded border border-current/30 px-1 text-[9px] font-semibold"
            data-testid="environment-banner-stale"
          >
            {view.staleLabel}
          </span>
        ) : null}
        {detailsOpen ? (
          <ChevronDown className="h-3 w-3 shrink-0 opacity-80" aria-hidden />
        ) : (
          <ChevronRight className="h-3 w-3 shrink-0 opacity-80" aria-hidden />
        )}
      </button>

      {onRefresh ? (
        <button
          type="button"
          onClick={onRefresh}
          disabled={busy}
          className="inline-flex items-center rounded-md border border-slate-700/70 bg-slate-900/50 p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-50"
          aria-label={view.showRetry ? view.retryLabel : view.refreshLabel}
          data-testid="environment-banner-refresh"
        >
          <RefreshCw className={`h-3 w-3 ${busy ? "animate-spin" : ""}`} aria-hidden />
        </button>
      ) : null}

      {showCriticalStrip ? (
        <div
          className={`absolute right-0 top-[calc(100%+6px)] z-40 w-[min(420px,calc(100vw-2rem))] rounded-md border px-2.5 py-1.5 text-[11px] shadow-lg ${criticalStripClasses()}`}
          data-testid="environment-banner-critical-strip"
        >
          <div className="flex items-start gap-2">
            <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="font-medium leading-snug" data-testid="environment-banner-critical-text">
                {view.mainText}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={onToggleDetails}
                  className="underline-offset-2 hover:underline"
                  data-testid="environment-banner-critical-open-details"
                >
                  {view.detailsTitle}
                </button>
                {onDismissCriticalStrip ? (
                  <button
                    type="button"
                    onClick={onDismissCriticalStrip}
                    className={`${muted} hover:underline`}
                    data-testid="environment-banner-critical-dismiss"
                  >
                    Ascunde
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {detailsOpen ? (
        <div
          id="runtime-status-details-panel"
          className="absolute right-0 top-[calc(100%+6px)] z-50 w-[min(440px,calc(100vw-2rem))] rounded-md border border-slate-700 bg-[#0D1321] p-3 text-[11px] text-slate-200 shadow-xl"
          data-testid="environment-banner-details-panel"
        >
          <div className="mb-2 flex flex-wrap items-center gap-2 border-b border-slate-700/70 pb-2">
            <SeverityIcon severity={view.severity} isLoading={busy} />
            <span className="min-w-0 flex-1 font-medium text-slate-100">{view.mainText}</span>
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
            {view.sessionNote ? (
              <span className={muted} data-testid="environment-banner-session">
                {view.sessionNote}
              </span>
            ) : null}
          </div>
          {view.technicalStrip ? (
            <p
              className={`mb-2 font-mono text-[10px] opacity-70 ${muted}`}
              data-testid="environment-banner-tech"
            >
              {view.technicalStrip}
            </p>
          ) : null}
          {details}
          <div className="mt-2 flex flex-wrap items-center gap-3 border-t border-slate-700/70 pt-2">
            <Link
              to="/modules"
              className="text-violet-300 hover:text-violet-200"
              data-testid="environment-banner-control-center-link"
            >
              Control Center
            </Link>
          </div>
        </div>
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
  const [criticalStripDismissed, setCriticalStripDismissed] = useState(false);

  const view = buildRuntimeStatusSummary({
    snapshot,
    isLoading: isLoading || isRefreshing,
    sessionState: mapAuthToSession(authState),
    lastError,
    serviceVersion: snapshot.environment.serviceVersion,
  });

  useEffect(() => {
    if (view.severity === "critical") {
      setCriticalStripDismissed(false);
    }
  }, [view.severity, view.mainText]);

  return (
    <EnvironmentBannerView
      view={view}
      isRefreshing={isRefreshing}
      onRefresh={() => {
        void refresh();
      }}
      detailsOpen={detailsOpen}
      onToggleDetails={() => setDetailsOpen((open) => !open)}
      criticalStripDismissed={criticalStripDismissed}
      onDismissCriticalStrip={() => setCriticalStripDismissed(true)}
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
