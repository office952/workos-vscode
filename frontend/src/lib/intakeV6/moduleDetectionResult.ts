import type {
  ConfidenceLevel,
  LayerKind,
  SvgAnalysisCoreReport,
} from "@/lib/svgAnalyzer";
import type {
  LayerAutoRole,
  LayerPaintEvidence,
  LayerProductionHint,
  LayerRoleCandidate,
  LayerRoleConfirmation,
  LayerRoleConfirmationStatus,
} from "@/lib/svgAnalyzer/analyzer/layerRoleTypes";

/** Step 1 detection contract — not ProductDefinition, cost, quote, or order. */
export const MODULE_DETECTION_RESULT_SCHEMA_VERSION = "module_detection_result_v1" as const;

export type ModuleDetectionResultSchemaVersion = typeof MODULE_DETECTION_RESULT_SCHEMA_VERSION;

export type ModuleDetectionSource = "svg_analyzer" | "ai_interpreter" | "combined";

export type DetectedModuleKind =
  | "volumetric_letters"
  | "printed_artwork"
  | "logo"
  | "support_structure"
  | "unknown";

export interface DetectedLayerGeometry {
  width_mm: number | null;
  height_mm: number | null;
  bounding_area_sqm: number | null;
  filled_area_sqm: number | null;
  perimeter_mm: number | null;
  path_element_count: number;
  closed_sub_path_count: number;
}

export interface DetectedLayer {
  layer_key: string;
  layer_id: string;
  layer_name: string;
  layer_kind?: LayerKind;
  layer_origin?: string | null;
  auto_role: LayerAutoRole;
  auto_confidence: ConfidenceLevel;
  paint_evidence: LayerPaintEvidence;
  production_hint: LayerProductionHint;
  role_reason?: string | null;
  geometry: DetectedLayerGeometry;
  layer_warnings: Array<{ code: string; message: string; severity: string }>;
  has_letter_path_geometry: boolean;
  is_artwork_candidate: boolean;
}

export interface RoleCandidateEntry {
  layer_key: string;
  layer_name: string;
  auto_role: LayerAutoRole;
  auto_confidence: ConfidenceLevel;
  candidates: LayerRoleCandidate[];
}

export interface DetectedModule {
  module_key: string;
  module_kind: DetectedModuleKind;
  source_layer_keys: string[];
  confidence: ConfidenceLevel;
  detection_reason: string;
}

export interface ModuleDetectionWarning {
  code: string;
  message: string;
  severity: "info" | "warning" | "error";
  scope?: string;
  target_id?: string;
}

export interface ModuleDetectionBlocker {
  code: string;
  message?: string;
}

/** Placeholder for future Product Form System — populated by recommendation engine later. */
export interface RecommendedFormStub {
  form_id: string;
  reason: string;
  confidence: ConfidenceLevel;
}

/** Placeholder for future Template Recommendation Engine — populated later. */
export interface RecommendedTemplateStub {
  template_code: string;
  reason: string;
  confidence: ConfidenceLevel;
}

export interface ModuleDetectionRawAnalyzerSummary {
  analyzer_schema_version: string;
  engine_version: string;
  created_at: string;
  layer_count: number;
  confirmation_status: LayerRoleConfirmationStatus;
  artwork_only_requires_decision: boolean;
  document_confidence: ConfidenceLevel;
}

export interface ModuleDetectionResult {
  schema_version: ModuleDetectionResultSchemaVersion;
  source: ModuleDetectionSource;
  analysis_hash?: string;
  source_file_name?: string;
  detected_layers: DetectedLayer[];
  detected_modules: DetectedModule[];
  role_candidates: RoleCandidateEntry[];
  warnings: ModuleDetectionWarning[];
  blockers: ModuleDetectionBlocker[];
  recommended_forms: RecommendedFormStub[];
  recommended_templates: RecommendedTemplateStub[];
  requires_operator_confirmation: boolean;
  raw_analyzer_summary?: ModuleDetectionRawAnalyzerSummary;
}

export interface MapModuleDetectionOptions {
  analysisHash?: string | null;
  source?: ModuleDetectionSource;
  /** Override confirmation draft; defaults to report.layerRoleConfirmation. */
  layerRoleConfirmation?: LayerRoleConfirmation | null;
}

export type ModuleDetectionMapperInput = SvgAnalysisCoreReport;
