/**
 * Shared domain path when support_panel is confirmed (manual select OR Confirm All).
 * Proposes segmented_background (never auto-confirms) and SUPPORT_CONTOUR bindings.
 */

import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import {
  buildAssociatePrimarySupportContourPatch,
} from "./associatePrimarySupportContour";
import type { SvgBindableComponent } from "@/lib/api";
import {
  buildLayerRoleComponentBindings,
  readSvgComponentBindings,
  type SvgComponentBinding,
} from "./svgComponentBindings";
import {
  proposeSegmentedBackgroundFromCandidates,
  readSegmentedBackground,
  type SegmentedBackground,
} from "./segmentedBackground";
import type { IntakeV6FinishSetup } from "./intakeV6Api";

export type SupportPanelConfirmationPathResult = {
  ok: boolean;
  blockers: string[];
  finishPatch: Partial<IntakeV6FinishSetup> | null;
  segmentedProposal: SegmentedBackground | null;
  mergedBindings: SvgComponentBinding[];
  contourId: string | null;
};

export function buildSupportPanelConfirmationPath(args: {
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  finishSetup: IntakeV6FinishSetup | Record<string, unknown> | null | undefined;
  bindables: SvgBindableComponent[];
  svgSourceHash: string | null;
}): SupportPanelConfirmationPathResult {
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
      segmentedProposal: null,
      mergedBindings: [],
      contourId: null,
    };
  }

  if (!report.closedContourCandidates?.candidate_count) {
    return {
      ok: false,
      blockers: [
        "Contur suport necesită candidați closed-contour din analiza SVG. Reîncarcă fișierul SVG, apoi confirmă Contur suport.",
      ],
      finishPatch: null,
      segmentedProposal: null,
      mergedBindings: [],
      contourId: null,
    };
  }

  const previous = readSvgComponentBindings(finishSetup);
  const letterLogoBindings = buildLayerRoleComponentBindings({
    confirmation,
    bindables,
    sourceSvgHash: svgSourceHash,
    previous,
  });

  const { patch, contourId, blockers } = buildAssociatePrimarySupportContourPatch({
    report,
    finishSetup,
    svgSourceHash,
  });

  if (blockers.length || !patch) {
    return {
      ok: false,
      blockers:
        blockers.length > 0
          ? blockers
          : ["Nu s-a putut asocia Panou Alucobond casetat. Verifică geometria conturului."],
      finishPatch: null,
      segmentedProposal: null,
      mergedBindings: [],
      contourId: null,
    };
  }

  const mergedBindings = [
    ...letterLogoBindings.filter((b) => b.geometry_role !== "SUPPORT_CONTOUR"),
    ...patch.svg_component_bindings.filter((b) => b.geometry_role === "SUPPORT_CONTOUR"),
  ];

  const existingSeg = readSegmentedBackground(finishSetup as Record<string, unknown> | null);
  const existingStatus = String(existingSeg?.status || "").toUpperCase();
  let segmentedProposal: SegmentedBackground | null = null;
  if (existingStatus !== "CONFIRMED" && existingStatus !== "REJECTED") {
    segmentedProposal =
      proposeSegmentedBackgroundFromCandidates(report.closedContourCandidates?.candidates || []) ??
      null;
  }

  return {
    ok: true,
    blockers: [],
    finishPatch: {
      ...patch,
      svg_component_bindings: mergedBindings,
    },
    segmentedProposal,
    mergedBindings,
    contourId,
  };
}

export function confirmationIncludesConfirmedSupportPanel(
  confirmation: LayerRoleConfirmation | null | undefined,
): boolean {
  if (!confirmation) return false;
  return confirmation.layers.some(
    (layer) =>
      layer.confirmedRole === "support_panel" && layer.confirmationState === "confirmed",
  );
}
