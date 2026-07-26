/**
 * Associate primary closed-contour geometry with ACM panel component (Intake adapter).
 * Uses proposed association/technical — not operator-confirmed selection.
 */

import type { ClosedContourCandidate, SvgAnalysisReport } from "@/lib/svgAnalyzer";
import { emptySvgSupportSelection } from "@/lib/svgAnalyzer";
import {
  proposeAlucobondSelection,
  buildAcmMountingSolutionProposed,
} from "./acmPanel/instantiate";
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
  acm_panel_domain_action?: "upsert" | "clear";
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
  const result = proposeAlucobondSelection({
    candidate: target,
    svg_source_hash: args.svgSourceHash ?? "",
    unit_ambiguity: Boolean(args.report.closedContourCandidates?.unit_ambiguity),
  });
  if (result.blockers.length) {
    return { patch: null, blockers: result.blockers, contourId: target.contour_id };
  }
  const supportBinding = bindingFromSupportSelection(result.selection as never);
  const prev = readSvgComponentBindings(args.finishSetup);
  return {
    patch: {
      acm_panel_domain_action: "upsert",
      svg_support_selection: result.selection as never,
      svg_component_bindings: supportBinding ? upsertBinding(prev, supportBinding) : prev,
      mounting_solution: buildAcmMountingSolutionProposed(result.selection as never),
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
    acm_panel_domain_action: "clear",
    svg_support_selection: emptySvgSupportSelection(),
    svg_component_bindings: prev.filter((b) => b.component_template_code !== code),
    mounting_solution: null,
    power_supply_service_corner: null,
  };
}
