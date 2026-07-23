/**
 * ExecutionDashboard — Sprint #12.
 *
 * READ-ONLY UI over `GET /api/v1/execution/dashboard`. This component
 * NEVER calls mutating endpoints, NEVER computes metrics, and NEVER
 * substitutes a value for one that the backend returned as null.
 *
 * Color coding (UI contract, not business rule):
 *   OK          -> emerald
 *   WARNING     -> amber
 *   CRITICAL    -> red
 *   UNCONFIRMED -> slate (neutral)
 *
 * Missing numeric fields (planned_time / actual_time / delta_time)
 * render as "—". Missing alert_severity renders as the word
 * "NECONFIRMAT" — never as "OK", never as 0.
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Activity, ChevronRight, RefreshCw, AlertTriangle, Info, ShieldAlert } from "lucide-react";
import {
  executionApi,
  type DashboardRow,
  type ExecutionStatus,
  type AlertSeverity,
} from "@/api/execution";
import FlowBreadcrumb, { executionBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import { ExecutionPlanStatesStrip } from "@/components/execution/ExecutionPlanStatesStrip";

// ---------------------------------------------------------------------------
// Formatting helpers — all null-safe. They ONLY handle presentation; they
// do not invent data. If the backend returned `null`, UI shows "—".
// ---------------------------------------------------------------------------

function formatMinutes(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(1)} min`;
}

function statusBadgeCls(status: ExecutionStatus): string {
  switch (status) {
    case "OK":
      return "bg-emerald-900/40 text-emerald-300 border-emerald-700";
    case "WARNING":
      return "bg-amber-900/40 text-amber-300 border-amber-700";
    case "CRITICAL":
      return "bg-red-900/40 text-red-300 border-red-700";
    case "UNCONFIRMED":
    default:
      return "bg-slate-800/60 text-slate-400 border-slate-600";
  }
}

function alertBadgeCls(severity: AlertSeverity | null): string {
  if (severity === "CRITICAL") return "bg-red-900/40 text-red-300 border-red-700";
  if (severity === "WARNING") return "bg-amber-900/40 text-amber-300 border-amber-700";
  return "bg-slate-800/60 text-slate-500 border-slate-700";
}

function presenceBadgeCls(value: "present" | "absent"): string {
  return value === "present"
    ? "bg-blue-900/30 text-blue-300 border-blue-800/60"
    : "bg-slate-800/60 text-slate-500 border-slate-700";
}

export default function ExecutionDashboard() {
  const navigate = useNavigate();
  const [rows, setRows] = useState<DashboardRow[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await executionApi.getExecutionDashboard();
      setRows(data.rows);
      setTotal(data.total);
      setLastRefreshed(new Date().toLocaleTimeString("ro-RO"));
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Counts by status — trivial UI summary, NOT a business metric.
  // Uses the exact values the backend assigned per row; nothing invented.
  // The Record is pre-initialised for all four statuses so every cell is
  // a known number (starting from zero). Backend-returned numeric values
  // are never coerced via fallback operators anywhere in this file.
  const countByStatus: Record<ExecutionStatus, number> = {
    OK: 0,
    WARNING: 0,
    CRITICAL: 0,
    UNCONFIRMED: 0,
  };
  for (const r of rows) {
    countByStatus[r.divergence_status] = countByStatus[r.divergence_status] + 1;
  }

  // Detect auth-related errors
  const isAuthError = error && (error.includes("401") || error.includes("403") || error.toLowerCase().includes("unauthorized") || error.toLowerCase().includes("forbidden") || error.toLowerCase().includes("auth"));
  const isNetworkError = error && (error.includes("fetch") || error.includes("network") || error.includes("ECONNREFUSED") || error.includes("Failed to fetch"));

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <FlowBreadcrumb items={executionBreadcrumb()} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Execution Dashboard</h1>
          {total !== null && (
            <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full ml-1">
              {total} comenzi
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/execution/reality-review"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-colors"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            Review Realitate
          </Link>
          {lastRefreshed && (
            <span className="text-[11px] text-slate-500">
              Ultima reîmprospătare: {lastRefreshed}
            </span>
          )}
          <button
            onClick={() => void load()}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-md bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <ExecutionPlanStatesStrip hasPreview hasDraftPlan={false} hasOperationalTasks={false} operationalBlocked />

      {/* Summary cards — one per status. Purely reflective. */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#1A2236] border border-[#2A3548] border-t-2 border-t-emerald-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wide">OK</p>
          <p className="text-[20px] font-bold text-emerald-400 mt-1">{countByStatus.OK}</p>
        </div>
        <div className="bg-[#1A2236] border border-[#2A3548] border-t-2 border-t-amber-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wide">Warning</p>
          <p className="text-[20px] font-bold text-amber-400 mt-1">{countByStatus.WARNING}</p>
        </div>
        <div className="bg-[#1A2236] border border-[#2A3548] border-t-2 border-t-red-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wide">Critical</p>
          <p className="text-[20px] font-bold text-red-400 mt-1">{countByStatus.CRITICAL}</p>
        </div>
        <div className="bg-[#1A2236] border border-[#2A3548] border-t-2 border-t-slate-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wide">Neconfirmat</p>
          <p className="text-[20px] font-bold text-slate-300 mt-1">{countByStatus.UNCONFIRMED}</p>
        </div>
      </div>

      {/* Error state — improved with auth/network detection */}
      {error && (
        <div className="space-y-2">
          <div className={`rounded-lg px-4 py-3 text-[12px] border ${
            isAuthError
              ? "bg-amber-900/20 border-amber-800/60 text-amber-300"
              : "bg-red-900/20 border-red-800/60 text-red-300"
          }`}>
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="space-y-1">
                <p className="font-semibold">
                  {isAuthError
                    ? "Autentificare necesară"
                    : isNetworkError
                      ? "Backend indisponibil"
                      : "Eroare la încărcarea dashboard-ului"}
                </p>
                <p className="text-[11px] opacity-80">
                  {isAuthError
                    ? "Sesiunea a expirat sau nu ai permisiuni. Reautentifică-te sau verifică setările de acces."
                    : isNetworkError
                      ? "Nu s-a putut conecta la server. Verifică dacă backend-ul rulează și este accesibil."
                      : error}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-start gap-2 px-3 py-2 bg-blue-900/10 border border-blue-800/20 rounded-lg">
            <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-blue-300/80">
              <strong>Sugestie:</strong> Dacă rulezi în modul mock, activează <code className="bg-slate-800 px-1 rounded">VITE_ENABLE_MOCK_DATA=true</code> în fișierul <code className="bg-slate-800 px-1 rounded">.env</code>.
              Pentru modul live, asigură-te că backend-ul FastAPI este pornit pe portul configurat.
            </p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && rows.length === 0 && !error && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <p className="text-[12px] text-slate-500">Se încarcă dashboard-ul...</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && rows.length === 0 && (
        <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg px-6 py-10 text-center">
          <Activity className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-[13px] text-slate-400">Nicio comandă de afișat.</p>
          <p className="text-[11px] text-slate-600 mt-1">Comenzile vor apărea aici după ce sunt create din modulul Comenzi.</p>
        </div>
      )}

      {/* Table */}
      {rows.length > 0 && (
        <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead className="bg-[#0F1626] border-b border-[#2A3548]">
                <tr className="text-left text-slate-400 uppercase text-[10px] tracking-wide">
                  <th className="px-3 py-2 font-semibold">Comandă</th>
                  <th className="px-3 py-2 font-semibold">Plan</th>
                  <th className="px-3 py-2 font-semibold">Realitate</th>
                  <th className="px-3 py-2 font-semibold">Status</th>
                  <th className="px-3 py-2 font-semibold">Alertă</th>
                  <th className="px-3 py-2 font-semibold text-right">Planificat</th>
                  <th className="px-3 py-2 font-semibold text-right">Actual</th>
                  <th className="px-3 py-2 font-semibold text-right">Δ</th>
                  <th className="px-3 py-2 font-semibold w-8"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr
                    key={r.order_id}
                    onClick={() => navigate(`/execution/${r.order_id}`)}
                    className="border-b border-[#2A3548] last:border-b-0 hover:bg-[#22304B] cursor-pointer transition-colors"
                  >
                    <td className="px-3 py-2.5">
                      <div className="flex flex-col">
                        <span className="text-slate-200 font-semibold">{r.order_code}</span>
                        <span className="text-[10px] text-slate-500">#{r.order_id}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`inline-block px-1.5 py-0.5 text-[10px] font-semibold rounded border ${presenceBadgeCls(r.plan_status)}`}
                      >
                        {r.plan_status === "present" ? "PREZENT" : "LIPSĂ"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`inline-block px-1.5 py-0.5 text-[10px] font-semibold rounded border ${presenceBadgeCls(r.reality_status)}`}
                      >
                        {r.reality_status === "present" ? "PREZENT" : "LIPSĂ"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded border ${statusBadgeCls(r.divergence_status)}`}
                      >
                        {r.divergence_status === "UNCONFIRMED"
                          ? "NECONFIRMAT"
                          : r.divergence_status}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded border ${alertBadgeCls(r.alert_severity)}`}
                      >
                        {r.alert_severity === null ? "—" : r.alert_severity}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right text-slate-300 tabular-nums">
                      {formatMinutes(r.planned_time)}
                    </td>
                    <td className="px-3 py-2.5 text-right text-slate-300 tabular-nums">
                      {formatMinutes(r.actual_time)}
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums">
                      {r.delta_time === null ? (
                        <span className="text-slate-500">—</span>
                      ) : (
                        <span
                          className={
                            r.delta_time > 0
                              ? "text-amber-300"
                              : r.delta_time < 0
                                ? "text-emerald-300"
                                : "text-slate-300"
                          }
                        >
                          {r.delta_time > 0 ? "+" : ""}
                          {r.delta_time.toFixed(1)}
                        </span>
                      )}
                    </td>
                    <td
                      className="px-3 py-2.5 text-slate-500"
                      title="Deschide detaliu comandă"
                      aria-label="Deschide detaliu comandă"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Footer note — explicit reminder that this view is read-only */}
      <p className="text-[10px] text-slate-600 italic">
        Dashboard-ul reflectă starea raportată de backend. Nicio valoare nu este
        calculată sau presupusă în interfață. Reîmprospătarea este manuală.
        Click pe un rând deschide pagina de detaliu read-only pentru comanda
        respectivă.
      </p>
    </div>
  );
}