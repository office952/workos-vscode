import { useState, useEffect, useCallback, useRef } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  managementKPIs,
  executionJobs,
  capacityLoad,
  productionAlerts,
  throughputTrend,
  recentEvents,
  type KPIValue,
  type ExecutionJob,
  type CapacitySlot,
  type ProductionAlert,
  type TrendPoint,
  type SystemEvent,
} from "@/lib/mockData";

export type DataSource = "db" | "mock" | "empty" | "error" | "loading";

interface DashboardStats {
  kpis: KPIValue[];
  jobs: ExecutionJob[];
  capacity: CapacitySlot[];
  alerts: ProductionAlert[];
  throughput: TrendPoint[];
  events: SystemEvent[];
  source: DataSource;
  loading: boolean;
  error: string | null;
  lastUpdate: Date;
  refresh: () => Promise<void>;
}

/**
 * Fetches real dashboard data from /api/v1/dashboard-stats.
 * Falls back to mockData if the API is unavailable.
 * Auto-refreshes every `intervalMs` milliseconds.
 */
export function useDashboardStats(intervalMs = 30000): DashboardStats {
  const mockEnabled = isMockEnabled();
  const [kpis, setKpis] = useState<KPIValue[]>(mockEnabled ? managementKPIs : []);
  const [jobs, setJobs] = useState<ExecutionJob[]>(mockEnabled ? executionJobs : []);
  const [capacity, setCapacity] = useState<CapacitySlot[]>(mockEnabled ? capacityLoad : []);
  const [alerts, setAlerts] = useState<ProductionAlert[]>(mockEnabled ? productionAlerts : []);
  const [throughput, setThroughput] = useState<TrendPoint[]>(mockEnabled ? throughputTrend : []);
  const [events, setEvents] = useState<SystemEvent[]>(mockEnabled ? recentEvents : []);
  const [source, setSource] = useState<DataSource>(mockEnabled ? "mock" : "loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const mountedRef = useRef(true);

  const fetchStats = useCallback(async () => {
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/dashboard-stats`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (!mountedRef.current) return;

      // Map API KPIs to the KPIValue shape
      if (data.kpis?.length) {
        setKpis(data.kpis as KPIValue[]);
      }

      // Map API execution jobs
      if (data.executionJobs?.length) {
        setJobs(data.executionJobs as ExecutionJob[]);
      }

      // Map capacity load
      if (data.capacityLoad?.length) {
        setCapacity(data.capacityLoad as CapacitySlot[]);
      }

      // Map alerts
      if (data.alerts) {
        setAlerts(data.alerts as ProductionAlert[]);
      }

      // Map throughput trend
      if (data.throughputTrend?.length) {
        setThroughput(data.throughputTrend as TrendPoint[]);
      }

      // Map events
      if (data.recentEvents?.length) {
        setEvents(data.recentEvents as SystemEvent[]);
      }

      setSource("db");
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      if (!mountedRef.current) return;
      if (mockEnabled) {
        console.warn("[useDashboardStats] API unavailable, using mock data:", err);
        setSource("mock");
      } else {
        console.warn("[useDashboardStats] API unavailable, mock disabled:", err);
        setKpis([]);
        setJobs([]);
        setCapacity([]);
        setAlerts([]);
        setThroughput([]);
        setEvents([]);
        setSource("error");
      }
      setError(err instanceof Error ? err.message : "Unknown error");
      setLastUpdate(new Date());
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchStats();

    const interval = setInterval(fetchStats, intervalMs);
    return () => {
      mountedRef.current = false;
      clearInterval(interval);
    };
  }, [fetchStats, intervalMs]);

  return {
    kpis,
    jobs,
    capacity,
    alerts,
    throughput,
    events,
    source,
    loading,
    error,
    lastUpdate,
    refresh: fetchStats,
  };
}