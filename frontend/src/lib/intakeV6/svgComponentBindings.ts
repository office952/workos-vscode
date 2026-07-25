/**
 * Unified SVG → Product System component bindings (FinishSetup SoT).
 * LEGACY_INTAKE_SVG_ROLE_ADAPTER must not invent ACP options.
 */

import type { SvgBindableComponent } from "@/lib/api";
import type { SvgSupportSelectionState } from "@/lib/svgAnalyzer";
import { ACM_BOXED_MOUNTING_TEMPLATE_CODE } from "@/lib/svgAnalyzer";

export const SVG_COMPONENT_BINDINGS_SCHEMA = "svg_component_bindings_v1" as const;

export type SvgGeometryRole =
  | "LETTER_VECTOR_SET"
  | "LOGO_VECTOR_SET"
  | "SUPPORT_CONTOUR"
  | "DECORATIVE_VECTOR"
  | "IGNORE"
  | "CUTOUT_TEXT"
  | "CUTOUT_LOGO"
  | "ACRYLIC_INSERT";

export type SvgBindingStatus = "DRAFT" | "CONFIRMED" | "RECONFIRM_REQUIRED" | "INACTIVE";

export type FaceTreatmentCode =
  | "FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT"
  | "FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT"
  | "FACE-TREATMENT-ACRYLIC-INSERT"
  | "FACE-TREATMENT-PLAIN-DECORATIVE"
  | "NOT_APPLICABLE";

export interface SvgSelectedGeometry {
  layer_ids: string[];
  group_ids: string[];
  element_ids: string[];
  geometry_hashes: string[];
  source_svg_hash: string | null;
}

export interface SvgBindingProvenance {
  source?: string;
  svg_hash?: string | null;
  geometry_hash?: string | null;
  legacy_note?: string;
  face_treatment_registry_version?: string;
}

export interface SvgLocalModuleConfiguration {
  schema?: string;
  module_code?: string;
  module_instance_id?: string;
  interface_instance_id?: string;
  status?: string;
  readiness?: { overall?: string; gates?: Array<{ path: string; status: string }> };
  [key: string]: unknown;
}

export interface SvgComponentBinding {
  schema: typeof SVG_COMPONENT_BINDINGS_SCHEMA;
  binding_id: string;
  geometry_role: SvgGeometryRole;
  component_template_code: string;
  selection_mode: string;
  selected_geometry: SvgSelectedGeometry;
  configuration: Record<string, unknown>;
  panel_geometry?: Record<string, unknown> | null;
  status: SvgBindingStatus;
  /** Stable zone identity — not array index. */
  local_zone_id?: string;
  face_treatment_code?: FaceTreatmentCode | string | null;
  confirmation_status?: string;
  local_configuration_status?: string;
  local_module_configuration?: SvgLocalModuleConfiguration | null;
  face_treatment_contract_version?: string;
  provenance?: string | SvgBindingProvenance;
  svg_support_element_id?: string | null;
  candidate_explanation?: string[];
  unit_ambiguity?: boolean;
  confirmed_at?: string | null;
}

export const FACE_TREATMENT_APPLIED = "FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT" as const;
export const FACE_TREATMENT_ROUTED = "FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT" as const;
export const FACE_TREATMENT_INSERT = "FACE-TREATMENT-ACRYLIC-INSERT" as const;
export const FACE_TREATMENT_PLAIN = "FACE-TREATMENT-PLAIN-DECORATIVE" as const;

const SHELL_LOCAL_ROLES: SvgGeometryRole[] = [
  "CUTOUT_TEXT",
  "CUTOUT_LOGO",
  "ACRYLIC_INSERT",
  "DECORATIVE_VECTOR",
];

export const LEGACY_INTAKE_SVG_ROLE_ADAPTER = "LEGACY_INTAKE_SVG_ROLE_ADAPTER" as const;

export function emptySelectedGeometry(sourceHash?: string | null): SvgSelectedGeometry {
  return {
    layer_ids: [],
    group_ids: [],
    element_ids: [],
    geometry_hashes: [],
    source_svg_hash: sourceHash ?? null,
  };
}

export function readSvgComponentBindings(
  finish: Record<string, unknown> | null | undefined,
): SvgComponentBinding[] {
  const raw = finish?.svg_component_bindings;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (item): item is SvgComponentBinding =>
      Boolean(item && typeof item === "object" && (item as SvgComponentBinding).component_template_code),
  );
}

export function upsertBinding(
  bindings: SvgComponentBinding[],
  next: SvgComponentBinding,
): SvgComponentBinding[] {
  // Identity is binding_id / role — not component_template_code alone.
  // Multiple ACM face-treatment bindings share TPL-ACM-BOXED… and must coexist.
  // Shell-local roles are one binding per geometry_role in Step 1 sync (stable zone via local_zone_id).
  const without = bindings.filter((b) => {
    if (next.binding_id && b.binding_id === next.binding_id) return false;
    if (next.geometry_role === "SUPPORT_CONTOUR" && b.geometry_role === "SUPPORT_CONTOUR") {
      return false;
    }
    if (
      (next.geometry_role === "LETTER_VECTOR_SET" || next.geometry_role === "LOGO_VECTOR_SET") &&
      b.geometry_role === next.geometry_role
    ) {
      return false;
    }
    if (SHELL_LOCAL_ROLES.includes(next.geometry_role) && b.geometry_role === next.geometry_role) {
      return false;
    }
    return true;
  });
  return [...without, next];
}

export function bindingFromSupportSelection(
  selection: SvgSupportSelectionState,
): SvgComponentBinding | null {
  if (selection.status === "none" || !selection.contour_id) return null;
  const status: SvgBindingStatus =
    selection.status === "reconfirm_required"
      ? "RECONFIRM_REQUIRED"
      : selection.status === "confirmed"
        ? "CONFIRMED"
        : "DRAFT"; // proposed association → DRAFT (not CONFIRMED)
  if (selection.role && selection.role !== "ALUCOBOND_CASED_PANEL" && status === "CONFIRMED") {
    return null;
  }
  return {
    schema: SVG_COMPONENT_BINDINGS_SCHEMA,
    binding_id: `bind_support_${selection.contour_id}`,
    geometry_role: "SUPPORT_CONTOUR",
    component_template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    selection_mode: "CLOSED_CONTOUR",
    selected_geometry: {
      layer_ids: [],
      group_ids: [],
      element_ids: selection.contour_id ? [selection.contour_id] : [],
      geometry_hashes: selection.geometry_hash ? [selection.geometry_hash] : [],
      source_svg_hash: selection.svg_source_hash,
    },
    configuration: {
      fold_count: selection.casing_profile?.fold_count,
      l1_mm: selection.casing_profile?.l1_mm,
      l2_mm: selection.casing_profile?.l2_mm,
      finished_depth_mm: selection.casing_profile?.finished_depth_mm,
      service_corner: selection.service_corner,
      internal_frame_enabled: selection.internal_frame_enabled,
    },
    panel_geometry: selection.panel_geometry,
    status,
    provenance: "svg_support_selection_sync",
    svg_support_element_id: selection.svg_support_element_id,
    candidate_explanation: selection.candidate_explanation,
    unit_ambiguity: selection.unit_ambiguity,
    confirmed_at: selection.confirmed_at,
  };
}

export function letterBinding(args: {
  layerIds: string[];
  sourceSvgHash: string | null;
  componentCode: string;
  selectionMode: string;
  /** When ACP shell host is present — applied interface, not absorbed into shell. */
  appliedOnAcpHost?: boolean;
}): SvgComponentBinding {
  const confirmed = args.layerIds.length > 0;
  return {
    schema: SVG_COMPONENT_BINDINGS_SCHEMA,
    binding_id: `bind_letters_${args.layerIds.join("_") || "none"}`,
    geometry_role: "LETTER_VECTOR_SET",
    component_template_code: args.componentCode,
    selection_mode: args.selectionMode || "LAYER_OR_GROUP",
    selected_geometry: {
      layer_ids: args.layerIds,
      group_ids: [],
      element_ids: [],
      geometry_hashes: [],
      source_svg_hash: args.sourceSvgHash,
    },
    configuration: {},
    status: confirmed ? "CONFIRMED" : "DRAFT",
    face_treatment_code: args.appliedOnAcpHost && confirmed ? FACE_TREATMENT_APPLIED : "NOT_APPLICABLE",
    provenance: "component_aware_assignment",
    confirmed_at: confirmed ? new Date().toISOString() : null,
  };
}

export function logoBinding(args: {
  layerIds: string[];
  sourceSvgHash: string | null;
  componentCode: string;
  selectionMode: string;
  appliedOnAcpHost?: boolean;
}): SvgComponentBinding {
  const confirmed = args.layerIds.length > 0;
  return {
    schema: SVG_COMPONENT_BINDINGS_SCHEMA,
    binding_id: `bind_logo_${args.layerIds.join("_") || "none"}`,
    geometry_role: "LOGO_VECTOR_SET",
    component_template_code: args.componentCode,
    selection_mode: args.selectionMode || "LAYER_OR_GROUP",
    selected_geometry: {
      layer_ids: args.layerIds,
      group_ids: [],
      element_ids: [],
      geometry_hashes: [],
      source_svg_hash: args.sourceSvgHash,
    },
    configuration: {},
    status: confirmed ? "CONFIRMED" : "DRAFT",
    face_treatment_code: args.appliedOnAcpHost && confirmed ? FACE_TREATMENT_APPLIED : "NOT_APPLICABLE",
    provenance: "component_aware_assignment",
    confirmed_at: confirmed ? new Date().toISOString() : null,
  };
}

export function acpShellLocalBinding(args: {
  geometryRole: "CUTOUT_TEXT" | "CUTOUT_LOGO" | "ACRYLIC_INSERT" | "DECORATIVE_VECTOR";
  layerIds: string[];
  sourceSvgHash: string | null;
  previous?: SvgComponentBinding | null;
}): SvgComponentBinding {
  const treatment: FaceTreatmentCode =
    args.geometryRole === "ACRYLIC_INSERT"
      ? FACE_TREATMENT_INSERT
      : args.geometryRole === "DECORATIVE_VECTOR"
        ? FACE_TREATMENT_PLAIN
        : FACE_TREATMENT_ROUTED;
  const layerKey = [...args.layerIds].sort().join("_") || "none";
  const prev = args.previous;
  const confirmed = args.layerIds.length > 0;
  return {
    schema: SVG_COMPONENT_BINDINGS_SCHEMA,
    binding_id: prev?.binding_id || `bind_${args.geometryRole.toLowerCase()}_${layerKey}`,
    geometry_role: args.geometryRole,
    component_template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    selection_mode: "LAYER_OR_GROUP",
    selected_geometry: {
      layer_ids: args.layerIds,
      group_ids: [],
      element_ids: [],
      geometry_hashes: [],
      source_svg_hash: args.sourceSvgHash,
    },
    configuration: prev?.configuration || {},
    status: confirmed ? "CONFIRMED" : "INACTIVE",
    local_zone_id: prev?.local_zone_id,
    face_treatment_code: treatment,
    local_module_configuration: prev?.local_module_configuration || null,
    confirmation_status: confirmed ? "CONFIRMED" : "INACTIVE",
    provenance: {
      source: "component_aware_assignment",
      face_treatment_registry_version: "acp_face_treatment_registry/v1",
    },
    confirmed_at: confirmed ? new Date().toISOString() : null,
  };
}

export function filterBindableForUi(components: SvgBindableComponent[]): SvgBindableComponent[] {
  return components.filter(
    (c) =>
      c.available !== false &&
      c.component_template_code !== "TPL-BOND-CASETAT" &&
      !c.guards?.includes("deprecated"),
  );
}

export function ownerGeometryLabel(role: string | undefined): string {
  switch (role) {
    case "LETTER_VECTOR_SET":
      return "Vector litere";
    case "LOGO_VECTOR_SET":
      return "Vector logo";
    case "SUPPORT_CONTOUR":
      return "Contur suport";
    case "DECORATIVE_VECTOR":
      return "Element decorativ";
    case "IGNORE":
      return "Ignoră";
    case "CUTOUT_TEXT":
      return "Text decupat";
    case "CUTOUT_LOGO":
      return "Logo decupat";
    case "ACRYLIC_INSERT":
      return "Insert plexiglas";
    default:
      return role || "—";
  }
}

/** Owner-facing product-component label (presentation). Distinct from geometry role. */
export function ownerFacingComponentProductLabel(
  component: Pick<SvgBindableComponent, "component_template_code" | "owner_label"> | null | undefined,
): string {
  if (!component) return "—";
  switch (component.component_template_code) {
    case "TPL-VOLUMETRIC-FACE_v1":
      return "Față litere volumetrice";
    case "TPL-VOLUMETRIC-LOGO_v1":
      return "Componentă logo volumetric";
    case "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1":
      return component.owner_label || "Alucobond casetat";
    default:
      return component.owner_label || component.component_template_code;
  }
}

export function findBindableByGeometryRole(
  bindables: SvgBindableComponent[],
  geometryRole: SvgGeometryRole,
): SvgBindableComponent | undefined {
  return bindables.find((c) => c.accepted_geometry_roles?.includes(geometryRole));
}

export function bindableForOwnerLayerRole(
  bindables: SvgBindableComponent[],
  role: string | null | undefined,
): SvgBindableComponent | undefined {
  if (role === "face") return findBindableByGeometryRole(bindables, "LETTER_VECTOR_SET");
  if (role === "printed_artwork" || role === "logo") {
    return findBindableByGeometryRole(bindables, "LOGO_VECTOR_SET");
  }
  if (role === "support_panel") {
    return findBindableByGeometryRole(bindables, "SUPPORT_CONTOUR");
  }
  if (role === "cutout_text") return findBindableByGeometryRole(bindables, "CUTOUT_TEXT");
  if (role === "cutout_logo") return findBindableByGeometryRole(bindables, "CUTOUT_LOGO");
  if (role === "acrylic_insert") return findBindableByGeometryRole(bindables, "ACRYLIC_INSERT");
  return undefined;
}

export function ownerLayerRoleToGeometryRole(
  role: string | null | undefined,
): SvgGeometryRole | null {
  if (role === "face") return "LETTER_VECTOR_SET";
  if (role === "printed_artwork" || role === "logo") return "LOGO_VECTOR_SET";
  if (role === "support_panel") return "SUPPORT_CONTOUR";
  if (role === "cutout_text") return "CUTOUT_TEXT";
  if (role === "cutout_logo") return "CUTOUT_LOGO";
  if (role === "acrylic_insert") return "ACRYLIC_INSERT";
  return null;
}

export function layerRoleBindingsSyncKey(bindings: SvgComponentBinding[]): string {
  return bindings
    .filter(
      (b) =>
        b.geometry_role === "LETTER_VECTOR_SET" ||
        b.geometry_role === "LOGO_VECTOR_SET" ||
        SHELL_LOCAL_ROLES.includes(b.geometry_role),
    )
    .map(
      (b) =>
        `${b.geometry_role}:${b.component_template_code}:${[...b.selected_geometry.layer_ids].sort().join(",")}:${b.status}:${b.face_treatment_code || ""}`,
    )
    .sort()
    .join("|");
}

/** Derive letter/logo/shell-local bindings from layer-role confirmation (keeps support intact). */
export function buildLayerRoleComponentBindings(args: {
  confirmation: {
    layers: Array<{
      layerKey: string;
      confirmedRole: string | null;
      confirmationState: string;
    }>;
  } | null;
  bindables: SvgBindableComponent[];
  sourceSvgHash: string | null;
  previous: SvgComponentBinding[];
}): SvgComponentBinding[] {
  const lettersComp = findBindableByGeometryRole(args.bindables, "LETTER_VECTOR_SET");
  if (!args.confirmation || !lettersComp) return args.previous;

  const activeLayers = args.confirmation.layers.filter((l) => l.confirmationState !== "ignored");
  const letterLayers = activeLayers
    .filter((l) => l.confirmedRole === "face")
    .map((l) => l.layerKey);
  const logoComp = findBindableByGeometryRole(args.bindables, "LOGO_VECTOR_SET");
  const logoLayers = activeLayers
    .filter((l) => l.confirmedRole === "printed_artwork" || l.confirmedRole === "logo")
    .map((l) => l.layerKey);
  const cutoutTextLayers = activeLayers
    .filter((l) => l.confirmedRole === "cutout_text")
    .map((l) => l.layerKey);
  const cutoutLogoLayers = activeLayers
    .filter((l) => l.confirmedRole === "cutout_logo")
    .map((l) => l.layerKey);
  const insertLayers = activeLayers
    .filter((l) => l.confirmedRole === "acrylic_insert")
    .map((l) => l.layerKey);

  const hasAcpHost = args.previous.some(
    (b) =>
      b.geometry_role === "SUPPORT_CONTOUR" &&
      (b.status === "CONFIRMED" || b.status === "DRAFT" || b.status === "RECONFIRM_REQUIRED"),
  );

  let next = args.previous.filter(
    (b) =>
      b.geometry_role !== "LETTER_VECTOR_SET" &&
      b.geometry_role !== "LOGO_VECTOR_SET" &&
      !SHELL_LOCAL_ROLES.includes(b.geometry_role),
  );
  next = upsertBinding(
    next,
    letterBinding({
      layerIds: letterLayers,
      sourceSvgHash: args.sourceSvgHash,
      componentCode: lettersComp.component_template_code,
      selectionMode: lettersComp.selection_mode,
      appliedOnAcpHost: hasAcpHost,
    }),
  );
  if (logoComp && logoLayers.length) {
    next = upsertBinding(
      next,
      logoBinding({
        layerIds: logoLayers,
        sourceSvgHash: args.sourceSvgHash,
        componentCode: logoComp.component_template_code,
        selectionMode: logoComp.selection_mode,
        appliedOnAcpHost: hasAcpHost,
      }),
    );
  }

  const prevByRole = (role: SvgGeometryRole) =>
    args.previous.find((b) => b.geometry_role === role) || null;

  if (cutoutTextLayers.length || prevByRole("CUTOUT_TEXT")) {
    next = upsertBinding(
      next,
      acpShellLocalBinding({
        geometryRole: "CUTOUT_TEXT",
        layerIds: cutoutTextLayers,
        sourceSvgHash: args.sourceSvgHash,
        previous: prevByRole("CUTOUT_TEXT"),
      }),
    );
  }
  if (cutoutLogoLayers.length || prevByRole("CUTOUT_LOGO")) {
    next = upsertBinding(
      next,
      acpShellLocalBinding({
        geometryRole: "CUTOUT_LOGO",
        layerIds: cutoutLogoLayers,
        sourceSvgHash: args.sourceSvgHash,
        previous: prevByRole("CUTOUT_LOGO"),
      }),
    );
  }
  if (insertLayers.length || prevByRole("ACRYLIC_INSERT")) {
    next = upsertBinding(
      next,
      acpShellLocalBinding({
        geometryRole: "ACRYLIC_INSERT",
        layerIds: insertLayers,
        sourceSvgHash: args.sourceSvgHash,
        previous: prevByRole("ACRYLIC_INSERT"),
      }),
    );
  }
  return next;
}
