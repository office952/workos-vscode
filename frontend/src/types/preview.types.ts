/**
 * S30 — ProductSystem Execution Preview types (read-only).
 *
 * Strict mirror of backend contract from:
 *   GET /api/v1/product_system/preview/{order_id}
 *
 * These types are consumed by the read-only UI visibility layer.
 * No mutation types exist here — the UI only reads.
 */

export interface GeneratedOperation {
  operation_id: string;
  task_type: string;
  sequence_index: number;
  depends_on_operation_ids: string[];
  component_id: string | null;
  description: string | null;
}

export interface GeneratedTaskRequirement {
  task_template_id: string;
  source_operation_id: string;
  task_type: string;
  required_skill_ids: string[];
  required_workcenter_id: string | null;
  required_machine_type: string | null;
  required_machine_id: string | null;
  material_requirements: Record<string, unknown>[];
  estimated_duration: Record<string, unknown>;
}

export interface PreviewMissingLink {
  field: string;
  task_template_id: string;
  reason: string;
  available_today: boolean;
}

export interface PreviewTraceSource {
  registries_consulted: string[];
  registries_unavailable: string[];
  template_resolved_at: string;
  linkage_validation_run: boolean;
  linkage_blockers_count: number;
  linkage_warnings_count: number;
}

export interface ProductSystemExecutionPreview {
  order_id: number;
  order_code: string;
  template_code: string;
  template_version: string | null;
  generated_operations: GeneratedOperation[];
  generated_task_requirements: GeneratedTaskRequirement[];
  missing_links: PreviewMissingLink[];
  blockers: Record<string, unknown>[];
  warnings: Record<string, unknown>[];
  trace_source: PreviewTraceSource;
}