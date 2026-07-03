export type ElementPaintKind = 'solid' | 'gradient' | 'pattern' | 'none'

export interface SvgPaintDefs {
  gradientIds: Set<string>
  patternIds: Set<string>
}

const SOLID_COLOR = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i
const RGB_COLOR = /^rgba?\(/i
const NAMED_COLOR = /^[a-z]+$/i

export function collectPaintDefs(svgRoot: Element): SvgPaintDefs {
  const gradientIds = new Set<string>()
  const patternIds = new Set<string>()

  for (const node of svgRoot.querySelectorAll('linearGradient, radialGradient')) {
    const id = node.getAttribute('id')
    if (id) gradientIds.add(id)
  }

  for (const node of svgRoot.querySelectorAll('pattern')) {
    const id = node.getAttribute('id')
    if (id) patternIds.add(id)
  }

  return { gradientIds, patternIds }
}

export function parsePaintReference(raw: string | null): string | null {
  if (!raw) return null
  const value = raw.trim()
  const match = value.match(/^url\(#([^)]+)\)$/i)
  return match?.[1] ?? null
}

export function classifyPaintValue(
  raw: string | null,
  defs: SvgPaintDefs,
): { kind: ElementPaintKind; solid: string | null; ref: string | null } {
  if (!raw) {
    return { kind: 'none', solid: null, ref: null }
  }

  const value = raw.trim().toLowerCase()
  if (!value || value === 'none' || value === 'transparent') {
    return { kind: 'none', solid: null, ref: null }
  }

  const ref = parsePaintReference(value)
  if (ref) {
    if (defs.gradientIds.has(ref)) {
      return { kind: 'gradient', solid: null, ref }
    }
    if (defs.patternIds.has(ref)) {
      return { kind: 'pattern', solid: null, ref }
    }
    return { kind: 'gradient', solid: null, ref }
  }

  if (SOLID_COLOR.test(value) || RGB_COLOR.test(value) || (NAMED_COLOR.test(value) && value !== 'currentcolor')) {
    return { kind: 'solid', solid: value, ref: null }
  }

  return { kind: 'none', solid: value, ref: null }
}

export function isSolidColorValue(raw: string | null): boolean {
  if (!raw) return false
  const value = raw.trim().toLowerCase()
  return SOLID_COLOR.test(value) || RGB_COLOR.test(value)
}
