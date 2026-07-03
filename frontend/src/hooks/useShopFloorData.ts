import { useEffect, useState, useCallback, useRef } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  machines as mockMachines,
  workcenters as mockWorkcenters,
  executionJobs as mockJobs,
  productionAlerts as mockAlerts,
  type Machine,
  type Workcenter,
  type ExecutionJob,
  type ProductionAlert,
} from "@/lib/mockData";

interface ShopFloorState {
  machines: Machine[];
  workcenters: Workcenter[];
  jobs: ExecutionJob[];
  alerts: ProductionAlert[];
  lastUpdate: Date;
  updateCount: number;
  source: "db" | "mock" | "empty" | "error" | "loading";
  connectionStatus: "connecting" | "connected" | "reconnecting";
  error: string | null;
}

/** DB machine row from /api/v1/machines */
interface DBMachine {
  id: number;
  machine_code: string;
  name: string;
  description?: string;
  machine_type: string;
  workcenter_code: string;
  operational_status: string;
  is_available: boolean;
  capabilities?: string[];
  capacity_metadata?: Record<string, unknown>;
}

/** Task from /api/v1/operator/tasks */
interface DBTask {
  task_id: string;
  order_id: number;
  order_code: string;
  name: string;
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
  order_status: string;
}

// Map workcenter_code to a friendly name
const wcNameMap: Record<string, string> = {
  WC_PRINT: "Print",
  WC_LAMINATE: "Laminare",
  WC_CUT: "Cut / Plotter",
  WC_CNC: "CNC",
  WC_METAL: "Metal / Sudură",
  WC_ASSEMBLY: "Asamblare",
  WC_ELECTRIC: "Electric",
  WC_OUTPUT: "Ambalare / Livrare",
};

function mapDBMachineToMachine(m: DBMachine, tasks: DBTask[]): Machine {
  // Find active task for this machine (by machine_type match)
  const activeTask = tasks.find(
    (t) =>
      t.status === "in_progress" &&
      t.machine_type.toLowerCase().includes(m.machine_type.toLowerCase().replace(/\s+/g, "_"))
  );

  const statusMap: Record<string, Machine["status"]> = {
    operational: "running",
    idle: "idle",
    maintenance: "maintenance",
    offline: "offline",
    under_maintenance: "maintenance",
  };

  const status: Machine["status"] =
    statusMap[m.operational_status?.toLowerCase()] ??
    (m.is_available ? "idle" : "maintenance");

  // Count queued tasks for this machine type
  const queuedTasks = tasks.filter(
    (t) =>
      t.status === "assigned" &&
      t.machine_type.toLowerCase().includes(m.machine_type.toLowerCase().replace(/\s+/g, "_"))
  );

  return {
    id: m.machine_code,
    name: m.name,
    type: m.machine_type,
    workcenterId: `wc_${m.workcenter_code.toLowerCase().replace(/^wc_/, "")}`,
    status: activeTask ? "running" : status,
    currentJobId: activeTask ? `ORD-${activeTask.order_id}` : null,
    currentOperationCode: activeTask ? activeTask.process_type : null,
    currentOperator: null,
    runtimeMinutes: activeTask?.actual_minutes ?? 0,
    utilizationPct: m.is_available
      ? activeTask
        ? Math.min(85, Math.round((activeTask.actual_minutes ?? 0) / Math.max(activeTask.estimated_time_minutes, 1) * 100))
        : 40
      : 0,
    queueCount: queuedTasks.length,
    nextJobId: queuedTasks[0] ? `ORD-${queuedTasks[0].order_id}` : null,
  };
}

function buildWorkcenters(machines: Machine[]): Workcenter[] {
  const wcMap = new Map<string, Workcenter>();

  for (const m of machines) {
    const wcId = m.workcenterId;
    if (!wcMap.has(wcId)) {
      const cleanCode = wcId.replace("wc_", "").toUpperCase();
      wcMap.set(wcId, {
        id: wcId,
        name: wcNameMap[`WC_${cleanCode}`] ?? cleanCode,
        machineIds: [],
        queueCount: 0,
        activeJobs: 0,
        blockedCount: 0,
      });
    }
    const wc = wcMap.get(wcId)!;
    wc.machineIds.push(m.id);
    wc.queueCount += m.queueCount;
    if (m.status === "running") wc.activeJobs++;
    if (m.status === "maintenance") wc.blockedCount++;
  }

  return Array.from(wcMap.values());
}

function tasksToJobs(tasks: DBTask[]): ExecutionJob[] {
  // Group tasks by order_id to create "jobs"
  const orderMap = new Map<number, DBTask[]>();
  for (const t of tasks) {
    if (!orderMap.has(t.order_id)) orderMap.set(t.order_id, []);
    orderMap.get(t.order_id)!.push(t);
  }

  return Array.from(orderMap.entries()).map(([orderId, orderTasks]) => {
    const first = orderTasks[0];
    const completed = orderTasks.filter((t) => t.status === "done").length;
    const inProgress = orderTasks.some((t) => t.status === "in_progress");
    const blocked = orderTasks.some((t) => t.status === "blocked");
    const totalEstMin = orderTasks.reduce((s, t) => s + t.estimated_time_minutes, 0);
    const totalActMin = orderTasks.reduce((s, t) => s + (t.actual_minutes ?? 0), 0);
    const progress = orderTasks.length > 0 ? Math.round((completed / orderTasks.length) * 100) : 0;

    let status: ExecutionJob["status"] = "scheduled";
    if (blocked) status = "blocked";
    else if (completed === orderTasks.length) status = "completed";
    else if (inProgress) status = "in_progress";

    // Find current operation
    const currentTask = orderTasks.find((t) => t.status === "in_progress");

    return {
      id: `JOB-${String(orderId).padStart(4, "0")}`,
      orderId: first.order_code,
      client: first.client || `Client #${orderId}`,
      product: first.product || first.name,
      productType: "general",
      status,
      priority: "normal" as const,
      promisedAt: "",
      productionDeadline: "",
      currentOperation: currentTask?.process_type ?? orderTasks[0]?.process_type ?? "",
      currentWorkcenter: currentTask?.machine_type ?? "",
      operationsCompleted: completed,
      operationsTotal: orderTasks.length,
      progress,
      estimatedTotalMinutes: totalEstMin,
      actualMinutes: totalActMin,
      isLate: false,
      isBlocked: blocked,
      riskLevel: blocked ? "high" : "none",
      riskReason: blocked ? "Task blocat" : null,
    };
  });
}

export function useShopFloorData(intervalMs = 10000): ShopFloorState {
  const mockEnabled = isMockEnabled();
  const [machines, setMachines] = useState<Machine[]>([]);
  const [workcenters, setWorkcenters] = useState<Workcenter[]>([]);
  const [jobs, setJobs] = useState<ExecutionJob[]>([]);
  const [alerts] = useState<ProductionAlert[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [updateCount, setUpdateCount] = useState(0);
  const [source, setSource] = useState<"db" | "mock" | "empty" | "error" | "loading">("loading");
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "reconnecting">("connecting");
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const base = getAPIBaseURL();
      const [machinesRes, tasksRes] = await Promise.all([
        fetch(`${base}/api/v1/machines`, { credentials: "include" }),
        fetch(`${base}/api/v1/operator/tasks`, { credentials: "include" }),
      ]);

      if (!machinesRes.ok || !tasksRes.ok) throw new Error("API error");

      const dbMachines: DBMachine[] = await machinesRes.json();
      const tasksData = await tasksRes.json();
      const dbTasks: DBTask[] = tasksData.tasks ?? [];

      if (dbMachines.length > 0) {
        const mappedMachines = dbMachines.map((m) => mapDBMachineToMachine(m, dbTasks));
        const builtWorkcenters = buildWorkcenters(mappedMachines);
        const builtJobs = tasksToJobs(dbTasks);

        setMachines(mappedMachines);
        setWorkcenters(builtWorkcenters);
        setJobs(builtJobs);
        setSource("db");
        setError(null);
      } else if (mockEnabled) {
        // DB has machines table but empty — use mock
        setMachines(mockMachines);
        setWorkcenters(mockWorkcenters);
        setJobs(mockJobs);
        setSource("mock");
        setError(null);
      } else {
        // DB empty, mock disabled — show empty
        setMachines([]);
        setWorkcenters([]);
        setJobs([]);
        setSource("empty");
        setError(null);
      }

      setConnectionStatus("connected");
      setLastUpdate(new Date());
      setUpdateCount((c) => c + 1);
    } catch (err) {
      console.warn("[useShopFloorData] API failed", err);
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
      if (source === "db") {
        setConnectionStatus("reconnecting");
      }
      // Only set mock/empty on first load failure
      if (source === "loading") {
        if (mockEnabled) {
          setMachines(mockMachines);
          setWorkcenters(mockWorkcenters);
          setJobs(mockJobs);
          setSource("mock");
        } else {
          setMachines([]);
          setWorkcenters([]);
          setJobs([]);
          setSource("error");
        }
        setConnectionStatus("reconnecting");
      }
      setLastUpdate(new Date());
      setUpdateCount((c) => c + 1);
    }
  }, [source]);

  useEffect(() => {
    fetchData();
    intervalRef.current = setInterval(fetchData, intervalMs);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchData, intervalMs]);

  return {
    machines,
    workcenters,
    jobs,
    alerts,
    lastUpdate,
    updateCount,
    source,
    connectionStatus,
    error,
  };
}