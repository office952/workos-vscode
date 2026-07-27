import { useState } from "react";
import { useMachinesData } from "@/hooks/useMachinesData";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import { CapacityNotice, chromeBanner } from "@/components/workos/design-system";
import { RegistryResourceEditor } from "@/features/operational-registry/RegistryResourceEditor";
import type {
  Machine,
  MachineSpec,
  MaintenanceRecord,
} from "@/lib/mockData";
import {
  Cog,
  Search,
  Activity,
  Pause,
  WrenchIcon,
  Power,
  RefreshCw,
  ChevronRight,
  Clock,
  Gauge,
  Calendar,
  DollarSign,
  Ruler,
  Droplets,
  Save,
  Check,
  Database,
  Loader2,
  Plus,
  AlertTriangle,
} from "lucide-react";
import { CncProcessableBadge } from "@/components/workos/CncProcessableBadge";
import { machineCarriesCncProcessableBadge } from "@/lib/cnc/cncProcessableBadge";
import { presentMachineUtilization } from "@/lib/machineUtilizationHonesty";

const machineStatusConfig: Record<string, { label: string; cls: string; icon: React.ReactNode }> = {
  running: { label: "Rulează", cls: "text-wo-success", icon: <Activity className="w-3 h-3" /> },
  idle: { label: "Idle", cls: "text-wo-warning", icon: <Pause className="w-3 h-3" /> },
  maintenance: { label: "Mentenanță", cls: "text-wo-error", icon: <WrenchIcon className="w-3 h-3" /> },
  offline: { label: "Offline", cls: "text-wo-text-muted", icon: <Power className="w-3 h-3" /> },
  changeover: { label: "Changeover", cls: "text-wo-info", icon: <RefreshCw className="w-3 h-3" /> },
};

function statusDotClass(status: string): string {
  switch (status) {
    case "running":
      return "bg-wo-success";
    case "idle":
      return "bg-wo-warning";
    case "maintenance":
      return "bg-wo-error";
    default:
      return "bg-wo-text-dim";
  }
}

function utilKindBadgeClass(kindLabel: string): string {
  if (kindLabel === "GAP" || kindLabel === "PROXY") {
    return "border-wo-warning/35 bg-wo-warning-muted text-wo-warning";
  }
  return "border-wo-info/35 bg-wo-info-muted text-wo-info";
}

function UtilBar({ value, max = 100, color = "bg-wo-info" }: { value: number; max?: number; color?: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-wo-surface-inset border border-wo-border-subtle rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] text-wo-text-muted font-mono w-10 text-right">{value}%</span>
    </div>
  );
}

function MntTypeBadge({ type }: { type: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    preventive: { label: "Preventivă", cls: "bg-wo-info-muted text-wo-info border-wo-info/35" },
    corrective: { label: "Corectivă", cls: "bg-wo-error-muted text-wo-error border-wo-error/35" },
    calibration: { label: "Calibrare", cls: "bg-wo-warning-muted text-wo-warning border-wo-warning/35" },
  };
  const c = cfg[type] || cfg.preventive;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded border ${c.cls}`}>
      {c.label}
    </span>
  );
}

/** Check if a machine is an Epson SC-60600 printer */
function isSC60600(machine: Machine): boolean {
  return machine.type === "printer" && machine.name.includes("SC-60600");
}

/** Check if a machine is a large format printer */
function isPrinter(machine: Machine): boolean {
  return machine.type === "printer_large_format" || machine.type === "printer_uv_flatbed" || machine.type === "printer";
}

interface InkSettings {
  tankCapacityML: number;
  avgConsumptionPerSqm: number;
}

const defaultInkSettings: Record<string, InkSettings> = {
  "MCH-PRINTER-LF-01": { tankCapacityML: 1500, avgConsumptionPerSqm: 18 },
  "MCH-PRINTER-LF-02": { tankCapacityML: 1500, avgConsumptionPerSqm: 18 },
  m_epson1: { tankCapacityML: 1500, avgConsumptionPerSqm: 18 },
  m_epson2: { tankCapacityML: 1500, avgConsumptionPerSqm: 18 },
};

/** Data source badge */
function SourceBadge({ source }: { source: "db" | "mock" | "empty" | "error" | "loading" }) {
  if (source === "loading") return null;
  if (source === "db") {
    return (
      <span className="text-[10px] text-wo-success bg-wo-success-muted px-2 py-0.5 rounded-full border border-wo-success/35 flex items-center gap-1">
        <Database className="w-3 h-3" /> Live DB
      </span>
    );
  }
  if (source === "mock") {
    return (
      <span className="text-[10px] text-wo-warning bg-wo-warning-muted px-2 py-0.5 rounded-full border border-wo-warning/35">
        Mock Data
      </span>
    );
  }
  return (
    <span className="text-[10px] text-wo-warning bg-wo-warning-muted px-2 py-0.5 rounded-full border border-wo-warning/35">
      No Data
    </span>
  );
}

export default function Utilaje() {
  const { capacity, operationalTruth } = useDashboardStats();
  const calendarShiftOk = Boolean(operationalTruth?.calendarShiftUtilAvailable);
  const activeWcCapacity = capacity.filter((c) => (c.plannedMinutes ?? 0) > 0 || c.loadToday > 0);
  const {
    machines,
    machineSpecs,
    maintenanceRecords,
    workcenters,
    source,
    loading,
  } = useMachinesData();

  const [searchQuery, setSearchQuery] = useState("");
  const [filterWC, setFilterWC] = useState<string>("all");
  const [selected, setSelected] = useState<Machine | null>(null);
  const [inkSettings, setInkSettings] = useState<Record<string, InkSettings>>(defaultInkSettings);
  const [editingInk, setEditingInk] = useState<{ tankCapacityML: string; avgConsumptionPerSqm: string } | null>(null);
  const [inkSaved, setInkSaved] = useState(false);
  const createBlockedReason = "Registrul Utilaje folosește backend read-only (/api/v1/machines: GET only). Nu există endpoint POST pentru creare.";

  const statusSummary = {
    running: machines.filter((m) => m.status === "running").length,
    idle: machines.filter((m) => m.status === "idle").length,
    maintenance: machines.filter((m) => m.status === "maintenance").length,
  };

  const filtered = machines.filter((m) => {
    if (filterWC !== "all" && m.workcenterId !== filterWC) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return m.name.toLowerCase().includes(q) || m.id.toLowerCase().includes(q) || m.type.toLowerCase().includes(q);
    }
    return true;
  });

  const selectedSpec: MachineSpec | undefined = selected
    ? machineSpecs.find((s) => s.machineId === selected.id)
    : undefined;

  const selectedMnt: MaintenanceRecord[] = selected
    ? maintenanceRecords.filter((r) => r.machineId === selected.id).sort((a, b) => b.date.localeCompare(a.date))
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-wo-info animate-spin" />
        <span className="ml-2 text-wo-text-muted text-sm">Se încarcă utilajele...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header — title / count first; honesty collapsed */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <Cog className="w-5 h-5 text-wo-info shrink-0" />
            <h1 className="text-[18px] font-bold text-wo-text-primary">Utilaje (registry)</h1>
            <span className="text-[10px] text-wo-text-muted bg-wo-surface-inset border border-wo-border-subtle px-2 py-0.5 rounded-full">
              {machines.length} echipamente
            </span>
            <SourceBadge source={source} />
          </div>
          <p className="text-[11px] text-wo-text-muted mt-0.5">
            Registry intern de capacitate — nu face parte din fluxul Product Template → Structură produs → Product Compiler.
          </p>
        </div>
        <button
          type="button"
          disabled
          title={createBlockedReason}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-wo-surface-inset text-wo-text-dim border border-wo-border-subtle rounded-md text-[11px] font-medium cursor-not-allowed opacity-70"
        >
          <Plus className="w-3.5 h-3.5" />
          Utilaj Nou (blocat)
        </button>
      </div>

      <details
        className={`rounded-lg px-3 py-2 group ${chromeBanner.info}`}
        data-testid="utilaje-capacity-honesty"
      >
        <summary className="cursor-pointer list-none text-[11px] font-semibold text-wo-text-primary flex items-center gap-2">
          <Gauge className="w-3.5 h-3.5 text-wo-info shrink-0" />
          Capacity — WC shift util% + utilaj GAP fără assignment
          <span className="text-[10px] font-normal text-wo-text-muted group-open:hidden">(detalii)</span>
        </summary>
        <div className="mt-2 space-y-2">
          <CapacityNotice
            message="Utilaje = feasibility / capacity — NU tarif comercial. Util% WC = planned/shift; utilaj fără assignment = GAP."
            compact
          />
          {calendarShiftOk ? (
            <div
              className="rounded-lg border border-wo-success/30 bg-wo-success-muted px-3 py-2 space-y-1.5"
              data-testid="utilaje-wc-capacity-strip"
            >
              <p className="text-[11px] font-semibold text-wo-success">
                Util% shift pe workcenter (Company Calendar) — nu CostEngine, nu tarif client
              </p>
              {activeWcCapacity.length > 0 ? (
                <ul className="space-y-1">
                  {activeWcCapacity.slice(0, 8).map((c) => (
                    <li
                      key={c.workcenterId}
                      className="flex items-center justify-between gap-2 text-[11px] text-wo-text-secondary"
                    >
                      <span>{c.workcenterName}</span>
                      <span className="font-mono text-wo-text-primary">
                        {c.loadToday}% · {c.plannedMinutes ?? 0}m / {c.availableMinutes ?? "—"}m
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[11px] text-wo-text-muted">
                  Niciun WC cu planned load &gt; 0 — util% 0% onest (nu inventat).
                </p>
              )}
            </div>
          ) : (
            <div
              className={`flex items-start gap-2 px-3 py-2 rounded-lg ${chromeBanner.warning}`}
              data-testid="utilaje-util-honesty"
              role="note"
            >
              <Gauge className="w-4 h-4 text-wo-warning mt-0.5 shrink-0" />
              <p className="text-[11px] text-wo-text-secondary">
                Calendar/shift indisponibil — nu inventăm util %.
              </p>
            </div>
          )}
          <div
            className={`flex items-start gap-2 px-3 py-2 rounded-lg ${chromeBanner.neutral}`}
            data-testid="utilaje-util-honesty"
            role="note"
          >
            <Gauge className="w-4 h-4 text-wo-info mt-0.5 shrink-0" />
            <p className="text-[11px] text-wo-text-secondary">
              Per utilaj: fără machine assignment (CAP-006=D) ={" "}
              <span className="font-semibold text-wo-warning">GAP</span> pe cardul din dreapta — load-ul e la nivel WC.
            </p>
          </div>
          <div className={`flex items-start gap-2 px-3 py-2 rounded-lg ${chromeBanner.warning}`}>
            <AlertTriangle className="w-4 h-4 text-wo-warning mt-0.5 shrink-0" />
            <p className="text-[11px]">
              Crearea utilajelor este blocată în UI deoarece backend-ul curent expune doar endpoint-uri read-only pentru registrul de mașini.
            </p>
          </div>
        </div>
      </details>

      {/* Status Summary */}
      <div className="grid grid-cols-3 gap-3">
        {(Object.entries(statusSummary) as [string, number][]).map(([status, count]) => {
          const cfg = machineStatusConfig[status];
          return (
            <div key={status} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <span className={cfg.cls}>{cfg.icon}</span>
                <span className="text-[12px] font-semibold text-foreground">{cfg.label}</span>
              </div>
              <p className="text-[24px] font-bold text-foreground">{count}</p>
            </div>
          );
        })}
      </div>

      {/* Search + Filter */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-wo-info/50">
          <Search className="w-4 h-4 text-wo-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Caută utilaj, tip..."
            className="bg-transparent text-[13px] text-wo-text-primary placeholder:text-wo-text-dim outline-none w-full"
          />
        </div>
        <select
          value={filterWC}
          onChange={(e) => setFilterWC(e.target.value)}
          className="bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-muted outline-none focus:border-wo-info/50"
        >
          <option value="all">Toate workcentrele</option>
          {workcenters.map((wc) => (
            <option key={wc.id} value={wc.id}>{wc.name}</option>
          ))}
        </select>
        <span className="text-[11px] text-muted-foreground ml-auto">{filtered.length} rezultate</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Machine List */}
        <div className="lg:col-span-2 space-y-2">
          {filtered.map((m) => {
            const stCfg = machineStatusConfig[m.status];
            const wc = workcenters.find((w) => w.id === m.workcenterId);
            return (
              <div
                key={m.id}
                onClick={() => { setSelected(m); setEditingInk(null); setInkSaved(false); }}
                className={`bg-wo-surface-raised border rounded-lg p-3 cursor-pointer transition-all ${
                  selected?.id === m.id
                    ? "border-wo-info/50 ring-1 ring-wo-info/30"
                    : "border-wo-border-subtle hover:border-wo-border-strong hover:bg-wo-hover"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-10 rounded-full shrink-0 ${statusDotClass(m.status)}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                      <span className="text-[13px] font-semibold text-foreground">{m.name}</span>
                      {machineCarriesCncProcessableBadge({
                        type: m.type,
                        id: m.id,
                        name: m.name,
                        workcenterCode: m.workcenterId,
                      }) ? (
                        <CncProcessableBadge size="sm" testId={`utilaje-cnc-badge-${m.id}`} />
                      ) : null}
                      <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${stCfg.cls}`}>
                        {stCfg.icon} {stCfg.label}
                      </span>
                    </div>
                    {(() => {
                      const util = presentMachineUtilization(m);
                      return (
                        <div className="flex items-center gap-3 text-[10px] text-muted-foreground flex-wrap">
                          <span>{wc?.name || m.workcenterId}</span>
                          <span>•</span>
                          <span
                            className={`uppercase tracking-wide font-semibold px-1 py-0.5 rounded border ${utilKindBadgeClass(util.kindLabel)}`}
                            data-testid={`utilaje-util-kind-${m.id}`}
                          >
                            {util.kindLabel}
                          </span>
                          <span>Util: {util.displayPct}</span>
                          <span>•</span>
                          <span>{m.currentJobId || "Fără job"}</span>
                          {m.currentOperator && (
                            <>
                              <span>•</span>
                              <span>{m.currentOperator}</span>
                            </>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                  <ChevronRight className="w-4 h-4 text-wo-text-dim shrink-0" />
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-8 text-center text-wo-text-muted text-[13px]">
              Niciun utilaj găsit.
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selected ? (
            <>
              {/* Machine Info */}
              <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  <div className={`w-3 h-3 rounded-full ${statusDotClass(selected.status)}`} />
                  <h3 className="text-[16px] font-bold text-wo-text-primary">{selected.name}</h3>
                  {machineCarriesCncProcessableBadge({
                    type: selected.type,
                    id: selected.id,
                    name: selected.name,
                    workcenterCode: selected.workcenterId,
                  }) ? (
                    <CncProcessableBadge size="sm" testId="utilaje-cnc-badge-selected" />
                  ) : null}
                </div>

                {machineCarriesCncProcessableBadge({
                  type: selected.type,
                  id: selected.id,
                  name: selected.name,
                  workcenterCode: selected.workcenterId,
                }) ? (
                  <div
                    className="mb-3 rounded-md border border-violet-800/40 bg-violet-950/25 px-3 py-2.5"
                    data-testid="utilaje-cnc-capability-block"
                  >
                    <p className="mb-1.5 text-[9px] font-semibold uppercase tracking-[0.12em] text-violet-400/85">
                      Capacitate CNC — față litere
                    </p>
                    <CncProcessableBadge
                      size="sm"
                      showBadgeMark={false}
                      showServices
                      showMaterial
                      testId="utilaje-cnc-capability"
                    />
                  </div>
                ) : null}

                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] font-semibold text-wo-text-secondary uppercase tracking-wide mb-1">Status</p>
                      <span className={`inline-flex items-center gap-1 text-[12px] font-medium ${machineStatusConfig[selected.status].cls}`}>
                        {machineStatusConfig[selected.status].icon} {machineStatusConfig[selected.status].label}
                      </span>
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold text-wo-text-secondary uppercase tracking-wide mb-1">Workcenter</p>
                      <p className="text-[12px] text-wo-text-primary">{workcenters.find((w) => w.id === selected.workcenterId)?.name || selected.workcenterId}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] font-semibold text-wo-text-secondary uppercase tracking-wide mb-1">Job Curent</p>
                      <p className="text-[12px] text-wo-text-primary font-mono">{selected.currentJobId || "—"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold text-wo-text-secondary uppercase tracking-wide mb-1">Operator</p>
                      <p className="text-[12px] text-wo-text-primary">{selected.currentOperator || "—"}</p>
                    </div>
                  </div>

                  <div>
                    {(() => {
                      const util = presentMachineUtilization(selected);
                      return (
                        <>
                          <p className="text-[10px] font-semibold text-wo-text-secondary uppercase tracking-wide mb-1 flex items-center gap-1.5 flex-wrap">
                            <Gauge className="w-3 h-3" /> Utilizare
                            <span
                              className={`normal-case tracking-normal font-semibold px-1.5 py-0.5 rounded border ${utilKindBadgeClass(util.kindLabel)}`}
                              data-testid="utilaje-util-kind-selected"
                            >
                              {util.kindLabel}
                            </span>
                          </p>
                          {util.showBar ? (
                            <UtilBar
                              value={util.barValue}
                              color={
                                util.barValue >= 80
                                  ? "bg-wo-success"
                                  : util.barValue >= 50
                                    ? "bg-wo-warning"
                                    : "bg-wo-error"
                              }
                            />
                          ) : (
                            <p
                              className="text-[12px] text-wo-text-primary leading-snug"
                              data-testid="utilaje-util-gap"
                            >
                              <span className="text-wo-text-muted">{util.displayPct}</span>
                              {" — "}
                              <span className="text-wo-warning">{util.note}</span>
                            </p>
                          )}
                        </>
                      );
                    })()}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] font-semibold text-wo-text-secondary uppercase tracking-wide mb-1">Runtime</p>
                      <p className="text-[12px] text-wo-text-primary">{selected.runtimeMinutes} min</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold text-wo-text-secondary uppercase tracking-wide mb-1">Coadă</p>
                      <p className="text-[12px] text-wo-text-primary">{selected.queueCount} job-uri</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Specs */}
              {selectedSpec && (
                <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Ruler className="w-4 h-4 text-wo-info" />
                    <span className="text-[13px] font-bold text-wo-text-primary">Specificații</span>
                  </div>
                  <div className="space-y-2 text-[11px]">
                    <div className="flex justify-between gap-3">
                      <span className="text-wo-text-secondary shrink-0">Producător</span>
                      <span className="text-wo-text-primary text-right">{selectedSpec.manufacturer} {selectedSpec.model}</span>
                    </div>
                    {selectedSpec.year > 0 && (
                      <div className="flex justify-between gap-3">
                        <span className="text-wo-text-secondary shrink-0">An fabricație</span>
                        <span className="text-wo-text-primary">{selectedSpec.year}</span>
                      </div>
                    )}
                    {selectedSpec.maxWidth > 0 && (
                      <div className="flex justify-between gap-3">
                        <span className="text-wo-text-secondary shrink-0">Dimensiune max</span>
                        <span className="text-wo-text-primary font-mono">
                          {selectedSpec.maxWidth}{selectedSpec.maxHeight > 0 ? `×${selectedSpec.maxHeight}` : ""} mm
                        </span>
                      </div>
                    )}
                    {selectedSpec.maxSpeed !== "N/A" && (
                      <div className="flex justify-between gap-3">
                        <span className="text-wo-text-secondary shrink-0">Viteză max</span>
                        <span className="text-wo-text-primary">{selectedSpec.maxSpeed}</span>
                      </div>
                    )}
                    {selectedSpec.resolution && (
                      <div className="flex justify-between gap-3">
                        <span className="text-wo-text-secondary shrink-0">Rezoluție</span>
                        <span className="text-wo-text-primary">{selectedSpec.resolution}</span>
                      </div>
                    )}
                    {selectedSpec.powerKW > 0 && (
                      <div className="flex justify-between gap-3">
                        <span className="text-wo-text-secondary shrink-0">Putere</span>
                        <span className="text-wo-text-primary">{selectedSpec.powerKW} kW</span>
                      </div>
                    )}
                    <div className="flex justify-between gap-3">
                      <span className="text-wo-text-secondary shrink-0">Locație</span>
                      <span className="text-wo-text-primary">{selectedSpec.location}</span>
                    </div>
                    {selectedSpec.totalJobsCompleted > 0 && (
                      <>
                        <div className="border-t border-wo-border-strong my-2" />
                        <div className="flex justify-between gap-3">
                          <span className="text-wo-text-secondary shrink-0">Total job-uri</span>
                          <span className="text-wo-text-primary font-bold">{selectedSpec.totalJobsCompleted}</span>
                        </div>
                        <div className="flex justify-between gap-3">
                          <span className="text-wo-text-secondary shrink-0">Total ore funcționare</span>
                          <span className="text-wo-text-primary">{selectedSpec.totalHoursRun}h</span>
                        </div>
                        <div className="flex justify-between gap-3">
                          <span className="text-wo-text-secondary shrink-0">Avg durată/job</span>
                          <span className="text-wo-text-primary">{selectedSpec.avgJobDurationMin} min</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {source === "db" && selected && (
                <RegistryResourceEditor resourceCode={selected.id} />
              )}

              {/* Ink Settings — only for printer machines */}
              {(isSC60600(selected) || isPrinter(selected)) && (() => {
                const currentSettings = inkSettings[selected.id] || { tankCapacityML: 1500, avgConsumptionPerSqm: 18 };
                const isEditing = editingInk !== null;

                return (
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Droplets className="w-4 h-4 text-wo-info" />
                        <span className="text-[13px] font-bold text-foreground">Setări Cerneală</span>
                      </div>
                      {!isEditing && (
                        <button
                          onClick={() => {
                            setEditingInk({
                              tankCapacityML: String(currentSettings.tankCapacityML),
                              avgConsumptionPerSqm: String(currentSettings.avgConsumptionPerSqm),
                            });
                            setInkSaved(false);
                          }}
                          className="text-[11px] text-wo-info hover:opacity-80 transition-colors font-semibold"
                        >
                          Editează
                        </button>
                      )}
                    </div>

                    {isEditing ? (
                      <div className="space-y-3">
                        <div>
                          <label className="block text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
                            Capacitate Rezervor Tank (ml)
                          </label>
                          <input
                            type="number"
                            min="0"
                            step="100"
                            value={editingInk.tankCapacityML}
                            onChange={(e) => setEditingInk({ ...editingInk, tankCapacityML: e.target.value })}
                            className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-foreground outline-none focus:border-wo-info/50"
                            placeholder="ex: 1500"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
                            Consum Mediu Cerneală / mp (ml/mp)
                          </label>
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={editingInk.avgConsumptionPerSqm}
                            onChange={(e) => setEditingInk({ ...editingInk, avgConsumptionPerSqm: e.target.value })}
                            className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-foreground outline-none focus:border-wo-info/50"
                            placeholder="ex: 18"
                          />
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingInk(null)}
                            className="flex-1 px-3 py-2 text-[11px] font-semibold text-muted-foreground bg-muted border border-border rounded-lg hover:text-foreground transition-colors"
                          >
                            Anulează
                          </button>
                          <button
                            onClick={() => {
                              const tank = parseFloat(editingInk.tankCapacityML);
                              const consumption = parseFloat(editingInk.avgConsumptionPerSqm);
                              if (!isNaN(tank) && !isNaN(consumption) && tank > 0 && consumption > 0) {
                                setInkSettings((prev) => ({
                                  ...prev,
                                  [selected.id]: { tankCapacityML: tank, avgConsumptionPerSqm: consumption },
                                }));
                                setEditingInk(null);
                                setInkSaved(true);
                                setTimeout(() => setInkSaved(false), 3000);
                              }
                            }}
                            className="flex-1 px-3 py-2 text-[11px] font-semibold text-wo-info bg-wo-info-muted border border-wo-info/40 rounded-lg hover:bg-wo-hover transition-colors flex items-center justify-center gap-1.5"
                          >
                            <Save className="w-3.5 h-3.5" />
                            Salvează
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2 text-[11px]">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Capacitate Rezervor Tank</span>
                          <span className="text-muted-foreground font-mono font-semibold">{currentSettings.tankCapacityML} ml</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Consum Mediu / mp</span>
                          <span className="text-muted-foreground font-mono font-semibold">{currentSettings.avgConsumptionPerSqm} ml/mp</span>
                        </div>
                        {inkSaved && (
                          <div className="flex items-center gap-1.5 text-wo-success text-[10px] mt-1">
                            <Check className="w-3 h-3" />
                            <span>Setări salvate cu succes</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Maintenance History */}
              <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <WrenchIcon className="w-4 h-4 text-wo-warning" />
                  <span className="text-[13px] font-bold text-wo-text-primary">Istoric Mentenanță</span>
                </div>
                {selectedMnt.length > 0 ? (
                  <div className="space-y-2">
                    {selectedMnt.map((mnt) => (
                      <div key={mnt.id} className="bg-wo-surface-inset border border-wo-border-subtle rounded-lg p-2.5">
                        <div className="flex items-center justify-between mb-1">
                          <MntTypeBadge type={mnt.type} />
                          <span className="text-[10px] text-wo-text-muted">{new Date(mnt.date).toLocaleDateString("ro-RO")}</span>
                        </div>
                        <p className="text-[11px] text-wo-text-primary mb-1">{mnt.description}</p>
                        <div className="flex items-center gap-3 text-[10px] text-wo-text-secondary">
                          <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{mnt.durationHours}h</span>
                          <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" />{mnt.cost} RON</span>
                          <span>{mnt.technician}</span>
                        </div>
                        {mnt.nextScheduled && (
                          <div className="flex items-center gap-1 mt-1 text-[10px] text-wo-info">
                            <Calendar className="w-3 h-3" />
                            Următoarea: {new Date(mnt.nextScheduled).toLocaleDateString("ro-RO")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-wo-text-secondary">Niciun istoric de mentenanță.</p>
                )}
              </div>
            </>
          ) : (
            <div className="bg-wo-surface-inset border border-dashed border-wo-border-strong rounded-lg p-8 text-center min-h-[220px] flex flex-col items-center justify-center">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-wo-surface-raised border border-wo-border-subtle mb-3">
                <Cog className="w-5 h-5 text-wo-text-muted" />
              </div>
              <p className="text-[13px] font-semibold text-wo-text-primary">Niciun utilaj selectat</p>
              <p className="text-[12px] text-wo-text-muted mt-1 max-w-[220px]">
                Alege un echipament din listă pentru status, utilizare (GAP dacă lipsește semnalul) și mentenanță.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}