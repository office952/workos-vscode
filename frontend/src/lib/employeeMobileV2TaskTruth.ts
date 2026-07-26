import type {
  EmployeeMobileTaskDTO,
  EmployeeMobileTaskTruthResponse,
} from "@/api/employeeMobileTasks";

export interface EmployeeMobileTruthTaskNested {
  identity: {
    task_id: string;
    deterministic_task_key?: string | null;
    display_label: string;
    component_label?: string | null;
    component_role?: string | null;
    operation_label?: string | null;
    operation_code?: string | null;
    logo_segment_label?: string | null;
    identity_source?: string;
    identity_classification?: string | null;
  };
  assignment: {
    assigned_employee_id?: number | null;
    assigned_employee_name?: string | null;
    is_assigned_to_current_employee: boolean;
    is_available_for_claim: boolean;
    can_claim: boolean;
    assignment_source?: string;
  };
  readiness: {
    is_startable: boolean;
    readiness_label?: string | null;
    readiness_status?: string | null;
    readiness_reasons?: Array<Record<string, unknown>>;
    blocking_task_ids?: string[];
    blocking_tasks?: Array<{ task_id: string; name: string }>;
    material_warning?: string | null;
    dependency_warning?: string | null;
    production_release_blocked: boolean;
    production_blocker_summary?: string | null;
    can_start: boolean;
    can_start_from_available?: boolean;
    can_complete: boolean;
  };
  authority?: {
    task_identity_version?: string | null;
    readiness_authority?: string | null;
    release_authority?: string | null;
    legacy_fallback_active?: boolean;
    execution_source?: string | null;
  };
  order_id: number;
  order_code?: string;
  client_label?: string;
  execution_plan_id?: number | null;
  plan_sequence?: number | null;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
  blocked_at?: string | null;
  blocked_reason?: string | null;
  access_mode?: string | null;
  preview_only?: boolean;
}

export interface EmployeeMobileV2TaskTruthView {
  contractVersion: string;
  employeeId: number;
  summary: EmployeeMobileTaskTruthResponse["summary"];
  assignedTasks: EmployeeMobileTaskDTO[];
  availableTasks: EmployeeMobileTaskDTO[];
  inProgressTasks: EmployeeMobileTaskDTO[];
  allTasks: EmployeeMobileTaskDTO[];
}

const COMPONENT_ROLE_LABELS: Record<string, string> = {
  root_product: "Produs principal",
  mounting_panel: "Panou montaj",
  premount_structure: "Premontaj",
  logo_segment: "Logo",
};

export function resolveTaskDisplayTitle(task: EmployeeMobileTaskDTO): string {
  return String(task.display_label || task.title || "").trim() || task.task_id;
}

export function resolveTaskComponentLine(task: EmployeeMobileTaskDTO): string | null {
  if (task.logo_segment_label) {
    return task.logo_segment_label.startsWith("Logo")
      ? task.logo_segment_label
      : `Logo — ${task.logo_segment_label}`;
  }
  if (task.component_label?.trim()) return task.component_label.trim();
  if (task.component_role && COMPONENT_ROLE_LABELS[task.component_role]) {
    return COMPONENT_ROLE_LABELS[task.component_role];
  }
  return null;
}

export function resolveTaskOperationLine(task: EmployeeMobileTaskDTO): string | null {
  const op = task.operation_label || task.process_type;
  return op?.trim() ? op.trim() : null;
}

export function truthTaskToDto(
  task: EmployeeMobileTruthTaskNested,
  contractVersion: string,
): EmployeeMobileTaskDTO {
  const ident = task.identity;
  const assign = task.assignment;
  const ready = task.readiness;
  const auth = task.authority;
  return {
    contract_version: contractVersion,
    task_id: ident.task_id,
    order_id: task.order_id,
    order_code: task.order_code,
    title: ident.display_label,
    display_label: ident.display_label,
    status: task.status as EmployeeMobileTaskDTO["status"],
    process_type: ident.operation_code || undefined,
    assigned_employee_id: assign.assigned_employee_id ?? undefined,
    employee_name: assign.assigned_employee_name ?? undefined,
    client: task.client_label,
    started_at: task.started_at,
    completed_at: task.completed_at,
    blocked_at: task.blocked_at,
    blocked_reason: task.blocked_reason,
    deterministic_task_key: ident.deterministic_task_key ?? undefined,
    component_label: ident.component_label ?? undefined,
    component_role: ident.component_role ?? undefined,
    operation_label: ident.operation_label ?? undefined,
    logo_segment_label: ident.logo_segment_label ?? undefined,
    identity_source: ident.identity_source,
    identity_classification: ident.identity_classification ?? undefined,
    execution_plan_id: task.execution_plan_id ?? undefined,
    plan_sequence: task.plan_sequence ?? undefined,
    legacy_mode: auth?.legacy_fallback_active,
    legacy_fallback_active: auth?.legacy_fallback_active,
    task_identity_version: auth?.task_identity_version ?? undefined,
    readiness_authority: auth?.readiness_authority ?? undefined,
    release_authority: auth?.release_authority ?? undefined,
    execution_source: auth?.execution_source ?? undefined,
    production_release_blocked: ready.production_release_blocked,
    production_blocker_summary: ready.production_blocker_summary ?? undefined,
    is_assigned_to_current_employee: assign.is_assigned_to_current_employee,
    is_available_for_claim: assign.is_available_for_claim,
    can_claim: assign.can_claim,
    claimable: assign.can_claim,
    assignment_source: assign.assignment_source,
    readiness_status: ready.readiness_status ?? undefined,
    readiness_label: ready.readiness_label ?? undefined,
    is_startable: ready.is_startable,
    readiness_reasons: (ready.readiness_reasons ?? []) as EmployeeMobileTaskDTO["readiness_reasons"],
    blocking_task_ids: ready.blocking_task_ids,
    blocking_tasks: ready.blocking_tasks,
    dependency_warning: ready.dependency_warning ?? undefined,
    material_warning: ready.material_warning ?? undefined,
    can_start: ready.can_start,
    can_start_from_available: ready.can_start_from_available,
    can_complete: ready.can_complete,
    access_mode: task.access_mode ?? undefined,
    preview_only: task.preview_only,
  };
}

export function buildEmployeeMobileV2TaskTruthView(
  response: EmployeeMobileTaskTruthResponse & { tasks?: EmployeeMobileTruthTaskNested[] },
): EmployeeMobileV2TaskTruthView {
  const contractVersion = response.contract_version;
  const nested = (response.tasks ?? []) as EmployeeMobileTruthTaskNested[];
  const allTasks = nested.map((task) => truthTaskToDto(task, contractVersion));
  const assignedTasks = allTasks.filter((task) => task.is_assigned_to_current_employee);
  const availableTasks = allTasks.filter((task) => task.is_available_for_claim);
  const inProgressTasks = assignedTasks.filter((task) => task.status === "in_progress");
  return {
    contractVersion,
    employeeId: response.employee_id,
    summary: response.summary,
    assignedTasks,
    availableTasks,
    inProgressTasks,
    allTasks,
  };
}

export function findTruthTaskById(
  view: EmployeeMobileV2TaskTruthView,
  taskId: string,
  orderId: number,
): EmployeeMobileTaskDTO | null {
  return (
    view.allTasks.find((task) => task.task_id === taskId && task.order_id === orderId) ?? null
  );
}

export { mapMobileTaskErrorMessage as mapEmployeeMobileTaskTruthError } from "@/lib/employeeMobileV2TaskErrors";
