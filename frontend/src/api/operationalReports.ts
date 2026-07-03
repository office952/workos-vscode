/**
 * Operational Reports API — read-only workforce/execution reality reports.
 */
import { getAPIBaseURL } from "../lib/config";

const getAPIBase = () => `${getAPIBaseURL()}/api/v1`;

export type ReportCategory =
  | "all"
  | "employee_activity"
  | "task_reality"
  | "materials"
  | "field_installation"
  | "completeness";

export interface EmployeeActivityRow {
  employee_id: number;
  employee_name: string;
  tasks_started: number;
  tasks_completed: number;
  tasks_blocked: number;
  observed_minutes_total: number;
  observed_minutes_computable: number;
}

export interface TaskRealityRow {
  order_id: number;
  order_code: string;
  task_id: string | null;
  process_type: string | null;
  operation_code: string | null;
  employee_id: number | null;
  employee_name: string | null;
  started_at: string | null;
  ended_at: string | null;
  status: string;
  completion_notes_present: boolean;
  materials_reported: boolean;
  observed_minutes: number | null;
  links?: TaskRealityLinks;
}

export interface MaterialsRealityRow {
  order_id: number;
  order_code: string;
  task_id: string | null;
  material_id: string | null;
  material_code: string | null;
  material_name: string | null;
  quantity: number | null;
  unit: string | null;
  reported_by_employee_id: number | null;
  reported_by_employee_name: string | null;
  reported_at: string | null;
  consumption_notes: string | null;
}

export interface FieldInstallationRow {
  team_id: number;
  installation_ref: string;
  order_id: number | null;
  order_code: string;
  status: string;
  team_members_count: number;
  started_at: string | null;
  ended_at: string | null;
  completion_photos_count: number;
  client_observations_present: boolean;
}

export interface CompletenessSummary {
  total_tasks: number;
  tasks_with_employee: number;
  tasks_without_employee: number;
  tasks_with_materials: number;
  tasks_without_materials: number;
  total_materials_reported: number;
  materials_with_reporter: number;
  materials_without_reporter: number;
  materials_with_task_id: number;
  materials_without_task_id: number;
  field_installations_complete: number;
  field_installations_incomplete: number;
  plan_operational_tasks_total?: number;
  plan_orders_v2_not_materialized?: number;
}

export interface TaskRealityLinks {
  order: string;
  execution_detail: string;
  operator: string;
  tablet: string | null;
}

export interface OperationalReportsFilters {
  from_date?: string;
  to_date?: string;
  employee_id?: number;
  order_id?: number;
  category?: ReportCategory;
}

export interface OperationalReportsResponse {
  read_only: true;
  filters_applied: OperationalReportsFilters & { category: string };
  employee_activity?: EmployeeActivityRow[];
  task_reality?: TaskRealityRow[];
  materials_reality?: MaterialsRealityRow[];
  field_installation?: FieldInstallationRow[];
  completeness_summary?: CompletenessSummary;
  counts: {
    employee_activity_rows: number;
    task_reality_rows: number;
    materials_reality_rows: number;
    field_installation_rows: number;
  };
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getOperationalReportsSummary(
  filters: OperationalReportsFilters = {}
): Promise<OperationalReportsResponse> {
  const params = new URLSearchParams();
  if (filters.from_date) params.set("from_date", filters.from_date);
  if (filters.to_date) params.set("to_date", filters.to_date);
  if (filters.employee_id) params.set("employee_id", String(filters.employee_id));
  if (filters.order_id) params.set("order_id", String(filters.order_id));
  if (filters.category) params.set("category", filters.category);

  const qs = params.toString();
  const url = `${getAPIBase()}/operational-reports/summary${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) {
    throw new Error(`GET /operational-reports/summary failed: ${res.status}`);
  }
  return res.json() as Promise<OperationalReportsResponse>;
}
