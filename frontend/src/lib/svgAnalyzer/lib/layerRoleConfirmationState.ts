import type { LayerAutoRole, LayerConfirmationState, LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import type { SvgAnalysisCoreReport } from '../analyzer/types'
import { recomputeLayerRoleConfirmationStatus } from '../analyzer/buildLayerRoleConfirmation'
import { syncInnerHoleCarcassFromBondWall } from './bondInnerHoleLinkage'

export function updateLayerRoleConfirmationEntry(
  confirmation: LayerRoleConfirmation,
  layerKey: string,
  patch: {
    confirmedRole?: LayerAutoRole
    confirmationState?: LayerConfirmationState
    operatorNote?: string | null
    plexiInserts10mm?: boolean
    returnDepthMm?: number | null
    returnDepth2Mm?: number | null
    illuminationCarcassDepthMm?: number | null
  },
): LayerRoleConfirmation {
  const layers = confirmation.layers.map((layer) => {
    if (layer.layerKey !== layerKey) return layer
    const confirmationState = patch.confirmationState ?? layer.confirmationState
    const confirmedRole = patch.confirmedRole ?? layer.confirmedRole ?? layer.autoRole
    return {
      ...layer,
      confirmedRole,
      confirmationState,
      operatorNote: patch.operatorNote !== undefined ? patch.operatorNote : layer.operatorNote,
      plexiInserts10mm: patch.plexiInserts10mm !== undefined ? patch.plexiInserts10mm : layer.plexiInserts10mm,
      returnDepthMm: patch.returnDepthMm !== undefined ? patch.returnDepthMm : layer.returnDepthMm,
      returnDepth2Mm: patch.returnDepth2Mm !== undefined ? patch.returnDepth2Mm : layer.returnDepth2Mm,
      illuminationCarcassDepthMm:
        patch.illuminationCarcassDepthMm !== undefined ? patch.illuminationCarcassDepthMm : layer.illuminationCarcassDepthMm,
    }
  })

  return {
    ...confirmation,
    layers,
    confirmationStatus: recomputeLayerRoleConfirmationStatus({ ...confirmation, layers }),
  }
}

export function confirmLayerRole(
  confirmation: LayerRoleConfirmation,
  layerKey: string,
  confirmedRole: LayerAutoRole,
): LayerRoleConfirmation {
  return updateLayerRoleConfirmationEntry(confirmation, layerKey, {
    confirmedRole,
    confirmationState: 'confirmed',
  })
}

/** Operator picked a role from the dropdown — save selection and mark confirmed. */
export function applyLayerRoleSelection(
  confirmation: LayerRoleConfirmation,
  layerKey: string,
  confirmedRole: LayerAutoRole,
): LayerRoleConfirmation {
  return confirmLayerRole(confirmation, layerKey, confirmedRole)
}

export function setPlexiInserts10mm(
  confirmation: LayerRoleConfirmation,
  layerKey: string,
  enabled: boolean,
): LayerRoleConfirmation {
  return updateLayerRoleConfirmationEntry(confirmation, layerKey, { plexiInserts10mm: enabled })
}

export function setReturnDepths(
  confirmation: LayerRoleConfirmation,
  layerKey: string,
  patch: { returnDepthMm?: number | null; returnDepth2Mm?: number | null },
  report?: SvgAnalysisCoreReport | null,
): LayerRoleConfirmation {
  let next = updateLayerRoleConfirmationEntry(confirmation, layerKey, patch)
  if (report) {
    next = syncInnerHoleCarcassFromBondWall(report, next, true)
  }
  return next
}

export function setIlluminationCarcassDepthMm(
  confirmation: LayerRoleConfirmation,
  layerKey: string,
  depthMm: number | null,
): LayerRoleConfirmation {
  return updateLayerRoleConfirmationEntry(confirmation, layerKey, { illuminationCarcassDepthMm: depthMm })
}

function isBondLayerRole(role: LayerAutoRole): boolean {
  return role === 'backing' || role === 'support_panel'
}

export function isBondReturnConfigLayer(role: LayerAutoRole, layerName: string): boolean {
  return isBondLayerRole(role) || /\bbond\b/i.test(layerName)
}
