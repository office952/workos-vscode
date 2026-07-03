import type { ColorAnalysis, ParsedSvgDocument } from './types'

function topColors(values: string[], limit = 5): string[] {
  const counts = new Map<string, number>()
  for (const color of values) {
    counts.set(color, (counts.get(color) ?? 0) + 1)
  }

  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([color]) => color)
}

export function analyzeColors(doc: ParsedSvgDocument): ColorAnalysis {
  const fills = doc.elements.map((e) => e.fill).filter((v): v is string => !!v)
  const strokes = doc.elements.map((e) => e.stroke).filter((v): v is string => !!v)
  const unique = Array.from(new Set([...fills, ...strokes]))

  const byLayer: Record<string, string[]> = {}
  for (const el of doc.elements) {
    const key = el.layerName ?? el.layerId ?? 'unassigned'
    const set = new Set(byLayer[key] ?? [])
    if (el.fill) {
      set.add(el.fill)
    }
    if (el.stroke) {
      set.add(el.stroke)
    }
    byLayer[key] = Array.from(set)
  }

  return {
    unique,
    dominant: topColors([...fills, ...strokes]),
    fills: Array.from(new Set(fills)),
    strokes: Array.from(new Set(strokes)),
    byLayer,
  }
}
