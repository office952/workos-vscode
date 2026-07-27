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
  type OperationalTruth,
} from "@/lib/mockData";

export type DataSource = "db" | "mock" | "empty" | "error" | "loading";

const MOCK_OPERATIONAL_TRUTH: OperationalTruth = {
  plannedMinutesTotal: 0,
  actualMinutesTotal: 0,
  overrunMinutesTotal: 0,
  throughputWindow: "utc_calendar_today",
  workcenterLoadKind: "planned_load_0_100",
  calendarShiftUtilAvailable: false,
  notices: [
    "Pricing Registry: gap mock — Owner data needed pe rate lipsă.",
    "Cost Intern (HR analytics — NU tarif client): gap mock angajați incompleți.",
    "Capacitate: util calendar/shift necunoscut — Utilaje fără semnal rămân GAP.",
    "Utilaj calendar/shift: date indisponibile — afișăm load planificat 0–100 pe workcenter (nu utilizare pe ture/calendar).",
    "Capacitate / load planificat — nu pricing comercial, nu cost orar utilaj → tarif client.",
    "Throughput azi = comenzi completed cu updated_at în ziua calendaristică UTC curentă.",
    "OTIF este proxy slab: fără realitate/deadline clar, comenzile finalizate sunt tratate ca on-time.",
  ],
  dataGaps: {
    pricing: {
      domain: "pricing_registry",
      ownerDataNeeded: true,
      missingPriceCount: 1,
      notice: "Pricing Registry: gap mock — Owner data needed pe rate lipsă.",
      boundary: "Material cost ≠ commercial markup ≠ internal op rate.",
    },
    costIntern: {
      domain: "hr_internal_cost",
      ownerDataNeeded: true,
      incompleteEmployeeCount: 1,
      valid: false,
      notice: "Cost Intern (HR analytics — NU tarif client): gap mock angajați incompleți.",
      boundary: "Employee cost = analytics only — NEVER client price.",
    },
    capacity: {
      domain: "capacity_feasibility",
      ownerDataNeeded: true,
      unknown: true,
      calendarShiftUtilAvailable: false,
      notice: "Capacitate: util calendar/shift necunoscut — Utilaje fără semnal rămân GAP.",
      boundary: "Capacity ≠ commercial tariff.",
    },
  },
  boundaries: {
    pricing: "Dashboard does not compute or display client tariffs. Material ≠ commercial ≠ internal rate.",
    hrCost: "Cost Intern / HR = analytics/profitability only — never client tariff.",
    machines: "Load is planned-load % / capacity feasibility — not machine hourly → client price.",
    executionPlan: "Reads ExecutionPlan/Reality only — no materialization.",
    productSystem: "No ProductDefinition / ProductAggregate ownership.",
  },
};

interface DashboardStats {
  kpis: KPIValue[];
  jobs: ExecutionJob[];
  capacity: CapacitySlot[];
  alerts: ProductionAlert[];
  throughput: TrendPoint[];
  events: SystemEvent[];
  operationalTruth: OperationalTruth | null;
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
  const [operationalTruth, setOperationalTruth] = useState<OperationalTruth | null>(
    mockEnabled ? MOCK_OPERATIONAL_TRUTH : null,
  );
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

      if (data.operationalTruth) {
        setOperationalTruth(data.operationalTruth as OperationalTruth);
      } else {
        setOperationalTruth(MOCK_OPERATIONAL_TRUTH);
      }

      setSource("db");
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      if (!mountedRef.current) return;
      if (mockEnabled) {
        console.warn("[useDashboardStats] API unavailable, using mock data:", err);
        setOperationalTruth(MOCK_OPERATIONAL_TRUTH);
        setSource("mock");
      } else {
        console.warn("[useDashboardStats] API unavailable, mock disabled:", err);
        setKpis([]);
        setJobs([]);
        setCapacity([]);
        setAlerts([]);
        setThroughput([]);
        setEvents([]);
        setOperationalTruth(null);
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
    operationalTruth,
    source,
    loading,
    error,
    lastUpdate,
    refresh: fetchStats,
  };
}