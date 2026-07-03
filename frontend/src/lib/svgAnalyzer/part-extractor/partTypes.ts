import type { ConfidenceLevel } from '../analyzer/types'
import type { DerivedPartKind } from './innerHolePackageConstants'

export type SvgPartExtractionStrategy = 'layer-as-part' | 'subpath-shape-grouping'
export type SvgPartExtractionMode = 'split-preferred' | 'fallback-layer'

export interface SvgPartSource {
  layerId: string | null
  layerName: string | null
  elementIds: string[]
  pathElementCount: number
  subPathCount: number
}

export interface SvgPartBounds {
  xMm?: number | null
  yMm?: number | null
  rightMm?: number | null
  bottomMm?: number | null
  widthMm: number | null
  heightMm: number | null
  boundingAreaSqm: number | null
}

export interface SvgPartGeometry {
  outerPerimeterMm: number | null
  outerPerimeterMl: number | null
  innerPerimeterMm: number | null
  innerPerimeterMl: number | null
  fragmentPerimeterMm: number | null
  fragmentPerimeterMl: number | null
  totalContourPerimeterMm: number | null
  totalContourPerimeterMl: number | null
  perimeterMm: number | null
  perimeterMl: number | null
  filledAreaSqm: number | null
  closedSubPathCount: number
  openSubPathCount: number
}

export interface SvgPartColor {
  values: string[]
}

export interface SvgPartConfidence {
  bounds: ConfidenceLevel
  perimeter: ConfidenceLevel
  area: ConfidenceLevel
  source: ConfidenceLevel
}

export interface SvgPartWarning {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  scope: 'part' | 'parts'
  targetId?: string
  details?: Record<string, string | number | boolean | null>
}

export interface SvgExtractedPart {
  id: string
  name: string
  partExtractionMethod: SvgPartExtractionStrategy
  shapeKind: 'compound-shape' | 'single-contour' | 'unknown'
  sourceSubPathIndexes: number[]
  contourCount: number
  outerContourCount: number
  innerContourCount: number
  splitConfidence: ConfidenceLevel
  groupingReason:
    | 'bbox-containment'
    | 'single-subpath'
    | 'fallback-layer'
    | 'print-zone'
    | 'inner-hole-package'
    | 'unknown'
  derivedPartKind?: DerivedPartKind | null
  preferredSheetConfigId?: string | null
  materialLabel?: string | null
  source: SvgPartSource
  bounds: SvgPartBounds
  geometry: SvgPartGeometry
  colors: string[]
  quantity: number
  canNest: boolean
  nestingMethod: 'bounding-box' | 'print-area-bbox' | 'none'
  confidence: SvgPartConfidence
  warnings: SvgPartWarning[]
}

export interface SvgPartSplitDiagnostics {
  enabled: boolean
  pathElementCount: number
  subPathCount: number
  groupsCreated: number
  fallbackUsed: boolean
  confidence: ConfidenceLevel
  notes: string[]
  subPathDiagnostics?: Array<{
    subPathIndex: number
    layerName: string | null
    closed: boolean
    bboxMm: { x: number; y: number; width: number; height: number } | null
    assignedGroupId: string | null
    classification: 'outer' | 'inner' | 'fragment' | 'ambiguous'
    reason: string
  }>
  layerChildSummary?: Array<{
    layerName: string
    childPartsCount: number
    childPartIds: string[]
  }>
}

export interface SvgPartExtractionReport {
  strategy: SvgPartExtractionStrategy
  fallbackStrategy: 'layer-as-part'
  extractionMode: SvgPartExtractionMode
  count: number
  nestableCount: number
  totalBoundingAreaSqm: number
  totalPerimeterMm: number
  totalPerimeterMl: number
  items: SvgExtractedPart[]
  warnings: SvgPartWarning[]
  splitDiagnostics: SvgPartSplitDiagnostics
}
