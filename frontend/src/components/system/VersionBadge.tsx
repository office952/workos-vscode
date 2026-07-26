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
      return `${base} bg-emerald-900/50 text-emerald-300 border border-emerald-700/70 shadow-[0_0_0_1px_rgba(16,185,129,0.08)]`;
    case "preview":
      return `${base} bg-amber-900/40 text-amber-300 border border-amber-800/60`;
    case "dev":
      return `${base} bg-slate-800 text-slate-300 border border-slate-700`;
    default:
      return `${base} bg-slate-800 text-slate-400 border border-slate-700`;
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
        <Activity className="w-3 h-3 text-slate-600" />
      </div>
    );
  }

  // Expanded variant
  if (state.status === "loading") {
    return (
      <div
        className="px-3 py-2 border-t border-wo-border-subtle text-[10px] text-slate-600 flex items-center gap-1.5"
        data-testid="version-badge"
      >
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-600 animate-pulse" />
        Loading version…
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div
        className="px-3 py-2 border-t border-wo-border-subtle text-[10px] text-slate-500"
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
        className="w-full px-3 py-2 flex items-center gap-2 text-left hover:bg-slate-900/40 transition-colors focus:outline-none focus:bg-slate-900/50"
        aria-expanded={popoverOpen}
        aria-label={`${app} ${version} ${env}`}
      >
        <Activity className="w-3 h-3 text-slate-500 shrink-0" />
        <div className="flex-1 min-w-0 leading-tight">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold text-slate-200 truncate">
              {app}{" "}
              <span className="font-mono text-slate-300">{version}</span>
            </span>
            <span className={envPillClasses(tone)}>
              <span
                className={`w-1 h-1 rounded-full ${envDotClasses(tone)}`}
              />
              {env}
            </span>
          </div>
          {scope && (
            <div className="text-[9px] text-slate-500 truncate font-mono">
              {scope}
            </div>
          )}
        </div>
      </button>

      {popoverOpen && (
        <div
          className="absolute bottom-full left-2 right-2 mb-1 z-50 rounded-md border border-slate-700/80 bg-slate-900/95 backdrop-blur-sm shadow-xl px-3 py-2.5 text-[10px] leading-tight"
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
            <span className="text-slate-200 font-semibold text-[11px]">
              {app} <span className="font-mono">{version}</span>
            </span>
          </div>

          {label && (
            <div className="text-slate-300 italic text-[10px] mb-1.5 border-l-2 border-slate-700 pl-2">
              {label}
            </div>
          )}

          <dl className="grid grid-cols-[64px_1fr] gap-x-2 gap-y-0.5 text-slate-400">
            {scope && (
              <>
                <dt className="text-slate-500">scope</dt>
                <dd className="font-mono text-slate-300 truncate">{scope}</dd>
              </>
            )}
            <dt className="text-slate-500">source</dt>
            <dd className="font-mono text-slate-300">{source}</dd>
            {buildTimeFmt && (
              <>
                <dt className="text-slate-500">build</dt>
                <dd className="font-mono text-slate-300">{buildTimeFmt}</dd>
              </>
            )}
            <dt className="text-slate-500">observed</dt>
            <dd className="font-mono text-slate-300 truncate">
              {data.observed_at}
            </dd>
          </dl>

          {diagnosticsOff && (
            <div className="mt-2 pt-2 border-t border-slate-800 flex items-center gap-1.5 text-slate-500">
              <ShieldOff className="w-3 h-3 shrink-0" />
              <span className="text-[9px]">
                Diagnostics gated off · <code>db-identity</code> disabled
              </span>
            </div>
          )}

          <div className="mt-1.5 text-[9px] text-slate-600">
            Read-only · <code>GET /api/v1/system/version</code>
          </div>
        </div>
      )}
    </div>
  );
}