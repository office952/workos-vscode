import type { LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import { findBondProductionLayer } from '../part-extractor/productionPlateBounds'
import type { SvgAnalysisCoreReport } from '../analyzer/types'
import { effectiveBondReturnDepths } from '../part-extractor/bondProductionDefaults'
import { maxIlluminationCarcassDepthMm } from '../part-extractor/innerHoleIlluminationBounds'
import { findLayerConfirmationEntry } from './effectiveLayerRole'
import { updateLayerRoleConfirmationEntry } from './layerRoleConfirmationState'

/** Propune adâncime cutie = perete Bond − 9mm când operatorul nu a setat explicit. */
export function defaultInnerHoleCarcassDepthMm(bondWallMm: number): number | null {
  return maxIlluminationCarcassDepthMm(bondWallMm)
}

export function syncInnerHoleCarcassFromBondWall(
  report: SvgAnalysisCoreReport,
  confirmation: LayerRoleConfirmation,
  onlyWhenUnset = true,
): LayerRoleConfirmation {
  const bondLayer = findBondProductionLayer(report, confirmation)
  if (!bondLayer) return confirmation

  const bondEntry = findLayerConfirmationEntry(bondLayer, confirmation)
  const { wallMm } = effectiveBondReturnDepths(bondEntry?.returnDepthMm, bondEntry?.returnDepth2Mm)
  const suggested = defaultInnerHoleCarcassDepthMm(wallMm)
  if (suggested == null || suggested <= 0) return confirmation

  let next = confirmation
  for (const layer of report.layers) {
    const entry = findLayerConfirmationEntry(layer, confirmation)
    const role = entry?.confirmedRole ?? layer.autoRole
    if (role !== 'inner_hole') continue
    if (onlyWhenUnset && entry?.illuminationCarcassDepthMm != null && entry.illuminationCarcassDepthMm > 0) {
      continue
    }
    next = updateLayerRoleConfirmationEntry(next, entry?.layerKey ?? layer.id, {
      illuminationCarcassDepthMm: suggested,
    })
  }
  return next
}
