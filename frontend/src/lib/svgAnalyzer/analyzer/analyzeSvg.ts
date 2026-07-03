import { analyzeColors } from './analyzeColors'
import { buildArtworkComplexityReport } from './artworkComplexityAssessment'
import { getBenchmarkOptionsForFile } from './benchmarkConfig'
import { analyzeGeometry } from './analyzeGeometry'
import { analyzeLayers } from './analyzeLayers'
import { buildAnalysisReport } from './buildAnalysisReport'
import { buildOfficialAnalysisJson } from './buildOfficialAnalysisJson'
import { detectWarnings } from './detectWarnings'
import { parseSvg } from './parseSvg'
import { expandSemanticAndPseudoLayers } from './semanticAndPseudoLayerExpansion'
import { extractParts } from '../part-extractor'
import { buildNestingReport } from '../nesting'
import type { ParsedSvgDocument, SvgAnalysisReport } from './types'

export interface AnalyzeOptions {
  referencePerimeterMm?: number
  referenceSource?: string
  passThresholdPercent?: number
}

export interface AnalyzeSvgEngineResult {
  parsed: ParsedSvgDocument
  report: SvgAnalysisReport
}

export function analyzeSvgString(source: string, fileName: string, fileSizeBytes: number, options?: AnalyzeOptions): AnalyzeSvgEngineResult {
  const mergedOptions = options ?? getBenchmarkOptionsForFile(fileName)
  const parsed = parseSvg(source, fileName, fileSizeBytes)
  const geometry = analyzeGeometry(parsed)
  const { doc: layerExpandedDoc, layerMeta } = expandSemanticAndPseudoLayers(parsed, geometry)
  const colors = analyzeColors(layerExpandedDoc)
  const layers = analyzeLayers(layerExpandedDoc, geometry, colors, layerMeta)
  const warnings = detectWarnings(layerExpandedDoc, geometry, layers, colors)
  const coreReport = buildAnalysisReport(layerExpandedDoc, geometry, layers, colors, warnings, mergedOptions)

  if (coreReport.confidence.perimeter === 'medium' && coreReport.benchmark.status !== 'PASS') {
    coreReport.warnings.push({
      code: 'PERIMETER_CONFIDENCE_MEDIUM',
      severity: 'warning',
      message: 'Perimeter should be validated against CAD reference for high confidence.',
      scope: 'benchmark',
    })
  }

  if (coreReport.benchmark.referencePerimeterMm != null && coreReport.benchmark.status === 'FAIL') {
    coreReport.warnings.push({
      code: 'PERIMETER_DIFFERS_FROM_REFERENCE',
      severity: 'warning',
      message: `deltaPercent=${coreReport.benchmark.deltaPercent?.toFixed(3)}% exceeds threshold ${coreReport.benchmark.passThresholdPercent}%.`,
      scope: 'benchmark',
    })
  }

  const partsReport = extractParts(coreReport, layerExpandedDoc)
  const nestingReport = buildNestingReport(partsReport)
  const artworkComplexity = buildArtworkComplexityReport(layerExpandedDoc, geometry, layers)

  const report = buildOfficialAnalysisJson(coreReport, partsReport, nestingReport, artworkComplexity)

  return {
    parsed: layerExpandedDoc,
    report,
  }
}
