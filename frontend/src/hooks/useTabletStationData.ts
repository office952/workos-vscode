import { useCallback, useEffect, useMemo, useState } from "react";
import { operationalRegistryApi, type OperationResourceMapping } from "@/api/operationalRegistry";
import { useOperatorData } from "@/hooks/useOperatorData";
import { useOperatorEmployees } from "@/hooks/useOperatorEmployees";
import type { OperatorEmployeeOption } from "@/lib/operatorEmployeeEligibility";
import {
  filterLiveTasksForStation,
  STATION_WORKCENTER_CODES,
  taskBelongsToStation,
} from "@/lib/tabletLiveBridge";
import type { OperatorTask } from "@/lib/mockData";
import { generateDemoTasks, WORKSTATIONS, type TabletTask } from "@/lib/workstationRouting";

export type TabletDataSource = "live" | "demo" | "empty" | "error" | "loading";

export interface UseTabletStationDataResult {
  tasks: TabletTask[];
  operatorTasks: OperatorTask[];
  source: TabletDataSource;
  operatorSource: ReturnType<typeof useOperatorData>["source"];
  loading: boolean;
  error: string | null;
  operationMappings: OperationResourceMapping[];
  refresh: () => Promise<void>;
  performAction: ReturnType<typeof useOperatorData>["performAction"];
  isLive: boolean;
  registryEmployees: OperatorEmployeeOption[];
  registrySource: ReturnType<typeof useOperatorEmployees>["source"];
  registryError: string | null;
  getStationLiveTasks: (id: string) => TabletTask[];
}

export function useTabletStationData(stationId?: string): UseTabletStationDataResult {
  const {
    tasks: operatorTasks,
    loading: operatorLoading,
    error: operatorError,
    source: operatorSource,
    refresh: refreshOperator,
    performAction,
  } = useOperatorData();

  const [mappings, setMappings] = useState<OperationResourceMapping[]>([]);
  const [mappingsLoading, setMappingsLoading] = useState(true);
  const [mappingsError, setMappingsError] = useState<string | null>(null);

  const loadMappings = useCallback(async () => {
    setMappingsLoading(true);
    setMappingsError(null);
    try {
      const res = await operationalRegistryApi.listOperationMappings();
      setMappings(res.items);
    } catch (err) {
      setMappings([]);
      setMappingsError(err instanceof Error ? err.message : "Eroare mapping registry");
    } finally {
      setMappingsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMappings();
  }, [loadMappings]);

  const eligibilityTask = useMemo((): OperatorTask | null => {
    if (!stationId || operatorTasks.length === 0) return operatorTasks[0] ?? null;
    const inStation = operatorTasks.filter(
      (t) => taskBelongsToStation(t, stationId, mappings).include
    );
    return (
      inStation.find((t) => t.status === "assigned" || t.status === "created") ??
      inStation[0] ??
      operatorTasks[0] ??
      null
    );
  }, [operatorTasks, stationId, mappings]);

  const {
    employees: registryEmployees,
    loading: employeesLoading,
    error: registryError,
    source: registrySource,
  } = useOperatorEmployees(eligibilityTask);

  const isOperatorLive = operatorSource === "db" || operatorSource === "empty";
  const isLive = isOperatorLive;
  const loading = operatorLoading || mappingsLoading || (stationId ? employeesLoading : false);

  const getStationLiveTasks = useCallback(
    (id: string) => filterLiveTasksForStation(operatorTasks, id, mappings),
    [operatorTasks, mappings]
  );

  const liveTabletTasks = useMemo(() => {
    if (!isLive) return [];
    if (stationId) return getStationLiveTasks(stationId);
    return WORKSTATIONS.flatMap((ws) => getStationLiveTasks(ws.id));
  }, [isLive, stationId, getStationLiveTasks]);

  const demoTasks = useMemo(() => {
    const all = generateDemoTasks().map((t) => ({ ...t, isDemo: true }));
    if (!stationId) return all;
    return all.filter((t) => t.workstationId === stationId);
  }, [stationId]);

  const tasks = isOperatorLive ? liveTabletTasks : demoTasks;

  const stationRegistryEmployees = useMemo(() => {
    if (!stationId || eligibilityTask) return registryEmployees;
    const stationWcs = STATION_WORKCENTER_CODES[stationId] ?? [];
    if (stationWcs.length === 0) return registryEmployees;
    return registryEmployees.filter((emp) =>
      emp.workcenterCodes.some((wc) => stationWcs.includes(wc))
    );
  }, [registryEmployees, stationId, eligibilityTask]);

  let source: TabletDataSource = "loading";
  if (!loading) {
    if (isOperatorLive) source = liveTabletTasks.length > 0 ? "live" : "empty";
    else if (operatorSource === "error") source = "error";
    else source = "demo";
  }

  const refresh = useCallback(async () => {
    await Promise.all([refreshOperator(), loadMappings()]);
  }, [refreshOperator, loadMappings]);

  return {
    tasks,
    operatorTasks,
    source,
    operatorSource,
    loading,
    error: operatorError || mappingsError || registryError,
    operationMappings: mappings,
    refresh,
    performAction,
    isLive,
    registryEmployees: stationRegistryEmployees,
    registrySource,
    registryError,
    getStationLiveTasks,
  };
}
