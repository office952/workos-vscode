/** Read-only types for GET /api/v1/intake-v6/form-contract/{template_code} (Step 5A/5B). */

export type IntakeV6ModularOperationalStatus =
  | "ACTIVE_OPERATIONAL"
  | "READONLY_EXPLANATORY"
  | "FUTURE_RESERVED_STEP_6"
  | "FUTURE_RESERVED_STEP_7"
  | "FUTURE_RESERVED_STEP_8"
  | "FUTURE_RESERVED_STEP_9"
  | "DEAD_PIECE_REMOVE_OR_APPROVE";

export type IntakeV6ModularActivationKind =
  | "always_on"
  | "required_module"
  | "optional_addon"
  | "conditional_gate";

export type IntakeV6ModularFieldRole =
  | "module_activation"
  | "module_configuration"
  | "geometry_input"
  | "product_definition_key"
  | "derived_quote_input"
  | "readonly_computed";

export interface IntakeV6FormOption {
  value: string;
  label_ro: string;
}

export interface IntakeV6VisibilityRule {
  kind?: "always" | "equals" | "not_equals" | "in_set" | "truthy" | "falsy" | null;
  workspace_path?: string | null;
  value?: unknown;
  values?: unknown[] | null;
}

export interface IntakeV6ModularFormFieldBinding {
  canonical_key: string;
  workspace_path: string;
  label_ro?: string | null;
  required?: boolean;
  field_type?: string | null;
  unit?: string | null;
  option_values?: string[] | null;
  options?: IntakeV6FormOption[] | null;
  visibility_rule?: string | null;
  visibility?: IntakeV6VisibilityRule | null;
  min_value?: number | null;
  max_value?: number | null;
  read_only?: boolean;
  display_mode?: string | null;
  decision?: string | null;
  consumers?: string[];
  field_role?: IntakeV6ModularFieldRole;
  module_codes?: string[];
  operational_status?: IntakeV6ModularOperationalStatus;
  product_definition_keys?: string[];
  aggregate_trace?: string[];
  cost_engine_step?: string | null;
  derived_from?: string | null;
  derivation_rule?: string | null;
  notes?: string[];
}

export interface IntakeV6RenderSection {
  section_key: string;
  title_ro: string;
  order: number;
  description_ro?: string | null;
  module_codes?: string[];
  field_keys?: string[];
  visibility?: IntakeV6VisibilityRule | null;
  pilot_role?: string | null;
}

export interface IntakeV6ModularFormModuleSection {
  module_code: string;
  module_name: string;
  operational_status: IntakeV6ModularOperationalStatus;
  activation_kind: IntakeV6ModularActivationKind;
  intake_trigger_fields?: string[];
  consumed_form_fields?: string[];
  required_form_fields?: string[];
  optional_form_fields?: string[];
  product_definition_outputs?: string[];
  valid_when?: string[];
  invalid_when?: string[];
  warnings?: string[];
}

export interface IntakeV6ModularTriggerAlignment {
  module_code: string;
  module_link_trigger_field: string;
  canonical_intake_field: string;
  derived_quote_input_key?: string | null;
  derivation_rule?: string | null;
  warning_code?: string;
  backwards_compatible?: boolean;
  resolution_owner_step?: number;
  notes?: string[];
}

export interface IntakeV6ModularFormContractSummary {
  contract_version?: string;
  template_code: string;
  registry_version?: string;
  active_module_count?: number;
  field_binding_count?: number;
  /** Full form authority — false for Letters; see runtime_authority_scope. */
  runtime_authority?: boolean;
  /** Bounded surface, e.g. review_labels — not full dynamic form generation. */
  runtime_authority_scope?: string | null;
  warnings?: string[];
}

export interface FormSystemBackboneRoot {
  requested_code?: string | null;
  code?: string | null;
  canonical_code?: string | null;
  root_type?: string | null;
  quote_mode?: string | null;
  offerability_status?: string | null;
  canonical_alias_resolution?: boolean | null;
  allowed?: boolean | null;
  blocked?: boolean | null;
  blocker_code?: string | null;
  reason?: string | null;
}

export interface FormSystemBackboneComponent {
  component_key?: string | null;
  label?: string | null;
  component_template_code?: string | null;
  module_code?: string | null;
  coverage?: string | null;
  role?: string | null;
  notes?: string | null;
}

export interface FormSystemBackboneField {
  field_key?: string | null;
  operator_label?: string | null;
  owning_component?: string | null;
  component_template_code?: string | null;
  source_type?: string | null;
  state?: string | null;
  product_truth_path?: string | null;
  missing_target_path?: string | null;
  required_for?: string[];
  blocker_code?: string | null;
  notes?: string | null;
}

export interface FormSystemBackboneBlocker {
  field_key?: string | null;
  owning_component?: string | null;
  blocker_code?: string | null;
  state?: string | null;
  blocks?: string[];
  message?: string | null;
  severity?: string | null;
}

export interface FormSystemBackboneReadiness {
  status?: string | null;
  blockers?: FormSystemBackboneBlocker[];
  operator_confirmation_required?: string[];
  suggestions_allowed?: string[];
  fallback_or_hydrated_not_confirmed?: string[];
  downstream_later?: string[];
}

export interface FormSystemBackboneContract {
  contract_version?: string | null;
  read_only?: boolean | null;
  root?: FormSystemBackboneRoot | null;
  components?: FormSystemBackboneComponent[];
  fields?: FormSystemBackboneField[];
  readiness?: FormSystemBackboneReadiness | null;
  blockers?: FormSystemBackboneBlocker[];
  downstream_write_intent?: Record<string, boolean>;
  notes?: string[];
}

export interface IntakeV6ModularFormContractResponse {
  summary: IntakeV6ModularFormContractSummary;
  modules: IntakeV6ModularFormModuleSection[];
  field_bindings: IntakeV6ModularFormFieldBinding[];
  render_sections?: IntakeV6RenderSection[];
  writable_workspace_paths?: string[];
  form_system_backbone?: FormSystemBackboneContract | null;
  trigger_alignments: IntakeV6ModularTriggerAlignment[];
  valid_combinations?: string[];
  invalid_combinations?: string[];
  orphan_fields_audit?: string[];
  notes?: string[];
}
