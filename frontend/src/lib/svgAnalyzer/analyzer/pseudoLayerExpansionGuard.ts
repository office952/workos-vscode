import type { ParsedSvgDocument } from './types'

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
 * Preserve validated multi-layer Corel exports (e.g. PBL) instead of color-based pseudo split.
 * Only counts declared `Layer_x0020_N` groups with drawable children — not nested `el-*` wrappers.
 */
export function shouldPreserveExistingLayerStructure(doc: ParsedSvgDocument): boolean {
  const numberedCorelLayers = doc.groups.filter(
    (group) => isCorelNumberedLayerId(group.id) && groupHasDrawableElements(doc, group.id),
  )
  return numberedCorelLayers.length >= 2
}
