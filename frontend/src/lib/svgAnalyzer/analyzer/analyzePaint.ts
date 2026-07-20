import type { LayerPaintEvidence, LayerPaintKind } from './layerRoleTypes'
import type { ParsedSvgElement } from './types'

function uniqueSolidColors(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((v): v is string => !!v && !v.startsWith('url('))))
}

export function buildLayerPaintEvidence(layerId: string, elements: ParsedSvgElement[]): LayerPaintEvidence {
  const layerElements = elements.filter((element) => element.layerId === layerId && element.type !== 'group')

  const fills = uniqueSolidColors(layerElements.map((element) => element.fillSolid))
  const strokes = uniqueSolidColors(layerElements.map((element) => element.strokeSolid))

  const gradientRefs = Array.from(
    new Set(
      layerElements.flatMap((element) => {
        const refs: string[] = []
        if (element.fillPaint === 'gradient' && element.fillRef) refs.push(element.fillRef)
        if (element.strokePaint === 'gradient' && element.strokeRef) refs.push(element.strokeRef)
        return refs
      }),
    ),
  )

  const hasGradient = layerElements.some((element) => element.fillPaint === 'gradient' || element.strokePaint === 'gradient')
  const hasPattern = layerElements.some((element) => element.fillPaint === 'pattern' || element.strokePaint === 'pattern')
  const hasImage = layerElements.some((element) => element.type === 'image')
  const textElementCount = layerElements.filter((element) => element.type === 'text').length

  // Real policromie = multiple fills, gradient/pattern/image — NOT fill+stroke technical contour.
  // ACM panels often use one solid fill + a darker stroke; that must stay "solid".
  const distinctFills = fills.length
  const isRealPolychrome =
    hasGradient ||
    hasPattern ||
    hasImage ||
    distinctFills >= 2 ||
    (distinctFills >= 1 && fills.some((fill) => fill.startsWith('url(')))

  let paintKind: LayerPaintKind = 'none'
  if (isRealPolychrome) {
    paintKind = 'policromie'
  } else if (fills.length === 1 || (fills.length === 0 && strokes.length === 1)) {
    paintKind = 'solid'
  } else if (fills.length === 0 && strokes.length === 0 && layerElements.length > 0) {
    paintKind = 'mixed'
  } else if (fills.length === 1 && strokes.length >= 1) {
    paintKind = 'solid'
  } else if (layerElements.length > 0) {
    paintKind = 'mixed'
  }

  return {
    fills,
    strokes,
    gradientRefs,
    hasGradient,
    hasPattern,
    hasImage,
    isMulticolor: isRealPolychrome,
    fillCount: fills.length,
    textElementCount,
    paintKind,
  }
}
