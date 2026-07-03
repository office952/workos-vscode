import type { SvgAnalysisCoreReport, SvgAnalysisLayer } from '../analyzer/types'
import type { LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import { pickIlluminationSheetConfigId } from '../nesting/pickIlluminationSheet'
import {
  computeDiffuserOuterBounds,
  computeInnerHoleBaseBounds,
  computeUnfoldedWallStripBounds,
  resolveIlluminationCarcassDepthMm,
  splitDiffuserSegments,
  type LayerBoundsMm,
} from './innerHoleIlluminationBounds'
export type { LayerBoundsMm } from './innerHoleIlluminationBounds'
export { computeLayerBoundsFromSubPaths, expandBoundsWithMargin } from './innerHoleIlluminationBounds'
import {
  DIFFUSER_PERIMETER_MARGIN_MM,
  ILLUMINATION_CARCASS_MATERIAL_OFFSET_MM,
  MATERIAL_LABELS,
  SHEET_CONFIG_PLEXI_10MM,
  type DerivedPartKind,
} from './innerHolePackageConstants'
import { createPartWarning } from './partWarnings'
import type { ExtractedSubPath } from './subPathExtractor'
import type { SvgExtractedPart } from './partTypes'

function partNameForKind(layer: SvgAnalysisLayer, kind: DerivedPartKind, index: number, total: number): string {
  if (kind === 'diffuser-plate') {
    return total > 1 ? `${layer.name} — difuzor 3mm (${index + 1}/${total})` : `${layer.name} — difuzor 3mm`
  }
  if (kind === 'back-cover-plate') return `${layer.name} — capac spate Forex 3mm`
  if (kind === 'wall-strip-plate') return `${layer.name} — pereti carcasă Forex 10mm`
  return `${layer.name} — insert plexi 10mm`
}

function buildDerivedPlatePart(
  layer: SvgAnalysisLayer,
  kind: DerivedPartKind,
  bounds: LayerBoundsMm,
  preferredSheetConfigId: string | null,
  index: number,
  nameOverride?: string,
): SvgExtractedPart {
  const id = `derived_${kind}_${layer.name}_${index + 1}`.toLowerCase().replace(/[^a-z0-9_]+/g, '_')
  const name = nameOverride ?? partNameForKind(layer, kind, index, 1)

  const infoMessage =
    kind === 'diffuser-plate'
      ? `Plexi difuzor 3mm — bbox inner_hole/inserturi + ${DIFFUSER_PERIMETER_MARGIN_MM}mm lipire perimetrală pe Bond.`
      : kind === 'back-cover-plate'
        ? 'Capac spate Forex 3mm — aceeași amprentă exterioară ca difuzorul (autoforante în pereti).'
        : kind === 'wall-strip-plate'
          ? 'Pereti carcasă Forex 10mm — bandă desfășurată (perimetru cutie), lipește pe difuzor.'
          : 'Insert plexiglas 10mm pentru relief în golul inner_hole.'

  return {
    id,
    name,
    partExtractionMethod: 'layer-as-part',
    shapeKind: kind === 'relief-insert' ? 'single-contour' : 'unknown',
    sourceSubPathIndexes: [],
    contourCount: 1,
    outerContourCount: 1,
    innerContourCount: 0,
    splitConfidence: 'high',
    groupingReason: 'inner-hole-package',
    derivedPartKind: kind,
    preferredSheetConfigId,
    materialLabel: MATERIAL_LABELS[kind],
    source: {
      layerId: layer.id,
      layerName: layer.name,
      elementIds: [],
      pathElementCount: layer.pathElementCount ?? 0,
      subPathCount: layer.subPathCount ?? 0,
    },
    bounds: {
      xMm: bounds.xMm,
      yMm: bounds.yMm,
      rightMm: bounds.xMm + bounds.widthMm,
      bottomMm: bounds.yMm + bounds.heightMm,
      widthMm: bounds.widthMm,
      heightMm: bounds.heightMm,
      boundingAreaSqm: (bounds.widthMm * bounds.heightMm) / 1_000_000,
    },
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
    canNest: bounds.widthMm > 0 && bounds.heightMm > 0,
    nestingMethod: 'bounding-box',
    confidence: {
      bounds: 'high',
      perimeter: 'low',
      area: 'low',
      source: 'high',
    },
    warnings: [
      createPartWarning(
        kind === 'relief-insert' ? 'INNER_HOLE_INSERT_10MM' : 'INNER_HOLE_DERIVED_PLATE',
        'info',
        infoMessage,
        id,
        {
          derivedPartKind: kind,
          marginMm: kind === 'diffuser-plate' ? DIFFUSER_PERIMETER_MARGIN_MM : null,
        },
      ),
    ],
  }
}

export interface DeriveInnerHolePackageInput {
  layer: SvgAnalysisLayer
  subPaths: ExtractedSubPath[]
  plexiInserts10mm: boolean
  layerRoleConfirmation?: LayerRoleConfirmation | null
  bondReturnDepth1Mm?: number | null
}

function routeIlluminationSheet(bounds: LayerBoundsMm): string | null {
  return pickIlluminationSheetConfigId(bounds.widthMm, bounds.heightMm)
}

export function deriveInnerHolePackageParts(input: DeriveInnerHolePackageInput): SvgExtractedPart[] {
  const { layer, subPaths, plexiInserts10mm, layerRoleConfirmation, bondReturnDepth1Mm } = input

  const baseResult = computeInnerHoleBaseBounds(layer, subPaths)

  if (!baseResult) {
    return [
      {
        ...buildDerivedPlatePart(
          layer,
          'diffuser-plate',
          { xMm: 0, yMm: 0, widthMm: layer.widthMm ?? 0, heightMm: layer.heightMm ?? 0 },
          null,
          0,
        ),
        canNest: false,
        warnings: [
          createPartWarning(
            'INNER_HOLE_BOUNDS_FALLBACK',
            'warning',
            'Nu s-a putut deriva bbox inner_hole — verificați layer-ul sau convertiți textul în path.',
            layer.id,
          ),
        ],
      },
    ]
  }

  const { bounds: baseBounds, source: baseSource } = baseResult
  const outerBounds = computeDiffuserOuterBounds(baseBounds)
  const carcass = resolveIlluminationCarcassDepthMm(layer, layerRoleConfirmation, bondReturnDepth1Mm)
  const wallBounds = computeUnfoldedWallStripBounds(outerBounds, carcass.depthMm)

  const diffuserSegments = splitDiffuserSegments(outerBounds)
  const packageSheetId = routeIlluminationSheet(outerBounds)
  const wallSheetId = routeIlluminationSheet(wallBounds)
  const parts: SvgExtractedPart[] = []

  diffuserSegments.forEach((segment, index) => {
    const part = buildDerivedPlatePart(
      layer,
      'diffuser-plate',
      segment,
      packageSheetId,
      index,
      partNameForKind(layer, 'diffuser-plate', index, diffuserSegments.length),
    )
    part.warnings.push(
      createPartWarning(
        'INNER_HOLE_DIFFUSER_FROM_LAYER',
        'info',
        `Difuzor derivat din bbox layer inner_hole + ${DIFFUSER_PERIMETER_MARGIN_MM}mm perimetral (nu din placa Bond).`,
        part.id,
        { baseSource: baseSource, segmentIndex: index + 1, segmentCount: diffuserSegments.length },
      ),
    )
    if (diffuserSegments.length > 1) {
      part.warnings.push(
        createPartWarning(
          'INNER_HOLE_DIFFUSER_SPLIT',
          'info',
          `Difuzor segmentat pentru nesting/producție (${index + 1}/${diffuserSegments.length}).`,
          part.id,
        ),
      )
    }
    parts.push(part)
  })

  parts.push(
    buildDerivedPlatePart(layer, 'back-cover-plate', outerBounds, packageSheetId, 0),
    (() => {
      const wallPart = buildDerivedPlatePart(layer, 'wall-strip-plate', wallBounds, wallSheetId ?? packageSheetId, 0)
      if (carcass.maxDepthMm != null) {
        wallPart.warnings.push(
          createPartWarning(
            'INNER_HOLE_CARCASS_DEPTH_LIMIT',
            carcass.depthMm <= 0 ? 'error' : carcass.clamped ? 'warning' : 'info',
            carcass.depthMm <= 0
              ? `Adâncime cutie 0mm — întoarcere Bond ${carcass.bondReturnDepth1Mm}mm insuficientă după materiale (${ILLUMINATION_CARCASS_MATERIAL_OFFSET_MM}mm: Bond+difuzor+capac).`
              : carcass.clamped
                ? `Adâncime cutie limitată la ${carcass.depthMm}mm (întoarcere1 ${carcass.bondReturnDepth1Mm}mm − ${carcass.materialOffsetMm}mm materiale).`
                : `Adâncime cutie ${carcass.depthMm}mm (max ${carcass.maxDepthMm}mm = întoarcere1 − ${carcass.materialOffsetMm}mm materiale).`,
            wallPart.id,
            {
              depthMm: carcass.depthMm,
              maxDepthMm: carcass.maxDepthMm,
              bondReturnDepth1Mm: carcass.bondReturnDepth1Mm,
              materialOffsetMm: carcass.materialOffsetMm,
              clamped: carcass.clamped,
            },
          ),
        )
      } else if (carcass.bondReturnDepth1Mm == null) {
        wallPart.warnings.push(
          createPartWarning(
            'INNER_HOLE_CARCASS_NO_BOND_RETURN',
            'warning',
            `Adâncime cutie ${carcass.depthMm}mm — nu există întoarcere 1 Bond confirmată pentru limită automată.`,
            wallPart.id,
          ),
        )
      }
      return wallPart
    })(),
  )

  if (plexiInserts10mm) {
    const layerSubPaths = subPaths.filter((subPath) => subPath.layerName === layer.name && subPath.bboxMm)
    layerSubPaths.forEach((subPath, index) => {
      const bbox = subPath.bboxMm!
      parts.push(
        buildDerivedPlatePart(
          layer,
          'relief-insert',
          { xMm: bbox.x, yMm: bbox.y, widthMm: bbox.width, heightMm: bbox.height },
          SHEET_CONFIG_PLEXI_10MM,
          index,
        ),
      )
    })
  }

  parts.push(
    createPartWarningPart(
      layer,
      'INNER_HOLE_ELECTRICAL_TEMPLATE',
      'Electric (LED, cablaj) — șablon produs / BOM, fără nesting geometric.',
    ),
  )

  return parts
}

function createPartWarningPart(layer: SvgAnalysisLayer, code: string, message: string): SvgExtractedPart {
  return {
    id: `derived_${layer.name}_electrical_note`.toLowerCase().replace(/[^a-z0-9_]+/g, '_'),
    name: `${layer.name} — electric (șablon)`,
    partExtractionMethod: 'layer-as-part',
    shapeKind: 'unknown',
    sourceSubPathIndexes: [],
    contourCount: 0,
    outerContourCount: 0,
    innerContourCount: 0,
    splitConfidence: 'high',
    groupingReason: 'inner-hole-package',
    derivedPartKind: null,
    preferredSheetConfigId: null,
    materialLabel: 'Electric — BOM șablon',
    source: {
      layerId: layer.id,
      layerName: layer.name,
      elementIds: [],
      pathElementCount: 0,
      subPathCount: 0,
    },
    bounds: {
      widthMm: null,
      heightMm: null,
      boundingAreaSqm: null,
    },
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
    canNest: false,
    nestingMethod: 'none',
    confidence: {
      bounds: 'low',
      perimeter: 'low',
      area: 'low',
      source: 'high',
    },
    warnings: [createPartWarning(code, 'info', message, layer.id)],
  }
}
