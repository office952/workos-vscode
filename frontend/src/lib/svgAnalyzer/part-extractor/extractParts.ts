import type { ParsedSvgDocument, SvgAnalysisCoreReport, SvgAnalysisLayer } from '../analyzer/types'
import type { LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import {
  effectiveLayerRole,
  isEffectiveInnerHoleLayer,
  plexiInsertsEnabledForLayer,
} from '../lib/effectiveLayerRole'
import { applyBondProductionPlates } from './applyBondProductionPlates'
import { findBondProductionLayer, returnDepthsForLayer } from './productionPlateBounds'
import { buildPartsReport } from './buildPartsReport'
import { deriveInnerHolePackageParts } from './deriveInnerHolePackage'
import { createPartWarning } from './partWarnings'
import { groupSubPathsByShape } from './shapeGrouping'
import { isDegenerateBbox } from './shapeBounds'
import { extractSubPaths } from './subPathExtractor'
import { partSplitWarning } from './partSplittingWarnings'
import type { SvgExtractedPart, SvgPartExtractionReport } from './partTypes'

function uniquePartId(name: string, index: number): string {
  const safe = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_')
  return `part_${safe || 'layer'}_${String(index + 1).padStart(3, '0')}`
}

function layerSourceConfidence(layer: SvgAnalysisLayer): SvgExtractedPart['confidence']['source'] {
  if (layer.id && layer.name) return 'high'
  if (layer.name) return 'medium'
  return 'low'
}

function layerBoundsConfidence(layer: SvgAnalysisLayer): SvgExtractedPart['confidence']['bounds'] {
  if ((layer.widthMm ?? 0) > 0 && (layer.heightMm ?? 0) > 0) return 'high'
  return 'low'
}

function layerPerimeterConfidence(report: SvgAnalysisCoreReport, perimeterMm: number | null): SvgExtractedPart['confidence']['perimeter'] {
  if (perimeterMm == null) return 'low'
  if (report.benchmark.status === 'PASS') return 'high'
  return 'medium'
}

function sortLayerChildPartsLeftToRight(items: SvgExtractedPart[]): SvgExtractedPart[] {
  const byLayer = new Map<string, SvgExtractedPart[]>()
  for (const item of items) {
    const key = item.source.layerName ?? item.source.layerId ?? 'unassigned'
    const current = byLayer.get(key) ?? []
    current.push(item)
    byLayer.set(key, current)
  }

  const output: SvgExtractedPart[] = []
  for (const layerItems of byLayer.values()) {
    const sorted = [...layerItems].sort((a, b) => {
      const ax = a.bounds.xMm
      const bx = b.bounds.xMm
      if (ax != null && bx != null && ax !== bx) return ax - bx
      if (ax != null && bx == null) return -1
      if (ax == null && bx != null) return 1
      const aw = a.bounds.widthMm ?? 0
      const bw = b.bounds.widthMm ?? 0
      return bw - aw
    })
    output.push(...sorted)
  }

  return output
}

function isNonProductionLayer(layer: SvgAnalysisLayer, confirmation: LayerRoleConfirmation | null | undefined): boolean {
  const role = effectiveLayerRole(layer, confirmation)
  return role === 'ignore' || role === 'reference'
}

/** Openings / slogan cuts in Bond — geometry for CNC on backing, not separate nest pieces. */
function isInnerHoleLayer(layer: SvgAnalysisLayer, confirmation: LayerRoleConfirmation | null | undefined): boolean {
  return isEffectiveInnerHoleLayer(layer, confirmation)
}

function isPrintLayer(layer: SvgAnalysisLayer, confirmation: LayerRoleConfirmation | null | undefined): boolean {
  return effectiveLayerRole(layer, confirmation) === 'printed_artwork'
}
function layerNameSet(layers: SvgAnalysisLayer[]): Set<string> {
  return new Set(layers.map((layer) => layer.name))
}

function rebuildLayerChildSummary(items: SvgExtractedPart[], report: SvgAnalysisCoreReport) {
  return report.layers.map((layer) => ({
    layerName: layer.name,
    childPartsCount: items.filter((item) => item.source.layerName === layer.name).length,
    childPartIds: items.filter((item) => item.source.layerName === layer.name).map((item) => item.id),
  }))
}

function applyLayerRolePartExtraction(
  report: SvgAnalysisCoreReport,
  built: SvgPartExtractionReport,
  confirmation: LayerRoleConfirmation | null | undefined,
): SvgPartExtractionReport {
  const skipNames = layerNameSet(
    report.layers.filter((layer) => isNonProductionLayer(layer, confirmation) || isInnerHoleLayer(layer, confirmation)),
  )
  const printNames = layerNameSet(report.layers.filter((layer) => isPrintLayer(layer, confirmation)))

  const cutItems = built.items.filter((item) => {
    const layerName = item.source.layerName ?? ''
    return !skipNames.has(layerName) && !printNames.has(layerName)
  })

  const printItems = report.layers
    .filter((layer) => isPrintLayer(layer, confirmation))
    .map((layer, index) => toPrintLayerPart(layer, report, index))
  const items = sortLayerChildPartsLeftToRight([...cutItems, ...printItems])

  return {
    ...built,
    items,
    count: items.length,
    nestableCount: items.filter((item) => item.canNest).length,
    splitDiagnostics: {
      ...built.splitDiagnostics,
      layerChildSummary: rebuildLayerChildSummary(items, report),
    },
  }
}

function toPrintLayerPart(layer: SvgAnalysisLayer, report: SvgAnalysisCoreReport, index: number): SvgExtractedPart {
  const part = toLayerPart(layer, report, index)
  return {
    ...part,
    name: layer.name,
    partExtractionMethod: 'layer-as-part',
    shapeKind: 'unknown',
    groupingReason: 'print-zone',
    nestingMethod: part.canNest ? 'print-area-bbox' : 'none',
    warnings: [
      ...part.warnings,
      createPartWarning(
        'PART_PRINT_ZONE_WHOLE_VINYL',
        'info',
        'Print zone — entire layer nests as one piece on vinyl.',
        part.id,
      ),
    ],
  }
}

function toLayerPart(layer: SvgAnalysisLayer, report: SvgAnalysisCoreReport, index: number): SvgExtractedPart {
  const id = uniquePartId(layer.name, index)
  const canNest = (layer.widthMm ?? 0) > 0 && (layer.heightMm ?? 0) > 0

  const warnings = [] as SvgExtractedPart['warnings']

  if (!canNest) {
    warnings.push(createPartWarning('PART_MISSING_BOUNDS', 'warning', 'Part bounds are missing or invalid.', id))
    warnings.push(createPartWarning('PART_NOT_NESTABLE', 'warning', 'Part cannot be nested due to invalid dimensions.', id))
  }

  if (layer.perimeterMm == null || layer.perimeterMm <= 0) {
    warnings.push(createPartWarning('PART_MISSING_PERIMETER', 'warning', 'Part perimeter is missing or invalid.', id))
  }

  if (layer.filledAreaSqm == null) {
    warnings.push(
      createPartWarning(
        'PART_FILLED_AREA_NOT_AVAILABLE',
        'info',
        'Filled area is not calculated for this part. Bounding area is available.',
        id,
      ),
    )
  }

  if ((layer.openSubPathCount ?? 0) > 0 && (layer.pathElementCount ?? 0) > 0) {
    warnings.push(createPartWarning('PART_OPEN_SUBPATHS', 'warning', 'Part may contain open subpaths.', id))
  }

  const contourCount = Math.max(1, layer.subPathCount ?? 1)

  return {
    id,
    name: layer.name,
    partExtractionMethod: 'layer-as-part',
    shapeKind: 'unknown',
    sourceSubPathIndexes: [],
    contourCount,
    outerContourCount: contourCount,
    innerContourCount: 0,
    splitConfidence: 'low',
    groupingReason: 'fallback-layer',
    source: {
      layerId: layer.id,
      layerName: layer.name,
      elementIds: [],
      pathElementCount: layer.pathElementCount ?? 0,
      subPathCount: layer.subPathCount ?? 0,
    },
    bounds: {
      xMm: null,
      yMm: null,
      rightMm: null,
      bottomMm: null,
      widthMm: layer.widthMm,
      heightMm: layer.heightMm,
      boundingAreaSqm: layer.boundingAreaSqm,
    },
    geometry: {
      outerPerimeterMm: layer.perimeterMm,
      outerPerimeterMl: layer.perimeterMl,
      innerPerimeterMm: 0,
      innerPerimeterMl: 0,
      fragmentPerimeterMm: 0,
      fragmentPerimeterMl: 0,
      totalContourPerimeterMm: layer.perimeterMm,
      totalContourPerimeterMl: layer.perimeterMl,
      perimeterMm: layer.perimeterMm,
      perimeterMl: layer.perimeterMl,
      filledAreaSqm: layer.filledAreaSqm,
      closedSubPathCount: layer.closedSubPathCount ?? 0,
      openSubPathCount: layer.openSubPathCount ?? 0,
    },
    colors: layer.colors,
    quantity: 1,
    canNest,
    nestingMethod: canNest ? 'bounding-box' : 'none',
    confidence: {
      bounds: layerBoundsConfidence(layer),
      perimeter: layerPerimeterConfidence(report, layer.perimeterMm),
      area: layer.filledAreaSqm == null ? 'low' : layer.areaConfidence,
      source: layerSourceConfidence(layer),
    },
    warnings,
  }
}

function appendInnerHolePackageParts(
  report: SvgAnalysisCoreReport,
  built: SvgPartExtractionReport,
  parsed: ParsedSvgDocument,
  confirmation: LayerRoleConfirmation | null | undefined,
): SvgPartExtractionReport {
  const innerHoleLayers = report.layers.filter((layer) => isInnerHoleLayer(layer, confirmation))
  if (innerHoleLayers.length === 0) return built

  const extracted = extractSubPaths(parsed, report.document.mmPerViewBoxUnit)
  const bondLayer = findBondProductionLayer(report, confirmation)
  const bondReturnDepth1Mm = bondLayer ? returnDepthsForLayer(bondLayer, confirmation).returnDepthMm : null
  const packageParts: SvgExtractedPart[] = []

  for (const layer of innerHoleLayers) {
    packageParts.push(
      ...deriveInnerHolePackageParts({
        layer,
        subPaths: extracted.subPaths,
        plexiInserts10mm: plexiInsertsEnabledForLayer(layer, confirmation),
        layerRoleConfirmation: confirmation,
        bondReturnDepth1Mm,
      }),
    )
  }

  const items = sortLayerChildPartsLeftToRight([...built.items, ...packageParts])

  return {
    ...built,
    items,
    count: items.length,
    nestableCount: items.filter((item) => item.canNest).length,
    splitDiagnostics: {
      ...built.splitDiagnostics,
      layerChildSummary: rebuildLayerChildSummary(items, report),
    },
  }
}

function extractLayerAsFallback(
  report: SvgAnalysisCoreReport,
  notes: string[],
  seedWarnings: SvgPartExtractionReport['warnings'] = [],
  confirmation: LayerRoleConfirmation | null | undefined = null,
): SvgPartExtractionReport {
  const validLayers = report.layers.filter((layer) => {
    if (isNonProductionLayer(layer, confirmation) || isPrintLayer(layer, confirmation) || isInnerHoleLayer(layer, confirmation)) {
      return false
    }    const hasPerimeterOrArea = (layer.perimeterMm ?? 0) > 0 || (layer.boundingAreaSqm ?? 0) > 0
    return layer.elementCount > 0 && hasPerimeterOrArea
  })

  const items = validLayers.map((layer, index) => toLayerPart(layer, report, index))
  const warnings = [...seedWarnings] as SvgPartExtractionReport['warnings']

  if (items.length === 0) {
    warnings.push(createPartWarning('NO_EXTRACTABLE_PARTS', 'warning', 'No extractable parts were generated from current layers.'))
  }

  const reportBuilt = buildPartsReport(
    items,
    warnings,
    'layer-as-part',
    'fallback-layer',
    {
      enabled: true,
      pathElementCount: report.geometry.pathElementCount,
      subPathCount: report.geometry.subPathCount,
      groupsCreated: items.length,
      fallbackUsed: true,
      confidence: 'low',
      notes,
      subPathDiagnostics: [],
      layerChildSummary: report.layers.map((layer) => ({
        layerName: layer.name,
        childPartsCount: items.filter((item) => item.source.layerName === layer.name).length,
        childPartIds: items.filter((item) => item.source.layerName === layer.name).map((item) => item.id),
      })),
    },
  )

  if (report.geometry.perimeterMm != null) {
    const delta = Math.abs(reportBuilt.totalPerimeterMm - report.geometry.perimeterMm)
    if (delta > 0.01) {
      reportBuilt.warnings.push(
        createPartWarning('PART_TOTAL_PERIMETER_MISMATCH', 'warning', 'Parts perimeter total differs from document perimeter.', undefined, {
          documentPerimeterMm: report.geometry.perimeterMm,
          partsOuterPerimeterMm: items.reduce((acc, item) => acc + (item.geometry.outerPerimeterMm ?? 0), 0),
          partsTotalContourPerimeterMm: reportBuilt.totalPerimeterMm,
          deltaOuterVsDocumentMm: Math.abs(items.reduce((acc, item) => acc + (item.geometry.outerPerimeterMm ?? 0), 0) - report.geometry.perimeterMm),
          deltaTotalVsDocumentMm: Math.abs(reportBuilt.totalPerimeterMm - report.geometry.perimeterMm),
          explanation: 'Layer fallback has no split contour decomposition; values mirror layer perimeter totals.',
        }),
      )
    }
  }

  return applyLayerRolePartExtraction(report, reportBuilt, confirmation)
}

function toSplitPartName(layerName: string | null, perLayerCounter: number): string {  const prefix = layerName?.trim() || 'shape'
  return `${prefix}_${String(perLayerCounter).padStart(2, '0')}`
}

function extractBySubPathGrouping(
  report: SvgAnalysisCoreReport,
  parsed: ParsedSvgDocument,
  confirmation: LayerRoleConfirmation | null | undefined,
): SvgPartExtractionReport {
  const mmPerVbu = report.document.mmPerViewBoxUnit
  const splitWarnings: SvgPartExtractionReport['warnings'] = []

  const extracted = extractSubPaths(parsed, mmPerVbu)
  splitWarnings.push(...extracted.warnings)

  if (extracted.subPaths.length === 0) {
    splitWarnings.push(partSplitWarning('SUBPATH_GROUPING_FALLBACK_USED', 'warning', 'No subpaths extracted; fallback to layer-as-part.'))
    return extractLayerAsFallback(report, ['No subpaths extracted from paths.'], splitWarnings, confirmation)
  }

  if (extracted.subPaths.some((subPath) => !subPath.bboxMm || isDegenerateBbox(subPath.bboxMm))) {
    splitWarnings.push(partSplitWarning('SUBPATH_GROUPING_FALLBACK_USED', 'warning', 'Subpath bounds unavailable; fallback to layer-as-part.'))
    return extractLayerAsFallback(report, ['At least one subpath has unavailable bounds.'], splitWarnings, confirmation)
  }

  const grouped = groupSubPathsByShape(extracted.subPaths, mmPerVbu)
  splitWarnings.push(...grouped.warnings)

  if (grouped.groups.length === 0 || grouped.confidence === 'low') {
    splitWarnings.push(partSplitWarning('PART_SPLIT_LOW_CONFIDENCE', 'warning', 'Subpath grouping confidence is low; fallback to layer-as-part.'))
    splitWarnings.push(partSplitWarning('SUBPATH_GROUPING_FALLBACK_USED', 'warning', 'Fallback used due to low split confidence.'))
    return extractLayerAsFallback(report, ['Grouping produced low confidence.'], splitWarnings, confirmation)
  }

  const layerShapeCounter = new Map<string, number>()
  const items: SvgExtractedPart[] = grouped.groups.map((group) => {
    const key = group.layerName ?? group.layerId ?? 'unassigned'
    const current = (layerShapeCounter.get(key) ?? 0) + 1
    layerShapeCounter.set(key, current)

    const widthMm = group.boundsMm?.width ?? null
    const heightMm = group.boundsMm?.height ?? null
    const xMm = group.boundsMm?.x ?? null
    const yMm = group.boundsMm?.y ?? null
    const rightMm = xMm != null && widthMm != null ? xMm + widthMm : null
    const bottomMm = yMm != null && heightMm != null ? yMm + heightMm : null
    const boundingAreaSqm = widthMm != null && heightMm != null ? (widthMm * heightMm) / 1_000_000 : null
    const canNest = (widthMm ?? 0) > 0 && (heightMm ?? 0) > 0

    const outerPerimeterMm = group.outerPerimeterMm
    const innerPerimeterMm = group.innerSubPaths.reduce((acc, subPath) => acc + (subPath.perimeterMm ?? 0), 0)
    const fragmentPerimeterMm = group.fragmentSubPaths.reduce((acc, subPath) => acc + (subPath.perimeterMm ?? 0), 0)
    const totalContourPerimeterMm = group.totalContourPerimeterMm

    const warnings = [...group.subPaths.flatMap((subPath) => subPath.warnings)]

    if (!canNest) {
      warnings.push(createPartWarning('PART_MISSING_BOUNDS', 'warning', 'Part bounds are missing or invalid.', group.id))
      warnings.push(createPartWarning('PART_NOT_NESTABLE', 'warning', 'Part cannot be nested due to invalid dimensions.', group.id))
    }

    return {
      id: group.id,
      name: toSplitPartName(group.layerName, current),
      partExtractionMethod: 'subpath-shape-grouping',
      shapeKind: group.innerSubPaths.length > 0 || group.fragmentSubPaths.length > 0 ? 'compound-shape' : 'single-contour',
      sourceSubPathIndexes: group.subPaths.map((subPath) => subPath.subPathIndex),
      contourCount: group.subPaths.length,
      outerContourCount: group.outerSubPaths.length,
      innerContourCount: group.innerSubPaths.length,
      splitConfidence: group.splitConfidence,
      groupingReason: group.groupingReason,
      source: {
        layerId: group.layerId,
        layerName: group.layerName,
        elementIds: [...new Set(group.subPaths.map((subPath) => subPath.elementId))],
        pathElementCount: new Set(group.subPaths.map((subPath) => subPath.elementId)).size,
        subPathCount: group.subPaths.length,
      },
      bounds: {
        xMm,
        yMm,
        rightMm,
        bottomMm,
        widthMm,
        heightMm,
        boundingAreaSqm,
      },
      geometry: {
        outerPerimeterMm,
        outerPerimeterMl: outerPerimeterMm == null ? null : outerPerimeterMm / 1000,
        innerPerimeterMm,
        innerPerimeterMl: innerPerimeterMm / 1000,
        fragmentPerimeterMm,
        fragmentPerimeterMl: fragmentPerimeterMm / 1000,
        totalContourPerimeterMm,
        totalContourPerimeterMl: totalContourPerimeterMm == null ? null : totalContourPerimeterMm / 1000,
        perimeterMm: outerPerimeterMm,
        perimeterMl: outerPerimeterMm == null ? null : outerPerimeterMm / 1000,
        filledAreaSqm: null,
        closedSubPathCount: group.subPaths.filter((subPath) => subPath.closed).length,
        openSubPathCount: group.subPaths.filter((subPath) => !subPath.closed).length,
      },
      colors: group.colors,
      quantity: 1,
      canNest,
      nestingMethod: canNest ? 'bounding-box' : 'none',
      confidence: {
        bounds: canNest ? 'high' : 'low',
        perimeter: layerPerimeterConfidence(report, outerPerimeterMm),
        area: 'low',
        source: group.layerId || group.layerName ? 'high' : 'medium',
      },
      warnings,
    }
  })

  const sortedItems = sortLayerChildPartsLeftToRight(items)

  const reportBuilt = buildPartsReport(
    sortedItems,
    splitWarnings,
    'subpath-shape-grouping',
    'split-preferred',
    {
      enabled: true,
      pathElementCount: extracted.pathElementCount,
      subPathCount: extracted.subPaths.length,
      groupsCreated: grouped.groups.length,
      fallbackUsed: false,
      confidence: grouped.confidence,
      notes: [
        'geometry.perimeterMm stores outer perimeter for backward compatibility.',
        'geometry.totalContourPerimeterMm includes outer + inner + fragment contours.',
      ],
      subPathDiagnostics: grouped.assignments,
      layerChildSummary: [...new Set(sortedItems.map((item) => item.source.layerName ?? 'unassigned'))].map((layerName) => ({
        layerName,
        childPartsCount: sortedItems.filter((item) => (item.source.layerName ?? 'unassigned') === layerName).length,
        childPartIds: sortedItems.filter((item) => (item.source.layerName ?? 'unassigned') === layerName).map((item) => item.id),
      })),
    },
  )

  if (report.geometry.perimeterMm != null) {
    const partsOuterPerimeterMm = sortedItems.reduce((acc, item) => acc + (item.geometry.outerPerimeterMm ?? 0), 0)
    const partsTotalContourPerimeterMm = sortedItems.reduce((acc, item) => acc + (item.geometry.totalContourPerimeterMm ?? 0), 0)

    const deltaOuterVsDocumentMm = Math.abs(partsOuterPerimeterMm - report.geometry.perimeterMm)
    const deltaTotalVsDocumentMm = Math.abs(partsTotalContourPerimeterMm - report.geometry.perimeterMm)

    if (deltaTotalVsDocumentMm > 1 || deltaOuterVsDocumentMm > 1) {
      reportBuilt.warnings.push(
        partSplitWarning('PART_SPLIT_PERIMETER_MISMATCH', 'warning', 'Split perimeter audit indicates differences between outer/total contour and document perimeter.', undefined, {
          documentPerimeterMm: report.geometry.perimeterMm,
          partsOuterPerimeterMm,
          partsTotalContourPerimeterMm,
          deltaOuterVsDocumentMm,
          deltaTotalVsDocumentMm,
          explanation:
            'Document perimeter includes all contours; geometry.perimeterMm currently stores outer perimeter while totalContourPerimeterMm captures inner/fragment paths.',
        }),
      )
    }
  }

  if (reportBuilt.count <= Math.max(1, report.layers.length) && report.geometry.subPathCount > report.layers.length) {
    reportBuilt.warnings.push(
      partSplitWarning(
        'PART_SPLIT_PRODUCED_LAYER_ONLY',
        'warning',
        'Split strategy did not increase part granularity over layer-as-part output.',
        undefined,
        {
          groupsCreated: reportBuilt.count,
          layerCount: report.layers.length,
          subPathCount: report.geometry.subPathCount,
        },
      ),
    )
  }

  return applyLayerRolePartExtraction(report, reportBuilt, confirmation)
}

export interface ExtractPartsOptions {
  layerRoleConfirmation?: LayerRoleConfirmation | null
}

export function extractParts(
  report: SvgAnalysisCoreReport,
  parsed?: ParsedSvgDocument,
  options?: ExtractPartsOptions,
): SvgPartExtractionReport {
  const confirmation = options?.layerRoleConfirmation ?? report.layerRoleConfirmation ?? null

  if (!parsed) {
    return extractLayerAsFallback(report, ['Parsed SVG document not available.'], [], confirmation)
  }

  const built = extractBySubPathGrouping(report, parsed, confirmation)
  const withInnerHole = appendInnerHolePackageParts(report, built, parsed, confirmation)
  return applyBondProductionPlates(report, withInnerHole, parsed, confirmation)
}