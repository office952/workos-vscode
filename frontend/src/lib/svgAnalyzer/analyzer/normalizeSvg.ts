import type { ConfidenceLevel, ParsedLength, SvgViewBox } from './types'

const PX_TO_MM = 25.4 / 96

export function parseLength(raw: string | null): ParsedLength | null {
  if (!raw) {
    return null
  }

  const trimmed = raw.trim()
  if (!trimmed) {
    return null
  }

  const match = trimmed.match(/^(-?\d*\.?\d+)([a-zA-Z%]*)$/)
  if (!match) {
    return null
  }

  const value = Number(match[1])
  if (!Number.isFinite(value)) {
    return null
  }

  const unit = match[2] ? match[2].toLowerCase() : null
  return {
    value,
    unit,
    raw: raw,
  }
}

export function parseViewBox(raw: string | null): SvgViewBox | null {
  if (!raw) {
    return null
  }

  const parts = raw
    .trim()
    .split(/[\s,]+/)
    .map(Number)

  if (parts.length !== 4 || parts.some((n) => !Number.isFinite(n))) {
    return null
  }

  return {
    minX: parts[0],
    minY: parts[1],
    width: parts[2],
    height: parts[3],
    raw,
  }
}

export function convertToMm(value: number, unit: string | null): number | null {
  if (!Number.isFinite(value)) {
    return null
  }

  switch (unit) {
    case null:
    case 'px':
      return value * PX_TO_MM
    case 'mm':
      return value
    case 'cm':
      return value * 10
    case 'in':
      return value * 25.4
    case 'inch':
      return value * 25.4
    case 'pt':
      return (value * 25.4) / 72
    default:
      return null
  }
}

export function inferConversion(
  width: ParsedLength | null,
  height: ParsedLength | null,
): {
  factor: number | null
  confidence: ConfidenceLevel
  detectedUnits: string | null
  reason: string
} {
  const unit = width?.unit ?? height?.unit ?? null

  if (!width && !height) {
    return {
      factor: null,
      confidence: 'low',
      detectedUnits: null,
      reason: 'No physical width/height declared in SVG root.',
    }
  }

  if (unit === 'mm' || unit === 'cm' || unit === 'in' || unit === 'inch' || unit === 'pt') {
    const one = convertToMm(1, unit)
    return {
      factor: one,
      confidence: 'high',
      detectedUnits: unit,
      reason: 'Explicit physical unit found on SVG root.',
    }
  }

  if (unit === 'px' || unit === null) {
    return {
      factor: convertToMm(1, 'px'),
      confidence: 'medium',
      detectedUnits: unit ?? 'px',
      reason: 'Pixel-based dimensions converted with 96 DPI assumption.',
    }
  }

  return {
    factor: null,
    confidence: 'low',
    detectedUnits: unit,
    reason: `Unsupported unit: ${unit}`,
  }
}

export function normalizeColor(raw: string | null): string | null {
  if (!raw) {
    return null
  }

  const value = raw.trim().toLowerCase()
  if (!value || value === 'none' || value === 'transparent') {
    return null
  }

  return value
}

export function numberAttr(value: string | null): number | null {
  if (value == null) {
    return null
  }

  const n = Number(value)
  return Number.isFinite(n) ? n : null
}
