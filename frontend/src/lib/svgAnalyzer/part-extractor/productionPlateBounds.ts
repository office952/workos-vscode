import type { LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import type { SvgAnalysisCoreReport, SvgAnalysisLayer } from '../analyzer/types'
import { effectiveLayerRole, findLayerConfirmationEntry } from '../lib/effectiveLayerRole'
import { effectiveBondReturnDepths } from './bondProductionDefaults'
import type { LayerBoundsMm } from './deriveInnerHolePackage'
import { computeLayerBoundsFromSubPaths } from './deriveInnerHolePackage'
import type { ExtractedSubPath } from './subPathExtractor'

/** Per-side flat margin: perete volum + buză prindere (same ACM sheet, operator mm). */
export function totalReturnDepthPerSide(
  returnDepth1Mm: number | null | undefined,
  returnDepth2Mm: number | null | undefined,
  useDefaults = false,
): number {
  const { wallMm, lipMm } = effectiveBondReturnDepths(returnDepth1Mm, returnDepth2Mm, useDefaults)
  return wallMm + lipMm
}

export function expandBoundsWithReturns(
  bounds: LayerBoundsMm,
  returnDepth1Mm: number | null | undefined,
  returnDepth2Mm: number | null | undefined,
): LayerBoundsMm {
  const perSide = totalReturnDepthPerSide(returnDepth1Mm, returnDepth2Mm)
  if (perSide <= 0) return bounds

  return {
    xMm: bounds.xMm - perSide,
    yMm: bounds.yMm - perSide,
    widthMm: bounds.widthMm + perSide * 2,
    heightMm: bounds.heightMm + perSide * 2,
  }
}

export function isBondProductionLayer(
  layer: SvgAnalysisLayer,
  confirmation: LayerRoleConfirmation | null | undefined,
): boolean {
  const role = effectiveLayerRole(layer, confirmation)
  if (role === 'backing' || role === 'support_panel') return true
  return /\bbond\b/i.test(layer.name)
}

export function findBondProductionLayer(
  report: SvgAnalysisCoreReport,
  confirmation: LayerRoleConfirmation | null | undefined,
): SvgAnalysisLayer | null {
  const bondByName = report.layers.find((layer) => /\bbond\b/i.test(layer.name) || /\bfundal\b/i.test(layer.name))
  if (bondByName) return bondByName

  return report.layers.find((layer) => isBondProductionLayer(layer, confirmation)) ?? null
}

export function layerVisualBoundsMm(
  layer: SvgAnalysisLayer,
  subPaths: ExtractedSubPath[],
): LayerBoundsMm {
  const fromSubPaths = computeLayerBoundsFromSubPaths(subPaths, layer.name)
  if (fromSubPaths) return fromSubPaths

  return {
    xMm: 0,
    yMm: 0,
    widthMm: layer.widthMm ?? 0,
    heightMm: layer.heightMm ?? 0,
  }
}

export function computeBondProductionBounds(
  layer: SvgAnalysisLayer,
  subPaths: ExtractedSubPath[],
  confirmation: LayerRoleConfirmation | null | undefined,
): LayerBoundsMm {
  const visual = layerVisualBoundsMm(layer, subPaths)
  const { returnDepthMm, returnDepth2Mm } = returnDepthsForLayer(layer, confirmation)
  return expandBoundsWithReturns(visual, returnDepthMm, returnDepth2Mm)
}

export function returnDepthsForLayer(
  layer: SvgAnalysisLayer,
  confirmation: LayerRoleConfirmation | null | undefined,
): { returnDepthMm: number; returnDepth2Mm: number; wallFromDefault: boolean; lipFromDefault: boolean } {
  const entry = findLayerConfirmationEntry(layer, confirmation)
  const effective = effectiveBondReturnDepths(entry?.returnDepthMm, entry?.returnDepth2Mm)
  return {
    returnDepthMm: effective.wallMm,
    returnDepth2Mm: effective.lipMm,
    wallFromDefault: effective.wallFromDefault,
    lipFromDefault: effective.lipFromDefault,
  }
}
