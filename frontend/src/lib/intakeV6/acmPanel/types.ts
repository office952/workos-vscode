/**
 * Generic reusable ACM boxed panel component contract.
 * SUPPORT_CONTOUR / finish_setup are Intake adapters for the current consumer — not the universal definition.
 */

export const ACM_PANEL_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" as const;
export const ACM_PANEL_INSTANCE_SCHEMA = "acm_panel_component_instance_v1" as const;

export type AcmPanelDomainAction = "preserve" | "upsert" | "clear";

export type AcmFieldAuthority =
  | "detected"
  | "catalog_default"
  | "proposed"
  | "operator_confirmed";

export type AcmLifecycleStatus = "unconfirmed" | "proposed" | "confirmed" | "unknown";

/** Field gating class — catalog_default never unlocks critical readiness. */
export type AcmFieldClass = "critical" | "optional" | "informational";

export type AcmPanelCapability =
  | "boxed_returns"
  | "rear_lip"
  | "internal_frame"
  | "segmented_panels"
  | "graphic_cutouts"
  | "illuminated_cutouts"
  | "plexiglass_inserts"
  | "led_system"
  | "rear_closure"
  | "totem_face"
  | "direct_letter_mounting"
  | "wall_mounting"
  | "structure_mounting";

export type ComponentRelationType =
  | "positioned_on"
  | "contained_by"
  | "contains"
  | "belongs_to_assembly"
  | "mounts_on"
  | "inserted_into"
  | "illuminates"
  | "attached_to_structure";

export type ComponentRelationStatus = "proposed" | "confirmed" | "unknown";

export interface ComponentRelation {
  relation_id: string;
  from_component_ref: string;
  to_component_ref: string;
  relation_type: ComponentRelationType;
  status: ComponentRelationStatus;
  provenance: string;
}

export interface AcmPanelCapabilities {
  active: AcmPanelCapability[];
  inactive: AcmPanelCapability[];
}

export interface AcmPanelGeometry {
  contour_id: string | null;
  element_id: string | null;
  geometry_hash: string | null;
  width_mm: number | null;
  height_mm: number | null;
  area_mm2: number | null;
  perimeter_mm: number | null;
  bbox?: { x: number; y: number; width: number; height: number } | null;
  panels?: Array<{
    panel_id: string;
    order: number;
    width_mm: number | null;
    height_mm: number | null;
    position: { x_mm: number; y_mm: number };
    contour_element_id?: string | null;
  }>;
  joints?: Array<{
    joint_id: string;
    left_panel_id: string;
    right_panel_id: string;
    orientation: string;
  }>;
}

export interface AcmPanelConfiguration {
  acm_thickness_mm: number | null;
  fold_count: 1 | 2 | null;
  l1_mm: number | null;
  l2_mm: number | null;
  finished_depth_mm: number | null;
  internal_frame_enabled: boolean;
  service_corner: string | null;
  field_authority: Record<string, AcmFieldAuthority>;
  field_class: Record<string, AcmFieldClass>;
}

export interface AcmPanelComponentInstance {
  schema: typeof ACM_PANEL_INSTANCE_SCHEMA;
  component_instance_id: string;
  component_template_code: typeof ACM_PANEL_TEMPLATE_CODE;
  /** Intake adapter role for letters-on-support consumer — not universal ACM identity. */
  intake_geometry_role_adapter: "SUPPORT_CONTOUR";
  role_status: AcmLifecycleStatus;
  association_status: AcmLifecycleStatus;
  technical_configuration_status: AcmLifecycleStatus;
  composition_status: AcmLifecycleStatus;
  capabilities: AcmPanelCapabilities;
  geometry: AcmPanelGeometry;
  configuration: AcmPanelConfiguration;
  relations: ComponentRelation[];
  /**
   * Shell foil Finish Contract (face ≠ volume). Optional — MIXED §7–8.
   * Shape: acm_shell_finish_v1 (see shellFinish.ts). Not letter finishes.
   */
  shell_finish?: unknown;
  /**
   * ACM sheet material — plate variant + installation environment. Optional.
   * Shape: acm_sheet_material_v1 (see acmSheetMaterial.ts). Operator truth, not pricing.
   */
  sheet_material?: unknown;
  svg_source_hash: string | null;
  updated_at: string;
}

export const ACM_CATALOG_DEFAULTS = {
  fold_count: 2 as const,
  l1_mm: 60,
  l2_mm: 25,
  acm_thickness_mm: 3,
  internal_frame_enabled: false,
  fold_sides: "all",
  v_groove_angle_deg: 135,
  total_fit_allowance_mm: 2,
} as const;
