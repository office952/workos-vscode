import { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { useOperatorData } from "@/hooks/useOperatorData";
import { useOperatorEmployees } from "@/hooks/useOperatorEmployees";
import { useMaterialsCapture } from "@/hooks/useMaterialsCapture";
import { MaterialsCapturePanel } from "@/components/workos/MaterialsCapturePanel";
import type { MaterialRow } from "@/components/workos/MaterialsCapturePanel";
import type { OperatorTask } from "@/lib/mockData";
import { SectionHeader, ProgressBar } from "@/components/workos/SharedComponents";
import { SourceBadge, StatusBadge } from "@/components/workos/design-system";
import FlowBreadcrumb, { operatorBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import { OperatorHint } from "@/components/workos/NextStepPanel";
import {
  Play,
  Pause,
  RotateCcw,
  Unlock,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ChevronRight,
  Wrench,
  Package,
  Zap,
  Loader2,
  User,
  Users,
} from "lucide-react";
import type { OperatorEmployeeOption } from "@/lib/operatorEmployeeEligibility";
import { OperationPoolPreviewPanel } from "@/features/operational-registry/OperationPoolPreviewPanel";
import OperatorTaskAssignmentPanel from "@/components/workos/OperatorTaskAssignmentPanel";
import OperatorClarificationRequestsPanel from "@/components/workos/OperatorClarificationRequestsPanel";
import OperatorProductionBlueprintPanel from "@/components/workos/OperatorProductionBlueprintPanel";
import { OperatorTaskIdentityPresentation } from "@/components/workos/OperatorTaskIdentityPresentation";
import { OperatorProductionReleaseSummary } from "@/components/workos/OperatorProductionReleaseSummary";
import { OperatorOwnerDecisionDetailsPanel } from "@/components/workos/OperatorOwnerDecisionDetailsPanel";
import { OperatorStructuredActionError } from "@/components/workos/OperatorStructuredActionError";
import { useAuth } from "@/contexts/AuthContext";
import { useOperatorTaskTruth } from "@/hooks/useOperatorTaskTruth";
import { resolveTaskTruth, taskTruthReadinessFromRuntime } from "@/lib/operatorTaskPresentation";

function ExecutionTaskStatusBadge({ status }: { status: OperatorTask["status"] }) {
  return (
    <StatusBadge
      domain="executionTask"
      status={status}
      className="text-[11px]"
    />
  );
}

/** Extract order_id number from task — for DB tasks the jobId is "JOB-XXXX" where XXXX = order_id */
function extractOrderId(task: OperatorTask): number {
  const match = task.jobId.match(/JOB-(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
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

export default function OperatorView() {
  const [searchParams] = useSearchParams();
  const orderIdFromUrl = useMemo(() => {
    const raw = searchParams.get("orderId");
    if (!raw) return null;
    const parsed = Number.parseInt(raw, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  }, [searchParams]);
  const { tasks, loading, source, error, performAction, refresh, lastActionError } = useOperatorData();
  const { user } = useAuth();
  const canAssignTasks = user?.role === "admin" || user?.role === "manager" || user?.role === "operator";
  const startCandidate = useMemo(
    () => tasks.find((t) => t.status === "assigned" || t.status === "created") ?? null,
    [tasks]
  );
  const {
    employees: registryEmployees,
    loading: employeesLoading,
    error: employeesError,
    source: registrySource,
  } = useOperatorEmployees(startCandidate);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [structuredActionError, setStructuredActionError] = useState<
    import("@/lib/operatorProductionBlockerPresentation").StructuredActionError | null
  >(null);
  const {
    materials,
    fetchMaterials,
    addMaterials,
    updateMaterial,
    removeMaterial,
  } = useMaterialsCapture();

  // Find current active task (in_progress, paused, or blocked — all are "active" from operator perspective)
  const currentTask = tasks.find((t) => t.status === "in_progress" || t.status === "paused" || t.status === "blocked");
  const nextTasks = tasks.filter((t) => t.status === "assigned" || t.status === "created");
  const completedToday = tasks.filter((t) => t.status === "done").length;
  const blueprintOrderIds = useMemo(
    () => [...new Set(tasks.map((t) => extractOrderId(t)).filter((id) => id > 0))],
    [tasks]
  );
  const defaultBlueprintOrderId =
    orderIdFromUrl && blueprintOrderIds.includes(orderIdFromUrl)
      ? orderIdFromUrl
      : currentTask
        ? extractOrderId(currentTask)
        : blueprintOrderIds[0] ?? null;
  const isWired = source === "db" || source === "empty";
  const [blueprintTruthOrderId, setBlueprintTruthOrderId] = useState<number | null>(
    defaultBlueprintOrderId,
  );
  useEffect(() => {
    setBlueprintTruthOrderId(defaultBlueprintOrderId);
  }, [defaultBlueprintOrderId]);
  const [ownerDetailsOpen, setOwnerDetailsOpen] = useState(false);
  const { data: taskTruthResponse, tasksById: taskTruthByTaskId, refresh: refreshTaskTruth } =
    useOperatorTaskTruth(isWired ? blueprintTruthOrderId : null);

  const resolveTruthForTask = (task: OperatorTask) =>
    resolveTaskTruth(taskTruthByTaskId, task.id);

  const isTaskStartable = (task: OperatorTask): boolean | null => {
    const truth = resolveTruthForTask(task);
    if (!truth) return null;
    return truth.runtime.is_startable !== false;
  };

  const taskStartBlockReason = (task: OperatorTask): string | null => {
    const truth = resolveTruthForTask(task);
    if (!truth) return null;
    if (truth.runtime.production_release_blocked) {
      const count = truth.runtime.blocking_owner_decision_codes?.length ?? 0;
      return count > 0
        ? `${count} decizie(i) owner nerezolvata(e) la nivel de comanda`
        : "Productie blocata la nivel de comanda";
    }
    const readiness = taskTruthReadinessFromRuntime(truth.runtime);
    return (
      (readiness.readiness_reasons?.[0] as { message?: string } | undefined)?.message ||
      (readiness.blocking_reasons?.[0] as { message?: string } | undefined)?.message ||
      readiness.readiness_label ||
      null
    );
  };

  // Calculate average variance
  const tasksWithActual = tasks.filter((t) => t.actualDurationMin !== null && t.actualDurationMin > 0);
  const avgVariance = tasksWithActual.length > 0
    ? Math.round(
        tasksWithActual.reduce((sum, t) => {
          const variance = ((t.actualDurationMin! - t.plannedDurationMin) / t.plannedDurationMin) * 100;
          return sum + variance;
        }, 0) / tasksWithActual.length
      )
    : 0;

  const isMockSource = source === "mock";
  const registryAvailable = registrySource === "db" && registryEmployees.length > 0;
  const selectedEmployee = registryEmployees.find((e) => e.id === selectedEmployeeId) ?? null;

  useEffect(() => {
    if (selectedEmployeeId != null && !registryEmployees.some((e) => e.id === selectedEmployeeId)) {
      setSelectedEmployeeId(null);
    }
  }, [registryEmployees, selectedEmployeeId]);

  // Current order ID for materials
  const currentOrderId = currentTask ? extractOrderId(currentTask) : 0;

  // Fetch materials when current task changes
  useEffect(() => {
    if (isWired && currentOrderId > 0) {
      fetchMaterials(currentOrderId);
    }
  }, [isWired, currentOrderId, fetchMaterials]);

  // Materials handlers
  async function handleAddMaterials(rows: MaterialRow[]): Promise<boolean> {
    if (currentOrderId <= 0) return false;
    return addMaterials(currentOrderId, rows);
  }

  async function handleUpdateMaterial(index: number, row: MaterialRow): Promise<boolean> {
    if (currentOrderId <= 0) return false;
    return updateMaterial(currentOrderId, index, row);
  }

  async function handleRemoveMaterial(index: number): Promise<boolean> {
    if (currentOrderId <= 0) return false;
    return removeMaterial(currentOrderId, index);
  }

  async function handleAction(task: OperatorTask, action: string, reason?: string) {
    if (!isWired) return;
    const orderId = extractOrderId(task);
    if (orderId === 0) return;

    const employeeForStart =
      action === "start" && selectedEmployee ? selectedEmployee.id : undefined;
    const operatorNameForStart =
      action === "start" && selectedEmployee ? selectedEmployee.name : undefined;

    if (action === "start" && registryAvailable && !selectedEmployee) {
      setActionError("Selectați un angajat din registry înainte de Start.");
      return;
    }

    setActionLoading(`${task.id}-${action}`);
    setActionError(null);
    setStructuredActionError(null);
    try {
      const result = await performAction(
        orderId,
        task.id,
        action,
        reason,
        employeeForStart ?? null,
        operatorNameForStart ?? null
      );
      if (result.success) {
        await refreshTaskTruth();
      } else {
        setStructuredActionError(result.actionError);
        if (!result.actionError) {
          setActionError(`Acțiunea "${action}" a eșuat. Verificați starea task-ului.`);
        }
      }
    } catch {
      setActionError(`Eroare la executarea acțiunii "${action}".`);
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
        <span className="ml-2 text-slate-400 text-sm">Se încarcă task-urile operatorului...</span>
      </div>
    );
  }

  // Get first job for timeline
  const firstJobId = tasks[0]?.jobId;

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* Breadcrumb */}
      <FlowBreadcrumb items={operatorBreadcrumb()} />

      {/* Operator Hint */}
      {!currentTask && nextTasks.length === 0 && !loading && (
        <OperatorHint
          text="Nu aveți task-uri asignate momentan. Verificați cu supervizorul sau așteptați alocarea unui task din planul de execuție."
          variant="info"
        />
      )}

      {error && source !== "mock" && (
        <div className="flex items-center gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-300">Datele operator nu au putut fi încărcate din backend: {error}</p>
        </div>
      )}

      {/* Status banner — only explicit mock fallback, not live-empty */}
      {isMockSource && (
        <div
          role="alert"
          className="flex items-start gap-3 bg-amber-500/10 border-2 border-amber-500/60 rounded-lg px-4 py-3"
        >
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/50 text-[10px] font-bold text-amber-300 uppercase tracking-wider">
                Mock Data
              </span>
              <span className="text-[13px] font-semibold text-amber-200">
                Butoanele sunt dezactivate — nu există conexiune la backend.
              </span>
            </div>
            <p className="text-[11px] text-amber-300/80 mt-1 leading-relaxed">
              Datele afișate sunt mock. Conectați backend-ul pentru a activa Start / Pause / Complete.
            </p>
          </div>
        </div>
      )}

      {/* Employee selector — canonical registry, no salary */}
      {isWired && (
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-4 h-4 text-cyan-400" />
            <h2 className="text-[13px] font-semibold text-slate-200">Angajat activ (registry)</h2>
            {employeesLoading && <Loader2 className="w-3.5 h-3.5 text-slate-500 animate-spin" />}
          </div>

          {employeesError && (
            <p className="text-[12px] text-amber-300 mb-2">
              Registry indisponibil — Start rămâne compatibil fără angajat selectat.
            </p>
          )}

          {registryAvailable ? (
            <div className="space-y-2">
              <select
                value={selectedEmployeeId ?? ""}
                onChange={(e) =>
                  setSelectedEmployeeId(e.target.value ? Number(e.target.value) : null)
                }
                className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-slate-200"
              >
                <option value="">— Selectează angajat —</option>
                {registryEmployees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.name}
                    {emp.role ? ` · ${emp.role}` : ""}
                    {` · ${emp.eligibilityLabel}`}
                  </option>
                ))}
              </select>

              {selectedEmployee && (
                <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                  <EligibilityBadge status={selectedEmployee.eligibility} />
                  {selectedEmployee.skillCodes.slice(0, 4).map((s) => (
                    <span key={s} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {s.replace(/^SK_/, "")}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : !employeesLoading ? (
            <p className="text-[12px] text-slate-500">
              Niciun angajat activ în registry — folosiți modul legacy la Start.
            </p>
          ) : null}

          {(startCandidate || currentTask) && (
            <div className="mt-3">
              <OperationPoolPreviewPanel
                operationCode={(currentTask ?? startCandidate)?.operationCode}
                machineType={(currentTask ?? startCandidate)?.machineName}
              />
            </div>
          )}
        </div>
      )}

      {canAssignTasks && isWired && blueprintTruthOrderId ? (
        <div className="space-y-3">
          <OperatorProductionReleaseSummary
            truth={taskTruthResponse}
            onOpenDetails={() => setOwnerDetailsOpen(true)}
          />
          {ownerDetailsOpen ? (
            <OperatorOwnerDecisionDetailsPanel truth={taskTruthResponse} defaultOpen />
          ) : null}
        </div>
      ) : null}

      {canAssignTasks && isWired && (
        <>
          <OperatorTaskAssignmentPanel
            tasks={tasks}
            wired={isWired}
            onAssigned={refresh}
            taskTruthByTaskId={taskTruthByTaskId}
          />
          <OperatorClarificationRequestsPanel />
          <OperatorProductionBlueprintPanel
            orderIds={blueprintOrderIds}
            defaultOrderId={defaultBlueprintOrderId}
            taskTruthByTaskId={taskTruthByTaskId}
            onSelectedOrderIdChange={setBlueprintTruthOrderId}
          />
        </>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-[14px] font-bold text-white">
            {selectedEmployee ? (
              <User className="w-5 h-5" />
            ) : (
              "OP"
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-[18px] font-bold text-slate-100">Operator View</h1>
              <SourceBadge source={source} />
            </div>
            <p className="text-[12px] text-slate-500">
              {selectedEmployee
                ? `Angajat selectat: ${selectedEmployee.name}`
                : "Panou operator · Task-uri din Execution Plans"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-[11px] text-slate-500">Tasks completate</p>
            <p className="text-[20px] font-bold text-emerald-400">{completedToday}</p>
          </div>
          <div className="text-right">
            <p className="text-[11px] text-slate-500">Varianță medie</p>
            <p className={`text-[20px] font-bold ${avgVariance < 0 ? "text-emerald-400" : avgVariance > 0 ? "text-amber-400" : "text-slate-400"}`}>
              {avgVariance > 0 ? "+" : ""}{avgVariance}%
            </p>
          </div>
        </div>
      </div>

      {/* Current Task — Big Card */}
      {currentTask ? (
        <div className="bg-wo-surface-raised border-2 border-emerald-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[13px] font-semibold text-emerald-400 uppercase tracking-wide">Task Curent</span>
            </div>
            <ExecutionTaskStatusBadge status={currentTask.status} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h2 className="text-[20px] font-bold text-slate-100">
                {resolveTruthForTask(currentTask)?.identity.display_label || currentTask.operationName}
              </h2>
              <OperatorTaskIdentityPresentation
                truth={resolveTruthForTask(currentTask)}
                fallbackOperationName={currentTask.operationName}
                fallbackTaskId={currentTask.id}
                compact
                testId="operator-current-task-identity"
              />
              <p className="text-[13px] text-slate-400 mt-1">
                {currentTask.client} — {currentTask.product}
              </p>
              <div className="flex items-center gap-3 mt-2 text-[12px] text-slate-500">
                <span className="font-mono text-blue-400">{currentTask.jobId}</span>
              </div>

              {/* Machine */}
              <div className="flex items-center gap-2 mt-4 bg-wo-surface-raised rounded-lg px-3 py-2">
                <Wrench className="w-4 h-4 text-slate-500" />
                <span className="text-[12px] text-slate-300">{currentTask.machineName}</span>
              </div>

              {(currentTask.assignedEmployeeName || currentTask.assignedEmployeeId) && (
                <div className="flex items-center gap-2 mt-2 text-[11px]">
                  <User className="w-3.5 h-3.5 text-violet-400" />
                  <span className="text-violet-300">
                    Plan: {currentTask.assignedEmployeeName || `Angajat #${currentTask.assignedEmployeeId}`}
                  </span>
                </div>
              )}

              {(currentTask.employeeName || currentTask.employeeId) && (
                <div className="flex items-center gap-2 mt-2 text-[11px]">
                  <User className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-cyan-300">
                    Reality: {currentTask.employeeName || `Angajat #${currentTask.employeeId}`}
                  </span>
                </div>
              )}

              {/* Instructions */}
              <div className="mt-4">
                <p className="text-[11px] text-slate-500 uppercase tracking-wide mb-1">Instrucțiuni</p>
                <p className="text-[12px] text-slate-300 leading-relaxed bg-wo-surface-raised rounded-lg px-3 py-2">
                  {currentTask.instructions}
                </p>
              </div>
            </div>

            <div>
              {/* Time */}
              <div className="bg-wo-surface-raised rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-4 h-4 text-slate-500" />
                  <span className="text-[11px] text-slate-500 uppercase tracking-wide">Timp</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-[10px] text-slate-500">Planificat</p>
                    <p className="text-[18px] font-bold text-slate-300">{currentTask.plannedDurationMin} min</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500">Elapsed</p>
                    <p className={`text-[18px] font-bold ${
                      (currentTask.actualDurationMin || 0) > currentTask.plannedDurationMin
                        ? "text-red-400"
                        : "text-emerald-400"
                    }`}>
                      {currentTask.actualDurationMin || 0} min
                    </p>
                  </div>
                </div>
                <div className="mt-2">
                  <ProgressBar value={currentTask.actualDurationMin || 0} max={currentTask.plannedDurationMin} size="md" />
                </div>
              </div>

              {/* Dependencies */}
              <div className="mt-3">
                <p className="text-[11px] text-slate-500 uppercase tracking-wide mb-1">Input Dependencies</p>
                <div className="space-y-1">
                  {currentTask.inputDependencies.map((dep, i) => (
                    <div key={i} className="flex items-center gap-2 text-[12px]">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      <span className="text-slate-300">{dep}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Expected Output */}
              <div className="mt-3">
                <p className="text-[11px] text-slate-500 uppercase tracking-wide mb-1">Output Așteptat</p>
                <div className="flex items-center gap-2 text-[12px]">
                  <Package className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-slate-300">{currentTask.expectedOutput}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons — WIRED when source === "db" */}
          {/* Error message display */}
          {actionError && !lastActionError ? (
            <div className="mt-4 px-3 py-2 bg-red-900/30 border border-red-700/50 rounded-lg">
              <p className="text-[12px] text-red-300">{actionError}</p>
            </div>
          ) : null}
          {lastActionError || structuredActionError ? (
            <div className="mt-4">
              <OperatorStructuredActionError
                error={structuredActionError ?? lastActionError}
                taskLabel={currentTask.operationName}
                testId="operator-structured-start-error"
              />
            </div>
          ) : null}
          <div className="flex items-center gap-3 mt-5 pt-4 border-t border-wo-border-strong">
            {/* Show Pause only when task is in_progress (not paused/blocked) */}
            {currentTask.status === "in_progress" && (
              <button
                type="button"
                disabled={!isWired || actionLoading !== null}
                onClick={() => handleAction(currentTask, "pause")}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold transition-colors ${
                  isWired
                    ? "bg-amber-600 hover:bg-amber-500 text-white cursor-pointer"
                    : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-60"
                }`}
              >
                {actionLoading === `${currentTask.id}-pause` ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Pause className="w-4 h-4" />
                )}
                Pause
              </button>
            )}

            {/* Show Resume when task is paused */}
            {currentTask.status === "paused" && (
              <button
                type="button"
                disabled={!isWired || actionLoading !== null}
                onClick={() => handleAction(currentTask, "resume")}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold transition-colors ${
                  isWired
                    ? "bg-blue-600 hover:bg-blue-500 text-white cursor-pointer"
                    : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-60"
                }`}
              >
                {actionLoading === `${currentTask.id}-resume` ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RotateCcw className="w-4 h-4" />
                )}
                Resume
              </button>
            )}

            {/* Show Block only when task is in_progress (not already blocked) */}
            {currentTask.status === "in_progress" && (
              <button
                type="button"
                disabled={!isWired || actionLoading !== null}
                onClick={() => handleAction(currentTask, "block", "Blocat de operator")}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold transition-colors ${
                  isWired
                    ? "bg-red-600 hover:bg-red-500 text-white cursor-pointer"
                    : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-60"
                }`}
              >
                {actionLoading === `${currentTask.id}-block` ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <AlertTriangle className="w-4 h-4" />
                )}
                Block
              </button>
            )}

            {/* Show Unblock when task is blocked */}
            {currentTask.status === "blocked" && (
              <button
                type="button"
                disabled={!isWired || actionLoading !== null}
                onClick={() => handleAction(currentTask, "unblock")}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-semibold transition-colors ${
                  isWired
                    ? "bg-orange-600 hover:bg-orange-500 text-white cursor-pointer"
                    : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-60"
                }`}
              >
                {actionLoading === `${currentTask.id}-unblock` ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Unlock className="w-4 h-4" />
                )}
                Unblock
              </button>
            )}

            <div className="flex-1" />

            {/* Complete — disabled when blocked or paused */}
            <button
              type="button"
              disabled={!isWired || actionLoading !== null || currentTask.status === "blocked" || currentTask.status === "paused"}
              onClick={() => handleAction(currentTask, "complete")}
              title={
                currentTask.status === "blocked"
                  ? "Nu se poate completa — task blocat. Deblocați mai întâi."
                  : currentTask.status === "paused"
                  ? "Nu se poate completa — task în pauză. Reluați mai întâi."
                  : undefined
              }
              className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-[13px] font-semibold transition-colors ${
                isWired && currentTask.status !== "blocked" && currentTask.status !== "paused"
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer"
                  : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-60"
              }`}
            >
              {actionLoading === `${currentTask.id}-complete` ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              Complete
            </button>
          </div>
          {isMockSource && (
            <p className="text-[10px] text-slate-500 mt-2 italic">
              Butoanele sunt dezactivate — conectați backend-ul pentru a le activa.
            </p>
          )}
          {isWired && currentTask.status === "blocked" && (
            <p className="text-[10px] text-red-400 mt-2 italic">
              Task blocat — deblocați pentru a putea completa.
              {currentTask.blockReason ? (
                <span className="block mt-1 text-red-300/90 not-italic">
                  Motiv: {currentTask.blockReason}
                </span>
              ) : null}
            </p>
          )}
          {isWired && currentTask.status === "paused" && (
            <p className="text-[10px] text-amber-400 mt-2 italic">
              Task în pauză — reluați pentru a putea completa.
            </p>
          )}
        </div>
      ) : (
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-xl p-8 text-center">
          <p className="text-slate-500 text-[14px]">Niciun task activ. Selectează din lista de mai jos.</p>
        </div>
      )}

      {/* Materials Capture Panel — visible when a task is active and wired to DB */}
      {currentTask && isWired && currentOrderId > 0 && (
        <MaterialsCapturePanel
          orderId={currentOrderId}
          taskId={currentTask.id}
          materials={materials}
          onAdd={handleAddMaterials}
          onUpdate={handleUpdateMaterial}
          onRemove={handleRemoveMaterial}
          disabled={false}
          reporterEmployeeId={currentTask.employeeId ?? selectedEmployeeId}
          reporterEmployeeName={
            currentTask.employeeName ??
            selectedEmployee?.name ??
            null
          }
        />
      )}

      {/* Next Tasks */}
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
        <SectionHeader title="Next Tasks" count={nextTasks.length} icon={<ChevronRight className="w-4 h-4" />} />
        <div className="space-y-2">
          {nextTasks.map((task, idx) => (
            <div
              key={task.id}
              className="flex items-center gap-3 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2.5 hover:border-blue-700/50 transition-colors cursor-pointer"
            >
              <span className="text-[12px] font-mono text-slate-600 w-5">{idx + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <OperatorTaskIdentityPresentation
                    truth={resolveTruthForTask(task)}
                    fallbackOperationName={task.operationName}
                    fallbackTaskId={task.id}
                    compact
                    testId={`operator-next-task-identity-${task.id}`}
                  />
                  <ExecutionTaskStatusBadge status={task.status} />
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {task.client} · {task.machineName} · {task.plannedDurationMin}min plan
                </p>
              </div>
              <button
                type="button"
                disabled={
                  !isWired ||
                  actionLoading !== null ||
                  (registryAvailable && !selectedEmployee) ||
                  isTaskStartable(task) === false
                }
                onClick={() => handleAction(task, "start")}
                title={
                  registryAvailable && !selectedEmployee
                    ? "Selectați angajat din registry"
                    : isTaskStartable(task) === false
                      ? taskStartBlockReason(task) || "Task nepregatit"
                      : undefined
                }
                className={`flex items-center gap-1 px-3 py-1.5 rounded text-[11px] font-semibold transition-colors ${
                  isWired && (!registryAvailable || selectedEmployee)
                    ? "bg-blue-600 hover:bg-blue-500 text-white cursor-pointer"
                    : "bg-slate-700 text-slate-400 cursor-not-allowed opacity-60"
                }`}
              >
                {actionLoading === `${task.id}-start` ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Play className="w-3 h-3" />
                )}
                Start
              </button>
            </div>
          ))}
          {nextTasks.length === 0 && (
            <div className="text-center py-4 text-[12px] text-slate-500">
              Niciun task în așteptare.
            </div>
          )}
        </div>
      </div>

      {/* Task Timeline */}
      {firstJobId && (
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <SectionHeader title={`Task Timeline — ${firstJobId}`} icon={<Zap className="w-4 h-4" />} />
          <div className="relative pl-6">
            {tasks
              .filter((t) => t.jobId === firstJobId)
              .sort((a, b) => a.sequenceIndex - b.sequenceIndex)
              .map((task, idx, arr) => {
                const isActive = task.status === "in_progress";
                const isDone = task.status === "done";
                const dotColor = isActive
                  ? "bg-emerald-500 ring-2 ring-emerald-500/30"
                  : isDone
                  ? "bg-emerald-600"
                  : "bg-slate-600";

                return (
                  <div key={task.id} className="relative pb-4">
                    {/* Line */}
                    {idx < arr.length - 1 && (
                      <div className="absolute left-[-16px] top-3 w-px h-full bg-wo-hover" />
                    )}
                    {/* Dot */}
                    <div className={`absolute left-[-20px] top-1 w-3 h-3 rounded-full ${dotColor}`} />
                    {/* Content */}
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <OperatorTaskIdentityPresentation
                            truth={resolveTruthForTask(task)}
                            fallbackOperationName={task.operationName}
                            fallbackTaskId={task.id}
                            compact
                            testId={`operator-timeline-task-identity-${task.id}`}
                          />
                          <ExecutionTaskStatusBadge status={task.status} />
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {task.machineName} · {task.employeeName || task.assignee || "—"} · {task.plannedDurationMin}min
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}