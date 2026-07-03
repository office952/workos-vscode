import { useState, useEffect, useCallback } from "react";

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

export interface ContractHandoff {
  from: string;
  to: string;
  payloadSummary: string;
  forbidden: string[];
  lastEvent: string;
  lastEventTime: string;
}

export interface SystemEvent {
  id: string;
  type: string;
  module: string;
  entityId: string;
  message: string;
  timestamp: string;
}

export interface SystemHealthPayload {
  status: string;
  checks: Record<string, { status: string; details: Record<string, unknown> }>;
  generated_at: string;
}

// ---------------------------------------------------------------------------
// Static architectural data (contract handoffs & golden rules)
// These describe the system architecture, not runtime data.
// ---------------------------------------------------------------------------

const CONTRACT_HANDOFFS: ContractHandoff[] = [
  {
    from: "OC",
    to: "WI",
    payloadSummary: "customer_ref, intake_channel, product_family, capabilities",
    forbidden: ["cost", "preț", "configurație finală"],
    lastEvent: "WI_CREATED",
    lastEventTime: "—",
  },
  {
    from: "WI",
    to: "PS",
    payloadSummary: "product_family, dimensions, quantity, constraints",
    forbidden: ["cost_total", "preț_final", "discount"],
    lastEvent: "WI_READY_FOR_QUOTE",
    lastEventTime: "—",
  },
  {
    from: "PS",
    to: "CE",
    payloadSummary: "product_definition, components, materials, processing_requirements",
    forbidden: ["marjă", "discount", "preț client"],
    lastEvent: "PRODUCT_RESOLVED",
    lastEventTime: "—",
  },
  {
    from: "CE",
    to: "QT",
    payloadSummary: "cost_total, cost_breakdown, time_estimate, risk_flags",
    forbidden: ["preț_final_client", "discount", "TVA"],
    lastEvent: "COST_CALCULATED",
    lastEventTime: "—",
  },
  {
    from: "QT",
    to: "OR",
    payloadSummary: "quote_snapshot, product_snapshot, commercial_terms, final_price",
    forbidden: ["recalcul cost", "reconfigurare produs"],
    lastEvent: "QUOTE_ACCEPTED",
    lastEventTime: "—",
  },
  {
    from: "OR",
    to: "WO",
    payloadSummary: "execution_order, product_snapshot, execution_context, deadline",
    forbidden: ["schimbare configurație", "schimbare preț"],
    lastEvent: "ORDER_LOCKED",
    lastEventTime: "—",
  },
  {
    from: "WO",
    to: "TK",
    payloadSummary: "task_batch, operations, dependencies, resources, roles",
    forbidden: ["redefinire order", "redefinire produs", "cost"],
    lastEvent: "WORK_SCHEDULED",
    lastEventTime: "—",
  },
];

// ---------------------------------------------------------------------------
// Module definitions (static structure, dynamic status from health API)
// ---------------------------------------------------------------------------

const MODULE_DEFINITIONS: Omit<ModuleNode, "status" | "statusCounts">[] = [
  { id: "oc", name: "Operational Core", shortName: "OC", description: "Adevărul operațional global", truthOwns: "Resurse reale, capabilități, constrângeri", activeCount: 0 },
  { id: "wi", name: "Work Intake", shortName: "WI", description: "Pregătire cerere", truthOwns: "Cerințe, specificații, intent produs", activeCount: 0 },
  { id: "product_system", name: "ProductSystem", shortName: "PS", description: "Adevăr de produs", truthOwns: "Componente, reguli configurare, structură", activeCount: 0 },
  { id: "cost_engine", name: "CostEngine", shortName: "CE", description: "Adevăr de cost și calcul", truthOwns: "Consumuri, procese, timpi, cost", activeCount: 0 },
  { id: "quotes", name: "Quotes", shortName: "QT", description: "Ofertă comercială", truthOwns: "Preț final, discount, marjă", activeCount: 0 },
  { id: "orders", name: "Orders", shortName: "OR", description: "Snapshot aprobat", truthOwns: "Configurație înghețată, preț, termene", activeCount: 0 },
  { id: "workos", name: "WorkOS", shortName: "WO", description: "Execuție orchestrată", truthOwns: "Planificare, producție, urmărire", activeCount: 0 },
  { id: "tasks", name: "Tasks", shortName: "TK", description: "Unități atomice de lucru", truthOwns: "Cine, ce, în ce ordine, stare", activeCount: 0 },
];

// Map health check names to module IDs for status enrichment
const HEALTH_CHECK_MODULE_MAP: Record<string, string[]> = {
  database: ["oc"],
  version: ["oc"],
  seed_pipeline: ["oc"],
  observation_thresholds: ["workos", "tasks"],
  execution_anchor_order_14: ["orders", "workos"],
};

function mapHealthToModuleStatus(
  checkStatus: string
): "active" | "processing" | "error" | "idle" {
  switch (checkStatus) {
    case "ok":
      return "active";
    case "warning":
    case "unknown":
      return "processing";
    case "fail":
      return "error";
    default:
      return "idle";
  }
}

function buildModulesFromHealth(
  health: SystemHealthPayload | null
): ModuleNode[] {
  if (!health) {
    // Fallback: all modules idle
    return MODULE_DEFINITIONS.map((def) => ({
      ...def,
      status: "idle" as const,
      statusCounts: { ok: 0, warning: 0, error: 0 },
    }));
  }

  // Collect per-module statuses from health checks
  const moduleStatuses: Record<string, string[]> = {};
  for (const [checkName, check] of Object.entries(health.checks)) {
    const mappedModules = HEALTH_CHECK_MODULE_MAP[checkName] || [];
    for (const modId of mappedModules) {
      if (!moduleStatuses[modId]) moduleStatuses[modId] = [];
      moduleStatuses[modId].push(check.status);
    }
  }

  return MODULE_DEFINITIONS.map((def) => {
    const statuses = moduleStatuses[def.id] || [];
    let moduleStatus: "active" | "processing" | "error" | "idle" = "active";
    const counts = { ok: 0, warning: 0, error: 0 };

    if (statuses.length === 0) {
      // No health checks map to this module — mark as active (no issues detected)
      moduleStatus = "active";
      counts.ok = 1;
    } else {
      for (const s of statuses) {
        if (s === "ok") counts.ok++;
        else if (s === "warning" || s === "unknown") counts.warning++;
        else if (s === "fail") counts.error++;
      }
      // Worst status wins
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

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

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
  const contractHandoffs = CONTRACT_HANDOFFS;
  const aggregateStatus = health?.status ?? "unknown";
  const generatedAt = health?.generated_at ?? null;

  return {
    modules,
    contractHandoffs,
    health,
    aggregateStatus,
    generatedAt,
    loading,
    error,
    isLive,
    refetch: fetchHealth,
  };
}