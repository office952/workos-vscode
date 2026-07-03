import { ModuleNodeCard, SectionHeader } from "@/components/workos/SharedComponents";
import { GitBranch, ArrowRight, Shield, Ban, Clock, Zap, Wifi, WifiOff, RefreshCw, Loader2 } from "lucide-react";
import { useModuleChainData } from "@/hooks/useModuleChainData";

// Static event stream (architectural reference — shows the event types that flow through the system)
const REFERENCE_EVENTS = [
  { id: "EVT-501", type: "TASK_STARTED", module: "Tasks", entityId: "TSK-0201", message: "Andrei M. a pornit PRINT_SOLVENT pe JOB-0042", timestamp: "09:15" },
  { id: "EVT-502", type: "OPERATION_COMPLETED", module: "WorkOS", entityId: "OP-0039-1", message: "PRINT_SOLVENT completat pe JOB-0039", timestamp: "09:08" },
  { id: "EVT-503", type: "OPERATION_BLOCKED", module: "WorkOS", entityId: "OP-0041-2", message: "CNC_CUT blocat pe JOB-0041 — material lipsă", timestamp: "08:15" },
  { id: "EVT-504", type: "MACHINE_DOWN", module: "OC", entityId: "m_cnc2", message: "CNC Laser 1390 — mentenanță neplanificată", timestamp: "07:30" },
  { id: "EVT-505", type: "JOB_RELEASED", module: "WorkOS", entityId: "JOB-0048", message: "JOB-0048 (MOL Totem) lansat în producție", timestamp: "07:00" },
  { id: "EVT-506", type: "ORDER_LOCKED", module: "Orders", entityId: "ORD-1138", message: "ORD-1138 snapshot înghețat", timestamp: "06:45" },
  { id: "EVT-507", type: "QUOTE_ACCEPTED", module: "Quotes", entityId: "QT-2245", message: "Ofertă QT-2245 acceptată de MOL", timestamp: "06:30" },
  { id: "EVT-508", type: "COST_CALCULATED", module: "CostEngine", entityId: "CALC-889", message: "Cost calculat pentru configurație totem LED", timestamp: "06:15" },
  { id: "EVT-509", type: "PRODUCT_RESOLVED", module: "ProductSystem", entityId: "PROD-445", message: "Configurație totem preț LED dublu-față rezolvată", timestamp: "06:00" },
  { id: "EVT-510", type: "WI_READY_FOR_QUOTE", module: "WI", entityId: "WI-3320", message: "Cerere MOL pregătită pentru ofertare", timestamp: "05:45" },
];

const moduleColor: Record<string, string> = {
  Tasks: "text-purple-400",
  WorkOS: "text-emerald-400",
  Orders: "text-blue-400",
  Quotes: "text-amber-400",
  CostEngine: "text-cyan-400",
  ProductSystem: "text-pink-400",
  WI: "text-orange-400",
  OC: "text-slate-400",
};

export default function ModuleChain() {
  const {
    modules,
    contractHandoffs,
    aggregateStatus,
    generatedAt,
    loading,
    isLive,
    refetch,
  } = useModuleChainData(30000);

  const statusBadge = aggregateStatus === "ok"
    ? "bg-emerald-900/40 text-emerald-300 border-emerald-700"
    : aggregateStatus === "warning"
      ? "bg-amber-900/40 text-amber-300 border-amber-700"
      : aggregateStatus === "fail"
        ? "bg-red-900/40 text-red-300 border-red-700"
        : "bg-slate-700/60 text-slate-300 border-slate-600";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <GitBranch className="w-5 h-5 text-blue-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Module Chain</h1>
          <span className={`ml-2 px-2 py-0.5 text-[10px] font-semibold rounded border ${statusBadge}`}>
            {aggregateStatus.toUpperCase()}
          </span>
          {/* Data source badge */}
          <span className={`ml-auto flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-semibold rounded border ${
            isLive
              ? "bg-emerald-900/30 text-emerald-400 border-emerald-700"
              : "bg-amber-900/30 text-amber-400 border-amber-700"
          }`}>
            {isLive ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {isLive ? "Live Health" : "Offline"}
          </span>
          <button
            onClick={refetch}
            className="p-1 rounded hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors"
            title="Refresh health data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-[12px] text-slate-500">
          OC → WI → ProductSystem → CostEngine → Quotes → Orders → WorkOS → Tasks
          {generatedAt && (
            <span className="ml-2 text-slate-600">
              · Ultima verificare: {new Date(generatedAt).toLocaleTimeString("ro-RO")}
            </span>
          )}
        </p>
      </div>

      {/* Chain Visualization */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-6 overflow-x-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8 gap-2 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-[13px]">Se încarcă starea modulelor...</span>
          </div>
        ) : (
          <div className="flex items-center gap-0 min-w-max">
            {modules.map((node, idx) => (
              <ModuleNodeCard key={node.id} node={node} isLast={idx === modules.length - 1} />
            ))}
          </div>
        )}
      </div>

      {/* Contract Handoffs */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Contract Handoffs" count={contractHandoffs.length} icon={<ArrowRight className="w-4 h-4" />} />
        <div className="space-y-3">
          {contractHandoffs.map((handoff, idx) => (
            <div key={idx} className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-[13px] font-bold text-blue-400">{handoff.from}</span>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <span className="text-[13px] font-bold text-blue-400">{handoff.to}</span>
                <span className="text-[10px] text-slate-500 ml-auto">{handoff.lastEvent}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Payload</p>
                  <p className="text-[11px] text-slate-300 leading-relaxed">{handoff.payloadSummary}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1 flex items-center gap-1">
                    <Ban className="w-3 h-3 text-red-400" /> Interzis
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {handoff.forbidden.map((f, i) => (
                      <span key={i} className="px-1.5 py-0.5 text-[10px] bg-red-900/30 text-red-400 border border-red-800/40 rounded">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Golden Rules */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Regula de Aur" icon={<Shield className="w-4 h-4 text-amber-400" />} />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
            <p className="text-[12px] font-semibold text-slate-200 mb-1">Fiecare modul deține un singur adevăr</p>
            <p className="text-[11px] text-slate-400">ProductSystem = produs. CostEngine = cost. Quotes = ofertă. Orders = snapshot. WorkOS = execuție.</p>
          </div>
          <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
            <p className="text-[12px] font-semibold text-slate-200 mb-1">Niciun modul nu fură adevărul altui modul</p>
            <p className="text-[11px] text-slate-400">Quotes nu calculează cost. WorkOS nu modifică produs. Tasks nu dețin adevăr de business.</p>
          </div>
          <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
            <p className="text-[12px] font-semibold text-slate-200 mb-1">Evenimentul spune ce s-a întâmplat</p>
            <p className="text-[11px] text-slate-400">Automatizarea decide ce facem mai departe. Evenimentele sunt imutabile.</p>
          </div>
        </div>
      </div>

      {/* Event Stream */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Event Stream — Cross-Module (Referință)" count={REFERENCE_EVENTS.length} icon={<Clock className="w-4 h-4" />} />
        <div className="space-y-1.5">
          {REFERENCE_EVENTS.map((evt) => (
            <div key={evt.id} className="flex items-start gap-3 py-1.5 border-b border-[#1E293B]/30 text-[12px]">
              <span className="text-slate-600 font-mono w-10 shrink-0">{evt.timestamp}</span>
              <span className={`font-semibold w-24 shrink-0 ${moduleColor[evt.module] || "text-slate-400"}`}>
                {evt.module}
              </span>
              <span className="text-slate-500 font-mono w-40 shrink-0">{evt.type}</span>
              <span className="text-slate-300 flex-1">{evt.message}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Snapshot Points */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Snapshot Points" icon={<Zap className="w-4 h-4 text-cyan-400" />} />
        <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
          {[
            { module: "ProductSystem", snapshot: "Produs definit tehnic", color: "border-t-pink-500" },
            { module: "CostEngine", snapshot: "Cost calculat", color: "border-t-cyan-500" },
            { module: "Quotes", snapshot: "Ofertă comercială", color: "border-t-amber-500" },
            { module: "Orders", snapshot: "Snapshot aprobat", color: "border-t-blue-500" },
            { module: "WorkOS", snapshot: "Pachet operațional", color: "border-t-emerald-500" },
          ].map((s) => (
            <div key={s.module} className={`bg-[#1A2236] border border-[#2A3548] border-t-2 ${s.color} rounded-lg p-3`}>
              <p className="text-[12px] font-semibold text-slate-200">{s.module}</p>
              <p className="text-[11px] text-slate-400 mt-1">{s.snapshot}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}