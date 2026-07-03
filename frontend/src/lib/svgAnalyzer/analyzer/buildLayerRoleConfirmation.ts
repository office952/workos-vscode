import type { LayerAnalysis } from './types'
import type { LayerAutoRole, LayerConfirmationState, LayerRoleConfirmation, LayerRoleConfirmationStatus } from './layerRoleTypes'
import { PRODUCTION_LAYER_ROLES } from './layerRoleTypes'
import { DEFAULT_BOND_LIP_DEPTH_MM, DEFAULT_BOND_WALL_DEPTH_MM } from '../part-extractor/bondProductionDefaults'

export function layerKeyFromLayer(layer: Pick<LayerAnalysis, 'id' | 'name'>): string {
  return layer.id || layer.name
}

function computeConfirmationStatus(layers: LayerRoleConfirmation['layers']): LayerRoleConfirmationStatus {
  const productionLayers = layers.filter((layer) => PRODUCTION_LAYER_ROLES.has(layer.autoRole) || layer.autoRole === 'unknown')
  if (productionLayers.length === 0) return 'missing'

  const confirmed = productionLayers.filter((layer) => layer.confirmationState === 'confirmed' || layer.confirmationState === 'ignored')

  if (confirmed.length === productionLayers.length) return 'complete'
  if (confirmed.length > 0) return 'partial'
  return 'missing'
}

function isBondLayerForDefaults(layer: LayerAnalysis): boolean {
  if (/\bbond\b/i.test(layer.name) || /\bfundal\b/i.test(layer.name)) return true
  return layer.autoRole === 'support_panel' || layer.autoRole === 'backing'
}

export function buildLayerRoleConfirmationDraft(layers: LayerAnalysis[]): LayerRoleConfirmation {
  const entries = layers.map((layer) => {
    const bondDefaults = isBondLayerForDefaults(layer)
    return {
      layerKey: layerKeyFromLayer(layer),
      layerId: layer.id,
      layerName: layer.name,
      autoRole: layer.autoRole,
      autoConfidence: layer.autoConfidence,
      autoRoleCandidates: layer.autoRoleCandidates,
      confirmedRole: null as LayerAutoRole | null,
      confirmationState: 'pending' as LayerConfirmationState,
      operatorNote: null,
      plexiInserts10mm: false,
      returnDepthMm: bondDefaults ? DEFAULT_BOND_WALL_DEPTH_MM : null,
      returnDepth2Mm: bondDefaults ? DEFAULT_BOND_LIP_DEPTH_MM : null,
      illuminationCarcassDepthMm: null as number | null,
      paintEvidence: layer.paintEvidence,
      productionHint: layer.productionHint,
    }
  })

  return {
    schemaVersion: 'layer_role_confirmation_v1',
    confirmationStatus: computeConfirmationStatus(entries),
    layers: entries,
  }
}

export function recomputeLayerRoleConfirmationStatus(
  confirmation: LayerRoleConfirmation,
): LayerRoleConfirmationStatus {
  return computeConfirmationStatus(confirmation.layers)
}
