import type { GeometrySummary, ParsedSvgDocument } from './types'
import {
  isLetterLayerId,
  isLogoLayerId,
  letterSemanticForSolidFill,
} from './anaMariaLetterSemantics'
import {
  deriveVisualPositionHint,
  isNeutralLogoInstanceId,
  nextNeutralLogoInstanceId,
} from '@/lib/intakeV6/layerInstanceIdentity'
import {
  isCorelInternalGroupId,
  isGenericLayerName,
  isLogoArtworkLayerName,
  isPseudoLayerId,
  isSemanticProductionOrArtworkLayerName,
  normalizeLayerDisplayName,
} from './layerNameSemantics'
import { shouldPreserveExistingLayerStructure } from './pseudoLayerExpansionGuard'

export type ExpandedLayerKind = 'real' | 'pseudo' | 'raster_artwork'

export interface LayerExpansionMeta {
  layerKind: ExpandedLayerKind
  layerOrigin: string
  roleReason: string
  positionHint?: 'left' | 'right' | 'center' | 'top' | 'bottom' | null
  /** Semantic SVG group ids before color-cluster rewrite (provenance). */
  sourceGroupIds?: string[]
  /** Drawable element ids owned by this layer after expansion. */
  elementIds?: string[]
}

export interface SemanticPseudoLayerExpansionResult {
  doc: ParsedSvgDocument
  layerMeta: Map<string, LayerExpansionMeta>
}

function viewBoxCenterX(doc: ParsedSvgDocument): number | null {
  if (!doc.viewBox) return null
  return doc.viewBox.minX + doc.viewBox.width / 2
}

function isDrawableElement(type: ParsedSvgDocument['elements'][number]['type']): boolean {
  return type !== 'group' && type !== 'unknown'
}

function findRealLetterGroups(doc: ParsedSvgDocument): ParsedSvgDocument['groups'] {
  return doc.groups.filter((group) => {
    if (isCorelInternalGroupId(group.id)) return false
    return isLetterLayerId(group.id) || isLetterLayerId(group.name ?? '')
  })
}

function findRealLogoGroups(doc: ParsedSvgDocument): ParsedSvgDocument['groups'] {
  return doc.groups.filter((group) => {
    if (isCorelInternalGroupId(group.id)) return false
    return isLogoLayerId(group.id) || isLogoLayerId(group.name ?? '')
  })
}

function drawableIdsForLayer(
  elements: ParsedSvgDocument['elements'],
  layerId: string,
): string[] {
  return elements
    .filter((element) => element.layerId === layerId && isDrawableElement(element.type))
    .map((element) => element.elementId)
}

function isLogoStrokeOutlinePath(element: ParsedSvgDocument['elements'][number]): boolean {
  if (!['path', 'polygon', 'polyline', 'rect', 'circle', 'ellipse', 'line'].includes(element.type)) return false
  const fill = element.fillSolid ?? element.fill
  const stroke = element.strokeSolid ?? element.stroke
  const fillNone = fill == null || fill === 'none' || fill === 'transparent'
  const hasStroke = stroke != null && stroke !== 'none'
  return fillNone && hasStroke
}

function assignLogoGroupElement(
  elements: ParsedSvgDocument['elements'],
  group: ParsedSvgDocument['groups'][number],
  elementId: string,
  layerId: string,
  layerName: string,
): void {
  const element = elements.find((entry) => entry.elementId === elementId)
  if (element) {
    element.layerId = layerId
    element.layerName = layerName
  }
  if (!group.elementIds.includes(elementId)) {
    group.elementIds.push(elementId)
  }
}

function bboxOverlap(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
  margin = 0,
): boolean {
  return !(
    a.x + a.width + margin < b.x ||
    b.x + b.width + margin < a.x ||
    a.y + a.height + margin < b.y ||
    b.y + b.height + margin < a.y
  )
}

function resolveSequentialLogoName(groups: ParsedSvgDocument['groups'], groupId: string): string {
  const existingIndex = groups.findIndex((entry) => entry.id === groupId)
  const logoGroupCount = groups.filter(
    (entry) => isNeutralLogoInstanceId(entry.id) || isLogoLayerId(entry.id) || entry.id.startsWith('logo-'),
  ).length
  const index = existingIndex >= 0 ? existingIndex + 1 : logoGroupCount + 1
  return `Logo ${index}`
}

function assignRasterLogoLayers(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
  elements: ParsedSvgDocument['elements'],
  newGroups: ParsedSvgDocument['groups'],
  layerMeta: Map<string, LayerExpansionMeta>,
  layerKind: ExpandedLayerKind,
): void {
  const geoById = new Map(geometry.elementGeometries.map((g) => [g.elementId, g]))
  const centerX = viewBoxCenterX(doc)
  const images = elements.filter((element) => element.type === 'image')

  for (const image of images) {
    const geo = geoById.get(image.elementId)
    const bbox = geo?.bbox
    const outlineMargin = bbox ? Math.max(bbox.width, bbox.height) * 0.08 : 0
    const imageCenterX = bbox ? bbox.x + bbox.width / 2 : 0
    const positionHint = deriveVisualPositionHint(imageCenterX, centerX)

    const imageElement = elements.find((entry) => entry.elementId === image.elementId)
    const parentLayerId = imageElement?.layerId ?? null

    let group = newGroups.find((entry) => entry.elementIds.includes(image.elementId))
    if (!group && bbox) {
      group = newGroups.find((entry) => {
        if (!isNeutralLogoInstanceId(entry.id) && !isLogoLayerId(entry.id)) return false
        const memberGeo = entry.elementIds
          .map((elementId) => geoById.get(elementId)?.bbox)
          .find(Boolean)
        return memberGeo ? bboxOverlap(bbox, memberGeo, outlineMargin) : false
      })
    }
    if (!group) {
      const id = nextNeutralLogoInstanceId(newGroups.map((entry) => entry.id))
      const name = resolveSequentialLogoName(newGroups, id)
      group = { id, name, elementIds: [] }
      newGroups.push(group)
      layerMeta.set(id, {
        layerKind: layerKind === 'real' ? 'real' : 'raster_artwork',
        layerOrigin: layerKind === 'real' ? 'corel_logo_layer' : 'raster_image_split',
        roleReason:
          layerKind === 'real'
            ? 'Named Corel logo layer preserved as printed artwork.'
            : 'Raster image isolated as printed artwork pseudo-layer.',
        positionHint,
      })
    }

    const { id, name } = group
    assignLogoGroupElement(elements, group, image.elementId, id, name)

    for (const candidate of elements) {
      if (candidate.elementId === image.elementId) continue
      if (!isLogoStrokeOutlinePath(candidate)) continue
      if (candidate.layerId === id) continue

      let shouldAssign = false
      if (parentLayerId && candidate.layerId === parentLayerId) {
        shouldAssign = true
      } else if (bbox) {
        const candidateGeo = geoById.get(candidate.elementId)
        if (candidateGeo?.bbox && bboxOverlap(bbox, candidateGeo.bbox, outlineMargin)) {
          shouldAssign = true
        }
      }

      if (shouldAssign) {
        assignLogoGroupElement(elements, group, candidate.elementId, id, name)
      }
    }
  }
}

function assignedElementIds(groups: ParsedSvgDocument['groups']): Set<string> {
  return new Set(groups.flatMap((group) => group.elementIds))
}

function shouldUseAnaMariaFillSemantics(fileName: string): boolean {
  const token = fileName.trim().toLowerCase()
  return token.includes('gradi-curat') || token.includes('ana-maria-gradinita')
}

function assignStrokeOnlyLogoLayers(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
  elements: ParsedSvgDocument['elements'],
  newGroups: ParsedSvgDocument['groups'],
  layerMeta: Map<string, LayerExpansionMeta>,
  layerKind: ExpandedLayerKind,
): void {
  const geoById = new Map(geometry.elementGeometries.map((g) => [g.elementId, g]))
  const centerX = viewBoxCenterX(doc)
  const alreadyAssigned = assignedElementIds(newGroups)
  const candidates = elements
    .filter((element) => isLogoStrokeOutlinePath(element) && !alreadyAssigned.has(element.elementId))
    .sort((a, b) => {
      return a.index - b.index
    })

  for (const candidate of candidates) {
    const bbox = geoById.get(candidate.elementId)?.bbox
    const candidateCenterX = bbox ? bbox.x + bbox.width / 2 : null
    const positionHint = deriveVisualPositionHint(candidateCenterX, centerX)

    let group = newGroups.find((entry) => entry.elementIds.includes(candidate.elementId))
    if (!group) {
      const id = nextNeutralLogoInstanceId(newGroups.map((entry) => entry.id))
      const name = resolveSequentialLogoName(newGroups, id)
      group = { id, name, elementIds: [] }
      newGroups.push(group)
      if (!layerMeta.has(id)) {
        layerMeta.set(id, {
          layerKind: layerKind === 'real' ? 'real' : 'pseudo',
          layerOrigin: layerKind === 'real' ? 'corel_logo_stroke_outline' : 'stroke_vector_outline',
          roleReason: 'Stroke-only vector isolated as logo/artwork candidate; operator must confirm production intent.',
          positionHint,
        })
      }
    }

    assignLogoGroupElement(elements, group, candidate.elementId, group.id, group.name)
  }
}

function buildRealSemanticLayerSet(
  doc: ParsedSvgDocument,
  elements: ParsedSvgDocument['elements'],
  geometry: GeometrySummary,
): SemanticPseudoLayerExpansionResult | null {
  const letterGroups = findRealLetterGroups(doc)
  if (letterGroups.length < 4) return null

  const layerMeta = new Map<string, LayerExpansionMeta>()
  const newGroups: ParsedSvgDocument['groups'] = []

  for (const group of letterGroups) {
    const name = normalizeLayerDisplayName(group.name ?? group.id)
    const elementIds = drawableIdsForLayer(elements, group.id)
    if (elementIds.length === 0) continue
    newGroups.push({ id: group.id, name, elementIds })
    layerMeta.set(group.id, {
      layerKind: 'real',
      layerOrigin: 'corel_layer_name',
      roleReason: 'Named Corel letter layer preserved as production geometry.',
    })
    for (const elementId of elementIds) {
      const element = elements.find((entry) => entry.elementId === elementId)
      if (element) {
        element.layerName = name
      }
    }
  }

  if (newGroups.length < 4) return null

  const logoGroups = findRealLogoGroups(doc)
  if (logoGroups.length >= 2) {
    for (const group of logoGroups) {
      const name = normalizeLayerDisplayName(group.name ?? group.id)
      const directIds = drawableIdsForLayer(elements, group.id)
      newGroups.push({ id: group.id, name, elementIds: [...directIds] })
      layerMeta.set(group.id, {
        layerKind: 'real',
        layerOrigin: 'corel_logo_layer',
        roleReason: 'Named Corel logo layer preserved as printed artwork.',
      })
    }
    assignRasterLogoLayers(doc, geometry, elements, newGroups, layerMeta, 'real')
  } else {
    assignRasterLogoLayers(doc, geometry, elements, newGroups, layerMeta, 'real')
  }

  assignStrokeOnlyLogoLayers(doc, geometry, elements, newGroups, layerMeta, 'real')

  const activeGroups = newGroups.filter((group) => group.elementIds.length > 0)
  if (activeGroups.length < 6) return null

  return {
    doc: { ...doc, groups: activeGroups, elements },
    layerMeta,
  }
}

function preserveParsedGroupsWithDrawableContent(
  doc: ParsedSvgDocument,
  elements: ParsedSvgDocument['elements'],
  layerMeta: Map<string, LayerExpansionMeta>,
): ParsedSvgDocument['groups'] {
  const preserved: ParsedSvgDocument['groups'] = []
  for (const group of doc.groups) {
    if (isCorelInternalGroupId(group.id)) continue
    const elementIds = drawableIdsForLayer(elements, group.id)
    if (elementIds.length === 0) continue
    const name = group.name ?? group.id
    preserved.push({ id: group.id, name, elementIds })
    if (isSemanticProductionOrArtworkLayerName(name)) {
      layerMeta.set(group.id, {
        layerKind: 'real',
        layerOrigin: 'corel_layer_name',
        roleReason: 'Named SVG group preserved as production or artwork layer.',
      })
    }
  }
  return preserved
}

export function expandSemanticAndPseudoLayers(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
): SemanticPseudoLayerExpansionResult {
  const elements = doc.elements.map((element) => ({ ...element }))

  const realSet = buildRealSemanticLayerSet(doc, elements, geometry)
  if (realSet) {
    return realSet
  }

  if (shouldPreserveExistingLayerStructure(doc)) {
    return { doc, layerMeta: new Map() }
  }

  const layerMeta = new Map<string, LayerExpansionMeta>()
  const newGroups: ParsedSvgDocument['groups'] = []
  const useAnaMariaFillSemantics = shouldUseAnaMariaFillSemantics(doc.fileName)

  const drawable = elements.filter((element) => isDrawableElement(element.type))
  const images = drawable.filter((element) => element.type === 'image')
  const vectors = drawable.filter((element) => element.type !== 'image')
  const vectorsWithFill = vectors.filter((element) => element.fillSolid)

  const uniqueFills = Array.from(
    new Set(vectorsWithFill.map((element) => element.fillSolid!.toLowerCase())),
  )

  assignRasterLogoLayers(doc, geometry, elements, newGroups, layerMeta, 'pseudo')

  // Capture semantic group provenance before color-cluster rewrite.
  const priorGroupByElement = new Map<string, string>()
  for (const element of elements) {
    if (element.layerId && element.type !== 'group' && element.type !== 'unknown') {
      priorGroupByElement.set(element.elementId, element.layerId)
    }
  }
  for (const group of doc.groups) {
    for (const elementId of group.elementIds) {
      if (!priorGroupByElement.has(elementId)) {
        priorGroupByElement.set(elementId, group.id)
      }
    }
  }

  for (const fill of uniqueFills) {
    const semantic = useAnaMariaFillSemantics ? letterSemanticForSolidFill(fill) : null
    const letterId = semantic?.letterId ?? `fill-${fill.replace('#', '')}`
    const id = `pseudo:${letterId}`
    const name = semantic?.pseudoDisplayName ?? `pseudo ${letterId}`
    if (!newGroups.some((group) => group.id === id)) {
      newGroups.push({ id, name, elementIds: [] })
      layerMeta.set(id, {
        layerKind: 'pseudo',
        layerOrigin: 'solid_fill_cluster',
        roleReason: 'Pseudo-layer generated from solid vector fill color cluster.',
        sourceGroupIds: [],
        elementIds: [],
      })
    }
  }

  for (const vector of vectorsWithFill) {
    const semantic = useAnaMariaFillSemantics ? letterSemanticForSolidFill(vector.fillSolid!) : null
    const letterId = semantic?.letterId ?? `fill-${vector.fillSolid!.replace('#', '')}`
    const id = `pseudo:${letterId}`
    const name = semantic?.pseudoDisplayName ?? `pseudo ${letterId}`
    const element = elements.find((entry) => entry.elementId === vector.elementId)
    if (!element) continue
    const priorGroupId = priorGroupByElement.get(vector.elementId)
    element.layerId = id
    element.layerName = name
    const group = newGroups.find((entry) => entry.id === id)
    if (group) {
      group.elementIds.push(vector.elementId)
    }
    const meta = layerMeta.get(id)
    if (meta) {
      meta.elementIds = [...(meta.elementIds ?? []), vector.elementId]
      if (priorGroupId && !isPseudoLayerId(priorGroupId) && !(meta.sourceGroupIds ?? []).includes(priorGroupId)) {
        meta.sourceGroupIds = [...(meta.sourceGroupIds ?? []), priorGroupId]
      }
    }
  }

  const logoOnlyFile = isLogoArtworkLayerName(doc.fileName)
  const semanticGroups = doc.groups.filter((group) => {
    if (logoOnlyFile) return false
    const name = group.name ?? group.id
    return isSemanticProductionOrArtworkLayerName(name) && !isCorelInternalGroupId(group.id)
  })

  if (uniqueFills.length <= 1 && semanticGroups.length > 0) {
    for (const group of semanticGroups) {
      const name = group.name ?? group.id
      const elementIds = drawableIdsForLayer(elements, group.id)
      if (elementIds.length === 0) continue
      newGroups.push({ id: group.id, name, elementIds })
      layerMeta.set(group.id, {
        layerKind: 'real',
        layerOrigin: 'corel_layer_name',
        roleReason: 'Named Corel layer preserved as production layer.',
      })
    }
  }

  const onlyGenericRoots =
    doc.groups.length > 0 &&
    doc.groups.every((group) => {
      const name = group.name ?? group.id
      return isGenericLayerName(name) || isCorelInternalGroupId(group.id)
    })

  if (
    onlyGenericRoots &&
    vectorsWithFill.length > 0 &&
    uniqueFills.length === 1 &&
    newGroups.length === 0
  ) {
    const id = 'pseudo:single_solid'
    const name = 'Pseudo solid vectors'
    newGroups.push({
      id,
      name,
      elementIds: vectorsWithFill.map((element) => element.elementId),
    })
    layerMeta.set(id, {
      layerKind: 'pseudo',
      layerOrigin: 'generic_layer_promotion',
      roleReason: 'Generic Corel layer promoted to pseudo production layer.',
    })
    for (const vector of vectorsWithFill) {
      const element = elements.find((entry) => entry.elementId === vector.elementId)
      if (element) {
        element.layerId = id
        element.layerName = name
      }
    }
  }

  if (images.length > 0 && newGroups.filter((g) => isLogoLayerId(g.id)).length === 0) {
    assignRasterLogoLayers(doc, geometry, elements, newGroups, layerMeta, 'pseudo')
  }

  assignStrokeOnlyLogoLayers(doc, geometry, elements, newGroups, layerMeta, 'pseudo')

  let activeGroups = newGroups.filter((group) => group.elementIds.length > 0)
  if (activeGroups.length === 0) {
    activeGroups = preserveParsedGroupsWithDrawableContent(doc, elements, layerMeta)
  }

  return {
    doc: {
      ...doc,
      groups: activeGroups,
      elements,
    },
    layerMeta,
  }
}
