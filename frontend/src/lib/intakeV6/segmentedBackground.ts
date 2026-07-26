/**
 * Segmented ACM/ACP background — analyzer proposal + operator confirmation helpers.
 * Authority: operator confirm writes finish_setup.segmented_background CONFIRMED.
 * Analyzer never auto-confirms.
 */

import type { ClosedContourCandidate } from "@/lib/svgAnalyzer/closed-contour/closedContourTypes";
import { segmentedAssemblyStatusLabelRo } from "./intakeV6OperatorVocabulary";

export const SEGMENTED_BACKGROUND_SCHEMA = "acm_segmented_background_v1";

export type SegmentedBackgroundStatus =
  | "SINGLE_PANEL"
  | "PROPOSED"
  | "CONFIRMED"
  | "REJECTED"
  | "INACTIVE";

export type SegmentedConstructionType =
  | "APPLIED_VOLUMETRIC_LETTER"
  | "SIMPLE_APPLIED"
  | "CUTOUT"
  | "ACRYLIC_INSERT";

export interface SegmentedPanel {
  panel_id: string;
  order: number;
  width_mm: number | null;
  height_mm: number | null;
  position: { x_mm: number; y_mm: number };
  contour_element_id?: string | null;
}

export interface SegmentedJoint {
  joint_id: string;
  left_panel_id: string;
  right_panel_id: string;
  orientation: string;
}

export interface SegmentedElementBinding {
  binding_id: string;
  element_ref?: string | null;
  construction_type: SegmentedConstructionType;
  primary_panel_id: string | null;
  secondary_panel_id?: string | null;
  crosses_joint: boolean;
  joint_id?: string | null;
  crossing_classification?: string;
  mount_strategy?: string;
  panel_alignment_dependency?: boolean;
  cable_passage_context?: boolean;
  applied_component_template_code?: string | null;
  does_not_absorb_letter_ownership?: boolean;
}

export interface SegmentedBackground {
  schema: typeof SEGMENTED_BACKGROUND_SCHEMA;
  contract_version?: string;
  status: SegmentedBackgroundStatus;
  assembly_id?: string;
  operator_confirmed?: boolean;
  graphic_continuity?: boolean;
  panels: SegmentedPanel[];
  joints: SegmentedJoint[];
  assembly_dimensions?: { width_mm?: number | null; height_mm?: number | null };
  element_bindings: SegmentedElementBinding[];
  detection?: Record<string, unknown> | null;
  validation?: {
    blockers?: Array<{ code: string; level: string; message: string }>;
    warnings?: Array<{ code: string; level: string; message: string }>;
    infos?: Array<{ code: string; level: string; message: string }>;
  };
  confirmation?: { message_code?: string; message?: string; authority?: string };
  electrical_connection_management?: Record<string, unknown> | null;
}

export const SEGMENTED_MESSAGES_RO = {
  proposal:
    "Am gasit mai multe fundaluri apropiate care pot forma un singur ansamblu. Verifica panourile si confirma.",
  distributed: "Grafica este impartita pe mai multe panouri. Verifica ordinea si continuitatea.",
  appliedCrossing: "Aceasta litera trece peste imbinare si necesita montaj in doua etape.",
  cutoutBlocker: "O litera sau un decupaj trece peste imbinare. Muta imbinarea sau modifica grafica.",
  insertBlocker:
    "Elementul din plexiglas de 10 mm trece peste imbinare. Muta imbinarea sau modifica grafica.",
  rejected: "Propunerea nu a fost confirmata. Nu se salveaza un ansamblu segmentat.",
  confirmed: "Ansamblul din mai multe panouri a fost confirmat.",
} as const;

function nearGapMm(a: ClosedContourCandidate, b: ClosedContourCandidate): number {
  const aRight = a.bbox.x + a.bbox.width;
  const bRight = b.bbox.x + b.bbox.width;
  const horizontalGap = Math.max(0, Math.max(a.bbox.x, b.bbox.x) - Math.min(aRight, bRight));
  const aBottom = a.bbox.y + a.bbox.height;
  const bBottom = b.bbox.y + b.bbox.height;
  const verticalGap = Math.max(0, Math.max(a.bbox.y, b.bbox.y) - Math.min(aBottom, bBottom));
  return Math.min(horizontalGap, verticalGap);
}

function similarHeight(a: ClosedContourCandidate, b: ClosedContourCandidate): boolean {
  const ha = Math.max(a.height_mm, 1);
  const hb = Math.max(b.height_mm, 1);
  const ratio = Math.min(ha, hb) / Math.max(ha, hb);
  return ratio >= 0.85;
}

/**
 * Select panel-like closed contours that may form one assembly.
 * Proposal only — never auto-confirms.
 */
export function selectNearbySupportCandidates(
  candidates: ClosedContourCandidate[],
): ClosedContourCandidate[] {
  const ranked = [...candidates]
    .filter((c) => c.is_closed && c.width_mm > 50 && c.height_mm > 50)
    .sort((a, b) => {
      if (a.is_outer_candidate !== b.is_outer_candidate) return a.is_outer_candidate ? -1 : 1;
      return b.confidence - a.confidence;
    });

  if (ranked.length < 2) return [];

  // Prefer outer candidates; fallback to top-2 by area if only one outer.
  const outers = ranked.filter((c) => c.is_outer_candidate);
  const pool = outers.length >= 2 ? outers : ranked.slice(0, Math.min(4, ranked.length));

  const seed = pool[0];
  const group: ClosedContourCandidate[] = [seed];
  for (const c of pool.slice(1)) {
    if (!similarHeight(seed, c)) continue;
    if (nearGapMm(seed, c) > 80) continue; // mm gap in candidate bbox space (already mm)
    group.push(c);
  }

  if (group.length < 2) {
    // Adjacent left-right by x if heights match among top two
    const top = pool.slice(0, 2).sort((a, b) => a.bbox.x - b.bbox.x);
    if (top.length === 2 && similarHeight(top[0], top[1]) && nearGapMm(top[0], top[1]) <= 120) {
      return top;
    }
    return [];
  }

  return group.sort((a, b) => a.bbox.x - b.bbox.x || a.bbox.y - b.bbox.y);
}

export function proposeSegmentedBackgroundFromCandidates(
  candidates: ClosedContourCandidate[],
  options?: {
    elementBindings?: SegmentedElementBinding[];
    assemblyId?: string;
  },
): SegmentedBackground | null {
  const group = selectNearbySupportCandidates(candidates);
  if (group.length < 2) return null;

  let xCursor = 0;
  const panels: SegmentedPanel[] = group.map((c, i) => {
    const panel: SegmentedPanel = {
      panel_id: `panel_${i + 1}`,
      order: i + 1,
      width_mm: c.width_mm,
      height_mm: c.height_mm,
      position: { x_mm: xCursor, y_mm: 0 },
      contour_element_id: c.element_id || c.contour_id,
    };
    xCursor += c.width_mm;
    return panel;
  });

  const joints: SegmentedJoint[] = [];
  for (let i = 0; i < panels.length - 1; i += 1) {
    const left = panels[i].panel_id;
    const right = panels[i + 1].panel_id;
    joints.push({
      joint_id: `joint_${left}_${right}`,
      left_panel_id: left,
      right_panel_id: right,
      orientation: "VERTICAL",
    });
  }

  const heights = panels.map((p) => p.height_mm).filter((h): h is number => h != null);
  const height =
    heights.length && heights.every((h) => h === heights[0]) ? heights[0] : heights[0] ?? null;

  return {
    schema: SEGMENTED_BACKGROUND_SCHEMA,
    contract_version: "acm_segmented_background/v1",
    status: "PROPOSED",
    assembly_id: options?.assemblyId || `asm_${panels.map((p) => p.contour_element_id).join("_")}`.slice(0, 48),
    operator_confirmed: false,
    graphic_continuity: true,
    panels,
    joints,
    assembly_dimensions: {
      width_mm: panels.reduce((sum, p) => sum + (p.width_mm || 0), 0),
      height_mm: height,
    },
    element_bindings: options?.elementBindings || [],
    detection: {
      source: "svg_analyzer_proposal",
      nearby_support_count: panels.length,
      message_code: "SEGMENTATION_PROPOSAL",
      message: SEGMENTED_MESSAGES_RO.proposal,
      authority: "PROPOSAL_ONLY",
    },
    validation: {
      blockers: [],
      warnings: [],
      infos: [{ code: "SEGMENTATION_PROPOSAL", level: "info", message: SEGMENTED_MESSAGES_RO.proposal }],
    },
  };
}

export function readSegmentedBackground(
  finish: Record<string, unknown> | null | undefined,
): SegmentedBackground | null {
  const raw = finish?.segmented_background;
  if (!raw || typeof raw !== "object") return null;
  const row = raw as SegmentedBackground;
  if (row.schema && row.schema !== SEGMENTED_BACKGROUND_SCHEMA) return null;
  return row;
}

export function buildConfirmSegmentedBackgroundPatch(
  current: SegmentedBackground,
): { segmented_background: SegmentedBackground } {
  return {
    segmented_background: {
      ...current,
      status: "CONFIRMED",
      operator_confirmed: true,
      confirmation: {
        message_code: "ASSEMBLY_CONFIRMED",
        message: SEGMENTED_MESSAGES_RO.confirmed,
        authority: "OPERATOR",
      },
    },
  };
}

export function buildRejectSegmentedBackgroundPatch(
  current: SegmentedBackground | null,
): { segmented_background: SegmentedBackground } {
  return {
    segmented_background: {
      schema: SEGMENTED_BACKGROUND_SCHEMA,
      contract_version: "acm_segmented_background/v1",
      status: "REJECTED",
      operator_confirmed: false,
      assembly_id: current?.assembly_id,
      graphic_continuity: current?.graphic_continuity ?? true,
      panels: current?.panels || [],
      joints: current?.joints || [],
      assembly_dimensions: current?.assembly_dimensions,
      element_bindings: [],
      detection: current?.detection || null,
      confirmation: {
        message_code: "PROPOSAL_REJECTED",
        message: SEGMENTED_MESSAGES_RO.rejected,
        authority: "OPERATOR",
      },
      validation: {
        blockers: [],
        warnings: [],
        infos: [{ code: "PROPOSAL_REJECTED", level: "info", message: SEGMENTED_MESSAGES_RO.rejected }],
      },
    },
  };
}

export function confirmationBlocked(config: SegmentedBackground | null): string[] {
  if (!config) return ["segmented_background_missing"];
  const messages: string[] = [];
  if ((config.panels || []).length < 2) {
    messages.push("Un ansamblu segmentat necesita cel putin doua panouri.");
  }
  const ids = (config.panels || []).map((p) => p.panel_id);
  if (new Set(ids).size !== ids.length) {
    messages.push("Exista panouri cu acelasi identificator. Corecteaza identificatorii.");
  }
  for (const b of config.element_bindings || []) {
    if (!b.crosses_joint) continue;
    if (b.construction_type === "CUTOUT") messages.push(SEGMENTED_MESSAGES_RO.cutoutBlocker);
    if (b.construction_type === "ACRYLIC_INSERT") messages.push(SEGMENTED_MESSAGES_RO.insertBlocker);
  }
  for (const b of config.validation?.blockers || []) {
    if (b.message) messages.push(b.message);
  }
  return [...new Set(messages)];
}

export function statusLabelRo(status: SegmentedBackgroundStatus | string | undefined): string {
  return segmentedAssemblyStatusLabelRo(status);
}
