/**
 * Operational Reality Review — read-only gaps dashboard.
 * Reflects backend GET /api/v1/operational-reality/review only.
 * No mutations, no cost/profit/salary display.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  ExternalLink,
  Filter,
  Info,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import FlowBreadcrumb, { operationalRealityReviewBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import {
  getOperationalRealityReview,
  type GapCategory,
  type GapSeverity,
  type OperationalRealityReviewResponse,
  type RealityGap,
} from "@/api/operationalRealityReview";

type SeverityFilter = "all" | GapSeverity;
type CategoryFilter = "all" | GapCategory;

function severityBadgeCls(severity: GapSeverity): string {
  switch (severity) {
    case "critical":
      return "bg-red-900/40 text-red-300 border-red-700";
    case "warning":
      return "bg-amber-900/40 text-amber-300 border-amber-700";
    default:
      return "bg-slate-800/60 text-slate-400 border-slate-600";
  }
}

function severityLabel(severity: GapSeverity): string {
  if (severity === "critical") return "Critical";
  if (severity === "warning") return "Warning";
  return "Info";
}

function categoryLabel(category: GapCategory): string {
  if (category === "atelier") return "Atelier";
  if (category === "montaj_teren") return "Montaj teren";
  return "Materiale";
}

function GapLinks({ gap }: { gap: RealityGap }) {
  const links = [
    gap.links.order ? { to: gap.links.order, label: "Comandă" } : null,
    gap.links.execution_detail ? { to: gap.links.execution_detail, label: "Execuție" } : null,
    gap.links.operator ? { to: gap.links.operator, label: "Operator" } : null,
    gap.links.tablet ? { to: gap.links.tablet, label: "Tablet" } : null,
    gap.links.field_installation
      ? { to: gap.links.field_installation, label: "Montaj" }
      : null,
  ].filter(Boolean) as { to: string; label: string }[];

  if (links.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {links.map((l) => (
        <Link
          key={l.to + l.label}
          to={l.to}
          className="inline-flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300"
        >
          <ExternalLink className="w-3 h-3" />
          {l.label}
        </Link>
      ))}
    </div>
  );
}

export default function OperationalRealityReview() {
  const [data, setData] = useState<OperationalRealityReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const review = await getOperationalRealityReview();
      setData(review);
      setLastRefreshed(new Date().toLocaleTimeString("ro-RO"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const filteredGaps = useMemo(() => {
    if (!data) return [];
    return data.gaps.filter((g) => {
      if (severityFilter !== "all" && g.severity !== severityFilter) return false;
      if (categoryFilter !== "all" && g.category !== categoryFilter) return false;
      return true;
    });
  }, [data, severityFilter, categoryFilter]);

  const summary = data?.summary;

  return (
    <div className="space-y-4">
      <FlowBreadcrumb items={operationalRealityReviewBreadcrumb()} />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Operational Reality Review</h1>
          {data?.read_only && (
            <span className="text-[10px] text-emerald-400 bg-emerald-900/30 border border-emerald-800 px-2 py-0.5 rounded-full">
              Read-only
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
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

      <p className="text-[12px] text-slate-500">
        Panou de verificare a calității realității operaționale colectate. Evidențiază
        lipsuri fără a modifica datele, fără auto-repair și fără calcule financiare.
      </p>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg px-4 py-3 text-[12px] text-red-300">
          {error}
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SummaryCard label="Taskuri analizate" value={summary.total_tasks_analyzed} />
          <SummaryCard label="Cu angajat" value={summary.tasks_with_employee} accent="emerald" />
          <SummaryCard label="Fără angajat" value={summary.tasks_without_employee} accent="amber" />
          <SummaryCard label="Finalizate" value={summary.tasks_completed} />
          <SummaryCard
            label="Pornite, nefinalizate"
            value={summary.tasks_started_not_completed}
            accent="amber"
          />
          <SummaryCard
            label="Finalizate fără materiale"
            value={summary.tasks_completed_without_materials}
            accent="amber"
          />
          <SummaryCard
            label="Materiale fără reporter"
            value={summary.materials_without_reporter}
            accent="amber"
          />
          <SummaryCard
            label="Montaje nefinalizate"
            value={summary.field_installations_started_not_completed}
            accent="amber"
          />
          <SummaryCard
            label="Montaje fără poze"
            value={summary.field_installations_completed_without_photos}
            accent="red"
          />
          <SummaryCard label="Total gaps" value={summary.total_gaps} accent="red" />
          <SummaryCard label="Comenzi analizate" value={summary.orders_analyzed} />
          <SummaryCard
            label="Echipe montaj"
            value={summary.field_installation_teams_analyzed}
          />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-4 py-3">
        <Filter className="w-4 h-4 text-slate-500" />
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value as SeverityFilter)}
          className="bg-[#0F1520] border border-wo-border-strong text-[12px] text-slate-300 rounded px-2 py-1"
        >
          <option value="all">Severitate: toate</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value as CategoryFilter)}
          className="bg-[#0F1520] border border-wo-border-strong text-[12px] text-slate-300 rounded px-2 py-1"
        >
          <option value="all">Categorie: toate</option>
          <option value="atelier">Atelier</option>
          <option value="montaj_teren">Montaj teren</option>
          <option value="materiale">Materiale</option>
        </select>
        <span className="text-[11px] text-slate-500 ml-auto">
          {filteredGaps.length} probleme afișate
        </span>
      </div>

      <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-wo-border-strong flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-400" />
          <h2 className="text-[13px] font-semibold text-slate-200">Lipsuri detectate</h2>
        </div>

        {loading && !data && (
          <p className="px-4 py-6 text-[12px] text-slate-500">Se încarcă...</p>
        )}

        {!loading && filteredGaps.length === 0 && (
          <p className="px-4 py-6 text-[12px] text-slate-500">
            Niciun gap pentru filtrele selectate.
          </p>
        )}

        <ul className="divide-y divide-wo-border-strong">
          {filteredGaps.map((gap, idx) => (
            <li key={`${gap.gap_type}-${gap.order_id}-${gap.task_id}-${idx}`} className="px-4 py-3">
              <div className="flex flex-wrap items-start gap-2">
                <span
                  className={`text-[10px] font-medium px-2 py-0.5 rounded border ${severityBadgeCls(gap.severity)}`}
                >
                  {severityLabel(gap.severity)}
                </span>
                <span className="text-[10px] text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700">
                  {categoryLabel(gap.category)}
                </span>
                <span className="text-[10px] font-mono text-slate-500">{gap.gap_type}</span>
              </div>
              <p className="text-[12px] text-slate-300 mt-2">{gap.message}</p>
              {(gap.order_code || gap.task_id) && (
                <p className="text-[11px] text-slate-500 mt-1">
                  {gap.order_code && <span>Comandă: {gap.order_code}</span>}
                  {gap.task_id && <span className="ml-3">Task: {gap.task_id}</span>}
                  {gap.team_id != null && <span className="ml-3">Echipă: #{gap.team_id}</span>}
                </p>
              )}
              <GapLinks gap={gap} />
            </li>
          ))}
        </ul>
      </div>

      {summary && (
        <div className="grid grid-cols-3 gap-3 text-[11px]">
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2">
            <p className="text-slate-500 flex items-center gap-1">
              <Info className="w-3 h-3" /> Info: {summary.gaps_by_severity.info}
            </p>
          </div>
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2">
            <p className="text-amber-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Warning: {summary.gaps_by_severity.warning}
            </p>
          </div>
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2">
            <p className="text-red-400 flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" /> Critical: {summary.gaps_by_severity.critical}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: "emerald" | "amber" | "red";
}) {
  const valueCls =
    accent === "emerald"
      ? "text-emerald-400"
      : accent === "amber"
        ? "text-amber-400"
        : accent === "red"
          ? "text-red-400"
          : "text-slate-200";

  return (
    <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg px-4 py-3">
      <p className="text-[11px] text-slate-400 uppercase tracking-wide">{label}</p>
      <p className={`text-[20px] font-bold mt-1 ${valueCls}`}>{value}</p>
    </div>
  );
}
