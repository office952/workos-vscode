import { inferConversion, normalizeColor, numberAttr, parseLength, parseViewBox } from './normalizeSvg'
import { classifyPaintValue, collectPaintDefs } from './classifyPaint'
import type { ParsedSvgDocument, ParsedSvgElement } from './types'

const SUPPORTED_TAGS = new Set([
  'path',
  'rect',
  'circle',
  'ellipse',
  'line',
  'polyline',
  'polygon',
  'text',
  'image',
  'g',
])

let autoId = 0

function nextElementId(): string {
  autoId += 1
  return `el-${autoId}`
}

function attr(el: Element, name: string): string | null {
  const value = el.getAttribute(name)
  return value == null ? null : value
}

function layerNameFromGroup(el: Element): string | null {
  return (
    attr(el, 'inkscape:label') ??
    attr(el, 'data-name') ??
    attr(el, 'label') ??
    attr(el, 'id') ??
    null
  )
}

function readAttributes(el: Element): Record<string, string> {
  const result: Record<string, string> = {}
  for (const item of Array.from(el.attributes)) {
    result[item.name] = item.value
  }
  return result
}

function getElementType(tagName: string): ParsedSvgElement['type'] {
  if (tagName === 'g') {
    return 'group'
  }

  if (tagName === 'path' || tagName === 'rect' || tagName === 'circle' || tagName === 'ellipse' || tagName === 'line' || tagName === 'polyline' || tagName === 'polygon' || tagName === 'text' || tagName === 'image') {
    return tagName
  }

  return 'unknown'
}

export function parseSvg(source: string, fileName: string, fileSizeBytes: number): ParsedSvgDocument {
  autoId = 0

  const parseErrors: string[] = []
  const parser = new DOMParser()
  const doc = parser.parseFromString(source, 'image/svg+xml')

  const parserError = doc.querySelector('parsererror')
  if (parserError) {
    parseErrors.push(`Invalid SVG XML: ${parserError.textContent?.trim() ?? 'unknown parser error'}`)
  }

  const svg = doc.querySelector('svg')
  if (!svg) {
    return {
      fileName,
      fileSizeBytes,
      source,
      width: null,
      height: null,
      viewBox: null,
      conversionToMm: {
        factor: null,
        confidence: 'low',
        detectedUnits: null,
        reason: 'No <svg> root element found.',
      },
      groups: [],
      elements: [],
      layerNameDuplicates: [],
      parseErrors: ['No <svg> root element found.', ...parseErrors],
    }
  }

  const width = parseLength(attr(svg, 'width'))
  const height = parseLength(attr(svg, 'height'))
  const viewBox = parseViewBox(attr(svg, 'viewBox'))
  const conversionToMm = inferConversion(width, height)
  const paintDefs = collectPaintDefs(svg)

  const elements: ParsedSvgElement[] = []
  const groups: ParsedSvgDocument['groups'] = []
  const layerNameSet = new Map<string, number>()

  const walk = (
    node: Element,
    currentLayerId: string | null,
    currentLayerName: string | null,
    inDefinitions: boolean,
  ): void => {
    const tagName = node.tagName.toLowerCase()
    const childInDefinitions =
      inDefinitions || tagName === 'defs' || tagName === 'clippath' || tagName === 'mask' || tagName === 'symbol'

    if (!SUPPORTED_TAGS.has(tagName)) {
      for (const child of Array.from(node.children)) {
        walk(child, currentLayerId, currentLayerName, childInDefinitions)
      }
      return
    }

    const id = attr(node, 'id')
    const elementId = id ?? nextElementId()
    const type = getElementType(tagName)

    let nextLayerId = currentLayerId
    let nextLayerName = currentLayerName

    if (tagName === 'g') {
      nextLayerId = elementId
      nextLayerName = layerNameFromGroup(node)
      groups.push({
        id: elementId,
        name: nextLayerName,
        elementIds: [],
      })

      if (nextLayerName) {
        const seen = layerNameSet.get(nextLayerName) ?? 0
        layerNameSet.set(nextLayerName, seen + 1)
      }
    }

    const rawFill = attr(node, 'fill')
    const rawStroke = attr(node, 'stroke')
    const fillClassified = classifyPaintValue(rawFill, paintDefs)
    const strokeClassified = classifyPaintValue(rawStroke, paintDefs)

    const parsedElement: ParsedSvgElement = {
      id,
      elementId,
      type,
      tagName,
      layerId: currentLayerId,
      layerName: currentLayerName,
      className: attr(node, 'class'),
      fill: normalizeColor(rawFill),
      stroke: normalizeColor(rawStroke),
      fillSolid: fillClassified.solid,
      strokeSolid: strokeClassified.solid,
      fillPaint: fillClassified.kind,
      strokePaint: strokeClassified.kind,
      fillRef: fillClassified.ref,
      strokeRef: strokeClassified.ref,
      strokeWidth: numberAttr(attr(node, 'stroke-width')),
      transform: attr(node, 'transform'),
      d: attr(node, 'd'),
      points: attr(node, 'points'),
      textContent: tagName === 'text' ? node.textContent?.trim() ?? null : null,
      attributes: readAttributes(node),
      index: elements.length,
      excludeFromPartExtraction: childInDefinitions && tagName === 'path',
    }

    elements.push(parsedElement)

    if (currentLayerId) {
      const group = groups.find((g) => g.id === currentLayerId)
      if (group) {
        group.elementIds.push(elementId)
      }
    }

    for (const child of Array.from(node.children)) {
      walk(child, nextLayerId, nextLayerName, childInDefinitions)
    }
  }

  for (const child of Array.from(svg.children)) {
    walk(child, null, null, false)
  }

  const layerNameDuplicates = Array.from(layerNameSet.entries())
    .filter(([, count]) => count > 1)
    .map(([name]) => name)

  return {
    fileName,
    fileSizeBytes,
    source,
    width,
    height,
    viewBox,
    conversionToMm,
    groups,
    elements,
    layerNameDuplicates,
    parseErrors,
  }
}
