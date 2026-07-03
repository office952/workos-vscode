import type { BoundingBox, ElementGeometry, GeometrySummary, ParsedSvgDocument, ParsedSvgElement } from './types'

export const RASTER_ARTWORK_MIN_OVERLAP_RATIO = 0.01

export type RasterArtworkRole = 'face_artwork' | 'vinyl_overlay' | 'print_overlay'

export interface RasterVectorBinding {
  artworkId: string
  imageElementId: string
  imageHref: string | null
  externalImageDetected: boolean
  missingExternalImageAsset: boolean
  imageBounds: BoundingBox | null
  overlappedVectorIds: string[]
  overlappedLayerNames: string[]
  artworkRole: RasterArtworkRole
  artworkAreaEstimateM2: number | null
  artworkAreaSource: 'covered_vector_area_estimate' | 'none'
  areaConfidence: 'high' | 'medium' | 'low' | 'estimated'
  warnings: string[]
}

function bboxOverlapRatio(a: BoundingBox, b: BoundingBox): number {
  const x0 = Math.max(a.x, b.x)
  const y0 = Math.max(a.y, b.y)
  const x1 = Math.min(a.x + a.width, b.x + b.width)
  const y1 = Math.min(a.y + a.height, b.y + b.height)
  if (x1 <= x0 || y1 <= y0) return 0
  const inter = (x1 - x0) * (y1 - y0)
  const minArea = Math.min(a.width * a.height, b.width * b.height)
  if (minArea <= 0) return 0
  return inter / minArea
}

function imageHref(el: ParsedSvgElement): string | null {
  const href = el.attributes.href ?? el.attributes['xlink:href'] ?? null
  return href?.trim() || null
}

function isExternalImageHref(href: string | null): boolean {
  if (!href) return false
  const lower = href.trim().toLowerCase()
  return !lower.startsWith('data:') && !lower.startsWith('#')
}

function isProductionVectorElement(el: ParsedSvgElement, geo: ElementGeometry | undefined): boolean {
  if (!geo?.bbox || geo.bbox.width <= 0 || geo.bbox.height <= 0) return false
  if (el.type === 'image' || el.type === 'text' || el.type === 'line' || el.type === 'polyline') {
    return false
  }
  if (geo.isClosed === false) return false
  return el.type === 'path' || el.type === 'rect' || el.type === 'circle' || el.type === 'ellipse' || el.type === 'polygon'
}

function vectorAreaM2(el: ParsedSvgElement, geo: ElementGeometry, mmPerVbu: number): number {
  if (geo.areaMm2 != null && geo.areaMm2 > 0) {
    return geo.areaMm2 / 1_000_000
  }
  if (!geo.bbox) return 0
  const wMm = geo.bbox.width * mmPerVbu
  const hMm = geo.bbox.height * mmPerVbu
  return (wMm * hMm) / 1_000_000
}

function inferArtworkRole(el: ParsedSvgElement): RasterArtworkRole {
  if (el.type === 'image') return 'print_overlay'
  return 'face_artwork'
}

export function detectRasterOverVectorBindings(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
): RasterVectorBinding[] {
  const geoById = new Map(geometry.elementGeometries.map((g) => [g.elementId, g]))
  const mmPerVbu = geometry.mmPerVbu
  const images = doc.elements.filter((el) => el.type === 'image')
  const vectorCandidates = doc.elements
    .filter((el) => el.type !== 'group' && el.type !== 'unknown' && el.type !== 'image')
    .map((el) => ({ el, geo: geoById.get(el.elementId) }))
    .filter((row) => isProductionVectorElement(row.el, row.geo))

  const bindings: RasterVectorBinding[] = []

  for (const imageEl of images) {
    const imageGeo = geoById.get(imageEl.elementId)
    const imageBounds = imageGeo?.bbox ?? null
    const href = imageHref(imageEl)
    const external = isExternalImageHref(href)
    const warnings: string[] = []
    if (external) {
      warnings.push('external_image_detected')
      warnings.push('missing_external_image_asset')
    }

    const overlapped: Array<{ el: ParsedSvgElement; geo: ElementGeometry }> = []
    if (imageBounds) {
      for (const candidate of vectorCandidates) {
        if (!candidate.geo?.bbox) continue
        const ratio = bboxOverlapRatio(imageBounds, candidate.geo.bbox)
        if (ratio >= RASTER_ARTWORK_MIN_OVERLAP_RATIO) {
          overlapped.push({ el: candidate.el, geo: candidate.geo })
        }
      }
    }

    let artworkAreaEstimateM2: number | null = null
    let artworkAreaSource: RasterVectorBinding['artworkAreaSource'] = 'none'
    let areaConfidence: RasterVectorBinding['areaConfidence'] = 'low'

    if (overlapped.length > 0) {
      artworkAreaEstimateM2 = overlapped.reduce((sum, row) => sum + vectorAreaM2(row.el, row.geo, mmPerVbu), 0)
      artworkAreaEstimateM2 = Math.round(artworkAreaEstimateM2 * 10000) / 10000
      artworkAreaSource = 'covered_vector_area_estimate'
      areaConfidence = overlapped.every((row) => row.geo.areaMm2 != null && !row.geo.estimated)
        ? 'high'
        : 'estimated'
      warnings.push('raster_artwork_area_approximated_by_covered_vector_geometry')
    } else if (imageBounds) {
      warnings.push('raster_image_not_attached_to_production_geometry')
    }

    bindings.push({
      artworkId: `raster:${imageEl.elementId}`,
      imageElementId: imageEl.elementId,
      imageHref: href,
      externalImageDetected: external,
      missingExternalImageAsset: external,
      imageBounds,
      overlappedVectorIds: overlapped.map((row) => row.el.elementId),
      overlappedLayerNames: Array.from(
        new Set(overlapped.map((row) => row.el.layerName).filter((name): name is string => !!name)),
      ),
      artworkRole: inferArtworkRole(imageEl),
      artworkAreaEstimateM2,
      artworkAreaSource,
      areaConfidence,
      warnings,
    })
  }

  return bindings
}
