import { useState, useEffect, useCallback, useRef } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  dailyMetrics as mockDailyMetrics,
  wcUtilHeatmap as mockWcHeatmap,
  executionJobs as mockExecutionJobs,
  type DailyMetric,
  type WorkcenterUtilHeatmap,
} from "@/lib/mockData";

export type ReportsSource = "db" | "mock" | "empty" | "error" | "loading";

interface JobStatusItem {
  label: string;
  count: number;
  color: string;
}

interface ReportsData {
  dailyMetrics: DailyMetric[];
  wcUtilHeatmap: WorkcenterUtilHeatmap[];
  jobStatuses: JobStatusItem[];
  source: ReportsSource;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Fetches real reports data from /api/v1/reports-summary.
 * Falls back to mockData if the API is unavailable.
 */
export function useReportsData(): ReportsData {
  const mockEnabled = isMockEnabled();

  // Compute default job statuses from mock data (only when mock is enabled)
  const defaultJobStatuses: JobStatusItem[] = mockEnabled
    ? [
        { label: "Pending", count: mockExecutionJobs.filter((j) => j.status === "pending").length, color: "bg-slate-500" },
        { label: "Scheduled", count: mockExecutionJobs.filter((j) => j.status === "scheduled").length, color: "bg-purple-500" },
        { label: "In Progress", count: mockExecutionJobs.filter((j) => j.status === "in_progress").length, color: "bg-blue-500" },
        { label: "Blocked", count: mockExecutionJobs.filter((j) => j.status === "blocked").length, color: "bg-red-500" },
        { label: "Completed", count: mockExecutionJobs.filter((j) => j.status === "completed").length, color: "bg-emerald-500" },
      ]
    : [];

  const [dailyMetrics, setDailyMetrics] = useState<DailyMetric[]>(mockEnabled ? mockDailyMetrics : []);
  const [wcUtilHeatmap, setWcUtilHeatmap] = useState<WorkcenterUtilHeatmap[]>(mockEnabled ? mockWcHeatmap : []);
  const [jobStatuses, setJobStatuses] = useState<JobStatusItem[]>(defaultJobStatuses);
  const [source, setSource] = useState<ReportsSource>(mockEnabled ? "mock" : "loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/reports-summary`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (!mountedRef.current) return;

      if (data.dailyMetrics?.length) {
        setDailyMetrics(data.dailyMetrics as DailyMetric[]);
      }

      if (data.wcUtilHeatmap?.length) {
        setWcUtilHeatmap(data.wcUtilHeatmap as WorkcenterUtilHeatmap[]);
      }

      if (data.jobStatuses?.length) {
        setJobStatuses(data.jobStatuses as JobStatusItem[]);
      }

      setSource("db");
      setError(null);
    } catch (err) {
      if (!mountedRef.current) return;
      if (mockEnabled) {
        console.warn("[useReportsData] API unavailable, using mock data:", err);
        setSource("mock");
      } else {
        console.warn("[useReportsData] API unavailable, mock disabled:", err);
        setDailyMetrics([]);
        setWcUtilHeatmap([]);
        setJobStatuses([]);
        setSource("error");
      }
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchData]);

  return {
    dailyMetrics,
    wcUtilHeatmap,
    jobStatuses,
    source,
    loading,
    error,
    refresh: fetchData,
  };
}