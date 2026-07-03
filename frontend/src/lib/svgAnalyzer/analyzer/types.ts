import type { ArtworkComplexityReport } from './artworkComplexityAssessment'
import type { SvgPartExtractionReport } from '../part-extractor/partTypes'
import type { NestingReport } from '../nesting/nestingTypes'
import type {
  LayerAutoRole,
  LayerPaintEvidence,
  LayerProductionHint,
  LayerRoleCandidate,
  LayerRoleConfirmation,
} from './layerRoleTypes'
import type { ElementPaintKind } from './classifyPaint'

export type ConfidenceLevel = 'high' | 'medium' | 'low'

export interface ParsedLength {
  value: number
  unit: string | null
  raw: string | null
}

export interface SvgViewBox {
  minX: number
  minY: number
  width: number
  height: number
  raw: string
}

export interface ParsedSvgElement {
  id: string | null
  elementId: string
  type: 'path' | 'rect' | 'circle' | 'ellipse' | 'line' | 'polyline' | 'polygon' | 'text' | 'image' | 'group' | 'unknown'
  tagName: string
  layerId: string | null
  layerName: string | null
  className: string | null
  fill: string | null
  stroke: string | null
  fillSolid: string | null
  strokeSolid: string | null
  fillPaint: ElementPaintKind
  strokePaint: ElementPaintKind
  fillRef: string | null
  strokeRef: string | null
  strokeWidth: number | null
  transform: string | null
  d: string | null
  points: string | null
  textContent: string | null
  attributes: Record<string, string>
  index: number
  /** Paths inside defs/clipPath/mask are geometry references, not production nest parts. */
  excludeFromPartExtraction?: boolean
}

export interface ParsedSvgDocument {
  fileName: string
  fileSizeBytes: number
  source: string
  width: ParsedLength | null
  height: ParsedLength | null
  viewBox: SvgViewBox | null
  conversionToMm: {
    factor: number | null
    confidence: ConfidenceLevel
    detectedUnits: string | null
    reason: string
  }
  groups: Array<{
    id: string
    name: string | null
    elementIds: string[]
  }>
  elements: ParsedSvgElement[]
  layerNameDuplicates: string[]
  parseErrors: string[]
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface ElementGeometry {
  elementId: string
  bbox: BoundingBox | null
  areaMm2: number | null
  perimeterMm: number | null
  isClosed: boolean | null
  estimated: boolean
  confidence: ConfidenceLevel
  warnings: string[]
  subPathCount: number
  closedSubPathCount: number
  openSubPathCount: number
}

export interface GeometrySummary {
  totalBbox: BoundingBox | null
  totalAreaMm2: number | null
  totalPerimeterMm: number | null
  elementGeometries: ElementGeometry[]
  openPathCount: number
  closedPathCount: number
  transformedElementCount: number
  tinyElementCount: number
  outsideViewBoxCount: number
  pathElementCount: number
  subPathCount: number
  closedSubPathCount: number
  openSubPathCount: number
  mmPerVbu: number
  scaleX: number | null
  scaleY: number | null
  uniformScale: boolean | null
}

export type LayerKind = 'real' | 'pseudo' | 'raster_artwork'

export interface LayerAnalysis {
  id: string
  name: string
  layerKind?: LayerKind
  layerOrigin?: string | null
  roleReason?: string | null
  autoRole: LayerAutoRole
  autoConfidence: ConfidenceLevel
  autoRoleCandidates: LayerRoleCandidate[]
  paintEvidence: LayerPaintEvidence
  productionHint: LayerProductionHint
  /** @deprecated Use autoRole — kept for one release for backward-compatible readers. */
  roleGuess: LayerAutoRole
  elementCount: number
  pathElementCount: number
  subPathCount: number
  closedSubPathCount: number
  openSubPathCount: number
  widthMm: number | null
  heightMm: number | null
  boundingAreaSqm: number | null
  filledAreaSqm: number | null
  areaConfidence: ConfidenceLevel
  perimeterMm: number | null
  perimeterMl: number | null
  colors: string[]
  warnings: string[]
}

export interface ColorAnalysis {
  unique: string[]
  dominant: string[]
  fills: string[]
  strokes: string[]
  byLayer: Record<string, string[]>
}

export interface SvgAnalysisFile {
  name: string
  sizeBytes: number
  detectedUnits: string | null
  conversionConfidence: ConfidenceLevel
  physicalSizeSource: 'svg width/height' | 'viewBox only' | 'unknown'
}

export interface SvgAnalysisDocument {
  widthMm: number | null
  heightMm: number | null
  viewBox: string | null
  viewBoxWidth: number | null
  viewBoxHeight: number | null
  scaleX: number | null
  scaleY: number | null
  mmPerViewBoxUnit: number | null
  boundingAreaSqm: number | null
  filledAreaSqm: number | null
  areaConfidence: ConfidenceLevel
  areaEstimated: boolean
}

export interface SvgAnalysisGeometry {
  perimeterMm: number | null
  perimeterMl: number | null
  perimeterConfidence: ConfidenceLevel
  pathElementCount: number
  subPathCount: number
  closedSubPathCount: number
  openSubPathCount: number
  shapeCount: number
  transformCount: number
}

export interface SvgAnalysisLayer {
  id: string
  name: string
  layerKind?: LayerKind
  layerOrigin?: string | null
  roleReason?: string | null
  autoRole: LayerAutoRole
  autoConfidence: ConfidenceLevel
  autoRoleCandidates: LayerRoleCandidate[]
  paintEvidence: LayerPaintEvidence
  productionHint: LayerProductionHint
  /** @deprecated Use autoRole */
  roleGuess: LayerAutoRole
  elementCount: number
  pathElementCount: number
  subPathCount: number
  closedSubPathCount: number
  openSubPathCount: number
  widthMm: number | null
  heightMm: number | null
  boundingAreaSqm: number | null
  filledAreaSqm: number | null
  areaConfidence: ConfidenceLevel
  perimeterMm: number | null
  perimeterMl: number | null
  colors: string[]
  warnings: SvgAnalysisWarning[]
}

export interface SvgAnalysisColorReport {
  unique: string[]
  dominant: string[]
  fills: string[]
  strokes: string[]
  byLayer: Record<string, string[]>
}

export interface SvgAnalysisWarning {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  scope: 'document' | 'layer' | 'element' | 'benchmark'
  targetId?: string
  details?: Record<string, string | number | boolean | null>
}

export interface SvgAnalysisBenchmark {
  status: 'PASS' | 'FAIL' | 'NO_REFERENCE'
  referenceSource: string | null
  referencePerimeterMm: number | null
  analyzerPerimeterMm: number | null
  deltaMm: number | null
  deltaPercent: number | null
  passThresholdPercent: number | null
}

export interface SvgAnalysisConfidence {
  dimensions: ConfidenceLevel
  perimeter: ConfidenceLevel
  area: ConfidenceLevel
  layers: ConfidenceLevel
  colors: ConfidenceLevel
}

export interface SvgAnalysisExportMeta {
  exportedAt: string
  exportedBy: string
  appName: string
  schemaVersion: string
  notes: string[]
}

export interface SvgAnalysisJson {
  schemaName: 'svg-analyzer-analysis'
  schemaVersion: '1.11.0'
  engineVersion: string
  createdAt: string
  sourceFileName: string
  sourceFileSize: number
  artworkComplexity?: ArtworkComplexityReport
  file: SvgAnalysisFile
  document: SvgAnalysisDocument
  geometry: SvgAnalysisGeometry
  layers: SvgAnalysisLayer[]
  layerRoleConfirmation: LayerRoleConfirmation
  colors: SvgAnalysisColorReport
  warnings: SvgAnalysisWarning[]
  errors: string[]
  confidence: SvgAnalysisConfidence
  benchmark: SvgAnalysisBenchmark
  exportMeta: SvgAnalysisExportMeta
  parts: SvgPartExtractionReport
  nesting: NestingReport
  debug: {
    groups: number
    elements: number
    transformedElementCount: number
    outsideViewBoxCount: number
    tinyElementCount: number
  }
}

export type SvgAnalysisCoreReport = Omit<SvgAnalysisJson, 'parts' | 'nesting'>

export type SvgAnalysisReport = SvgAnalysisJson
