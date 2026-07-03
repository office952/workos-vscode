/**
 * EnvironmentBanner — Global environment/source clarity strip.
 *
 * Shows the current application mode (DEV/MOCK, LIVE/DB, etc.)
 * so the operator always knows what kind of data they're seeing.
 *
 * Rules:
 *  - Does NOT change business logic or auth
 *  - Does NOT introduce mock fallback
 *  - Only displays current status clearly
 */
import { isMockEnabled, isDevAuthFallback } from "@/lib/mockGuard";
import { useAuth } from "@/contexts/AuthContext";
import { AlertTriangle, Database, Monitor, Shield } from "lucide-react";

export type EnvironmentMode = "dev_mock" | "live_db" | "dev_no_auth" | "unknown";

export function getEnvironmentMode(authState?: "loading" | "authenticated" | "unauthenticated" | "auth_config_missing" | "dev_auth_enabled"): EnvironmentMode {
  const mockOn = isMockEnabled();
  const devFallback = isDevAuthFallback();

  if (mockOn) return "dev_mock";
  if (authState === "authenticated") return "live_db";
  if (authState === "dev_auth_enabled" || devFallback) return "dev_no_auth";
  if (authState === "unauthenticated" || authState === "auth_config_missing") return "dev_no_auth";

  if (!mockOn && !devFallback) return "live_db";
  return "unknown";
}

export function getEnvironmentLabel(mode: EnvironmentMode): string {
  switch (mode) {
    case "dev_mock":
      return "DEV MOCK DATA — aceste date nu vin din API real.";
    case "dev_no_auth":
      return "Lipsă sesiune / autentificare necesară pentru API real.";
    case "live_db":
      return "MOD PRODUCȚIE — Sursa de date: backend live.";
    default:
      return "Mod necunoscut — verificați configurarea.";
  }
}

export function getEnvironmentShortLabel(mode: EnvironmentMode): string {
  switch (mode) {
    case "dev_mock":
      return "DEV / MOCK";
    case "dev_no_auth":
      return "DEV / NO AUTH";
    case "live_db":
      return "LIVE / DB";
    default:
      return "NECUNOSCUT";
  }
}

export default function EnvironmentBanner() {
  const { authState } = useAuth();
  const mode = getEnvironmentMode(authState);

  // In live/db mode, show a minimal green indicator — don't distract
  if (mode === "live_db") {
    return (
      <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-950/30 border-b border-emerald-900/30 text-emerald-400 text-[11px]">
        <Database className="w-3 h-3" />
        <span className="font-medium">LIVE / DB</span>
        <span className="text-emerald-500/70">— Sursa de date: backend live</span>
      </div>
    );
  }

  // Dev/mock modes — show amber warning banner
  const isDev = mode === "dev_mock" || mode === "dev_no_auth";

  return (
    <div
      className={`flex items-center gap-2 px-4 py-1.5 border-b text-[11px] ${
        isDev
          ? "bg-amber-950/30 border-amber-900/30 text-amber-400"
          : "bg-slate-800/50 border-slate-700/30 text-slate-400"
      }`}
    >
      {isDev ? (
        <AlertTriangle className="w-3 h-3 shrink-0" />
      ) : (
        <Monitor className="w-3 h-3 shrink-0" />
      )}
      <span className="font-semibold">{getEnvironmentShortLabel(mode)}</span>
      <span className={isDev ? "text-amber-500/70" : "text-slate-500"}>
        — {getEnvironmentLabel(mode).split("—")[1]?.trim() || getEnvironmentLabel(mode)}
      </span>
      {mode === "dev_no_auth" && (
        <span className="ml-auto flex items-center gap-1 text-amber-500/60">
          <Shield className="w-3 h-3" />
          Auth demo
        </span>
      )}
    </div>
  );
}