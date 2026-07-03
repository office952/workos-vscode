/**
 * Operational Workforce & Resource Registry API client.
 *
 * Canonical read surface for employees, resources, and operation mappings.
 * Consumed by /operator, /tablet (future), montaj, and reports — not owned locally.
 */
import { getAPIBaseURL } from "@/lib/config";

const base = () => `${getAPIBaseURL()}/api/v1/operational-registry`;

export interface RegistryEmployee {
  id: number;
  name: string;
  role: string | null;
  department: string | null;
  status: string;
  employee_type: string;
  user_id: string | null;
  salary_amount: number | null;
  salary_currency: string;
  salary_period: string;
  skill_codes: string[];
  workcenter_codes: string[];
  resource_codes: string[];
}

export interface RegistryResource {
  resource_code: string;
  name: string;
  description: string | null;
  machine_type: string;
  resource_kind: "machine" | "tool" | "work_area" | string;
  workcenter_code: string | null;
  operational_status: string;
  is_available: boolean;
  is_active: boolean;
  capabilities: string[];
  capacity_metadata: Record<string, unknown>;
}

export interface OperationResourceMapping {
  operation_code: string;
  required_skill_codes: string[];
  allowed_workcenter_codes: string[];
  allowed_resource_codes: string[];
  authorization_mode: "skill" | "explicit" | "hybrid" | string;
  default_resource_code: string | null;
  product_system_aliases: string[];
  authorized_employee_ids: number[];
  notes: string | null;
}

export interface OperationalCatalogSkill {
  skill_code: string;
  label_ro: string;
  category: string;
}

export interface OperationalCatalogWorkcenter {
  workcenter_code: string;
  label_ro: string;
  category: string;
}

export interface OperationalCatalog {
  skills: OperationalCatalogSkill[];
  workcenters: OperationalCatalogWorkcenter[];
  resources: RegistryResource[];
  suggested_operation_aliases: Record<string, string>;
  authorization_modes: string[];
}

export interface EligibleEmployeePool {
  operation_code: string;
  resolved_operation_code: string | null;
  authorization_mode: string;
  resolution?: string;
  required_skill_codes: string[];
  allowed_workcenter_codes: string[];
  allowed_resource_codes: string[];
  default_resource_code: string | null;
  authorized_employee_ids: number[];
  items: Array<RegistryEmployee & { eligibility?: string; skill_match?: boolean; explicit_override?: boolean }>;
  total: number;
}

export type FieldInstallationTeamStatus =
  | "draft"
  | "planned"
  | "in_progress"
  | "completed"
  | "cancelled";

export interface FieldInstallationTeamMember {
  employee_id: number;
  employee_name: string;
  employee_role: string | null;
  role_on_site: string | null;
  skill_codes: string[];
}

export interface FieldInstallationTeam {
  id: number;
  installation_ref: string;
  order_id: number | null;
  status: FieldInstallationTeamStatus;
  site_address: string | null;
  scheduled_at: string | null;
  notes: string | null;
  members: FieldInstallationTeamMember[];
  member_count: number;
  reporting_ready: boolean;
  started_at: string | null;
  ended_at: string | null;
  completion_photos: string[];
  client_observations: string | null;
  members_present: Array<{
    employee_id: number;
    employee_name: string;
    present_at: string;
  }>;
  materials_consumed: Array<{
    material_name: string;
    quantity: number;
    unit: string;
    reported_at?: string;
    reported_by_employee_id?: number;
    consumption_notes?: string;
  }>;
  internal_notes: string | null;
  started_by_employee_id: number | null;
  warnings: string[];
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/** Operator-safe employee shape — excludes salary fields from UI usage. */
export type OperatorRegistryEmployee = Omit<
  RegistryEmployee,
  "salary_amount" | "salary_currency" | "salary_period"
>;

export function toOperatorSafeEmployee(emp: RegistryEmployee): OperatorRegistryEmployee {
  const { salary_amount: _a, salary_currency: _c, salary_period: _p, ...safe } = emp;
  return safe;
}

export const operationalRegistryApi = {
  getCatalog: () => fetchJson<OperationalCatalog>(`${base()}/catalog`),

  listEmployees: () =>
    fetchJson<{ items: RegistryEmployee[]; total: number }>(`${base()}/employees`),

  listActiveEmployees: async (): Promise<{ items: OperatorRegistryEmployee[]; total: number }> => {
    const res = await fetchJson<{ items: RegistryEmployee[]; total: number }>(
      `${base()}/employees`
    );
    const active = res.items
      .filter((e) => e.status === "active")
      .map(toOperatorSafeEmployee);
    return { items: active, total: active.length };
  },

  getEmployee: (id: number) =>
    fetchJson<RegistryEmployee>(`${base()}/employees/${id}`),

  updateEmployeeAuthorizations: (
    id: number,
    payload: {
      skill_codes?: string[];
      workcenter_codes?: string[];
      resource_codes?: string[];
    }
  ) =>
    fetchJson<{ employee_id: number; skill_codes: string[]; workcenter_codes: string[]; resource_codes: string[] }>(
      `${base()}/employees/${id}/authorizations`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    ),

  listResources: () =>
    fetchJson<{ items: RegistryResource[]; total: number }>(`${base()}/resources`),

  getResource: (code: string) =>
    fetchJson<RegistryResource>(`${base()}/resources/${encodeURIComponent(code)}`),

  upsertResource: (payload: {
    machine_code: string;
    name: string;
    machine_type: string;
    resource_kind?: string;
    workcenter_code?: string | null;
    description?: string | null;
    operational_status?: string;
    is_available?: boolean;
    is_active?: boolean;
    capabilities?: string[];
    capacity_metadata?: Record<string, unknown>;
  }) =>
    fetchJson<RegistryResource>(`${base()}/resources`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  listAuthorizedEmployeesForResource: (code: string) =>
    fetchJson<{ resource_code: string; items: RegistryEmployee[]; total: number }>(
      `${base()}/resources/${encodeURIComponent(code)}/authorized-employees`
    ),

  listOperationMappings: () =>
    fetchJson<{ items: OperationResourceMapping[]; total: number }>(
      `${base()}/operation-mappings`
    ),

  getOperationMapping: (operationCode: string) =>
    fetchJson<OperationResourceMapping>(
      `${base()}/operation-mappings/${encodeURIComponent(operationCode)}`
    ),

  resolveOperationMapping: (operationCode: string) =>
    fetchJson<OperationResourceMapping & { resolved_operation_code?: string; resolution?: string; matched_alias?: string }>(
      `${base()}/operation-mappings/${encodeURIComponent(operationCode)}/resolve`
    ),

  upsertOperationMapping: (payload: OperationResourceMapping) =>
    fetchJson<OperationResourceMapping>(`${base()}/operation-mappings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  getEligibleEmployeesForOperation: (operationCode: string, machineType?: string) => {
    const qs = machineType ? `?machine_type=${encodeURIComponent(machineType)}` : "";
    return fetchJson<EligibleEmployeePool>(
      `${base()}/operation-mappings/${encodeURIComponent(operationCode)}/eligible-employees${qs}`
    );
  },

  listFieldInstallationTeams: (params?: { order_id?: number; installation_ref?: string }) => {
    const qs = new URLSearchParams();
    if (params?.order_id != null) qs.set("order_id", String(params.order_id));
    if (params?.installation_ref) qs.set("installation_ref", params.installation_ref);
    const query = qs.toString();
    return fetchJson<{ items: FieldInstallationTeam[]; total: number; installation_ref: string | null }>(
      `${base()}/field-installation-teams${query ? `?${query}` : ""}`
    );
  },

  getFieldInstallationTeam: (teamId: number) =>
    fetchJson<FieldInstallationTeam>(`${base()}/field-installation-teams/${teamId}`),

  createFieldInstallationTeam: (payload: {
    installation_ref: string;
    member_employee_ids?: number[];
    site_address?: string;
    notes?: string;
    roles_on_site?: Record<number, string>;
    status?: FieldInstallationTeamStatus;
  }) =>
    fetchJson<FieldInstallationTeam>(`${base()}/field-installation-teams`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  updateFieldInstallationTeam: (
    teamId: number,
    payload: { status?: FieldInstallationTeamStatus; site_address?: string; notes?: string }
  ) =>
    fetchJson<FieldInstallationTeam>(`${base()}/field-installation-teams/${teamId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  addFieldInstallationTeamMember: (
    teamId: number,
    payload: { employee_id: number; role_on_site?: string }
  ) =>
    fetchJson<FieldInstallationTeam>(`${base()}/field-installation-teams/${teamId}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  removeFieldInstallationTeamMember: (teamId: number, employeeId: number) =>
    fetchJson<FieldInstallationTeam>(
      `${base()}/field-installation-teams/${teamId}/members/${employeeId}`,
      { method: "DELETE" }
    ),

  startFieldInstallationReporting: (
    teamId: number,
    payload: { started_by_employee_id?: number; members_present?: number[] }
  ) =>
    fetchJson<FieldInstallationTeam>(
      `${base()}/field-installation-teams/${teamId}/start-reporting`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    ),

  completeFieldInstallationReporting: (
    teamId: number,
    payload: {
      client_observations?: string;
      completion_photos?: string[];
      internal_notes?: string;
      members_present?: number[];
      materials_consumed?: Array<{
        material_name: string;
        quantity: number;
        unit: string;
        reported_by_employee_id?: number;
        consumption_notes?: string;
      }>;
      completed_by_employee_id?: number;
    }
  ) =>
    fetchJson<FieldInstallationTeam>(
      `${base()}/field-installation-teams/${teamId}/complete-reporting`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    ),

  updateFieldInstallationReporting: (
    teamId: number,
    payload: {
      client_observations?: string;
      completion_photos?: string[];
      members_present?: number[];
      internal_notes?: string;
    }
  ) =>
    fetchJson<FieldInstallationTeam>(
      `${base()}/field-installation-teams/${teamId}/reporting`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    ),
};
