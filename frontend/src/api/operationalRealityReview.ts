/**
 * Operational Reality Review API — read-only gaps dashboard.
 * GET-only; no mutations.
 */
import { getAPIBaseURL } from "../lib/config";

const getAPIBase = () => `${getAPIBaseURL()}/api/v1`;

export type GapSeverity = "info" | "warning" | "critical";
export type GapCategory = "atelier" | "materiale" | "montaj_teren";

export type GapType =
  | "TASK_MISSING_EMPLOYEE"
  | "TASK_STARTED_NOT_COMPLETED"
  | "TASK_COMPLETED_WITHOUT_COMPLETION_NOTES"
  | "TASK_COMPLETED_WITHOUT_MATERIALS"
  | "MATERIAL_WITHOUT_TASK_ID"
  | "MATERIAL_WITHOUT_REPORTER"
  | "FIELD_INSTALLATION_PLANNED_NOT_STARTED"
  | "FIELD_INSTALLATION_STARTED_NOT_COMPLETED"
  | "FIELD_INSTALLATION_COMPLETED_WITHOUT_PHOTOS"
  | "FIELD_INSTALLATION_COMPLETED_WITHOUT_CLIENT_OBSERVATIONS"
  | "FIELD_INSTALLATION_WITHOUT_TEAM_MEMBERS"
  | "TASK_MAPPING_UNCONFIRMED"
  | "LEGACY_TASK_WITHOUT_EMPLOYEE_ID";

export interface RealityGapLinks {
  order: string | null;
  operator: string | null;
  tablet: string | null;
  field_installation: string | null;
  execution_detail: string | null;
  team_id: string | null;
  task_id: string | null;
}

export interface RealityGap {
  gap_type: GapType;
  severity: GapSeverity;
  category: GapCategory;
  message: string;
  order_id: number | null;
  order_code: string | null;
  task_id: string | null;
  team_id: number | null;
  links: RealityGapLinks;
  context?: Record<string, unknown>;
}

export interface RealityReviewSummary {
  orders_analyzed: number;
  total_tasks_analyzed: number;
  tasks_with_employee: number;
  tasks_without_employee: number;
  tasks_completed: number;
  tasks_started_not_completed: number;
  tasks_completed_without_materials: number;
  materials_without_task_id: number;
  materials_without_reporter: number;
  field_installation_teams_analyzed: number;
  field_installations_started_not_completed: number;
  field_installations_completed_without_photos: number;
  total_gaps: number;
  gaps_by_severity: Record<GapSeverity, number>;
  gaps_by_category: Record<GapCategory, number>;
}

export interface OperationalRealityReviewResponse {
  read_only: true;
  summary: RealityReviewSummary;
  gaps: RealityGap[];
  gap_types_supported: GapType[];
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getOperationalRealityReview(): Promise<OperationalRealityReviewResponse> {
  const res = await fetch(`${getAPIBase()}/operational-reality/review`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(`GET /operational-reality/review failed: ${res.status}`);
  }
  return res.json() as Promise<OperationalRealityReviewResponse>;
}
