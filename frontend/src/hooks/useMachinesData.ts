import { useState, useEffect, useCallback, useRef } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  machines as mockMachines,
  machineSpecs as mockSpecs,
  maintenanceRecords as mockMaintenance,
  workcenters as mockWorkcenters,
  type Machine,
  type MachineSpec,
  type MaintenanceRecord,
  type Workcenter,
} from "@/lib/mockData";

export type DataSource = "db" | "mock" | "empty" | "error" | "loading";

/** DB row shape from /api/v1/machines */
interface DBMachine {
  id: number;
  machine_code: string;
  name: string;
  description: string | null;
  machine_type: string;
  workcenter_code: string;
  operational_status: string;
  is_available: boolean;
  manufacturer: string | null;
  model: string | null;
  year_acquired: number | null;
  capabilities: string[];
  capacity_metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Map DB operational_status → frontend Machine.status
 * DB uses: "active" | "idle" | "maintenance" | "offline" | "changeover"
 * Frontend uses: "running" | "idle" | "maintenance" | "offline" | "changeover"
 */
function mapStatus(
  dbStatus: string
): "running" | "idle" | "maintenance" | "offline" | "changeover" {
  switch (dbStatus) {
    case "active":
      return "running";
    case "idle":
      return "idle";
    case "maintenance":
      return "maintenance";
    case "offline":
      return "offline";
    case "changeover":
      return "changeover";
    default:
      return "idle";
  }
}

/** Map a DB machine row to the frontend Machine interface */
function mapDBToMachine(db: DBMachine): Machine {
  return {
    id: db.machine_code,
    name: db.name,
    type: db.machine_type,
    workcenterId: db.workcenter_code,
    status: mapStatus(db.operational_status),
    currentJobId: null, // Not tracked in machines registry
    currentOperationCode: null,
    currentOperator: null,
    runtimeMinutes: 0,
    utilizationPct: db.is_available ? 70 : 0, // Default estimate
    queueCount: 0,
    nextJobId: null,
  };
}

/** Build a MachineSpec from DB data (partial — enriches from capacity_metadata when present) */
function mapDBToSpec(db: DBMachine): MachineSpec {
  const meta = db.capacity_metadata ?? {};
  const tableW = Number(meta.table_width_mm ?? meta.max_print_width_mm ?? 0);
  const tableL = Number(meta.table_length_mm ?? meta.max_laminate_width_mm ?? 0);
  const software = typeof meta.software === "string" ? meta.software : null;
  const resolution =
    software != null
      ? software
      : meta.max_cant_width_mm != null
        ? `cant ≤ ${meta.max_cant_width_mm} mm`
        : null;

  return {
    machineId: db.machine_code,
    manufacturer: db.manufacturer || "N/A",
    model: db.model || db.machine_type,
    year: db.year_acquired || 0,
    maxWidth: Number.isFinite(tableW) ? tableW : 0,
    maxHeight: Number.isFinite(tableL) ? tableL : 0,
    maxSpeed: software ? `Software: ${software}` : "N/A",
    resolution,
    powerKW: 0,
    weight: 0,
    location: db.workcenter_code,
    purchaseCost: 0,
    monthlyMaintenanceCost: 0,
    totalJobsCompleted: 0,
    totalHoursRun: 0,
    avgJobDurationMin: 0,
  };
}

/** Derive workcenters from machines list */
function deriveWorkcenters(machines: Machine[]): Workcenter[] {
  const wcMap = new Map<
    string,
    { machineIds: string[]; queueCount: number; activeJobs: number; blockedCount: number }
  >();

  for (const m of machines) {
    if (!wcMap.has(m.workcenterId)) {
      wcMap.set(m.workcenterId, {
        machineIds: [],
        queueCount: 0,
        activeJobs: 0,
        blockedCount: 0,
      });
    }
    const wc = wcMap.get(m.workcenterId)!;
    wc.machineIds.push(m.id);
    wc.queueCount += m.queueCount;
    if (m.status === "running") wc.activeJobs++;
  }

  // Friendly workcenter names
  const wcNames: Record<string, string> = {
    WC_CNC_ROUTING: "CNC Routing",
    WC_PRINT_LARGE_FORMAT: "Print Large Format",
    WC_UV_FLATBED_PRINT: "UV Flatbed Print",
    WC_LAMINATING: "Laminare",
    WC_LASER_CUTTING: "Laser Cutting",
    WC_EDGE_BENDING: "Edge Bending",
    WC_WELDING: "Sudură",
    WC_PAINT_BOOTH: "Vopsire",
    WC_LED_ASSEMBLY: "LED Assembly",
    WC_LIGHTBOX_ASSEMBLY: "Asamblare Lightbox",
    WC_PACKAGING: "Ambalare",
  };

  return Array.from(wcMap.entries()).map(([id, data]) => ({
    id,
    name: wcNames[id] || id.replace(/^WC_/, "").replace(/_/g, " "),
    machineIds: data.machineIds,
    queueCount: data.queueCount,
    activeJobs: data.activeJobs,
    blockedCount: data.blockedCount,
  }));
}

interface MachinesDataState {
  machines: Machine[];
  machineSpecs: MachineSpec[];
  maintenanceRecords: MaintenanceRecord[];
  workcenters: Workcenter[];
  source: DataSource;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useMachinesData(): MachinesDataState {
  const mockEnabled = isMockEnabled();
  const [machines, setMachines] = useState<Machine[]>(mockEnabled ? mockMachines : []);
  const [machineSpecs, setMachineSpecs] = useState<MachineSpec[]>(mockEnabled ? mockSpecs : []);
  const [maintenanceRecords] = useState<MaintenanceRecord[]>(mockEnabled ? mockMaintenance : []);
  const [workcenters, setWorkcenters] = useState<Workcenter[]>(mockEnabled ? mockWorkcenters : []);
  const [source, setSource] = useState<DataSource>(mockEnabled ? "mock" : "loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/machines`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const dbRows: DBMachine[] = await res.json();

      if (!mountedRef.current) return;

      if (dbRows.length > 0) {
        const mappedMachines = dbRows.map(mapDBToMachine);
        const mappedSpecs = dbRows.map(mapDBToSpec);
        const derivedWC = deriveWorkcenters(mappedMachines);

        setMachines(mappedMachines);
        setMachineSpecs(mappedSpecs);
        setWorkcenters(derivedWC);
        setSource("db");
        setError(null);
      } else if (mockEnabled) {
        // Empty DB — use mock data
        setMachines(mockMachines);
        setMachineSpecs(mockSpecs);
        setWorkcenters(mockWorkcenters);
        setSource("mock");
      } else {
        // Empty DB, mock disabled — show empty
        setMachines([]);
        setMachineSpecs([]);
        setWorkcenters([]);
        setSource("empty");
      }
    } catch (err) {
      if (!mountedRef.current) return;
      if (mockEnabled) {
        console.warn("[useMachinesData] API unavailable, using mock data:", err);
        setSource("mock");
      } else {
        console.warn("[useMachinesData] API unavailable, mock disabled:", err);
        setMachines([]);
        setMachineSpecs([]);
        setWorkcenters([]);
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
    machines,
    machineSpecs,
    maintenanceRecords,
    workcenters,
    source,
    loading,
    error,
    refresh: fetchData,
  };
}