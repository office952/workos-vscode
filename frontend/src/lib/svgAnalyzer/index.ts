export { analyzeSvgString } from "./analyzer/analyzeSvg";
export type { AnalyzeSvgEngineResult, AnalyzeOptions } from "./analyzer/analyzeSvg";
export type { SvgAnalysisReport, ParsedSvgDocument, SvgAnalysisCoreReport } from "./analyzer/types";
export type { LayerRoleConfirmation, LayerAutoRole, LayerConfirmationState } from "./analyzer/layerRoleTypes";
export { buildLayerRoleConfirmationDraft } from "./analyzer/buildLayerRoleConfirmation";
export {
  applyLayerRoleSelection,
  updateLayerRoleConfirmationEntry,
} from "./lib/layerRoleConfirmationState";
export { LAYER_ROLE_OPTIONS } from "./analyzer/layerRoleTypes";
export { detectClosedContourCandidates, findCandidateById } from "./closed-contour/closedContourCandidates";
export type {
  ClosedContourCandidate,
  ClosedContourDetectionReport,
  SvgSupportSelectionState,
  ContourRoleOption,
} from "./closed-contour/closedContourTypes";
export {
  confirmAlucobondSelection,
  readSvgSupportSelection,
  buildAcmMountingSolutionFromSelection,
  reconcileSelectionAfterReanalysis,
  casingRequirementsActive,
  blankPreviewMm,
  emptySvgSupportSelection,
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
} from "./closed-contour/alucobondCasedPanelSelection";
