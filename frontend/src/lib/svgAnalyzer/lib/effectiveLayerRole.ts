import type { LayerAutoRole, LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import type { SvgAnalysisLayer } from '../analyzer/types'

export function findLayerConfirmationEntry(
  layer: Pick<SvgAnalysisLayer, 'id' | 'name'>,
  confirmation: LayerRoleConfirmation | null | undefined,
): LayerRoleConfirmation['layers'][number] | null {
  if (!confirmation) return null
  return (
    confirmation.layers.find((entry) => entry.layerKey === layer.id) ??
    confirmation.layers.find((entry) => entry.layerKey === layer.name) ??
    confirmation.layers.find((entry) => entry.layerId === layer.id) ??
    confirmation.layers.find((entry) => entry.layerName === layer.name) ??
    null
  )
}

export function effectiveLayerRole(
  layer: SvgAnalysisLayer,
  confirmation: LayerRoleConfirmation | null | undefined,
): LayerAutoRole {
  const entry = findLayerConfirmationEntry(layer, confirmation)
  if (entry?.confirmedRole) return entry.confirmedRole
  return layer.autoRole
}

export function isEffectiveInnerHoleLayer(
  layer: SvgAnalysisLayer,
  confirmation: LayerRoleConfirmation | null | undefined,
): boolean {
  return effectiveLayerRole(layer, confirmation) === 'inner_hole'
}

export function plexiInsertsEnabledForLayer(
  layer: SvgAnalysisLayer,
  confirmation: LayerRoleConfirmation | null | undefined,
): boolean {
  const entry = findLayerConfirmationEntry(layer, confirmation)
  return entry?.plexiInserts10mm === true
}
