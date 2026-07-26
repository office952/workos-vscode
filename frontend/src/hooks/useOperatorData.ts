import { useEffect, useState, useCallback } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  parseStructuredActionError,
  type StructuredActionError,
} from "@/lib/operatorProductionBlockerPresentation";
import {
  operatorTasks as mockOperatorTasks,
  type OperatorTask,
  type TaskStatus,
} from "@/lib/mockData";

type OperatorSource = "db" | "mock" | "empty" | "error" | "loading";

interface OperatorDataState {
  tasks: OperatorTask[];
  loading: boolean;
  error: string | null;
  source: OperatorSource;
  lastActionError: StructuredActionError | null;
  refresh: () => Promise<void>;
  performAction: (
    orderId: number,
    taskId: string,
    action: string,
    reason?: string,
    employeeId?: number | null,
    operatorName?: string | null,
    completionNotes?: string | null
  ) => Promise<{ success: boolean; actionError: StructuredActionError | null }>;
}

/** Task from /api/v1/operator/tasks */
interface DBTask {
  task_id: string;
  order_id: number;
  order_code: string;
  name: string;
  display_name?: string;
  process_id?: string;
  process_type: string;
  machine_type: string;
  estimated_time_minutes: number;
  quantity: number;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  actual_minutes?: number;
  client: string;
  product: string;
  product_template?: string;
  quote_code?: string;
  intake_code?: string;
  material?: string;
  finish?: string;
  order_status: string;
  layer_id?: string;
  instructions?: string;
  employee_id?: number | null;
  employee_name?: string | null;
  operator_name?: string | null;
  assigned_employee_id?: number | null;
  assigned_employee_name?: string | null;
  block_reason?: string | null;
}

function mapDBTaskToOperatorTask(t: DBTask, idx: number): OperatorTask {
  const statusMap: Record<string, TaskStatus> = {
    assigned: "assigned",
    in_progress: "in_progress",
    paused: "paused",
    done: "done",
    blocked: "blocked",
    created: "created",
    cancelled: "cancelled",
  };

  const displayName = t.display_name || t.name;

  return {
    id: t.task_id,
    jobId: `JOB-${String(t.order_id).padStart(4, "0")}`,
    client: t.client || `Client #${t.order_id}`,
    product: t.product || displayName,
    operationCode: t.process_type,
    operationName: displayName,
    machineName: t.machine_type || "—",
    status: statusMap[t.status] ?? "created",
    assignee: t.assigned_employee_name || t.employee_name || t.operator_name || "—",
    employeeId: t.employee_id ?? null,
    employeeName: t.employee_name ?? null,
    assignedEmployeeId: t.assigned_employee_id ?? null,
    assignedEmployeeName: t.assigned_employee_name ?? null,
    blockReason: t.block_reason ?? null,
    plannedDurationMin: t.estimated_time_minutes,
    actualDurationMin: t.actual_minutes ?? null,
    startedAt: t.started_at ?? null,
    targetEndAt: null,
    instructions: (t.instructions || "").trim(),
    inputDependencies: idx > 0 ? ["Etapa anterioară completă"] : ["Material pregătit"],
    expectedOutput: `${displayName} completat`,
    sequenceIndex: idx + 1,
    orderCode: t.order_code,
    quoteCode: t.quote_code,
    intakeCode: t.intake_code,
    productTemplate: t.product_template,
    material: t.material,
    finish: t.finish,
    layerId: t.layer_id,
    processId: t.process_id,
  };
}

export function useOperatorData(): OperatorDataState {
  const mockEnabled = isMockEnabled();
  const [tasks, setTasks] = useState<OperatorTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastActionError, setLastActionError] = useState<StructuredActionError | null>(null);
  const [source, setSource] = useState<OperatorSource>("loading");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/operator/tasks`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const dbTasks: DBTask[] = data.tasks ?? [];

      if (dbTasks.length > 0) {
        setTasks(dbTasks.map((t, i) => mapDBTaskToOperatorTask(t, i)));
        setSource("db");
      } else {
        // Successful API with zero tasks is live empty — never substitute mock tasks.
        setTasks([]);
        setSource("empty");
      }
    } catch (err) {
      if (mockEnabled) {
        console.warn("[useOperatorData] API failed, using mock data", err);
        setTasks(mockOperatorTasks);
        setSource("mock");
      } else {
        console.warn("[useOperatorData] API failed, mock disabled", err);
        setTasks([]);
        setSource("error");
      }
      setError(err instanceof Error ? err.message : "Eroare necunoscută");
    } finally {
      setLoading(false);
    }
  }, [mockEnabled]);

  const performAction = useCallback(
    async (
      orderId: number,
      taskId: string,
      action: string,
      reason?: string,
      employeeId?: number | null,
      operatorName?: string | null,
      completionNotes?: string | null
    ): Promise<{ success: boolean; actionError: StructuredActionError | null }> => {
      setLastActionError(null);
      try {
        const base = getAPIBaseURL();
        const payload: Record<string, unknown> = {
          order_id: orderId,
          task_id: taskId,
          action,
          reason,
        };
        if (employeeId != null) {
          payload.employee_id = employeeId;
        }
        if (operatorName) {
          payload.operator_name = operatorName;
        }
        if (completionNotes) {
          payload.completion_notes = completionNotes;
        }
        const res = await fetch(`${base}/api/v1/operator/task-action`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          const parsed = parseStructuredActionError(res.status, errData);
          setLastActionError(parsed);
          console.error("[performAction] Failed:", errData);
          return { success: false, actionError: parsed };
        }
        // Refresh tasks after action
        await fetchData();
        return { success: true, actionError: null };
      } catch (err) {
        console.error("[performAction] Error:", err);
        return { success: false, actionError: null };
      }
    },
    [fetchData]
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { tasks, loading, error, source, lastActionError, refresh: fetchData, performAction };
}