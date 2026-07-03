import type { ArtworkComplexityReport } from './artworkComplexityAssessment'
import type { AnalyzeOptions } from './analyzeSvg'
import { buildLayerRoleConfirmationDraft } from './buildLayerRoleConfirmation'
import type {
  ColorAnalysis,
  ConfidenceLevel,
  GeometrySummary,
  LayerAnalysis,
  ParsedSvgDocument,
  SvgAnalysisCoreReport,
  SvgAnalysisWarning,
} from './types'

export const ANALYSIS_SCHEMA_NAME = 'svg-analyzer-analysis'
export const ANALYSIS_SCHEMA_VERSION = '1.11.0'
export const ANALYZER_ENGINE_VERSION = '1.11.0'

function toDimensionConfidence(doc: ParsedSvgDocument): ConfidenceLevel {
  if (doc.width && doc.height && doc.conversionToMm.confidence === 'high') {
    return 'high'
  }

  if (doc.width && doc.height && doc.conversionToMm.confidence === 'medium') {
    return 'medium'
  }

  return 'low'
}

function toLayerConfidence(layers: LayerAnalysis[]): ConfidenceLevel {
  if (layers.length === 0) {
    return 'low'
  }

  if (layers.some((layer) => layer.name === 'unassigned')) {
    return 'medium'
  }

  return 'high'
}

function toColorConfidence(colors: ColorAnalysis): ConfidenceLevel {
  if (colors.unique.length === 0) {
    return 'low'
  }

  if (colors.byLayer && Object.keys(colors.byLayer).length > 0) {
    return 'high'
  }

  return 'medium'
}

function toAreaConfidence(geometry: GeometrySummary, filledAreaSqm: number | null): ConfidenceLevel {
  if (filledAreaSqm == null) {
    return 'low'
  }

  if (geometry.elementGeometries.every((e) => !e.estimated)) {
    return 'high'
  }

  return 'medium'
}

function toPerimeterConfidence(analyzerPerimeterMm: number | null, benchmarkStatus: SvgAnalysisCoreReport['benchmark']['status']): ConfidenceLevel {
  if (analyzerPerimeterMm == null) {
    return 'low'
  }

  if (benchmarkStatus === 'PASS') {
    return 'high'
  }

  return 'medium'
}

function splitWarning(raw: string): { code: string; message: string } {
  const match = raw.match(/^([A-Z0-9_]+):\s*(.*)$/)
  if (match) {
    return {
      code: match[1],
      message: match[2] || match[1],
    }
  }

  return {
    code: 'GENERAL_WARNING',
    message: raw,
  }
}

function warningScope(code: string): SvgAnalysisWarning['scope'] {
  if (code.includes('BENCHMARK') || code.includes('REFERENCE') || code.includes('PERIMETER')) {
    return 'benchmark'
  }

  return 'document'
}

function warningSeverity(code: string): SvgAnalysisWarning['severity'] {
  if (code.includes('ERROR')) {
    return 'error'
  }

  if (code.includes('INFO')) {
    return 'info'
  }

  return 'warning'
}

export function buildAnalysisReport(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
  layers: LayerAnalysis[],
  colors: ColorAnalysis,
  warnings: string[],
  options?: AnalyzeOptions,
): SvgAnalysisCoreReport {
  const factor = doc.conversionToMm.factor
  const widthMm = doc.width && factor != null ? doc.width.value * factor : null
  const heightMm = doc.height && factor != null ? doc.height.value * factor : null
  const physicalSizeSource: SvgAnalysisCoreReport['file']['physicalSizeSource'] =
    widthMm && heightMm ? 'svg width/height' : doc.viewBox ? 'viewBox only' : 'unknown'

  const boundingAreaSqm = widthMm != null && heightMm != null ? (widthMm * heightMm) / 1_000_000 : null
  const filledAreaSqm = geometry.totalAreaMm2 == null ? null : geometry.totalAreaMm2 / 1_000_000

  const refMm = options?.referencePerimeterMm ?? null
  const analyzerMm = geometry.totalPerimeterMm
  const threshold = options?.passThresholdPercent ?? null

  let deltaMm: number | null = null
  let deltaPercent: number | null = null
  let benchmarkStatus: SvgAnalysisCoreReport['benchmark']['status'] = 'NO_REFERENCE'
  if (refMm != null && analyzerMm != null && threshold != null) {
    deltaMm = analyzerMm - refMm
    deltaPercent = (Math.abs(deltaMm) / refMm) * 100
    benchmarkStatus = deltaPercent <= threshold ? 'PASS' : 'FAIL'
  }

  const areaConfidence = toAreaConfidence(geometry, filledAreaSqm)
  const perimeterConfidence = toPerimeterConfidence(analyzerMm, benchmarkStatus)

  const structuredWarnings: SvgAnalysisWarning[] = warnings.map((raw) => {
    const normalized = splitWarning(raw)
    return {
      code: normalized.code,
      severity: warningSeverity(normalized.code),
      message: normalized.message,
      scope: warningScope(normalized.code),
    }
  })

  const layerWarnings = (items: string[]): SvgAnalysisWarning[] =>
    items.map((raw) => {
      const normalized = splitWarning(raw)
      return {
        code: normalized.code,
        severity: warningSeverity(normalized.code),
        message: normalized.message,
        scope: 'layer',
      }
    })

  return {
    schemaName: ANALYSIS_SCHEMA_NAME,
    schemaVersion: ANALYSIS_SCHEMA_VERSION,
    engineVersion: ANALYZER_ENGINE_VERSION,
    createdAt: new Date().toISOString(),
    sourceFileName: doc.fileName,
    sourceFileSize: doc.fileSizeBytes,
    file: {
      name: doc.fileName,
      sizeBytes: doc.fileSizeBytes,
      detectedUnits: doc.conversionToMm.detectedUnits,
      conversionConfidence: doc.conversionToMm.confidence,
      physicalSizeSource,
    },
    document: {
      widthMm,
      heightMm,
      viewBox: doc.viewBox?.raw ?? null,
      viewBoxWidth: doc.viewBox?.width ?? null,
      viewBoxHeight: doc.viewBox?.height ?? null,
      scaleX: geometry.scaleX,
      scaleY: geometry.scaleY,
      mmPerViewBoxUnit: geometry.mmPerVbu ?? null,
      boundingAreaSqm,
      filledAreaSqm,
      areaConfidence,
      areaEstimated: filledAreaSqm == null || geometry.elementGeometries.some((e) => e.estimated),
    },
    geometry: {
      perimeterMm: analyzerMm,
      perimeterMl: analyzerMm == null ? null : analyzerMm / 1000,
      perimeterConfidence,
      pathElementCount: geometry.pathElementCount,
      subPathCount: geometry.subPathCount,
      closedSubPathCount: geometry.closedSubPathCount,
      openSubPathCount: geometry.openSubPathCount,
      shapeCount: geometry.elementGeometries.length,
      transformCount: geometry.transformedElementCount,
    },
    layers: layers.map((layer) => ({
      id: layer.id,
      name: layer.name,
      layerKind: layer.layerKind,
      layerOrigin: layer.layerOrigin,
      roleReason: layer.roleReason,
      autoRole: layer.autoRole,
      autoConfidence: layer.autoConfidence,
      autoRoleCandidates: layer.autoRoleCandidates,
      paintEvidence: layer.paintEvidence,
      productionHint: layer.productionHint,
      roleGuess: layer.roleGuess,
      elementCount: layer.elementCount,
      pathElementCount: layer.pathElementCount,
      subPathCount: layer.subPathCount,
      closedSubPathCount: layer.closedSubPathCount,
      openSubPathCount: layer.openSubPathCount,
      widthMm: layer.widthMm,
      heightMm: layer.heightMm,
      boundingAreaSqm: layer.boundingAreaSqm,
      filledAreaSqm: layer.filledAreaSqm,
      areaConfidence: layer.areaConfidence,
      perimeterMm: layer.perimeterMm,
      perimeterMl: layer.perimeterMl,
      colors: layer.colors,
      warnings: layerWarnings(layer.warnings),
    })),
    layerRoleConfirmation: buildLayerRoleConfirmationDraft(layers),
    colors: {
      unique: colors.unique,
      dominant: colors.dominant,
      fills: colors.fills,
      strokes: colors.strokes,
      byLayer: colors.byLayer,
    },
    warnings: structuredWarnings,
    errors: doc.parseErrors,
    confidence: {
      dimensions: toDimensionConfidence(doc),
      perimeter: perimeterConfidence,
      area: areaConfidence,
      layers: toLayerConfidence(layers),
      colors: toColorConfidence(colors),
    },
    benchmark: {
      status: benchmarkStatus,
      referenceSource: options?.referenceSource ?? null,
      referencePerimeterMm: refMm,
      analyzerPerimeterMm: analyzerMm,
      deltaMm,
      deltaPercent,
      passThresholdPercent: threshold,
    },
    exportMeta: {
      exportedAt: new Date().toISOString(),
      exportedBy: 'local-user',
      appName: 'SVG Analyzer Engine',
      schemaVersion: ANALYSIS_SCHEMA_VERSION,
      notes: [],
    },
    debug: {
      groups: doc.groups.length,
      elements: doc.elements.length,
      transformedElementCount: geometry.transformedElementCount,
      outsideViewBoxCount: geometry.outsideViewBoxCount,
      tinyElementCount: geometry.tinyElementCount,
    },
  }
}
