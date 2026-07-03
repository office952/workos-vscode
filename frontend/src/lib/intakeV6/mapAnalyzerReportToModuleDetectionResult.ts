import type { SvgAnalysisCoreReport, SvgAnalysisLayer } from "@/lib/svgAnalyzer";
import { layerKeyFromLayer } from "@/lib/svgAnalyzer/analyzer/buildLayerRoleConfirmation";
import {
  artworkOnlyDecisionPending,
  detectArtworkOnlyRequiresDecision,
  layerHasLetterPathGeometry,
  layerIsArtworkCandidate,
  resolveArtworkOnlyFatalBlockers,
} from "./intakeV6ArtworkOnlyGuard";
import type {
  DetectedLayer,
  DetectedModule,
  DetectedModuleKind,
  MapModuleDetectionOptions,
  ModuleDetectionBlocker,
  ModuleDetectionResult,
  ModuleDetectionWarning,
  RoleCandidateEntry,
} from "./moduleDetectionResult";
import {
  MODULE_DETECTION_RESULT_SCHEMA_VERSION,
} from "./moduleDetectionResult";
import type { ConfidenceLevel, LayerAutoRole } from "@/lib/svgAnalyzer/analyzer/layerRoleTypes";

const LETTER_PRODUCTION_ROLES = new Set<LayerAutoRole>([
  "face",
  "return",
  "bevel",
  "inner_hole",
  "backing",
  "support_panel",
]);

function layerKey(layer: SvgAnalysisLayer): string {
  return layerKeyFromLayer(layer);
}

function mapLayerWarnings(layer: SvgAnalysisLayer): DetectedLayer["layer_warnings"] {
  return (layer.warnings ?? []).map((warning) => ({
    code: warning.code,
    message: warning.message,
    severity: warning.severity,
  }));
}

function mapDetectedLayer(layer: SvgAnalysisLayer): DetectedLayer {
  return {
    layer_key: layerKey(layer),
    layer_id: layer.id,
    layer_name: layer.name,
    layer_kind: layer.layerKind,
    layer_origin: layer.layerOrigin ?? null,
    auto_role: layer.autoRole,
    auto_confidence: layer.autoConfidence,
    paint_evidence: layer.paintEvidence,
    production_hint: layer.productionHint,
    role_reason: layer.roleReason ?? null,
    geometry: {
      width_mm: layer.widthMm,
      height_mm: layer.heightMm,
      bounding_area_sqm: layer.boundingAreaSqm,
      filled_area_sqm: layer.filledAreaSqm,
      perimeter_mm: layer.perimeterMm,
      path_element_count: layer.pathElementCount,
      closed_sub_path_count: layer.closedSubPathCount,
    },
    layer_warnings: mapLayerWarnings(layer),
    has_letter_path_geometry: layerHasLetterPathGeometry(layer),
    is_artwork_candidate: layerIsArtworkCandidate(layer),
  };
}

function moduleConfidence(keys: string[], layers: DetectedLayer[]): ConfidenceLevel {
  if (keys.length === 0) return "low";
  const confidences = layers
    .filter((layer) => keys.includes(layer.layer_key))
    .map((layer) => layer.auto_confidence);
  if (confidences.every((value) => value === "high")) return "high";
  if (confidences.some((value) => value === "low")) return "low";
  return "medium";
}

function buildVolumetricLettersModule(layers: DetectedLayer[]): DetectedModule | null {
  const sourceLayerKeys = layers
    .filter(
      (layer) =>
        layer.has_letter_path_geometry &&
        (layer.auto_role === "face" || LETTER_PRODUCTION_ROLES.has(layer.auto_role)),
    )
    .map((layer) => layer.layer_key);

  const faceLayerKeys = layers
    .filter((layer) => layer.has_letter_path_geometry && layer.auto_role === "face")
    .map((layer) => layer.layer_key);

  const keys = faceLayerKeys.length > 0 ? faceLayerKeys : sourceLayerKeys;
  if (keys.length === 0) return null;

  return {
    module_key: "volumetric_letters",
    module_kind: "volumetric_letters",
    source_layer_keys: keys,
    confidence: moduleConfidence(keys, layers),
    detection_reason: "Layers with letter path geometry and production letter roles detected.",
  };
}

function buildPrintedArtworkModule(layers: DetectedLayer[]): DetectedModule | null {
  const sourceLayerKeys = layers
    .filter(
      (layer) =>
        layer.is_artwork_candidate ||
        layer.auto_role === "printed_artwork" ||
        layer.auto_role === "logo",
    )
    .map((layer) => layer.layer_key);

  if (sourceLayerKeys.length === 0) return null;

  const moduleKind: DetectedModuleKind = layers.some((layer) => layer.auto_role === "logo")
    ? "logo"
    : "printed_artwork";

  return {
    module_key: moduleKind === "logo" ? "logo" : "printed_artwork",
    module_kind: moduleKind,
    source_layer_keys: sourceLayerKeys,
    confidence: moduleConfidence(sourceLayerKeys, layers),
    detection_reason: "Artwork, policromie, gradient, or logo layer candidates detected.",
  };
}

function buildSupportStructureModule(layers: DetectedLayer[]): DetectedModule | null {
  const sourceLayerKeys = layers
    .filter(
      (layer) =>
        !layer.has_letter_path_geometry &&
        (layer.auto_role === "support_panel" ||
          layer.auto_role === "frame" ||
          layer.auto_role === "backing"),
    )
    .map((layer) => layer.layer_key);

  if (sourceLayerKeys.length === 0) return null;

  return {
    module_key: "support_structure",
    module_kind: "support_structure",
    source_layer_keys: sourceLayerKeys,
    confidence: moduleConfidence(sourceLayerKeys, layers),
    detection_reason: "Non-letter structural layers detected (support panel, frame, backing).",
  };
}

function buildDetectedModules(layers: DetectedLayer[], artworkOnly: boolean): DetectedModule[] {
  const modules: DetectedModule[] = [];

  const artworkModule = buildPrintedArtworkModule(layers);
  if (artworkModule) modules.push(artworkModule);

  if (!artworkOnly) {
    const lettersModule = buildVolumetricLettersModule(layers);
    if (lettersModule) modules.push(lettersModule);
  }

  const supportModule = buildSupportStructureModule(layers);
  if (supportModule) modules.push(supportModule);

  return modules;
}

function mapReportWarnings(report: SvgAnalysisCoreReport): ModuleDetectionWarning[] {
  return (report.warnings ?? []).map((warning) => ({
    code: warning.code,
    message: warning.message,
    severity: warning.severity,
    scope: warning.scope,
    target_id: warning.targetId,
  }));
}

function mapBlockers(
  report: SvgAnalysisCoreReport,
  confirmation: NonNullable<MapModuleDetectionOptions["layerRoleConfirmation"]>,
): ModuleDetectionBlocker[] {
  return resolveArtworkOnlyFatalBlockers(report, confirmation, []).map((code) => ({ code }));
}

function buildRoleCandidates(report: SvgAnalysisCoreReport): RoleCandidateEntry[] {
  return report.layers.map((layer) => ({
    layer_key: layerKey(layer),
    layer_name: layer.name,
    auto_role: layer.autoRole,
    auto_confidence: layer.autoConfidence,
    candidates: layer.autoRoleCandidates ?? [],
  }));
}

function requiresOperatorConfirmation(
  report: SvgAnalysisCoreReport,
  confirmation: NonNullable<MapModuleDetectionOptions["layerRoleConfirmation"]>,
): boolean {
  if (confirmation.confirmationStatus !== "complete") return true;
  if (detectArtworkOnlyRequiresDecision(report, confirmation)) return true;
  if (artworkOnlyDecisionPending(report, confirmation)) return true;
  return false;
}

/**
 * Pure mapper: SvgAnalysisCoreReport → ModuleDetectionResult.
 * No side effects, API calls, autosave, pricing, or ProductDefinition.
 */
export function mapAnalyzerReportToModuleDetectionResult(
  report: SvgAnalysisCoreReport,
  options: MapModuleDetectionOptions = {},
): ModuleDetectionResult {
  const confirmation = options.layerRoleConfirmation ?? report.layerRoleConfirmation;
  const detectedLayers = report.layers.map(mapDetectedLayer);
  const artworkOnly = detectArtworkOnlyRequiresDecision(report, confirmation);

  return {
    schema_version: MODULE_DETECTION_RESULT_SCHEMA_VERSION,
    source: options.source ?? "svg_analyzer",
    analysis_hash: options.analysisHash ?? undefined,
    source_file_name: report.sourceFileName,
    detected_layers: detectedLayers,
    detected_modules: buildDetectedModules(detectedLayers, artworkOnly),
    role_candidates: buildRoleCandidates(report),
    warnings: mapReportWarnings(report),
    blockers: mapBlockers(report, confirmation),
    recommended_forms: [],
    recommended_templates: [],
    requires_operator_confirmation: requiresOperatorConfirmation(report, confirmation),
    raw_analyzer_summary: {
      analyzer_schema_version: report.schemaVersion,
      engine_version: report.engineVersion,
      created_at: report.createdAt,
      layer_count: report.layers.length,
      confirmation_status: confirmation.confirmationStatus,
      artwork_only_requires_decision: artworkOnly,
      document_confidence: report.confidence.dimensions,
    },
  };
}
