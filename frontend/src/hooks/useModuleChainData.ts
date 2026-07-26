import { useState, useEffect, useCallback } from "react";
import { PRESENT_SYSTEMS } from "@/lib/currentTruthControlCenter";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ModuleNode {
  id: string;
  name: string;
  shortName: string;
  description: string;
  truthOwns: string;
  status: "active" | "idle" | "processing" | "error";
  activeCount: number;
  statusCounts: { ok: number; warning: number; error: number };
}

export interface SystemHealthPayload {
  status: string;
  checks: Record<string, { status: string; details: Record<string, unknown> }>;
  generated_at: string;
}

/**
 * Runtime cards follow the canonical present spine.
 * Public health often returns checks:{} → all NEVERIFICAT / idle (honest).
 */
const MODULE_DEFINITIONS: Omit<ModuleNode, "status" | "statusCounts">[] = PRESENT_SYSTEMS.map(
  (s) => ({
    id: s.id,
    name: s.labelRo,
    shortName: s.technicalName.split(" ")[0]?.slice(0, 8) || s.id,
    description: s.purposeRo,
    truthOwns: s.outputRo,
    activeCount: 0,
  })
);

const HEALTH_CHECK_MODULE_MAP: Record<string, string[]> = {
  database: ["order_snapshot", "execution_plan"],
  version: ["intake_v6"],
  seed_pipeline: ["product_aggregate"],
  observation_thresholds: ["execution_reality", "post_job"],
  execution_anchor_order_14: ["order_snapshot", "execution_plan"],
};

function buildModulesFromHealth(health: SystemHealthPayload | null): ModuleNode[] {
  if (!health) {
    return MODULE_DEFINITIONS.map((def) => ({
      ...def,
      status: "idle" as const,
      statusCounts: { ok: 0, warning: 0, error: 0 },
    }));
  }

  const moduleStatuses: Record<string, string[]> = {};
  for (const [checkName, check] of Object.entries(health.checks || {})) {
    const mappedModules = HEALTH_CHECK_MODULE_MAP[checkName] || [];
    for (const modId of mappedModules) {
      if (!moduleStatuses[modId]) moduleStatuses[modId] = [];
      moduleStatuses[modId].push(check.status);
    }
  }

  return MODULE_DEFINITIONS.map((def) => {
    const statuses = moduleStatuses[def.id] || [];
    let moduleStatus: "active" | "processing" | "error" | "idle" = "idle";
    const counts = { ok: 0, warning: 0, error: 0 };

    if (statuses.length === 0) {
      moduleStatus = "idle";
    } else {
      for (const s of statuses) {
        if (s === "ok") counts.ok++;
        else if (s === "warning" || s === "unknown") counts.warning++;
        else if (s === "fail") counts.error++;
      }
      if (counts.error > 0) moduleStatus = "error";
      else if (counts.warning > 0) moduleStatus = "processing";
      else moduleStatus = "active";
    }

    return {
      ...def,
      activeCount: counts.ok + counts.warning + counts.error,
      status: moduleStatus,
      statusCounts: counts,
    };
  });
}

export function useModuleChainData(pollIntervalMs = 30000) {
  const [health, setHealth] = useState<SystemHealthPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/system/health");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SystemHealthPayload = await res.json();
      setHealth(data);
      setIsLive(true);
      setError(null);
    } catch (err) {
      console.warn("[useModuleChainData] Health fetch failed, using defaults:", err);
      setIsLive(false);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchHealth, pollIntervalMs]);

  const modules = buildModulesFromHealth(health);
  const aggregateStatus = health?.status ?? "unknown";
  const generatedAt = health?.generated_at ?? null;

  return {
    modules,
    health,
    aggregateStatus,
    generatedAt,
    loading,
    error,
    isLive,
    refetch: fetchHealth,
  };
}
