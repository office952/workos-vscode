import type { SvgPartExtractionReport, SvgPartWarning } from './partTypes'

export function buildPartsReport(
  items: SvgPartExtractionReport['items'],
  warnings: SvgPartWarning[],
  strategy: SvgPartExtractionReport['strategy'],
  extractionMode: SvgPartExtractionReport['extractionMode'],
  splitDiagnostics: SvgPartExtractionReport['splitDiagnostics'],
): SvgPartExtractionReport {
  const totalBoundingAreaSqm = items.reduce((acc, item) => acc + (item.bounds.boundingAreaSqm ?? 0), 0)
  const totalPerimeterMm = items.reduce((acc, item) => acc + (item.geometry.totalContourPerimeterMm ?? item.geometry.perimeterMm ?? 0), 0)
  const nestableCount = items.filter((item) => item.canNest).length

  return {
    strategy,
    fallbackStrategy: 'layer-as-part',
    extractionMode,
    count: items.length,
    nestableCount,
    totalBoundingAreaSqm,
    totalPerimeterMm,
    totalPerimeterMl: totalPerimeterMm / 1000,
    items,
    warnings,
    splitDiagnostics,
  }
}
