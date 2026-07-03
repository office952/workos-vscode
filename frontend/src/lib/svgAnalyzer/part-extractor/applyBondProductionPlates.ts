import type { SvgAnalysisLayer } from '../analyzer/types'
import type { LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import type { ParsedSvgDocument, SvgAnalysisCoreReport } from '../analyzer/types'
import { isBondPlatePart, pickAcmPanelSheetForParts } from '../nesting/pickAcmPanelSheet'
import { createPartWarning } from './partWarnings'
import {
  computeBondProductionBounds,
  findBondProductionLayer,
  isBondProductionLayer,
  returnDepthsForLayer,
  totalReturnDepthPerSide,
} from './productionPlateBounds'
import type { ExtractedSubPath } from './subPathExtractor'
import type { SvgExtractedPart, SvgPartExtractionReport } from './partTypes'
import { extractSubPaths } from './subPathExtractor'
function boundsToPartFields(bounds: { xMm: number; yMm: number; widthMm: number; heightMm: number }) {
  return {
    xMm: bounds.xMm,
    yMm: bounds.yMm,
    rightMm: bounds.xMm + bounds.widthMm,
    bottomMm: bounds.yMm + bounds.heightMm,
    widthMm: bounds.widthMm,
    heightMm: bounds.heightMm,
    boundingAreaSqm: (bounds.widthMm * bounds.heightMm) / 1_000_000,
  }
}

function applyBondBoundsToPart(
  part: SvgExtractedPart,
  productionBounds: ReturnType<typeof computeBondProductionBounds>,
  returnPerSide: number,
): SvgExtractedPart {
  const warnings = [...part.warnings]
  if (returnPerSide > 0) {
    warnings.push(
      createPartWarning(
        'BOND_PLATE_RETURN_MARGIN',
        'info',
        `Placă Bond pentru nesting: bbox vizual + ${returnPerSide}mm întoarceri pe fiecare latură.`,
        part.id,
        { returnPerSideMm: returnPerSide },
      ),
    )
  } else {
    warnings.push(
      createPartWarning(
        'BOND_PLATE_NEST_RECT',
        'info',
        'Placă Bond — nesting pe dreptunghiul layer (fără întoarceri selectate).',
        part.id,
      ),
    )
  }

  return {
    ...part,
    materialLabel: part.materialLabel ?? 'Bond / Dibond backing',
    canNest: productionBounds.widthMm > 0 && productionBounds.heightMm > 0,
    nestingMethod: 'bounding-box',
    bounds: boundsToPartFields(productionBounds),
    warnings,
  }
}

function buildBondPlatePart(
  layer: SvgAnalysisLayer,
  productionBounds: ReturnType<typeof computeBondProductionBounds>,
  returnPerSide: number,
): SvgExtractedPart {
  const id = `bond_plate_${layer.name}`.toLowerCase().replace(/[^a-z0-9_]+/g, '_')
  const warnings = [
    createPartWarning(
      returnPerSide > 0 ? 'BOND_PLATE_RETURN_MARGIN' : 'BOND_PLATE_NEST_RECT',
      'info',
      returnPerSide > 0
        ? `Placă Bond pentru nesting: bbox vizual + ${returnPerSide}mm întoarceri pe fiecare latură.`
        : 'Placă Bond — nesting pe dreptunghiul layer (fără întoarceri selectate).',
      id,
      returnPerSide > 0 ? { returnPerSideMm: returnPerSide } : undefined,
    ),
  ]

  return {
    id,
    name: `${layer.name} — placă Bond`,
    partExtractionMethod: 'layer-as-part',
    shapeKind: 'unknown',
    sourceSubPathIndexes: [],
    contourCount: 1,
    outerContourCount: 1,
    innerContourCount: 0,
    splitConfidence: 'high',
    groupingReason: 'inner-hole-package',
    materialLabel: 'Bond / Dibond backing',
    source: {
      layerId: layer.id,
      layerName: layer.name,
      elementIds: [],
      pathElementCount: layer.pathElementCount ?? 0,
      subPathCount: layer.subPathCount ?? 0,
    },
    bounds: boundsToPartFields(productionBounds),
    geometry: {
      outerPerimeterMm: null,
      outerPerimeterMl: null,
      innerPerimeterMm: 0,
      innerPerimeterMl: 0,
      fragmentPerimeterMm: 0,
      fragmentPerimeterMl: 0,
      totalContourPerimeterMm: null,
      totalContourPerimeterMl: null,
      perimeterMm: null,
      perimeterMl: null,
      filledAreaSqm: null,
      closedSubPathCount: 0,
      openSubPathCount: 0,
    },
    colors: layer.colors,
    quantity: 1,
    canNest: productionBounds.widthMm > 0 && productionBounds.heightMm > 0,
    nestingMethod: 'bounding-box',
    confidence: { bounds: 'high', perimeter: 'low', area: 'low', source: 'high' },
    warnings,
  }
}

export function applyBondProductionPlates(
  report: SvgAnalysisCoreReport,
  built: SvgPartExtractionReport,
  parsed: ParsedSvgDocument,
  confirmation: LayerRoleConfirmation | null | undefined,
): SvgPartExtractionReport {
  let items = built.items

  const bondLayer = findBondProductionLayer(report, confirmation)
  if (bondLayer) {
    const extracted = extractSubPaths(parsed, report.document.mmPerViewBoxUnit)
    const productionBounds = computeBondProductionBounds(bondLayer, extracted.subPaths, confirmation)
    const { returnDepthMm, returnDepth2Mm } = returnDepthsForLayer(bondLayer, confirmation)
    const returnPerSide = totalReturnDepthPerSide(returnDepthMm, returnDepth2Mm)

    const bondParts = built.items.filter((part) => part.source.layerName === bondLayer.name)

    if (bondParts.length === 0) {
      if (productionBounds.widthMm > 0 && productionBounds.heightMm > 0) {
        items = [...built.items, buildBondPlatePart(bondLayer, productionBounds, returnPerSide)]
      }
    } else {
      items = built.items.map((part) => {
        if (part.source.layerName !== bondLayer.name) return part
        return applyBondBoundsToPart(part, productionBounds, returnPerSide)
      })
    }
  }

  const syncedItems = syncBondSheetRouting(items)

  return {
    ...built,
    items: syncedItems,
    count: syncedItems.length,
    nestableCount: syncedItems.filter((item) => item.canNest).length,
  }
}

function syncBondSheetRouting(items: SvgExtractedPart[]): SvgExtractedPart[] {
  const bondParts = items.filter(isBondPlatePart)
  if (bondParts.length === 0) return items

  const sheetConfigId = pickAcmPanelSheetForParts(bondParts)
  if (!sheetConfigId) {
    return items.map((part) => {
      if (!isBondPlatePart(part)) return part
      return {
        ...part,
        preferredSheetConfigId: null,
        warnings: [
          ...part.warnings,
          createPartWarning(
            'BOND_PLATE_DOES_NOT_FIT_SHEET',
            'warning',
            'Placă Bond depășește formatele ACM standard (3000×1500, 4000×1500).',
            part.id,
            {
              widthMm: part.bounds.widthMm,
              heightMm: part.bounds.heightMm,
            },
          ),
        ],
      }
    })
  }

  return items.map((part) => {
    if (!isBondPlatePart(part)) return part
    const warnings = [...part.warnings]
    if (!warnings.some((warning) => warning.code === 'BOND_PLATE_SHEET_ROUTING')) {
      warnings.push(
        createPartWarning(
          'BOND_PLATE_SHEET_ROUTING',
          'info',
          `Placă Bond ACM pe foaia ${sheetConfigId}.`,
          part.id,
          { sheetConfigId },
        ),
      )
    }
    return {
      ...part,
      preferredSheetConfigId: sheetConfigId,
      warnings,
    }
  })
}

export { isBondProductionLayer }
