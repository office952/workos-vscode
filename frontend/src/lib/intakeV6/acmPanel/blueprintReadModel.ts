/**
 * AcmPanel Blueprint Nivel 1 — pure read-model derivation (L1-P focused).
 * Projection only: never writes finish_setup / operatorPatch / domain.
 */

import type {
  AcmFieldAuthority,
  AcmPanelComponentInstance,
  ComponentRelation,
} from "./types";
import {
  ASSEMBLY_DIMENSION_TOLERANCE_MM,
  computeAcmAssemblyExtent,
} from "./assemblyExtent";
import { resolveAcmPanelInstance } from "./resolveInstance";

export { ASSEMBLY_DIMENSION_TOLERANCE_MM } from "./assemblyExtent";

export type AcmBlueprintReadiness = "L0" | "L1-P" | "L1-C" | "L1-B";

export type AcmBlueprintCalloutStyle =
  | "solid_final"
  | "solid_subtle"
  | "dashed_proposed"
  | "dashed_catalog"
  | "warning"
  | "omitted";

export type AcmBlueprintCalloutFinality = "final" | "provisional" | "omitted";

export type AcmBlueprintPanel = {
  id: string;
  order: number;
  x_mm: number;
  y_mm: number;
  width_mm: number;
  height_mm: number;
  authority: AcmFieldAuthority | "proposed" | "unknown";
  statusLabel: string;
  label: string;
  warnings: string[];
};

export type AcmBlueprintJoint = {
  id: string;
  orientation: "VERTICAL" | "HORIZONTAL" | "UNKNOWN";
  /** Derived schematic line (no gap width). */
  x1_mm: number;
  y1_mm: number;
  x2_mm: number;
  y2_mm: number;
  statusLabel: string;
  note: string;
  authority: "proposed" | "operator_confirmed" | "unknown";
};

export type AcmBlueprintCallout = {
  id: string;
  kind: "overall_width" | "overall_height" | "panel" | "construction" | "note";
  label: string;
  value: number | null;
  unit: "mm" | null;
  authority: AcmFieldAuthority | "proposed" | "unknown" | "missing";
  style: AcmBlueprintCalloutStyle;
  finality: AcmBlueprintCalloutFinality;
  targetId?: string;
};

export type AcmBlueprintConstructionElement = {
  id: string;
  present: boolean;
  value: number | string | null;
  unit: "mm" | null;
  authority: AcmFieldAuthority | "missing" | "inactive";
  style: AcmBlueprintCalloutStyle;
  label: string;
};

export type AcmBlueprintConstructionSection = {
  face: AcmBlueprintConstructionElement;
  thickness: AcmBlueprintConstructionElement;
  l1: AcmBlueprintConstructionElement;
  l2: AcmBlueprintConstructionElement;
  foldCount: AcmBlueprintConstructionElement;
  rearClosure: AcmBlueprintConstructionElement;
  internalFrame: AcmBlueprintConstructionElement;
  mountingPlane: AcmBlueprintConstructionElement;
  warnings: string[];
};

export type AcmBlueprintRelationView = {
  relation_id: string;
  relation_type: string;
  from_component_ref: string;
  to_component_ref: string;
  status: string;
  provenance: string;
  display: "show" | "note_only" | "omit";
  note: string | null;
};

export type AcmBlueprintAssembly = {
  width_mm: number;
  height_mm: number;
  min_x_mm: number;
  min_y_mm: number;
  max_x_mm: number;
  max_y_mm: number;
  source: "panel_extent" | "assembly_dimensions" | "single_panel" | "none";
  unit: "mm";
  origin: "top_left";
  axis: { x: "+right"; y: "+down" };
};

export type AcmPanelBlueprintReadModel = {
  readiness: AcmBlueprintReadiness;
  label: string;
  disclaimer: string;
  provisionalNote: string | null;
  assembly: AcmBlueprintAssembly | null;
  panels: AcmBlueprintPanel[];
  joints: AcmBlueprintJoint[];
  callouts: AcmBlueprintCallout[];
  constructionSection: AcmBlueprintConstructionSection | null;
  relations: AcmBlueprintRelationView[];
  missing: string[];
  warnings: string[];
  blockers: string[];
  provenance: {
    instanceId: string | null;
    source: string;
    contourId: string | null;
    geometryHash: string | null;
    svgSourceHash: string | null;
    segmentedStatus: string | null;
  };
  compositionInconsistency: boolean;
  compositionInconsistencyMessage: string | null;
  letterPlacementUnknown: boolean;
  collapsedSummary: string;
};

const CRITICAL_FOR_L1C = [
  "panel_geometry",
  "fold_count",
  "l1_mm",
  "l2_mm",
  "acm_thickness_mm",
  "finished_depth_mm",
] as const;

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function num(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function formatMm(value: number): string {
  return Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10);
}

function authorityStyle(authority: AcmFieldAuthority | "proposed" | "unknown" | "missing"): {
  style: AcmBlueprintCalloutStyle;
  finality: AcmBlueprintCalloutFinality;
  statusLabel: string;
} {
  switch (authority) {
    case "operator_confirmed":
      return { style: "solid_final", finality: "final", statusLabel: "Confirmat" };
    case "detected":
      return { style: "solid_subtle", finality: "provisional", statusLabel: "Detectat" };
    case "proposed":
      return { style: "dashed_proposed", finality: "provisional", statusLabel: "Propus" };
    case "catalog_default":
      return { style: "dashed_catalog", finality: "provisional", statusLabel: "Propunere catalog" };
    case "missing":
      return { style: "omitted", finality: "omitted", statusLabel: "Lipsă" };
    case "unknown":
    default:
      return { style: "warning", finality: "provisional", statusLabel: "Necunoscut" };
  }
}

type RawPanel = {
  panel_id: string;
  order: number;
  width_mm: number | null;
  height_mm: number | null;
  x_mm: number;
  y_mm: number;
  contour_element_id?: string | null;
};

function readPanels(
  instance: AcmPanelComponentInstance | null,
  segmented: Record<string, unknown> | null,
): RawPanel[] {
  const fromInstance = instance?.geometry?.panels ?? [];
  if (fromInstance.length > 0) {
    return fromInstance.map((p, i) => ({
      panel_id: p.panel_id,
      order: p.order ?? i + 1,
      width_mm: p.width_mm,
      height_mm: p.height_mm,
      x_mm: p.position?.x_mm ?? 0,
      y_mm: p.position?.y_mm ?? 0,
      contour_element_id: p.contour_element_id,
    }));
  }
  const segPanels = Array.isArray(segmented?.panels) ? segmented!.panels : [];
  return segPanels.map((raw, i) => {
    const p = asRecord(raw);
    const pos = asRecord(p?.position);
    return {
      panel_id: String(p?.panel_id ?? `panel_${i + 1}`),
      order: num(p?.order) ?? i + 1,
      width_mm: num(p?.width_mm),
      height_mm: num(p?.height_mm),
      x_mm: num(pos?.x_mm) ?? 0,
      y_mm: num(pos?.y_mm) ?? 0,
      contour_element_id:
        typeof p?.contour_element_id === "string" ? p.contour_element_id : null,
    };
  });
}

function panelExtent(panels: Array<{ x_mm: number; y_mm: number; width_mm: number; height_mm: number }>): {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  width: number;
  height: number;
} | null {
  if (!panels.length) return null;
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const p of panels) {
    minX = Math.min(minX, p.x_mm);
    maxX = Math.max(maxX, p.x_mm + p.width_mm);
    minY = Math.min(minY, p.y_mm);
    maxY = Math.max(maxY, p.y_mm + p.height_mm);
  }
  const width = maxX - minX;
  const height = maxY - minY;
  if (!(width > 0) || !(height > 0)) return null;
  return { minX, maxX, minY, maxY, width, height };
}

function compositionInconsistency(args: {
  payload: Record<string, unknown> | null;
  instance: AcmPanelComponentInstance | null;
}): { inconsistent: boolean; message: string | null } {
  const confirmedRaw = asRecord(args.payload?.product_composition_confirmed);
  const productConfirmed = confirmedRaw?.confirmed === true;
  const instanceStatus = args.instance?.composition_status ?? null;
  if (
    productConfirmed &&
    args.instance &&
    instanceStatus &&
    instanceStatus !== "confirmed"
  ) {
    return {
      inconsistent: true,
      message:
        "Compoziția produsului este confirmată, dar composition_status pe instanța AcmPanel nu este confirmat.",
    };
  }
  return { inconsistent: false, message: null };
}

function criticalFieldsOperatorConfirmed(instance: AcmPanelComponentInstance): boolean {
  const auth = instance.configuration?.field_authority ?? {};
  return CRITICAL_FOR_L1C.every((key) => {
    if (key === "panel_geometry") {
      const a = auth.panel_geometry;
      return a === "operator_confirmed" || a === "detected";
    }
    if (key === "l2_mm" && instance.configuration.fold_count === 1) return true;
    return auth[key] === "operator_confirmed";
  });
}

function deriveJoints(
  panels: AcmBlueprintPanel[],
  rawJoints: Array<{
    joint_id: string;
    left_panel_id: string;
    right_panel_id: string;
    orientation: string;
  }>,
  segmentedStatus: string | null,
): AcmBlueprintJoint[] {
  const byId = new Map(panels.map((p) => [p.id, p]));
  const jointAuthority: AcmBlueprintJoint["authority"] =
    String(segmentedStatus ?? "").toUpperCase() === "CONFIRMED"
      ? "operator_confirmed"
      : "proposed";
  const statusLabel = jointAuthority === "operator_confirmed" ? "Confirmat" : "Propus";
  const out: AcmBlueprintJoint[] = [];

  for (const j of rawJoints) {
    const left = byId.get(j.left_panel_id);
    const right = byId.get(j.right_panel_id);
    if (!left || !right) continue;
    const orientationRaw = String(j.orientation ?? "").toUpperCase();
    const orientation: AcmBlueprintJoint["orientation"] =
      orientationRaw === "VERTICAL"
        ? "VERTICAL"
        : orientationRaw === "HORIZONTAL"
          ? "HORIZONTAL"
          : "UNKNOWN";
    if (orientation === "UNKNOWN") continue;

    if (orientation === "VERTICAL") {
      const leftEdge = left.x_mm + left.width_mm;
      const rightEdge = right.x_mm;
      if (Math.abs(leftEdge - rightEdge) > ASSEMBLY_DIMENSION_TOLERANCE_MM) continue;
      const x = (leftEdge + rightEdge) / 2;
      const y1 = Math.min(left.y_mm, right.y_mm);
      const y2 = Math.max(left.y_mm + left.height_mm, right.y_mm + right.height_mm);
      out.push({
        id: j.joint_id,
        orientation,
        x1_mm: x,
        y1_mm: y1,
        x2_mm: x,
        y2_mm: y2,
        statusLabel,
        note: "Rost schematic derivat",
        authority: jointAuthority,
      });
      continue;
    }

    const bottom = left.y_mm + left.height_mm;
    const top = right.y_mm;
    if (Math.abs(bottom - top) > ASSEMBLY_DIMENSION_TOLERANCE_MM) continue;
    const y = (bottom + top) / 2;
    const x1 = Math.min(left.x_mm, right.x_mm);
    const x2 = Math.max(left.x_mm + left.width_mm, right.x_mm + right.width_mm);
    out.push({
      id: j.joint_id,
      orientation,
      x1_mm: x1,
      y1_mm: y,
      x2_mm: x2,
      y2_mm: y,
      statusLabel,
      note: "Rost schematic derivat",
      authority: jointAuthority,
    });
  }
  return out;
}

function buildConstruction(
  instance: AcmPanelComponentInstance,
): AcmBlueprintConstructionSection {
  const cfg = instance.configuration;
  const auth = cfg.field_authority ?? {};
  const caps = new Set(instance.capabilities?.active ?? []);
  const inactive = new Set(instance.capabilities?.inactive ?? []);
  const warnings: string[] = [];

  const el = (
    id: string,
    label: string,
    present: boolean,
    value: number | string | null,
    unit: "mm" | null,
    authority: AcmFieldAuthority | "missing" | "inactive",
  ): AcmBlueprintConstructionElement => {
    if (!present || authority === "inactive") {
      return {
        id,
        present: false,
        value: null,
        unit: null,
        authority: "inactive",
        style: "omitted",
        label,
      };
    }
    if (value == null || authority === "missing") {
      return {
        id,
        present: true,
        value: null,
        unit,
        authority: "missing",
        style: "omitted",
        label,
      };
    }
    const mapped =
      authority === "operator_confirmed" ||
      authority === "detected" ||
      authority === "proposed" ||
      authority === "catalog_default"
        ? authorityStyle(authority)
        : { style: "omitted" as const, finality: "omitted" as const, statusLabel: "Lipsă" };
    return {
      id,
      present: true,
      value,
      unit,
      authority: authority as AcmFieldAuthority | "missing" | "inactive",
      style: mapped.style,
      label,
    };
  };

  if (cfg.fold_count === 1 && cfg.l2_mm != null && cfg.l2_mm > 0) {
    warnings.push("fold_count=1 dar l2_mm este prezent — verificare honesty necesară.");
  }

  const rearPresent = caps.has("rear_closure") && !inactive.has("rear_closure");
  const framePresent =
    Boolean(cfg.internal_frame_enabled) &&
    caps.has("internal_frame") &&
    !inactive.has("internal_frame");
  const mountPresent =
    (caps.has("wall_mounting") || caps.has("structure_mounting")) &&
    !(inactive.has("wall_mounting") && inactive.has("structure_mounting"));

  return {
    face: el("face", "Față", true, "ACM", null, auth.acm_thickness_mm ?? "catalog_default"),
    thickness: el(
      "thickness",
      "Grosime ACM",
      true,
      cfg.acm_thickness_mm,
      "mm",
      auth.acm_thickness_mm ?? "missing",
    ),
    l1: el("l1", "Întoarcere L1", true, cfg.l1_mm, "mm", auth.l1_mm ?? "missing"),
    l2: el(
      "l2",
      "Buză L2",
      cfg.fold_count !== 1,
      cfg.fold_count === 1 ? null : cfg.l2_mm,
      "mm",
      cfg.fold_count === 1 ? "inactive" : (auth.l2_mm ?? "missing"),
    ),
    foldCount: el(
      "fold_count",
      "Număr pliuri",
      true,
      cfg.fold_count,
      null,
      auth.fold_count ?? "missing",
    ),
    rearClosure: el("rear_closure", "Închidere spate", rearPresent, null, null, "inactive"),
    internalFrame: el(
      "internal_frame",
      "Structură interioară",
      framePresent,
      null,
      null,
      framePresent ? (auth.internal_frame ?? "catalog_default") : "inactive",
    ),
    mountingPlane: el("mounting_plane", "Plan montaj", mountPresent, null, null, "inactive"),
    warnings,
  };
}

function mapRelations(
  relations: ComponentRelation[],
): { views: AcmBlueprintRelationView[]; letterPlacementUnknown: boolean } {
  let letterPlacementUnknown = false;
  const views: AcmBlueprintRelationView[] = [];

  for (const rel of relations) {
    if (rel.relation_type === "belongs_to_assembly") {
      views.push({
        relation_id: rel.relation_id,
        relation_type: rel.relation_type,
        from_component_ref: rel.from_component_ref,
        to_component_ref: rel.to_component_ref,
        status: rel.status,
        provenance: rel.provenance,
        display: "show",
        note: null,
      });
      continue;
    }
    if (rel.relation_type === "positioned_on") {
      if (rel.status === "unknown") {
        letterPlacementUnknown = true;
        views.push({
          relation_id: rel.relation_id,
          relation_type: rel.relation_type,
          from_component_ref: rel.from_component_ref,
          to_component_ref: rel.to_component_ref,
          status: rel.status,
          provenance: rel.provenance,
          display: "note_only",
          note: "Plasarea literelor pe panou este necunoscută",
        });
      } else {
        views.push({
          relation_id: rel.relation_id,
          relation_type: rel.relation_type,
          from_component_ref: rel.from_component_ref,
          to_component_ref: rel.to_component_ref,
          status: rel.status,
          provenance: rel.provenance,
          display: "show",
          note: null,
        });
      }
      continue;
    }
    if (rel.relation_type === "contained_by") {
      views.push({
        relation_id: rel.relation_id,
        relation_type: rel.relation_type,
        from_component_ref: rel.from_component_ref,
        to_component_ref: rel.to_component_ref,
        status: rel.status,
        provenance: rel.provenance,
        display: "show",
        note: null,
      });
      continue;
    }
    if (rel.relation_type === "mounts_on") {
      if (rel.status === "confirmed" && rel.provenance === "operator") {
        views.push({
          relation_id: rel.relation_id,
          relation_type: rel.relation_type,
          from_component_ref: rel.from_component_ref,
          to_component_ref: rel.to_component_ref,
          status: rel.status,
          provenance: rel.provenance,
          display: "show",
          note: null,
        });
      }
      continue;
    }
  }

  return { views, letterPlacementUnknown };
}

export type BuildAcmPanelBlueprintReadModelArgs = {
  finishSetup?: unknown;
  payload?: Record<string, unknown> | null;
};

/**
 * Pure derivation of AcmPanel Blueprint L1 read model.
 */
export function buildAcmPanelBlueprintReadModel(
  args: BuildAcmPanelBlueprintReadModelArgs = {},
): AcmPanelBlueprintReadModel {
  const empty = (readiness: AcmBlueprintReadiness, extras?: Partial<AcmPanelBlueprintReadModel>): AcmPanelBlueprintReadModel => ({
    readiness,
    label: "Panou Alucobond casetat",
    disclaimer: "Schematic Nivel 1 provizoriu — nu este desen de execuție.",
    provisionalNote:
      readiness === "L1-P" || readiness === "L1-B"
        ? "Valorile propuse sau din catalog necesită confirmarea operatorului."
        : null,
    assembly: null,
    panels: [],
    joints: [],
    callouts: [],
    constructionSection: null,
    relations: [],
    missing: readiness === "L0" ? ["acm_panel_instance"] : [],
    warnings: [],
    blockers: [],
    provenance: {
      instanceId: null,
      source: "none",
      contourId: null,
      geometryHash: null,
      svgSourceHash: null,
      segmentedStatus: null,
    },
    compositionInconsistency: false,
    compositionInconsistencyMessage: null,
    letterPlacementUnknown: false,
    collapsedSummary: "Fără previzualizare tehnică",
    ...extras,
  });

  const payload = args.payload ?? null;
  const finish =
    args.finishSetup ?? asRecord(payload)?.finish_setup ?? null;
  const resolved = resolveAcmPanelInstance(finish);
  const instance = resolved.instance;
  if (!instance) {
    return empty("L0");
  }

  const finishRec = asRecord(finish);
  const segmented = asRecord(finishRec?.segmented_background);
  const segmentedStatus =
    typeof segmented?.status === "string" ? segmented.status : null;

  const rawPanels = readPanels(instance, segmented);
  const warnings: string[] = [];
  const blockers: string[] = [];
  const missing: string[] = [];

  const geomAuth = (instance.configuration.field_authority?.panel_geometry ??
    "detected") as AcmFieldAuthority;
  const segmentAuthority: AcmFieldAuthority | "proposed" =
    String(segmentedStatus ?? "").toUpperCase() === "CONFIRMED"
      ? geomAuth === "operator_confirmed"
        ? "operator_confirmed"
        : "detected"
      : String(segmentedStatus ?? "").toUpperCase() === "PROPOSED"
        ? "proposed"
        : geomAuth;

  const validPanels: AcmBlueprintPanel[] = [];
  let geometryBlocked = false;

  if (rawPanels.length === 0) {
    const w = num(instance.geometry.width_mm);
    const h = num(instance.geometry.height_mm);
    if (w != null && h != null && w > 0 && h > 0) {
      validPanels.push({
        id: instance.geometry.element_id ?? instance.component_instance_id,
        order: 1,
        x_mm: 0,
        y_mm: 0,
        width_mm: w,
        height_mm: h,
        authority: geomAuth,
        statusLabel: authorityStyle(geomAuth).statusLabel,
        label: "Panou",
        warnings: [],
      });
    } else {
      geometryBlocked = true;
      missing.push("panel_geometry");
    }
  } else {
    for (const p of rawPanels) {
      const w = p.width_mm;
      const h = p.height_mm;
      if (w == null || h == null || !(w > 0) || !(h > 0) || !Number.isFinite(p.x_mm) || !Number.isFinite(p.y_mm)) {
        geometryBlocked = true;
        warnings.push(`Panou ${p.panel_id}: dimensiuni/poziție invalide.`);
        continue;
      }
      validPanels.push({
        id: p.panel_id,
        order: p.order,
        x_mm: p.x_mm,
        y_mm: p.y_mm,
        width_mm: w,
        height_mm: h,
        authority: segmentAuthority,
        statusLabel: authorityStyle(segmentAuthority).statusLabel,
        label: `Panou ${p.order}`,
        warnings: [],
      });
    }
    if (rawPanels.length > 0 && validPanels.length === 0) {
      geometryBlocked = true;
    }
  }

  const extent = panelExtent(validPanels);
  if (geometryBlocked || !extent) {
    const comp = compositionInconsistency({ payload, instance });
    return empty("L1-B", {
      missing,
      warnings,
      blockers: ["Geometrie panouri contradictorie sau insuficientă pentru schematic."],
      provenance: {
        instanceId: instance.component_instance_id,
        source: resolved.source,
        contourId: instance.geometry.contour_id,
        geometryHash: instance.geometry.geometry_hash,
        svgSourceHash: instance.svg_source_hash,
        segmentedStatus,
      },
      compositionInconsistency: comp.inconsistent,
      compositionInconsistencyMessage: comp.message,
      collapsedSummary: "L1-B · Geometrie blocată",
      constructionSection: buildConstruction(instance),
    });
  }

  // Normalize to assembly origin top-left (minX, minY) → (0,0) for renderer space
  const originX = extent.minX;
  const originY = extent.minY;
  const panels: AcmBlueprintPanel[] = validPanels
    .map((p) => ({
      ...p,
      x_mm: p.x_mm - originX,
      y_mm: p.y_mm - originY,
    }))
    .sort((a, b) => a.order - b.order);

  const asmDims = asRecord(segmented?.assembly_dimensions);
  const extentResult = computeAcmAssemblyExtent({
    panels: validPanels.map((p) => ({
      width_mm: p.width_mm,
      height_mm: p.height_mm,
      x_mm: p.x_mm,
      y_mm: p.y_mm,
    })),
    assembly_dimensions: asmDims
      ? {
          width_mm: num(asmDims.width_mm),
          height_mm: num(asmDims.height_mm),
        }
      : null,
    envelope_width_mm: num(instance.geometry.width_mm),
    envelope_height_mm: num(instance.geometry.height_mm),
  });
  for (const w of extentResult.warnings) {
    warnings.push(w);
  }
  const assemblyWidth = extentResult.assembly_width_mm ?? extent.width;
  const assemblyHeight = extentResult.assembly_height_mm ?? extent.height;
  const assemblySource: AcmBlueprintAssembly["source"] = extentResult.source;

  const assembly: AcmBlueprintAssembly = {
    width_mm: assemblyWidth,
    height_mm: assemblyHeight,
    min_x_mm: 0,
    min_y_mm: 0,
    max_x_mm: assemblyWidth,
    max_y_mm: assemblyHeight,
    source: assemblySource,
    unit: "mm",
    origin: "top_left",
    axis: { x: "+right", y: "+down" },
  };

  const rawJoints = (instance.geometry.joints?.length
    ? instance.geometry.joints
    : Array.isArray(segmented?.joints)
      ? (segmented!.joints as Array<{
          joint_id: string;
          left_panel_id: string;
          right_panel_id: string;
          orientation: string;
        }>)
      : []
  ).map((j) => ({
    joint_id: j.joint_id,
    left_panel_id: j.left_panel_id,
    right_panel_id: j.right_panel_id,
    orientation: j.orientation,
  }));

  // Joints derived in normalized panel space
  const joints = deriveJoints(panels, rawJoints, segmentedStatus);

  const overallAuth: AcmFieldAuthority | "proposed" =
    panels.length > 1 && String(segmentedStatus ?? "").toUpperCase() === "PROPOSED"
      ? "proposed"
      : geomAuth;
  const overallStyle = authorityStyle(overallAuth);

  const callouts: AcmBlueprintCallout[] = [
    {
      id: "overall_width",
      kind: "overall_width",
      label: "Lățime ansamblu",
      value: assemblyWidth,
      unit: "mm",
      authority: overallAuth,
      style: overallStyle.style,
      finality: overallStyle.finality,
      targetId: "assembly",
    },
    {
      id: "overall_height",
      kind: "overall_height",
      label: "Înălțime ansamblu",
      value: assemblyHeight,
      unit: "mm",
      authority: overallAuth,
      style: overallStyle.style,
      finality: overallStyle.finality,
      targetId: "assembly",
    },
  ];

  for (const p of panels) {
    const st = authorityStyle(p.authority);
    callouts.push({
      id: `panel_${p.id}_w`,
      kind: "panel",
      label: `${p.label} lățime`,
      value: p.width_mm,
      unit: "mm",
      authority: p.authority,
      style: st.style,
      finality: st.finality,
      targetId: p.id,
    });
    callouts.push({
      id: `panel_${p.id}_h`,
      kind: "panel",
      label: `${p.label} înălțime`,
      value: p.height_mm,
      unit: "mm",
      authority: p.authority,
      style: st.style,
      finality: st.finality,
      targetId: p.id,
    });
  }

  const constructionSection = buildConstruction(instance);
  warnings.push(...constructionSection.warnings);

  for (const key of ["acm_thickness_mm", "l1_mm", "l2_mm", "fold_count"] as const) {
    const el =
      key === "acm_thickness_mm"
        ? constructionSection.thickness
        : key === "l1_mm"
          ? constructionSection.l1
          : key === "l2_mm"
            ? constructionSection.l2
            : constructionSection.foldCount;
    if (!el.present || el.style === "omitted" || el.value == null) {
      if (key === "l2_mm" && instance.configuration.fold_count === 1) continue;
      if (el.authority === "missing") missing.push(key);
      continue;
    }
    const auth = el.authority === "inactive" || el.authority === "missing"
      ? "missing"
      : el.authority;
    const st = authorityStyle(auth);
    callouts.push({
      id: `construction_${key}`,
      kind: "construction",
      label: el.label,
      value: typeof el.value === "number" ? el.value : null,
      unit: el.unit,
      authority: auth,
      style: st.style,
      finality: st.finality,
    });
  }

  const { views: relationViews, letterPlacementUnknown } = mapRelations(
    instance.relations ?? [],
  );
  if (letterPlacementUnknown) {
    warnings.push("Plasarea literelor pe panou este necunoscută");
  }

  const comp = compositionInconsistency({ payload, instance });
  if (comp.inconsistent && comp.message) {
    warnings.push(comp.message);
  }

  const multiPanel =
    panels.length > 1 || String(segmentedStatus ?? "").toUpperCase() === "PROPOSED";
  const segmentedOkForL1C =
    !multiPanel ||
    String(segmentedStatus ?? "").toUpperCase() === "CONFIRMED" ||
    String(segmentedStatus ?? "").toUpperCase() === "SINGLE_PANEL";

  const l1c =
    instance.association_status === "confirmed" &&
    instance.technical_configuration_status === "confirmed" &&
    criticalFieldsOperatorConfirmed(instance) &&
    segmentedOkForL1C &&
    !comp.inconsistent &&
    blockers.length === 0 &&
    assembly.width_mm > 0 &&
    assembly.height_mm > 0;

  // Fixture / typical path stays L1-P; never fabricate L1-C from partial confirmations
  const readiness: AcmBlueprintReadiness = l1c ? "L1-C" : "L1-P";

  const collapsedSummary = `${readiness} · ${
    readiness === "L1-C" ? "Confirmat" : "Provizoriu"
  } · ${formatMm(assemblyWidth)} × ${formatMm(assemblyHeight)} mm · ${panels.length} panouri`;

  return {
    readiness,
    label: "Panou Alucobond casetat",
    disclaimer: "Schematic Nivel 1 provizoriu — nu este desen de execuție.",
    provisionalNote:
      readiness === "L1-P"
        ? "Valorile propuse sau din catalog necesită confirmarea operatorului."
        : null,
    assembly,
    panels,
    joints,
    callouts,
    constructionSection,
    relations: relationViews,
    missing,
    warnings,
    blockers,
    provenance: {
      instanceId: instance.component_instance_id,
      source: resolved.source,
      contourId: instance.geometry.contour_id,
      geometryHash: instance.geometry.geometry_hash,
      svgSourceHash: instance.svg_source_hash,
      segmentedStatus,
    },
    compositionInconsistency: comp.inconsistent,
    compositionInconsistencyMessage: comp.message,
    letterPlacementUnknown,
    collapsedSummary,
  };
}
