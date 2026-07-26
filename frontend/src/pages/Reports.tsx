import { useCallback } from "react";
import { Link } from "react-router-dom";
import { useReportsData } from "@/hooks/useReportsData";
import { SectionHeader } from "@/components/workos/SharedComponents";
import FlowBreadcrumb, { reportsBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import { OperatorHint } from "@/components/workos/NextStepPanel";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Percent,
  Clock,
  DollarSign,
  Factory,
  Database,
  HardDrive,
  Download,
} from "lucide-react";

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const h = 32;
  const w = data.length * 8;

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={w} height={h} className="shrink-0">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MetricCard({
  label,
  value,
  unit,
  trend,
  sparkData,
  color,
  icon,
}: {
  label: string;
  value: string;
  unit: string;
  trend: number;
  sparkData: number[];
  color: string;
  icon: React.ReactNode;
}) {
  const isPositive = trend >= 0;
  return (
    <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">{icon}</span>
          <p className="text-[11px] text-slate-400 uppercase tracking-wide">
            {label}
          </p>
        </div>
        <MiniSparkline data={sparkData} color={color} />
      </div>
      <div className="flex items-end gap-2">
        <span className="text-[24px] font-bold text-wo-text-primary">{value}</span>
        <span className="text-[12px] text-slate-400 mb-1">{unit}</span>
      </div>
      <div
        className={`flex items-center gap-1 mt-1 text-[11px] ${isPositive ? "text-emerald-400" : "text-red-400"}`}
      >
        {isPositive ? (
          <TrendingUp className="w-3 h-3" />
        ) : (
          <TrendingDown className="w-3 h-3" />
        )}
        <span>
          {isPositive ? "+" : ""}
          {trend.toFixed(1)}% vs prev 7d
        </span>
      </div>
    </div>
  );
}

function HeatmapCell({ value }: { value: number }) {
  const bg =
    value === 0
      ? "bg-slate-800"
      : value < 40
        ? "bg-emerald-900/40"
        : value < 60
          ? "bg-emerald-700/40"
          : value < 75
            ? "bg-amber-700/40"
            : value < 90
              ? "bg-amber-600/50"
              : "bg-red-600/50";

  return (
    <div
      className={`${bg} rounded text-center py-1.5 text-[11px] font-mono ${value >= 85 ? "text-red-300" : value >= 70 ? "text-amber-300" : value > 0 ? "text-emerald-300" : "text-slate-600"}`}
    >
      {value > 0 ? `${value}%` : "\u2014"}
    </div>
  );
}

function DataSourceBanner({ source }: { source: string }) {
  if (source === "db") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-900/20 border border-emerald-800/30 rounded-lg">
        <Database className="w-3.5 h-3.5 text-emerald-400" />
        <p className="text-[11px] text-emerald-300">
          Connected to production database — showing real data
        </p>
      </div>
    );
  }
  if (source === "mock") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-900/20 border border-amber-800/30 rounded-lg">
        <HardDrive className="w-3.5 h-3.5 text-amber-400" />
        <p className="text-[11px] text-amber-300">
          API unavailable — showing simulated data
        </p>
      </div>
    );
  }
  if (source === "error") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-red-900/20 border border-red-800/30 rounded-lg">
        <HardDrive className="w-3.5 h-3.5 text-red-400" />
        <p className="text-[11px] text-red-300">
          Backend unavailable and mock disabled — no operational report data
        </p>
      </div>
    );
  }
  if (source === "empty") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/60 border border-slate-700 rounded-lg">
        <Database className="w-3.5 h-3.5 text-slate-400" />
        <p className="text-[11px] text-slate-300">Backend connected but no reports data yet</p>
      </div>
    );
  }
  return null;
}

export default function Reports() {
  const { dailyMetrics, wcUtilHeatmap, jobStatuses, source, loading, error, refresh } = useReportsData();

  const exportCSV = useCallback(() => {
    if (dailyMetrics.length === 0) return;
    const headers = ["Date", "Throughput", "OTIF%", "Rework%", "MachineUtil%", "AvgLeadTime", "Revenue"];
    const rows = dailyMetrics.map((d) =>
      [d.date, d.throughput, d.otif, d.reworkRate, d.machineUtil, d.avgLeadTime, d.revenue].join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `WorkOS_Reports_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [dailyMetrics]);

  const last7 = dailyMetrics.slice(-7);
  const prev7 = dailyMetrics.slice(-14, -7);

  const avg = (arr: number[]) =>
    arr.length > 0 ? arr.reduce((s, v) => s + v, 0) / arr.length : 0;
  const pctChange = (curr: number, prev: number) =>
    prev === 0 ? 0 : ((curr - prev) / prev) * 100;

  const throughputAvg = avg(last7.map((d) => d.throughput));
  const prevThroughputAvg = avg(prev7.map((d) => d.throughput));
  const otifAvg = avg(last7.map((d) => d.otif));
  const prevOtifAvg = avg(prev7.map((d) => d.otif));
  const reworkAvg = avg(last7.map((d) => d.reworkRate));
  const prevReworkAvg = avg(prev7.map((d) => d.reworkRate));
  const utilAvg = avg(last7.map((d) => d.machineUtil));
  const prevUtilAvg = avg(prev7.map((d) => d.machineUtil));
  const revenueTotal = last7.reduce((s, d) => s + d.revenue, 0);
  const prevRevenueTotal = prev7.reduce((s, d) => s + d.revenue, 0);
  const leadTimeAvg = avg(last7.map((d) => d.avgLeadTime));
  const prevLeadTimeAvg = avg(prev7.map((d) => d.avgLeadTime));

  const maxJobCount = Math.max(...jobStatuses.map((s) => s.count), 1);

  const days = ["Lun", "Mar", "Mie", "Joi", "Vin", "S\u00e2m", "Dum"];

  if (loading && dailyMetrics.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-[12px] text-slate-500">Se încarcă rapoartele...</p>
      </div>
    );
  }

  if (source === "error") {
    return (
      <div className="space-y-4">
        <DataSourceBanner source={source} />
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-4">
          <p className="text-[12px] text-red-300">Rapoartele nu au putut fi încărcate din backend: {error || "Unknown error"}</p>
          <button
            onClick={() => void refresh()}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded bg-red-700 text-white hover:bg-red-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!loading && dailyMetrics.length === 0) {
    return (
      <div className="space-y-4">
        <DataSourceBanner source={source} />
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6">
          <p className="text-[12px] text-slate-400">Nu există date de raportare disponibile încă.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <FlowBreadcrumb items={reportsBreadcrumb()} />

      {/* Data Source Banner */}
      <DataSourceBanner source={source} />

      {/* Header */}
      <div className="flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-purple-400" />
        <h1 className="text-[18px] font-bold text-wo-text-primary">
          Rapoarte &amp; Analiză
        </h1>
        <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full ml-1">
          Ultimele 30 zile
        </span>
        <div className="ml-auto">
          <button
            onClick={exportCSV}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded bg-purple-600 text-white hover:bg-purple-500 transition-colors"
          >
            <Download className="w-3 h-3" />
            Export CSV
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 px-3 py-2 bg-wo-surface-raised border border-wo-border-strong rounded-lg">
        <Factory className="w-4 h-4 text-blue-400" />
        <p className="text-[12px] text-slate-300">
          Rapoarte operaționale (realitate execuție, fără cost/profit/salarii)
        </p>
        <Link
          to="/reports/operational"
          className="ml-auto text-[12px] text-blue-400 hover:text-blue-300"
        >
          Operational Reports →
        </Link>
      </div>

      {/* KPI Cards with Sparklines */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        <MetricCard
          label="Throughput"
          value={throughputAvg.toFixed(1)}
          unit="jobs/zi"
          trend={pctChange(throughputAvg, prevThroughputAvg)}
          sparkData={dailyMetrics.map((d) => d.throughput)}
          color="#3b82f6"
          icon={<Activity className="w-4 h-4" />}
        />
        <MetricCard
          label="OTIF"
          value={otifAvg.toFixed(0)}
          unit="%"
          trend={pctChange(otifAvg, prevOtifAvg)}
          sparkData={dailyMetrics.map((d) => d.otif)}
          color="#10b981"
          icon={<Target className="w-4 h-4" />}
        />
        <MetricCard
          label="Rework Rate"
          value={reworkAvg.toFixed(1)}
          unit="%"
          trend={-pctChange(reworkAvg, prevReworkAvg)}
          sparkData={dailyMetrics.map((d) => d.reworkRate)}
          color="#ef4444"
          icon={<Percent className="w-4 h-4" />}
        />
        <MetricCard
          label="Machine Util."
          value={utilAvg.toFixed(0)}
          unit="%"
          trend={pctChange(utilAvg, prevUtilAvg)}
          sparkData={dailyMetrics.map((d) => d.machineUtil)}
          color="#8b5cf6"
          icon={<Factory className="w-4 h-4" />}
        />
        <MetricCard
          label="Lead Time"
          value={leadTimeAvg.toFixed(1)}
          unit="zile"
          trend={-pctChange(leadTimeAvg, prevLeadTimeAvg)}
          sparkData={dailyMetrics.map((d) => d.avgLeadTime)}
          color="#f59e0b"
          icon={<Clock className="w-4 h-4" />}
        />
        <MetricCard
          label="Revenue 7d"
          value={(revenueTotal / 1000).toFixed(1) + "k"}
          unit="RON"
          trend={pctChange(revenueTotal, prevRevenueTotal)}
          sparkData={dailyMetrics.map((d) => d.revenue)}
          color="#06b6d4"
          icon={<DollarSign className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 30-Day Throughput Chart */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <SectionHeader
            title="Throughput \u2014 30 Zile"
            icon={<BarChart3 className="w-4 h-4" />}
          />
          <div className="flex items-end gap-[3px] h-40">
            {dailyMetrics.map((d, i) => {
              const maxVal = Math.max(
                ...dailyMetrics.map((m) => m.throughput),
                1
              );
              const h = (d.throughput / maxVal) * 100;
              const isLast7 = i >= dailyMetrics.length - 7;
              return (
                <div
                  key={d.date}
                  className="flex-1 flex flex-col items-center justify-end"
                  title={`${d.date}: ${d.throughput} jobs`}
                >
                  <div
                    className={`w-full rounded-t transition-all ${isLast7 ? "bg-blue-500" : "bg-blue-900/50"}`}
                    style={{ height: `${Math.max(h, 2)}%` }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-2 text-[9px] text-slate-600">
            <span>{dailyMetrics[0]?.date ?? ""}</span>
            <span>{dailyMetrics[dailyMetrics.length - 1]?.date ?? ""}</span>
          </div>
        </div>

        {/* OTIF Trend */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <SectionHeader
            title="OTIF % \u2014 30 Zile"
            icon={<Target className="w-4 h-4" />}
          />
          <div className="flex items-end gap-[3px] h-40">
            {dailyMetrics.map((d, i) => {
              const h = d.otif;
              const isLast7 = i >= dailyMetrics.length - 7;
              const color =
                d.otif >= 90
                  ? isLast7
                    ? "bg-emerald-500"
                    : "bg-emerald-900/50"
                  : d.otif >= 85
                    ? isLast7
                      ? "bg-amber-500"
                      : "bg-amber-900/50"
                    : isLast7
                      ? "bg-red-500"
                      : "bg-red-900/50";
              return (
                <div
                  key={d.date}
                  className="flex-1 flex flex-col items-center justify-end"
                  title={`${d.date}: ${d.otif}%`}
                >
                  <div
                    className={`w-full rounded-t transition-all ${color}`}
                    style={{ height: `${h}%` }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-[9px] text-slate-600">
              {dailyMetrics[0]?.date ?? ""}
            </span>
            <div className="flex items-center gap-2 text-[9px]">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded bg-emerald-500" />
                {"\u2265"}90%
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded bg-amber-500" />
                85-89%
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded bg-red-500" />
                {"<"}85%
              </span>
            </div>
            <span className="text-[9px] text-slate-600">
              {dailyMetrics[dailyMetrics.length - 1]?.date ?? ""}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Workcenter Utilization Heatmap */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <SectionHeader
            title="Utilizare Workcentere \u2014 S\u0103pt\u0103m\u00e2na Curent\u0103"
            icon={<Factory className="w-4 h-4" />}
          />
          <div className="space-y-1.5">
            {/* Header row */}
            <div className="grid grid-cols-8 gap-1.5">
              <div className="text-[10px] text-slate-500" />
              {days.map((d) => (
                <div
                  key={d}
                  className="text-[10px] text-slate-500 text-center font-medium"
                >
                  {d}
                </div>
              ))}
            </div>
            {/* Data rows */}
            {wcUtilHeatmap.map((wc) => (
              <div key={wc.workcenter} className="grid grid-cols-8 gap-1.5">
                <div className="text-[10px] text-slate-400 truncate flex items-center">
                  {wc.workcenter}
                </div>
                {wc.data.map((val, i) => (
                  <HeatmapCell key={i} value={val} />
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Job Completion Funnel */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <SectionHeader
            title="Job Status Funnel"
            icon={<Activity className="w-4 h-4" />}
          />
          <div className="space-y-3 mt-2">
            {jobStatuses.map((s) => (
              <div key={s.label} className="flex items-center gap-3">
                <span className="text-[11px] text-slate-400 w-24 shrink-0">
                  {s.label}
                </span>
                <div className="flex-1 bg-slate-800 rounded-full h-6 overflow-hidden">
                  <div
                    className={`${s.color} h-6 rounded-full flex items-center px-2 transition-all`}
                    style={{
                      width: `${Math.max((s.count / maxJobCount) * 100, 8)}%`,
                    }}
                  >
                    <span className="text-[11px] font-bold text-white">
                      {s.count}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Revenue by Day */}
          <div className="mt-6">
            <SectionHeader
              title="Revenue \u2014 Ultimele 7 Zile"
              icon={<DollarSign className="w-4 h-4" />}
            />
            <div className="flex items-end gap-2 h-24">
              {last7.map((d) => {
                const maxRev = Math.max(...last7.map((m) => m.revenue), 1);
                const h = (d.revenue / maxRev) * 100;
                return (
                  <div
                    key={d.date}
                    className="flex-1 flex flex-col items-center justify-end gap-1"
                    title={`${d.date}: ${d.revenue.toLocaleString()} RON`}
                  >
                    <span className="text-[9px] text-slate-500">
                      {(d.revenue / 1000).toFixed(1)}k
                    </span>
                    <div
                      className="w-full bg-cyan-500/70 rounded-t"
                      style={{ height: `${Math.max(h, 2)}%` }}
                    />
                    <span className="text-[9px] text-slate-600">
                      {d.date.split(" ")[1] ?? d.date}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Operator Hint */}
      <OperatorHint
        text="Rapoartele reflectă datele din backend. Pentru date actualizate, asigurați-vă că backend-ul rulează și comenzile au fost procesate."
        variant="info"
      />
    </div>
  );
}