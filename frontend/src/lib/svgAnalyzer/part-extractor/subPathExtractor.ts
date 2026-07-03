import type { ParsedSvgDocument, ParsedSvgElement } from '../analyzer/types'
import type { ConfidenceLevel } from '../analyzer/types'
import type { SvgPartWarning } from './partTypes'
import { partSplitWarning } from './partSplittingWarnings'
import { measurePathShape, isDegenerateBbox } from './shapeBounds'

export interface ExtractedSubPath {
  id: string
  subPathIndex: number
  localSubPathIndex: number
  elementId: string
  layerId: string | null
  layerName: string | null
  d: string
  closed: boolean
  bboxMm: { x: number; y: number; width: number; height: number } | null
  perimeterMm: number | null
  confidence: ConfidenceLevel
  colors: string[]
  warnings: SvgPartWarning[]
}

interface SplitResult {
  subPaths: ExtractedSubPath[]
  pathElementCount: number
  warnings: SvgPartWarning[]
}

function splitPathDataSubpaths(d: string): string[] {
  const starts = [...d.matchAll(/[Mm]/g)].map((m) => m.index ?? 0)
  if (starts.length === 0) {
    return []
  }

  const segments: string[] = []
  for (let i = 0; i < starts.length; i += 1) {
    const start = starts[i]
    const end = i + 1 < starts.length ? starts[i + 1] : d.length
    const segment = d.slice(start, end).trim()
    if (segment.length > 0) {
      segments.push(segment)
    }
  }
  return segments
}

function pathColors(el: ParsedSvgElement): string[] {
  const out = new Set<string>()
  if (el.fill) out.add(el.fill)
  if (el.stroke) out.add(el.stroke)
  return [...out]
}

export function extractSubPaths(doc: ParsedSvgDocument, mmPerVbu: number | null): SplitResult {
  const warnings: SvgPartWarning[] = []
  const subPaths: ExtractedSubPath[] = []
  const pathElements = doc.elements.filter(
    (el) => el.type === 'path' && !!el.d && !el.excludeFromPartExtraction,
  )

  let globalSubPathIndex = 0
  for (const pathElement of pathElements) {
    const d = pathElement.d ?? ''
    const segments = splitPathDataSubpaths(d)

    for (let localIndex = 0; localIndex < segments.length; localIndex += 1) {
      const segment = segments[localIndex]
      const measured = measurePathShape(segment, mmPerVbu)
      const partWarnings: SvgPartWarning[] = []
      if (!measured.bboxMm || isDegenerateBbox(measured.bboxMm)) {
        partWarnings.push(
          partSplitWarning('SUBPATH_BOUNDS_UNAVAILABLE', 'warning', 'Unable to compute bounding box for subpath.', `${pathElement.elementId}_sp_${globalSubPathIndex + 1}`),
        )
      }

      const extracted: ExtractedSubPath = {
        id: `${pathElement.elementId}_sp_${globalSubPathIndex + 1}`,
        subPathIndex: globalSubPathIndex,
        localSubPathIndex: localIndex,
        elementId: pathElement.elementId,
        layerId: pathElement.layerId,
        layerName: pathElement.layerName,
        d: segment,
        closed: /[Zz]\s*$/.test(segment),
        bboxMm: measured.bboxMm,
        perimeterMm: measured.perimeterMm,
        confidence: measured.confidence,
        colors: pathColors(pathElement),
        warnings: partWarnings,
      }

      subPaths.push(extracted)
      warnings.push(...partWarnings)
      globalSubPathIndex += 1
    }
  }

  return {
    subPaths,
    pathElementCount: pathElements.length,
    warnings,
  }
}
