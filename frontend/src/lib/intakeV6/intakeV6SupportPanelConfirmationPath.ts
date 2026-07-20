/**
 * Intake adapter: support_panel role confirm → atomic AcmPanel instantiation.
 * SUPPORT_CONTOUR is the letters-on-support geometry-role adapter, not the universal ACM definition.
 * Does NOT auto-confirm product composition.
 */

import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import type { SvgBindableComponent } from "@/lib/api";
import type { SvgComponentBinding } from "./svgComponentBindings";
import type { SegmentedBackground } from "./segmentedBackground";
import type { IntakeV6FinishSetup } from "./intakeV6Api";
import {
  buildAtomicAcmPanelInstantiationPatch,
  type AtomicAcmPanelInstantiationResult,
} from "./acmPanel";

export type SupportPanelConfirmationPathResult = {
  ok: boolean;
  blockers: string[];
  finishPatch: Partial<IntakeV6FinishSetup> | null;
  /** @deprecated Prefer finishPatch.segmented_background — kept for call-site compat. */
  segmentedProposal: SegmentedBackground | null;
  mergedBindings: SvgComponentBinding[];
  contourId: string | null;
  instance: AtomicAcmPanelInstantiationResult["instance"];
};

export function buildSupportPanelConfirmationPath(args: {
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  finishSetup: IntakeV6FinishSetup | Record<string, unknown> | null | undefined;
  bindables: SvgBindableComponent[];
  svgSourceHash: string | null;
}): SupportPanelConfirmationPathResult {
  const atomic = buildAtomicAcmPanelInstantiationPatch(args);
  if (!atomic.ok) {
    return {
      ok: false,
      blockers: atomic.blockers,
      finishPatch: null,
      segmentedProposal: null,
      mergedBindings: [],
      contourId: atomic.contourId,
      instance: null,
    };
  }
  if (!atomic.finishPatch) {
    return {
      ok: true,
      blockers: [],
      finishPatch: null,
      segmentedProposal: null,
      mergedBindings: [],
      contourId: null,
      instance: null,
    };
  }
  const seg =
    (atomic.finishPatch.segmented_background as SegmentedBackground | undefined) ?? null;
  return {
    ok: true,
    blockers: [],
    finishPatch: atomic.finishPatch as Partial<IntakeV6FinishSetup>,
    segmentedProposal: seg,
    mergedBindings: atomic.mergedBindings,
    contourId: atomic.contourId,
    instance: atomic.instance,
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
