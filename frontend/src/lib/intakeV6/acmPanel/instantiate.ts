/**
 * Atomic ACM panel component instantiation (upsert).
 * Role confirm → association/technical proposed; composition stays unconfirmed.
 */

import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import type { ClosedContourCandidate } from "@/lib/svgAnalyzer/closed-contour/closedContourTypes";
import {
  buildCasingProfile,
  emptySvgSupportSelection,
  validateCasingProfile,
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
} from "@/lib/svgAnalyzer/closed-contour/alucobondCasedPanelSelection";
import type { SvgBindableComponent } from "@/lib/api";
import { resolvePrimaryClosedContourCandidate } from "../associatePrimarySupportContour";
import {
  bindingFromSupportSelection,
  buildLayerRoleComponentBindings,
  readSvgComponentBindings,
  upsertBinding,
  type SvgComponentBinding,
} from "../svgComponentBindings";
import {
  proposeSegmentedBackgroundFromCandidates,
  readSegmentedBackground,
  type SegmentedBackground,
} from "../segmentedBackground";
import type { IntakeV6FinishSetup } from "../intakeV6Api";
import {
  buildPanelBelongsToAssemblyRelations,
  proposeGeometryPlacementRelations,
  assertNoAutoMountRelations,
} from "./relations";
import {
  ACM_CATALOG_DEFAULTS,
  ACM_PANEL_INSTANCE_SCHEMA,
  ACM_PANEL_TEMPLATE_CODE,
  type AcmPanelComponentInstance,
  type AcmPanelDomainAction,
  type AcmFieldAuthority,
  type AcmFieldClass,
} from "./types";

export type AtomicAcmPanelInstantiationResult = {
  ok: boolean;
  blockers: string[];
  finishPatch: Partial<IntakeV6FinishSetup> & {
    acm_panel_domain_action?: AcmPanelDomainAction;
    acm_panel_instance?: AcmPanelComponentInstance | null;
  } | null;
  instance: AcmPanelComponentInstance | null;
  contourId: string | null;
  mergedBindings: SvgComponentBinding[];
};

function stableInstanceId(contourId: string, svgHash: string | null): string {
  const h = (svgHash || "nohash").slice(0, 12);
  return `acm_${contourId}_${h}`;
}

function catalogAuthorityMap(): {
  field_authority: Record<string, AcmFieldAuthority>;
  field_class: Record<string, AcmFieldClass>;
} {
  return {
    field_authority: {
      panel_geometry: "detected",
      fold_count: "catalog_default",
      l1_mm: "catalog_default",
      l2_mm: "catalog_default",
      finished_depth_mm: "catalog_default",
      acm_thickness_mm: "catalog_default",
      internal_frame: "catalog_default",
      service_corner: "catalog_default",
    },
    field_class: {
      panel_geometry: "critical",
      contour_association: "critical",
      fold_count: "critical",
      l1_mm: "critical",
      l2_mm: "critical",
      acm_thickness_mm: "critical",
      finished_depth_mm: "critical",
      internal_frame: "optional",
      service_corner: "optional",
      detection_message: "informational",
    },
  };
}

/** Propose Alucobond selection — NOT operator-confirmed. */
export function proposeAlucobondSelection(args: {
  candidate: ClosedContourCandidate;
  svg_source_hash: string;
  unit_ambiguity: boolean;
}): { selection: ReturnType<typeof emptySvgSupportSelection>; blockers: string[] } {
  const casing_profile = buildCasingProfile({
    fold_count: ACM_CATALOG_DEFAULTS.fold_count,
    l1_mm: ACM_CATALOG_DEFAULTS.l1_mm,
    l2_mm: ACM_CATALOG_DEFAULTS.l2_mm,
  });
  const blockers = [...validateCasingProfile(casing_profile)];
  if (!(args.candidate.width_mm > 0) || !(args.candidate.height_mm > 0)) {
    blockers.push("Geometria panoului este invalidă.");
  }
  if (!(args.candidate.area_mm2 > 0) || !(args.candidate.perimeter_mm > 0)) {
    blockers.push("Aria/perimetrul panoului sunt invalide.");
  }
  if (blockers.length) {
    return { selection: emptySvgSupportSelection(), blockers };
  }
  const auth = catalogAuthorityMap();
  return {
    blockers: [],
    selection: {
      schema: "svg_support_selection_v1",
      status: "proposed",
      role: "ALUCOBOND_CASED_PANEL",
      contour_id: args.candidate.contour_id,
      svg_support_element_id: args.candidate.element_id,
      geometry_hash: args.candidate.geometry_hash,
      svg_source_hash: args.svg_source_hash,
      panel_geometry: {
        width_mm: args.candidate.width_mm,
        height_mm: args.candidate.height_mm,
        area_mm2: args.candidate.area_mm2,
        perimeter_mm: args.candidate.perimeter_mm,
        geometry_hash: args.candidate.geometry_hash,
      },
      casing_profile,
      service_corner: null,
      internal_frame_enabled: ACM_CATALOG_DEFAULTS.internal_frame_enabled,
      candidate_explanation: args.candidate.reasons,
      unit_ambiguity: args.unit_ambiguity,
      confirmed_at: null,
      field_authority: auth.field_authority,
      field_class: auth.field_class,
      association_status: "proposed",
      technical_configuration_status: "proposed",
    } as ReturnType<typeof emptySvgSupportSelection>,
  };
}

export function buildAcmMountingSolutionProposed(
  selection: {
    role: string | null;
    status: string;
    panel_geometry: {
      width_mm: number;
      height_mm: number;
      area_mm2?: number;
      perimeter_mm?: number;
    } | null;
    casing_profile: {
      fold_count: 1 | 2;
      l1_mm: number;
      l2_mm?: number | null;
      finished_depth_mm: number;
    } | null;
    svg_support_element_id: string | null;
    geometry_hash: string | null;
    contour_id: string | null;
    internal_frame_enabled: boolean;
  },
): Record<string, unknown> | null {
  if (selection.role !== "ALUCOBOND_CASED_PANEL") return null;
  if (selection.status !== "proposed" && selection.status !== "confirmed") return null;
  if (!selection.panel_geometry || !selection.casing_profile) return null;
  const fold = selection.casing_profile.fold_count;
  const auth = catalogAuthorityMap();
  return {
    kind: "product_system_template",
    template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    configuration: {
      panel_width_mm: selection.panel_geometry.width_mm,
      panel_height_mm: selection.panel_geometry.height_mm,
      return_depth_mm: selection.casing_profile.l1_mm,
      rear_lip_mm: fold === 2 ? selection.casing_profile.l2_mm ?? 0 : 0,
      fold_count: fold,
      finished_depth_mm: selection.casing_profile.finished_depth_mm,
      svg_support_element_id: selection.svg_support_element_id,
      geometry_hash: selection.geometry_hash,
      contour_id: selection.contour_id,
      panel_area_mm2: selection.panel_geometry.area_mm2,
      panel_perimeter_mm: selection.panel_geometry.perimeter_mm,
      internal_frame_enabled: selection.internal_frame_enabled,
      frame_clearance_mm: 0,
      internal_frame: {
        enabled: selection.internal_frame_enabled,
        total_fit_allowance_mm: ACM_CATALOG_DEFAULTS.total_fit_allowance_mm,
        confirmation_status: "NOT_APPLICABLE",
      },
      acm_thickness_mm: ACM_CATALOG_DEFAULTS.acm_thickness_mm,
      fold_sides: ACM_CATALOG_DEFAULTS.fold_sides,
      v_groove_angle_deg: ACM_CATALOG_DEFAULTS.v_groove_angle_deg,
      field_authority: auth.field_authority,
      field_class: auth.field_class,
      technical_configuration_status: "proposed",
    },
  };
}

export function buildAtomicAcmPanelInstantiationPatch(args: {
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  finishSetup: IntakeV6FinishSetup | Record<string, unknown> | null | undefined;
  bindables: SvgBindableComponent[];
  svgSourceHash: string | null;
  candidate?: ClosedContourCandidate | null;
}): AtomicAcmPanelInstantiationResult {
  const { report, confirmation, finishSetup, bindables, svgSourceHash } = args;

  const hasSupport = confirmation.layers.some(
    (layer) =>
      layer.confirmedRole === "support_panel" && layer.confirmationState === "confirmed",
  );
  if (!hasSupport) {
    return {
      ok: true,
      blockers: [],
      finishPatch: null,
      instance: null,
      contourId: null,
      mergedBindings: [],
    };
  }

  const candidates = report.closedContourCandidates?.candidates ?? [];
  if (!report.closedContourCandidates?.candidate_count) {
    return {
      ok: false,
      blockers: [
        "Contur ACM necesită candidați closed-contour din analiza SVG. Reîncarcă fișierul SVG, apoi confirmă rolul.",
      ],
      finishPatch: null,
      instance: null,
      contourId: null,
      mergedBindings: [],
    };
  }

  const target = args.candidate ?? resolvePrimaryClosedContourCandidate(candidates);
  if (!target) {
    return {
      ok: false,
      blockers: ["Nu există un contur închis candidabil pentru Panou Alucobond."],
      finishPatch: null,
      instance: null,
      contourId: null,
      mergedBindings: [],
    };
  }

  const proposed = proposeAlucobondSelection({
    candidate: target,
    svg_source_hash: svgSourceHash ?? "",
    unit_ambiguity: Boolean(report.closedContourCandidates?.unit_ambiguity),
  });
  if (proposed.blockers.length) {
    return {
      ok: false,
      blockers: proposed.blockers,
      finishPatch: null,
      instance: null,
      contourId: target.contour_id,
      mergedBindings: [],
    };
  }

  const supportBinding = bindingFromSupportSelection(proposed.selection as never);
  const previous = readSvgComponentBindings(finishSetup);
  const letterLogoBindings = buildLayerRoleComponentBindings({
    confirmation,
    bindables,
    sourceSvgHash: svgSourceHash,
    previous,
  });
  const withSupport = supportBinding ? upsertBinding(previous, supportBinding) : previous;
  const mergedBindings = [
    ...letterLogoBindings.filter((b) => b.geometry_role !== "SUPPORT_CONTOUR"),
    ...withSupport.filter((b) => b.geometry_role === "SUPPORT_CONTOUR"),
  ];

  const existingSeg = readSegmentedBackground(finishSetup as Record<string, unknown> | null);
  const existingStatus = String(existingSeg?.status || "").toUpperCase();
  let segmented: SegmentedBackground | null = null;
  if (existingStatus !== "CONFIRMED" && existingStatus !== "REJECTED") {
    segmented =
      proposeSegmentedBackgroundFromCandidates(candidates) ??
      null;
  } else {
    segmented = existingSeg;
  }

  const instanceId = stableInstanceId(target.contour_id, svgSourceHash);
  const panels = segmented?.panels ?? [];
  const relations = [
    ...buildPanelBelongsToAssemblyRelations({
      componentInstanceId: instanceId,
      panels: panels.length ? panels : [{ panel_id: "panel_1" }],
    }),
    ...proposeGeometryPlacementRelations({
      componentInstanceId: instanceId,
      confirmation,
      candidates,
      panels,
    }),
  ];
  if (!assertNoAutoMountRelations(relations)) {
    return {
      ok: false,
      blockers: ["Relații mounts_on/attached_to_structure nu pot fi derivate automat din geometrie."],
      finishPatch: null,
      instance: null,
      contourId: target.contour_id,
      mergedBindings: [],
    };
  }

  const auth = catalogAuthorityMap();
  const activeCaps: AcmPanelComponentInstance["capabilities"]["active"] = [
    "boxed_returns",
    "rear_lip",
  ];
  if (panels.length >= 2) activeCaps.push("segmented_panels");
  if (proposed.selection.internal_frame_enabled) activeCaps.push("internal_frame");

  const allCaps = [
    "boxed_returns",
    "rear_lip",
    "internal_frame",
    "segmented_panels",
    "graphic_cutouts",
    "illuminated_cutouts",
    "plexiglass_inserts",
    "led_system",
    "rear_closure",
    "totem_face",
    "direct_letter_mounting",
    "wall_mounting",
    "structure_mounting",
  ] as const;
  const inactive = allCaps.filter((c) => !activeCaps.includes(c));

  const instance: AcmPanelComponentInstance = {
    schema: ACM_PANEL_INSTANCE_SCHEMA,
    component_instance_id: instanceId,
    component_template_code: ACM_PANEL_TEMPLATE_CODE,
    intake_geometry_role_adapter: "SUPPORT_CONTOUR",
    role_status: "confirmed",
    association_status: "proposed",
    technical_configuration_status: "proposed",
    composition_status: "unconfirmed",
    capabilities: { active: activeCaps, inactive: [...inactive] },
    geometry: {
      contour_id: target.contour_id,
      element_id: target.element_id,
      geometry_hash: target.geometry_hash,
      width_mm: target.width_mm,
      height_mm: target.height_mm,
      area_mm2: target.area_mm2,
      perimeter_mm: target.perimeter_mm,
      bbox: target.bbox
        ? {
            x: target.bbox.x,
            y: target.bbox.y,
            width: target.bbox.width,
            height: target.bbox.height,
          }
        : null,
      panels: panels.map((p) => ({
        panel_id: p.panel_id,
        order: p.order,
        width_mm: p.width_mm,
        height_mm: p.height_mm,
        position: p.position,
        contour_element_id: p.contour_element_id,
      })),
      joints: segmented?.joints,
    },
    configuration: {
      acm_thickness_mm: ACM_CATALOG_DEFAULTS.acm_thickness_mm,
      fold_count: ACM_CATALOG_DEFAULTS.fold_count,
      l1_mm: ACM_CATALOG_DEFAULTS.l1_mm,
      l2_mm: ACM_CATALOG_DEFAULTS.l2_mm,
      finished_depth_mm: ACM_CATALOG_DEFAULTS.l1_mm,
      internal_frame_enabled: ACM_CATALOG_DEFAULTS.internal_frame_enabled,
      service_corner: null,
      field_authority: auth.field_authority,
      field_class: auth.field_class,
    },
    relations,
    svg_source_hash: svgSourceHash,
    updated_at: new Date().toISOString(),
  };

  // Attach relations onto segmented envelope for nested observability (not SoT identity).
  if (segmented) {
    segmented = {
      ...segmented,
      element_bindings: [
        ...(segmented.element_bindings || []),
      ],
      meta: {
        ...(typeof (segmented as { meta?: Record<string, unknown> }).meta === "object"
          ? (segmented as { meta?: Record<string, unknown> }).meta
          : {}),
        host_component_instance_id: instanceId,
        component_relations: relations,
        association_status: "proposed",
        technical_configuration_status: "proposed",
      },
    } as SegmentedBackground;
  }

  const mounting = buildAcmMountingSolutionProposed(proposed.selection as never);

  // Embed instance on selection dict (survives finish normalize even when top-level
  // schema fields are unavailable on a stale server process). Also set top-level when possible.
  const selectionWithInstance = {
    ...(proposed.selection as Record<string, unknown>),
    acm_panel_instance: instance,
    acm_panel_domain_action: "upsert" as const,
    component_relations: relations,
  };

  const mountingWithInstance = mounting
    ? {
        ...mounting,
        configuration: {
          ...((mounting.configuration as Record<string, unknown>) || {}),
          acm_panel_instance: instance,
          component_relations: relations,
        },
      }
    : null;

  return {
    ok: true,
    blockers: [],
    finishPatch: {
      acm_panel_domain_action: "upsert",
      acm_panel_instance: instance,
      svg_support_selection: selectionWithInstance as never,
      svg_component_bindings: mergedBindings,
      mounting_solution: mountingWithInstance,
      power_supply_service_corner: null,
      ...(segmented ? { segmented_background: segmented as never } : {}),
    },
    instance,
    contourId: target.contour_id,
    mergedBindings,
  };
}

export function buildAtomicAcmPanelClearPatch(args: {
  finishSetup: IntakeV6FinishSetup | Record<string, unknown> | null | undefined;
}): Partial<IntakeV6FinishSetup> & {
  acm_panel_domain_action: AcmPanelDomainAction;
  acm_panel_instance: null;
} {
  const prev = readSvgComponentBindings(args.finishSetup);
  return {
    acm_panel_domain_action: "clear",
    acm_panel_instance: null,
    svg_support_selection: emptySvgSupportSelection() as never,
    svg_component_bindings: prev.filter(
      (b) => b.component_template_code !== ACM_PANEL_TEMPLATE_CODE,
    ),
    mounting_solution: null,
    power_supply_service_corner: null,
    segmented_background: {
      schema: "acm_segmented_background_v1",
      status: "INACTIVE",
      operator_confirmed: false,
      panels: [],
      joints: [],
      element_bindings: [],
    } as never,
  };
}
