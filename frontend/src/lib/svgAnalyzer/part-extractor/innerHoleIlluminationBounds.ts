import type { LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import type { SvgAnalysisLayer } from '../analyzer/types'
import { findLayerConfirmationEntry } from '../lib/effectiveLayerRole'
import type { ExtractedSubPath } from './subPathExtractor'
import {
  DEFAULT_ILLUMINATION_CARCASS_DEPTH_MM,
  DIFFUSER_MAX_SEGMENT_WIDTH_MM,
  DIFFUSER_PERIMETER_MARGIN_MM,
  ILLUMINATION_CARCASS_MATERIAL_OFFSET_MM,
} from './innerHolePackageConstants'

export interface LayerBoundsMm {
  xMm: number
  yMm: number
  widthMm: number
  heightMm: number
}

export function computeLayerBoundsFromSubPaths(subPaths: ExtractedSubPath[], layerName: string): LayerBoundsMm | null {
  const layerSubPaths = subPaths.filter((subPath) => subPath.layerName === layerName && subPath.bboxMm)
  if (layerSubPaths.length === 0) return null

  let minX = Number.POSITIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY

  for (const subPath of layerSubPaths) {
    const bbox = subPath.bboxMm!
    minX = Math.min(minX, bbox.x)
    minY = Math.min(minY, bbox.y)
    maxX = Math.max(maxX, bbox.x + bbox.width)
    maxY = Math.max(maxY, bbox.y + bbox.height)
  }

  return {
    xMm: minX,
    yMm: minY,
    widthMm: maxX - minX,
    heightMm: maxY - minY,
  }
}

export function expandBoundsWithMargin(bounds: LayerBoundsMm, marginMm: number): LayerBoundsMm {
  return {
    xMm: bounds.xMm - marginMm,
    yMm: bounds.yMm - marginMm,
    widthMm: bounds.widthMm + marginMm * 2,
    heightMm: bounds.heightMm + marginMm * 2,
  }
}

export function maxIlluminationCarcassDepthMm(bondReturnDepth1Mm: number | null | undefined): number | null {
  if (bondReturnDepth1Mm == null || bondReturnDepth1Mm <= 0) return null
  return Math.max(0, bondReturnDepth1Mm - ILLUMINATION_CARCASS_MATERIAL_OFFSET_MM)
}

export interface ResolvedIlluminationCarcassDepth {
  depthMm: number
  requestedDepthMm: number | null
  maxDepthMm: number | null
  bondReturnDepth1Mm: number | null
  clamped: boolean
  materialOffsetMm: number
}

export function resolveIlluminationCarcassDepthMm(
  layer: SvgAnalysisLayer,
  confirmation: LayerRoleConfirmation | null | undefined,
  bondReturnDepth1Mm: number | null | undefined,
): ResolvedIlluminationCarcassDepth {
  const entry = findLayerConfirmationEntry(layer, confirmation)
  const requested = entry?.illuminationCarcassDepthMm
  const maxDepthMm = maxIlluminationCarcassDepthMm(bondReturnDepth1Mm)
  const requestedOrDefault =
    requested != null && requested > 0
      ? requested
      : maxDepthMm != null && maxDepthMm > 0
        ? maxDepthMm
        : DEFAULT_ILLUMINATION_CARCASS_DEPTH_MM

  let depthMm = requestedOrDefault
  let clamped = false

  if (maxDepthMm != null && depthMm > maxDepthMm) {
    depthMm = maxDepthMm
    clamped = true
  }

  return {
    depthMm,
    requestedDepthMm: requested,
    maxDepthMm,
    bondReturnDepth1Mm: bondReturnDepth1Mm ?? null,
    clamped,
    materialOffsetMm: ILLUMINATION_CARCASS_MATERIAL_OFFSET_MM,
  }
}

/** @deprecated Prefer resolveIlluminationCarcassDepthMm — nu limitează la întoarcerea Bond. */
export function illuminationCarcassDepthMm(
  layer: SvgAnalysisLayer,
  confirmation: LayerRoleConfirmation | null | undefined,
): number {
  return resolveIlluminationCarcassDepthMm(layer, confirmation, null).depthMm
}

export function computeInnerHoleBaseBounds(
  layer: SvgAnalysisLayer,
  subPaths: ExtractedSubPath[],
): { bounds: LayerBoundsMm; source: 'inner-hole-layer' } | null {
  if ((layer.widthMm ?? 0) > 0 && (layer.heightMm ?? 0) > 0) {
    return {
      bounds: {
        xMm: 0,
        yMm: 0,
        widthMm: layer.widthMm ?? 0,
        heightMm: layer.heightMm ?? 0,
      },
      source: 'inner-hole-layer',
    }
  }

  const fromSubPaths = computeLayerBoundsFromSubPaths(subPaths, layer.name)
  if (fromSubPaths && fromSubPaths.widthMm > 0 && fromSubPaths.heightMm > 0) {
    return { bounds: fromSubPaths, source: 'inner-hole-layer' }
  }

  return null
}

export function computeDiffuserOuterBounds(base: LayerBoundsMm): LayerBoundsMm {
  return expandBoundsWithMargin(base, DIFFUSER_PERIMETER_MARGIN_MM)
}

export function splitDiffuserSegments(outer: LayerBoundsMm, maxSegmentWidthMm = DIFFUSER_MAX_SEGMENT_WIDTH_MM): LayerBoundsMm[] {
  if (outer.widthMm <= maxSegmentWidthMm) return [outer]

  const segments: LayerBoundsMm[] = []
  const right = outer.xMm + outer.widthMm
  let x = outer.xMm

  while (x < right - 0.001) {
    const widthMm = Math.min(maxSegmentWidthMm, right - x)
    segments.push({
      xMm: x,
      yMm: outer.yMm,
      widthMm,
      heightMm: outer.heightMm,
    })
    x += widthMm
  }

  return segments
}

export function computeUnfoldedWallStripBounds(outer: LayerBoundsMm, carcassDepthMm: number): LayerBoundsMm {
  const flangeMm = 10
  return {
    xMm: outer.xMm,
    yMm: outer.yMm,
    widthMm: 2 * (outer.widthMm + outer.heightMm),
    heightMm: carcassDepthMm + flangeMm,
  }
}
