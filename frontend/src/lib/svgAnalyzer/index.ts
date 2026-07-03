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
