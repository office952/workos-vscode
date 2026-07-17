/**
 * EnvironmentBanner — Global runtime health strip (UI-TRUTH-01B).
 *
 * Driven by useRuntimeHealth + RuntimeStatusSummary.
 * Auth/session is a separate note — never implies LIVE/DB health.
 */

import { AlertTriangle, CheckCircle2, HelpCircle, Loader2, XCircle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useRuntimeHealth } from "@/hooks/useRuntimeHealth";
import {
  buildRuntimeStatusSummary,
  type BannerSeverity,
  type RuntimeStatusSummaryView,
} from "@/components/workos/RuntimeStatusSummary";
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
  // Avoid noisy announcements on every poll when healthy/warning steady-state
  if (isLoading) return "polite";
  if (severity === "critical") return "polite";
  return "off";
}

export function EnvironmentBannerView({ view }: { view: RuntimeStatusSummaryView }) {
  const muted =
    view.severity === "positive"
      ? "text-emerald-500/70"
      : view.severity === "warning"
        ? "text-amber-500/70"
        : view.severity === "critical"
          ? "text-red-400/70"
          : "text-slate-500";

  return (
    <div
      className={`flex flex-wrap items-center gap-x-2 gap-y-0.5 px-4 py-1.5 border-b text-[11px] ${severityClasses(view.severity)}`}
      role="status"
      aria-live={ariaLivePolitely(view.severity, view.isLoading)}
      aria-label={view.accessibleDescription}
      data-testid="environment-banner"
      data-severity={view.severity}
    >
      <SeverityIcon severity={view.severity} isLoading={view.isLoading} />
      <span className="font-medium" data-testid="environment-banner-main">
        {view.mainText}
      </span>
      {view.freshnessText ? (
        <span className={muted} data-testid="environment-banner-freshness">
          — {view.freshnessText}
        </span>
      ) : null}
      {view.sessionNote ? (
        <span className={`ml-auto ${muted}`} data-testid="environment-banner-session">
          {view.sessionNote}
        </span>
      ) : null}
      {view.technicalStrip ? (
        <span
          className={`basis-full w-full font-mono text-[10px] opacity-70 ${muted}`}
          data-testid="environment-banner-tech"
        >
          {view.technicalStrip}
        </span>
      ) : null}
    </div>
  );
}

export default function EnvironmentBanner() {
  const { authState } = useAuth();
  const { snapshot, isLoading, lastError } = useRuntimeHealth();

  const view = buildRuntimeStatusSummary({
    snapshot,
    isLoading,
    sessionState: mapAuthToSession(authState),
    lastError,
  });

  return <EnvironmentBannerView view={view} />;
}
