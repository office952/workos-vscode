import { useState, useMemo, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTabletStationData } from "@/hooks/useTabletStationData";
import { computeTabletStationCounts } from "@/lib/tabletLiveBridge";
import type { OperatorEmployeeOption } from "@/lib/operatorEmployeeEligibility";
import {
  WORKSTATIONS,
  DEMO_OPERATORS,
  TASK_STATUS_CONFIG,
  STATION_CHECKLISTS,
  HELP_REASONS,
  getWorkstation,
  getEligibleOperators,
  getStationStats,
  generateDemoTasks,
  generateDemoHelpRequests,
  type TabletTask,
  type HelpRequest,
  type DemoOperator,
  type HelpReason,
} from "@/lib/workstationRouting";
import { SourceBadge, StatusBadge } from "@/components/workos/design-system";
import type { SourceState } from "@/components/workos/design-system";
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Users,
  HelpCircle,
  Play,
  Square,
  Hand,
  Ban,
  ChevronRight,
  Image,
  Paperclip,
  ClipboardCheck,
  Info,
  X,
  Wrench,
  Zap,
  Loader2,
  RotateCcw,
  Unlock,
} from "lucide-react";

// ============================================================
// LIVE / DEMO BADGES
// ============================================================
function resolveTabletSourceBadge(
  source: string,
  operatorSource?: string,
): { source: SourceState; label?: string } {
  if (source === "loading") return { source: "loading", label: "Se încarcă" };
  if (source === "live") return { source: "db" };
  if (source === "empty") return { source: "empty" };
  if (source === "error") return { source: "error", label: "Eroare API" };
  if (operatorSource === "mock") return { source: "mock", label: "Demo fallback" };
  return { source: "demo", label: "Demo fallback" };
}

function TabletSourceBadge({ source, operatorSource }: { source: string; operatorSource?: string }) {
  const resolved = resolveTabletSourceBadge(source, operatorSource);
  return (
    <SourceBadge
      source={resolved.source}
      label={resolved.label}
      className="text-[11px] font-semibold px-3 py-1"
    />
  );
}

function tabletTaskExecutionStatus(task: TabletTask): string {
  if (task.liveStatus) return task.liveStatus;
  switch (task.status) {
    case "in_coada":
      return "created";
    case "pregatit":
      return "assigned";
    case "in_lucru":
      return "in_progress";
    case "blocat":
      return "blocked";
    case "finalizat":
      return "done";
    case "predat":
      return "completed";
    case "necesita_clarificare":
      return "blocked";
    case "ajutor_cerut":
    case "ajutor_preluat":
      return "paused";
    default:
      return task.status;
  }
}

function EligibilityBadge({ status }: { status: OperatorEmployeeOption["eligibility"] }) {
  const cfg = {
    authorized: "bg-emerald-900/40 text-emerald-300 border-emerald-700",
    not_authorized: "bg-amber-900/40 text-amber-300 border-amber-700",
    unverified: "bg-slate-800/60 text-slate-400 border-slate-600",
  }[status];
  const label = {
    authorized: "Autorizat",
    not_authorized: "Neautorizat",
    unverified: "Neconfirmat",
  }[status];
  return (
    <span className={`inline-flex px-2 py-0.5 text-[10px] font-semibold rounded border ${cfg}`}>
      {label}
    </span>
  );
}

function extractOrderId(task: TabletTask): number {
  if (task.orderIdNum) return task.orderIdNum;
  const match = task.orderId.match(/\d+/);
  return match ? parseInt(match[0], 10) : 0;
}

// ============================================================
// STATION SELECTOR (main /tablet page)
// ============================================================
export function TabletStationSelector() {
  const navigate = useNavigate();
  const { source, isLive, getStationLiveTasks, operatorSource, loading } = useTabletStationData();
  const helpRequests = useMemo(() => generateDemoHelpRequests(), []);
  const demoTasks = useMemo(() => generateDemoTasks(), []);

  return (
    <div className="min-h-screen bg-[#0A0F1C] p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🏭</span>
          <h1 className="text-[28px] font-bold text-slate-100">Atelier — Stații de lucru</h1>
          <span className="ml-auto">
            <TabletSourceBadge source={loading ? "loading" : source} operatorSource={operatorSource} />
          </span>
        </div>
        <p className="text-[14px] text-slate-500">Selectează stația de lucru pentru a vedea taskurile în coadă.</p>
      </div>

      {/* Station Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        {WORKSTATIONS.map((station) => {
          const stationTasks = isLive
            ? getStationLiveTasks(station.id)
            : demoTasks.filter((t) => t.workstationId === station.id);
          const counts = computeTabletStationCounts(stationTasks);
          const stats = isLive
            ? { ...counts, activeOperators: 0, helpRequests: 0 }
            : getStationStats(station.id, demoTasks, helpRequests);
          const hasUrgent = stats.blocked > 0 || stats.helpRequests > 0;

          return (
            <button
              key={station.id}
              onClick={() => navigate(`/tablet/${station.id}`)}
              className={`bg-[#111827] border-2 rounded-2xl p-6 text-left transition-all hover:scale-[1.02] hover:shadow-lg ${
                hasUrgent ? "border-red-700/50 hover:border-red-600/70" : "border-[#1E293B] hover:border-blue-700/50"
              }`}
            >
              {/* Station icon + name */}
              <div className="flex items-center gap-3 mb-4">
                <span className="text-4xl">{station.icon}</span>
                <div>
                  <h2 className="text-[18px] font-bold text-slate-100">{station.name}</h2>
                  <p className={`text-[12px] font-semibold ${station.color}`}>{station.shortName}</p>
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <StatBox label="Coadă" value={stats.queue} color="text-blue-400" />
                <StatBox label="În lucru" value={stats.inProgress} color="text-emerald-400" />
                <StatBox label="Blocate" value={stats.blocked} color={stats.blocked > 0 ? "text-red-400" : "text-slate-600"} />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <StatBox label="Azi" value={stats.completedToday} color="text-slate-400" />
                <StatBox label="Operatori" value={stats.activeOperators} color="text-cyan-400" />
                <StatBox label="Ajutor" value={stats.helpRequests} color={stats.helpRequests > 0 ? "text-purple-400" : "text-slate-600"} />
              </div>

              {/* Urgent indicator */}
              {hasUrgent && (
                <div className="mt-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-red-900/20 border border-red-800/30">
                  <AlertTriangle className="w-4 h-4 text-red-400" />
                  <span className="text-[12px] text-red-300 font-medium">Atenție necesară</span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer info */}
      <div className="mt-8 text-center">
        <p className="text-[11px] text-slate-700">
          {isLive
            ? "Tablet Mode — coadă live din execuție. Cereri ajutor rămân UI demo."
            : "Tablet Mode — fallback demo când API-ul nu este disponibil."}
        </p>
      </div>
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="text-center">
      <p className={`text-[20px] font-bold ${color}`}>{value}</p>
      <p className="text-[9px] text-slate-600 uppercase tracking-wide">{label}</p>
    </div>
  );
}

// ============================================================
// STATION QUEUE VIEW (/tablet/:stationId)
// ============================================================
export function TabletStationQueue() {
  const { stationId } = useParams<{ stationId: string }>();
  const navigate = useNavigate();
  const [selectedOperator, setSelectedOperator] = useState<string | null>(null);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);

  const {
    tasks: stationTasks,
    source,
    isLive,
    loading,
    error,
    operatorSource,
    registryEmployees,
    registrySource,
  } = useTabletStationData(stationId);

  const station = getWorkstation(stationId || "");
  const helpRequests = useMemo(() => generateDemoHelpRequests(), []);

  const eligibleOperators = useMemo(
    () => (stationId && !isLive ? getEligibleOperators(stationId) : []),
    [stationId, isLive]
  );

  const registryAvailable = isLive && registrySource === "db" && registryEmployees.length > 0;

  useEffect(() => {
    if (selectedEmployeeId != null && !registryEmployees.some((e) => e.id === selectedEmployeeId)) {
      setSelectedEmployeeId(null);
    }
  }, [registryEmployees, selectedEmployeeId]);

  const stationHelpRequests = useMemo(
    () => helpRequests.filter((h) => h.stationId === stationId && h.status === "activ"),
    [helpRequests, stationId]
  );

  if (!station) {
    return (
      <div className="min-h-screen bg-[#0A0F1C] p-6 flex items-center justify-center">
        <p className="text-slate-400 text-lg">Stație necunoscută.</p>
      </div>
    );
  }

  const queueTasks = stationTasks.filter((t) => t.status === "in_coada" || t.status === "pregatit");
  const activeTasks = stationTasks.filter((t) => t.status === "in_lucru" || t.status === "blocat" || t.status === "ajutor_cerut");
  const completedTasks = stationTasks.filter((t) => t.status === "finalizat" || t.status === "predat");

  return (
    <div className="min-h-screen bg-[#0A0F1C] p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate("/tablet")} className="p-3 rounded-xl bg-[#1E293B] hover:bg-[#2A3548] transition-colors">
          <ArrowLeft className="w-6 h-6 text-slate-300" />
        </button>
        <div className="flex items-center gap-3">
          <span className="text-4xl">{station.icon}</span>
          <div>
            <h1 className="text-[24px] font-bold text-slate-100">{station.name}</h1>
            <p className="text-[13px] text-slate-500">
              {queueTasks.length} în coadă · {activeTasks.length} active · {completedTasks.length} finalizate azi
            </p>
          </div>
        </div>
        <span className="ml-auto flex items-center gap-2">
          <TabletSourceBadge source={loading ? "loading" : source} operatorSource={operatorSource} />
          {error && (
            <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-red-900/30 text-red-300 border border-red-700/50">
              Eroare sincronizare
            </span>
          )}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT: Task Queue */}
        <div className="lg:col-span-2 space-y-4">
          {/* Active tasks */}
          {activeTasks.length > 0 && (
            <div>
              <h2 className="text-[14px] font-semibold text-emerald-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4" /> Active
              </h2>
              <div className="space-y-3">
                {activeTasks.map((task) => (
                  <TaskCard key={task.id} task={task} isLive={isLive} onOpen={() => navigate(`/tablet/${stationId}/${task.id}`)} />
                ))}
              </div>
            </div>
          )}

          {/* Queue */}
          <div>
            <h2 className="text-[14px] font-semibold text-blue-400 uppercase tracking-wide mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" /> Coadă ({queueTasks.length})
            </h2>
            {queueTasks.length === 0 ? (
              <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-8 text-center">
                <p className="text-[14px] text-slate-500">Nu există taskuri în coadă pentru această stație.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {queueTasks.map((task) => (
                  <TaskCard key={task.id} task={task} isLive={isLive} onOpen={() => navigate(`/tablet/${stationId}/${task.id}`)} />
                ))}
              </div>
            )}
          </div>

          {/* Completed */}
          {completedTasks.length > 0 && (
            <div>
              <h2 className="text-[14px] font-semibold text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> Finalizate azi ({completedTasks.length})
              </h2>
              <div className="space-y-2">
                {completedTasks.map((task) => (
                  <TaskCard key={task.id} task={task} isLive={isLive} onOpen={() => navigate(`/tablet/${stationId}/${task.id}`)} compact />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Operator Selector + Help Requests */}
        <div className="space-y-5">
          {/* Operator Selector */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-400" /> Operator activ
            </h3>
            <p className="text-[11px] text-slate-600 mb-3">
              {isLive
                ? "Selectează angajat din Operational Registry înainte de Start."
                : "Fallback demo — operatori fictivi, non-canonic."}
            </p>
            <div className="space-y-2">
              {isLive && registryAvailable ? (
                registryEmployees.map((emp) => (
                  <RegistryEmployeeRow
                    key={emp.id}
                    employee={emp}
                    selected={selectedEmployeeId === emp.id}
                    onSelect={() =>
                      setSelectedEmployeeId(selectedEmployeeId === emp.id ? null : emp.id)
                    }
                    stationName={station.name}
                  />
                ))
              ) : isLive && registrySource === "error" ? (
                <p className="text-[11px] text-amber-400 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Registry indisponibil — Start permite fallback legacy fără employee_id.
                </p>
              ) : isLive && registrySource === "db" && registryEmployees.length === 0 ? (
                <p className="text-[12px] text-slate-500">
                  Nu există operatori alocați acestei stații în Operational Registry.
                </p>
              ) : !isLive ? (
                DEMO_OPERATORS.map((op) => {
                  const isEligible = eligibleOperators.some((e) => e.id === op.id);
                  const isSelected = selectedOperator === op.id;
                  return (
                    <OperatorRow
                      key={op.id}
                      operator={op}
                      eligible={isEligible}
                      selected={isSelected}
                      onSelect={() => isEligible && setSelectedOperator(isSelected ? null : op.id)}
                      stationName={station.name}
                    />
                  );
                })
              ) : null}
            </div>
            {isLive && registryAvailable && !selectedEmployeeId && (
              <p className="text-[11px] text-amber-400 mt-3 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                Selectați un angajat înainte de Start task.
              </p>
            )}
            {!isLive && !selectedOperator && (
              <p className="text-[11px] text-amber-400 mt-3 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                Demo: selectați operator fictiv pentru preview UI.
              </p>
            )}
            {selectedEmployeeId && (
              <p className="text-[11px] text-cyan-400 mt-3 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Angajat selectat: {registryEmployees.find((e) => e.id === selectedEmployeeId)?.name}
              </p>
            )}
          </div>

          {/* Help Requests */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-purple-400" /> Cereri ajutor
              {stationHelpRequests.length > 0 && (
                <span className="ml-auto px-2 py-0.5 text-[11px] font-bold rounded-full bg-purple-900/40 text-purple-300 border border-purple-700">
                  {stationHelpRequests.length}
                </span>
              )}
            </h3>
            {stationHelpRequests.length === 0 ? (
              <p className="text-[12px] text-slate-600">Nu există cereri de ajutor active.</p>
            ) : (
              <div className="space-y-3">
                {stationHelpRequests.map((hr) => (
                  <HelpRequestCard key={hr.id} request={hr} />
                ))}
              </div>
            )}
          </div>

          {/* Auto-routing explanation */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4 text-blue-400" /> Routing taskuri
            </h3>
            <p className="text-[11px] text-slate-500 mb-2">De ce sunt taskurile în această stație:</p>
            <div className="space-y-1.5">
              {stationTasks.slice(0, 4).map((t) => (
                <div key={t.id} className="text-[11px] text-slate-400 bg-[#0D1321] px-3 py-1.5 rounded">
                  {t.routingExplanation}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// TASK CARD
// ============================================================
function TaskCard({
  task,
  onOpen,
  compact,
  isLive,
}: {
  task: TabletTask;
  onOpen: () => void;
  compact?: boolean;
  isLive?: boolean;
}) {
  const statusCfg = TASK_STATUS_CONFIG[task.status];

  if (compact) {
    return (
      <button onClick={onOpen} className="w-full bg-[#111827] border border-[#1E293B] rounded-xl px-4 py-3 text-left hover:border-slate-600 transition-colors flex items-center gap-3">
        <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-[13px] font-semibold text-slate-400 truncate">{task.operationName}</p>
          <p className="text-[11px] text-slate-600">{task.client} · {task.product}</p>
        </div>
        <span className="text-[10px] text-slate-600 font-mono">{task.orderCode}</span>
      </button>
    );
  }

  return (
    <button
      onClick={onOpen}
      className={`w-full bg-[#111827] border-2 rounded-xl px-5 py-4 text-left transition-all hover:scale-[1.01] ${
        task.status === "blocat" ? "border-red-700/50" :
        task.status === "in_lucru" ? "border-emerald-700/50" :
        task.priority === "urgent" ? "border-amber-700/40" :
        "border-[#1E293B] hover:border-blue-700/40"
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="text-[16px] font-bold text-slate-100">{task.operationName}</h3>
          <p className="text-[13px] text-slate-400 mt-0.5">{task.client} — {task.product}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {isLive && task.mappingConfirmed === false && (
            <span className="px-2 py-0.5 text-[9px] font-bold rounded bg-amber-900/40 text-amber-300 border border-amber-700">
              Mapping neconfirmat
            </span>
          )}
          {task.priority === "urgent" && (
            <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-red-900/40 text-red-300 border border-red-700">URGENT</span>
          )}
          <StatusBadge
            domain="executionTask"
            status={tabletTaskExecutionStatus(task)}
            label={statusCfg.label}
            size="sm"
            className="text-[11px]"
          />
        </div>
      </div>

      <div className="flex items-center gap-4 text-[12px] text-slate-500 flex-wrap">
        <span className="font-mono text-blue-400">{task.orderCode}</span>
        <span>Skill: {task.skillLabel}</span>
        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {task.deadline}</span>
        {task.machineName && isLive && <span>Resursă: {task.machineName}</span>}
        {task.employeeName && <span>Angajat: {task.employeeName}</span>}
        {task.nextStation && <span>→ {task.nextStation}</span>}
      </div>

      {task.status === "blocat" && task.observations && (
        <div className="mt-2 px-3 py-2 rounded-lg bg-red-900/15 border border-red-800/30">
          <p className="text-[11px] text-red-300">{task.observations}</p>
        </div>
      )}
    </button>
  );
}

// ============================================================
// REGISTRY EMPLOYEE ROW (live flow)
// ============================================================
function RegistryEmployeeRow({
  employee,
  selected,
  onSelect,
  stationName,
}: {
  employee: OperatorEmployeeOption;
  selected: boolean;
  onSelect: () => void;
  stationName: string;
}) {
  const canSelect = employee.eligibility !== "not_authorized";
  return (
    <button
      onClick={() => canSelect && onSelect()}
      disabled={!canSelect}
      title={
        employee.eligibility === "not_authorized"
          ? `Neautorizat pentru ${stationName}`
          : undefined
      }
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left ${
        selected
          ? "bg-blue-900/30 border-2 border-blue-500"
          : canSelect
            ? "bg-[#0D1321] border-2 border-transparent hover:border-blue-700/40"
            : "bg-[#0D1321] border-2 border-transparent opacity-50 cursor-not-allowed"
      }`}
    >
      <div className="flex-1 min-w-0">
        <p className={`text-[14px] font-semibold ${canSelect ? "text-slate-200" : "text-slate-600"}`}>
          {employee.name}
        </p>
        <p className="text-[10px] text-slate-600">{employee.role || "Angajat atelier"}</p>
      </div>
      <EligibilityBadge status={employee.eligibility} />
      {selected && <CheckCircle2 className="w-5 h-5 text-blue-400" />}
      {!canSelect && <Ban className="w-4 h-4 text-slate-700" />}
    </button>
  );
}

// ============================================================
// OPERATOR ROW (demo fallback only)
// ============================================================
function OperatorRow({ operator, eligible, selected, onSelect, stationName }: {
  operator: DemoOperator; eligible: boolean; selected: boolean; onSelect: () => void; stationName: string;
}) {
  const statusColors: Record<string, string> = {
    disponibil: "bg-emerald-500",
    ocupat: "bg-amber-500",
    in_ajutor: "bg-purple-500",
    indisponibil: "bg-slate-600",
  };
  const statusLabels: Record<string, string> = {
    disponibil: "Disponibil",
    ocupat: "Ocupat",
    in_ajutor: "În ajutor",
    indisponibil: "Indisponibil",
  };

  return (
    <button
      onClick={onSelect}
      disabled={!eligible}
      title={!eligible ? `Operatorul nu are skill pentru ${stationName}.` : undefined}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left ${
        selected ? "bg-blue-900/30 border-2 border-blue-500" :
        eligible ? "bg-[#0D1321] border-2 border-transparent hover:border-blue-700/40" :
        "bg-[#0D1321] border-2 border-transparent opacity-50 cursor-not-allowed"
      }`}
    >
      <div className={`w-3 h-3 rounded-full ${statusColors[operator.status]}`} />
      <div className="flex-1 min-w-0">
        <p className={`text-[14px] font-semibold ${eligible ? "text-slate-200" : "text-slate-600"}`}>{operator.name}</p>
        <p className="text-[10px] text-slate-600">
          {eligible ? statusLabels[operator.status] : `Nu are skill pentru ${stationName}`}
        </p>
      </div>
      {selected && <CheckCircle2 className="w-5 h-5 text-blue-400" />}
      {!eligible && <Ban className="w-4 h-4 text-slate-700" />}
    </button>
  );
}

// ============================================================
// HELP REQUEST CARD
// ============================================================
function HelpRequestCard({ request }: { request: HelpRequest }) {
  return (
    <div className={`bg-[#0D1321] border rounded-xl px-4 py-3 ${
      request.priority === "urgent" ? "border-red-700/50" : "border-[#1E293B]"
    }`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[12px] font-semibold text-slate-200">{request.operatorName}</span>
        {request.priority === "urgent" && (
          <span className="px-2 py-0.5 text-[9px] font-bold rounded bg-red-900/40 text-red-300 border border-red-700">URGENT</span>
        )}
      </div>
      <p className="text-[12px] text-purple-300 font-medium">{request.reasonLabel}</p>
      {request.observation && <p className="text-[11px] text-slate-500 mt-1">{request.observation}</p>}
      <div className="mt-2">
        <button
          disabled
          title="Coming soon — necesită flow backend"
          className="px-3 py-1.5 text-[11px] font-semibold rounded-lg bg-purple-900/20 text-purple-400 border border-purple-700/40 cursor-not-allowed opacity-70"
        >
          Preiau ajutor — coming soon
        </button>
      </div>
    </div>
  );
}

// ============================================================
// TASK DETAIL VIEW (/tablet/:stationId/:taskId)
// ============================================================
export function TabletTaskDetail() {
  const { stationId, taskId } = useParams<{ stationId: string; taskId: string }>();
  const navigate = useNavigate();
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const {
    tasks,
    operatorTasks,
    source,
    isLive,
    loading,
    error,
    operatorSource,
    performAction,
    registryEmployees,
    registrySource,
  } = useTabletStationData(stationId);

  const station = getWorkstation(stationId || "");
  const task = tasks.find((t) => t.id === taskId);
  const operatorTask = operatorTasks.find((t) => t.id === taskId) ?? null;

  const checklist = STATION_CHECKLISTS[stationId || ""] || [];
  const registryAvailable = isLive && registrySource === "db" && registryEmployees.length > 0;
  const selectedEmployee = registryEmployees.find((e) => e.id === selectedEmployeeId) ?? null;

  useEffect(() => {
    if (selectedEmployeeId != null && !registryEmployees.some((e) => e.id === selectedEmployeeId)) {
      setSelectedEmployeeId(null);
    }
  }, [registryEmployees, selectedEmployeeId]);

  async function handleAction(action: string, reason?: string) {
    if (!isLive || !task || !operatorTask) return;
    const orderId = extractOrderId(task);
    if (orderId === 0) return;

    if (action === "start" && registryAvailable && !selectedEmployee) {
      setActionError("Selectați un angajat din registry înainte de Start.");
      return;
    }

    const employeeForStart =
      action === "start" && selectedEmployee ? selectedEmployee.id : undefined;
    const operatorNameForStart =
      action === "start" && selectedEmployee ? selectedEmployee.name : undefined;

    setActionLoading(`${task.id}-${action}`);
    setActionError(null);
    try {
      const success = await performAction(
        orderId,
        task.id,
        action,
        reason,
        employeeForStart ?? null,
        operatorNameForStart ?? null
      );
      if (!success) {
        setActionError(`Acțiunea "${action}" a eșuat.`);
      }
    } catch {
      setActionError(`Eroare la executarea acțiunii "${action}".`);
    } finally {
      setActionLoading(null);
    }
  }

  const liveStatus = operatorTask?.status;
  const canStart = isLive && (liveStatus === "assigned" || liveStatus === "created");
  const canPause = isLive && liveStatus === "in_progress";
  const canBlock = isLive && liveStatus === "in_progress";
  const canResume = isLive && liveStatus === "paused";
  const canUnblock = isLive && liveStatus === "blocked";
  const canComplete = isLive && (liveStatus === "in_progress" || liveStatus === "paused");

  if (!station || !task) {
    return (
      <div className="min-h-screen bg-[#0A0F1C] p-6 flex items-center justify-center">
        <p className="text-slate-400 text-lg">Task negăsit.</p>
      </div>
    );
  }

  const statusCfg = TASK_STATUS_CONFIG[task.status];

  function toggleCheck(idx: number) {
    setCheckedItems((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }

  return (
    <div className="min-h-screen bg-[#0A0F1C] p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(`/tablet/${stationId}`)} className="p-3 rounded-xl bg-[#1E293B] hover:bg-[#2A3548] transition-colors">
          <ArrowLeft className="w-6 h-6 text-slate-300" />
        </button>
        <div className="flex-1">
          <h1 className="text-[22px] font-bold text-slate-100">{task.operationName}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-[14px] text-slate-400">{task.client} — {task.product}</span>
            <span className="font-mono text-[12px] text-blue-400">{task.orderCode}</span>
            <StatusBadge
              domain="executionTask"
              status={tabletTaskExecutionStatus(task)}
              label={statusCfg.label}
              size="sm"
              className="text-[11px]"
            />
            <TabletSourceBadge source={loading ? "loading" : source} operatorSource={operatorSource} />
            {isLive && task.mappingConfirmed === false && (
              <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-900/40 text-amber-300 border border-amber-700">
                Mapping neconfirmat
              </span>
            )}
            {task.priority === "urgent" && (
              <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-red-900/40 text-red-300 border border-red-700">URGENT</span>
            )}
          </div>
        </div>
        <div className="text-right">
          <p className="text-[11px] text-slate-600">Termen</p>
          <p className="text-[16px] font-bold text-slate-300">{task.deadline}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT COLUMN */}
        <div className="space-y-5">
          {/* Reference Image */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Image className="w-4 h-4 text-blue-400" /> Referință vizuală
            </h3>
            <div className="bg-[#0D1321] border border-[#1E293B] rounded-xl h-48 flex items-center justify-center">
              <div className="text-center">
                <Image className="w-12 h-12 text-slate-700 mx-auto mb-2" />
                <p className="text-[13px] text-slate-600">Fără imagine atașată.</p>
                <p className="text-[10px] text-slate-700 mt-1">Preview indisponibil — necesită sistem de fișiere.</p>
              </div>
            </div>
          </div>

          {/* Quick Details */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" /> Detalii rapide
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <DetailField label="Dimensiuni" value={task.dimensions} />
              <DetailField label="Material" value={task.material} />
              <DetailField label="Culoare / Finisaj" value={task.color} />
              <DetailField label="Cantitate" value={String(task.quantity)} />
              <DetailField label="Stație anterioară" value={task.previousStation || "Prima stație"} />
              <DetailField label="Stație următoare" value={task.nextStation || "Finalizare"} />
              {isLive && task.machineName && (
                <DetailField label="Resursă / utilaj" value={task.machineName} />
              )}
              {task.employeeName && (
                <DetailField label="Angajat task" value={task.employeeName} />
              )}
              {task.layerId && <DetailField label="Layer" value={task.layerId} />}
            </div>
            {isLive && task.instructions && (
              <div className="mt-3 px-4 py-3 rounded-lg bg-blue-900/10 border border-blue-800/30">
                <p className="text-[11px] text-blue-400 font-semibold mb-1">Instrucțiuni:</p>
                <p className="text-[12px] text-blue-200/80">{task.instructions}</p>
              </div>
            )}
            {task.observations && (
              <div className="mt-3 px-4 py-3 rounded-lg bg-amber-900/10 border border-amber-800/30">
                <p className="text-[11px] text-amber-400 font-semibold mb-1">Observații producție:</p>
                <p className="text-[12px] text-amber-200/80">{task.observations}</p>
              </div>
            )}
          </div>

          {/* Lăcătușerie special details */}
          {task.metalDetails && (
            <div className="bg-[#111827] border border-orange-800/30 rounded-xl p-5">
              <h3 className="text-[14px] font-semibold text-orange-300 mb-3 flex items-center gap-2">
                <Wrench className="w-4 h-4" /> Detalii structură metalică
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <DetailField label="Tip structură" value={task.metalDetails.tipStructura} />
                <DetailField label="Profil metalic" value={task.metalDetails.profilMetalic} />
                <DetailField label="Lungimi" value={task.metalDetails.lungimi} />
                <DetailField label="Nr. bucăți" value={String(task.metalDetails.nrBucati)} />
                <DetailField label="Puncte prindere" value={task.metalDetails.punctePrindere} />
              </div>
              <div className="mt-3 px-4 py-3 rounded-lg bg-orange-900/10 border border-orange-800/30">
                <p className="text-[11px] text-orange-400 font-semibold mb-1">Observații sudură / finisare:</p>
                <p className="text-[12px] text-orange-200/80">{task.metalDetails.observatiiSudura}</p>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-5">
          {/* Attachments */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <Paperclip className="w-4 h-4 text-slate-400" /> Atașamente
            </h3>
            {task.attachments.length === 0 ? (
              <p className="text-[12px] text-slate-600">Nu există atașamente.</p>
            ) : (
              <div className="space-y-2">
                {task.attachments.map((att, idx) => (
                  <div key={idx} className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#0D1321] border border-[#1E293B]">
                    <Paperclip className="w-4 h-4 text-slate-500 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] text-slate-300 truncate">{att.name}</p>
                      <p className="text-[10px] text-slate-600">{att.type}</p>
                    </div>
                    <span className={`px-2 py-0.5 text-[9px] font-semibold rounded border ${
                      att.status === "aprobat" ? "bg-emerald-900/30 text-emerald-300 border-emerald-700" :
                      att.status === "draft" ? "bg-amber-900/30 text-amber-300 border-amber-700" :
                      "bg-slate-800 text-slate-500 border-slate-700"
                    }`}>
                      {att.status === "aprobat" ? "Aprobat" : att.status === "draft" ? "Draft" : "Vechi"}
                    </span>
                    <button disabled title="Preview indisponibil — necesită sistem de fișiere" className="px-3 py-1.5 text-[11px] rounded bg-slate-800 text-slate-600 cursor-not-allowed">
                      Vezi
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Checklist */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4 text-emerald-400" /> Checklist — {station.name}
            </h3>
            <div className="space-y-2">
              {checklist.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => toggleCheck(idx)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    checkedItems.has(idx) ? "bg-emerald-900/20 border border-emerald-700/30" : "bg-[#0D1321] border border-[#1E293B] hover:border-slate-600"
                  }`}
                >
                  <div className={`w-6 h-6 rounded-md border-2 flex items-center justify-center shrink-0 ${
                    checkedItems.has(idx) ? "bg-emerald-600 border-emerald-500" : "border-slate-600"
                  }`}>
                    {checkedItems.has(idx) && <CheckCircle2 className="w-4 h-4 text-white" />}
                  </div>
                  <span className={`text-[14px] ${checkedItems.has(idx) ? "text-emerald-300 line-through" : "text-slate-300"}`}>
                    {item}
                  </span>
                </button>
              ))}
            </div>
            <p className="text-[10px] text-slate-700 mt-3 italic">
              Checklist local — nu se salvează în backend.
            </p>
          </div>

          {/* Employee selector (live) */}
          {isLive && (
            <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
              <h3 className="text-[14px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
                <Users className="w-4 h-4 text-cyan-400" /> Angajat pentru Start
              </h3>
              {registryAvailable ? (
                <div className="space-y-2">
                  {registryEmployees.map((emp) => (
                    <RegistryEmployeeRow
                      key={emp.id}
                      employee={emp}
                      selected={selectedEmployeeId === emp.id}
                      onSelect={() =>
                        setSelectedEmployeeId(selectedEmployeeId === emp.id ? null : emp.id)
                      }
                      stationName={station.name}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-amber-400">
                  Registry indisponibil — Start fără employee_id (legacy).
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-slate-200 mb-4">Acțiuni</h3>
            {actionError && (
              <p className="text-[11px] text-red-400 mb-3 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> {actionError}
              </p>
            )}
            {error && (
              <p className="text-[11px] text-red-400 mb-3">Eroare API: {error}</p>
            )}
            <div className="grid grid-cols-2 gap-3">
              {isLive ? (
                <>
                  <LiveActionButton
                    icon={<Play className="w-5 h-5" />}
                    label="Start"
                    color="bg-blue-600 hover:bg-blue-500"
                    enabled={canStart}
                    loading={actionLoading === `${task.id}-start`}
                    onClick={() => handleAction("start")}
                    reason="Disponibil pentru task assigned/created"
                  />
                  <LiveActionButton
                    icon={<CheckCircle2 className="w-5 h-5" />}
                    label="Finalizează"
                    color="bg-emerald-600 hover:bg-emerald-500"
                    enabled={canComplete}
                    loading={actionLoading === `${task.id}-complete`}
                    onClick={() => handleAction("complete")}
                    reason="Disponibil când taskul este în lucru"
                  />
                  <LiveActionButton
                    icon={<Square className="w-5 h-5" />}
                    label="Pauză"
                    color="bg-slate-600 hover:bg-slate-500"
                    enabled={canPause}
                    loading={actionLoading === `${task.id}-pause`}
                    onClick={() => handleAction("pause")}
                    reason="Disponibil când taskul este în lucru"
                  />
                  <LiveActionButton
                    icon={<Ban className="w-5 h-5" />}
                    label="Blochează"
                    color="bg-red-600 hover:bg-red-500"
                    enabled={canBlock}
                    loading={actionLoading === `${task.id}-block`}
                    onClick={() => handleAction("block", "Blocat de operator tablet")}
                    reason="Disponibil când taskul este în lucru"
                  />
                  <LiveActionButton
                    icon={<RotateCcw className="w-5 h-5" />}
                    label="Reia"
                    color="bg-cyan-600 hover:bg-cyan-500"
                    enabled={canResume}
                    loading={actionLoading === `${task.id}-resume`}
                    onClick={() => handleAction("resume")}
                    reason="Disponibil când taskul este în pauză"
                  />
                  <LiveActionButton
                    icon={<Unlock className="w-5 h-5" />}
                    label="Deblochează"
                    color="bg-amber-600 hover:bg-amber-500"
                    enabled={canUnblock}
                    loading={actionLoading === `${task.id}-unblock`}
                    onClick={() => handleAction("unblock")}
                    reason="Disponibil când taskul este blocat"
                  />
                </>
              ) : (
                <>
                  <ActionButton icon={<Play className="w-5 h-5" />} label="Start" color="bg-blue-600" reason="Demo — acțiuni dezactivate" />
                  <ActionButton icon={<CheckCircle2 className="w-5 h-5" />} label="Finalizează" color="bg-emerald-600" reason="Demo — acțiuni dezactivate" />
                  <ActionButton icon={<Square className="w-5 h-5" />} label="Blochează" color="bg-red-600" reason="Demo — acțiuni dezactivate" />
                </>
              )}
              <button
                onClick={() => setShowHelpModal(true)}
                className="flex items-center justify-center gap-2 px-4 py-4 rounded-xl text-[14px] font-semibold bg-purple-700/30 text-purple-300 border-2 border-purple-600/50 hover:bg-purple-700/50 transition-colors col-span-2"
              >
                <Hand className="w-5 h-5" /> Cere ajutor (UI demo)
              </button>
            </div>
            <p className="text-[10px] text-slate-700 mt-3 italic">
              {isLive
                ? "Acțiuni conectate la /api/v1/operator/task-action (același API ca /operator)."
                : "Mod demo — acțiunile live necesită API disponibil."}
            </p>
          </div>

          {/* Routing */}
          <div className="bg-[#0D1321] border border-[#1E293B] rounded-xl px-5 py-3">
            <p className="text-[11px] text-slate-500 flex items-center gap-2">
              <ChevronRight className="w-3 h-3" />
              {task.routingExplanation}
            </p>
          </div>
        </div>
      </div>

      {/* Help Request Modal */}
      {showHelpModal && <HelpRequestModal onClose={() => setShowHelpModal(false)} taskId={task.id} stationId={stationId || ""} />}
    </div>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-slate-600 uppercase tracking-wide">{label}</p>
      <p className="text-[14px] text-slate-200 font-medium mt-0.5">{value}</p>
    </div>
  );
}

function ActionButton({ icon, label, color, reason }: { icon: React.ReactNode; label: string; color: string; reason: string }) {
  return (
    <button
      disabled
      title={reason}
      className={`flex items-center justify-center gap-2 px-4 py-4 rounded-xl text-[14px] font-semibold text-white/40 border-2 border-transparent cursor-not-allowed opacity-50 ${color}`}
    >
      {icon} {label}
    </button>
  );
}

function LiveActionButton({
  icon,
  label,
  color,
  enabled,
  loading,
  onClick,
  reason,
}: {
  icon: React.ReactNode;
  label: string;
  color: string;
  enabled: boolean;
  loading?: boolean;
  onClick: () => void;
  reason: string;
}) {
  return (
    <button
      disabled={!enabled || loading}
      title={enabled ? reason : `Indisponibil — ${reason}`}
      onClick={onClick}
      className={`flex items-center justify-center gap-2 px-4 py-4 rounded-xl text-[14px] font-semibold text-white border-2 border-transparent transition-colors ${
        enabled ? color : "bg-slate-800 text-slate-500 cursor-not-allowed opacity-50"
      }`}
    >
      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : icon} {label}
    </button>
  );
}

// ============================================================
// HELP REQUEST MODAL
// ============================================================
function HelpRequestModal({ onClose, taskId, stationId }: { onClose: () => void; taskId: string; stationId: string }) {
  const [reason, setReason] = useState<HelpReason | "">("");
  const [priority, setPriority] = useState<"normal" | "urgent">("normal");
  const [observation, setObservation] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit() {
    setSubmitted(true);
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-6">
      <div className="bg-[#111827] border border-[#1E293B] rounded-2xl w-full max-w-lg p-6">
        {submitted ? (
          <div className="text-center py-8">
            <CheckCircle2 className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <h2 className="text-[20px] font-bold text-slate-100 mb-2">Cerere înregistrată (demo)</h2>
            <p className="text-[13px] text-slate-500 mb-4">
              Aceasta este o demonstrație. Cererea nu a fost salvată în backend.
            </p>
            <span className="inline-block px-3 py-1 text-[11px] font-semibold rounded-full bg-amber-900/30 text-amber-300 border border-amber-700/50 mb-4">
              COMING SOON — necesită flow backend
            </span>
            <br />
            <button onClick={onClose} className="mt-4 px-6 py-3 rounded-xl bg-slate-700 text-slate-200 text-[14px] font-semibold hover:bg-slate-600 transition-colors">
              Închide
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-[20px] font-bold text-slate-100 flex items-center gap-2">
                <Hand className="w-5 h-5 text-purple-400" /> Cere ajutor
              </h2>
              <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-800 transition-colors">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Reason */}
              <div>
                <label className="text-[12px] text-slate-400 font-semibold uppercase tracking-wide block mb-2">Motiv</label>
                <div className="grid grid-cols-2 gap-2">
                  {HELP_REASONS.map((r) => (
                    <button
                      key={r.value}
                      onClick={() => setReason(r.value)}
                      className={`px-4 py-3 rounded-xl text-[13px] font-medium text-left transition-colors ${
                        reason === r.value
                          ? "bg-purple-900/30 border-2 border-purple-500 text-purple-200"
                          : "bg-[#0D1321] border-2 border-[#1E293B] text-slate-300 hover:border-purple-700/40"
                      }`}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Priority */}
              <div>
                <label className="text-[12px] text-slate-400 font-semibold uppercase tracking-wide block mb-2">Prioritate</label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setPriority("normal")}
                    className={`flex-1 px-4 py-3 rounded-xl text-[14px] font-semibold transition-colors ${
                      priority === "normal" ? "bg-blue-900/30 border-2 border-blue-500 text-blue-200" : "bg-[#0D1321] border-2 border-[#1E293B] text-slate-300"
                    }`}
                  >
                    Normal
                  </button>
                  <button
                    onClick={() => setPriority("urgent")}
                    className={`flex-1 px-4 py-3 rounded-xl text-[14px] font-semibold transition-colors ${
                      priority === "urgent" ? "bg-red-900/30 border-2 border-red-500 text-red-200" : "bg-[#0D1321] border-2 border-[#1E293B] text-slate-300"
                    }`}
                  >
                    Urgent
                  </button>
                </div>
              </div>

              {/* Observation */}
              <div>
                <label className="text-[12px] text-slate-400 font-semibold uppercase tracking-wide block mb-2">Observație</label>
                <textarea
                  value={observation}
                  onChange={(e) => setObservation(e.target.value)}
                  placeholder="Descrie pe scurt ce ai nevoie..."
                  className="w-full bg-[#0D1321] border border-[#1E293B] rounded-xl px-4 py-3 text-[14px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-purple-600 resize-none h-24"
                />
              </div>

              {/* Submit */}
              <button
                onClick={handleSubmit}
                disabled={!reason}
                className={`w-full py-4 rounded-xl text-[16px] font-bold transition-colors ${
                  reason ? "bg-purple-600 hover:bg-purple-500 text-white" : "bg-slate-700 text-slate-500 cursor-not-allowed"
                }`}
              >
                Trimite cerere (demo)
              </button>
              <p className="text-[10px] text-slate-700 text-center italic">
                Demo UI — cererea nu se salvează real. Coming soon.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}