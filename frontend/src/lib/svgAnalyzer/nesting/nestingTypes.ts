import type { SvgPartExtractionReport, SvgPartWarning } from '../part-extractor/partTypes'

export type NestingMaterialType = 'roll' | 'sheet'
export type NestingStrategy = 'bounding-box-shelf'
export type NestingRotation = 0 | 90
export type NestingGranularity = 'child-parts'
export type NestingItemType = 'child-part'
export type NestingAssignmentSource = 'auto-from-layer-color' | 'manual-future' | 'default-preview'
export type NestingSeparationReason = 'source-layer-color-preview' | 'sheet-global-preview' | 'sheet-config-routing'

export interface NestingWarning {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  scope: 'nesting' | 'part'
  targetId?: string
  details?: Record<string, string | number | boolean | null>
}

export interface NestingConfig {
  configId: string
  materialType: NestingMaterialType
  allowRotation: boolean
}

export interface RollNestingConfig extends NestingConfig {
  materialType: 'roll'
  rollWidthMm: number
  leftMarginMm: number
  rightMarginMm: number
  usableWidthMm: number
  partSpacingMm: number
}

export interface SheetNestingConfig extends NestingConfig {
  materialType: 'sheet'
  sheetWidthMm: number
  sheetLengthMm: number
  edgeMarginMm: number
  usableWidthMm: number
  usableLengthMm: number
  partSpacingMm: number
}

export interface RollMaterialFrame {
  materialType: 'roll'
  rollWidthMm: number
  usableWidthMm: number
  feedAxis: 'length'
  crossAxis: 'width'
  packingDirection: 'width-first'
  optimizeFor: 'minimize-consumed-length'
}

export interface SheetMaterialFrame {
  materialType: 'sheet'
  sheetLengthMm: number
  sheetWidthMm: number
  usableLengthMm: number
  usableWidthMm: number
  feedAxis: 'length'
  crossAxis: 'width'
  packingDirection: 'width-first'
  optimizeFor: 'preserve-continuous-length'
}

export type MaterialFrame = RollMaterialFrame | SheetMaterialFrame

export interface NestingInputItem {
  itemId: string
  itemName: string
  sourceLayerName: string | null
  colorKey: string | null
  widthMm: number
  heightMm: number
  bounds: {
    widthMm: number
    heightMm: number
    boundingAreaSqm: number
  }
  sourceType: 'layer' | 'part'
  roleAssignment: null
  canNest: boolean
  preferredSheetConfigId?: string | null
  materialLabel?: string | null
  sourceWarnings: SvgPartWarning[]
}

export interface NestingJobInput {
  jobId: string
  jobKind: NestingMaterialType
  materialKey: string | null
  materialLabel: string | null
  sourceLayerName: string | null
  colorKey: string | null
  granularity: NestingGranularity
  itemType: NestingItemType
  separationKey: string
  items: NestingInputItem[]
  materialFrame: MaterialFrame
  assignmentSource: NestingAssignmentSource
  separationReason: NestingSeparationReason
}

export interface NestingPlacement {
  partId: string
  partName: string
  sourceLayerName: string | null
  materialType: NestingMaterialType
  containerId: string
  xMm: number
  yMm: number
  placedWidthMm: number
  placedHeightMm: number
  rotationDeg: NestingRotation
  spacingMm: number
}

export interface NestingUnplacedPart {
  partId: string
  partName: string
  reason: 'DOES_NOT_FIT_USABLE_WIDTH' | 'DOES_NOT_FIT_SHEET' | 'MISSING_BOUNDS' | 'NOT_NESTABLE'
}

export interface NestingRollLayout {
  configId: string
  materialType: 'roll'
  granularity: NestingGranularity
  assignmentSource: NestingAssignmentSource
  materialFrame: RollMaterialFrame
  rollWidthMm: number
  usableWidthMm: number
  leftMarginMm: number
  rightMarginMm: number
  partSpacingMm: number
  allowRotation: boolean
  jobs: NestingRollJobLayout[]
  aggregate: {
    jobsCount: number
    totalSourceItemsCount: number
    totalPlacedItemsCount: number
    totalUnplacedItemsCount: number
    totalUsedLengthMm: number
  }
}

export interface NestingRollJobLayout {
  jobKey: string
  jobId: string
  assignmentSource: NestingAssignmentSource
  sourceLayerName: string | null
  colorKey: string | null
  separationReason: NestingSeparationReason
  itemType: NestingItemType
  sourceItemsCount: number
  placedItemsCount: number
  unplacedItemsCount: number
  consumedLengthMm: number
  usedWidthMm: number
  usedLengthMm: number
  usedRollAreaSqm: number
  partsBoundingAreaSqm: number
  wasteAreaSqm: number
  efficiencyPercent: number
  placements: NestingPlacement[]
  unplaced: NestingUnplacedPart[]
  warnings: NestingWarning[]
}

export interface NestingSheetLayout {
  configId: string
  materialType: 'sheet'
  granularity: NestingGranularity
  assignmentSource: NestingAssignmentSource
  materialFrame: SheetMaterialFrame
  itemType: NestingItemType
  sourceItemsCount: number
  placedItemsCount: number
  unplacedItemsCount: number
  sheetWidthMm: number
  sheetLengthMm: number
  usableWidthMm: number
  usableLengthMm: number
  edgeMarginMm: number
  partSpacingMm: number
  allowRotation: boolean
  sheetsUsed: number
  consumedLengthMm: number
  usedWidthMm: number
  preservedLengthMm: number
  usedSheetAreaSqm: number
  partsBoundingAreaSqm: number
  wasteAreaSqm: number
  efficiencyPercent: number
  placements: NestingPlacement[]
  unplaced: NestingUnplacedPart[]
  warnings: NestingWarning[]
}

export interface NestingInputs {
  partsCount: number
  nestablePartsCount: number
}

export interface NestingResult {
  strategy: NestingStrategy
  generatedAt: string
  inputs: NestingInputs
  jobInputs: NestingJobInput[]
  rolls: NestingRollLayout[]
  sheets: NestingSheetLayout[]
  warnings: NestingWarning[]
}

export interface NestingReport extends NestingResult {}

export interface NestingBuildContext {
  partsReport: SvgPartExtractionReport
}

export interface NestingPreparedPart {
  partId: string
  partName: string
  itemType: NestingItemType
  sourceLayerId: string | null
  sourceLayerName: string | null
  colorKey: string | null
  widthMm: number
  heightMm: number
  boundingAreaSqm: number
  canNest: boolean
  preferredSheetConfigId: string | null
  materialLabel: string | null
  sourceWarnings: SvgPartWarning[]
}
