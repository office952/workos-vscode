import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, UserPlus } from "lucide-react";
import { employeesApi } from "@/api/costEngine";
import {
  assignExecutionPlanTask,
  updateExecutionPlanTaskInstructions,
} from "@/api/executionTaskAssignment";
import type { OperatorTask } from "@/lib/mockData";
import { OperatorTaskIdentityPresentation } from "@/components/workos/OperatorTaskIdentityPresentation";
import type { OperatorTaskTruthTask } from "@/api/operatorTaskTruth";

type Props = {
  tasks: OperatorTask[];
  wired: boolean;
  onAssigned: () => Promise<void> | void;
  taskTruthByTaskId?: Record<string, OperatorTaskTruthTask>;
};

function extractOrderId(task: OperatorTask): number {
  const match = task.jobId.match(/JOB-(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

export default function OperatorTaskAssignmentPanel({ tasks, wired, onAssigned, taskTruthByTaskId = {} }: Props) {
  const [employees, setEmployees] = useState<Array<{ id: number; name: string }>>([]);
  const [loadingEmployees, setLoadingEmployees] = useState(true);
  const [selection, setSelection] = useState<Record<string, string>>({});
  const [instructionDrafts, setInstructionDrafts] = useState<Record<string, string>>({});
  const [assigning, setAssigning] = useState<string | null>(null);
  const [savingInstructions, setSavingInstructions] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoadingEmployees(true);
      try {
        const res = await employeesApi.list({ limit: 200 });
        if (!cancelled) {
          setEmployees(res.items.map((e) => ({ id: e.id, name: e.name })));
        }
      } catch {
        if (!cancelled) setEmployees([]);
      } finally {
        if (!cancelled) setLoadingEmployees(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const assignableTasks = useMemo(
    () =>
      tasks.filter(
        (task) =>
          wired &&
          task.status !== "done" &&
          task.status !== "cancelled",
      ),
    [tasks, wired],
  );

  const handleAssign = useCallback(
    async (task: OperatorTask) => {
      const orderId = extractOrderId(task);
      const selected = selection[task.id];
      if (!orderId || !selected) return;
      setAssigning(task.id);
      setError(null);
      setSuccess(null);
      try {
        await assignExecutionPlanTask(orderId, task.id, Number(selected));
        setSuccess(`Task ${task.id} atribuit.`);
        await onAssigned();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Atribuire eșuată.");
      } finally {
        setAssigning(null);
      }
    },
    [onAssigned, selection],
  );

  const handleSaveInstructions = useCallback(
    async (task: OperatorTask) => {
      const orderId = extractOrderId(task);
      if (!orderId) return;
      const draft = instructionDrafts[task.id] ?? task.instructions ?? "";
      setSavingInstructions(task.id);
      setError(null);
      setSuccess(null);
      try {
        await updateExecutionPlanTaskInstructions(orderId, task.id, draft);
        setSuccess(`Instrucțiuni salvate pentru ${task.id}.`);
        await onAssigned();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Salvare instrucțiuni eșuată.");
      } finally {
        setSavingInstructions(null);
      }
    },
    [instructionDrafts, onAssigned],
  );

  if (!wired) return null;

  return (
    <div
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-xl p-4 space-y-3"
      data-testid="operator-task-assignment-panel"
    >
      <div className="flex items-center gap-2">
        <UserPlus className="w-4 h-4 text-violet-400" />
        <h2 className="text-[13px] font-semibold text-slate-200">Atribuire taskuri (plan producție)</h2>
        {loadingEmployees && <Loader2 className="w-3.5 h-3.5 text-slate-500 animate-spin" />}
      </div>
      <p className="text-[11px] text-slate-400 leading-relaxed">
        Atribuie taskuri din execution plan către angajați. Instrucțiunile manuale apar pe Employee Mobile
        doar când sunt completate aici — nu se generează automat.
      </p>
      {error && (
        <p className="text-[11px] text-red-300" data-testid="operator-task-assignment-error">
          {error}
        </p>
      )}
      {success && (
        <p className="text-[11px] text-emerald-300" data-testid="operator-task-assignment-success">
          {success}
        </p>
      )}
      {assignableTasks.length === 0 ? (
        <p className="text-[12px] text-slate-500">Niciun task disponibil pentru atribuire.</p>
      ) : (
        <div className="space-y-2">
          {assignableTasks.map((task) => {
            const assignedLabel =
              task.assignedEmployeeName ||
              (task.assignedEmployeeId ? `Angajat #${task.assignedEmployeeId}` : "Neatribuit");
            const instructionValue =
              instructionDrafts[task.id] ?? task.instructions ?? "";
            return (
              <div
                key={task.id}
                className="flex flex-col gap-2 rounded-lg border border-wo-border-strong bg-wo-surface-raised px-3 py-2.5"
                data-testid={`operator-task-assignment-row-${task.id}`}
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <div className="min-w-0 flex-1">
                    <OperatorTaskIdentityPresentation
                      truth={taskTruthByTaskId[task.id]}
                      fallbackOperationName={task.operationName}
                      fallbackTaskId={task.id}
                      compact
                      testId={`operator-assignment-task-identity-${task.id}`}
                    />
                    <p className="text-[10px] text-slate-500 mt-1">
                      {task.jobId} · {task.status} · {assignedLabel}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={selection[task.id] ?? String(task.assignedEmployeeId ?? "")}
                      onChange={(event) =>
                        setSelection((prev) => ({ ...prev, [task.id]: event.target.value }))
                      }
                      className="min-w-[160px] bg-[#0A1020] border border-wo-border-strong rounded-lg px-2 py-1.5 text-[12px] text-slate-200"
                      data-testid={`operator-task-assignment-select-${task.id}`}
                    >
                      <option value="">— Angajat —</option>
                      {employees.map((emp) => (
                        <option key={emp.id} value={emp.id}>
                          {emp.name}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      disabled={assigning === task.id || !selection[task.id]}
                      onClick={() => void handleAssign(task)}
                      className="px-3 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 disabled:opacity-50 text-[12px] font-semibold text-white"
                      data-testid={`operator-task-assignment-submit-${task.id}`}
                    >
                      {assigning === task.id ? "…" : "Atribuie"}
                    </button>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label
                    className="text-[10px] font-medium text-slate-400"
                    htmlFor={`operator-task-instructions-${task.id}`}
                  >
                    Instrucțiuni execuție
                  </label>
                  <textarea
                    id={`operator-task-instructions-${task.id}`}
                    value={instructionValue}
                    onChange={(event) =>
                      setInstructionDrafts((prev) => ({
                        ...prev,
                        [task.id]: event.target.value,
                      }))
                    }
                    rows={3}
                    placeholder="Opțional — vizibile pe Employee Mobile când sunt salvate."
                    className="w-full bg-[#0A1020] border border-wo-border-strong rounded-lg px-2.5 py-2 text-[12px] text-slate-200 resize-y min-h-[72px]"
                    data-testid={`operator-task-instructions-input-${task.id}`}
                  />
                  <div className="flex justify-end">
                    <button
                      type="button"
                      disabled={savingInstructions === task.id}
                      onClick={() => void handleSaveInstructions(task)}
                      className="px-3 py-1.5 rounded-lg border border-wo-border-strong hover:bg-[#243047] disabled:opacity-50 text-[12px] font-medium text-slate-200"
                      data-testid={`operator-task-instructions-save-${task.id}`}
                    >
                      {savingInstructions === task.id ? "…" : "Salvează instrucțiuni"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
