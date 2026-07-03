import type { LayerAnalysis, ParsedSvgDocument } from './types'
import type { RasterVectorBinding } from './rasterOverVectorArtwork'
import { detectRasterOverVectorBindings } from './rasterOverVectorArtwork'
import type { GeometrySummary } from './types'

export type ArtworkRecommendedApplication = 'vinyl_cut' | 'print_on_vinyl_laminated' | 'manual_review'

export interface ArtworkComplexityAssessment {
  artwork_id: string
  source_element_type: 'image' | 'vector' | 'mixed'
  source_layer_name: string | null
  bounds: { x: number; y: number; width: number; height: number } | null
  overlapped_vector_ids: string[]
  dominant_color_count: number
  has_gradient: boolean
  has_raster_image: boolean
  has_external_image: boolean
  has_clip_path: boolean
  has_mask: boolean
  has_transparency: boolean
  has_many_colors: boolean
  recommended_application: ArtworkRecommendedApplication
  recommendation_reason: string
  artwork_area_estimate_m2: number | null
  artwork_area_source: string | null
  confidence: 'high' | 'medium' | 'low' | 'estimated'
  warnings: string[]
  artwork_role: 'face_artwork' | 'vinyl_overlay' | 'print_overlay' | null
  image_href: string | null
  external_image_detected: boolean
  missing_external_image_asset: boolean
}

export interface ArtworkComplexityReport {
  assessments: ArtworkComplexityAssessment[]
  has_raster_over_vector: boolean
  default_recommended_application: ArtworkRecommendedApplication | null
}

function decideApplication(args: {
  hasRaster: boolean
  hasExternalImage: boolean
  hasGradient: boolean
  hasClipPath: boolean
  hasMask: boolean
  dominantColorCount: number
  paintKind: string
  overlappedVectorCount: number
}): { application: ArtworkRecommendedApplication; reason: string } {
  if (args.hasRaster || args.hasExternalImage) {
    if (args.overlappedVectorCount === 0) {
      return {
        application: 'manual_review',
        reason: 'Raster or external image not overlapping production geometry — manual review required.',
      }
    }
    return {
      application: 'print_on_vinyl_laminated',
      reason: 'Raster or external image over production geometry — recommend print on vinyl + lamination.',
    }
  }
  if (args.hasGradient || args.hasClipPath || args.hasMask) {
    return {
      application: 'print_on_vinyl_laminated',
      reason: 'Gradient, clip path, or mask detected — recommend print + lamination.',
    }
  }
  if (args.dominantColorCount > 3) {
    return {
      application: 'print_on_vinyl_laminated',
      reason: 'More than three dominant colors — recommend print + lamination.',
    }
  }
  if (args.overlappedVectorCount === 0 && args.hasRaster) {
    return {
      application: 'manual_review',
      reason: 'Raster not overlapping production geometry — manual review required.',
    }
  }
  if (args.dominantColorCount >= 1 && args.dominantColorCount <= 3 && (args.paintKind === 'solid' || args.paintKind === 'policromie')) {
    return {
      application: 'vinyl_cut',
      reason: 'Up to three flat colors — cut vinyl (Oracal) may be suitable.',
    }
  }
  return {
    application: 'manual_review',
    reason: 'Artwork complexity unclear — operator review required.',
  }
}

function assessmentFromRasterBinding(
  binding: RasterVectorBinding,
  layer: LayerAnalysis | undefined,
  doc: ParsedSvgDocument,
): ArtworkComplexityAssessment {
  const dominantColorCount = layer?.paintEvidence?.fillCount ?? layer?.colors?.length ?? 0
  const hasGradient = layer?.paintEvidence?.hasGradient ?? false
  const paintKind = layer?.paintEvidence?.paintKind ?? 'none'
  const hasClipPath = docHasClipPath(doc)
  const hasMask = docHasMask(doc)

  const { application, reason } = decideApplication({
    hasRaster: true,
    hasExternalImage: binding.externalImageDetected,
    hasGradient,
    hasClipPath,
    hasMask,
    dominantColorCount,
    paintKind,
    overlappedVectorCount: binding.overlappedVectorIds.length,
  })

  const warnings = [...binding.warnings]
  if (binding.overlappedVectorIds.length === 0) {
    warnings.push('raster_image_not_attached_to_production_geometry')
  }

  return {
    artwork_id: binding.artworkId,
    source_element_type: 'image',
    source_layer_name: binding.overlappedLayerNames[0] ?? layer?.name ?? null,
    bounds: binding.imageBounds
      ? {
          x: binding.imageBounds.x,
          y: binding.imageBounds.y,
          width: binding.imageBounds.width,
          height: binding.imageBounds.height,
        }
      : null,
    overlapped_vector_ids: binding.overlappedVectorIds,
    dominant_color_count: dominantColorCount,
    has_gradient: hasGradient,
    has_raster_image: true,
    has_external_image: binding.externalImageDetected,
    has_clip_path: hasClipPath,
    has_mask: hasMask,
    has_transparency: binding.externalImageDetected,
    has_many_colors: dominantColorCount > 3 || paintKind === 'policromie',
    recommended_application: application,
    recommendation_reason: reason,
    artwork_area_estimate_m2: binding.artworkAreaEstimateM2,
    artwork_area_source: binding.artworkAreaSource === 'none' ? null : binding.artworkAreaSource,
    confidence: binding.areaConfidence,
    warnings,
    artwork_role: binding.artworkRole,
    image_href: binding.imageHref,
    external_image_detected: binding.externalImageDetected,
    missing_external_image_asset: binding.missingExternalImageAsset,
  }
}

function assessmentFromLayer(layer: LayerAnalysis, doc: ParsedSvgDocument): ArtworkComplexityAssessment | null {
  if (layer.paintEvidence?.hasImage) return null

  const dominantColorCount = layer.paintEvidence?.fillCount ?? layer.colors?.length ?? 0
  const hasGradient = layer.paintEvidence?.hasGradient ?? false
  const paintKind = layer.paintEvidence?.paintKind ?? 'none'
  const hasClipPath = docHasClipPath(doc)
  const hasMask = docHasMask(doc)

  const { application, reason } = decideApplication({
    hasRaster: layer.paintEvidence?.hasImage ?? false,
    hasExternalImage: false,
    hasGradient,
    hasClipPath,
    hasMask,
    dominantColorCount,
    paintKind,
    overlappedVectorCount: layer.pathElementCount > 0 ? 1 : 0,
  })

  if (application === 'manual_review' && paintKind === 'none' && dominantColorCount === 0) {
    return null
  }

  return {
    artwork_id: `layer:${layer.id}`,
    source_element_type: 'vector',
    source_layer_name: layer.name,
    bounds: null,
    overlapped_vector_ids: [],
    dominant_color_count: dominantColorCount,
    has_gradient: hasGradient,
    has_raster_image: false,
    has_external_image: false,
    has_clip_path: hasClipPath,
    has_mask: hasMask,
    has_transparency: layer.paintEvidence?.hasPattern ?? false,
    has_many_colors: dominantColorCount > 3 || paintKind === 'policromie',
    recommended_application: application,
    recommendation_reason: reason,
    artwork_area_estimate_m2: layer.filledAreaSqm ?? layer.boundingAreaSqm ?? null,
    artwork_area_source: layer.filledAreaSqm != null ? 'layer_filled_area' : 'layer_bounding_area',
    confidence: layer.areaConfidence,
    warnings: [],
    artwork_role: null,
    image_href: null,
    external_image_detected: false,
    missing_external_image_asset: false,
  }
}

function docHasClipPath(doc: ParsedSvgDocument): boolean {
  return /clip-path|clipPath/i.test(doc.source)
}

function docHasMask(doc: ParsedSvgDocument): boolean {
  return /<mask[\s>]/i.test(doc.source)
}

export function buildArtworkComplexityReport(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
  layers: LayerAnalysis[],
): ArtworkComplexityReport {
  const rasterBindings = detectRasterOverVectorBindings(doc, geometry)
  const layerByName = new Map(layers.map((l) => [l.name, l]))

  const assessments: ArtworkComplexityAssessment[] = []

  for (const binding of rasterBindings) {
    const layerName = binding.overlappedLayerNames[0]
    const layer = layerName ? layerByName.get(layerName) : undefined
    assessments.push(assessmentFromRasterBinding(binding, layer, doc))
  }

  for (const layer of layers) {
    if (layer.paintEvidence?.hasImage) continue
    if (
      layer.paintEvidence?.paintKind === 'policromie' ||
      (layer.paintEvidence?.fillCount ?? 0) > 3 ||
      layer.paintEvidence?.hasGradient
    ) {
      const row = assessmentFromLayer(layer, doc)
      if (row) assessments.push(row)
    }
  }

  const defaultRecommended = pickDefaultRecommendation(assessments)

  return {
    assessments,
    has_raster_over_vector: rasterBindings.some((b) => b.overlappedVectorIds.length > 0),
    default_recommended_application: defaultRecommended,
  }
}

function pickDefaultRecommendation(
  assessments: ArtworkComplexityAssessment[],
): ArtworkRecommendedApplication | null {
  if (!assessments.length) return null
  if (assessments.some((a) => a.recommended_application === 'print_on_vinyl_laminated')) {
    return 'print_on_vinyl_laminated'
  }
  if (assessments.every((a) => a.recommended_application === 'vinyl_cut')) {
    return 'vinyl_cut'
  }
  return 'manual_review'
}
