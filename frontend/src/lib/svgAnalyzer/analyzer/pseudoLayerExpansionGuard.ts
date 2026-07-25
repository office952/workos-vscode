import type { ParsedSvgDocument } from './types'
import {
  isCorelInternalGroupId,
  isGenericLayerName,
  isSemanticProductionOrArtworkLayerName,
} from './layerNameSemantics'

/** Corel numbered layer ids such as `Layer_x0020_2`. */
export function isCorelNumberedLayerId(id: string): boolean {
  return /^Layer_x0020_\d+$/i.test(id.trim())
}

function isDrawableElement(type: ParsedSvgDocument['elements'][number]['type']): boolean {
  return type !== 'group' && type !== 'unknown'
}

function groupHasDrawableElements(doc: ParsedSvgDocument, groupId: string): boolean {
  return doc.elements.some(
    (element) => element.layerId === groupId && isDrawableElement(element.type),
  )
}

/**
 * Preserve validated multi-layer Corel exports instead of color-based pseudo split.
 * - PBL-style `Layer_x0020_N` groups with drawable children
 * - Named production layers (e.g. Remus Alucobond Casetat + Litere Volumetrice)
 */
export function shouldPreserveExistingLayerStructure(doc: ParsedSvgDocument): boolean {
  const numberedCorelLayers = doc.groups.filter(
    (group) => isCorelNumberedLayerId(group.id) && groupHasDrawableElements(doc, group.id),
  )
  if (numberedCorelLayers.length >= 2) return true

  const namedProductionLayers = doc.groups.filter((group) => {
    if (isCorelInternalGroupId(group.id)) return false
    const name = group.name ?? group.id
    if (isGenericLayerName(name)) return false
    if (!groupHasDrawableElements(doc, group.id)) return false
    return isSemanticProductionOrArtworkLayerName(name)
  })
  return namedProductionLayers.length >= 2
}
