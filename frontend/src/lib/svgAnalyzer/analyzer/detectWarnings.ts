import type { ColorAnalysis, GeometrySummary, LayerAnalysis, ParsedSvgDocument } from './types'

export function detectWarnings(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
  layers: LayerAnalysis[],
  colors: ColorAnalysis,
): string[] {
  const warnings: string[] = []

  if (!doc.viewBox) {
    warnings.push('SVG has no viewBox.')
  }

  if (!doc.width || !doc.height) {
    warnings.push('SVG has no explicit physical width/height.')
  }

  if (doc.conversionToMm.confidence !== 'high') {
    warnings.push('Unit conversion is estimated. SVG appears pixel-based or ambiguous.')
  }

  // Non-uniform scale: scaleX ≠ scaleY (viewBox to physical mm)
  if (geometry.scaleX != null && geometry.scaleY != null && geometry.uniformScale === false) {
    warnings.push(
      `NON_UNIFORM_SCALE: scaleX=${geometry.scaleX.toFixed(4)} scaleY=${geometry.scaleY.toFixed(4)}. Perimeter metrics may be inaccurate.`,
    )
  }

  if (doc.layerNameDuplicates.length > 0) {
    warnings.push(`Duplicate layer names detected: ${doc.layerNameDuplicates.join(', ')}`)
  }

  if (layers.some((l) => l.elementCount === 0)) {
    warnings.push('At least one layer is empty.')
  }

  if (geometry.openPathCount > 0) {
    warnings.push(`Open paths detected: ${geometry.openPathCount}`)
  }

  if (geometry.outsideViewBoxCount > 0) {
    warnings.push(`Elements outside viewBox detected: ${geometry.outsideViewBoxCount}`)
  }

  if (geometry.tinyElementCount > 0) {
    warnings.push(`Very small elements detected: ${geometry.tinyElementCount}`)
  }

  if (doc.elements.some((e) => e.type === 'text')) {
    warnings.push('Text elements found. Consider converting text to curves for production stability.')
  }

  if (doc.elements.some((e) => e.type === 'image')) {
    warnings.push('Raster image embedded inside SVG.')
  }

  if (colors.unique.length === 0) {
    warnings.push('No fill/stroke colors detected.')
  }

  const withoutPaint = geometry.elementGeometries.filter((g) => g.warnings.some((w) => w.includes('no fill and no stroke')))
  if (withoutPaint.length > 0) {
    warnings.push(`Elements without fill and stroke: ${withoutPaint.length}`)
  }

  if ((doc.width?.value ?? 0) > 3000 && doc.width?.unit === 'px' && doc.conversionToMm.confidence !== 'high') {
    warnings.push('Large pixel dimensions detected; physical size may be interpreted incorrectly.')
  }

  if (doc.width?.unit && doc.height?.unit && doc.width.unit !== doc.height.unit) {
    warnings.push('Mixed units detected between width and height.')
  }

  if (doc.elements.some((e) => !!e.transform)) {
    warnings.push('Transforms detected. Some metrics may be estimated.')
  }

  // Area diagnostics
  if (geometry.totalAreaMm2 == null && (doc.width || doc.height)) {
    warnings.push(
      'FILLED_AREA_NOT_AVAILABLE: Element types present (e.g. <path>) do not support geometric area calculation. Use boundingAreaSqm as reference.',
    )
  }

  const factor = doc.conversionToMm.factor
  const widthMm = doc.width && factor != null ? doc.width.value * factor : null
  const heightMm = doc.height && factor != null ? doc.height.value * factor : null
  if (geometry.totalAreaMm2 === 0 && widthMm && heightMm && widthMm * heightMm > 0) {
    warnings.push('AREA_ZERO_BUT_BOUNDS_EXIST: Computed filled area is 0 but document has non-zero dimensions.')
  }

  if (layers.some((layer) => layer.filledAreaSqm === 0 && (layer.widthMm ?? 0) > 0 && (layer.heightMm ?? 0) > 0)) {
    warnings.push('AREA_ZERO_BUT_BOUNDS_EXIST: At least one layer has zero filled area but non-zero bounds.')
  }

  return warnings
}
