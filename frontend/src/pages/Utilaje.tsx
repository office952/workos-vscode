import { useState } from "react";
import { useMachinesData } from "@/hooks/useMachinesData";
import { CapacityNotice } from "@/components/workos/design-system";
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

const machineStatusConfig: Record<string, { label: string; cls: string; icon: React.ReactNode }> = {
  running: { label: "Rulează", cls: "text-emerald-600 dark:text-emerald-400", icon: <Activity className="w-3 h-3" /> },
  idle: { label: "Idle", cls: "text-amber-600 dark:text-amber-400", icon: <Pause className="w-3 h-3" /> },
  maintenance: { label: "Mentenanță", cls: "text-red-600 dark:text-red-400", icon: <WrenchIcon className="w-3 h-3" /> },
  offline: { label: "Offline", cls: "text-muted-foreground", icon: <Power className="w-3 h-3" /> },
  changeover: { label: "Changeover", cls: "text-blue-600 dark:text-blue-400", icon: <RefreshCw className="w-3 h-3" /> },
};

function UtilBar({ value, max = 100, color = "bg-blue-500" }: { value: number; max?: number; color?: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] text-muted-foreground font-mono w-10 text-right">{value}%</span>
    </div>
  );
}

function MntTypeBadge({ type }: { type: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    preventive: { label: "Preventivă", cls: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/40 dark:text-blue-300 dark:border-blue-700" },
    corrective: { label: "Corectivă", cls: "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-700" },
    calibration: { label: "Calibrare", cls: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/40 dark:text-amber-300 dark:border-amber-700" },
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
      <span className="text-[10px] text-emerald-700 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/20 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800/30 flex items-center gap-1">
        <Database className="w-3 h-3" /> Live DB
      </span>
    );
  }
  if (source === "mock") {
    return (
      <span className="text-[10px] text-amber-700 bg-amber-100 dark:text-amber-400 dark:bg-amber-900/20 px-2 py-0.5 rounded-full border border-amber-200 dark:border-amber-800/30">
        Mock Data
      </span>
    );
  }
  return (
    <span className="text-[10px] text-amber-700 bg-amber-100 dark:text-amber-400 dark:bg-amber-900/20 px-2 py-0.5 rounded-full border border-amber-200 dark:border-amber-800/30">
      No Data
    </span>
  );
}

export default function Utilaje() {
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
        <Loader2 className="w-6 h-6 text-cyan-600 dark:text-cyan-400 animate-spin" />
        <span className="ml-2 text-muted-foreground text-sm">Se încarcă utilajele...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Capacity Notice */}
      <CapacityNotice compact />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cog className="w-5 h-5 text-cyan-600 dark:text-cyan-600 dark:text-cyan-400" />
          <h1 className="text-[18px] font-bold text-foreground">Utilaje (registry)</h1>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            Registry intern de capacitate — nu face parte din fluxul Product Template → Structură produs → Product
            Compiler.
          </p>
          <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full ml-1">
            {machines.length} echipamente
          </span>
          <SourceBadge source={source} />
        </div>
        <button
          type="button"
          disabled
          title={createBlockedReason}
          className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 text-muted-foreground rounded-lg text-[12px] font-bold cursor-not-allowed"
        >
          <Plus className="w-3.5 h-3.5" />
          Utilaj Nou
        </button>
      </div>

      <div className="flex items-start gap-2 px-3 py-2 bg-amber-50 border border-amber-200 dark:bg-amber-900/15 dark:border-amber-800/30 rounded-lg">
        <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
        <p className="text-[11px] text-amber-700 dark:text-amber-300/90">
          Crearea utilajelor este blocată în UI deoarece backend-ul curent expune doar endpoint-uri read-only pentru registrul de maşini.
        </p>
      </div>

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
        <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-blue-500/50">
          <Search className="w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Caută utilaj, tip..."
            className="bg-transparent text-[13px] text-foreground placeholder:text-wo-text-dim outline-none w-full"
          />
        </div>
        <select
          value={filterWC}
          onChange={(e) => setFilterWC(e.target.value)}
          className="bg-card border border-border rounded-lg px-3 py-2 text-[12px] text-muted-foreground outline-none focus:border-blue-500/50"
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
                className={`bg-card border rounded-lg p-3 cursor-pointer transition-all ${
                  selected?.id === m.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-border hover:border-slate-500"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-10 rounded-full shrink-0 ${
                    m.status === "running" ? "bg-emerald-500" :
                    m.status === "idle" ? "bg-amber-500" :
                    m.status === "maintenance" ? "bg-red-500" : "bg-slate-600"
                  }`} />
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
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      <span>{wc?.name || m.workcenterId}</span>
                      <span>•</span>
                      <span>Util: {m.utilizationPct}%</span>
                      <span>•</span>
                      <span>{m.currentJobId || "Fără job"}</span>
                      {m.currentOperator && (
                        <>
                          <span>•</span>
                          <span>{m.currentOperator}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-wo-text-dim shrink-0" />
                </div>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="bg-card border border-border rounded-lg p-8 text-center text-muted-foreground text-[13px]">
              Niciun utilaj găsit.
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selected ? (
            <>
              {/* Machine Info */}
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  <div className={`w-3 h-3 rounded-full ${
                    selected.status === "running" ? "bg-emerald-500" :
                    selected.status === "idle" ? "bg-amber-500" :
                    selected.status === "maintenance" ? "bg-red-500" : "bg-slate-600"
                  }`} />
                  <h3 className="text-[16px] font-bold text-foreground">{selected.name}</h3>
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
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Status</p>
                      <span className={`inline-flex items-center gap-1 text-[12px] font-medium ${machineStatusConfig[selected.status].cls}`}>
                        {machineStatusConfig[selected.status].icon} {machineStatusConfig[selected.status].label}
                      </span>
                    </div>
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Workcenter</p>
                      <p className="text-[12px] text-muted-foreground">{workcenters.find((w) => w.id === selected.workcenterId)?.name || selected.workcenterId}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Job Curent</p>
                      <p className="text-[12px] text-muted-foreground font-mono">{selected.currentJobId || "—"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Operator</p>
                      <p className="text-[12px] text-muted-foreground">{selected.currentOperator || "—"}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
                      <Gauge className="w-3 h-3" /> Utilizare
                    </p>
                    <UtilBar
                      value={selected.utilizationPct}
                      color={selected.utilizationPct >= 80 ? "bg-emerald-500" : selected.utilizationPct >= 50 ? "bg-amber-500" : "bg-red-500"}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Runtime</p>
                      <p className="text-[12px] text-muted-foreground">{selected.runtimeMinutes} min</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Coadă</p>
                      <p className="text-[12px] text-muted-foreground">{selected.queueCount} job-uri</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Specs */}
              {selectedSpec && (
                <div className="bg-card border border-border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Ruler className="w-4 h-4 text-cyan-600 dark:text-cyan-600 dark:text-cyan-400" />
                    <span className="text-[13px] font-bold text-foreground">Specificații</span>
                  </div>
                  <div className="space-y-2 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Producător</span>
                      <span className="text-muted-foreground">{selectedSpec.manufacturer} {selectedSpec.model}</span>
                    </div>
                    {selectedSpec.year > 0 && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">An fabricație</span>
                        <span className="text-muted-foreground">{selectedSpec.year}</span>
                      </div>
                    )}
                    {selectedSpec.maxWidth > 0 && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Dimensiune max</span>
                        <span className="text-muted-foreground font-mono">
                          {selectedSpec.maxWidth}{selectedSpec.maxHeight > 0 ? `×${selectedSpec.maxHeight}` : ""} mm
                        </span>
                      </div>
                    )}
                    {selectedSpec.maxSpeed !== "N/A" && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Viteză max</span>
                        <span className="text-muted-foreground">{selectedSpec.maxSpeed}</span>
                      </div>
                    )}
                    {selectedSpec.resolution && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Rezoluție</span>
                        <span className="text-muted-foreground">{selectedSpec.resolution}</span>
                      </div>
                    )}
                    {selectedSpec.powerKW > 0 && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Putere</span>
                        <span className="text-muted-foreground">{selectedSpec.powerKW} kW</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Locație</span>
                      <span className="text-muted-foreground">{selectedSpec.location}</span>
                    </div>
                    {selectedSpec.totalJobsCompleted > 0 && (
                      <>
                        <div className="border-t border-wo-border-strong my-2" />
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Total job-uri</span>
                          <span className="text-muted-foreground font-bold">{selectedSpec.totalJobsCompleted}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Total ore funcționare</span>
                          <span className="text-muted-foreground">{selectedSpec.totalHoursRun}h</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Avg durată/job</span>
                          <span className="text-muted-foreground">{selectedSpec.avgJobDurationMin} min</span>
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
                        <Droplets className="w-4 h-4 text-cyan-600 dark:text-cyan-600 dark:text-cyan-400" />
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
                          className="text-[11px] text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300 transition-colors font-semibold"
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
                            className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-foreground outline-none focus:border-cyan-500/50"
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
                            className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-foreground outline-none focus:border-cyan-500/50"
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
                            className="flex-1 px-3 py-2 text-[11px] font-semibold text-white bg-cyan-600 rounded-lg hover:bg-cyan-500 transition-colors flex items-center justify-center gap-1.5"
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
                          <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 text-[10px] mt-1">
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
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <WrenchIcon className="w-4 h-4 text-amber-600 dark:text-amber-600 dark:text-amber-400" />
                  <span className="text-[13px] font-bold text-foreground">Istoric Mentenanță</span>
                </div>
                {selectedMnt.length > 0 ? (
                  <div className="space-y-2">
                    {selectedMnt.map((mnt) => (
                      <div key={mnt.id} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-2.5">
                        <div className="flex items-center justify-between mb-1">
                          <MntTypeBadge type={mnt.type} />
                          <span className="text-[10px] text-muted-foreground">{new Date(mnt.date).toLocaleDateString("ro-RO")}</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground mb-1">{mnt.description}</p>
                        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                          <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{mnt.durationHours}h</span>
                          <span className="flex items-center gap-1"><DollarSign className="w-3 h-3" />{mnt.cost} RON</span>
                          <span>{mnt.technician}</span>
                        </div>
                        {mnt.nextScheduled && (
                          <div className="flex items-center gap-1 mt-1 text-[10px] text-blue-600 dark:text-blue-400">
                            <Calendar className="w-3 h-3" />
                            Următoarea: {new Date(mnt.nextScheduled).toLocaleDateString("ro-RO")}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-muted-foreground">Niciun istoric de mentenanță.</p>
                )}
              </div>
            </>
          ) : (
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <Cog className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
              <p className="text-[13px] text-muted-foreground">Selectează un utilaj pentru detalii</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}