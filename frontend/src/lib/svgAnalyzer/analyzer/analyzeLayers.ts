import { buildLayerPaintEvidence } from './analyzePaint'
import { guessLayerAutoRole } from './guessLayerAutoRole'
import { isPseudoLayerId } from './layerNameSemantics'
import type { LayerExpansionMeta } from './semanticAndPseudoLayerExpansion'
import type { ColorAnalysis, GeometrySummary, LayerAnalysis, ParsedSvgDocument } from './types'

function countElementTypes(doc: ParsedSvgDocument, layerId: string) {
  const layerElements = doc.elements.filter((element) => element.layerId === layerId && element.type !== 'group')
  return {
    pathCount: layerElements.filter((element) => element.type === 'path').length,
    rectCount: layerElements.filter((element) => element.type === 'rect').length,
    polygonCount: layerElements.filter((element) => element.type === 'polygon' || element.type === 'polyline').length,
  }
}

function buildLayerRoleFields(
  layerId: string,
  layerName: string,
  doc: ParsedSvgDocument,
  subPathCount: number,
): Pick<LayerAnalysis, 'autoRole' | 'autoConfidence' | 'autoRoleCandidates' | 'paintEvidence' | 'productionHint' | 'roleGuess'> {
  const paintEvidence = buildLayerPaintEvidence(layerId, doc.elements)
  const counts = countElementTypes(doc, layerId)
  const role = guessLayerAutoRole(layerName, paintEvidence, {
    ...counts,
    subPathCount,
  }, layerId)

  return {
    autoRole: role.autoRole,
    autoConfidence: role.autoConfidence,
    autoRoleCandidates: role.autoRoleCandidates,
    paintEvidence,
    productionHint: role.productionHint,
    roleGuess: role.autoRole,
  }
}

function layerWarnings(
  layerName: string,
  paintEvidence: LayerAnalysis['paintEvidence'],
  elementCount: number,
  layerKind?: LayerAnalysis['layerKind'],
  layerOrigin?: string | null,
): string[] {
  const warnings: string[] = []
  if (elementCount === 0) {
    warnings.push('Layer has no drawable elements.')
  }
  if (layerOrigin === 'stroke_vector_outline' || layerOrigin === 'corel_logo_stroke_outline') {
    warnings.push('STROKE_ONLY_VECTOR_LAYER: Stroke-only vector isolated as logo/artwork candidate - confirm what it represents and how it goes to production.')
  } else if (layerKind === 'pseudo') {
    warnings.push(
      'PSEUDO_LAYER_SOLID_FILL: Pseudo-layer generated from solid vector fills — confirm physical role (letter face vs Contur suport); proposal is not confirmation.',
    )
  }
  if (layerKind === 'raster_artwork') {
    warnings.push('RASTER_ARTWORK_LAYER: Raster image isolated — confirm printed artwork role.')
  }
  if (paintEvidence.textElementCount > 0) {
    warnings.push('TEXT_NOT_CONVERTED_TO_PATHS: Layer contains <text> elements — convert to paths for reliable part extraction.')
  }
  if (paintEvidence.paintKind === 'policromie' && layerKind !== 'pseudo') {
    warnings.push('GRADIENT_OR_POLICROMIE_PRINT_VINYL: Layer uses gradient/policromie — entire zone prints on vinyl as one piece.')
  }
  if (layerName.toLowerCase().includes('publi') && paintEvidence.paintKind === 'solid') {
    // no misleading print role on solid letter layers
  }
  return warnings
}

function activeLayerGroups(doc: ParsedSvgDocument): ParsedSvgDocument['groups'] {
  return doc.groups.filter((group) =>
    doc.elements.some(
      (element) =>
        element.layerId === group.id &&
        element.type !== 'group' &&
        element.type !== 'unknown',
    ),
  )
}

function layersFromElementLayerAssignments(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
  colors: ColorAnalysis,
  layerMeta: Map<string, LayerExpansionMeta> | undefined,
  mmPerVbu: number,
  byElementId: Map<string, GeometrySummary['elementGeometries'][number]>,
): LayerAnalysis[] {
  const assignments = new Map<string, string>()
  for (const element of doc.elements) {
    if (element.type === 'group' || element.type === 'unknown' || element.type === 'image') continue
    if (!element.layerId) continue
    const name = element.layerName ?? element.layerId
    if (!name || name === 'unassigned') continue
    assignments.set(element.layerId, name)
  }

  return Array.from(assignments.entries()).map(([layerId, layerName]) => {
    const layerElements = doc.elements.filter(
      (element) => element.layerId === layerId && element.type !== 'group',
    )
    const layerPathElements = layerElements.filter((element) => element.type === 'path')
    const geos = layerElements.map((element) => byElementId.get(element.elementId)).filter(Boolean)
    const bboxWidth = Math.max(0, ...geos.map((geo) => geo?.bbox?.width ?? 0))
    const bboxHeight = Math.max(0, ...geos.map((geo) => geo?.bbox?.height ?? 0))
    const widthMm = bboxWidth * mmPerVbu
    const heightMm = bboxHeight * mmPerVbu
    const filledAreaMm2 = geos.reduce<number | null>((acc, geo) => {
      if (geo?.areaMm2 == null) return acc
      return (acc ?? 0) + geo.areaMm2
    }, null)
    const perimeterMm = geos.reduce((acc, geo) => acc + (geo?.perimeterMm ?? 0), 0)
    const subPathCount = layerElements
      .map((element) => byElementId.get(element.elementId)?.subPathCount ?? 0)
      .reduce((acc, value) => acc + value, 0)
    const roleFields = buildLayerRoleFields(layerId, layerName, doc, subPathCount)
    const expansion = layerMeta?.get(layerId)

    return {
      id: layerId,
      name: layerName,
      layerKind: expansion?.layerKind,
      layerOrigin: expansion?.layerOrigin ?? null,
      roleReason: expansion?.roleReason ?? roleFields.autoRoleCandidates[0]?.reason ?? null,
      sourceGroupIds: expansion?.sourceGroupIds ?? [],
      elementIds: expansion?.elementIds ?? layerElements.map((element) => element.elementId),
      ...roleFields,
      elementCount: layerElements.length,
      pathElementCount: layerPathElements.length,
      subPathCount,
      closedSubPathCount: layerElements
        .map((element) => byElementId.get(element.elementId)?.closedSubPathCount ?? 0)
        .reduce((acc, value) => acc + value, 0),
      openSubPathCount: layerElements
        .map((element) => byElementId.get(element.elementId)?.openSubPathCount ?? 0)
        .reduce((acc, value) => acc + value, 0),
      widthMm,
      heightMm,
      boundingAreaSqm: widthMm > 0 && heightMm > 0 ? (widthMm * heightMm) / 1_000_000 : null,
      filledAreaSqm: filledAreaMm2 == null ? null : filledAreaMm2 / 1_000_000,
      areaConfidence: filledAreaMm2 == null ? 'low' : geos.some((geo) => geo?.estimated) ? 'medium' : 'high',
      perimeterMm,
      perimeterMl: perimeterMm / 1000,
      colors: colors.byLayer[layerName] ?? colors.byLayer[layerId] ?? [],
      warnings: layerWarnings(
        layerName,
        roleFields.paintEvidence,
        layerElements.length,
        expansion?.layerKind,
        expansion?.layerOrigin,
      ),
    }
  })
}

export function analyzeLayers(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
  colors: ColorAnalysis,
  layerMeta?: Map<string, LayerExpansionMeta>,
): LayerAnalysis[] {
  const byElementId = new Map(geometry.elementGeometries.map((g) => [g.elementId, g]))
  const mmPerVbu = geometry.mmPerVbu

  if (!doc.groups.length) {
    const fromAssignments = layersFromElementLayerAssignments(
      doc,
      geometry,
      colors,
      layerMeta,
      mmPerVbu,
      byElementId,
    )
    if (fromAssignments.length > 0) {
      return fromAssignments
    }

    const all = doc.elements.filter((e) => e.type !== 'group' && e.type !== 'unknown' && e.type !== 'image')
    const pathElements = all.filter((e) => e.type === 'path')
    const geos = all.map((e) => byElementId.get(e.elementId)).filter((v) => !!v)
    const maxW = Math.max(0, ...geos.map((g) => g?.bbox?.width ?? 0))
    const maxH = Math.max(0, ...geos.map((g) => g?.bbox?.height ?? 0))
    const widthMm = maxW * mmPerVbu
    const heightMm = maxH * mmPerVbu
    const filledAreaMm2 = geos.reduce<number | null>((acc, g) => {
      if (g?.areaMm2 == null) return acc
      return (acc ?? 0) + g.areaMm2
    }, null)
    const perimeterMm = geos.reduce((acc, g) => acc + (g?.perimeterMm ?? 0), 0)
    const roleFields = buildLayerRoleFields('unassigned', 'unassigned', doc, geometry.subPathCount)

    return [
      {
        id: 'unassigned',
        name: 'unassigned',
        ...roleFields,
        elementCount: all.length,
        pathElementCount: pathElements.length,
        subPathCount: geometry.subPathCount,
        closedSubPathCount: geometry.closedSubPathCount,
        openSubPathCount: geometry.openSubPathCount,
        widthMm,
        heightMm,
        boundingAreaSqm: widthMm > 0 && heightMm > 0 ? (widthMm * heightMm) / 1_000_000 : null,
        filledAreaSqm: filledAreaMm2 == null ? null : filledAreaMm2 / 1_000_000,
        areaConfidence: filledAreaMm2 == null ? 'low' : geos.some((g) => g?.estimated) ? 'medium' : 'high',
        perimeterMm,
        perimeterMl: perimeterMm / 1000,
        colors: colors.byLayer.unassigned ?? [],
        warnings: layerWarnings('unassigned', roleFields.paintEvidence, all.length),
      },
    ]
  }

  return activeLayerGroups(doc).map((group) => {
    const layerElements = doc.elements.filter(
      (e) => e.layerId === group.id && e.type !== 'group',
    )
    const layerPathElements = layerElements.filter((e) => e.type === 'path')
    const geos = layerElements.map((e) => byElementId.get(e.elementId)).filter((v) => !!v)
    const bboxWidth = Math.max(0, ...geos.map((g) => g?.bbox?.width ?? 0))
    const bboxHeight = Math.max(0, ...geos.map((g) => g?.bbox?.height ?? 0))
    const widthMm = bboxWidth * mmPerVbu
    const heightMm = bboxHeight * mmPerVbu
    const filledAreaMm2 = geos.reduce<number | null>((acc, g) => {
      if (g?.areaMm2 == null) return acc
      return (acc ?? 0) + g.areaMm2
    }, null)
    const perimeterMm = geos.reduce((acc, g) => acc + (g?.perimeterMm ?? 0), 0)
    const layerName = group.name ?? group.id
    const subPathCount = layerElements
      .map((e) => byElementId.get(e.elementId)?.subPathCount ?? 0)
      .reduce((acc, value) => acc + value, 0)
    const roleFields = buildLayerRoleFields(group.id, layerName, doc, subPathCount)
    const expansion = layerMeta?.get(group.id)

    return {
      id: group.id,
      name: layerName,
      layerKind: expansion?.layerKind,
      layerOrigin: expansion?.layerOrigin ?? null,
      roleReason: expansion?.roleReason ?? roleFields.autoRoleCandidates[0]?.reason ?? null,
      sourceGroupIds: expansion?.sourceGroupIds ?? (isPseudoLayerId(group.id) ? [] : [group.id]),
      elementIds: expansion?.elementIds ?? layerElements.map((e) => e.elementId),
      ...roleFields,
      elementCount: layerElements.length,
      pathElementCount: layerPathElements.length,
      subPathCount,
      closedSubPathCount: layerElements
        .map((e) => byElementId.get(e.elementId)?.closedSubPathCount ?? 0)
        .reduce((acc, value) => acc + value, 0),
      openSubPathCount: layerElements
        .map((e) => byElementId.get(e.elementId)?.openSubPathCount ?? 0)
        .reduce((acc, value) => acc + value, 0),
      widthMm,
      heightMm,
      boundingAreaSqm: widthMm > 0 && heightMm > 0 ? (widthMm * heightMm) / 1_000_000 : null,
      filledAreaSqm: filledAreaMm2 == null ? null : filledAreaMm2 / 1_000_000,
      areaConfidence: filledAreaMm2 == null ? 'low' : geos.some((g) => g?.estimated) ? 'medium' : 'high',
      perimeterMm,
      perimeterMl: perimeterMm / 1000,
      colors: colors.byLayer[group.name ?? group.id] ?? colors.byLayer[group.id] ?? [],
      warnings: layerWarnings(
        layerName,
        roleFields.paintEvidence,
        layerElements.length,
        expansion?.layerKind,
        expansion?.layerOrigin,
      ),
    }
  })
}
