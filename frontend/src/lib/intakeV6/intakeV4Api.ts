/**
 * Intake V4 API — own contract, decoupled from Intake V3 workspace form.
 */

import type { IntakeV4ProductionTaskDryRunResponse } from "@/lib/intakeV6/productionTaskDryRunContracts";
import { getAPIBaseURL } from "@/lib/config";

const apiBase = () => {
  const pathname = globalThis.location?.pathname ?? "";
  const intakeVersion = pathname.startsWith("/intake-v6") || pathname.startsWith("/intake-v6-app")
    ? "intake-v6"
    : "intake-v4";
  return `${getAPIBaseURL()}/api/v1/${intakeVersion}`;
};

export type IntakeV4WorkspaceDraftStatus =
  | "draft"
  | "collecting_data"
  | "blocked"
  | "ready_for_quote_preview"
  | "archived";

export interface IntakeV4WorkspaceResponse {
  id: string;
  workspace_code: string;
  title: string;
  template_code: string;
  status: IntakeV4WorkspaceDraftStatus;
  payload: Record<string, unknown>;
  readiness_status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface IntakeV4LayerRoleLayer {
  layer_key: string;
  layer_id?: string | null;
  layer_name?: string | null;
  auto_role: string;
  auto_confidence: string;
  confirmed_role?: string | null;
  confirmation_state: "pending" | "confirmed" | "ignored";
  operator_note?: string | null;
  path_count?: number | null;
  dominant_fill?: string | null;
}

export interface IntakeV4LayerRoleSetup {
  confirmation_status: "missing" | "partial" | "complete";
  layers: IntakeV4LayerRoleLayer[];
  warnings: string[];
}

export interface IntakeV4SvgUploadResponse {
  workspace: IntakeV4WorkspaceResponse;
  layer_role_setup: IntakeV4LayerRoleSetup;
  warnings: string[];
}

export interface IntakeV4ProductSystemBindingResponse {
  workspace_id: string;
  template_code: string;
  template_id?: number | null;
  template_label?: string | null;
  product_family?: string | null;
  product_family_name?: string | null;
  operation_count: number;
  component_count: number;
  template_active: boolean;
  module_links: Array<{
    module_template_id?: number | null;
    module_template_code: string;
    module_template_label?: string | null;
    relation_type: string;
    trigger_field: string;
    trigger_value?: unknown;
    input_mapping: Record<string, unknown>;
    default_values: Record<string, unknown>;
    pricing_mode: string;
    execution_mode: string;
    active: boolean;
    notes?: string | null;
  }>;
  blockers: string[];
}

export interface IntakeV4TemplateContractCanonicalRow {
  discovered_option: string;
  blueprint_rule: string;
  template_option: string;
  material_intent: string;
  pricing_code_blk18: string;
  costengine_field: string;
  production_material_job: string;
  production_operation_group: string;
  future_task_seed: string;
  status: "aligned" | "partial" | "missing" | "provisional";
  notes: string;
}

export interface IntakeV4TemplateContractIssue {
  code: string;
  severity: "blocking" | "warning" | "info";
  message: string;
  source: string;
  option_key?: string | null;
}

export interface IntakeV4TemplateFormContractField {
  field_key: string;
  label: string;
  owner: "product_system_dossier" | "intake_v4_operator" | "pricing_registry" | "quote_wizard";
  current_runtime_owner: "product_system_dossier" | "intake_v4_hardcoded_form" | "quote_wizard_default";
  alignment_status: "canonical" | "mapped" | "adapter_only" | "missing_in_v4";
  allowed_values: unknown[];
  default_value?: unknown;
  v4_field_key?: string | null;
  source: string;
  notes: string[];
}

export interface IntakeV4TemplateFormContractResponse {
  workspace_id: string;
  template_code: string;
  contract_version: string;
  intended_form_authority: string;
  current_runtime_authority: string;
  alignment_status: "aligned" | "partial" | "blocked";
  template_active: boolean;
  dossier_status?: string | null;
  dossier_source: "product_blueprint_dossier" | "static_contract_fallback";
  ui_must_not_invent_final_options: boolean;
  variant_fields: IntakeV4TemplateFormContractField[];
  canonical_rows: IntakeV4TemplateContractCanonicalRow[];
  warnings: IntakeV4TemplateContractIssue[];
  blockers: IntakeV4TemplateContractIssue[];
  discovered_v4_values: Record<string, unknown>;
}

export interface IntakeV4TaskPreviewItem {
  operation_code: string;
  label: string;
  workcenter?: string | null;
  sequence: number;
  component_ref?: string | null;
  active: boolean;
  inactive_reason?: string | null;
  source: "product_system" | "operation_catalog";
  depends_on?: string[];
  required_skill?: string[];
  active_reason?: string | null;
  operator_instruction?: string | null;
}

export interface IntakeV4ArtworkComplexityDecision {
  artwork_id: string;
  operator_application: "vinyl_cut" | "print_on_vinyl_laminated" | "manual_review";
  accepted_system_recommendation: boolean;
  override_manual_vinyl_cut: boolean;
  operator_note?: string | null;
}

export interface IntakeV4CommercialInputsPayload {
  markup_percent?: number | null;
  discount_percent?: number | null;
  vat_percent?: number | null;
  manual_adjustment_ron?: number | null;
}

export interface IntakeV4FinishSetup {
  face_finish_type?: string | null;
  face_vinyl_roll_width_mm?: number | null;
  return_finish_type?: string | null;
  volum_aluminum_module_template_code?: string | null;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  illuminated?: boolean;
  lighting_system_type?: string | null;
  light_color?: string | null;
  led_module_power_w?: number | null;
  led_strip_power_w_per_ml?: number | null;
  led_module_count?: number | null;
  letter_led_strip_length_m?: number | null;
  emblem_led_strip_length_m?: number | null;
  total_led_strip_length_m?: number | null;
  estimated_led_watts?: number | null;
  required_psu_watts?: number | null;
  psu_configuration?: number[];
  psu_allocation_status?: string | null;
  selected_psu_watts?: number | null;
  letter_group_finishes?: IntakeV4LetterGroupFinish[];
  artwork_finishes?: IntakeV4ArtworkFinish[];
  artwork_complexity_decisions?: IntakeV4ArtworkComplexityDecision[];
  backing_mode?: "none" | "forex_10_no_bevel" | "forex_10_with_bevel";
  back_bevel_enabled?: boolean | null;
  mounting_template_enabled?: boolean | null;
  mounting_template_area_m2?: number | null;
  mounting_template_material_type?: "forex" | "paper" | null;
  mounting_system?: "direct_wall" | "steel_bars" | "aluminum_bars" | "acm_panel" | null;
  mounting_bar_profile?: string | null;
  mounting_scope?:
    | "none"
    | "preparation_only"
    | "preparation_and_site_installation"
    | "no_mounting"
    | "mounting_included"
    | "mounting_external"
    | "to_be_decided"
    | null;
  site_installation_included?: boolean | null;
  mounting_solution?: {
    kind?: string;
    template_code: string | null;
    configuration?: Record<string, unknown>;
  } | null;
  /** Operator-confirmed SVG closed-contour support selection (Alucobond panel etc.). */
  svg_support_selection?: Record<string, unknown> | null;
  /** Unified Product System component bindings (letters / logo / support). */
  svg_component_bindings?: Record<string, unknown>[] | null;
  /** Typed process config — Intake → ProductDefinition → modular resolver (not pricing). */
  mains_cable_length_m?: number | null;
  power_supply_service_corner?:
    | "TOP_LEFT"
    | "TOP_RIGHT"
    | "BOTTOM_LEFT"
    | "BOTTOM_RIGHT"
    | "MANUAL_CONFIRMED"
    | null;
  service_screw_finish?: "NATURAL" | "PAINTED_TO_MATCH_CANT" | null;
  emblem_lighting_mode?: "excluded" | "area_lit" | "needs_decision";
  letter_led_module_count?: number | null;
  emblem_led_module_count?: number | null;
  total_led_module_count?: number | null;
  commercial_inputs?: IntakeV4CommercialInputsPayload | null;
  confirmed?: boolean;
}

export interface IntakeV4LetterGroupFinish {
  group_key: string;
  layer_name?: string | null;
  source_fill_color?: string | null;
  face_area_m2?: number | null;
  perimeter_m?: number | null;
  element_count?: number | null;
  face_finish_type?: string | null;
  face_oracal_code?: string | null;
  face_oracal_name?: string | null;
  return_finish_type?: string | null;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  face_vinyl_roll_width_mm?: number | null;
  confirmed?: boolean;
}

export interface IntakeV4ArtworkFinish {
  layer_key: string;
  layer_name?: string | null;
  execution_type?: string | null;
  color_mode?: string | null;
  print_transparency?: "standard" | "translucent" | "transparent";
  material_code?: string | null;
  estimated_area_m2?: number | null;
  element_count?: number | null;
  distinct_fill_count?: number | null;
  return_finish_type?: string | null;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  confirmed?: boolean;
}

export interface IntakeV4NestingMaterialRow {
  material_key: string;
  display_name: string;
  nesting_kind: "sheet" | "roll";
  config_id?: string | null;
  source_layer?: string | null;
  quantity: number;
  unit: string;
  efficiency_percent?: number | null;
  waste_area_sqm?: number | null;
  sheets_used?: number | null;
  consumed_length_mm?: number | null;
}

export interface IntakeV4MaterialQuantityRow {
  material_key: string;
  display_name: string;
  category: "material" | "consumable" | "nesting";
  quantity: number;
  unit: string;
  quantity_source: string;
  quantity_quality: string;
  waste_percent?: number | null;
  quantity_with_waste: number;
  registry_code?: string | null;
  unit_price?: number | null;
  currency: string;
  material_cost?: number | null;
  price_source: string;
  warnings: string[];
  material_code?: string | null;
  material_name?: string | null;
  quantity_basis?: string | null;
  base_quantity?: number | null;
  priced_quantity?: number | null;
  estimated_cost?: number | null;
  confidence?: string;
  consumption_mode?: "quote_estimate";
}

export interface IntakeV4NestingPreviewResponse {
  preview_mode: "bounding_box_mvp";
  preview_only: boolean;
  mutates_inventory: boolean;
  uses_stock: boolean;
  source: string;
  workspace_id?: string | null;
  disclaimer: string;
  active_sheet_config_id: string | null;
  breakdown_uses_single_active_layout: boolean;
  boundary: {
    preview_only: boolean;
    mutates_inventory: boolean;
    uses_stock: boolean;
    creates_execution_plan: boolean;
    creates_execution_tasks: boolean;
    consumes_stock: boolean;
    used_for_stock_reservation: boolean;
  };
  summary: {
    sheet_layouts: number;
    roll_layouts: number;
    active_sheet_layouts: number;
    active_roll_layouts: number;
    alternative_layouts: number;
    nestable_parts: number;
    holes_excluded: number;
    artwork_parts: number;
  };
  sheets: Array<{
    config_id: string;
    display_label: string;
    sheet_width_mm: number | null;
    sheet_length_mm: number | null;
    material_target: string | null;
    sheets_used: number;
    used_sheet_area_sqm: number | null;
    parts_bounding_area_sqm: number | null;
    efficiency_percent: number | null;
    placed_items_count: number;
    unplaced_items_count: number;
    placement_count: number;
    is_active_for_breakdown: boolean;
    layout_kind: "active_breakdown" | "alternative_variant";
    breakdown_note: string | null;
  }>;
  rolls: Array<{
    roll_config_id: string;
    roll_width_mm: number | null;
    source_layer_name: string | null;
    layer_role: string | null;
    color_key: string | null;
    used_roll_area_sqm: number | null;
    consumed_length_mm: number | null;
    placed_items_count: number;
    efficiency_percent: number | null;
    is_active_for_breakdown: boolean;
    layout_kind: "active_breakdown" | "alternative_variant";
    material_target: string | null;
  }>;
  parts: Array<{
    part_id: string;
    source_layer_name: string | null;
    layer_role: string | null;
    part_kind?: "face_part" | "artwork_part" | "hole" | "backing_part" | "unknown";
    material_intent: "face" | "backing" | null;
    nestable?: boolean;
    counts_as_material_piece?: boolean;
    bounds_width_mm: number | null;
    bounds_height_mm: number | null;
    area_sqm: number | null;
    perimeter_ml: number | null;
    nesting_target: string | null;
    placement_x_mm: number | null;
    placement_y_mm: number | null;
    counted_in_material_lines: string[];
    preview_shape: "bounding_box";
  }>;
  material_traces: Array<{
    material_key: string;
    display_name: string;
    reported_quantity: number;
    unit: string;
    quantity_basis: string | null;
    quantity_source: string | null;
    source_part_ids: string[];
    active_sheet_config_id: string | null;
    breakdown_mode: string | null;
    uses_placement_footprint: boolean;
    uses_full_sheet_stock_proration: boolean;
  }>;
  warnings: Array<{ code: string; severity: string; message: string }>;
}

export interface IntakeV4CncOperationRow {
  key: string;
  display_name: string;
  operation_type: string;
  material_family?: string | null;
  material_name?: string | null;
  thickness_mm?: number | null;
  quantity: number;
  unit: string;
  basis_key?: string;
  basis_label?: string;
  passes?: number;
  depth_per_pass_mm?: number | null;
  owner_pass_override?: boolean;
  operation_equivalent_quantity?: number | null;
  operation_equivalent_unit?: string | null;
  pricing_rate_key?: string | null;
  unit_price?: number | null;
  estimated_cost?: number | null;
  pricing_status?: string;
  tpl_operation_key?: string | null;
  dossier_operation_key?: string | null;
  operation_catalog_key?: string | null;
  production_task_type?: string | null;
  workstation_key?: string | null;
  required_skill_key?: string | null;
  registry_skill_code?: string | null;
  machine_type?: string | null;
  required_machine_key?: string | null;
  workcenter_code?: string | null;
  operational_operation_code?: string | null;
  resource_mapping_status?: "mapped" | "pending_mapping";
  mapping_gaps?: string[];
  material_key?: string | null;
  consumes_stock_now?: boolean;
  creates_task_now?: boolean;
  warnings?: string[];
}

export interface IntakeV4EdgeCantOperationRow extends IntakeV4CncOperationRow {
  source?: string;
}

export type IntakeV4FaceBackPrepComponentKey = "FACE_PLEXI" | "BACK_FOREX" | "GENERAL";

export type IntakeV4FaceBackPrepCostRowStatus =
  | "calculated"
  | "missing_price"
  | "manual_required"
  | "optional"
  | "calculated_when_enabled"
  | "skipped";

export type IntakeV4FaceBackPrepPerimeterConfidence = "high" | "derived_candidate" | "manual_required";

export interface IntakeV4FaceBackPrepMaterialCostRow {
  component: IntakeV4FaceBackPrepComponentKey;
  material_key: string;
  material_label: string;
  registry_code?: string | null;
  thickness_mm: number;
  quantity: number;
  unit: "sqm";
  unit_price?: number | null;
  currency: string;
  price_source: string;
  cost?: number | null;
  status: IntakeV4FaceBackPrepCostRowStatus;
}

export interface IntakeV4FaceBackPrepOperationCostRow {
  operation_key: string;
  label: string;
  component: IntakeV4FaceBackPrepComponentKey;
  task_key: string;
  quantity: number;
  unit: "ml";
  unit_price?: number | null;
  pass_count: number;
  currency: string;
  price_source: string;
  cost?: number | null;
  status: IntakeV4FaceBackPrepCostRowStatus;
  perimeter_source?: string | null;
  perimeter_confidence?: IntakeV4FaceBackPrepPerimeterConfidence | null;
  is_vector_perimeter_source: boolean;
}

export interface IntakeV4FaceBackPrepTaskDraft {
  task_key: string;
  label: string;
  station: string;
  component: IntakeV4FaceBackPrepComponentKey;
  order_index: number;
  depends_on: string[];
  cost_rows: string[];
  creates_real_task: boolean;
  preview_only: boolean;
}

export interface IntakeV4FaceBackPrepCostDraftTotals {
  material_cost?: number | null;
  operation_cost?: number | null;
  total_internal_cost?: number | null;
  currency: string;
}

export interface IntakeV4FaceBackPrepCostDraftWarning {
  code: string;
  message: string;
  severity: "info" | "warning" | "error";
  source?: string | null;
}

export interface IntakeV4FaceBackPrepCostDraftResponse {
  workspace_id?: string | null;
  template_key: string;
  version: string;
  preview_only: boolean;
  currency: string;
  materials: IntakeV4FaceBackPrepMaterialCostRow[];
  operations: IntakeV4FaceBackPrepOperationCostRow[];
  task_drafts: IntakeV4FaceBackPrepTaskDraft[];
  totals: IntakeV4FaceBackPrepCostDraftTotals;
  missing_prices: string[];
  manual_inputs_required: string[];
  warnings: IntakeV4FaceBackPrepCostDraftWarning[];
  creates_real_tasks: boolean;
  consumes_stock: boolean;
  creates_quote: boolean;
  cnc_rate_eur_per_ml: number;
}

export interface IntakeV4MaterialBreakdownResponse {
  workspace_id: string;
  template_code: string;
  breakdown_scope: string;
  costing_purpose?: string;
  consumption_mode?: string;
  policy_version?: string;
  quote_waste_percent_default?: number;
  stock_consumption?: boolean;
  nesting_rows: IntakeV4NestingMaterialRow[];
  material_rows: IntakeV4MaterialQuantityRow[];
  consumable_rows: IntakeV4MaterialQuantityRow[];
  operation_rows?: IntakeV4CncOperationRow[];
  edge_cant_operation_rows?: IntakeV4EdgeCantOperationRow[];
  nesting_preview?: IntakeV4NestingPreviewResponse | null;
  totals: {
    material_cost_total: number;
    estimated_cost_total?: number;
    currency: string;
    contains_estimates: boolean;
    contains_missing_prices: boolean;
  };
  warnings: Array<{ code: string; severity: string; message: string; source: string }>;
  sheet_quote_material_candidates?: IntakeV4SheetQuoteMaterialCandidates | null;
}

export interface IntakeV4SheetQuoteRecommendedAutoCandidate {
  source?: string;
  area_sqm?: number | null;
  buffer_percent?: number;
  confidence?: "low" | "medium" | "high";
  reason?: string;
}

export interface IntakeV4SheetQuoteSelectionPreview {
  selected_source?: string;
  final_area_sqm?: number | null;
  selection_mode?: "current_floor" | "auto_candidate_preview" | "manual_override_preview";
  is_applied_to_quote?: boolean;
}

export interface IntakeV4SheetQuoteOperatorOverridePreview {
  enabled?: boolean;
  width_cm?: number | null;
  height_cm?: number | null;
  area_sqm?: number | null;
  note?: string | null;
}

export interface IntakeV4SheetQuoteMaterialCandidates {
  eligible_face_area_sqm?: number | null;
  placement_footprint_face_sqm?: number | null;
  face_union_bbox_sqm?: number | null;
  layout_occupied_area_sqm?: number | null;
  full_sheet_allocation_sqm?: number | null;
  unknown_placement_sqm?: number | null;
  orphan_defs_split_placement_sqm?: number | null;
  operator_manual_footprint_sqm?: number | null;
  operator_manual_footprint_width_cm?: number | null;
  operator_manual_footprint_height_cm?: number | null;
  operator_manual_use_for_quote_estimate?: boolean;
  selected_quote_sheet_area_sqm?: number | null;
  selected_quote_sheet_area_source?: string | null;
  child_part_bbox_sum_sqm?: number | null;
  semantic_group_bbox_sum_sqm?: number | null;
  design_space_union_bbox_sqm?: number | null;
  design_space_union_bbox_with_buffer_sqm?: number | null;
  nesting_shelf_occupied_sqm?: number | null;
  recommended_auto_candidate?: IntakeV4SheetQuoteRecommendedAutoCandidate | null;
  requires_manual_review?: boolean;
  manual_review_reason?: string | null;
  operator_override?: IntakeV4SheetQuoteOperatorOverridePreview | null;
  selection?: IntakeV4SheetQuoteSelectionPreview | null;
}

export interface IntakeV4SheetFootprintOverrideRequest {
  selected_footprint_source: string;
  width_cm?: number;
  height_cm?: number;
  reason?: string;
  applies_to?: string[];
  use_for_quote_estimate?: boolean;
}

export interface IntakeV4SheetFootprintOverrideResponse {
  enabled: boolean;
  source: "operator_manual_footprint";
  selected_footprint_source?: string | null;
  width_cm?: number | null;
  height_cm?: number | null;
  area_sqm?: number | null;
  reason?: string;
  applies_to?: string[];
  use_for_quote_estimate: boolean;
  created_by?: string | null;
  created_at?: string | null;
}

export interface IntakeV4TaskPreviewResponse {
  workspace_id: string;
  template_code: string;
  items: IntakeV4TaskPreviewItem[];
  preview_only: boolean;
  operation_flags?: Record<string, boolean> | null;
  preview_engine?: string;
}

export interface IntakeV4PricingInputPreviewResponse {
  workspace_id: string;
  template_code: string;
  is_ready_for_quote: boolean;
  adapter_status: string;
  adapter_blockers: string[];
  adapter_warnings: string[];
  quote_input_payload: Record<string, unknown>;
  operation_flags: Record<string, unknown>;
  production_counts: {
    letter_count?: number | null;
    cut_contour_count?: number | null;
    inner_hole_count?: number | null;
  };
  finish_summary: Record<string, unknown>;
  readiness_status?: string | null;
  requires_grouped_finish_review: boolean;
  preview_only: boolean;
}

export interface IntakeV4ProductionHandoffMaterialJob {
  job_key: string;
  material_code?: string | null;
  role?: string | null;
  display_name: string;
  quantity_basis?: string | null;
  quantity: number;
  priced_quantity?: number | null;
  waste_percent?: number | null;
  unit: string;
  source: string;
  confidence: string;
  creates_stock_reservation: boolean;
  quote_estimate_only: boolean;
  warnings: string[];
}

export interface IntakeV4ProductionHandoffOperationGroup {
  group_key: string;
  title: string;
  description?: string | null;
  station_hint?: string | null;
  operation_codes: string[];
  legacy_operation_codes?: string[];
  material_job_keys: string[];
  canonical_operation_keys?: string[];
  operation_code_source?: "product_system_dossier" | "operation_catalog_compat";
  template_alignment?: {
    status: "aligned" | "partial" | "missing" | "not_applicable";
    provisional: boolean;
    source: string;
    missing_keys: string[];
    partial_keys: string[];
  } | null;
  active: boolean;
  inactive_reason?: string | null;
}

export interface IntakeV4ProductionHandoffTaskSeedPreview {
  task_key: string;
  title: string;
  operation_code: string;
  legacy_operation_code?: string | null;
  canonical_operation_key?: string | null;
  canonical_operation_keys?: string[];
  dossier_operation_key?: string | null;
  future_execution_task_type?: string | null;
  operation_code_source?: "product_system_dossier" | "operation_catalog_compat";
  station_hint?: string | null;
  role_hint?: string | null;
  depends_on: string[];
  source_material_jobs: string[];
  creates_execution_task: boolean;
  active: boolean;
  inactive_reason?: string | null;
  notes: string[];
}

export interface IntakeV4ProductionHandoffIssue {
  code: string;
  severity: "blocking" | "warning" | "info";
  message: string;
  source: string;
}

export interface IntakeV4ProductionHandoffSummary {
  material_jobs_count?: number;
  operation_groups_count?: number;
  task_seed_preview_count?: number;
  blockers_count?: number;
  warnings_count?: number;
  has_material_breakdown?: boolean;
  cnc_task_source?: string | null;
  compat_cnc_mapping_used?: boolean;
  legacy_cnc_mapping_used?: boolean;
  cnc_operation_candidate_count?: number;
  edge_cant_task_source?: string | null;
  edge_cant_operation_candidate_count?: number;
  template_operation_alignment?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface IntakeV4EdgeCantOperationDryRunCandidate {
  candidate_key: string;
  title: string;
  operation_key: string;
  operation_type: string;
  material_key?: string | null;
  material_label?: string | null;
  quantity: number;
  unit: string;
  operation_equivalent_quantity?: number | null;
  passes: number;
  owner_pass_override: boolean;
  basis_label: string;
  pricing_status: string;
  estimated_cost?: number | null;
  required_machine_key?: string | null;
  machine_type?: string | null;
  workstation_key?: string | null;
  required_skill_key?: string | null;
  registry_skill_code?: string | null;
  operation_catalog_key?: string | null;
  dossier_operation_key?: string | null;
  tpl_operation_key?: string | null;
  production_task_type?: string | null;
  resource_mapping_status?: "mapped" | "pending_mapping";
  mapping_gaps: string[];
  consumes_stock_now: boolean;
  creates_task_now: boolean;
  source: string;
  warnings: string[];
}

export interface IntakeV4CncOperationDryRunCandidate {
  candidate_key: string;
  title: string;
  operation_key: string;
  operation_type: string;
  material_key?: string | null;
  material_label?: string | null;
  quantity: number;
  unit: string;
  operation_equivalent_quantity?: number | null;
  passes: number;
  owner_pass_override: boolean;
  basis_label: string;
  pricing_status: string;
  estimated_cost?: number | null;
  required_machine_key?: string | null;
  machine_type?: string | null;
  workstation_key?: string | null;
  required_skill_key?: string | null;
  registry_skill_code?: string | null;
  operation_catalog_key?: string | null;
  dossier_operation_key?: string | null;
  tpl_operation_key?: string | null;
  production_task_type?: string | null;
  resource_mapping_status?: "mapped" | "pending_mapping";
  mapping_gaps: string[];
  consumes_stock_now: boolean;
  creates_task_now: boolean;
  source: string;
  warnings: string[];
}

export interface IntakeV4ProductionHandoffPreviewResponse {
  workspace_id: string;
  template_code: string;
  handoff_mode: "preview_only";
  stock_consumption: boolean;
  creates_execution_tasks: boolean;
  creates_stock_reservations: boolean;
  quote_estimate_only: boolean;
  production_notes: string[];
  material_jobs: IntakeV4ProductionHandoffMaterialJob[];
  operation_groups: IntakeV4ProductionHandoffOperationGroup[];
  task_seed_preview: IntakeV4ProductionHandoffTaskSeedPreview[];
  cnc_operation_candidates?: IntakeV4CncOperationDryRunCandidate[];
  cnc_task_source?: string | null;
  compat_cnc_mapping_used?: boolean;
  legacy_cnc_mapping_used?: boolean;
  edge_cant_operation_candidates?: IntakeV4EdgeCantOperationDryRunCandidate[];
  edge_cant_task_source?: string | null;
  blockers: IntakeV4ProductionHandoffIssue[];
  warnings: IntakeV4ProductionHandoffIssue[];
  summary: IntakeV4ProductionHandoffSummary;
}

export type IntakeV4AiSemanticSuggestedKind =
  | "letters"
  | "logo_or_emblem"
  | "artwork"
  | "shape_symbol"
  | "mixed"
  | "unknown";

export interface IntakeV4AiSemanticClassificationBoundaryFlags {
  is_ai_suggestion: boolean;
  informational_only: boolean;
  requires_operator_confirmation: boolean;
  used_for_pricing: boolean;
  used_for_production: boolean;
  used_for_task_generation: boolean;
  can_create_order: boolean;
  can_create_execution_tasks: boolean;
}

export type IntakeV4AiInformationalSourceContext =
  | "intake_v4_svg_review"
  | "website_chatbot"
  | "website_order_form"
  | "work_intake_internal"
  | "product_template_assist";

export type IntakeV4AiSuggestionCategory =
  | "semantic_classification"
  | "missing_information"
  | "template_recommendation"
  | "client_intake_summary"
  | "production_risk_hint"
  | "material_intent_hint"
  | "file_quality_hint"
  | "question_suggestion"
  | "operator_explanation";

export interface IntakeV4AiInformationalSuggestionItem {
  suggestion_id: string;
  category: IntakeV4AiSuggestionCategory;
  title?: string | null;
  summary?: string | null;
  confidence: number;
  reasons: string[];
  payload: Record<string, unknown>;
  requires_confirmation: boolean;
  boundary_flags: IntakeV4AiSemanticClassificationBoundaryFlags;
}

export interface IntakeV4AiInformationalSuggestionEnvelope {
  schema_version: string;
  source_context: IntakeV4AiInformationalSourceContext;
  suggestions: IntakeV4AiInformationalSuggestionItem[];
  confidence: number;
  requires_confirmation: boolean;
  confirmed_by_user_id?: number | null;
  confirmed_at?: string | null;
  used_for_pricing: boolean;
  used_for_production: boolean;
  used_for_task_generation: boolean;
  writes_business_state: boolean;
  warnings: string[];
}

export interface IntakeV4AiInformationalAssistPreviewResponse {
  workspace_id: string;
  template_code: string;
  preview_only: boolean;
  ai_not_called: boolean;
  context: "intake_v4_svg_review";
  candidate_payload: IntakeV4AiSemanticClassificationCandidatePayload;
  mock_suggestions: IntakeV4AiInformationalSuggestionItem[];
  informational_envelope: IntakeV4AiInformationalSuggestionEnvelope;
  boundary_flags: IntakeV4AiSemanticClassificationBoundaryFlags;
  operator_confirmation_contract: {
    schema_version: string;
    status: "not_persisted" | "draft";
    note?: string | null;
    applies_to_contexts: IntakeV4AiInformationalSourceContext[];
    fields_available_for_future_build: string[];
  };
  mock_suggestion?: IntakeV4AiSemanticClassificationSuggestionResponse | null;
}

export interface IntakeV4AiSemanticClassificationGroupGeometry {
  outer_contours_count: number;
  inner_holes_count: number;
  area_sqm?: number | null;
  outer_perimeter_ml?: number | null;
  inner_hole_perimeter_ml?: number | null;
  cutting_perimeter_ml?: number | null;
  return_perimeter_ml?: number | null;
  bbox_mm?: Record<string, unknown> | null;
}

export interface IntakeV4AiSemanticClassificationGroup {
  group_id: string;
  source_layer: string;
  operator_role: string;
  geometry: IntakeV4AiSemanticClassificationGroupGeometry;
  current_system_classification: {
    counts_as_letters: boolean;
    counts_as_artwork: boolean;
    counts_as_logo: boolean;
  };
}

export interface IntakeV4AiSemanticClassificationCandidatePayload {
  workspace_id: string;
  template_id: string;
  source_file_type: "svg";
  render_preview: {
    available: boolean;
    png_preview_token?: string | null;
    note?: string | null;
  };
  groups: IntakeV4AiSemanticClassificationGroup[];
}

export interface IntakeV4AiSemanticClassificationSuggestion {
  group_id: string;
  suggested_kind: IntakeV4AiSemanticSuggestedKind;
  suggested_text?: string | null;
  suggested_label?: string | null;
  confidence: number;
  reasons: string[];
  requires_operator_confirmation: boolean;
  boundary_flags: IntakeV4AiSemanticClassificationBoundaryFlags;
}

export interface IntakeV4AiSemanticClassificationSuggestionResponse {
  schema_version: string;
  suggestions: IntakeV4AiSemanticClassificationSuggestion[];
  warnings: string[];
}

export interface IntakeV4AiSemanticClassificationPreviewResponse {
  workspace_id: string;
  template_code: string;
  preview_only: boolean;
  ai_not_called: boolean;
  candidate_payload: IntakeV4AiSemanticClassificationCandidatePayload;
  mock_suggestion: IntakeV4AiSemanticClassificationSuggestionResponse;
  boundary_flags: IntakeV4AiSemanticClassificationBoundaryFlags;
  operator_confirmation_contract: {
    schema_version: string;
    status: "not_persisted" | "draft";
    note?: string | null;
    fields_available_for_future_build: string[];
  };
}

export interface IntakeV4TaskGenerationDryRunIssue {
  code: string;
  severity: "blocking" | "warning" | "info";
  message: string;
  source: string;
}

export interface IntakeV4TaskGenerationEstimatedInputs {
  material_codes: string[];
  quantity_basis?: string | null;
  quantity?: number | null;
  unit?: string | null;
  passes?: number | null;
  operation_equivalent_quantity?: number | null;
  owner_pass_override?: boolean | null;
  basis_label?: string | null;
  pricing_status?: string | null;
  preview_source?: string | null;
  required_machine_key?: string | null;
  machine_type?: string | null;
  workstation_key?: string | null;
  required_skill_key?: string | null;
  registry_skill_code?: string | null;
  operation_catalog_key?: string | null;
  mapping_gaps: string[];
  consumes_stock_now: boolean;
  creates_task_now: boolean;
}

export interface IntakeV4TaskGenerationTaskCandidate {
  task_key: string;
  title: string;
  template_code: string;
  template_backed: boolean;
  provisional: boolean;
  provisional_reason?: string | null;
  operation_key?: string | null;
  canonical_operation_key?: string | null;
  template_alignment_status?: "aligned" | "partial" | "missing" | "not_applicable" | null;
  dossier_backed?: boolean;
  critical_for_execution?: boolean;
  future_execution_task_type?: string | null;
  operation_group?: string | null;
  station_hint?: string | null;
  role_hint?: string | null;
  source_material_jobs: string[];
  source_operation_groups: string[];
  estimated_inputs?: IntakeV4TaskGenerationEstimatedInputs;
  depends_on: string[];
  creates_execution_task: boolean;
  idempotency_key: string;
  blockers: string[];
  warnings: string[];
  active: boolean;
  inactive_reason?: string | null;
}

export interface IntakeV4TaskGenerationDependencyEdge {
  from_task_key: string;
  to_task_key: string;
  reason: string;
  confidence: "template_rule" | "catalog_doc" | "provisional";
  provisional: boolean;
}

export interface IntakeV4TaskGenerationIdempotencyEntry {
  task_key: string;
  idempotency_key: string;
  source_fingerprint: string;
  duplicate_policy: string;
}

export interface IntakeV4TaskGenerationDryRunResponse {
  dry_run_mode: "task_generation_preview_only";
  creates_execution_tasks: boolean;
  writes_to_production: boolean;
  stock_consumption: boolean;
  dry_run_only: boolean;
  workspace_id: string;
  template_code: string;
  template_backed: boolean;
  can_generate_tasks: boolean;
  task_candidates: IntakeV4TaskGenerationTaskCandidate[];
  dependency_graph: IntakeV4TaskGenerationDependencyEdge[];
  idempotency_plan: IntakeV4TaskGenerationIdempotencyEntry[];
  blockers: IntakeV4TaskGenerationDryRunIssue[];
  warnings: IntakeV4TaskGenerationDryRunIssue[];
  cnc_task_source?: string | null;
  cnc_operation_candidate_count?: number;
  cnc_operation_candidates?: IntakeV4CncOperationDryRunCandidate[];
  compat_cnc_mapping_used?: boolean;
  legacy_cnc_mapping_used?: boolean;
  edge_cant_task_source?: string | null;
  edge_cant_operation_candidate_count?: number;
  edge_cant_operation_candidates?: IntakeV4EdgeCantOperationDryRunCandidate[];
  summary: Record<string, unknown>;
}

export interface IntakeV4LinkedQuoteSummary {
  exists: boolean;
  quote_id?: number | null;
  quote_code?: string | null;
  status?: string | null;
  requires_pricing_review?: boolean | null;
  snapshot_valid?: boolean;
  analysis_hash_synced?: boolean | null;
}

export interface IntakeV4LinkedOrderSummary {
  exists: boolean;
  order_id?: number | null;
  order_code?: string | null;
  status?: string | null;
  has_execution_plan?: boolean;
  source_quote_id?: number | null;
}

export interface IntakeV4FutureGenerationContract {
  contract_version: string;
  target_entity: "Order";
  target_order_id?: number | null;
  requires_owner_confirmation: boolean;
  requires_idempotency_check: boolean;
  requires_analysis_hash_sync: boolean;
  requires_quote_accepted: boolean;
  requires_order_ready: boolean;
  would_create_execution_tasks: boolean;
  would_write_execution_plan: boolean;
  next_action_label: string;
  next_action_enabled: boolean;
}

export interface IntakeV4OrderBoundTaskReadinessResponse {
  readiness_mode: "order_bound_task_generation_readiness";
  creates_execution_tasks: boolean;
  writes_to_production: boolean;
  stock_consumption: boolean;
  dry_run_only: boolean;
  order_bound_readiness: boolean;
  workspace_id: string;
  template_code: string;
  linked_quote: IntakeV4LinkedQuoteSummary;
  linked_order: IntakeV4LinkedOrderSummary;
  can_generate_real_tasks: boolean;
  can_generate_reason?: string | null;
  owner_confirmation_required: boolean;
  pricing_review: Record<string, unknown>;
  owner_approval: Record<string, unknown>;
  v4_order_conversion: Record<string, unknown>;
  blockers: IntakeV4TaskGenerationDryRunIssue[];
  warnings: IntakeV4TaskGenerationDryRunIssue[];
  dry_run_summary: Record<string, unknown>;
  idempotency_summary: Record<string, unknown>;
  pricing_status: Record<string, unknown>;
  template_contract_status: Record<string, unknown>;
  analysis_hash_status: Record<string, unknown>;
  future_generation_contract: IntakeV4FutureGenerationContract;
}

export interface IntakeV4CreateDraftQuoteRequest {
  confirm_create_draft_only: boolean;
  confirm_no_order: boolean;
  confirm_no_execution: boolean;
  confirm_no_inventory: boolean;
  confirm_internal_draft_quote: boolean;
  decision_reason?: string;
  client_analysis_hash: string;
}

export interface IntakeV4CreateDraftQuoteResponse {
  quote_created: boolean;
  quote_id: number;
  quote_code: string;
  quote_status: string;
  source_module: string;
  source_workspace_id: string;
  quote_input_payload: Record<string, unknown>;
  snapshot_attached: boolean;
  requires_pricing_review: boolean;
  client_send_allowed: boolean;
  accept_allowed: boolean;
  convert_to_order_allowed: boolean;
  production_allowed: boolean;
  order_created: boolean;
  execution_plan_created: boolean;
  inventory_mutated: boolean;
}

export interface IntakeV4QuoteHandoffPreviewResponse {
  workspace_id: string;
  workspace_readiness_status?: string | null;
  handoff_allowed: boolean;
  status_label:
    | "HANDOFF_ALLOWED"
    | "QUOTE_HANDOFF_BLOCKED"
    | "REVIEW_REQUIRED"
    | "ACTION_NEEDED"
    | "READY_FOR_INTERNAL_DRAFT_REVIEW";
  blockers: string[];
  can_create_internal_draft_quote: boolean;
  requires_operator_confirmation: boolean;
  operator_confirmation_complete: boolean;
  fatal_blockers: string[];
  review_warnings: string[];
  /** Aggregate info traces — visible technical diagnostics; do not gate accept/convert/production. */
  diagnostic_warnings?: string[];
  client_send_allowed: boolean;
  accept_allowed: boolean;
  convert_to_order_allowed: boolean;
  production_allowed: boolean;
  preview_only: boolean;
}

export interface IntakeV4PromoteVolumetricLettersV2Response {
  template_code: string;
  template_id: number;
  template_action: "created" | "updated";
  dossier_id: number;
  dossier_action: "created" | "updated";
  dossier_status: string;
  created_from: string;
  requested_by?: string | null;
  pricing: {
    inserted_materials: number;
    updated_materials: number;
    inserted_rates: number;
    updated_rates: number;
  };
}

export class IntakeV4ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "IntakeV4ApiError";
    this.status = status;
  }
}

function parseApiErrorMessage(status: number, raw: string): string {
  if (!raw.trim()) return `Request failed (${status})`;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (typeof parsed === "object" && parsed !== null && "detail" in parsed) {
      const detail = (parsed as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (typeof detail === "object" && detail !== null) {
        const obj = detail as Record<string, unknown>;
        if (typeof obj.message === "string") return obj.message;
        if (typeof obj.error === "string") {
          if (obj.error === "workspace_not_found") {
            return "Workspace V6 inexistent. Deschide /intake-v6/operator pentru un workspace V6 nou.";
          }
          return obj.error;
        }
      }
    }
  } catch {
    // keep raw text
  }
  return raw.length > 240 ? `${raw.slice(0, 240)}…` : raw;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { credentials: "include", cache: "no-store", ...init });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new IntakeV4ApiError(response.status, parseApiErrorMessage(response.status, text));
  }
  return response.json() as Promise<T>;
}

export async function getIntakeV4Workspace(id: string): Promise<IntakeV4WorkspaceResponse> {
  return requestJson(`${apiBase()}/workspaces/${encodeURIComponent(id)}`);
}

export async function createIntakeV4Workspace(body: {
  title: string;
  template_code?: string;
  client_name?: string;
  job_title?: string;
  intake_request_code?: string;
}): Promise<IntakeV4WorkspaceResponse> {
  return requestJson(`${apiBase()}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function ensureIntakeV4WorkspaceForIntakeRequest(
  intakeRequestCode: string,
): Promise<IntakeV4WorkspaceResponse> {
  return requestJson(`${apiBase()}/workspaces/ensure-for-intake-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intake_request_code: intakeRequestCode }),
  });
}

export async function uploadIntakeV4SvgFile(
  workspaceId: string,
  file: File,
): Promise<IntakeV4SvgUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return requestJson(`${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/svg`, {
    method: "POST",
    body: form,
  });
}

export async function getIntakeV4ProductSystemBinding(
  workspaceId: string,
): Promise<IntakeV4ProductSystemBindingResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/product-system-binding`,
  );
}

export async function getIntakeV4TemplateFormContract(
  workspaceId: string,
): Promise<IntakeV4TemplateFormContractResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/template-form-contract`,
  );
}

export async function promoteIntakeV4VolumetricLettersV2Template(): Promise<IntakeV4PromoteVolumetricLettersV2Response> {
  return requestJson(`${apiBase()}/product-system/templates/volumetric-letters-v2`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
}

export async function getIntakeV4TaskPreview(
  workspaceId: string,
  finishDraft?: Partial<IntakeV4FinishSetup>,
): Promise<IntakeV4TaskPreviewResponse> {
  const params = new URLSearchParams();
  if (finishDraft?.face_finish_type) params.set("face_finish_type", finishDraft.face_finish_type);
  if (finishDraft?.return_finish_type) params.set("return_finish_type", finishDraft.return_finish_type);
  if (finishDraft?.illuminated != null) params.set("illuminated", String(finishDraft.illuminated));
  if (finishDraft?.lighting_system_type) {
    params.set("lighting_system_type", finishDraft.lighting_system_type);
  }
  const qs = params.toString();
  const suffix = qs ? `?${qs}` : "";
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/task-preview${suffix}`,
  );
}

export async function getIntakeV4MaterialBreakdown(
  workspaceId: string,
): Promise<IntakeV4MaterialBreakdownResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/material-breakdown`,
  );
}

export async function getIntakeV4FaceBackPrepCostDraft(
  workspaceId: string,
  options?: { shanfrenForex?: boolean },
): Promise<IntakeV4FaceBackPrepCostDraftResponse> {
  const params = new URLSearchParams();
  if (options?.shanfrenForex != null) {
    params.set("shanfren_forex", String(options.shanfrenForex));
  }
  const qs = params.toString();
  const suffix = qs ? `?${qs}` : "";
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/volumetric-face-back-prep/cost-draft${suffix}`,
  );
}

export async function getIntakeV4NestingPreview(
  workspaceId: string,
): Promise<IntakeV4NestingPreviewResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/nesting-preview`,
  );
}

export async function getIntakeV4PricingInputPreview(
  workspaceId: string,
): Promise<IntakeV4PricingInputPreviewResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/pricing-input-preview`,
  );
}

export async function getIntakeV4ProductionTaskDryRun(
  workspaceId: string,
): Promise<IntakeV4ProductionTaskDryRunResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/production-task-dry-run`,
  );
}

export async function getIntakeV4AiInformationalAssistCandidate(
  workspaceId: string,
): Promise<IntakeV4AiInformationalAssistPreviewResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/ai-informational-assist-candidate`,
  );
}

export async function getIntakeV4AiSemanticClassificationCandidate(
  workspaceId: string,
): Promise<IntakeV4AiSemanticClassificationPreviewResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/ai-semantic-classification-candidate`,
  );
}

export async function getIntakeV4ProductionHandoffPreview(
  workspaceId: string,
): Promise<IntakeV4ProductionHandoffPreviewResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/production-handoff-preview`,
  );
}

export async function getIntakeV4TaskGenerationDryRun(
  workspaceId: string,
): Promise<IntakeV4TaskGenerationDryRunResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/task-generation-dry-run`,
  );
}

export async function getIntakeV4OrderBoundTaskReadiness(
  workspaceId: string,
): Promise<IntakeV4OrderBoundTaskReadinessResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/order-bound-task-readiness`,
  );
}

export async function getIntakeV4QuoteHandoffPreview(
  workspaceId: string,
  clientAnalysisHash?: string | null,
): Promise<IntakeV4QuoteHandoffPreviewResponse> {
  const params = new URLSearchParams();
  if (clientAnalysisHash) params.set("client_analysis_hash", clientAnalysisHash);
  const qs = params.toString();
  const suffix = qs ? `?${qs}` : "";
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/quote-handoff-preview${suffix}`,
  );
}

export async function saveIntakeV4InternalDraftQuoteConfirmation(
  workspaceId: string,
  body: { confirmed: boolean },
): Promise<IntakeV4WorkspaceResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/internal-draft-quote-confirmation`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function createIntakeV4DraftQuote(
  workspaceId: string,
  body: IntakeV4CreateDraftQuoteRequest,
): Promise<IntakeV4CreateDraftQuoteResponse> {
  return requestJson(`${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/create-draft-quote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function persistIntakeV4AnalysisBundle(
  workspaceId: string,
  body: {
    file_name: string;
    file_size_bytes: number;
    svg_text: string;
    svg_analysis_json: Record<string, unknown>;
    layer_role_setup: IntakeV4LayerRoleSetup;
  },
): Promise<IntakeV4WorkspaceResponse> {
  return requestJson(`${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/analysis-bundle`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function saveIntakeV4FinishSetup(
  workspaceId: string,
  body: IntakeV4FinishSetup,
): Promise<IntakeV4WorkspaceResponse> {
  return requestJson(`${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/finish-setup`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function saveIntakeV4LayerRoles(
  workspaceId: string,
  layers: Array<{
    layer_key: string;
    confirmed_role: string;
    confirmation_state?: "pending" | "confirmed" | "ignored";
    operator_note?: string;
  }>,
): Promise<IntakeV4WorkspaceResponse> {
  return requestJson(`${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/layer-roles`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ layers }),
  });
}

export async function putIntakeV4SheetFootprintOverride(
  workspaceId: string,
  body: IntakeV4SheetFootprintOverrideRequest,
): Promise<IntakeV4SheetFootprintOverrideResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/operator/sheet-footprint-override`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export interface IntakeV4CommercialSpineStateResponse {
  quote_exists: boolean;
  is_iv4_quote: boolean;
  quote_id?: number | null;
  quote_code?: string | null;
  quote_status?: string | null;
  intake_code?: string | null;
  workspace_id?: string | null;
  requires_pricing_review?: boolean | null;
  pricing_review: Record<string, unknown>;
  owner_approval: Record<string, unknown>;
  quote_accepted: boolean;
  quote_commercial_totals: Record<string, unknown>;
  v4_order_conversion: Record<string, unknown>;
  creates_execution_tasks: boolean;
  writes_execution_plan: boolean;
  stock_consumption: boolean;
  owner_approval_persisted: boolean;
  v4_quote_to_order_enabled: boolean;
}

export async function getIntakeV4CommercialSpineState(
  workspaceId: string,
): Promise<IntakeV4CommercialSpineStateResponse> {
  return requestJson(
    `${apiBase()}/workspaces/${encodeURIComponent(workspaceId)}/commercial-spine-state`,
  );
}

export async function completeIntakeV4PricingReview(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestJson(`${apiBase()}/quotes/${quoteId}/complete-pricing-review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function persistIntakeV4OwnerApproval(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestJson(`${apiBase()}/quotes/${quoteId}/owner-approval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function acceptIntakeV4Quote(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestJson(`${apiBase()}/quotes/${quoteId}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function convertIntakeV4QuoteToOrder(
  quoteId: number,
  body: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return requestJson(`${apiBase()}/quotes/${quoteId}/convert-to-order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
