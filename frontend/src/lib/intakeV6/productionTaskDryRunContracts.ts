export interface IntakeV4TaskGenerationBlocker {
  code: string;
  severity: string;
  message: string;
  source: string;
}

export interface IntakeV4CandidateTaskInput {
  label: string;
  value: string | number | boolean | null;
  unit?: string | null;
  quality: string;
  availability_status?: string | null;
  procurement_status?: string | null;
}

export interface IntakeV4CandidateTaskDependency {
  from_candidate_task_id: string;
  to_candidate_task_id: string;
  dependency_type: string;
  reason?: string | null;
}

export interface IntakeV4CandidateProductionTask {
  candidate_task_id: string;
  group_key: string;
  title: string;
  description?: string | null;
  operation_type: string;
  station_hint?: string | null;
  department_hint?: string | null;
  is_required: boolean;
  is_conditional: boolean;
  condition_reason?: string | null;
  source_data: string[];
  inputs_preview: IntakeV4CandidateTaskInput[];
  output_preview: string[];
  blocking_issues: string[];
  warnings: string[];
  will_create_real_task: boolean;
  seed_code?: string | null;
  parallel_with?: string[];
}

export interface IntakeV4CandidateTaskGroup {
  group_key: string;
  title: string;
  description?: string | null;
  sort_order: number;
  candidate_task_ids: string[];
  is_required: boolean;
  is_conditional: boolean;
  condition_reason?: string | null;
}

export interface IntakeV4TaskDryRunBoundary {
  dry_run_scope: string;
  would_create_execution_plan: boolean;
  would_create_execution_tasks: boolean;
  creates_execution_plan: boolean;
  creates_execution_tasks: boolean;
  creates_work_sessions: boolean;
  mutates_inventory: boolean;
  starts_production: boolean;
  modifies_order: boolean;
  modifies_quote: boolean;
  costengine_used: boolean;
}

export interface IntakeV4ProductionTaskDryRunSummary {
  candidate_groups_count: number;
  candidate_tasks_count: number;
  blocking_issues_count: number;
  warnings_count: number;
}

export interface IntakeV4ProductionTaskDryRunResponse {
  source_module: string | null;
  source_type: string;
  source_id: string;
  order_id: number | null;
  quote_id: number | null;
  source_workspace_id: string | null;
  is_intake_v3: boolean;
  dry_run_scope: string;
  production_readiness_status: string | null;
  material_breakdown_available: boolean;
  material_availability_available?: boolean;
  material_availability_status?: string | null;
  material_shortage_rows_count?: number;
  material_manual_check_rows_count?: number;
  material_indirect_consumables_count?: number;
  procurement_preview_available?: boolean;
  procurement_preview_status?: string | null;
  procurement_purchase_recommended_count?: number;
  procurement_owner_decision_required_count?: number;
  procurement_advance_recommended_count?: number;
  procurement_manual_check_count?: number;
  geometry_snapshot_available: boolean;
  geometry_status: string;
  can_generate_real_tasks_now: boolean;
  would_create_execution_plan: boolean;
  would_create_execution_tasks: boolean;
  creates_execution_plan: boolean;
  creates_execution_tasks: boolean;
  creates_work_sessions: boolean;
  mutates_inventory: boolean;
  starts_production: boolean;
  modifies_order: boolean;
  modifies_quote: boolean;
  costengine_used: boolean;
  boundary: IntakeV4TaskDryRunBoundary;
  summary: IntakeV4ProductionTaskDryRunSummary;
  candidate_task_groups: IntakeV4CandidateTaskGroup[];
  candidate_tasks: IntakeV4CandidateProductionTask[];
  dependencies: IntakeV4CandidateTaskDependency[];
  blockers: IntakeV4TaskGenerationBlocker[];
  warnings: IntakeV4TaskGenerationBlocker[];
  future_builds: string[];
}

export type IntakeV6TaskGenerationBlocker = IntakeV4TaskGenerationBlocker;
export type IntakeV6CandidateTaskInput = IntakeV4CandidateTaskInput;
export type IntakeV6CandidateTaskDependency = IntakeV4CandidateTaskDependency;
export type IntakeV6CandidateProductionTask = IntakeV4CandidateProductionTask;
export type IntakeV6CandidateTaskGroup = IntakeV4CandidateTaskGroup;
export type IntakeV6TaskDryRunBoundary = IntakeV4TaskDryRunBoundary;
export type IntakeV6ProductionTaskDryRunSummary = IntakeV4ProductionTaskDryRunSummary;
export type IntakeV6ProductionTaskDryRunResponse = IntakeV4ProductionTaskDryRunResponse;
