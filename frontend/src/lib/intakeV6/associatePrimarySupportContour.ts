/**
 * Associate primary closed-contour geometry with live ACM support component.
 * Used from canonical layer role Contur suport — not a parallel UI SoT.
 */

import type { ClosedContourCandidate, SvgAnalysisReport } from "@/lib/svgAnalyzer";
import {
  buildAcmMountingSolutionFromSelection,
  confirmAlucobondSelection,
  emptySvgSupportSelection,
} from "@/lib/svgAnalyzer";
import {
  bindingFromSupportSelection,
  readSvgComponentBindings,
  upsertBinding,
  type SvgComponentBinding,
} from "./svgComponentBindings";

export function resolvePrimaryClosedContourCandidate(
  candidates: ClosedContourCandidate[] | undefined | null,
): ClosedContourCandidate | null {
  if (!candidates?.length) return null;
  return candidates.find((c) => c.is_outer_candidate) ?? candidates[0] ?? null;
}

export type SupportContourPersistPatch = {
  svg_support_selection: Record<string, unknown> | null;
  svg_component_bindings: SvgComponentBinding[];
  mounting_solution: Record<string, unknown> | null;
  power_supply_service_corner?: string | null;
};

export function buildAssociatePrimarySupportContourPatch(args: {
  report: SvgAnalysisReport;
  finishSetup: Record<string, unknown> | null | undefined;
  svgSourceHash: string | null | undefined;
  candidate?: ClosedContourCandidate | null;
}): { patch: SupportContourPersistPatch | null; blockers: string[]; contourId: string | null } {
  const candidates = args.report.closedContourCandidates?.candidates ?? [];
  const target = args.candidate ?? resolvePrimaryClosedContourCandidate(candidates);
  if (!target) {
    return {
      patch: null,
      blockers: ["Nu există un contur închis candidabil pentru Contur suport."],
      contourId: null,
    };
  }
  const result = confirmAlucobondSelection({
    candidate: target,
    svg_source_hash: args.svgSourceHash ?? "",
    fold_count: 2,
    l1_mm: 60,
    l2_mm: 25,
    service_corner: null,
    internal_frame_enabled: false,
    unit_ambiguity: Boolean(args.report.closedContourCandidates?.unit_ambiguity),
  });
  if (result.blockers.length) {
    return { patch: null, blockers: result.blockers, contourId: target.contour_id };
  }
  const supportBinding = bindingFromSupportSelection(result.selection);
  const prev = readSvgComponentBindings(args.finishSetup);
  return {
    patch: {
      svg_support_selection: result.selection,
      svg_component_bindings: supportBinding ? upsertBinding(prev, supportBinding) : prev,
      mounting_solution: buildAcmMountingSolutionFromSelection(result.selection),
      power_supply_service_corner: result.selection.service_corner,
    },
    blockers: [],
    contourId: target.contour_id,
  };
}

export function buildClearSupportContourPatch(args: {
  finishSetup: Record<string, unknown> | null | undefined;
  componentTemplateCode?: string;
}): SupportContourPersistPatch {
  const code = args.componentTemplateCode ?? "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
  const prev = readSvgComponentBindings(args.finishSetup);
  return {
    svg_support_selection: emptySvgSupportSelection(),
    svg_component_bindings: prev.filter((b) => b.component_template_code !== code),
    mounting_solution: null,
    power_supply_service_corner: null,
  };
}
