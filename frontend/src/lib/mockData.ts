// ============================================================
// WorkOS Mock Data — Full Module Chain + KPI + Production
// ============================================================

// Compile-time guard for demo datasets: production bundles with
// VITE_ENABLE_MOCK_DATA=false must not ship mock/demo entities.
const DEMO_DATA_ENABLED = import.meta.env.DEV || import.meta.env.VITE_ENABLE_MOCK_DATA === "true";

import type { IntakeProductSpec } from "./intakeProductSpec";
import type { QuoteReadinessSnapshot } from "./volumetricQuoteReady";

// --- MODULE CHAIN ---
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

export const moduleChain: ModuleNode[] = [
  {
    id: "oc",
    name: "Operational Core",
    shortName: "OC",
    description: "Adevărul operațional global",
    truthOwns: "Resurse reale, capabilități, constrângeri",
    status: "active",
    activeCount: 42,
    statusCounts: { ok: 38, warning: 3, error: 1 },
  },
  {
    id: "wi",
    name: "Work Intake",
    shortName: "WI",
    description: "Pregătire cerere",
    truthOwns: "Cerințe, specificații, intent produs",
    status: "processing",
    activeCount: 8,
    statusCounts: { ok: 5, warning: 2, error: 1 },
  },
  {
    id: "product_system",
    name: "ProductSystem",
    shortName: "PS",
    description: "Adevăr de produs",
    truthOwns: "Componente, reguli configurare, structură",
    status: "active",
    activeCount: 12,
    statusCounts: { ok: 10, warning: 2, error: 0 },
  },
  {
    id: "cost_engine",
    name: "CostEngine",
    shortName: "CE",
    description: "Adevăr de cost și calcul",
    truthOwns: "Consumuri, procese, timpi, cost",
    status: "active",
    activeCount: 12,
    statusCounts: { ok: 11, warning: 1, error: 0 },
  },
  {
    id: "quotes",
    name: "Quotes",
    shortName: "QT",
    description: "Ofertă comercială",
    truthOwns: "Preț final, discount, marjă",
    status: "processing",
    activeCount: 6,
    statusCounts: { ok: 3, warning: 2, error: 1 },
  },
  {
    id: "orders",
    name: "Orders",
    shortName: "OR",
    description: "Snapshot aprobat",
    truthOwns: "Configurație înghețată, preț, termene",
    status: "active",
    activeCount: 18,
    statusCounts: { ok: 15, warning: 2, error: 1 },
  },
  {
    id: "workos",
    name: "WorkOS",
    shortName: "WO",
    description: "Execuție orchestrată",
    truthOwns: "Planificare, producție, urmărire",
    status: "processing",
    activeCount: 14,
    statusCounts: { ok: 8, warning: 4, error: 2 },
  },
  {
    id: "tasks",
    name: "Tasks",
    shortName: "TK",
    description: "Unități atomice de lucru",
    truthOwns: "Cine, ce, în ce ordine, stare",
    status: "active",
    activeCount: 47,
    statusCounts: { ok: 32, warning: 10, error: 5 },
  },
];

export interface ContractHandoff {
  from: string;
  to: string;
  payloadSummary: string;
  forbidden: string[];
  lastEvent: string;
  lastEventTime: string;
}

export const contractHandoffs: ContractHandoff[] = [
  {
    from: "OC",
    to: "WI",
    payloadSummary: "customer_ref, intake_channel, product_family, capabilities",
    forbidden: ["cost", "preț", "configurație finală"],
    lastEvent: "WI_CREATED",
    lastEventTime: "2 min ago",
  },
  {
    from: "WI",
    to: "PS",
    payloadSummary: "product_family, dimensions, quantity, constraints",
    forbidden: ["cost_total", "preț_final", "discount"],
    lastEvent: "WI_READY_FOR_QUOTE",
    lastEventTime: "5 min ago",
  },
  {
    from: "PS",
    to: "CE",
    payloadSummary: "product_definition, components, materials, processing_requirements",
    forbidden: ["marjă", "discount", "preț client"],
    lastEvent: "PRODUCT_RESOLVED",
    lastEventTime: "8 min ago",
  },
  {
    from: "CE",
    to: "QT",
    payloadSummary: "cost_total, cost_breakdown, time_estimate, risk_flags",
    forbidden: ["preț_final_client", "discount", "TVA"],
    lastEvent: "COST_CALCULATED",
    lastEventTime: "12 min ago",
  },
  {
    from: "QT",
    to: "OR",
    payloadSummary: "quote_snapshot, product_snapshot, commercial_terms, final_price",
    forbidden: ["recalcul cost", "reconfigurare produs"],
    lastEvent: "QUOTE_ACCEPTED",
    lastEventTime: "1h ago",
  },
  {
    from: "OR",
    to: "WO",
    payloadSummary: "execution_order, product_snapshot, execution_context, deadline",
    forbidden: ["schimbare configurație", "schimbare preț"],
    lastEvent: "ORDER_LOCKED",
    lastEventTime: "2h ago",
  },
  {
    from: "WO",
    to: "TK",
    payloadSummary: "task_batch, operations, dependencies, resources, roles",
    forbidden: ["redefinire order", "redefinire produs", "cost"],
    lastEvent: "WORK_SCHEDULED",
    lastEventTime: "30 min ago",
  },
];

// --- MACHINES & WORKCENTERS ---
/** Honesty kind for machine util — mirrors Dashboard ACTUAL/PROXY/GAP. */
export type MachineUtilizationKind = "actual" | "proxy" | "placeholder";

export interface Machine {
  id: string;
  name: string;
  type: string;
  workcenterId: string;
  status: "running" | "idle" | "maintenance" | "offline" | "changeover";
  currentJobId: string | null;
  currentOperationCode: string | null;
  currentOperator: string | null;
  runtimeMinutes: number;
  utilizationPct: number;
  /**
   * When absent on mock demo rows, UI may treat values as proxy.
   * Registry/DB rows without shop-floor load must use "placeholder".
   */
  utilizationKind?: MachineUtilizationKind;
  queueCount: number;
  nextJobId: string | null;
}

export interface Workcenter {
  id: string;
  name: string;
  machineIds: string[];
  queueCount: number;
  activeJobs: number;
  blockedCount: number;
}

export const workcenters: Workcenter[] = [
  { id: "wc_print", name: "Print", machineIds: ["m_epson1", "m_epson2"], queueCount: 5, activeJobs: 2, blockedCount: 0 },
  { id: "wc_laminate", name: "Laminare", machineIds: ["m_lam1"], queueCount: 3, activeJobs: 1, blockedCount: 0 },
  { id: "wc_cut", name: "Cut / Plotter", machineIds: ["m_summa1"], queueCount: 4, activeJobs: 1, blockedCount: 1 },
  { id: "wc_cnc", name: "CNC", machineIds: ["m_cnc1", "m_cnc2"], queueCount: 6, activeJobs: 2, blockedCount: 1 },
  { id: "wc_metal", name: "Metal / Sudură", machineIds: ["m_weld1"], queueCount: 2, activeJobs: 1, blockedCount: 0 },
  { id: "wc_assembly", name: "Asamblare", machineIds: ["m_bench1", "m_bench2"], queueCount: 3, activeJobs: 2, blockedCount: 0 },
  { id: "wc_electric", name: "Electric", machineIds: ["m_elec1"], queueCount: 2, activeJobs: 1, blockedCount: 0 },
  { id: "wc_output", name: "Ambalare / Livrare", machineIds: ["m_pack1"], queueCount: 1, activeJobs: 1, blockedCount: 0 },
];

export const machines: Machine[] = [
  { id: "m_epson1", name: "Epson SC-60600 #1", type: "printer", workcenterId: "wc_print", status: "running", currentJobId: "JOB-0042", currentOperationCode: "PRINT_SOLVENT", currentOperator: "Andrei M.", runtimeMinutes: 45, utilizationPct: 82, queueCount: 3, nextJobId: "JOB-0045" },
  { id: "m_epson2", name: "Epson SC-60600 #2", type: "printer", workcenterId: "wc_print", status: "idle", currentJobId: null, currentOperationCode: null, currentOperator: null, runtimeMinutes: 0, utilizationPct: 45, queueCount: 2, nextJobId: "JOB-0048" },
  { id: "m_lam1", name: "Laminator X-PRO 160", type: "laminator", workcenterId: "wc_laminate", status: "running", currentJobId: "JOB-0039", currentOperationCode: "LAMINATION", currentOperator: "Ion P.", runtimeMinutes: 22, utilizationPct: 71, queueCount: 3, nextJobId: "JOB-0042" },
  { id: "m_summa1", name: "Summa S2 T140", type: "cutter_plotter", workcenterId: "wc_cut", status: "running", currentJobId: "JOB-0038", currentOperationCode: "CONTOUR_CUT", currentOperator: "Vlad R.", runtimeMinutes: 18, utilizationPct: 67, queueCount: 3, nextJobId: "JOB-0041" },
  { id: "m_cnc1", name: "CNC Router 4050x2050", type: "cnc_router", workcenterId: "wc_cnc", status: "running", currentJobId: "JOB-0036", currentOperationCode: "CNC_CUT", currentOperator: "Mihai D.", runtimeMinutes: 55, utilizationPct: 88, queueCount: 4, nextJobId: "JOB-0040" },
  { id: "m_cnc2", name: "CNC Laser 1390", type: "cnc_laser", workcenterId: "wc_cnc", status: "maintenance", currentJobId: null, currentOperationCode: null, currentOperator: null, runtimeMinutes: 0, utilizationPct: 0, queueCount: 2, nextJobId: "JOB-0044" },
  { id: "m_weld1", name: "Stație Sudură TIG", type: "welding", workcenterId: "wc_metal", status: "running", currentJobId: "JOB-0035", currentOperationCode: "WELD_FRAME", currentOperator: "George T.", runtimeMinutes: 32, utilizationPct: 74, queueCount: 2, nextJobId: "JOB-0037" },
  { id: "m_bench1", name: "Banc Montaj #1", type: "assembly_bench", workcenterId: "wc_assembly", status: "running", currentJobId: "JOB-0033", currentOperationCode: "ASSEMBLY_GENERAL", currentOperator: "Cosmin L.", runtimeMinutes: 40, utilizationPct: 79, queueCount: 2, nextJobId: "JOB-0036" },
  { id: "m_bench2", name: "Banc Montaj #2", type: "assembly_bench", workcenterId: "wc_assembly", status: "idle", currentJobId: null, currentOperationCode: null, currentOperator: null, runtimeMinutes: 0, utilizationPct: 35, queueCount: 1, nextJobId: "JOB-0038" },
  { id: "m_elec1", name: "Stație Electrică", type: "electrical", workcenterId: "wc_electric", status: "running", currentJobId: "JOB-0031", currentOperationCode: "LED_INSTALL", currentOperator: "Adrian V.", runtimeMinutes: 25, utilizationPct: 62, queueCount: 2, nextJobId: "JOB-0033" },
  { id: "m_pack1", name: "Zona Ambalare", type: "packing", workcenterId: "wc_output", status: "running", currentJobId: "JOB-0030", currentOperationCode: "PACKAGING", currentOperator: "Elena S.", runtimeMinutes: 15, utilizationPct: 55, queueCount: 1, nextJobId: "JOB-0031" },
];

// --- EXECUTION JOBS ---
export type JobStatus = "pending" | "ready" | "scheduled" | "in_progress" | "blocked" | "partially_completed" | "completed" | "cancelled";

export interface ExecutionJob {
  id: string;
  orderId: string;
  client: string;
  product: string;
  productType: string;
  status: JobStatus;
  priority: "low" | "normal" | "high" | "urgent";
  promisedAt: string;
  productionDeadline: string;
  currentOperation: string;
  currentWorkcenter: string;
  progress: number;
  isLate: boolean;
  isBlocked: boolean;
  riskLevel: "none" | "low" | "medium" | "high";
  riskReason: string | null;
  operationsTotal: number;
  operationsCompleted: number;
}

export const executionJobs: ExecutionJob[] = DEMO_DATA_ENABLED ? [
  { id: "JOB-0030", orderId: "ORD-1120", client: "Mega Image", product: "Panou luminos exterior 3x2m", productType: "panou_bond_casetat", status: "in_progress", priority: "high", promisedAt: "2026-04-08", productionDeadline: "2026-04-07", currentOperation: "PACKAGING", currentWorkcenter: "Ambalare", progress: 92, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 8, operationsCompleted: 7 },
  { id: "JOB-0031", orderId: "ORD-1121", client: "Dedeman", product: "Litere volumetrice LED 'DEDEMAN'", productType: "litere_volumetrice", status: "in_progress", priority: "high", promisedAt: "2026-04-09", productionDeadline: "2026-04-08", currentOperation: "LED_INSTALL", currentWorkcenter: "Electric", progress: 65, isLate: false, isBlocked: false, riskLevel: "low", riskReason: null, operationsTotal: 10, operationsCompleted: 6 },
  { id: "JOB-0033", orderId: "ORD-1123", client: "Kaufland", product: "Casetă luminoasă dublu-față 2.5x1m", productType: "caseta_luminoasa", status: "in_progress", priority: "normal", promisedAt: "2026-04-10", productionDeadline: "2026-04-09", currentOperation: "ASSEMBLY_GENERAL", currentWorkcenter: "Asamblare", progress: 50, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 9, operationsCompleted: 4 },
  { id: "JOB-0035", orderId: "ORD-1125", client: "OMV", product: "Totem preț carburanți 5m", productType: "totem", status: "in_progress", priority: "urgent", promisedAt: "2026-04-08", productionDeadline: "2026-04-07", currentOperation: "WELD_FRAME", currentWorkcenter: "Metal", progress: 40, isLate: false, isBlocked: false, riskLevel: "medium", riskReason: "Termen strâns — sudură în curs", operationsTotal: 12, operationsCompleted: 5 },
  { id: "JOB-0036", orderId: "ORD-1126", client: "Profi", product: "Panou ACP casetat 4x1.5m", productType: "panou_bond_casetat", status: "in_progress", priority: "normal", promisedAt: "2026-04-11", productionDeadline: "2026-04-10", currentOperation: "CNC_CUT", currentWorkcenter: "CNC", progress: 25, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 8, operationsCompleted: 2 },
  { id: "JOB-0038", orderId: "ORD-1128", client: "Lidl", product: "Colant vitrină 12mp", productType: "print_flat", status: "in_progress", priority: "normal", promisedAt: "2026-04-09", productionDeadline: "2026-04-08", currentOperation: "CONTOUR_CUT", currentWorkcenter: "Cut", progress: 55, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 6, operationsCompleted: 3 },
  { id: "JOB-0039", orderId: "ORD-1129", client: "Penny", product: "Banner mesh 6x3m", productType: "print_flat", status: "in_progress", priority: "low", promisedAt: "2026-04-12", productionDeadline: "2026-04-11", currentOperation: "LAMINATION", currentWorkcenter: "Laminare", progress: 35, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 5, operationsCompleted: 2 },
  { id: "JOB-0040", orderId: "ORD-1130", client: "Carrefour", product: "Litere PVC 50mm 'CARREFOUR'", productType: "litere_volumetrice", status: "scheduled", priority: "normal", promisedAt: "2026-04-12", productionDeadline: "2026-04-11", currentOperation: "—", currentWorkcenter: "—", progress: 0, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 7, operationsCompleted: 0 },
  { id: "JOB-0041", orderId: "ORD-1131", client: "Auchan", product: "Panou dibond print 2x1m", productType: "panou_bond_casetat", status: "blocked", priority: "high", promisedAt: "2026-04-09", productionDeadline: "2026-04-08", currentOperation: "CNC_CUT", currentWorkcenter: "CNC", progress: 15, isLate: true, isBlocked: true, riskLevel: "high", riskReason: "Material ACP lipsă — așteptare furnizor", operationsTotal: 7, operationsCompleted: 1 },
  { id: "JOB-0042", orderId: "ORD-1132", client: "Emag", product: "Print autocolant 8mp + laminare", productType: "print_flat", status: "in_progress", priority: "normal", promisedAt: "2026-04-10", productionDeadline: "2026-04-09", currentOperation: "PRINT_SOLVENT", currentWorkcenter: "Print", progress: 20, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 5, operationsCompleted: 1 },
  { id: "JOB-0044", orderId: "ORD-1134", client: "Cora", product: "Litere inox tăiate laser", productType: "litere_volumetrice", status: "blocked", priority: "normal", promisedAt: "2026-04-13", productionDeadline: "2026-04-12", currentOperation: "LASER_CUT", currentWorkcenter: "CNC", progress: 10, isLate: false, isBlocked: true, riskLevel: "medium", riskReason: "CNC Laser în mentenanță", operationsTotal: 8, operationsCompleted: 1 },
  { id: "JOB-0045", orderId: "ORD-1135", client: "Altex", product: "Mesh banner 4x2m", productType: "print_flat", status: "pending", priority: "low", promisedAt: "2026-04-14", productionDeadline: "2026-04-13", currentOperation: "—", currentWorkcenter: "—", progress: 0, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 4, operationsCompleted: 0 },
  { id: "JOB-0048", orderId: "ORD-1138", client: "MOL", product: "Totem preț LED dublu-față", productType: "totem", status: "pending", priority: "high", promisedAt: "2026-04-11", productionDeadline: "2026-04-10", currentOperation: "—", currentWorkcenter: "—", progress: 0, isLate: false, isBlocked: false, riskLevel: "none", riskReason: null, operationsTotal: 14, operationsCompleted: 0 },
] : [];

// --- KPI DATA ---
/** G7: kind clarifies actual vs planned vs derived vs proxy vs placeholder. */
export type KPIMetricKind = "actual" | "planned" | "derived" | "proxy" | "placeholder";

export interface KPIValue {
  code: string;
  label: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "stable";
  trendValue: number;
  status: "good" | "warning" | "critical";
  kind?: KPIMetricKind;
  window?: string;
  explanation?: string;
  gapNote?: string;
}

export const managementKPIs: KPIValue[] = [
  { code: "KPI_ACTIVE_JOBS", label: "Job-uri în pipeline", value: 10, unit: "", trend: "stable", trendValue: 0, status: "good", kind: "actual", window: "open_orders", explanation: "Comenzi created/confirmed/locked/in_execution." },
  { code: "KPI_BLOCKED_JOBS", label: "Blocate (execuție)", value: 2, unit: "", trend: "up", trendValue: 1, status: "critical", kind: "actual", window: "in_execution_with_blocked_tasks", explanation: "Task-uri reality.blocked=true." },
  { code: "KPI_THROUGHPUT", label: "Throughput azi (UTC)", value: 4, unit: "jobs", trend: "down", trendValue: -1, status: "warning", kind: "actual", window: "utc_calendar_today", explanation: "Completed cu updated_at în ziua UTC curentă." },
  { code: "KPI_OTIF", label: "OTIF (proxy)", value: 87, unit: "%", trend: "down", trendValue: -3, status: "warning", kind: "proxy", window: "completed_with_promised_delivery", explanation: "Proxy slab — lipsa date = assumed on-time.", gapNote: "Semnal OTIF durabil indisponibil." },
  { code: "KPI_REWORK_RATE", label: "Rework Rate", value: 0, unit: "%", trend: "stable", trendValue: 0, status: "good", kind: "placeholder", window: "none", explanation: "Placeholder — fără semnal rework în DB.", gapNote: "0 ≠ zero rework." },
  { code: "KPI_MACHINE_UTIL", label: "Load planificat WC", value: 68, unit: "%", trend: "stable", trendValue: 0, status: "good", kind: "derived", window: "lifetime_plan_vs_finished_sessions", explanation: "Media load planificat 0–100 pe workcenter.", gapNote: "Utilaj calendar/shift: date indisponibile." },
  { code: "KPI_LEAD_TIME", label: "Lead time mediu", value: 3.2, unit: "days", trend: "up", trendValue: 0.3, status: "warning", kind: "derived", window: "completed_created_to_updated", explanation: "created_at → updated_at pe completed." },
  { code: "KPI_QUEUE_TIME", label: "Vârstă medie coadă", value: 42, unit: "min", trend: "down", trendValue: -5, status: "good", kind: "derived", window: "open_pipeline_age", explanation: "Vârsta medie a comenzilor în pipeline." },
];

// --- ALERTS ---
export type AlertSeverity = "info" | "warning" | "critical";

export interface ProductionAlert {
  id: string;
  severity: AlertSeverity;
  code: string;
  message: string;
  entityType: string;
  entityId: string;
  jobId: string | null;
  workcenterId: string | null;
  machineId: string | null;
  triggeredAt: string;
  resolvedAt: string | null;
}

export const productionAlerts: ProductionAlert[] = DEMO_DATA_ENABLED ? [
  { id: "ALR-001", severity: "critical", code: "ALRT_MATERIAL_MISSING", message: "Material ACP 3mm lipsă — JOB-0041 blocat", entityType: "job", entityId: "JOB-0041", jobId: "JOB-0041", workcenterId: "wc_cnc", machineId: null, triggeredAt: "2026-04-07T08:15:00", resolvedAt: null },
  { id: "ALR-002", severity: "critical", code: "ALRT_MACHINE_DOWN", message: "CNC Laser 1390 — mentenanță neplanificată", entityType: "machine", entityId: "m_cnc2", jobId: "JOB-0044", workcenterId: "wc_cnc", machineId: "m_cnc2", triggeredAt: "2026-04-07T07:30:00", resolvedAt: null },
  { id: "ALR-003", severity: "warning", code: "ALRT_DEADLINE_RISK", message: "JOB-0035 (OMV Totem) — termen strâns, sudură în curs", entityType: "job", entityId: "JOB-0035", jobId: "JOB-0035", workcenterId: "wc_metal", machineId: null, triggeredAt: "2026-04-07T09:00:00", resolvedAt: null },
  { id: "ALR-004", severity: "warning", code: "ALRT_THROUGHPUT_DROP", message: "Throughput sub media ultimelor 7 zile pe Print", entityType: "workcenter", entityId: "wc_print", jobId: null, workcenterId: "wc_print", machineId: null, triggeredAt: "2026-04-07T10:00:00", resolvedAt: null },
  { id: "ALR-005", severity: "info", code: "ALRT_QUEUE_LONG", message: "Coadă CNC — 6 job-uri în așteptare", entityType: "workcenter", entityId: "wc_cnc", jobId: null, workcenterId: "wc_cnc", machineId: null, triggeredAt: "2026-04-07T09:30:00", resolvedAt: null },
  { id: "ALR-006", severity: "warning", code: "ALRT_DURATION_OVERRUN", message: "JOB-0036 CNC_CUT depășește planul cu 15min", entityType: "operation", entityId: "OP-0036-2", jobId: "JOB-0036", workcenterId: "wc_cnc", machineId: "m_cnc1", triggeredAt: "2026-04-07T10:30:00", resolvedAt: null },
  { id: "ALR-007", severity: "info", code: "ALRT_IDLE_MACHINE", message: "Epson #2 idle — disponibil pentru alocare", entityType: "machine", entityId: "m_epson2", jobId: null, workcenterId: "wc_print", machineId: "m_epson2", triggeredAt: "2026-04-07T10:15:00", resolvedAt: null },
] : [];

// --- OPERATOR TASKS ---
export type TaskStatus = "created" | "assigned" | "in_progress" | "paused" | "blocked" | "done" | "cancelled";

export interface OperatorTask {
  id: string;
  jobId: string;
  client: string;
  product: string;
  operationCode: string;
  operationName: string;
  machineName: string;
  status: TaskStatus;
  assignee: string;
  employeeId?: number | null;
  employeeName?: string | null;
  assignedEmployeeId?: number | null;
  assignedEmployeeName?: string | null;
  blockReason?: string | null;
  plannedDurationMin: number;
  actualDurationMin: number | null;
  startedAt: string | null;
  targetEndAt: string | null;
  instructions: string;
  inputDependencies: string[];
  expectedOutput: string;
  sequenceIndex: number;
  orderCode?: string;
  quoteCode?: string;
  intakeCode?: string;
  productTemplate?: string;
  material?: string;
  finish?: string;
  layerId?: string;
  processId?: string;
}

export const operatorTasks: OperatorTask[] = DEMO_DATA_ENABLED ? [
  { id: "TSK-0201", jobId: "JOB-0042", client: "Emag", product: "Print autocolant 8mp", operationCode: "PRINT_SOLVENT", operationName: "Print Solvent", machineName: "Epson SC-60600 #1", status: "in_progress", assignee: "Andrei M.", plannedDurationMin: 60, actualDurationMin: 45, startedAt: "2026-04-07T09:15:00", targetEndAt: "2026-04-07T10:15:00", instructions: "Print pe autocolant alb lucios, rezoluție 720dpi, profil CMYK standard. Verificare aliniament la 1m.", inputDependencies: ["Fișier RIP validat", "Material încărcat"], expectedOutput: "Material printat 8mp", sequenceIndex: 1 },
  { id: "TSK-0202", jobId: "JOB-0042", client: "Emag", product: "Print autocolant 8mp", operationCode: "LAMINATION", operationName: "Laminare", machineName: "Laminator X-PRO 160", status: "assigned", assignee: "Ion P.", plannedDurationMin: 30, actualDurationMin: null, startedAt: null, targetEndAt: null, instructions: "Laminare mată 80μm. Verificare bule și riduri.", inputDependencies: ["Print complet validat"], expectedOutput: "Material laminat", sequenceIndex: 2 },
  { id: "TSK-0203", jobId: "JOB-0042", client: "Emag", product: "Print autocolant 8mp", operationCode: "CONTOUR_CUT", operationName: "Decupare Contur", machineName: "Summa S2 T140", status: "created", assignee: "Vlad R.", plannedDurationMin: 25, actualDurationMin: null, startedAt: null, targetEndAt: null, instructions: "Decupare pe contur vector. Verificare aliniere optică.", inputDependencies: ["Material laminat"], expectedOutput: "Forme decupate", sequenceIndex: 3 },
  { id: "TSK-0204", jobId: "JOB-0042", client: "Emag", product: "Print autocolant 8mp", operationCode: "VISUAL_CHECK", operationName: "Verificare Vizuală", machineName: "—", status: "created", assignee: "Andrei M.", plannedDurationMin: 10, actualDurationMin: null, startedAt: null, targetEndAt: null, instructions: "Control vizual: culori, decupare, defecte.", inputDependencies: ["Decupare completă"], expectedOutput: "Validare OK / Rework", sequenceIndex: 4 },
  { id: "TSK-0205", jobId: "JOB-0042", client: "Emag", product: "Print autocolant 8mp", operationCode: "PACKAGING", operationName: "Ambalare", machineName: "Zona Ambalare", status: "created", assignee: "Elena S.", plannedDurationMin: 15, actualDurationMin: null, startedAt: null, targetEndAt: null, instructions: "Ambalare tub carton Ø100mm. Etichetare.", inputDependencies: ["Verificare OK"], expectedOutput: "Colet gata livrare", sequenceIndex: 5 },
  { id: "TSK-0210", jobId: "JOB-0036", client: "Profi", product: "Panou ACP casetat 4x1.5m", operationCode: "CNC_CUT", operationName: "Debitare CNC", machineName: "CNC Router 4050x2050", status: "in_progress", assignee: "Mihai D.", plannedDurationMin: 40, actualDurationMin: 55, startedAt: "2026-04-07T08:30:00", targetEndAt: "2026-04-07T09:10:00", instructions: "Debitare ACP 3mm conform DXF. Verificare dimensiuni la fiecare piesă.", inputDependencies: ["Fișier DXF validat", "Material ACP pe masă"], expectedOutput: "Piese debitate conform plan", sequenceIndex: 2 },
  { id: "TSK-0211", jobId: "JOB-0036", client: "Profi", product: "Panou ACP casetat 4x1.5m", operationCode: "V_CUT", operationName: "V-Cut", machineName: "CNC Router 4050x2050", status: "assigned", assignee: "Mihai D.", plannedDurationMin: 30, actualDurationMin: null, startedAt: null, targetEndAt: null, instructions: "V-cut pe liniile de îndoire conform plan tehnic.", inputDependencies: ["Piese debitate"], expectedOutput: "Piese cu linii V-cut", sequenceIndex: 3 },
] : [];

// --- CAPACITY LOAD ---
export interface CapacitySlot {
  workcenterId: string;
  workcenterName: string;
  /** CAP-001: planned_min / shift_available_min % 0–100 (legacy key loadToday). */
  loadToday: number;
  load7d: number;
  load30d: number;
  availableToday: number;
  plannedMinutes?: number;
  actualMinutes?: number;
  overrunMinutes?: number;
  availableMinutes?: number;
  loadKind?: "planned_load" | "calendar_shift_planned_load";
  loadLabel?: string;
  window?: string;
  explanation?: string;
}

/** G7 operational-truth envelope from /dashboard-stats (optional on mock). */
export interface OperationalDataGapBlock {
  domain: string;
  ownerDataNeeded?: boolean;
  notice?: string;
  boundary?: string;
  missingPriceCount?: number;
  missingMaterialCount?: number;
  missingOperationRateCount?: number;
  sampleCodes?: string[];
  valid?: boolean;
  incompleteEmployeeCount?: number;
  warnings?: string[];
  calendarShiftUtilAvailable?: boolean;
  unknown?: boolean;
}

export interface OperationalDataGaps {
  pricing?: OperationalDataGapBlock;
  costIntern?: OperationalDataGapBlock;
  capacity?: OperationalDataGapBlock;
}

export interface CapacityBatch02Truth {
  tasksMissingMinutes?: number;
  tasksWithMinutes?: number;
  maintenanceAvailability?: string;
  materialize?: string;
}

export interface CapacityModelPayload {
  batch?: string;
  materialize?: string;
  availableMinutesMonth?: number;
  workdaysInMonth?: number;
  year?: number;
  month?: number;
  warnings?: string[];
  minutesReadiness?: {
    tasksWithMinutes?: number;
    tasksMissingMinutes?: number;
    labels?: { required?: string; nullWarn?: string };
    materialize?: string;
  };
  machineMappingReadiness?: {
    summary?: {
      machineCount?: number;
      mappedToWc?: number;
      unmappedWc?: number;
      calendarizedMaintenancePresent?: boolean;
    };
    maintenance?: {
      availability?: string;
      notice?: string;
    };
  };
}

export interface OperationalTruth {
  plannedMinutesTotal: number;
  actualMinutesTotal: number;
  overrunMinutesTotal: number;
  throughputWindow: string;
  workcenterLoadKind: string;
  calendarShiftUtilAvailable: boolean;
  notices: string[];
  dataGaps?: OperationalDataGaps;
  boundaries: Record<string, string>;
  capacityBatch02?: CapacityBatch02Truth;
}

export const capacityLoad: CapacitySlot[] = [
  { workcenterId: "wc_print", workcenterName: "Print", loadToday: 78, load7d: 72, load30d: 68, availableToday: 22 },
  { workcenterId: "wc_laminate", workcenterName: "Laminare", loadToday: 71, load7d: 65, load30d: 60, availableToday: 29 },
  { workcenterId: "wc_cut", workcenterName: "Cut / Plotter", loadToday: 67, load7d: 70, load30d: 62, availableToday: 33 },
  { workcenterId: "wc_cnc", workcenterName: "CNC", loadToday: 92, load7d: 85, load30d: 80, availableToday: 8 },
  { workcenterId: "wc_metal", workcenterName: "Metal / Sudură", loadToday: 74, load7d: 68, load30d: 65, availableToday: 26 },
  { workcenterId: "wc_assembly", workcenterName: "Asamblare", loadToday: 60, load7d: 58, load30d: 55, availableToday: 40 },
  { workcenterId: "wc_electric", workcenterName: "Electric", loadToday: 62, load7d: 55, load30d: 50, availableToday: 38 },
  { workcenterId: "wc_output", workcenterName: "Ambalare", loadToday: 55, load7d: 50, load30d: 48, availableToday: 45 },
];

// --- TREND DATA ---
export interface TrendPoint {
  date: string;
  value: number;
}

export const throughputTrend: TrendPoint[] = [
  { date: "Apr 1", value: 6 },
  { date: "Apr 2", value: 5 },
  { date: "Apr 3", value: 7 },
  { date: "Apr 4", value: 4 },
  { date: "Apr 5", value: 3 },
  { date: "Apr 6", value: 5 },
  { date: "Apr 7", value: 4 },
];

export const utilizationTrend: TrendPoint[] = [
  { date: "Apr 1", value: 72 },
  { date: "Apr 2", value: 68 },
  { date: "Apr 3", value: 75 },
  { date: "Apr 4", value: 70 },
  { date: "Apr 5", value: 65 },
  { date: "Apr 6", value: 71 },
  { date: "Apr 7", value: 68 },
];

// --- EVENTS LOG ---
export interface SystemEvent {
  id: string;
  type: string;
  module: string;
  entityId: string;
  message: string;
  timestamp: string;
}

export const recentEvents: SystemEvent[] = [
  { id: "EVT-501", type: "TASK_STARTED", module: "Tasks", entityId: "TSK-0201", message: "Andrei M. a pornit PRINT_SOLVENT pe JOB-0042", timestamp: "09:15" },
  { id: "EVT-502", type: "OPERATION_COMPLETED", module: "WorkOS", entityId: "OP-0039-1", message: "PRINT_SOLVENT completat pe JOB-0039", timestamp: "09:08" },
  { id: "EVT-503", type: "OPERATION_BLOCKED", module: "WorkOS", entityId: "OP-0041-2", message: "CNC_CUT blocat pe JOB-0041 — material lipsă", timestamp: "08:15" },
  { id: "EVT-504", type: "MACHINE_DOWN", module: "OC", entityId: "m_cnc2", message: "CNC Laser 1390 — mentenanță neplanificată", timestamp: "07:30" },
  { id: "EVT-505", type: "JOB_RELEASED", module: "WorkOS", entityId: "JOB-0048", message: "JOB-0048 (MOL Totem) lansat în producție", timestamp: "07:00" },
  { id: "EVT-506", type: "ORDER_LOCKED", module: "Orders", entityId: "ORD-1138", message: "ORD-1138 snapshot înghețat", timestamp: "06:45" },
  { id: "EVT-507", type: "QUOTE_ACCEPTED", module: "Quotes", entityId: "QT-2245", message: "Ofertă QT-2245 acceptată de MOL", timestamp: "06:30" },
  { id: "EVT-508", type: "COST_CALCULATED", module: "CostEngine", entityId: "CALC-889", message: "Cost calculat pentru configurație totem LED", timestamp: "06:15" },
  { id: "EVT-509", type: "PRODUCT_RESOLVED", module: "ProductSystem", entityId: "PROD-445", message: "Configurație totem preț LED dublu-față rezolvată", timestamp: "06:00" },
  { id: "EVT-510", type: "WI_READY_FOR_QUOTE", module: "WI", entityId: "WI-3320", message: "Cerere MOL pregătită pentru ofertare", timestamp: "05:45" },
];

// ============================================================
// WORK INTAKE
// ============================================================
export type IntakeStatus = "new" | "in_review" | "needs_info" | "ready_for_quote" | "blocked" | "cancelled";

export type DeliveryType = "pickup" | "delivery_standard" | "delivery_express" | "delivery_install" | "courier";

export const deliveryTypeLabels: Record<DeliveryType, string> = {
  pickup: "Ridicare din sediu",
  delivery_standard: "Livrare standard",
  delivery_express: "Livrare express",
  delivery_install: "Livrare + Montaj",
  courier: "Curier",
};

export type IdentityType = "temp" | "fiscal";

export interface IntakeIdentity {
  type: IdentityType;
  tempRef: string;
  cui?: string;
  resolvedAt?: string;
}

export interface IntakeRequest {
  id: string;
  client: string;
  contactPerson: string;
  channel: "email" | "phone" | "walk_in" | "web_form";
  productFamily: string;
  description: string;
  dimensions: string;
  quantity: number;
  status: IntakeStatus;
  assignedTo: string;
  createdAt: string;
  updatedAt: string;
  notes: string;
  priority: "low" | "normal" | "high" | "urgent";
  deliveryType: DeliveryType;
  identity: IntakeIdentity;
  productSpec?: IntakeProductSpec | null;
  confirmedTemplateCode?: string | null;
  confirmedTemplateName?: string | null;
  siteAudit?: import("@/lib/intakeSiteAudit").IntakeSiteAuditJson | null;
  dbId?: number;
}

export const intakeRequests: IntakeRequest[] = DEMO_DATA_ENABLED ? [
  { id: "WI-3320", client: "MOL", contactPerson: "Radu Ionescu", channel: "email", productFamily: "Totemuri / Pyloni", description: "Totem preț LED dublu-față, h=5m, iluminat LED, 4 fețe preț", dimensions: "5000x800x400mm", quantity: 1, status: "ready_for_quote", assignedTo: "Maria C.", createdAt: "2026-04-05T09:00:00", updatedAt: "2026-04-07T05:45:00", notes: "Client solicită montaj inclus. Verificat locație.", priority: "high", deliveryType: "delivery_install", identity: { type: "fiscal", tempRef: "TMP-20260405-M1K9", cui: "14399840", resolvedAt: "2026-04-05T10:30:00" } },
  { id: "WI-3321", client: "Vodafone", contactPerson: "Ana Popescu", channel: "email", productFamily: "Casete Luminoase", description: "Casetă luminoasă frontlit cu logo Vodafone, montaj pe fațadă", dimensions: "3000x1000x150mm", quantity: 2, status: "in_review", assignedTo: "Maria C.", createdAt: "2026-04-06T14:30:00", updatedAt: "2026-04-07T08:00:00", notes: "Așteptăm fișier vector logo actualizat.", priority: "normal", deliveryType: "delivery_install", identity: { type: "fiscal", tempRef: "TMP-20260406-V2P3", cui: "15268498", resolvedAt: "2026-04-06T15:00:00" } },
  { id: "WI-3322", client: "Banca Transilvania", contactPerson: "Mihai Stancu", channel: "phone", productFamily: "Litere Volumetrice", description: "Litere volumetrice halo LED 'BT' pentru sediu central", dimensions: "H=600mm per literă", quantity: 1, status: "new", assignedTo: "—", createdAt: "2026-04-07T08:15:00", updatedAt: "2026-04-07T08:15:00", notes: "", priority: "high", deliveryType: "delivery_install", identity: { type: "temp", tempRef: "TMP-20260407-B3T7" } },
  { id: "WI-3323", client: "Decathlon", contactPerson: "Laura Marin", channel: "web_form", productFamily: "Print Flexibil", description: "Banner mesh pentru fațadă magazin, print full color", dimensions: "12000x4000mm", quantity: 1, status: "in_review", assignedTo: "Cristian B.", createdAt: "2026-04-05T11:00:00", updatedAt: "2026-04-06T16:00:00", notes: "Fișier grafic primit. Verificare rezoluție în curs.", priority: "normal", deliveryType: "delivery_standard", identity: { type: "temp", tempRef: "TMP-20260405-D4L2" } },
  { id: "WI-3324", client: "Hornbach", contactPerson: "Stefan Voicu", channel: "email", productFamily: "Semnalistica Interioara", description: "Set complet semnalistică interioară — 45 plăcuțe + directional", dimensions: "Diverse", quantity: 45, status: "needs_info", assignedTo: "Maria C.", createdAt: "2026-04-04T10:00:00", updatedAt: "2026-04-07T09:30:00", notes: "Lipsesc planurile de amplasare. Solicitat de la client.", priority: "normal", deliveryType: "delivery_standard", identity: { type: "fiscal", tempRef: "TMP-20260404-H5V8", cui: "18236490", resolvedAt: "2026-04-04T11:00:00" } },
  { id: "WI-3325", client: "Petrom", contactPerson: "Andrei Dobre", channel: "phone", productFamily: "Totemuri / Pyloni", description: "Totem preț carburanți standard Petrom, h=6m", dimensions: "6000x900x450mm", quantity: 3, status: "in_review", assignedTo: "Cristian B.", createdAt: "2026-04-06T09:00:00", updatedAt: "2026-04-07T07:00:00", notes: "Specificații standard Petrom. Verificare disponibilitate LED.", priority: "urgent", deliveryType: "delivery_install", identity: { type: "fiscal", tempRef: "TMP-20260406-P6D1", cui: "1590082", resolvedAt: "2026-04-06T09:30:00" } },
  { id: "WI-3326", client: "Orange", contactPerson: "Elena Barbu", channel: "email", productFamily: "Colantari", description: "Colantare integrală vitrină magazin Orange — 6 panouri", dimensions: "6x (2000x1500mm)", quantity: 6, status: "ready_for_quote", assignedTo: "Maria C.", createdAt: "2026-04-03T13:00:00", updatedAt: "2026-04-06T14:00:00", notes: "Design aprobat de client. Gata pentru ofertare.", priority: "normal", deliveryType: "delivery_install", identity: { type: "fiscal", tempRef: "TMP-20260403-O7B4", cui: "9010105", resolvedAt: "2026-04-03T14:00:00" } },
  { id: "WI-3327", client: "Farmacia Tei", contactPerson: "Ioana Nistor", channel: "walk_in", productFamily: "Casete Luminoase", description: "Casetă luminoasă dublu-față cu cruce farmacie LED", dimensions: "800x800x200mm", quantity: 1, status: "blocked", assignedTo: "Cristian B.", createdAt: "2026-04-02T15:00:00", updatedAt: "2026-04-06T10:00:00", notes: "Blocat: necesită autorizație primărie pentru montaj.", priority: "low", deliveryType: "pickup", identity: { type: "temp", tempRef: "TMP-20260402-F8N5" } },
  { id: "WI-3328", client: "Mega Image", contactPerson: "Dan Gheorghe", channel: "email", productFamily: "Print Flexibil", description: "Autocolant vitrină promoție Paște — 12 magazine", dimensions: "Diverse per magazin", quantity: 12, status: "new", assignedTo: "—", createdAt: "2026-04-07T10:00:00", updatedAt: "2026-04-07T10:00:00", notes: "Cerere urgentă — termen scurt.", priority: "urgent", deliveryType: "courier", identity: { type: "temp", tempRef: "TMP-20260407-M9G6" } },
  { id: "WI-3329", client: "KFC", contactPerson: "Vlad Enescu", channel: "web_form", productFamily: "Structuri Metalice", description: "Structură metalică pentru panou exterior drive-through", dimensions: "4000x2500x300mm", quantity: 1, status: "cancelled", assignedTo: "Maria C.", createdAt: "2026-04-01T09:00:00", updatedAt: "2026-04-05T11:00:00", notes: "Client a anulat — schimbare furnizor.", priority: "normal", deliveryType: "delivery_express", identity: { type: "fiscal", tempRef: "TMP-20260401-K0E3", cui: "12345678", resolvedAt: "2026-04-01T10:00:00" } },
] : [];

// ============================================================
// QUOTES
// ============================================================
export type QuoteStatus = "draft" | "priced" | "sent" | "viewed" | "negotiating" | "accepted" | "rejected" | "expired";

export interface QuoteLineItem {
  description: string;
  productCode: string;
  quantity: number;
  unitCost: number;
  unitPrice: number;
  total: number;
}

// Sprint #18 — component-aware breakdown shape.
// Mirrors the dict written by CostEngine v2 (`build_execution_layers_from_components`)
// and attached to `QuoteCalculationSnapshot` by QuoteOrchestrator (Sprint #17).
// Frontend ONLY reads it — never recomputes.
export interface ComponentBreakdownMaterial {
  material_code?: string;
  name?: string;
  quantity?: number;
  unit?: string;
  unit_cost?: number;
  line_total?: number;
  path?: string;
}

export interface ComponentBreakdownOperation {
  code?: string;
  name?: string;
  workcenter?: string;
  estimated_minutes?: number;
  hours?: number;
  rate_per_hour?: number;
  line_total?: number;
  path?: string;
}

export interface ComponentBreakdownError {
  kind?: string;
  path?: string;
  detail?: string;
}

export interface ComponentBreakdownWarning {
  kind?: string;
  path?: string;
  detail?: string;
}

export interface ComponentBreakdownItem {
  component_id?: string;
  type?: string;
  name?: string;
  material_cost?: number;
  operation_cost?: number;
  total_component_cost?: number;
  materials_detail?: ComponentBreakdownMaterial[];
  operations_detail?: ComponentBreakdownOperation[];
  errors?: ComponentBreakdownError[];
  warnings?: ComponentBreakdownWarning[];
}

export interface Quote {
  id: string;
  /** Numeric DB primary key — used for backend API calls (e.g. commercial document endpoint). */
  dbId?: number;
  intakeId: string;
  client: string;
  contactPerson: string;
  status: QuoteStatus;
  version: number;
  createdAt: string;
  validUntil: string;
  lineItems: QuoteLineItem[];
  subtotal: number;
  discount: number;
  discountPct: number;
  totalBeforeVAT: number;
  vatPct?: number;
  vat: number;
  grandTotal: number;
  marginPct: number;
  notes: string;
  assignedTo: string;
  // Sprint #18 — optional. Populated only when backend persists
  // component_breakdown into line_items (as a wrapper object). Legacy
  // flat quotes leave this undefined and fall back to the old UI.
  componentBreakdown?: ComponentBreakdownItem[];
  /** Persisted volumetric readiness from quote.line_items wrapper (when present). */
  volumetricReadiness?: QuoteReadinessSnapshot;
  /** Assisted delivery audit trail from line_items wrapper (send-log build). */
  commercialDeliveryLog?: QuoteCommercialDeliveryLogEntry[];
  /** Archived commercial versions from line_items.revision_history[]. */
  revisionHistory?: QuoteRevisionHistoryEntry[];
  /** Priced currency from line_items snapshot (cost_result.currency); RON when unknown. */
  currency?: string;
  /** Flat material nesting summary from line_items wrapper (plexi/Forex/vinyl). */
  flatMaterialNestingSummary?: import("@/components/workos/FlatMaterialNestingSummary").FlatMaterialNestingSummaryData;
}

export interface QuoteCommercialDeliveryLogEntry {
  id?: string;
  event_type?: string;
  quote_code?: string;
  quote_version?: number;
  channel: string;
  sent_at: string;
  recipient?: string;
  note?: string;
  document_ref?: string;
  actor_email?: string;
  old_status?: string;
  new_status?: string;
  assisted_delivery?: boolean;
}

export interface QuoteRevisionHistoryEntry {
  version: number;
  archivedAt: string;
  discountPct?: number;
  grandTotal?: number;
  totalBeforeVat?: number;
}

export const quotes: Quote[] = DEMO_DATA_ENABLED ? [
  {
    id: "QT-2245", intakeId: "WI-3320", client: "MOL", contactPerson: "Radu Ionescu", status: "accepted", version: 2,
    createdAt: "2026-04-05T14:00:00", validUntil: "2026-04-20",
    lineItems: [
      { description: "Totem preț LED dublu-față h=5m", productCode: "TOTEM-ILUMINAT-STD", quantity: 1, unitCost: 4200, unitPrice: 6800, total: 6800 },
      { description: "Sistem LED module + surse", productCode: "ELEC-LED-SISTEM", quantity: 1, unitCost: 850, unitPrice: 1350, total: 1350 },
      { description: "Montaj + transport", productCode: "SERV-MONTAJ-STD", quantity: 1, unitCost: 600, unitPrice: 950, total: 950 },
    ],
    subtotal: 9100, discount: 455, discountPct: 5, totalBeforeVAT: 8645, vat: 1642.55, grandTotal: 10287.55, marginPct: 38,
    notes: "Discount 5% negociat. Termen livrare 10 zile.", assignedTo: "Diana P.",
  },
  {
    id: "QT-2246", intakeId: "WI-3321", client: "Vodafone", contactPerson: "Ana Popescu", status: "draft", version: 1,
    createdAt: "2026-04-07T09:00:00", validUntil: "2026-04-22",
    lineItems: [
      { description: "Casetă luminoasă frontlit 3x1m", productCode: "CL-SIMPLU-STD", quantity: 2, unitCost: 1800, unitPrice: 2900, total: 5800 },
      { description: "Montaj pe fațadă", productCode: "SERV-MONTAJ-STD", quantity: 2, unitCost: 350, unitPrice: 550, total: 1100 },
    ],
    subtotal: 6900, discount: 0, discountPct: 0, totalBeforeVAT: 6900, vat: 1311, grandTotal: 8211, marginPct: 42,
    notes: "Așteptare logo vector pentru finalizare.", assignedTo: "Diana P.",
  },
  {
    id: "QT-2247", intakeId: "WI-3323", client: "Decathlon", contactPerson: "Laura Marin", status: "sent", version: 1,
    createdAt: "2026-04-06T16:30:00", validUntil: "2026-04-21",
    lineItems: [
      { description: "Banner mesh 12x4m print full color", productCode: "PRINT-MESH-STD", quantity: 1, unitCost: 720, unitPrice: 1200, total: 1200 },
      { description: "Montaj cu alpiniști", productCode: "SERV-MONTAJ-STD", quantity: 1, unitCost: 800, unitPrice: 1300, total: 1300 },
    ],
    subtotal: 2500, discount: 0, discountPct: 0, totalBeforeVAT: 2500, vat: 475, grandTotal: 2975, marginPct: 39,
    notes: "Trimis pe email 06.04. Așteptare feedback.", assignedTo: "Diana P.",
  },
  {
    id: "QT-2248", intakeId: "WI-3325", client: "Petrom", contactPerson: "Andrei Dobre", status: "negotiating", version: 3,
    createdAt: "2026-04-06T11:00:00", validUntil: "2026-04-21",
    lineItems: [
      { description: "Totem preț carburanți h=6m", productCode: "TOTEM-ILUMINAT-STD", quantity: 3, unitCost: 5100, unitPrice: 7800, total: 23400 },
      { description: "Sistem LED per totem", productCode: "ELEC-LED-SISTEM", quantity: 3, unitCost: 950, unitPrice: 1500, total: 4500 },
      { description: "Transport + montaj (3 locații)", productCode: "SERV-MONTAJ-STD", quantity: 3, unitCost: 900, unitPrice: 1400, total: 4200 },
    ],
    subtotal: 32100, discount: 3210, discountPct: 10, totalBeforeVAT: 28890, vat: 5489.1, grandTotal: 34379.1, marginPct: 35,
    notes: "Client solicită discount suplimentar 10%. V3 cu reducere aplicată.", assignedTo: "Diana P.",
  },
  {
    id: "QT-2249", intakeId: "WI-3326", client: "Orange", contactPerson: "Elena Barbu", status: "priced", version: 1,
    createdAt: "2026-04-07T08:00:00", validUntil: "2026-04-22",
    lineItems: [
      { description: "Colantare vitrină (6 panouri)", productCode: "COL-VITRINE-STD", quantity: 6, unitCost: 180, unitPrice: 320, total: 1920 },
      { description: "Design grafic adaptare", productCode: "SERV-DESIGN-STD", quantity: 1, unitCost: 200, unitPrice: 350, total: 350 },
      { description: "Aplicare la fața locului", productCode: "SERV-MONTAJ-STD", quantity: 1, unitCost: 250, unitPrice: 400, total: 400 },
    ],
    subtotal: 2670, discount: 0, discountPct: 0, totalBeforeVAT: 2670, vat: 507.3, grandTotal: 3177.3, marginPct: 44,
    notes: "Preț calculat. Pregătit pentru trimitere.", assignedTo: "Diana P.",
  },
  {
    id: "QT-2240", intakeId: "WI-3310", client: "Mega Image", contactPerson: "Dan Gheorghe", status: "accepted", version: 1,
    createdAt: "2026-04-02T10:00:00", validUntil: "2026-04-17",
    lineItems: [
      { description: "Panou luminos exterior 3x2m bond casetat", productCode: "CL-ALU-PLEXI", quantity: 1, unitCost: 2800, unitPrice: 4500, total: 4500 },
      { description: "Sistem LED backlit", productCode: "ELEC-LED-SISTEM", quantity: 1, unitCost: 600, unitPrice: 950, total: 950 },
      { description: "Montaj + transport", productCode: "SERV-MONTAJ-STD", quantity: 1, unitCost: 450, unitPrice: 700, total: 700 },
    ],
    subtotal: 6150, discount: 0, discountPct: 0, totalBeforeVAT: 6150, vat: 1168.5, grandTotal: 7318.5, marginPct: 37,
    notes: "Acceptat. Order creat.", assignedTo: "Diana P.",
  },
  {
    id: "QT-2238", intakeId: "WI-3305", client: "Auchan", contactPerson: "Cristina Radu", status: "rejected", version: 2,
    createdAt: "2026-03-28T09:00:00", validUntil: "2026-04-12",
    lineItems: [
      { description: "Panou dibond print 2x1m", productCode: "CNC-DIBOND-DEBITARE", quantity: 1, unitCost: 450, unitPrice: 750, total: 750 },
      { description: "Print + laminare", productCode: "PRINT-AUTO-LAMINAT", quantity: 1, unitCost: 180, unitPrice: 300, total: 300 },
    ],
    subtotal: 1050, discount: 0, discountPct: 0, totalBeforeVAT: 1050, vat: 199.5, grandTotal: 1249.5, marginPct: 40,
    notes: "Client a ales alt furnizor — preț mai mic.", assignedTo: "Diana P.",
  },
] : [];

// ============================================================
// ORDERS
// ============================================================
export type OrderStatus = "created" | "confirmed" | "locked" | "in_execution" | "completed" | "cancelled";

export interface ReadinessSnapshot {
  source: 'backend' | string;
  snapshot_type: string;
  snapshot_at: string;
  readiness_result?: {
    entity_type: string;
    entity_id: string;
    overall_status: string;
    ready_for_quote: boolean;
    contract_version: string;
    policy: Record<string, unknown>;
    source: string;
  } | null;
  warnings_acknowledged?: boolean;
  warnings_acknowledged_at?: string;
  quote_status?: string;
  requires_production_handoff_build?: boolean;
  production_started?: boolean;
  execution_plan_created?: boolean;
  inventory_mutated?: boolean;
  no_execution_plan_created?: boolean;
}

export interface Order {
  id: string;
  dbId?: number;
  quoteId: string;
  client: string;
  contactPerson: string;
  status: OrderStatus;
  productSummary: string;
  totalAmount: number;
  createdAt: string;
  lockedAt: string | null;
  promisedDelivery: string;
  jobId: string | null;
  paymentStatus: "pending" | "partial" | "paid";
  snapshotVersion: number;
  readinessSnapshot?: ReadinessSnapshot | null;
  commercialCurrencyHandoff?: import("./orderCurrency").OrderCommercialCurrencyHandoff | null;
  baseCurrency?: string;
  notes: string;
}

export const orders: Order[] = DEMO_DATA_ENABLED ? [
  { id: "ORD-1120", quoteId: "QT-2240", client: "Mega Image", contactPerson: "Dan Gheorghe", status: "in_execution", productSummary: "Panou luminos exterior 3x2m", totalAmount: 7318.5, createdAt: "2026-04-03T09:00:00", lockedAt: "2026-04-03T10:00:00", promisedDelivery: "2026-04-08", jobId: "JOB-0030", paymentStatus: "partial", snapshotVersion: 1, notes: "Avans 50% încasat." },
  { id: "ORD-1121", quoteId: "QT-2241", client: "Dedeman", contactPerson: "Marius Ene", status: "in_execution", productSummary: "Litere volumetrice LED 'DEDEMAN'", totalAmount: 12450, createdAt: "2026-04-02T14:00:00", lockedAt: "2026-04-02T15:00:00", promisedDelivery: "2026-04-09", jobId: "JOB-0031", paymentStatus: "paid", snapshotVersion: 1, notes: "Plată integrală primită." },
  { id: "ORD-1123", quoteId: "QT-2242", client: "Kaufland", contactPerson: "Sorin Vlad", status: "in_execution", productSummary: "Casetă luminoasă dublu-față 2.5x1m", totalAmount: 5890, createdAt: "2026-04-03T11:00:00", lockedAt: "2026-04-03T12:00:00", promisedDelivery: "2026-04-10", jobId: "JOB-0033", paymentStatus: "partial", snapshotVersion: 1, notes: "" },
  { id: "ORD-1125", quoteId: "QT-2243", client: "OMV", contactPerson: "Bogdan Preda", status: "in_execution", productSummary: "Totem preț carburanți 5m", totalAmount: 9450, createdAt: "2026-04-01T10:00:00", lockedAt: "2026-04-01T11:00:00", promisedDelivery: "2026-04-08", jobId: "JOB-0035", paymentStatus: "paid", snapshotVersion: 1, notes: "Termen strâns. Prioritate urgentă." },
  { id: "ORD-1126", quoteId: "QT-2244", client: "Profi", contactPerson: "Alina Matei", status: "in_execution", productSummary: "Panou ACP casetat 4x1.5m", totalAmount: 6200, createdAt: "2026-04-04T09:00:00", lockedAt: "2026-04-04T10:00:00", promisedDelivery: "2026-04-11", jobId: "JOB-0036", paymentStatus: "pending", snapshotVersion: 1, notes: "Factură emisă, așteptare plată." },
  { id: "ORD-1131", quoteId: "QT-2238", client: "Auchan", contactPerson: "Cristina Radu", status: "in_execution", productSummary: "Panou dibond print 2x1m", totalAmount: 1249.5, createdAt: "2026-04-04T14:00:00", lockedAt: "2026-04-04T15:00:00", promisedDelivery: "2026-04-09", jobId: "JOB-0041", paymentStatus: "paid", snapshotVersion: 1, notes: "BLOCAT — material lipsă." },
  { id: "ORD-1138", quoteId: "QT-2245", client: "MOL", contactPerson: "Radu Ionescu", status: "locked", productSummary: "Totem preț LED dublu-față", totalAmount: 10287.55, createdAt: "2026-04-07T06:30:00", lockedAt: "2026-04-07T06:45:00", promisedDelivery: "2026-04-11", jobId: "JOB-0048", paymentStatus: "pending", snapshotVersion: 2, notes: "Snapshot înghețat. Gata pentru execuție." },
  { id: "ORD-1140", quoteId: "QT-2250", client: "Lidl", contactPerson: "Florin Neagu", status: "completed", productSummary: "Colant vitrină 12mp", totalAmount: 2150, createdAt: "2026-03-25T09:00:00", lockedAt: "2026-03-25T10:00:00", promisedDelivery: "2026-04-02", jobId: "JOB-0025", paymentStatus: "paid", snapshotVersion: 1, notes: "Livrat și facturat." },
] : [];

// ============================================================
// INVENTORY / OPERATIONAL CORE
// ============================================================
export type StockStatus = "ok" | "low" | "critical" | "out_of_stock" | "untracked";

export interface InventoryMaterial {
  id: string;
  name: string;
  category: string;
  unit: string;
  /** null = stock not tracked (never treat as zero). */
  stockCurrent: number | null;
  stockMin: number;
  stockMax: number;
  stockStatus: StockStatus;
  /** Purchase / acquisition cost; null when missing. */
  unitCost: number | null;
  supplier: string;
  lastRestocked: string;
  consumptionRate: number; // units per day avg
  daysUntilEmpty: number;
  location: string;
  /** Live registry status when known (active / missing_price / …). */
  registryStatus?: string | null;
  /** Inventory UI tab membership derived from live category (not mock IDs). */
  uiTabCategory?: "placi" | "role" | "cerneala" | "altele";
}

export const inventoryMaterials: InventoryMaterial[] = [
  { id: "MAT-001", name: "ACP / Dibond 3mm alb", category: "Plăci", unit: "mp", stockCurrent: 12, stockMin: 20, stockMax: 100, stockStatus: "critical", unitCost: 45, supplier: "Alucobond RO", lastRestocked: "2026-03-28", consumptionRate: 3.5, daysUntilEmpty: 3, location: "Depozit A1" },
  { id: "MAT-002", name: "ACP / Dibond 3mm negru", category: "Plăci", unit: "mp", stockCurrent: 35, stockMin: 20, stockMax: 100, stockStatus: "ok", unitCost: 48, supplier: "Alucobond RO", lastRestocked: "2026-04-02", consumptionRate: 2.0, daysUntilEmpty: 17, location: "Depozit A1" },
  { id: "MAT-003", name: "PVC expandat 5mm alb", category: "Plăci", unit: "mp", stockCurrent: 45, stockMin: 30, stockMax: 150, stockStatus: "ok", unitCost: 18, supplier: "Simona AG", lastRestocked: "2026-04-01", consumptionRate: 4.0, daysUntilEmpty: 11, location: "Depozit A2" },
  { id: "MAT-004", name: "plexiglas 3mm PMMA - opal", category: "Plăci", unit: "mp", stockCurrent: 18, stockMin: 15, stockMax: 80, stockStatus: "low", unitCost: 55, supplier: "Evonik RO", lastRestocked: "2026-03-30", consumptionRate: 2.5, daysUntilEmpty: 7, location: "Depozit A2" },
  { id: "MAT-005", name: "Autocolant alb lucios 1.37m", category: "Rolă", unit: "ml", stockCurrent: 120, stockMin: 50, stockMax: 300, stockStatus: "ok", unitCost: 3.5, supplier: "Oracal", lastRestocked: "2026-04-03", consumptionRate: 12, daysUntilEmpty: 10, location: "Depozit B1" },
  { id: "MAT-006", name: "Laminat mat 80μm", category: "Rolă", unit: "ml", stockCurrent: 85, stockMin: 40, stockMax: 200, stockStatus: "ok", unitCost: 2.8, supplier: "Oracal", lastRestocked: "2026-04-03", consumptionRate: 10, daysUntilEmpty: 8, location: "Depozit B1" },
  { id: "MAT-007", name: "Banner frontlit 440g", category: "Rolă", unit: "ml", stockCurrent: 60, stockMin: 30, stockMax: 150, stockStatus: "ok", unitCost: 4.2, supplier: "Heytex", lastRestocked: "2026-04-01", consumptionRate: 5, daysUntilEmpty: 12, location: "Depozit B2" },
  { id: "MAT-008", name: "Mesh perforat 270g", category: "Rolă", unit: "ml", stockCurrent: 25, stockMin: 20, stockMax: 100, stockStatus: "low", unitCost: 3.8, supplier: "Heytex", lastRestocked: "2026-03-29", consumptionRate: 3, daysUntilEmpty: 8, location: "Depozit B2" },
  { id: "MAT-009", name: "Module LED SMD 3x2W", category: "Electric", unit: "buc", stockCurrent: 450, stockMin: 200, stockMax: 1000, stockStatus: "ok", unitCost: 1.2, supplier: "Seoul Semi", lastRestocked: "2026-04-02", consumptionRate: 30, daysUntilEmpty: 15, location: "Depozit C1" },
  { id: "MAT-010", name: "Surse LED 12V 150W", category: "Electric", unit: "buc", stockCurrent: 15, stockMin: 10, stockMax: 50, stockStatus: "low", unitCost: 35, supplier: "MeanWell", lastRestocked: "2026-03-28", consumptionRate: 2, daysUntilEmpty: 7, location: "Depozit C1" },
  { id: "MAT-011", name: "Profil aluminiu U 40x40", category: "Metal", unit: "ml", stockCurrent: 80, stockMin: 30, stockMax: 200, stockStatus: "ok", unitCost: 8.5, supplier: "Aluminiu SA", lastRestocked: "2026-04-01", consumptionRate: 6, daysUntilEmpty: 13, location: "Depozit D1" },
  { id: "MAT-012", name: "Țeavă oțel 40x40x2mm", category: "Metal", unit: "ml", stockCurrent: 55, stockMin: 25, stockMax: 150, stockStatus: "ok", unitCost: 12, supplier: "ArcelorMittal", lastRestocked: "2026-03-30", consumptionRate: 4, daysUntilEmpty: 13, location: "Depozit D1" },
  { id: "MAT-013", name: "Polistiren expandat 50mm", category: "Plăci", unit: "mp", stockCurrent: 30, stockMin: 15, stockMax: 80, stockStatus: "ok", unitCost: 8, supplier: "Austrotherm", lastRestocked: "2026-04-02", consumptionRate: 2, daysUntilEmpty: 15, location: "Depozit A3" },
  { id: "MAT-014", name: "Cerneală solvent Cyan", category: "Consumabile", unit: "litru", stockCurrent: 2.5, stockMin: 3, stockMax: 15, stockStatus: "critical", unitCost: 85, supplier: "Epson", lastRestocked: "2026-03-25", consumptionRate: 0.5, daysUntilEmpty: 5, location: "Print Room" },
  { id: "MAT-015", name: "Cerneală solvent Magenta", category: "Consumabile", unit: "litru", stockCurrent: 4.0, stockMin: 3, stockMax: 15, stockStatus: "ok", unitCost: 85, supplier: "Epson", lastRestocked: "2026-03-25", consumptionRate: 0.4, daysUntilEmpty: 10, location: "Print Room" },
  { id: "MAT-016", name: "Cerneală solvent Yellow", category: "Consumabile", unit: "litru", stockCurrent: 3.8, stockMin: 3, stockMax: 15, stockStatus: "ok", unitCost: 85, supplier: "Epson", lastRestocked: "2026-03-25", consumptionRate: 0.4, daysUntilEmpty: 9, location: "Print Room" },
  { id: "MAT-017", name: "Cerneală solvent Black", category: "Consumabile", unit: "litru", stockCurrent: 1.8, stockMin: 3, stockMax: 15, stockStatus: "critical", unitCost: 85, supplier: "Epson", lastRestocked: "2026-03-25", consumptionRate: 0.6, daysUntilEmpty: 3, location: "Print Room" },
  { id: "MAT-018", name: "Folie sablată", category: "Rolă", unit: "ml", stockCurrent: 0, stockMin: 10, stockMax: 50, stockStatus: "out_of_stock", unitCost: 6.5, supplier: "Oracal", lastRestocked: "2026-03-15", consumptionRate: 1, daysUntilEmpty: 0, location: "Depozit B1" },
];

export interface Supplier {
  id: string;
  name: string;
  category: string;
  leadTimeDays: number;
  rating: number; // 1-5
  activeOrders: number;
  lastDelivery: string;
}

export const suppliers: Supplier[] = [
  { id: "SUP-01", name: "Alucobond RO", category: "Plăci ACP", leadTimeDays: 5, rating: 4, activeOrders: 1, lastDelivery: "2026-04-02" },
  { id: "SUP-02", name: "Oracal", category: "Folii & Autocolante", leadTimeDays: 3, rating: 5, activeOrders: 2, lastDelivery: "2026-04-03" },
  { id: "SUP-03", name: "Heytex", category: "Banner & Mesh", leadTimeDays: 7, rating: 4, activeOrders: 0, lastDelivery: "2026-04-01" },
  { id: "SUP-04", name: "Epson", category: "Consumabile Print", leadTimeDays: 2, rating: 5, activeOrders: 1, lastDelivery: "2026-03-25" },
  { id: "SUP-05", name: "Seoul Semi", category: "LED & Electric", leadTimeDays: 10, rating: 3, activeOrders: 0, lastDelivery: "2026-04-02" },
  { id: "SUP-06", name: "MeanWell", category: "Surse LED", leadTimeDays: 8, rating: 4, activeOrders: 1, lastDelivery: "2026-03-28" },
  { id: "SUP-07", name: "ArcelorMittal", category: "Metal", leadTimeDays: 4, rating: 4, activeOrders: 0, lastDelivery: "2026-03-30" },
  { id: "SUP-08", name: "Evonik RO", category: "Plexiglas", leadTimeDays: 6, rating: 4, activeOrders: 1, lastDelivery: "2026-03-30" },
];

// ============================================================
// REPORTS — 30-DAY TREND DATA
// ============================================================
export interface DailyMetric {
  date: string;
  throughput: number;
  otif: number;
  reworkRate: number;
  machineUtil: number;
  avgLeadTime: number;
  revenue: number;
}

export const dailyMetrics: DailyMetric[] = [
  { date: "Mar 08", throughput: 5, otif: 92, reworkRate: 2.1, machineUtil: 72, avgLeadTime: 2.8, revenue: 8500 },
  { date: "Mar 09", throughput: 6, otif: 90, reworkRate: 3.0, machineUtil: 75, avgLeadTime: 2.9, revenue: 9200 },
  { date: "Mar 10", throughput: 4, otif: 88, reworkRate: 2.5, machineUtil: 68, avgLeadTime: 3.1, revenue: 7100 },
  { date: "Mar 11", throughput: 7, otif: 93, reworkRate: 1.8, machineUtil: 78, avgLeadTime: 2.7, revenue: 11200 },
  { date: "Mar 12", throughput: 5, otif: 91, reworkRate: 2.2, machineUtil: 71, avgLeadTime: 3.0, revenue: 8800 },
  { date: "Mar 13", throughput: 3, otif: 85, reworkRate: 4.0, machineUtil: 62, avgLeadTime: 3.4, revenue: 5400 },
  { date: "Mar 14", throughput: 2, otif: 80, reworkRate: 3.5, machineUtil: 55, avgLeadTime: 3.6, revenue: 3200 },
  { date: "Mar 15", throughput: 6, otif: 89, reworkRate: 2.8, machineUtil: 74, avgLeadTime: 2.9, revenue: 9800 },
  { date: "Mar 16", throughput: 5, otif: 87, reworkRate: 3.2, machineUtil: 70, avgLeadTime: 3.1, revenue: 8200 },
  { date: "Mar 17", throughput: 7, otif: 94, reworkRate: 1.5, machineUtil: 80, avgLeadTime: 2.5, revenue: 12100 },
  { date: "Mar 18", throughput: 6, otif: 91, reworkRate: 2.0, machineUtil: 76, avgLeadTime: 2.8, revenue: 10500 },
  { date: "Mar 19", throughput: 4, otif: 86, reworkRate: 3.8, machineUtil: 65, avgLeadTime: 3.3, revenue: 6800 },
  { date: "Mar 20", throughput: 5, otif: 88, reworkRate: 2.6, machineUtil: 72, avgLeadTime: 3.0, revenue: 8900 },
  { date: "Mar 21", throughput: 3, otif: 82, reworkRate: 4.5, machineUtil: 58, avgLeadTime: 3.5, revenue: 4800 },
  { date: "Mar 22", throughput: 6, otif: 90, reworkRate: 2.3, machineUtil: 73, avgLeadTime: 2.9, revenue: 9600 },
  { date: "Mar 23", throughput: 7, otif: 93, reworkRate: 1.9, machineUtil: 79, avgLeadTime: 2.6, revenue: 11800 },
  { date: "Mar 24", throughput: 5, otif: 89, reworkRate: 2.7, machineUtil: 71, avgLeadTime: 3.0, revenue: 8400 },
  { date: "Mar 25", throughput: 4, otif: 85, reworkRate: 3.3, machineUtil: 66, avgLeadTime: 3.2, revenue: 7000 },
  { date: "Mar 26", throughput: 6, otif: 91, reworkRate: 2.1, machineUtil: 75, avgLeadTime: 2.8, revenue: 10200 },
  { date: "Mar 27", throughput: 5, otif: 88, reworkRate: 2.9, machineUtil: 70, avgLeadTime: 3.1, revenue: 8600 },
  { date: "Mar 28", throughput: 3, otif: 83, reworkRate: 4.2, machineUtil: 60, avgLeadTime: 3.4, revenue: 5100 },
  { date: "Mar 29", throughput: 2, otif: 78, reworkRate: 5.0, machineUtil: 52, avgLeadTime: 3.8, revenue: 3000 },
  { date: "Mar 30", throughput: 6, otif: 90, reworkRate: 2.4, machineUtil: 74, avgLeadTime: 2.9, revenue: 9900 },
  { date: "Mar 31", throughput: 7, otif: 92, reworkRate: 1.7, machineUtil: 78, avgLeadTime: 2.7, revenue: 11500 },
  { date: "Apr 01", throughput: 6, otif: 91, reworkRate: 2.2, machineUtil: 72, avgLeadTime: 2.9, revenue: 10100 },
  { date: "Apr 02", throughput: 5, otif: 88, reworkRate: 3.0, machineUtil: 68, avgLeadTime: 3.1, revenue: 8300 },
  { date: "Apr 03", throughput: 7, otif: 93, reworkRate: 1.6, machineUtil: 75, avgLeadTime: 2.6, revenue: 11900 },
  { date: "Apr 04", throughput: 4, otif: 86, reworkRate: 3.5, machineUtil: 70, avgLeadTime: 3.2, revenue: 7200 },
  { date: "Apr 05", throughput: 3, otif: 84, reworkRate: 4.0, machineUtil: 65, avgLeadTime: 3.3, revenue: 5500 },
  { date: "Apr 06", throughput: 5, otif: 87, reworkRate: 2.8, machineUtil: 71, avgLeadTime: 3.0, revenue: 8700 },
  { date: "Apr 07", throughput: 4, otif: 87, reworkRate: 4.2, machineUtil: 68, avgLeadTime: 3.2, revenue: 7400 },
];

export interface WorkcenterUtilHeatmap {
  workcenter: string;
  data: number[]; // 7 days Mon-Sun
}

export const wcUtilHeatmap: WorkcenterUtilHeatmap[] = [
  { workcenter: "Print", data: [78, 82, 75, 80, 72, 45, 0] },
  { workcenter: "Laminare", data: [71, 68, 74, 65, 70, 30, 0] },
  { workcenter: "Cut / Plotter", data: [67, 72, 65, 70, 68, 35, 0] },
  { workcenter: "CNC", data: [92, 88, 90, 85, 88, 50, 0] },
  { workcenter: "Metal / Sudură", data: [74, 70, 78, 72, 68, 40, 0] },
  { workcenter: "Asamblare", data: [60, 65, 58, 62, 55, 25, 0] },
  { workcenter: "Electric", data: [62, 58, 65, 60, 55, 20, 0] },
  { workcenter: "Ambalare", data: [55, 50, 58, 52, 48, 15, 0] },
];

// ============================================================
// PRODUCT SYSTEM — PRODUCTION TEMPLATES
// ============================================================
export interface MaterialRequirement {
  materialId: string;
  name: string;
  quantity: number;
  unit: string;
  stockStatus: StockStatus;
  stockCurrent: number;
}

export interface OperationStep {
  code: string;
  name: string;
  workcenter: string;
  estimatedMinutes: number;
  sequence: number;
}

export interface ProductTemplate {
  templateCode: string;
  familyId: string;
  familyName: string;
  description: string;
  components: string[];
  operations: OperationStep[];
  estimatedHours: number;
  requiredMaterials: MaterialRequirement[];
}

export const productTemplates: ProductTemplate[] = [
  {
    templateCode: "TOTEM-ILUMINAT-STD",
    familyId: "totemuri_pyloni",
    familyName: "Totemuri / Pyloni",
    description: "Totem preț iluminat LED, structură metalică cu casete ACP și sistem LED integrat",
    components: ["Structură metalică sudată", "Casete ACP casetate", "Sistem LED module + surse", "Cablaj electric", "Fundație / ancoraj"],
    operations: [
      { code: "CNC_CUT", name: "Debitare CNC", workcenter: "CNC", estimatedMinutes: 60, sequence: 1 },
      { code: "V_CUT", name: "V-Cut ACP", workcenter: "CNC", estimatedMinutes: 45, sequence: 2 },
      { code: "WELD_FRAME", name: "Sudură cadru metalic", workcenter: "Metal / Sudură", estimatedMinutes: 120, sequence: 3 },
      { code: "BEND_ACP", name: "Îndoire ACP", workcenter: "CNC", estimatedMinutes: 40, sequence: 4 },
      { code: "PRINT_SOLVENT", name: "Print grafică", workcenter: "Print", estimatedMinutes: 45, sequence: 5 },
      { code: "LAMINATION", name: "Laminare", workcenter: "Laminare", estimatedMinutes: 20, sequence: 6 },
      { code: "APPLY_VINYL", name: "Aplicare grafică pe casetă", workcenter: "Asamblare", estimatedMinutes: 60, sequence: 7 },
      { code: "LED_INSTALL", name: "Montaj LED + cablaj", workcenter: "Electric", estimatedMinutes: 90, sequence: 8 },
      { code: "ASSEMBLY_GENERAL", name: "Asamblare generală", workcenter: "Asamblare", estimatedMinutes: 120, sequence: 9 },
      { code: "VISUAL_CHECK", name: "Test funcțional + QC", workcenter: "Asamblare", estimatedMinutes: 30, sequence: 10 },
      { code: "PACKAGING", name: "Ambalare", workcenter: "Ambalare", estimatedMinutes: 45, sequence: 11 },
    ],
    estimatedHours: 11.25,
    requiredMaterials: [
      { materialId: "MAT-012", name: "Țeavă oțel 40x40x2mm", quantity: 12, unit: "ml", stockStatus: "ok", stockCurrent: 55 },
      { materialId: "MAT-001", name: "ACP / Dibond 3mm alb", quantity: 6, unit: "mp", stockStatus: "critical", stockCurrent: 12 },
      { materialId: "MAT-009", name: "Module LED SMD 3x2W", quantity: 80, unit: "buc", stockStatus: "ok", stockCurrent: 450 },
      { materialId: "MAT-010", name: "Surse LED 12V 150W", quantity: 4, unit: "buc", stockStatus: "low", stockCurrent: 15 },
      { materialId: "MAT-005", name: "Autocolant alb lucios 1.37m", quantity: 8, unit: "ml", stockStatus: "ok", stockCurrent: 120 },
      { materialId: "MAT-006", name: "Laminat mat 80μm", quantity: 8, unit: "ml", stockStatus: "ok", stockCurrent: 85 },
    ],
  },
  {
    templateCode: "CL-SIMPLU-STD",
    familyId: "casete_luminoase",
    familyName: "Casete Luminoase",
    description: "Casetă luminoasă simplă/dublu-față, cadru aluminiu, față plexiglas opal, iluminare LED",
    components: ["Cadru aluminiu U", "Față plexiglas opal", "Backplate ACP", "Sistem LED module", "Surse LED"],
    operations: [
      { code: "CNC_CUT", name: "Debitare CNC profil + plexiglas", workcenter: "CNC", estimatedMinutes: 40, sequence: 1 },
      { code: "BEND_PROFILE", name: "Îndoire profil aluminiu", workcenter: "CNC", estimatedMinutes: 30, sequence: 2 },
      { code: "PRINT_SOLVENT", name: "Print grafică", workcenter: "Print", estimatedMinutes: 30, sequence: 3 },
      { code: "LAMINATION", name: "Laminare", workcenter: "Laminare", estimatedMinutes: 15, sequence: 4 },
      { code: "LED_INSTALL", name: "Montaj LED + cablaj", workcenter: "Electric", estimatedMinutes: 45, sequence: 5 },
      { code: "ASSEMBLY_GENERAL", name: "Asamblare casetă", workcenter: "Asamblare", estimatedMinutes: 60, sequence: 6 },
      { code: "VISUAL_CHECK", name: "Test iluminare + QC", workcenter: "Asamblare", estimatedMinutes: 15, sequence: 7 },
      { code: "PACKAGING", name: "Ambalare", workcenter: "Ambalare", estimatedMinutes: 20, sequence: 8 },
    ],
    estimatedHours: 4.25,
    requiredMaterials: [
      { materialId: "MAT-011", name: "Profil aluminiu U 40x40", quantity: 8, unit: "ml", stockStatus: "ok", stockCurrent: 80 },
      { materialId: "MAT-004", name: "plexiglas 3mm PMMA - opal", quantity: 3, unit: "mp", stockStatus: "low", stockCurrent: 18 },
      { materialId: "MAT-001", name: "ACP / Dibond 3mm alb", quantity: 3, unit: "mp", stockStatus: "critical", stockCurrent: 12 },
      { materialId: "MAT-009", name: "Module LED SMD 3x2W", quantity: 40, unit: "buc", stockStatus: "ok", stockCurrent: 450 },
      { materialId: "MAT-010", name: "Surse LED 12V 150W", quantity: 2, unit: "buc", stockStatus: "low", stockCurrent: 15 },
    ],
  },
  {
    templateCode: "LIT-VOL-HALO",
    familyId: "litere_volumetrice",
    familyName: "Litere Volumetrice",
    description: "Litere volumetrice cu efect halo LED, față inox/aluminiu, laterale ACP, iluminare spate",
    components: ["Față literă (inox/aluminiu)", "Laterale ACP", "Backplate montaj", "LED halo module", "Distanțiere montaj"],
    operations: [
      { code: "LASER_CUT", name: "Tăiere laser față literă", workcenter: "CNC", estimatedMinutes: 60, sequence: 1 },
      { code: "CNC_CUT", name: "Debitare laterale ACP", workcenter: "CNC", estimatedMinutes: 30, sequence: 2 },
      { code: "V_CUT", name: "V-Cut laterale", workcenter: "CNC", estimatedMinutes: 20, sequence: 3 },
      { code: "BEND_ACP", name: "Îndoire laterale", workcenter: "CNC", estimatedMinutes: 25, sequence: 4 },
      { code: "LED_INSTALL", name: "Montaj LED halo", workcenter: "Electric", estimatedMinutes: 45, sequence: 5 },
      { code: "ASSEMBLY_GENERAL", name: "Asamblare litere", workcenter: "Asamblare", estimatedMinutes: 90, sequence: 6 },
      { code: "VISUAL_CHECK", name: "Test iluminare + QC", workcenter: "Asamblare", estimatedMinutes: 20, sequence: 7 },
      { code: "PACKAGING", name: "Ambalare", workcenter: "Ambalare", estimatedMinutes: 25, sequence: 8 },
    ],
    estimatedHours: 5.25,
    requiredMaterials: [
      { materialId: "MAT-001", name: "ACP / Dibond 3mm alb", quantity: 2, unit: "mp", stockStatus: "critical", stockCurrent: 12 },
      { materialId: "MAT-009", name: "Module LED SMD 3x2W", quantity: 30, unit: "buc", stockStatus: "ok", stockCurrent: 450 },
      { materialId: "MAT-010", name: "Surse LED 12V 150W", quantity: 1, unit: "buc", stockStatus: "low", stockCurrent: 15 },
      { materialId: "MAT-011", name: "Profil aluminiu U 40x40", quantity: 4, unit: "ml", stockStatus: "ok", stockCurrent: 80 },
    ],
  },
  {
    templateCode: "PRINT-MESH-STD",
    familyId: "print_flexibil",
    familyName: "Print Flexibil",
    description: "Print pe mesh/banner, protecție UV integrată în cerneală (fără laminare), confecționare cu ochi metalici",
    components: ["Material print (mesh/banner)", "Print protective UV (cerneală UV-rezistentă)", "Ochi metalici / finisare"],
    operations: [
      { code: "PRINT_SOLVENT", name: "Print solvent UV-protective", workcenter: "Print", estimatedMinutes: 60, sequence: 1 },
      { code: "CONTOUR_CUT", name: "Decupare / confecționare + ochi metalici", workcenter: "Cut / Plotter", estimatedMinutes: 25, sequence: 2 },
      { code: "VISUAL_CHECK", name: "Verificare vizuală", workcenter: "Asamblare", estimatedMinutes: 10, sequence: 3 },
      { code: "PACKAGING", name: "Ambalare", workcenter: "Ambalare", estimatedMinutes: 15, sequence: 4 },
    ],
    estimatedHours: 1.83,
    requiredMaterials: [
      { materialId: "MAT-008", name: "Mesh perforat 270g", quantity: 48, unit: "ml", stockStatus: "low", stockCurrent: 25 },
    ],
  },
  {
    templateCode: "COL-VITRINE-STD",
    familyId: "colantari",
    familyName: "Colantari",
    description: "Colantare vitrină cu autocolant printat, laminare UV, aplicare la fața locului",
    components: ["Autocolant printat", "Laminat protecție UV"],
    operations: [
      { code: "PRINT_SOLVENT", name: "Print autocolant", workcenter: "Print", estimatedMinutes: 45, sequence: 1 },
      { code: "LAMINATION", name: "Laminare", workcenter: "Laminare", estimatedMinutes: 20, sequence: 2 },
      { code: "CONTOUR_CUT", name: "Decupare contur", workcenter: "Cut / Plotter", estimatedMinutes: 15, sequence: 3 },
      { code: "VISUAL_CHECK", name: "Verificare vizuală", workcenter: "Asamblare", estimatedMinutes: 10, sequence: 4 },
      { code: "PACKAGING", name: "Ambalare", workcenter: "Ambalare", estimatedMinutes: 10, sequence: 5 },
    ],
    estimatedHours: 1.67,
    requiredMaterials: [
      { materialId: "MAT-005", name: "Autocolant alb lucios 1.37m", quantity: 18, unit: "ml", stockStatus: "ok", stockCurrent: 120 },
      { materialId: "MAT-006", name: "Laminat mat 80μm", quantity: 18, unit: "ml", stockStatus: "ok", stockCurrent: 85 },
    ],
  },
  {
    templateCode: "SEMN-INT-STD",
    familyId: "semnalistica_interioara",
    familyName: "Semnalistica Interioara",
    description: "Semnalistică interioară — plăcuțe PVC/plexiglas cu print UV sau gravură",
    components: ["Plăci PVC/Plexiglas", "Print UV direct", "Distanțiere montaj"],
    operations: [
      { code: "CNC_CUT", name: "Debitare CNC plăci", workcenter: "CNC", estimatedMinutes: 60, sequence: 1 },
      { code: "PRINT_UV", name: "Print UV direct", workcenter: "Print", estimatedMinutes: 90, sequence: 2 },
      { code: "CONTOUR_CUT", name: "Decupare finală", workcenter: "Cut / Plotter", estimatedMinutes: 30, sequence: 3 },
      { code: "ASSEMBLY_GENERAL", name: "Montaj distanțiere", workcenter: "Asamblare", estimatedMinutes: 45, sequence: 4 },
      { code: "VISUAL_CHECK", name: "Verificare set complet", workcenter: "Asamblare", estimatedMinutes: 20, sequence: 5 },
      { code: "PACKAGING", name: "Ambalare set", workcenter: "Ambalare", estimatedMinutes: 30, sequence: 6 },
    ],
    estimatedHours: 4.58,
    requiredMaterials: [
      { materialId: "MAT-003", name: "PVC expandat 5mm alb", quantity: 8, unit: "mp", stockStatus: "ok", stockCurrent: 45 },
      { materialId: "MAT-004", name: "plexiglas 3mm PMMA - opal", quantity: 4, unit: "mp", stockStatus: "low", stockCurrent: 18 },
    ],
  },
  {
    templateCode: "STRUCT-METAL-STD",
    familyId: "structuri_metalice",
    familyName: "Structuri Metalice",
    description: "Structură metalică sudată pentru suport panou/totem exterior",
    components: ["Țeavă oțel", "Platbandă ancorare", "Grunduire + vopsire"],
    operations: [
      { code: "CNC_CUT", name: "Debitare CNC metal", workcenter: "CNC", estimatedMinutes: 45, sequence: 1 },
      { code: "WELD_FRAME", name: "Sudură cadru", workcenter: "Metal / Sudură", estimatedMinutes: 180, sequence: 2 },
      { code: "PAINT", name: "Grunduire + vopsire", workcenter: "Metal / Sudură", estimatedMinutes: 60, sequence: 3 },
      { code: "VISUAL_CHECK", name: "Verificare dimensiuni + QC", workcenter: "Asamblare", estimatedMinutes: 20, sequence: 4 },
      { code: "PACKAGING", name: "Ambalare", workcenter: "Ambalare", estimatedMinutes: 30, sequence: 5 },
    ],
    estimatedHours: 5.58,
    requiredMaterials: [
      { materialId: "MAT-012", name: "Țeavă oțel 40x40x2mm", quantity: 20, unit: "ml", stockStatus: "ok", stockCurrent: 55 },
    ],
  },
];

// ---------------------------------------------------------------------------
// BUILD 4 — 6 real advertising production templates
// ---------------------------------------------------------------------------
export const build4ProductTemplates: ProductTemplate[] = [
  {
    templateCode: "TPL-BANNER-STANDARD",
    familyId: "print_large_format",
    familyName: "Print format mare",
    description: "Banner publicitar PVC — imprimare ecosolvent/UV format mare, cu opțiuni tiv, capse, sudură. Role: 1100/1350/1600mm.",
    components: ["Substrat banner — imprimare", "Finisare banner — tiv, capse, tăiere"],
    operations: [
      { code: "prepress", name: "Pregătire fișier print", workcenter: "PREPRESS", estimatedMinutes: 30, sequence: 1 },
      { code: "print_large_format", name: "Imprimare format mare", workcenter: "LARGE_FORMAT_PRINT", estimatedMinutes: 0, sequence: 2 },
      { code: "cutting_banner", name: "Tăiere la dimensiune", workcenter: "PANEL_CUTTING", estimatedMinutes: 0, sequence: 3 },
      { code: "tiv_welding", name: "Sudură tiv", workcenter: "WELDING_BANNER", estimatedMinutes: 0, sequence: 4 },
      { code: "capsare", name: "Montaj capse metalice", workcenter: "CAPSARE", estimatedMinutes: 0, sequence: 5 },
      { code: "qc_banner", name: "Control calitate", workcenter: "QC_INSPECTION", estimatedMinutes: 10, sequence: 6 },
      { code: "packaging_banner", name: "Ambalare", workcenter: "PACKAGING", estimatedMinutes: 15, sequence: 7 },
    ],
    estimatedHours: 2.5,
    requiredMaterials: [
      { materialId: "MAT-BANNER-510", name: "Banner PVC 510g", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 100 },
      { materialId: "MAT-INK-ECOSOLVENT", name: "Cerneală ecosolvent", quantity: 0, unit: "set", stockStatus: "ok", stockCurrent: 50 },
      { materialId: "MAT-TIV-BANDA", name: "Bandă tiv", quantity: 0, unit: "ml", stockStatus: "ok", stockCurrent: 200 },
      { materialId: "MAT-CAPSE-METAL", name: "Capse metalice", quantity: 0, unit: "buc", stockStatus: "ok", stockCurrent: 500 },
    ],
  },
  {
    templateCode: "TPL-PLEXI-PLATE",
    familyId: "plexi_cnc",
    familyName: "Plexiglass / Debitare CNC",
    description: "Placă plexiglas — tăiere laser/CNC, finisare muchii, opțional print/vinyl, distanțiere, găurire. Grosimi: 3/5/10mm.",
    components: ["Placă plexiglas — tăiere și prelucrare", "Aplicare print/vinyl pe plexiglas", "Montaj final — distanțiere, ambalare"],
    operations: [
      { code: "prepress_plexi", name: "Pregătire fișier vector", workcenter: "PREPRESS", estimatedMinutes: 20, sequence: 1 },
      { code: "cnc_laser_cut", name: "Tăiere laser/CNC", workcenter: "LASER_CUTTING", estimatedMinutes: 0, sequence: 2 },
      { code: "edge_finish", name: "Finisare muchii", workcenter: "FINISHING", estimatedMinutes: 20, sequence: 3 },
      { code: "drilling", name: "Găurire montaj", workcenter: "CNC_ROUTER", estimatedMinutes: 0, sequence: 4 },
      { code: "print_vinyl_plexi", name: "Print/vinyl aplicare", workcenter: "LARGE_FORMAT_PRINT", estimatedMinutes: 0, sequence: 5 },
      { code: "spacer_assembly", name: "Montaj distanțiere", workcenter: "ASSEMBLY", estimatedMinutes: 0, sequence: 6 },
      { code: "qc_plexi", name: "Control calitate", workcenter: "QC_INSPECTION", estimatedMinutes: 10, sequence: 7 },
      { code: "packaging_plexi", name: "Ambalare", workcenter: "PACKAGING", estimatedMinutes: 15, sequence: 8 },
    ],
    estimatedHours: 3.0,
    requiredMaterials: [
      { materialId: "MAT-PLEXI-TRANSP-3MM", name: "Plexiglas transp. 3mm", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 30 },
      { materialId: "MAT-FOLIE-PROTECTIE", name: "Folie protecție", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 50 },
      { materialId: "MAT-VINYL-TRANSPARENT", name: "Vinyl transparent printabil", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 40 },
      { materialId: "MAT-DISTANTIERE-INOX", name: "Distanțiere inox", quantity: 0, unit: "set", stockStatus: "ok", stockCurrent: 100 },
    ],
  },
  {
    templateCode: "TPL-VINYL-STICKER",
    familyId: "vinyl_stickers",
    familyName: "Autocolant / Sticker",
    description: "Autocolant / sticker — print pe vinyl autoadeziv, laminare UV opțională, tăiere contur, bandă transfer.",
    components: ["Print pe vinyl autoadeziv", "Laminare protecție UV", "Tăiere contur și pregătire", "Control calitate și ambalare"],
    operations: [
      { code: "prepress_vinyl", name: "Pregătire fișier", workcenter: "PREPRESS", estimatedMinutes: 20, sequence: 1 },
      { code: "print_vinyl", name: "Imprimare vinyl", workcenter: "LARGE_FORMAT_PRINT", estimatedMinutes: 0, sequence: 2 },
      { code: "lamination", name: "Laminare", workcenter: "LAMINATION", estimatedMinutes: 0, sequence: 3 },
      { code: "contour_cut", name: "Tăiere contur", workcenter: "CONTOUR_CUTTING", estimatedMinutes: 0, sequence: 4 },
      { code: "weeding", name: "Weeding (îndepărtare surplus)", workcenter: "FINISHING", estimatedMinutes: 30, sequence: 5 },
      { code: "transfer_tape", name: "Aplicare bandă transfer", workcenter: "FINISHING", estimatedMinutes: 0, sequence: 6 },
      { code: "qc_vinyl", name: "Control calitate", workcenter: "QC_INSPECTION", estimatedMinutes: 10, sequence: 7 },
      { code: "packaging_vinyl", name: "Ambalare", workcenter: "PACKAGING", estimatedMinutes: 10, sequence: 8 },
    ],
    estimatedHours: 2.0,
    requiredMaterials: [
      { materialId: "MAT-VINYL-CALANDRAT", name: "Vinyl calandrat", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 80 },
      { materialId: "MAT-INK-ECOSOLVENT", name: "Cerneală ecosolvent", quantity: 0, unit: "set", stockStatus: "ok", stockCurrent: 50 },
      { materialId: "MAT-LAMINARE-MAT", name: "Folie laminare mat", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 60 },
      { materialId: "MAT-TRANSFER-TAPE", name: "Bandă transfer", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 40 },
    ],
  },
  {
    templateCode: "TPL-LIGHTBOX-STANDARD",
    familyId: "casete_luminoase",
    familyName: "Casete luminoase",
    description: "Casetă luminoasă cu LED — cadru aluminiu, față plexiglas/policarbonat, panou spate, module LED, surse alimentare.",
    components: ["Cadru aluminiu casetă", "Față casetă — plexiglas/policarbonat", "Panou spate casetă", "Sistem iluminare LED", "Asamblare finală și QC"],
    operations: [
      { code: "frame_cutting", name: "Debitare profil cadru", workcenter: "PANEL_CUTTING", estimatedMinutes: 0, sequence: 1 },
      { code: "frame_assembly", name: "Asamblare cadru", workcenter: "ASSEMBLY", estimatedMinutes: 60, sequence: 2 },
      { code: "prepress_lightbox", name: "Pregătire grafică", workcenter: "PREPRESS", estimatedMinutes: 30, sequence: 3 },
      { code: "face_cutting", name: "Tăiere față", workcenter: "LASER_CUTTING", estimatedMinutes: 0, sequence: 4 },
      { code: "face_print", name: "Print pe față", workcenter: "LARGE_FORMAT_PRINT", estimatedMinutes: 0, sequence: 5 },
      { code: "back_cutting", name: "Tăiere panou spate", workcenter: "PANEL_CUTTING", estimatedMinutes: 0, sequence: 6 },
      { code: "led_mounting", name: "Montaj module LED", workcenter: "LED_ASSEMBLY", estimatedMinutes: 0, sequence: 7 },
      { code: "electrical_wiring", name: "Cablaj electric", workcenter: "ELECTRICAL_WIRING", estimatedMinutes: 45, sequence: 8 },
      { code: "led_testing", name: "Test iluminare", workcenter: "QC_INSPECTION", estimatedMinutes: 15, sequence: 9 },
      { code: "final_assembly", name: "Asamblare finală", workcenter: "ASSEMBLY", estimatedMinutes: 45, sequence: 10 },
      { code: "qc_lightbox", name: "Control calitate", workcenter: "QC_INSPECTION", estimatedMinutes: 15, sequence: 11 },
      { code: "packaging_lightbox", name: "Ambalare", workcenter: "PACKAGING", estimatedMinutes: 20, sequence: 12 },
    ],
    estimatedHours: 8.0,
    requiredMaterials: [
      { materialId: "MAT-PROFIL-ALU-BOX", name: "Profil aluminiu casetă", quantity: 0, unit: "ml", stockStatus: "ok", stockCurrent: 60 },
      { materialId: "MAT-POLICARBONAT-OPAL", name: "Policarbonat opal", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 25 },
      { materialId: "MAT-VINYL-TRANSPARENT", name: "Vinyl print față", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 40 },
      { materialId: "MAT-PANOU-SPATE-ALU", name: "Panou spate aluminiu", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 30 },
      { materialId: "MAT-LED-MODULE", name: "Modul LED 12V", quantity: 0, unit: "buc", stockStatus: "ok", stockCurrent: 300 },
      { materialId: "MAT-LED-PSU-12V", name: "Surse alimentare LED", quantity: 0, unit: "buc", stockStatus: "ok", stockCurrent: 20 },
    ],
  },
  {
    templateCode: "TPL-VOLUMETRIC-LETTERS",
    familyId: "litere_volumetrice",
    familyName: "Litere volumetrice",
    description: "Litere volumetrice 3D — față plexiglas 3mm PMMA - opal, bordură profil aluminiu, spate Forex 10 mm. LED pe spate. Premontaj opțional ACM/structură.",
    components: ["Față litere — plexiglas 3mm PMMA - opal (CNC/laser)", "Laterale litere — profil aluminiu (bordură)", "Spate litere — Forex 10 mm", "Iluminare LED — montaj pe spate Forex", "Finisare — vopsire, asamblare, QC"],
    operations: [
      { code: "vector_prep", name: "Pregătire vector / font", workcenter: "PREPRESS", estimatedMinutes: 45, sequence: 1 },
      { code: "face_cnc_cut", name: "Tăiere CNC față litere", workcenter: "CNC_ROUTER", estimatedMinutes: 0, sequence: 2 },
      { code: "side_forming", name: "Formare laterale", workcenter: "ASSEMBLY", estimatedMinutes: 0, sequence: 3 },
      { code: "back_cut", name: "Tăiere spate litere", workcenter: "LASER_CUTTING", estimatedMinutes: 0, sequence: 4 },
      { code: "led_install_letters", name: "Montaj LED per literă", workcenter: "LED_ASSEMBLY", estimatedMinutes: 0, sequence: 5 },
      { code: "electrical_letters", name: "Cablaj electric litere", workcenter: "ELECTRICAL_WIRING", estimatedMinutes: 30, sequence: 6 },
      { code: "painting", name: "Vopsire RAL", workcenter: "PAINTING", estimatedMinutes: 0, sequence: 7 },
      { code: "assembly_letters", name: "Asamblare litere", workcenter: "ASSEMBLY", estimatedMinutes: 60, sequence: 8 },
      { code: "qc_letters", name: "Control calitate", workcenter: "QC_INSPECTION", estimatedMinutes: 15, sequence: 9 },
      { code: "packaging_letters", name: "Ambalare + șablon", workcenter: "PACKAGING", estimatedMinutes: 20, sequence: 10 },
    ],
    estimatedHours: 12.0,
    requiredMaterials: [
      { materialId: "MAT-ACP-FATA-LITERE", name: "ACP/aluminiu față", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 15 },
      { materialId: "MAT-PROFIL-LATERAL-LITERE", name: "Volum aluminiu — alege lățimea (30/60/80/100)", quantity: 0, unit: "ml", stockStatus: "ok", stockCurrent: 50 },
      { materialId: "MAT-SPATE-PVC-LITERE", name: "Forex 10 mm spate litere", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 20 },
      { materialId: "MAT-LED-MODULE", name: "Modul LED 12V", quantity: 0, unit: "buc", stockStatus: "ok", stockCurrent: 300 },
      { materialId: "MAT-LED-PSU-12V", name: "Surse LED litere", quantity: 0, unit: "buc", stockStatus: "ok", stockCurrent: 20 },
      { materialId: "MAT-VOPSEA-RAL", name: "Vopsea RAL", quantity: 0, unit: "set", stockStatus: "ok", stockCurrent: 10 },
    ],
  },
  {
    templateCode: "TPL-MESH-EXTERNALIZED",
    familyId: "externalized_print",
    familyName: "Print externalizat",
    description: "Mesh publicitar externalizat — NU se produce intern. Producția este subcontractată la furnizor extern. Intern: pregătire fișier, recepție QC, tiv/capse opțional, ambalare.",
    components: ["Pregătire fișier mesh", "Producție externalizată mesh", "Recepție, QC, tiv/capse, ambalare"],
    operations: [
      { code: "prepress_mesh", name: "Pregătire fișier print", workcenter: "PREPRESS", estimatedMinutes: 30, sequence: 1 },
      { code: "external_production", name: "Subcontractare producție mesh", workcenter: "EXTERNAL_SUBCONTRACT", estimatedMinutes: 0, sequence: 2 },
      { code: "incoming_qc", name: "QC recepție", workcenter: "QC_INSPECTION", estimatedMinutes: 15, sequence: 3 },
      { code: "tiv_mesh", name: "Tiv mesh", workcenter: "WELDING_BANNER", estimatedMinutes: 0, sequence: 4 },
      { code: "capsare_mesh", name: "Capse mesh", workcenter: "CAPSARE", estimatedMinutes: 0, sequence: 5 },
      { code: "packaging_mesh", name: "Ambalare", workcenter: "PACKAGING", estimatedMinutes: 15, sequence: 6 },
    ],
    estimatedHours: 1.5,
    requiredMaterials: [
      { materialId: "MAT-MESH-270", name: "Mesh perforat (furnizor extern)", quantity: 0, unit: "mp", stockStatus: "ok", stockCurrent: 0 },
      { materialId: "MAT-TIV-BANDA", name: "Bandă tiv mesh", quantity: 0, unit: "ml", stockStatus: "ok", stockCurrent: 200 },
      { materialId: "MAT-CAPSE-METAL", name: "Capse mesh", quantity: 0, unit: "buc", stockStatus: "ok", stockCurrent: 500 },
    ],
  },
];

/** All product templates (original + BUILD 4). */
export const allProductTemplates: ProductTemplate[] = [
  ...productTemplates,
  ...build4ProductTemplates,
];

/** Lookup a product template by canonical family_id (registry slug). */
export function getTemplateByFamilyId(familyId: string): ProductTemplate | undefined {
  return allProductTemplates.find((t) => t.familyId === familyId);
}

// ============================================================
// BUILD 4 COMPONENT TYPE MAPPING
// Maps template code + component index to proper ProductComponentType
// ============================================================
const BUILD4_COMPONENT_TYPE_MAP: Record<string, string[]> = {
  "TPL-BANNER-STANDARD": ["PRINT_SUBSTRATE", "FINISAJ"],
  "TPL-PLEXI-PLATE": ["PLEXI_PANEL", "VINYL_APPLICATION", "FINISAJ"],
  "TPL-VINYL-STICKER": ["PRINT_SUBSTRATE", "LAMINARE", "TAIERE_CNC_LASER", "FINISAJ"],
  "TPL-LIGHTBOX-STANDARD": ["FRAME_PROFILE", "DIFUZIE_PLEXI", "ELECTRIC_LED", "FATA_ACP_ROUTATA", "FINISAJ"],
  "TPL-VOLUMETRIC-LETTERS": ["LITERE_3D", "LITERE_3D", "LITERE_3D", "ELECTRIC_LED", "FINISAJ"],
  "TPL-MESH-EXTERNALIZED": ["PRINT_SUBSTRATE", "EXTERNALIZARE", "FINISAJ"],
};

/**
 * Convert mock ProductTemplate[] to ProductTemplateEntity[] format
 * for use as API fallback when backend is unavailable.
 */
export function mockTemplatesToEntities(): Array<{
  id: number;
  template_code: string;
  family_id: string;
  family_name: string;
  description: string;
  components_json: string;
  operations_json: string;
  required_materials_json: string;
  estimated_hours: number;
  base_labor_rate: number;
  base_margin_pct: number;
  active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}> {
  return build4ProductTemplates.map((t, idx) => {
    const typeMap = BUILD4_COMPONENT_TYPE_MAP[t.templateCode] || [];
    const components = t.components.map((name, ci) => ({
      component_id: `comp_${ci}`,
      type: typeMap[ci] || "FINISAJ",
      name,
      operations: t.operations
        .filter((_, oi) => Math.floor(oi / Math.max(1, Math.ceil(t.operations.length / t.components.length))) === ci)
        .map((op) => ({
          code: op.code,
          workcenter: op.workcenter,
          sequence: op.sequence,
          estimatedMinutes: op.estimatedMinutes,
          estimated_minutes: op.estimatedMinutes,
          calculation_type: "static",
          label: op.name,
        })),
      materials: t.requiredMaterials
        .filter((_, mi) => Math.floor(mi / Math.max(1, Math.ceil(t.requiredMaterials.length / t.components.length))) === ci)
        .map((mat) => ({
          materialCode: mat.materialId,
          material_code: mat.materialId,
          unit: mat.unit,
          quantity: mat.quantity,
          calculation_type: "static",
          label: mat.name,
        })),
    }));

    const flatOps = t.operations.map((op) => ({
      code: op.code,
      workcenter: op.workcenter,
      sequence: op.sequence,
      estimatedMinutes: op.estimatedMinutes,
      estimated_minutes: op.estimatedMinutes,
      calculation_type: "static",
      label: op.name,
    }));

    const flatMats = t.requiredMaterials.map((mat) => ({
      materialCode: mat.materialId,
      material_code: mat.materialId,
      unit: mat.unit,
      quantity: mat.quantity,
      calculation_type: "static",
      label: mat.name,
    }));

    return {
      id: 9000 + idx,
      template_code: t.templateCode,
      family_id: t.familyId,
      family_name: t.familyName,
      description: t.description,
      components_json: JSON.stringify(components),
      operations_json: JSON.stringify(flatOps),
      required_materials_json: JSON.stringify(flatMats),
      estimated_hours: t.estimatedHours,
      base_labor_rate: 80,
      base_margin_pct: 30,
      active: true,
      notes: "",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  });
}

// ============================================================
// MOCK PRODUCT FAMILIES — for DEV/MOCK fallback
// ============================================================

/**
 * Returns mock ProductFamily[] matching the Build 4 templates.
 * Used when backend is unavailable in DEV/MOCK mode.
 * Mirrors the canonical families from seed_product_families.py.
 */
export function mockProductFamilies(): Array<{
  id: number;
  family_id: string;
  label: string;
  category: string;
  active: boolean;
  default_template_id: number | null;
  description: string;
  created_at: string;
  updated_at: string;
}> {
  const now = new Date().toISOString();
  const families = [
    { id: 1, family_id: "print_large_format", label: "Print format mare", category: "print", description: "Imprimare pe banner, PVC, folie, backlit" },
    { id: 2, family_id: "casete_luminoase", label: "Casete luminoase", category: "semnalistica", description: "Casete luminoase cu LED, frontlit/backlit" },
    { id: 3, family_id: "litere_volumetrice", label: "Litere volumetrice", category: "semnalistica", description: "Litere 3D volumetrice luminoase sau neluminoase" },
    { id: 4, family_id: "colantari_auto", label: "Colantări auto", category: "colantari", description: "Colantare vehicule, parțiale sau integrale" },
    { id: 5, family_id: "semnalistica_interioara", label: "Semnalistică interioară", category: "semnalistica", description: "Plăcuțe, indicatoare și semnalistică pentru spații interioare" },
    { id: 6, family_id: "semnalistica_exterioara", label: "Semnalistică exterioară", category: "semnalistica", description: "Semnalistică exterioară, totemuri, indicatoare stradale" },
    { id: 7, family_id: "panouri_publicitare", label: "Panouri publicitare", category: "publicitate", description: "Panouri publicitare mari, billboarduri" },
    { id: 8, family_id: "textile_banner", label: "Textile și banner", category: "print", description: "Banner textil, flag-uri, steaguri publicitare" },
    { id: 9, family_id: "cnc_debitare", label: "Debitare CNC", category: "productie", description: "Debitare CNC pentru PVC, acril, aluminiu, lemn" },
    { id: 10, family_id: "servicii_montaj", label: "Servicii montaj", category: "servicii", description: "Servicii de montaj și instalare la beneficiar" },
    { id: 11, family_id: "panouri_acp_iluminate", label: "Panouri ACP Iluminate", category: "semnalistica", description: "Panouri ACP/Dibond iluminate din spate, cu frezare CNC." },
    { id: 12, family_id: "plexi_cnc", label: "Plexiglass / Debitare CNC", category: "productie", description: "Plăci plexiglas — tăiere laser/CNC, finisare muchii, montaj distanțiere." },
    { id: 13, family_id: "vinyl_stickers", label: "Autocolant / Sticker", category: "colantari", description: "Autocolante și stickere — print vinyl, laminare UV, tăiere contur." },
    { id: 14, family_id: "externalized_print", label: "Print externalizat", category: "print", description: "Producție externalizată — mesh, bannere subcontractate la furnizor extern." },
  ];
  return families.map((f) => ({
    ...f,
    active: true,
    default_template_id: null,
    created_at: now,
    updated_at: now,
  }));
}

// ============================================================
// PHYSICAL SHEET INVENTORY — Sheet-Based Stock for Plate Materials
// ============================================================

export type SheetType = "full_sheet" | "remnant";
export type SheetStatus = "available" | "reserved" | "in_use";

export interface PhysicalSheet {
  sheetId: string;
  materialId: string;
  widthMM: number;
  heightMM: number;
  type: SheetType;
  status: SheetStatus;
  location: string;
  /** If remnant, which job produced it */
  sourceJobId?: string;
  /** Label for display */
  label?: string;
}

export interface StandardSheetFormat {
  materialId: string;
  materialName: string;
  formats: { widthMM: number; heightMM: number; label: string }[];
}

/** Standard purchase formats per plate material */
export const standardSheetFormats: StandardSheetFormat[] = [
  {
    materialId: "MAT-001",
    materialName: "ACP / Dibond 3mm alb",
    formats: [
      { widthMM: 3050, heightMM: 1500, label: "3050×1500mm" },
      { widthMM: 4050, heightMM: 1500, label: "4050×1500mm" },
    ],
  },
  {
    materialId: "MAT-002",
    materialName: "ACP / Dibond 3mm negru",
    formats: [
      { widthMM: 3050, heightMM: 1500, label: "3050×1500mm" },
      { widthMM: 4050, heightMM: 1500, label: "4050×1500mm" },
    ],
  },
  {
    materialId: "MAT-003",
    materialName: "PVC expandat 5mm alb",
    formats: [
      { widthMM: 3050, heightMM: 2050, label: "3050×2050mm" },
      { widthMM: 2440, heightMM: 1220, label: "2440×1220mm" },
    ],
  },
  {
    materialId: "MAT-004",
    materialName: "plexiglas 3mm PMMA - opal",
    formats: [
      { widthMM: 3050, heightMM: 2050, label: "3050×2050mm" },
      { widthMM: 2050, heightMM: 1250, label: "2050×1250mm" },
    ],
  },
  {
    materialId: "MAT-013",
    materialName: "Polistiren expandat 50mm",
    formats: [
      { widthMM: 2500, heightMM: 1250, label: "2500×1250mm" },
      { widthMM: 2000, heightMM: 1000, label: "2000×1000mm" },
    ],
  },
];

/** Physical sheets in stock — individual plates with real dimensions */
export const physicalSheets: PhysicalSheet[] = [
  // MAT-001: ACP / Dibond 3mm alb — 12 mp total, but as individual sheets:
  { sheetId: "SHT-001", materialId: "MAT-001", widthMM: 3050, heightMM: 1500, type: "full_sheet", status: "available", location: "Depozit A1" },
  { sheetId: "SHT-002", materialId: "MAT-001", widthMM: 4050, heightMM: 1500, type: "full_sheet", status: "available", location: "Depozit A1" },
  { sheetId: "SHT-003", materialId: "MAT-001", widthMM: 2200, heightMM: 1500, type: "remnant", status: "available", location: "Depozit A1", sourceJobId: "JOB-0036", label: "Rest din JOB-0036" },
  { sheetId: "SHT-004", materialId: "MAT-001", widthMM: 3050, heightMM: 180, type: "remnant", status: "available", location: "Depozit A1", sourceJobId: "JOB-0033", label: "Fâșie din JOB-0033" },
  // MAT-002: ACP / Dibond 3mm negru — 35 mp
  { sheetId: "SHT-010", materialId: "MAT-002", widthMM: 3050, heightMM: 1500, type: "full_sheet", status: "available", location: "Depozit A1" },
  { sheetId: "SHT-011", materialId: "MAT-002", widthMM: 3050, heightMM: 1500, type: "full_sheet", status: "available", location: "Depozit A1" },
  { sheetId: "SHT-012", materialId: "MAT-002", widthMM: 3050, heightMM: 1500, type: "full_sheet", status: "available", location: "Depozit A1" },
  { sheetId: "SHT-013", materialId: "MAT-002", widthMM: 4050, heightMM: 1500, type: "full_sheet", status: "available", location: "Depozit A1" },
  { sheetId: "SHT-014", materialId: "MAT-002", widthMM: 3050, heightMM: 1500, type: "full_sheet", status: "available", location: "Depozit A1" },
  { sheetId: "SHT-015", materialId: "MAT-002", widthMM: 1800, heightMM: 1500, type: "remnant", status: "available", location: "Depozit A1", sourceJobId: "JOB-0030", label: "Rest din JOB-0030" },
  // MAT-003: PVC expandat 5mm alb — 45 mp
  { sheetId: "SHT-020", materialId: "MAT-003", widthMM: 3050, heightMM: 2050, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-021", materialId: "MAT-003", widthMM: 3050, heightMM: 2050, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-022", materialId: "MAT-003", widthMM: 3050, heightMM: 2050, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-023", materialId: "MAT-003", widthMM: 2440, heightMM: 1220, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-024", materialId: "MAT-003", widthMM: 2440, heightMM: 1220, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-025", materialId: "MAT-003", widthMM: 3050, heightMM: 2050, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-026", materialId: "MAT-003", widthMM: 1500, heightMM: 1220, type: "remnant", status: "available", location: "Depozit A2", sourceJobId: "JOB-0031", label: "Rest din JOB-0031" },
  // MAT-004: plexiglas 3mm PMMA - opal — 18 mp
  { sheetId: "SHT-030", materialId: "MAT-004", widthMM: 3050, heightMM: 2050, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-031", materialId: "MAT-004", widthMM: 2050, heightMM: 1250, type: "full_sheet", status: "available", location: "Depozit A2" },
  { sheetId: "SHT-032", materialId: "MAT-004", widthMM: 3050, heightMM: 100, type: "remnant", status: "available", location: "Depozit A2", sourceJobId: "JOB-0033", label: "Fâșie din JOB-0033" },
  { sheetId: "SHT-033", materialId: "MAT-004", widthMM: 3050, heightMM: 100, type: "remnant", status: "available", location: "Depozit A2", sourceJobId: "JOB-0033", label: "Fâșie din JOB-0033" },
  { sheetId: "SHT-034", materialId: "MAT-004", widthMM: 3050, heightMM: 100, type: "remnant", status: "available", location: "Depozit A2", sourceJobId: "JOB-0033", label: "Fâșie din JOB-0033" },
  // MAT-013: Polistiren expandat 50mm — 30 mp
  { sheetId: "SHT-040", materialId: "MAT-013", widthMM: 2500, heightMM: 1250, type: "full_sheet", status: "available", location: "Depozit A3" },
  { sheetId: "SHT-041", materialId: "MAT-013", widthMM: 2500, heightMM: 1250, type: "full_sheet", status: "available", location: "Depozit A3" },
  { sheetId: "SHT-042", materialId: "MAT-013", widthMM: 2500, heightMM: 1250, type: "full_sheet", status: "available", location: "Depozit A3" },
  { sheetId: "SHT-043", materialId: "MAT-013", widthMM: 2500, heightMM: 1250, type: "full_sheet", status: "available", location: "Depozit A3" },
  { sheetId: "SHT-044", materialId: "MAT-013", widthMM: 2500, heightMM: 1250, type: "full_sheet", status: "available", location: "Depozit A3" },
  { sheetId: "SHT-045", materialId: "MAT-013", widthMM: 2000, heightMM: 1000, type: "full_sheet", status: "available", location: "Depozit A3" },
  { sheetId: "SHT-046", materialId: "MAT-013", widthMM: 2000, heightMM: 1000, type: "full_sheet", status: "available", location: "Depozit A3" },
  { sheetId: "SHT-047", materialId: "MAT-013", widthMM: 1200, heightMM: 1000, type: "remnant", status: "available", location: "Depozit A3", sourceJobId: "JOB-0035", label: "Rest din JOB-0035" },
];

/** Materials that are plate-type and should use sheet-based tracking */
const plateMaterialIds = new Set(["MAT-001", "MAT-002", "MAT-003", "MAT-004", "MAT-013"]);

/** Roll-type material IDs — tracked by linear meters on rolls */
const rollMaterialIds = new Set(["MAT-005", "MAT-006", "MAT-007", "MAT-008", "MAT-018"]);

/** Check if a material is roll-type (tracked by linear meters on rolls) */
export function isRollMaterial(materialId: string): boolean {
  return rollMaterialIds.has(materialId);
}

/** Check if a material is plate-type (tracked by sheets, not mp) */
export function isPlateMaterial(materialId: string): boolean {
  return plateMaterialIds.has(materialId);
}

/** Get all available physical sheets for a given material */
export function getAvailableSheets(materialId: string): PhysicalSheet[] {
  return physicalSheets.filter(
    (s) => s.materialId === materialId && s.status === "available"
  );
}

/** Get standard formats for a material */
export function getStandardFormats(materialId: string): StandardSheetFormat | undefined {
  return standardSheetFormats.find((f) => f.materialId === materialId);
}

export type FitCheckResult = "fits" | "limited" | "no_fit";

/**
 * Check if a piece with given minimum dimension (mm) can fit on available sheets.
 * - "fits": piece fits on at least one available sheet (full or remnant)
 * - "limited": piece fits only on full sheets (remnants too small)
 * - "no_fit": no available sheet can accommodate the piece
 */
export function checkSheetFit(
  materialId: string,
  minDimensionMM: number
): { result: FitCheckResult; fitsOnFull: number; fitsOnRemnant: number; totalSheets: number } {
  const sheets = getAvailableSheets(materialId);
  let fitsOnFull = 0;
  let fitsOnRemnant = 0;

  for (const sheet of sheets) {
    // A piece fits if its min dimension is <= the smaller side of the sheet
    const minSide = Math.min(sheet.widthMM, sheet.heightMM);
    if (minSide >= minDimensionMM) {
      if (sheet.type === "full_sheet") fitsOnFull++;
      else fitsOnRemnant++;
    }
  }

  const totalFits = fitsOnFull + fitsOnRemnant;
  let result: FitCheckResult;
  if (totalFits === 0) {
    result = "no_fit";
  } else if (fitsOnRemnant > 0) {
    result = "fits";
  } else {
    result = "limited";
  }

  return { result, fitsOnFull, fitsOnRemnant, totalSheets: sheets.length };
}

// ============================================================
// PERSONAL (Team Members / Operators — Internal HR)
// ============================================================
export type PersonalRole = "operator" | "team_lead" | "technician" | "manager" | "apprentice";
export type PersonalStatus = "active" | "on_leave" | "sick" | "training";

export interface PersonalMember {
  id: string;
  name: string;
  role: PersonalRole;
  status: PersonalStatus;
  workcenterId: string;
  workcenterName: string;
  skills: string[];
  currentTaskId: string | null;
  currentJobId: string | null;
  shiftStart: string;
  shiftEnd: string;
  hoursToday: number;
  tasksCompletedToday: number;
  tasksCompletedWeek: number;
  avgTaskDurationMin: number;
  qualityScore: number; // 0-100
  phone: string;
  hireDate: string;
}

export const personalMembers: PersonalMember[] = [
  { id: "COL-01", name: "Andrei M.", role: "operator", status: "active", workcenterId: "wc_print", workcenterName: "Print", skills: ["Print solvent", "Print eco-solvent", "RIP software", "Color management"], currentTaskId: "TSK-0201", currentJobId: "JOB-0042", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 4.5, tasksCompletedToday: 2, tasksCompletedWeek: 14, avgTaskDurationMin: 52, qualityScore: 94, phone: "0722-111-001", hireDate: "2022-03-15" },
  { id: "COL-02", name: "Ion P.", role: "operator", status: "active", workcenterId: "wc_laminate", workcenterName: "Laminare", skills: ["Laminare caldă", "Laminare rece", "Verificare bule"], currentTaskId: "TSK-0202", currentJobId: "JOB-0039", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 4.0, tasksCompletedToday: 3, tasksCompletedWeek: 18, avgTaskDurationMin: 28, qualityScore: 91, phone: "0722-111-002", hireDate: "2021-06-01" },
  { id: "COL-03", name: "Vlad R.", role: "operator", status: "active", workcenterId: "wc_cut", workcenterName: "Cut / Plotter", skills: ["Decupare contur", "Plotter operare", "Aliniere optică"], currentTaskId: "TSK-0203", currentJobId: "JOB-0038", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 3.5, tasksCompletedToday: 2, tasksCompletedWeek: 12, avgTaskDurationMin: 22, qualityScore: 88, phone: "0722-111-003", hireDate: "2023-01-10" },
  { id: "COL-04", name: "Mihai D.", role: "technician", status: "active", workcenterId: "wc_cnc", workcenterName: "CNC", skills: ["CNC Router", "CNC Laser", "V-Cut", "DXF/CAM", "Calibrare"], currentTaskId: "TSK-0210", currentJobId: "JOB-0036", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 5.0, tasksCompletedToday: 1, tasksCompletedWeek: 8, avgTaskDurationMin: 48, qualityScore: 96, phone: "0722-111-004", hireDate: "2019-09-01" },
  { id: "COL-05", name: "George T.", role: "technician", status: "active", workcenterId: "wc_metal", workcenterName: "Metal / Sudură", skills: ["Sudură TIG", "Sudură MIG", "Debitare metal", "Grunduire"], currentTaskId: null, currentJobId: "JOB-0035", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 4.2, tasksCompletedToday: 1, tasksCompletedWeek: 6, avgTaskDurationMin: 95, qualityScore: 93, phone: "0722-111-005", hireDate: "2020-02-15" },
  { id: "COL-06", name: "Cosmin L.", role: "operator", status: "active", workcenterId: "wc_assembly", workcenterName: "Asamblare", skills: ["Asamblare generală", "Aplicare grafică", "Montaj distanțiere"], currentTaskId: null, currentJobId: "JOB-0033", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 4.8, tasksCompletedToday: 2, tasksCompletedWeek: 11, avgTaskDurationMin: 65, qualityScore: 89, phone: "0722-111-006", hireDate: "2021-11-01" },
  { id: "COL-07", name: "Adrian V.", role: "technician", status: "active", workcenterId: "wc_electric", workcenterName: "Electric", skills: ["Montaj LED", "Cablaj electric", "Test funcțional", "Schemă electrică"], currentTaskId: null, currentJobId: "JOB-0031", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 3.8, tasksCompletedToday: 1, tasksCompletedWeek: 7, avgTaskDurationMin: 55, qualityScore: 95, phone: "0722-111-007", hireDate: "2020-08-01" },
  { id: "COL-08", name: "Elena S.", role: "operator", status: "active", workcenterId: "wc_output", workcenterName: "Ambalare / Livrare", skills: ["Ambalare", "Etichetare", "Pregătire livrare", "Documentație transport"], currentTaskId: "TSK-0205", currentJobId: "JOB-0030", shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 3.2, tasksCompletedToday: 3, tasksCompletedWeek: 20, avgTaskDurationMin: 18, qualityScore: 92, phone: "0722-111-008", hireDate: "2022-05-15" },
  { id: "COL-09", name: "Maria C.", role: "manager", status: "active", workcenterId: "wc_print", workcenterName: "Comercial", skills: ["Work Intake", "Relații clienți", "Ofertare", "Planificare"], currentTaskId: null, currentJobId: null, shiftStart: "08:00", shiftEnd: "17:00", hoursToday: 3.0, tasksCompletedToday: 5, tasksCompletedWeek: 28, avgTaskDurationMin: 15, qualityScore: 97, phone: "0722-111-009", hireDate: "2018-03-01" },
  { id: "COL-10", name: "Cristian B.", role: "team_lead", status: "active", workcenterId: "wc_cnc", workcenterName: "Producție", skills: ["Planificare producție", "CNC", "Coordonare echipă", "QC"], currentTaskId: null, currentJobId: null, shiftStart: "06:00", shiftEnd: "14:00", hoursToday: 5.0, tasksCompletedToday: 0, tasksCompletedWeek: 3, avgTaskDurationMin: 30, qualityScore: 95, phone: "0722-111-010", hireDate: "2017-06-01" },
  { id: "COL-11", name: "Diana P.", role: "manager", status: "active", workcenterId: "wc_print", workcenterName: "Comercial", skills: ["Ofertare", "Negociere", "CRM", "Raportare"], currentTaskId: null, currentJobId: null, shiftStart: "08:00", shiftEnd: "17:00", hoursToday: 4.0, tasksCompletedToday: 4, tasksCompletedWeek: 22, avgTaskDurationMin: 20, qualityScore: 96, phone: "0722-111-011", hireDate: "2019-01-15" },
  { id: "COL-12", name: "Florin N.", role: "apprentice", status: "training", workcenterId: "wc_assembly", workcenterName: "Asamblare", skills: ["Asamblare de bază", "Ambalare"], currentTaskId: null, currentJobId: null, shiftStart: "08:00", shiftEnd: "16:00", hoursToday: 2.5, tasksCompletedToday: 1, tasksCompletedWeek: 5, avgTaskDurationMin: 40, qualityScore: 72, phone: "0722-111-012", hireDate: "2026-03-01" },
  { id: "COL-13", name: "Bogdan P.", role: "operator", status: "on_leave", workcenterId: "wc_cnc", workcenterName: "CNC", skills: ["CNC Router", "Debitare", "V-Cut"], currentTaskId: null, currentJobId: null, shiftStart: "—", shiftEnd: "—", hoursToday: 0, tasksCompletedToday: 0, tasksCompletedWeek: 0, avgTaskDurationMin: 42, qualityScore: 87, phone: "0722-111-013", hireDate: "2021-04-01" },
  { id: "COL-14", name: "Radu S.", role: "operator", status: "sick", workcenterId: "wc_metal", workcenterName: "Metal / Sudură", skills: ["Sudură MIG", "Polizare", "Grunduire"], currentTaskId: null, currentJobId: null, shiftStart: "—", shiftEnd: "—", hoursToday: 0, tasksCompletedToday: 0, tasksCompletedWeek: 2, avgTaskDurationMin: 80, qualityScore: 84, phone: "0722-111-014", hireDate: "2022-09-01" },
];

// ============================================================
// UTILAJE (Equipment / Machines Extended)
// ============================================================
export type MaintenanceType = "preventive" | "corrective" | "calibration";

export interface MaintenanceRecord {
  id: string;
  machineId: string;
  type: MaintenanceType;
  description: string;
  date: string;
  durationHours: number;
  cost: number;
  technician: string;
  nextScheduled: string | null;
}

export const maintenanceRecords: MaintenanceRecord[] = [
  { id: "MNT-001", machineId: "m_epson1", type: "preventive", description: "Curățare capete print + calibrare culori", date: "2026-04-01", durationHours: 2, cost: 150, technician: "Andrei M.", nextScheduled: "2026-05-01" },
  { id: "MNT-002", machineId: "m_epson2", type: "preventive", description: "Curățare capete print + verificare sistem cerneală", date: "2026-03-28", durationHours: 2, cost: 150, technician: "Andrei M.", nextScheduled: "2026-04-28" },
  { id: "MNT-003", machineId: "m_lam1", type: "calibration", description: "Calibrare temperatură role + verificare presiune", date: "2026-03-25", durationHours: 1, cost: 80, technician: "Ion P.", nextScheduled: "2026-04-25" },
  { id: "MNT-004", machineId: "m_summa1", type: "preventive", description: "Înlocuire lamă + calibrare senzor optic", date: "2026-04-03", durationHours: 1.5, cost: 120, technician: "Vlad R.", nextScheduled: "2026-05-03" },
  { id: "MNT-005", machineId: "m_cnc1", type: "preventive", description: "Lubrifiere ghidaje + verificare backlash", date: "2026-03-30", durationHours: 3, cost: 250, technician: "Mihai D.", nextScheduled: "2026-04-30" },
  { id: "MNT-006", machineId: "m_cnc2", type: "corrective", description: "Defect sursă laser — înlocuire tub CO2", date: "2026-04-07", durationHours: 8, cost: 1200, technician: "Service extern", nextScheduled: null },
  { id: "MNT-007", machineId: "m_weld1", type: "preventive", description: "Verificare torță TIG + înlocuire electrod", date: "2026-04-02", durationHours: 1, cost: 60, technician: "George T.", nextScheduled: "2026-05-02" },
  { id: "MNT-008", machineId: "m_cnc1", type: "calibration", description: "Calibrare axe X/Y/Z + verificare precizie", date: "2026-03-15", durationHours: 4, cost: 350, technician: "Service extern", nextScheduled: "2026-06-15" },
  { id: "MNT-009", machineId: "m_epson1", type: "corrective", description: "Înlocuire damper cerneală Cyan", date: "2026-03-20", durationHours: 3, cost: 280, technician: "Service Epson", nextScheduled: null },
  { id: "MNT-010", machineId: "m_elec1", type: "preventive", description: "Verificare scule + calibrare multimetru", date: "2026-04-05", durationHours: 1, cost: 50, technician: "Adrian V.", nextScheduled: "2026-05-05" },
];

export interface MachineSpec {
  machineId: string;
  manufacturer: string;
  model: string;
  year: number;
  maxWidth: number; // mm
  maxHeight: number; // mm
  maxSpeed: string;
  resolution: string | null;
  powerKW: number;
  weight: number; // kg
  location: string;
  purchaseCost: number;
  monthlyMaintenanceCost: number;
  totalJobsCompleted: number;
  totalHoursRun: number;
  avgJobDurationMin: number;
}

export const machineSpecs: MachineSpec[] = [
  { machineId: "m_epson1", manufacturer: "Epson", model: "SC-60600", year: 2023, maxWidth: 1625, maxHeight: 0, maxSpeed: "21.2 m²/h", resolution: "1440 dpi", powerKW: 2.4, weight: 285, location: "Hala Print", purchaseCost: 28000, monthlyMaintenanceCost: 350, totalJobsCompleted: 420, totalHoursRun: 3200, avgJobDurationMin: 48 },
  { machineId: "m_epson2", manufacturer: "Epson", model: "SC-60600", year: 2024, maxWidth: 1625, maxHeight: 0, maxSpeed: "21.2 m²/h", resolution: "1440 dpi", powerKW: 2.4, weight: 285, location: "Hala Print", purchaseCost: 28000, monthlyMaintenanceCost: 300, totalJobsCompleted: 180, totalHoursRun: 1400, avgJobDurationMin: 45 },
  { machineId: "m_lam1", manufacturer: "GMP", model: "X-PRO 160", year: 2022, maxWidth: 1600, maxHeight: 0, maxSpeed: "8 m/min", resolution: null, powerKW: 1.8, weight: 120, location: "Hala Print", purchaseCost: 8500, monthlyMaintenanceCost: 100, totalJobsCompleted: 650, totalHoursRun: 2100, avgJobDurationMin: 22 },
  { machineId: "m_summa1", manufacturer: "Summa", model: "S2 T140", year: 2023, maxWidth: 1400, maxHeight: 0, maxSpeed: "1130 mm/s", resolution: null, powerKW: 0.3, weight: 75, location: "Hala Cut", purchaseCost: 12000, monthlyMaintenanceCost: 80, totalJobsCompleted: 520, totalHoursRun: 1800, avgJobDurationMin: 20 },
  { machineId: "m_cnc1", manufacturer: "Custom", model: "Router 4050x2050", year: 2021, maxWidth: 4050, maxHeight: 2050, maxSpeed: "25 m/min", resolution: null, powerKW: 7.5, weight: 1800, location: "Hala CNC", purchaseCost: 45000, monthlyMaintenanceCost: 500, totalJobsCompleted: 380, totalHoursRun: 4200, avgJobDurationMin: 55 },
  { machineId: "m_cnc2", manufacturer: "Custom", model: "Laser 1390", year: 2022, maxWidth: 1300, maxHeight: 900, maxSpeed: "400 mm/s", resolution: null, powerKW: 4.5, weight: 650, location: "Hala CNC", purchaseCost: 22000, monthlyMaintenanceCost: 400, totalJobsCompleted: 210, totalHoursRun: 1600, avgJobDurationMin: 40 },
  { machineId: "m_weld1", manufacturer: "Lincoln", model: "Invertec V310-T", year: 2020, maxWidth: 0, maxHeight: 0, maxSpeed: "—", resolution: null, powerKW: 11.2, weight: 45, location: "Hala Metal", purchaseCost: 5500, monthlyMaintenanceCost: 80, totalJobsCompleted: 290, totalHoursRun: 3800, avgJobDurationMin: 90 },
  { machineId: "m_bench1", manufacturer: "—", model: "Banc Montaj Custom", year: 2020, maxWidth: 3000, maxHeight: 1500, maxSpeed: "—", resolution: null, powerKW: 0.5, weight: 200, location: "Hala Asamblare", purchaseCost: 2000, monthlyMaintenanceCost: 30, totalJobsCompleted: 450, totalHoursRun: 5200, avgJobDurationMin: 70 },
  { machineId: "m_bench2", manufacturer: "—", model: "Banc Montaj Custom", year: 2021, maxWidth: 3000, maxHeight: 1500, maxSpeed: "—", resolution: null, powerKW: 0.5, weight: 200, location: "Hala Asamblare", purchaseCost: 2000, monthlyMaintenanceCost: 30, totalJobsCompleted: 320, totalHoursRun: 3600, avgJobDurationMin: 65 },
  { machineId: "m_elec1", manufacturer: "—", model: "Stație Electrică Custom", year: 2021, maxWidth: 0, maxHeight: 0, maxSpeed: "—", resolution: null, powerKW: 1.0, weight: 80, location: "Hala Electric", purchaseCost: 3000, monthlyMaintenanceCost: 50, totalJobsCompleted: 280, totalHoursRun: 2800, avgJobDurationMin: 55 },
  { machineId: "m_pack1", manufacturer: "—", model: "Zona Ambalare", year: 2020, maxWidth: 0, maxHeight: 0, maxSpeed: "—", resolution: null, powerKW: 0.2, weight: 50, location: "Zona Livrare", purchaseCost: 1000, monthlyMaintenanceCost: 20, totalJobsCompleted: 680, totalHoursRun: 2000, avgJobDurationMin: 18 },
];

// ============================================================
// SETĂRI SOCIETATE (Company Settings)
// ============================================================
export interface CompanySettings {
  name: string;
  cui: string;
  regCom: string;
  address: string;
  city: string;
  county: string;
  postalCode: string;
  phone: string;
  email: string;
  website: string;
  bankName: string;
  iban: string;
  vatPayer: boolean;
  logoUrl: string;
  adminContact: string;
}

export const companySettings: CompanySettings = {
  name: "SignTech Advertising SRL",
  cui: "RO12345678",
  regCom: "J40/1234/2015",
  address: "Str. Industriilor Nr. 45, Sector 3",
  city: "București",
  county: "București",
  postalCode: "032266",
  phone: "021-300-4500",
  email: "office@signtech.ro",
  website: "www.signtech.ro",
  bankName: "Banca Transilvania",
  iban: "RO49 BTRL 0130 1205 A123 4567",
  vatPayer: true,
  logoUrl: "",
  adminContact: "Adrian Popescu — Administrator",
};

// ============================================================
// PLĂȚI REPETITIVE (Recurring Payments)
// ============================================================
export type PaymentFrequency = "monthly" | "quarterly" | "yearly";
export type PaymentCategory = "chirie" | "utilitati" | "leasing" | "asigurare" | "abonament" | "servicii" | "altele";

export interface RecurringPayment {
  id: string;
  name: string;
  category: PaymentCategory;
  amount: number;
  currency: string;
  frequency: PaymentFrequency;
  dueDay: number; // day of month
  supplier: string;
  iban: string;
  notes: string;
  active: boolean;
  startDate: string;
  endDate: string | null;
}

export const paymentCategoryLabels: Record<PaymentCategory, string> = {
  chirie: "Chirie",
  utilitati: "Utilități",
  leasing: "Leasing",
  asigurare: "Asigurare",
  abonament: "Abonament",
  servicii: "Servicii",
  altele: "Altele",
};

export const frequencyLabels: Record<PaymentFrequency, string> = {
  monthly: "Lunar",
  quarterly: "Trimestrial",
  yearly: "Anual",
};

export const recurringPayments: RecurringPayment[] = [
  { id: "PAY-001", name: "Chirie hală producție", category: "chirie", amount: 4500, currency: "EUR", frequency: "monthly", dueDay: 5, supplier: "Imobiliare Vest SRL", iban: "RO12 RZBR 0000 0600 1234 5678", notes: "Contract până 2028", active: true, startDate: "2023-01-01", endDate: "2028-12-31" },
  { id: "PAY-002", name: "Chirie birou comercial", category: "chirie", amount: 1200, currency: "EUR", frequency: "monthly", dueDay: 5, supplier: "Imobiliare Vest SRL", iban: "RO12 RZBR 0000 0600 1234 5678", notes: "Inclus în contractul halei", active: true, startDate: "2023-01-01", endDate: "2028-12-31" },
  { id: "PAY-003", name: "Energie electrică", category: "utilitati", amount: 3200, currency: "RON", frequency: "monthly", dueDay: 15, supplier: "Enel Energie", iban: "RO55 RNCB 0082 0441 2345 0001", notes: "Consum mediu hală + birou", active: true, startDate: "2023-01-01", endDate: null },
  { id: "PAY-004", name: "Gaz natural", category: "utilitati", amount: 1800, currency: "RON", frequency: "monthly", dueDay: 20, supplier: "Engie România", iban: "RO33 BRDE 445S V123 4567 8900", notes: "Încălzire hală iarna", active: true, startDate: "2023-01-01", endDate: null },
  { id: "PAY-005", name: "Apă + canalizare", category: "utilitati", amount: 450, currency: "RON", frequency: "monthly", dueDay: 25, supplier: "Apa Nova", iban: "RO77 INGB 0001 0084 5678 9012", notes: "", active: true, startDate: "2023-01-01", endDate: null },
  { id: "PAY-006", name: "Leasing CNC Router", category: "leasing", amount: 1850, currency: "EUR", frequency: "monthly", dueDay: 10, supplier: "BT Leasing", iban: "RO49 BTRL 0130 1205 9876 5432", notes: "36 rate, mai rămân 12", active: true, startDate: "2024-01-01", endDate: "2027-01-01" },
  { id: "PAY-007", name: "Leasing Epson SC-60600 #2", category: "leasing", amount: 980, currency: "EUR", frequency: "monthly", dueDay: 10, supplier: "BT Leasing", iban: "RO49 BTRL 0130 1205 9876 5432", notes: "48 rate, mai rămân 24", active: true, startDate: "2024-04-01", endDate: "2028-04-01" },
  { id: "PAY-008", name: "Asigurare hală + echipamente", category: "asigurare", amount: 2400, currency: "EUR", frequency: "yearly", dueDay: 1, supplier: "Allianz-Țiriac", iban: "RO88 RZBR 0000 0600 9999 8888", notes: "Polița se reînnoiește în ianuarie", active: true, startDate: "2023-01-01", endDate: null },
  { id: "PAY-009", name: "Abonament SmartBill", category: "abonament", amount: 149, currency: "RON", frequency: "monthly", dueDay: 1, supplier: "SmartBill SRL", iban: "", notes: "Plan Business", active: true, startDate: "2022-06-01", endDate: null },
  { id: "PAY-010", name: "Abonament internet fibră", category: "abonament", amount: 89, currency: "RON", frequency: "monthly", dueDay: 15, supplier: "RCS-RDS", iban: "", notes: "1Gbps business", active: true, startDate: "2023-03-01", endDate: null },
  { id: "PAY-011", name: "Servicii contabilitate", category: "servicii", amount: 2500, currency: "RON", frequency: "monthly", dueDay: 5, supplier: "Expert Conta SRL", iban: "RO22 BTRL 0130 1205 1111 2222", notes: "", active: true, startDate: "2020-01-01", endDate: null },
  { id: "PAY-012", name: "Pază + monitorizare", category: "servicii", amount: 800, currency: "RON", frequency: "monthly", dueDay: 1, supplier: "SecurGuard SRL", iban: "RO66 INGB 0001 0084 3333 4444", notes: "Monitorizare 24/7 + patrulă nocturnă", active: true, startDate: "2023-01-01", endDate: null },
];

// ============================================================
// COLABORATORI EXTERNI (External Partners)
// ============================================================
export type CollabCategory = "produs" | "serviciu";
export type CollabStatus = "activ" | "inactiv" | "preferat";

export interface ExternalCollaborator {
  id: string;
  companyName: string;
  cui: string;
  contactPerson: string;
  phone: string;
  email: string;
  category: CollabCategory;
  specializations: string[];
  description: string;
  status: CollabStatus;
  qualityRating: number; // 1-5
  avgDeliveryDays: number;
  totalOrdersCompleted: number;
  totalValueRON: number;
  lastOrderDate: string;
  city: string;
  notes: string;
}

export const collabCategoryLabels: Record<CollabCategory, string> = {
  produs: "Produs",
  serviciu: "Serviciu",
};

export const collabStatusLabels: Record<CollabStatus, string> = {
  activ: "Activ",
  inactiv: "Inactiv",
  preferat: "Preferat",
};

// ============================================================
// PRINT MATERIAL TYPES — For Work Intake Material Selection
// ============================================================
export interface PrintMaterialType {
  id: string;
  name: string;
  category: "banner" | "autocolant" | "folie" | "mesh" | "vinil" | "rigid";
  /** Cost per mp for the material itself */
  materialCostPerSqm: number;
  /** Roll width in mm (0 for rigid/sheet materials) */
  rollWidthMM: number;
  /** Related inventory material ID */
  inventoryMaterialId: string;
  /** Whether this material requires lamination */
  requiresLamination: boolean;
}

export const printMaterialTypes: PrintMaterialType[] = [
  { id: "PMAT-01", name: "Banner Frontlit 440g", category: "banner", materialCostPerSqm: 3.2, rollWidthMM: 3200, inventoryMaterialId: "MAT-007", requiresLamination: false },
  { id: "PMAT-02", name: "Mesh Perforat 270g", category: "mesh", materialCostPerSqm: 2.8, rollWidthMM: 3200, inventoryMaterialId: "MAT-008", requiresLamination: false },
  { id: "PMAT-03", name: "Autocolant Alb Lucios", category: "autocolant", materialCostPerSqm: 2.5, rollWidthMM: 1370, inventoryMaterialId: "MAT-005", requiresLamination: true },
  { id: "PMAT-04", name: "Autocolant Alb Mat", category: "autocolant", materialCostPerSqm: 2.5, rollWidthMM: 1370, inventoryMaterialId: "MAT-005", requiresLamination: true },
  { id: "PMAT-05", name: "Autocolant Transparent", category: "autocolant", materialCostPerSqm: 3.0, rollWidthMM: 1370, inventoryMaterialId: "MAT-005", requiresLamination: true },
  { id: "PMAT-06", name: "Vinil Autoadeziv", category: "vinil", materialCostPerSqm: 3.5, rollWidthMM: 1370, inventoryMaterialId: "MAT-005", requiresLamination: true },
  { id: "PMAT-07", name: "Folie Sablată", category: "folie", materialCostPerSqm: 6.5, rollWidthMM: 1220, inventoryMaterialId: "MAT-018", requiresLamination: false },
  { id: "PMAT-08", name: "Banner Backlit 510g", category: "banner", materialCostPerSqm: 4.5, rollWidthMM: 3200, inventoryMaterialId: "MAT-007", requiresLamination: false },
  { id: "PMAT-09", name: "PVC Expandat 5mm (print UV)", category: "rigid", materialCostPerSqm: 18.0, rollWidthMM: 0, inventoryMaterialId: "MAT-003", requiresLamination: false },
  { id: "PMAT-10", name: "ACP / Dibond 3mm (print aplicat)", category: "rigid", materialCostPerSqm: 45.0, rollWidthMM: 0, inventoryMaterialId: "MAT-001", requiresLamination: false },
];

// ============================================================
// COST ENGINE — Ink Consumption & Machine Cost Profiles
// ============================================================
export interface MachineCostProfile {
  machineId: string;
  machineName: string;
  /** Ink consumption cost per square meter (EUR) */
  inkCostPerSqm: number;
  /** Lamination cost per sqm if applicable (EUR) */
  laminationCostPerSqm: number;
  /** Print speed m²/h — used for time estimation */
  printSpeedSqmPerHour: number;
  /** Currency */
  currency: string;
}

export const machineCostProfiles: MachineCostProfile[] = [
  { machineId: "m_epson1", machineName: "Epson SC-60600 #1", inkCostPerSqm: 1.5, laminationCostPerSqm: 0.8, printSpeedSqmPerHour: 21.2, currency: "EUR" },
  { machineId: "m_epson2", machineName: "Epson SC-60600 #2", inkCostPerSqm: 1.5, laminationCostPerSqm: 0.8, printSpeedSqmPerHour: 21.2, currency: "EUR" },
];

/** Get cost profile for the default assigned printer (first available) */
export function getDefaultCostProfile(): MachineCostProfile {
  return machineCostProfiles[0];
}

/** Calculate cost breakdown for a print job */
export function calculatePrintCost(
  materialId: string,
  widthMM: number,
  heightMM: number,
  quantity: number = 1
): {
  areaSqm: number;
  materialCost: number;
  inkCost: number;
  laminationCost: number;
  totalCostPerUnit: number;
  totalCost: number;
  currency: string;
  estimatedPrintMinutes: number;
  machineUsed: string;
} {
  const material = printMaterialTypes.find((m) => m.id === materialId);
  const profile = getDefaultCostProfile();
  const areaSqm = (widthMM * heightMM) / 1_000_000;

  const materialCost = material ? areaSqm * material.materialCostPerSqm : 0;
  const inkCost = areaSqm * profile.inkCostPerSqm;
  const laminationCost = material?.requiresLamination ? areaSqm * profile.laminationCostPerSqm : 0;
  const totalCostPerUnit = materialCost + inkCost + laminationCost;
  const totalCost = totalCostPerUnit * quantity;
  const estimatedPrintMinutes = Math.ceil((areaSqm / profile.printSpeedSqmPerHour) * 60);

  return {
    areaSqm,
    materialCost,
    inkCost,
    laminationCost,
    totalCostPerUnit,
    totalCost,
    currency: profile.currency,
    estimatedPrintMinutes,
    machineUsed: profile.machineName,
  };
}

export const externalCollaborators: ExternalCollaborator[] = [
  // === PRODUSE (ce pot confecționa) ===
  { id: "EXT-001", companyName: "PrintMaster Offset SRL", cui: "RO18765432", contactPerson: "Gheorghe Marin", phone: "0744-200-001", email: "comenzi@printmaster.ro", category: "produs", specializations: ["Tipografie offset", "Cărți vizită", "Broșuri", "Cataloage", "Flyere"], description: "Tipografie offset cu experiență 15+ ani, tiraje medii și mari", status: "preferat", qualityRating: 5, avgDeliveryDays: 5, totalOrdersCompleted: 48, totalValueRON: 125000, lastOrderDate: "2026-04-02", city: "București", notes: "Partener de încredere, prețuri competitive pe tiraje >1000 buc" },
  { id: "EXT-002", companyName: "MetalCraft Industries SRL", cui: "RO22334455", contactPerson: "Vasile Dumitrescu", phone: "0755-300-002", email: "office@metalcraft.ro", category: "produs", specializations: ["Confecții metalice grele", "Structuri sudate", "Stâlpi totem >8m", "Porți acces", "Garduri metalice"], description: "Atelier de confecții metalice grele — structuri care depășesc capacitatea noastră", status: "activ", qualityRating: 4, avgDeliveryDays: 12, totalOrdersCompleted: 15, totalValueRON: 89000, lastOrderDate: "2026-03-20", city: "Ploiești", notes: "Capacitate mare, dar termen de livrare mai lung" },
  { id: "EXT-003", companyName: "NeonArt Studio SRL", cui: "RO33445566", contactPerson: "Alina Cristea", phone: "0722-400-003", email: "alina@neonart.ro", category: "produs", specializations: ["Neon LED flexibil", "Neon tradițional", "Litere neon custom", "Instalații artistice neon"], description: "Producție neon LED și tradițional — produse pe care nu le confecționăm intern", status: "activ", qualityRating: 5, avgDeliveryDays: 8, totalOrdersCompleted: 22, totalValueRON: 67000, lastOrderDate: "2026-03-28", city: "Cluj-Napoca", notes: "Calitate excelentă, prețuri premium" },
  { id: "EXT-004", companyName: "GravTech Laser SRL", cui: "RO44556677", contactPerson: "Marius Ionescu", phone: "0733-500-004", email: "comenzi@gravtech.ro", category: "produs", specializations: ["Gravură laser industrială", "Tăiere laser inox >5mm", "Gravură pe sticlă", "Plăcuțe industriale"], description: "Gravură laser de precizie și tăiere materiale groase — completează CNC-ul nostru", status: "activ", qualityRating: 4, avgDeliveryDays: 6, totalOrdersCompleted: 31, totalValueRON: 42000, lastOrderDate: "2026-04-05", city: "Timișoara", notes: "Laser fibră 4kW — poate tăia inox până la 12mm" },
  { id: "EXT-005", companyName: "AluProfile Expert SRL", cui: "RO55667788", contactPerson: "Dan Voicu", phone: "0744-600-005", email: "dan@aluprofile.ro", category: "produs", specializations: ["Tâmplărie aluminiu", "Profile LED custom", "Casete aluminiu speciale", "Rame click"], description: "Tâmplărie aluminiu specializată — profile custom și casete speciale", status: "preferat", qualityRating: 5, avgDeliveryDays: 7, totalOrdersCompleted: 38, totalValueRON: 156000, lastOrderDate: "2026-04-08", city: "București", notes: "Partener strategic — profile custom la comandă" },
  { id: "EXT-006", companyName: "TextilPrint RO SRL", cui: "RO66778899", contactPerson: "Ioana Barbu", phone: "0755-700-006", email: "ioana@textilprint.ro", category: "produs", specializations: ["Steaguri personalizate", "Textile printate", "Bannere textile", "Drapele", "Copertine printate"], description: "Print pe textile — steaguri, bannere textile, copertine", status: "activ", qualityRating: 4, avgDeliveryDays: 5, totalOrdersCompleted: 19, totalValueRON: 28000, lastOrderDate: "2026-03-15", city: "Brașov", notes: "Sublimație pe poliester, calitate bună" },
  // === SERVICII (ce servicii oferă) ===
  { id: "EXT-007", companyName: "LargeFormat Pro SRL", cui: "RO77889900", contactPerson: "Cristian Neagu", phone: "0722-800-007", email: "cristian@largeformat.ro", category: "serviciu", specializations: ["Printing large format UV", "Print flatbed >3m", "Print pe sticlă", "Print pe lemn", "Print pe metal"], description: "Servicii de print large format UV flatbed — suprafețe rigide mari", status: "activ", qualityRating: 4, avgDeliveryDays: 4, totalOrdersCompleted: 26, totalValueRON: 52000, lastOrderDate: "2026-04-01", city: "București", notes: "Flatbed 3.2x2m — complementar cu printerele noastre roll-to-roll" },
  { id: "EXT-008", companyName: "VopsitPro Industrial SRL", cui: "RO88990011", contactPerson: "Florin Popa", phone: "0733-900-008", email: "florin@vopsitpro.ro", category: "serviciu", specializations: ["Vopsitorie electrostatică", "Vopsitorie RAL", "Lăcuire", "Grunduire industrială", "Zincare"], description: "Vopsitorie industrială — vopsire electrostatică și RAL pentru structuri metalice", status: "preferat", qualityRating: 5, avgDeliveryDays: 5, totalOrdersCompleted: 42, totalValueRON: 78000, lastOrderDate: "2026-04-06", city: "Ilfov", notes: "Cabină vopsire 6m — poate vopsi totemi întregi" },
  { id: "EXT-009", companyName: "AlpinSign Montaj SRL", cui: "RO99001122", contactPerson: "Radu Enescu", phone: "0744-100-009", email: "radu@alpinsign.ro", category: "serviciu", specializations: ["Montaj la înălțime", "Alpinism utilitar", "Montaj fațade", "Montaj totemi", "Montaj casete luminoase"], description: "Echipă de alpiniști utilitari — montaj signalistică la înălțime", status: "preferat", qualityRating: 5, avgDeliveryDays: 3, totalOrdersCompleted: 55, totalValueRON: 95000, lastOrderDate: "2026-04-10", city: "București", notes: "Echipă rapidă și profesionistă, autorizați ISCIR" },
  { id: "EXT-010", companyName: "TransGabarit Logistics SRL", cui: "RO10112233", contactPerson: "Bogdan Matei", phone: "0755-200-010", email: "bogdan@transgabarit.ro", category: "serviciu", specializations: ["Transport agabaritic", "Transport totemi", "Macara", "Escortă rutieră"], description: "Transport agabaritic și macara — pentru totemi și structuri mari", status: "activ", qualityRating: 4, avgDeliveryDays: 2, totalOrdersCompleted: 18, totalValueRON: 45000, lastOrderDate: "2026-03-25", city: "București", notes: "Macara 40t disponibilă" },
  { id: "EXT-011", companyName: "StructDesign Engineering SRL", cui: "RO11223344", contactPerson: "Andrei Stoica", phone: "0722-300-011", email: "andrei@structdesign.ro", category: "serviciu", specializations: ["Proiectare structuri", "Calcul rezistență", "Avize ISC", "Proiecte fundații", "Expertize tehnice"], description: "Proiectare structuri metalice și fundații — documentație tehnică pentru autorizări", status: "activ", qualityRating: 5, avgDeliveryDays: 10, totalOrdersCompleted: 12, totalValueRON: 36000, lastOrderDate: "2026-03-18", city: "București", notes: "Inginer autorizat MLPAT — necesar pentru totemi >4m" },
  { id: "EXT-012", companyName: "ElectroSign Install SRL", cui: "RO12334455", contactPerson: "Mihai Radu", phone: "0733-400-012", email: "mihai@electrosign.ro", category: "serviciu", specializations: ["Instalații electrice", "Branșamente", "Tablouri electrice", "Autorizare ANRE"], description: "Instalații electrice autorizate ANRE — branșamente pentru casete și totemi", status: "activ", qualityRating: 4, avgDeliveryDays: 5, totalOrdersCompleted: 28, totalValueRON: 52000, lastOrderDate: "2026-04-03", city: "București", notes: "Electrician autorizat ANRE gradul IIB" },
  { id: "EXT-013", companyName: "QuickPrint Digital SRL", cui: "RO13445566", contactPerson: "Elena Dinu", phone: "0744-500-013", email: "elena@quickprint.ro", category: "serviciu", specializations: ["Print digital mic format", "Cărți vizită urgente", "Etichete", "Stickere die-cut"], description: "Print digital rapid — tiraje mici și urgențe pe care nu le acoperim", status: "inactiv", qualityRating: 3, avgDeliveryDays: 2, totalOrdersCompleted: 8, totalValueRON: 5600, lastOrderDate: "2025-11-20", city: "București", notes: "Folosit rar, doar pentru urgențe" },
];