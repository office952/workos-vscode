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

  const colorTokens = new Set([...fills, ...strokes])
  const isMulticolor = colorTokens.size >= 2 || hasGradient || hasPattern || hasImage

  let paintKind: LayerPaintKind = 'none'
  if (hasGradient || hasPattern || hasImage || (isMulticolor && colorTokens.size >= 2)) {
    paintKind = 'policromie'
  } else if (fills.length === 1 || strokes.length === 1) {
    paintKind = 'solid'
  } else if (colorTokens.size === 1) {
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
    isMulticolor,
    fillCount: colorTokens.size,
    textElementCount,
    paintKind,
  }
}
