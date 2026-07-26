import { useShopFloorData } from "@/hooks/useShopFloorData";
import {
  productionAlerts,
} from "@/lib/mockData";
import {
  MachineCard,
  SectionHeader,
  JobStatusBadge,
  PriorityBadge,
  AlertItem,
} from "@/components/workos/SharedComponents";
import FlowBreadcrumb, { shopFloorBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import { OperatorHint } from "@/components/workos/NextStepPanel";
import { SourceBadge } from "@/components/workos/design-system";
import type { SourceState } from "@/components/workos/design-system";
import { Factory, AlertTriangle, Layers, RefreshCw } from "lucide-react";

function LiveDot() {
  return (
    <span className="relative flex h-2 w-2">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
    </span>
  );
}

type ShopFloorSource = "db" | "mock" | "empty" | "error" | "loading";

/** Presentation-only: hook keeps `mock`; owner canonical maps mock → demo label. */
export function mapShopFloorSourceToBadge(source: ShopFloorSource): SourceState {
  if (source === "mock") return "demo";
  return source;
}

export default function ShopFloor() {
  const {
    machines,
    workcenters,
    jobs,
    alerts,
    lastUpdate,
    updateCount,
    source,
    connectionStatus,
    error,
  } = useShopFloorData(10000);

  // Never show mock alerts while source is live DB.
  const runtimeAlerts = source === "mock" ? productionAlerts : alerts;
  const activeAlerts = runtimeAlerts.filter((a) => !a.resolvedAt && a.severity !== "info");
  const blockedJobs = jobs.filter((j) => j.isBlocked);

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <FlowBreadcrumb items={shopFloorBreadcrumb()} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Factory className="w-5 h-5 text-blue-400" />
          <h1 className="text-[18px] font-bold text-wo-text-primary">Shop Floor — Live</h1>
          <SourceBadge source={mapShopFloorSourceToBadge(source)} />
          <div className="flex items-center gap-2 ml-2">
            {connectionStatus === "connected" ? (
              <span className="flex items-center gap-1.5 text-[11px] text-emerald-400 bg-emerald-900/20 border border-emerald-800/30 px-2 py-0.5 rounded-full">
                <LiveDot />
                Connected
              </span>
            ) : connectionStatus === "reconnecting" ? (
              <span className="flex items-center gap-1.5 text-[11px] text-amber-400 bg-amber-900/20 border border-amber-800/30 px-2 py-0.5 rounded-full">
                <RefreshCw className="w-3 h-3 animate-spin" />
                Reconnecting
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-[11px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
                Connecting
              </span>
            )}
            <span className="text-[10px] text-slate-600 font-mono">
              {lastUpdate.toLocaleTimeString("ro-RO", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
            <span className="text-[10px] text-slate-700 font-mono">tick #{updateCount}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {blockedJobs.length > 0 && (
            <span className="flex items-center gap-1 px-2 py-1 bg-red-900/30 border border-red-800/50 rounded text-red-400 text-[11px] font-semibold animate-pulse">
              <AlertTriangle className="w-3 h-3" />
              {blockedJobs.length} blocked
            </span>
          )}
          <div className="flex items-center gap-1 text-[10px] text-slate-600">
            <span>{machines.filter((m) => m.status === "running").length} running</span>
            <span>·</span>
            <span>{machines.filter((m) => m.status === "idle").length} idle</span>
            <span>·</span>
            <span>{machines.filter((m) => m.status === "maintenance").length} maint.</span>
          </div>
        </div>
      </div>

      {error && source !== "mock" && (
        <div className="flex items-center gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-300">Datele shopfloor nu au putut fi încărcate din backend: {error}</p>
        </div>
      )}

      {(source === "empty" || source === "error") && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-amber-300/90">
            Live data unavailable pentru ShopFloor. Fără contract backend activ nu se afișează adevăr operațional.
          </p>
        </div>
      )}

      {/* Workcenter Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {workcenters.map((wc) => {
          const wcMachines = machines.filter((m) => m.workcenterId === wc.id);
          const wcAlerts = activeAlerts.filter((a) => a.workcenterId === wc.id);
          const hasBlocked = wcMachines.some((m) => m.status === "maintenance") || blockedJobs.some((j) => j.currentWorkcenter === wc.name);
          const runningCount = wcMachines.filter((m) => m.status === "running").length;
          const totalQueue = wcMachines.reduce((sum, m) => sum + m.queueCount, 0);

          return (
            <div
              key={wc.id}
              className={`bg-wo-surface-raised border rounded-lg p-3 transition-all duration-500 ${
                hasBlocked ? "border-red-800/50 shadow-red-900/10 shadow-lg" : "border-wo-border-subtle"
              }`}
            >
              {/* WC Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-[14px] font-semibold text-wo-text-primary">{wc.name}</h3>
                  {runningCount > 0 && <LiveDot />}
                  {hasBlocked && <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />}
                </div>
                <div className="flex items-center gap-2 text-[10px] text-slate-500">
                  <span className="flex items-center gap-0.5">
                    <Layers className="w-3 h-3" />
                    {totalQueue} queue
                  </span>
                  <span>{runningCount}/{wcMachines.length} active</span>
                </div>
              </div>

              {/* Machines */}
              <div className="space-y-2">
                {wcMachines.map((m) => (
                  <div key={m.id} className="transition-all duration-500">
                    <MachineCard machine={m} />
                  </div>
                ))}
              </div>

              {/* WC Alerts */}
              {wcAlerts.length > 0 && (
                <div className="mt-3 space-y-1">
                  {wcAlerts.slice(0, 2).map((a) => (
                    <AlertItem key={a.id} alert={a} />
                  ))}
                </div>
              )}

              {/* Queue Preview */}
              {totalQueue > 0 && (
                <div className="mt-3 pt-2 border-t border-wo-border-subtle">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Queue</p>
                  <div className="space-y-1">
                    {jobs
                      .filter(
                        (j) =>
                          j.currentWorkcenter === wc.name &&
                          (j.status === "in_progress" || j.status === "scheduled" || j.status === "blocked")
                      )
                      .slice(0, 3)
                      .map((j) => (
                        <div key={j.id} className="flex items-center gap-2 text-[11px] transition-all duration-300">
                          <span className="font-mono text-blue-400">{j.id}</span>
                          <span className="text-slate-400 truncate flex-1">{j.client}</span>
                          <PriorityBadge priority={j.priority} />
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom: Blocked + Machine State */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Blocked Jobs Board */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <SectionHeader title="Blocked Jobs" count={blockedJobs.length} icon={<AlertTriangle className="w-4 h-4 text-red-400" />} />
          {blockedJobs.length === 0 ? (
            <div className="flex items-center justify-center py-6 text-[12px] text-emerald-500/70">
              <span className="flex items-center gap-1.5">
                ✓ No blocked jobs — all clear
              </span>
            </div>
          ) : (
            <div className="space-y-2">
              {blockedJobs.map((job) => (
                <div key={job.id} className="bg-wo-surface-raised border border-red-900/30 rounded-lg px-3 py-2 transition-all duration-500">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[12px] text-red-400">{job.id}</span>
                    <PriorityBadge priority={job.priority} />
                    <JobStatusBadge status={job.status} />
                  </div>
                  <p className="text-[11px] text-slate-300 mt-1">{job.client} — {job.product}</p>
                  {job.riskReason && (
                    <p className="text-[11px] text-red-400/80 mt-1">⚠ {job.riskReason}</p>
                  )}
                  <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-500">
                    <span>Op: {job.currentOperation}</span>
                    <span>WC: {job.currentWorkcenter}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Machine State Summary */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <SectionHeader title="Machine State" count={machines.length} icon={<Factory className="w-4 h-4" />} />
          <div className="overflow-x-auto">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="text-slate-500 text-left border-b border-wo-border-subtle">
                  <th className="pb-2 font-medium">Machine</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Job</th>
                  <th className="pb-2 font-medium">Runtime</th>
                  <th className="pb-2 font-medium">Util %</th>
                  <th className="pb-2 font-medium">Queue</th>
                </tr>
              </thead>
              <tbody>
                {machines.map((m) => {
                  const statusColor: Record<string, string> = {
                    running: "text-emerald-400",
                    idle: "text-slate-500",
                    maintenance: "text-red-400",
                    offline: "text-slate-600",
                    changeover: "text-amber-400",
                  };
                  return (
                    <tr key={m.id} className="border-b border-wo-border-subtle/50 hover:bg-wo-surface-raised/50 transition-colors duration-300">
                      <td className="py-1.5 text-slate-300">{m.name}</td>
                      <td className={`py-1.5 font-semibold transition-colors duration-500 ${statusColor[m.status] || "text-slate-500"}`}>
                        <span className="flex items-center gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            m.status === "running" ? "bg-emerald-500 animate-pulse" :
                            m.status === "maintenance" ? "bg-red-500" :
                            m.status === "changeover" ? "bg-amber-500 animate-pulse" :
                            "bg-slate-600"
                          }`} />
                          {m.status}
                        </span>
                      </td>
                      <td className="py-1.5 font-mono text-blue-400">{m.currentJobId || "—"}</td>
                      <td className="py-1.5 text-slate-400 transition-all duration-500">{m.runtimeMinutes > 0 ? `${m.runtimeMinutes}m` : "—"}</td>
                      <td className="py-1.5">
                        <div className="flex items-center gap-1">
                          <div className="w-12 bg-slate-700 rounded-full h-1 overflow-hidden">
                            <div
                              className={`h-1 rounded-full transition-all duration-1000 ease-out ${
                                m.utilizationPct >= 80 ? "bg-emerald-500" : m.utilizationPct >= 50 ? "bg-blue-500" : "bg-slate-500"
                              }`}
                              style={{ width: `${m.utilizationPct}%` }}
                            />
                          </div>
                          <span className="text-slate-400 transition-all duration-500">{m.utilizationPct}%</span>
                        </div>
                      </td>
                      <td className="py-1.5 text-slate-400 transition-all duration-500">{m.queueCount}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Operator Hint */}
      <OperatorHint
        text="Shop Floor afișează starea live a utilajelor și cozilor. Pentru acțiuni pe task-uri individuale, accesați pagina Operator."
        variant="info"
      />
    </div>
  );
}