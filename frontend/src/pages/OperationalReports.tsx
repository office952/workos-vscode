/**
 * Operational Reports — read-only workforce/execution reality reports.
 * No cost, profit, or salary data.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ClipboardList,
  Factory,
  Filter,
  Package,
  RefreshCw,
  Users,
} from "lucide-react";
import FlowBreadcrumb, { operationalReportsBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import {
  getOperationalReportsSummary,
  type OperationalReportsResponse,
  type ReportCategory,
  type TaskRealityLinks,
} from "@/api/operationalReports";

type TabId = "employee_activity" | "task_reality" | "materials" | "field_installation" | "completeness";

const TABS: { id: TabId; label: string; category: ReportCategory }[] = [
  { id: "completeness", label: "Completitudine", category: "completeness" },
  { id: "employee_activity", label: "Activitate angajați", category: "employee_activity" },
  { id: "task_reality", label: "Realitate taskuri", category: "task_reality" },
  { id: "materials", label: "Materiale", category: "materials" },
  { id: "field_installation", label: "Montaj teren", category: "field_installation" },
];

function statusBadge(status: string): string {
  switch (status) {
    case "completed":
      return "bg-emerald-900/40 text-emerald-300 border-emerald-700";
    case "in_progress":
      return "bg-blue-900/40 text-blue-300 border-blue-700";
    case "blocked":
      return "bg-red-900/40 text-red-300 border-red-700";
    case "paused":
      return "bg-amber-900/40 text-amber-300 border-amber-700";
    default:
      return "bg-slate-800/60 text-slate-400 border-slate-600";
  }
}

function boolBadge(value: boolean, yes = "Da", no = "Nu"): string {
  return value
    ? "bg-emerald-900/30 text-emerald-300 border-emerald-800"
    : "bg-slate-800/60 text-slate-500 border-slate-700";
}

export default function OperationalReports() {
  const [activeTab, setActiveTab] = useState<TabId>("completeness");
  const [data, setData] = useState<OperationalReportsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [orderId, setOrderId] = useState("");
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  const activeCategory = useMemo(
    () => TABS.find((t) => t.id === activeTab)?.category ?? "all",
    [activeTab]
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const report = await getOperationalReportsSummary({
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        employee_id: employeeId ? Number(employeeId) : undefined,
        order_id: orderId ? Number(orderId) : undefined,
        category: activeCategory,
      });
      setData(report);
      setLastRefreshed(new Date().toLocaleTimeString("ro-RO"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setLoading(false);
    }
  }, [fromDate, toDate, employeeId, orderId, activeCategory]);

  useEffect(() => {
    void load();
  }, [load]);

  const summary = data?.completeness_summary;

  return (
    <div className="space-y-4">
      <FlowBreadcrumb items={operationalReportsBreadcrumb()} />

      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-blue-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Operational Reports</h1>
          {data?.read_only && (
            <span className="text-[10px] text-emerald-400 bg-emerald-900/30 border border-emerald-800 px-2 py-0.5 rounded-full">
              Read-only
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/execution/reality-review"
            className="text-[12px] text-slate-400 hover:text-slate-200"
          >
            Review gaps →
          </Link>
          {lastRefreshed && (
            <span className="text-[11px] text-slate-500">Refresh: {lastRefreshed}</span>
          )}
          <button
            onClick={() => void load()}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-md bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <p className="text-[12px] text-slate-500">
        Rapoarte operaționale bazate pe realitatea colectată — fără cost intern, profit sau salarii.
      </p>

      <div className="flex flex-wrap items-center gap-3 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-4 py-3">
        <Filter className="w-4 h-4 text-slate-500" />
        <input
          type="date"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          className="bg-[#0F1520] border border-wo-border-strong text-[12px] text-slate-300 rounded px-2 py-1"
          placeholder="De la"
        />
        <input
          type="date"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          className="bg-[#0F1520] border border-wo-border-strong text-[12px] text-slate-300 rounded px-2 py-1"
          placeholder="Până la"
        />
        <input
          type="number"
          min={1}
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          placeholder="Employee ID"
          className="bg-[#0F1520] border border-wo-border-strong text-[12px] text-slate-300 rounded px-2 py-1 w-32"
        />
        <input
          type="number"
          min={1}
          value={orderId}
          onChange={(e) => setOrderId(e.target.value)}
          placeholder="Order ID"
          className="bg-[#0F1520] border border-wo-border-strong text-[12px] text-slate-300 rounded px-2 py-1 w-28"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 text-[12px] rounded-md border transition-colors ${
              activeTab === tab.id
                ? "bg-blue-600/30 border-blue-600 text-blue-200"
                : "bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg px-4 py-3 text-[12px] text-red-300">
          {error}
        </div>
      )}

      {activeTab === "completeness" && summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard icon={<Activity className="w-4 h-4" />} label="Total taskuri" value={summary.total_tasks} />
          <MetricCard icon={<Users className="w-4 h-4" />} label="Cu angajat" value={summary.tasks_with_employee} />
          <MetricCard icon={<Users className="w-4 h-4" />} label="Fără angajat" value={summary.tasks_without_employee} />
          <MetricCard icon={<Package className="w-4 h-4" />} label="Cu materiale" value={summary.tasks_with_materials} />
          <MetricCard icon={<Package className="w-4 h-4" />} label="Fără materiale" value={summary.tasks_without_materials} />
          <MetricCard icon={<Package className="w-4 h-4" />} label="Materiale raportate" value={summary.total_materials_reported} />
          <MetricCard icon={<Package className="w-4 h-4" />} label="Mat. cu reporter" value={summary.materials_with_reporter} />
          <MetricCard icon={<Package className="w-4 h-4" />} label="Mat. fără reporter" value={summary.materials_without_reporter} />
          <MetricCard icon={<Package className="w-4 h-4" />} label="Mat. cu task_id" value={summary.materials_with_task_id} />
          <MetricCard icon={<Package className="w-4 h-4" />} label="Mat. fără task_id" value={summary.materials_without_task_id} />
          <MetricCard icon={<Factory className="w-4 h-4" />} label="Montaje complete" value={summary.field_installations_complete} />
          <MetricCard icon={<Factory className="w-4 h-4" />} label="Montaje incomplete" value={summary.field_installations_incomplete} />
          {summary.plan_operational_tasks_total != null ? (
            <MetricCard
              icon={<Activity className="w-4 h-4" />}
              label="Taskuri operaționale plan"
              value={summary.plan_operational_tasks_total}
            />
          ) : null}
          {summary.plan_orders_v2_not_materialized != null ? (
            <MetricCard
              icon={<ClipboardList className="w-4 h-4" />}
              label="Comenzi V2 nematerializate"
              value={summary.plan_orders_v2_not_materialized}
            />
          ) : null}
        </div>
      )}

      {activeTab === "employee_activity" && (
        <DataTable
          loading={loading}
          empty={!data?.employee_activity?.length}
          headers={["Angajat", "Pornite", "Finalizate", "Blocate", "Minute observate"]}
          rows={(data?.employee_activity ?? []).map((r) => [
            r.employee_name,
            String(r.tasks_started),
            String(r.tasks_completed),
            String(r.tasks_blocked),
            `${r.observed_minutes_total} min`,
          ])}
        />
      )}

      {activeTab === "task_reality" && (
        <DataTable
          loading={loading}
          empty={!data?.task_reality?.length}
          headers={[
            "Comandă",
            "Task",
            "Operație",
            "Angajat",
            "Status",
            "Note",
            "Materiale",
            "Linkuri",
          ]}
          rows={(data?.task_reality ?? []).map((r) => [
            r.order_code,
            r.task_id ?? "—",
            r.operation_code || r.process_type || "—",
            r.employee_name ?? "—",
            <span key={`${r.task_id}-st`} className={`text-[10px] px-2 py-0.5 rounded border ${statusBadge(r.status)}`}>
              {r.status}
            </span>,
            <span key={`${r.task_id}-n`} className={`text-[10px] px-2 py-0.5 rounded border ${boolBadge(r.completion_notes_present)}`}>
              {r.completion_notes_present ? "Da" : "Nu"}
            </span>,
            <span key={`${r.task_id}-m`} className={`text-[10px] px-2 py-0.5 rounded border ${boolBadge(r.materials_reported)}`}>
              {r.materials_reported ? "Da" : "Nu"}
            </span>,
            <TaskLinks key={`${r.task_id}-links`} links={r.links} />,
          ])}
        />
      )}

      {activeTab === "materials" && (
        <DataTable
          loading={loading}
          empty={!data?.materials_reality?.length}
          headers={["Comandă", "Task", "Material", "Cant.", "Reporter", "Raportat la", "Note"]}
          rows={(data?.materials_reality ?? []).map((r) => [
            r.order_code,
            r.task_id ?? "—",
            r.material_name || r.material_code || "—",
            `${r.quantity ?? "—"} ${r.unit ?? ""}`.trim(),
            r.reported_by_employee_name ?? "—",
            r.reported_at ?? "—",
            r.consumption_notes ?? "—",
          ])}
        />
      )}

      {activeTab === "field_installation" && (
        <DataTable
          loading={loading}
          empty={!data?.field_installation?.length}
          headers={[
            "Comandă",
            "Status",
            "Echipă",
            "Pornit",
            "Finalizat",
            "Poze",
            "Obs. client",
          ]}
          rows={(data?.field_installation ?? []).map((r) => [
            r.order_code,
            r.status,
            String(r.team_members_count),
            r.started_at ?? "—",
            r.ended_at ?? "—",
            String(r.completion_photos_count),
            <span key={`${r.team_id}-obs`} className={`text-[10px] px-2 py-0.5 rounded border ${boolBadge(r.client_observations_present)}`}>
              {r.client_observations_present ? "Da" : "Nu"}
            </span>,
          ])}
        />
      )}
    </div>
  );
}

function TaskLinks({ links }: { links?: TaskRealityLinks }) {
  if (!links) return <span className="text-slate-500">—</span>;
  const items = [
    { to: links.order, label: "Cmd" },
    { to: links.execution_detail, label: "Exec" },
    { to: links.operator, label: "Op" },
    links.tablet ? { to: links.tablet, label: "Tab" } : null,
  ].filter(Boolean) as { to: string; label: string }[];

  return (
    <div className="flex flex-wrap gap-1">
      {items.map((l) => (
        <Link key={l.to + l.label} to={l.to} className="text-[10px] text-blue-400 hover:text-blue-300">
          {l.label}
        </Link>
      ))}
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg px-4 py-3">
      <div className="flex items-center gap-2 text-slate-400 mb-1">
        {icon}
        <p className="text-[11px] uppercase tracking-wide">{label}</p>
      </div>
      <p className="text-[20px] font-bold text-slate-100">{value}</p>
    </div>
  );
}

function DataTable({
  loading,
  empty,
  headers,
  rows,
}: {
  loading: boolean;
  empty: boolean;
  headers: string[];
  rows: (string | React.ReactNode)[][];
}) {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg overflow-x-auto">
      <table className="w-full text-[12px]">
        <thead>
          <tr className="border-b border-wo-border-strong text-slate-400">
            {headers.map((h) => (
              <th key={h} className="text-left px-4 py-2 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td colSpan={headers.length} className="px-4 py-6 text-slate-500">
                Se încarcă...
              </td>
            </tr>
          )}
          {!loading && empty && (
            <tr>
              <td colSpan={headers.length} className="px-4 py-6 text-slate-500">
                Niciun rând pentru filtrele selectate.
              </td>
            </tr>
          )}
          {!loading &&
            rows.map((row, idx) => (
              <tr key={idx} className="border-b border-wo-border-strong/60 hover:bg-slate-800/30">
                {row.map((cell, cidx) => (
                  <td key={cidx} className="px-4 py-2 text-slate-300">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
