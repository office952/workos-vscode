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

export interface IntakeV6ModularFormFieldBinding {
  canonical_key: string;
  workspace_path: string;
  label_ro?: string | null;
  required?: boolean;
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
  warnings?: string[];
}

export interface IntakeV6ModularFormContractResponse {
  summary: IntakeV6ModularFormContractSummary;
  modules: IntakeV6ModularFormModuleSection[];
  field_bindings: IntakeV6ModularFormFieldBinding[];
  trigger_alignments: IntakeV6ModularTriggerAlignment[];
  valid_combinations?: string[];
  invalid_combinations?: string[];
  orphan_fields_audit?: string[];
  notes?: string[];
}
