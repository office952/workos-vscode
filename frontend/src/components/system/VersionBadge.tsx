/**
 * Runtime release version indicator.
 *
 * Rules (canonical, Sprint #38, polished Sprint SAFE WORKSPACE):
 *   - Data ONLY from GET /api/v1/system/version (backend/runtime config).
 *   - Never invents a fallback version; on error shows "Version unavailable".
 *   - Read-only; zero business logic.
 *   - Hover/focus reveals an expanded popover with all non-sensitive fields
 *     already present in the /system/version payload (no new request, no
 *     new endpoint, no DB, no publish).
 *
 * Rendered discreetly in the sidebar footer, above the collapse toggle.
 */

import { useEffect, useRef, useState } from "react";
import { Activity, ShieldOff } from "lucide-react";
import {
  fetchSystemVersion,
  type SystemVersionPayload,
} from "@/api/system";
import { useAuth } from "@/contexts/AuthContext";

type State =
  | { status: "loading" }
  | { status: "ready"; data: SystemVersionPayload }
  | { status: "error"; message: string };

type EnvTone = "live" | "preview" | "dev" | "unknown";

function classifyEnv(env: string | null): EnvTone {
  const e = (env || "").toLowerCase();
  if (e === "live" || e === "prod" || e === "production") return "live";
  if (e === "app_viewer" || e === "preview") return "preview";
  if (e === "dev" || e === "development" || e === "local") return "dev";
  return "unknown";
}

function envPillClasses(tone: EnvTone): string {
  const base =
    "inline-flex items-center gap-1 px-1.5 py-[1px] rounded text-[9px] font-bold uppercase tracking-wider leading-none";
  switch (tone) {
    case "live":
      return `${base} border border-wo-success/40 bg-wo-success-muted text-wo-success`;
    case "preview":
      return `${base} border border-wo-warning/40 bg-wo-warning-muted text-amber-900 dark:text-wo-warning`;
    case "dev":
      return `${base} border border-wo-border-strong bg-wo-surface-inset text-wo-text-muted`;
    default:
      return `${base} border border-wo-border-subtle bg-wo-surface-inset text-wo-text-dim`;
  }
}

function envDotClasses(tone: EnvTone): string {
  switch (tone) {
    case "live":
      return "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]";
    case "preview":
      return "bg-amber-400";
    case "dev":
      return "bg-slate-400";
    default:
      return "bg-slate-500";
  }
}

function formatBuildTime(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const yyyy = d.getUTCFullYear();
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mi = String(d.getUTCMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${mi} UTC`;
}

interface VersionBadgeProps {
  collapsed?: boolean;
}

export default function VersionBadge({ collapsed = false }: VersionBadgeProps) {
  const { canAccessProtectedApi } = useAuth();
  const [state, setState] = useState<State>({ status: "loading" });
  const [popoverOpen, setPopoverOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!canAccessProtectedApi) {
      setState({ status: "error", message: "Protected API gated by auth state" });
      return;
    }

    let alive = true;
    fetchSystemVersion()
      .then((data) => {
        if (alive) setState({ status: "ready", data });
      })
      .catch((err: unknown) => {
        if (alive) {
          const message = err instanceof Error ? err.message : "unknown error";
          setState({ status: "error", message });
        }
      });
    return () => {
      alive = false;
    };
  }, [canAccessProtectedApi]);

  // Collapsed mini-variant: a single dot + environment letter.
  if (collapsed) {
    if (state.status === "ready") {
      const env = state.data.environment || "?";
      const tone = classifyEnv(env);
      const letter = env.charAt(0).toUpperCase() || "?";
      return (
        <div
          className="flex items-center justify-center h-8 border-t border-wo-border-subtle"
          title={`${state.data.app_name || "WorkOS"} ${
            state.data.release_version || ""
          } · ${env}`}
          data-testid="version-badge-collapsed"
        >
          <span className={envPillClasses(tone)}>
            <span className={`w-1 h-1 rounded-full ${envDotClasses(tone)}`} />
            {letter}
          </span>
        </div>
      );
    }
    return (
      <div
        className="flex items-center justify-center h-8 border-t border-wo-border-subtle"
        title="Version unavailable"
        data-testid="version-badge-collapsed"
      >
        <Activity className="w-3 h-3 text-wo-text-dim" />
      </div>
    );
  }

  // Expanded variant
  if (state.status === "loading") {
    return (
      <div
        className="px-3 py-2 border-t border-wo-border-subtle text-[10px] text-wo-text-dim flex items-center gap-1.5"
        data-testid="version-badge"
      >
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-wo-text-dim animate-pulse" />
        Loading version…
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div
        className="px-3 py-2 border-t border-wo-border-subtle text-[10px] text-wo-text-muted"
        title={state.message}
        data-testid="version-badge"
      >
        Version unavailable
      </div>
    );
  }

  const { data } = state;
  const app = data.app_name || "WorkOS";
  const version = data.release_version || "—";
  const env = data.environment || "unknown";
  const tone = classifyEnv(env);
  const scope = data.release_scope || "";
  const label = data.release_label || "";
  const source = data.source || "unknown";
  const buildTimeFmt = formatBuildTime(data.build_time);
  // Static hint: the diagnostic /db-identity endpoint is gated OFF by
  // default in the live build. We surface this as passive info only,
  // without making any new network call.
  const diagnosticsOff = tone === "live";

  return (
    <div
      ref={containerRef}
      className="relative border-t border-wo-border-subtle"
      onMouseEnter={() => setPopoverOpen(true)}
      onMouseLeave={() => setPopoverOpen(false)}
      onFocus={() => setPopoverOpen(true)}
      onBlur={() => setPopoverOpen(false)}
      data-testid="version-badge"
    >
      <button
        type="button"
        className="w-full px-3 py-2 flex items-center gap-2 text-left hover:bg-wo-hover transition-colors focus:outline-none focus:bg-wo-active"
        aria-expanded={popoverOpen}
        aria-label={`${app} ${version} ${env}`}
      >
        <Activity className="w-3 h-3 text-wo-text-dim shrink-0" />
        <div className="flex-1 min-w-0 leading-tight">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold text-wo-text-secondary truncate">
              {app}{" "}
              <span className="font-mono text-wo-text-muted">{version}</span>
            </span>
            <span className={envPillClasses(tone)}>
              <span
                className={`w-1 h-1 rounded-full ${envDotClasses(tone)}`}
              />
              {env}
            </span>
          </div>
          {scope && (
            <div className="text-[9px] text-wo-text-dim truncate font-mono">
              {scope}
            </div>
          )}
        </div>
      </button>

      {popoverOpen && (
        <div
          className="absolute bottom-full left-2 right-2 mb-1 z-50 rounded-md border border-wo-border-strong bg-wo-surface-raised shadow-xl px-3 py-2.5 text-[10px] leading-tight"
          role="tooltip"
          data-testid="version-badge-popover"
        >
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className={envPillClasses(tone)}>
              <span
                className={`w-1 h-1 rounded-full ${envDotClasses(tone)}`}
              />
              {env}
            </span>
            <span className="text-wo-text-primary font-semibold text-[11px]">
              {app} <span className="font-mono text-wo-text-muted">{version}</span>
            </span>
          </div>

          {label && (
            <div className="text-wo-text-secondary italic text-[10px] mb-1.5 border-l-2 border-wo-border-strong pl-2">
              {label}
            </div>
          )}

          <dl className="grid grid-cols-[64px_1fr] gap-x-2 gap-y-0.5 text-wo-text-muted">
            {scope && (
              <>
                <dt className="text-wo-text-dim">scope</dt>
                <dd className="font-mono text-wo-text-secondary truncate">{scope}</dd>
              </>
            )}
            <dt className="text-wo-text-dim">source</dt>
            <dd className="font-mono text-wo-text-secondary">{source}</dd>
            {buildTimeFmt && (
              <>
                <dt className="text-wo-text-dim">build</dt>
                <dd className="font-mono text-wo-text-secondary">{buildTimeFmt}</dd>
              </>
            )}
            <dt className="text-wo-text-dim">observed</dt>
            <dd className="font-mono text-wo-text-secondary truncate">
              {data.observed_at}
            </dd>
          </dl>

          {diagnosticsOff && (
            <div className="mt-2 pt-2 border-t border-wo-border-subtle flex items-center gap-1.5 text-wo-text-dim">
              <ShieldOff className="w-3 h-3 shrink-0" />
              <span className="text-[9px]">
                Diagnostics gated off · <code>db-identity</code> disabled
              </span>
            </div>
          )}

          <div className="mt-1.5 text-[9px] text-wo-text-dim">
            Read-only · <code>GET /api/v1/system/version</code>
          </div>
        </div>
      )}
    </div>
  );
}