import { convertToMm, numberAttr } from './normalizeSvg'
import type { BoundingBox, ElementGeometry, GeometrySummary, ParsedSvgDocument, ParsedSvgElement } from './types'

// ---------------------------------------------------------------------------
// Bezier arc-length helpers (de Casteljau adaptive subdivision)
// ---------------------------------------------------------------------------

function cubicBezierArcLength(
  p0x: number, p0y: number,
  p1x: number, p1y: number,
  p2x: number, p2y: number,
  p3x: number, p3y: number,
  depth: number,
): number {
  const chord = Math.hypot(p3x - p0x, p3y - p0y)
  const poly =
    Math.hypot(p1x - p0x, p1y - p0y) +
    Math.hypot(p2x - p1x, p2y - p1y) +
    Math.hypot(p3x - p2x, p3y - p2y)
  if (depth >= 10 || poly - chord <= chord * 5e-5) {
    return (poly + chord) * 0.5
  }
  const m01x = (p0x + p1x) * 0.5, m01y = (p0y + p1y) * 0.5
  const m12x = (p1x + p2x) * 0.5, m12y = (p1y + p2y) * 0.5
  const m23x = (p2x + p3x) * 0.5, m23y = (p2y + p3y) * 0.5
  const m012x = (m01x + m12x) * 0.5, m012y = (m01y + m12y) * 0.5
  const m123x = (m12x + m23x) * 0.5, m123y = (m12y + m23y) * 0.5
  const mx = (m012x + m123x) * 0.5, my = (m012y + m123y) * 0.5
  return (
    cubicBezierArcLength(p0x, p0y, m01x, m01y, m012x, m012y, mx, my, depth + 1) +
    cubicBezierArcLength(mx, my, m123x, m123y, m23x, m23y, p3x, p3y, depth + 1)
  )
}

function quadBezierArcLength(
  p0x: number, p0y: number,
  p1x: number, p1y: number,
  p2x: number, p2y: number,
  depth: number,
): number {
  const chord = Math.hypot(p2x - p0x, p2y - p0y)
  const poly = Math.hypot(p1x - p0x, p1y - p0y) + Math.hypot(p2x - p1x, p2y - p1y)
  if (depth >= 10 || poly - chord <= chord * 5e-5) {
    return (poly + chord) * 0.5
  }
  const m01x = (p0x + p1x) * 0.5, m01y = (p0y + p1y) * 0.5
  const m12x = (p1x + p2x) * 0.5, m12y = (p1y + p2y) * 0.5
  const mx = (m01x + m12x) * 0.5, my = (m01y + m12y) * 0.5
  return (
    quadBezierArcLength(p0x, p0y, m01x, m01y, mx, my, depth + 1) +
    quadBezierArcLength(mx, my, m12x, m12y, p2x, p2y, depth + 1)
  )
}

// ---------------------------------------------------------------------------
// Sub-path counter (count M commands, check each segment for Z)
// ---------------------------------------------------------------------------

export function countSubPaths(d: string): { subPathCount: number; closedSubPathCount: number; openSubPathCount: number } {
  if (!d.trim()) {
    return { subPathCount: 0, closedSubPathCount: 0, openSubPathCount: 0 }
  }
  const mMatches = [...d.matchAll(/[Mm]/g)]
  if (!mMatches.length) {
    return { subPathCount: 0, closedSubPathCount: 0, openSubPathCount: 0 }
  }
  let closedCount = 0
  for (let idx = 0; idx < mMatches.length; idx += 1) {
    const start = mMatches[idx].index!
    const end = idx + 1 < mMatches.length ? mMatches[idx + 1].index! : d.length
    if (/[Zz]/.test(d.slice(start, end))) {
      closedCount += 1
    }
  }
  return {
    subPathCount: mMatches.length,
    closedSubPathCount: closedCount,
    openSubPathCount: mMatches.length - closedCount,
  }
}

function mergeBoxes(boxes: Array<BoundingBox | null>): BoundingBox | null {
  const valid = boxes.filter((b): b is BoundingBox => b != null)
  if (!valid.length) {
    return null
  }

  const minX = Math.min(...valid.map((b) => b.x))
  const minY = Math.min(...valid.map((b) => b.y))
  const maxX = Math.max(...valid.map((b) => b.x + b.width))
  const maxY = Math.max(...valid.map((b) => b.y + b.height))

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  }
}

function bboxFromElement(el: ParsedSvgElement): { bbox: BoundingBox | null; estimated: boolean; confidence: ElementGeometry['confidence'] } {
  const x = numberAttr(el.attributes.x ?? null) ?? 0
  const y = numberAttr(el.attributes.y ?? null) ?? 0

  switch (el.type) {
    case 'rect': {
      const width = numberAttr(el.attributes.width ?? null)
      const height = numberAttr(el.attributes.height ?? null)
      if (width == null || height == null) {
        return { bbox: null, estimated: true, confidence: 'low' }
      }
      return { bbox: { x, y, width, height }, estimated: false, confidence: 'high' }
    }
    case 'circle': {
      const cx = numberAttr(el.attributes.cx ?? null)
      const cy = numberAttr(el.attributes.cy ?? null)
      const r = numberAttr(el.attributes.r ?? null)
      if (cx == null || cy == null || r == null) {
        return { bbox: null, estimated: true, confidence: 'low' }
      }
      return {
        bbox: { x: cx - r, y: cy - r, width: r * 2, height: r * 2 },
        estimated: false,
        confidence: 'high',
      }
    }
    case 'ellipse': {
      const cx = numberAttr(el.attributes.cx ?? null)
      const cy = numberAttr(el.attributes.cy ?? null)
      const rx = numberAttr(el.attributes.rx ?? null)
      const ry = numberAttr(el.attributes.ry ?? null)
      if (cx == null || cy == null || rx == null || ry == null) {
        return { bbox: null, estimated: true, confidence: 'low' }
      }
      return {
        bbox: { x: cx - rx, y: cy - ry, width: rx * 2, height: ry * 2 },
        estimated: false,
        confidence: 'high',
      }
    }
    case 'line': {
      const x1 = numberAttr(el.attributes.x1 ?? null)
      const y1 = numberAttr(el.attributes.y1 ?? null)
      const x2 = numberAttr(el.attributes.x2 ?? null)
      const y2 = numberAttr(el.attributes.y2 ?? null)
      if (x1 == null || y1 == null || x2 == null || y2 == null) {
        return { bbox: null, estimated: true, confidence: 'low' }
      }
      const minX = Math.min(x1, x2)
      const minY = Math.min(y1, y2)
      return {
        bbox: { x: minX, y: minY, width: Math.abs(x2 - x1), height: Math.abs(y2 - y1) },
        estimated: false,
        confidence: 'high',
      }
    }
    case 'polyline':
    case 'polygon': {
      const parsedPoints = parsePoints(el.points)
      if (!parsedPoints.length) {
        return { bbox: null, estimated: true, confidence: 'low' }
      }
      const xs = parsedPoints.map((p) => p[0])
      const ys = parsedPoints.map((p) => p[1])
      return {
        bbox: {
          x: Math.min(...xs),
          y: Math.min(...ys),
          width: Math.max(...xs) - Math.min(...xs),
          height: Math.max(...ys) - Math.min(...ys),
        },
        estimated: false,
        confidence: 'high',
      }
    }
    case 'path': {
      if (!el.d) {
        return { bbox: null, estimated: true, confidence: 'low' }
      }
      return bboxFromPathData(el.d)
    }
    case 'text': {
      const width = 8 * (el.textContent?.length ?? 0)
      const height = 16
      return {
        bbox: { x, y: y - height, width, height },
        estimated: true,
        confidence: 'low',
      }
    }
    case 'image': {
      const width = numberAttr(el.attributes.width ?? null) ?? 0
      const height = numberAttr(el.attributes.height ?? null) ?? 0
      return {
        bbox: { x, y, width, height },
        estimated: true,
        confidence: 'medium',
      }
    }
    default:
      return { bbox: null, estimated: true, confidence: 'low' }
  }
}

function parsePoints(raw: string | null): Array<[number, number]> {
  if (!raw) {
    return []
  }

  const numbers = raw
    .trim()
    .split(/[\s,]+/)
    .map(Number)
    .filter((n) => Number.isFinite(n))

  const points: Array<[number, number]> = []
  for (let i = 0; i < numbers.length - 1; i += 2) {
    points.push([numbers[i], numbers[i + 1]])
  }
  return points
}

function bboxFromPathData(d: string): { bbox: BoundingBox | null; estimated: boolean; confidence: ElementGeometry['confidence'] } {
  const tokens = d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g)
  if (!tokens?.length) {
    return { bbox: null, estimated: true, confidence: 'low' }
  }

  let x = 0
  let y = 0
  let cmd = ''
  let i = 0
  const xs: number[] = []
  const ys: number[] = []

  while (i < tokens.length) {
    const token = tokens[i]
    if (/^[a-zA-Z]$/.test(token)) {
      cmd = token
      i += 1
      if (cmd === 'Z' || cmd === 'z') {
        continue
      }
    }

    const isRelative = cmd === cmd.toLowerCase()
    if (!cmd) {
      break
    }

    const pushPoint = (nx: number, ny: number): void => {
      x = nx
      y = ny
      xs.push(x)
      ys.push(y)
    }

    const n = (offset: number): number | null => {
      const value = Number(tokens[i + offset])
      return Number.isFinite(value) ? value : null
    }

    if (cmd.toLowerCase() === 'm' || cmd.toLowerCase() === 'l' || cmd.toLowerCase() === 't') {
      const nx = n(0)
      const ny = n(1)
      if (nx == null || ny == null) {
        break
      }
      pushPoint(isRelative ? x + nx : nx, isRelative ? y + ny : ny)
      i += 2
      continue
    }

    if (cmd.toLowerCase() === 'h') {
      const nx = n(0)
      if (nx == null) {
        break
      }
      pushPoint(isRelative ? x + nx : nx, y)
      i += 1
      continue
    }

    if (cmd.toLowerCase() === 'v') {
      const ny = n(0)
      if (ny == null) {
        break
      }
      pushPoint(x, isRelative ? y + ny : ny)
      i += 1
      continue
    }

    if (cmd.toLowerCase() === 'c') {
      const nx = n(4)
      const ny = n(5)
      if (nx == null || ny == null) {
        break
      }
      pushPoint(isRelative ? x + nx : nx, isRelative ? y + ny : ny)
      i += 6
      continue
    }

    if (cmd.toLowerCase() === 's' || cmd.toLowerCase() === 'q') {
      const nx = n(2)
      const ny = n(3)
      if (nx == null || ny == null) {
        break
      }
      pushPoint(isRelative ? x + nx : nx, isRelative ? y + ny : ny)
      i += 4
      continue
    }

    if (cmd.toLowerCase() === 'a') {
      const nx = n(5)
      const ny = n(6)
      if (nx == null || ny == null) {
        break
      }
      pushPoint(isRelative ? x + nx : nx, isRelative ? y + ny : ny)
      i += 7
      continue
    }

    i += 1
  }

  if (!xs.length || !ys.length) {
    return { bbox: null, estimated: true, confidence: 'low' }
  }

  return {
    bbox: {
      x: Math.min(...xs),
      y: Math.min(...ys),
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys),
    },
    estimated: true,
    confidence: 'medium',
  }
}

function isPathClosed(el: ParsedSvgElement): boolean | null {
  if (el.type === 'polygon') {
    return true
  }

  if (el.type === 'polyline' || el.type === 'line' || el.type === 'text' || el.type === 'image') {
    return false
  }

  if (el.type !== 'path') {
    return true
  }

  return el.d ? /[zZ]\s*$/.test(el.d.trim()) : null
}

function perimeterPx(el: ParsedSvgElement): { value: number | null; estimated: boolean } {
  switch (el.type) {
    case 'rect': {
      const w = numberAttr(el.attributes.width ?? null)
      const h = numberAttr(el.attributes.height ?? null)
      return { value: w != null && h != null ? 2 * (w + h) : null, estimated: false }
    }
    case 'circle': {
      const r = numberAttr(el.attributes.r ?? null)
      return { value: r != null ? 2 * Math.PI * r : null, estimated: false }
    }
    case 'ellipse': {
      const rx = numberAttr(el.attributes.rx ?? null)
      const ry = numberAttr(el.attributes.ry ?? null)
      if (rx == null || ry == null) {
        return { value: null, estimated: true }
      }
      return { value: Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry))), estimated: true }
    }
    case 'line': {
      const x1 = numberAttr(el.attributes.x1 ?? null)
      const y1 = numberAttr(el.attributes.y1 ?? null)
      const x2 = numberAttr(el.attributes.x2 ?? null)
      const y2 = numberAttr(el.attributes.y2 ?? null)
      if (x1 == null || y1 == null || x2 == null || y2 == null) {
        return { value: null, estimated: true }
      }
      return { value: Math.hypot(x2 - x1, y2 - y1), estimated: false }
    }
    case 'polyline':
    case 'polygon': {
      const points = parsePoints(el.points)
      if (points.length < 2) {
        return { value: null, estimated: true }
      }
      let p = 0
      for (let i = 1; i < points.length; i += 1) {
        p += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1])
      }
      if (el.type === 'polygon' && points.length > 2) {
        p += Math.hypot(points[0][0] - points[points.length - 1][0], points[0][1] - points[points.length - 1][1])
      }
      return { value: p, estimated: false }
    }
    case 'path': {
      if (!el.d) {
        return { value: null, estimated: true }
      }
      const approx = approximatePathLength(el.d)
      return { value: approx, estimated: true }
    }
    default:
      return { value: null, estimated: true }
  }
}

// Rewritten: uses bezier arc-length subdivision instead of chord-only.
// C/S commands: cubicBezierArcLength; Q/T: quadBezierArcLength; A: chord (lower bound, mark estimated).
// S/T smooth bezier: reflects last control point as per SVG spec.
function approximatePathLength(d: string): number | null {
  const tokens = d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g)
  if (!tokens?.length) {
    return null
  }

  let x = 0, y = 0
  let startX = 0, startY = 0
  let lastCp2x = 0, lastCp2y = 0
  let lastCmd = ''
  let cmd = ''
  let i = 0
  let totalLength = 0

  const num = (offset: number): number | null => {
    const v = Number(tokens[i + offset])
    return Number.isFinite(v) ? v : null
  }
  const toAbs = (delta: number, base: number): number => cmd === cmd.toLowerCase() ? base + delta : delta

  while (i < tokens.length) {
    const tok = tokens[i]
    if (/^[a-zA-Z]$/.test(tok)) {
      cmd = tok
      i += 1
      if (cmd === 'Z' || cmd === 'z') {
        totalLength += Math.hypot(x - startX, y - startY)
        x = startX; y = startY
        lastCp2x = x; lastCp2y = y; lastCmd = cmd
        continue
      }
    }
    if (!cmd) { i += 1; continue }

    if (cmd === 'M' || cmd === 'm') {
      const nx = num(0), ny = num(1)
      if (nx == null || ny == null) { i += 1; continue }
      x = toAbs(nx, x); y = toAbs(ny, y)
      startX = x; startY = y
      lastCp2x = x; lastCp2y = y; lastCmd = cmd
      cmd = cmd === 'm' ? 'l' : 'L'
      i += 2; continue
    }

    if (cmd === 'L' || cmd === 'l') {
      const nx = num(0), ny = num(1)
      if (nx == null || ny == null) { i += 1; continue }
      const tx = toAbs(nx, x), ty = toAbs(ny, y)
      totalLength += Math.hypot(tx - x, ty - y)
      lastCp2x = x; lastCp2y = y; lastCmd = cmd
      x = tx; y = ty; i += 2; continue
    }

    if (cmd === 'H' || cmd === 'h') {
      const n = num(0)
      if (n == null) { i += 1; continue }
      const tx = toAbs(n, x)
      totalLength += Math.abs(tx - x)
      lastCp2x = tx; lastCp2y = y; lastCmd = cmd
      x = tx; i += 1; continue
    }

    if (cmd === 'V' || cmd === 'v') {
      const n = num(0)
      if (n == null) { i += 1; continue }
      const ty = toAbs(n, y)
      totalLength += Math.abs(ty - y)
      lastCp2x = x; lastCp2y = ty; lastCmd = cmd
      y = ty; i += 1; continue
    }

    if (cmd === 'C' || cmd === 'c') {
      const cp1x = num(0), cp1y = num(1), cp2x = num(2), cp2y = num(3), ex = num(4), ey = num(5)
      if (cp1x == null || cp1y == null || cp2x == null || cp2y == null || ex == null || ey == null) { i += 1; continue }
      const acp1x = toAbs(cp1x, x), acp1y = toAbs(cp1y, y)
      const acp2x = toAbs(cp2x, x), acp2y = toAbs(cp2y, y)
      const tx = toAbs(ex, x), ty = toAbs(ey, y)
      totalLength += cubicBezierArcLength(x, y, acp1x, acp1y, acp2x, acp2y, tx, ty, 0)
      lastCp2x = acp2x; lastCp2y = acp2y; lastCmd = cmd
      x = tx; y = ty; i += 6; continue
    }

    if (cmd === 'S' || cmd === 's') {
      const cp2x = num(0), cp2y = num(1), ex = num(2), ey = num(3)
      if (cp2x == null || cp2y == null || ex == null || ey == null) { i += 1; continue }
      const prevC = lastCmd.toLowerCase()
      const cp1x = (prevC === 'c' || prevC === 's') ? 2 * x - lastCp2x : x
      const cp1y = (prevC === 'c' || prevC === 's') ? 2 * y - lastCp2y : y
      const acp2x = toAbs(cp2x, x), acp2y = toAbs(cp2y, y)
      const tx = toAbs(ex, x), ty = toAbs(ey, y)
      totalLength += cubicBezierArcLength(x, y, cp1x, cp1y, acp2x, acp2y, tx, ty, 0)
      lastCp2x = acp2x; lastCp2y = acp2y; lastCmd = cmd
      x = tx; y = ty; i += 4; continue
    }

    if (cmd === 'Q' || cmd === 'q') {
      const cpx = num(0), cpy = num(1), ex = num(2), ey = num(3)
      if (cpx == null || cpy == null || ex == null || ey == null) { i += 1; continue }
      const acpx = toAbs(cpx, x), acpy = toAbs(cpy, y)
      const tx = toAbs(ex, x), ty = toAbs(ey, y)
      totalLength += quadBezierArcLength(x, y, acpx, acpy, tx, ty, 0)
      lastCp2x = acpx; lastCp2y = acpy; lastCmd = cmd
      x = tx; y = ty; i += 4; continue
    }

    if (cmd === 'T' || cmd === 't') {
      const ex = num(0), ey = num(1)
      if (ex == null || ey == null) { i += 1; continue }
      const prevC = lastCmd.toLowerCase()
      const cpx = (prevC === 'q' || prevC === 't') ? 2 * x - lastCp2x : x
      const cpy = (prevC === 'q' || prevC === 't') ? 2 * y - lastCp2y : y
      const tx = toAbs(ex, x), ty = toAbs(ey, y)
      totalLength += quadBezierArcLength(x, y, cpx, cpy, tx, ty, 0)
      lastCp2x = cpx; lastCp2y = cpy; lastCmd = cmd
      x = tx; y = ty; i += 2; continue
    }

    if (cmd === 'A' || cmd === 'a') {
      // Elliptical arc: approximate with chord (conservative lower bound, estimated=true)
      const ex = num(5), ey = num(6)
      if (ex == null || ey == null) { i += 1; continue }
      const tx = toAbs(ex, x), ty = toAbs(ey, y)
      totalLength += Math.hypot(tx - x, ty - y)
      lastCp2x = x; lastCp2y = y; lastCmd = cmd
      x = tx; y = ty; i += 7; continue
    }

    i += 1 // safety fallthrough for unknown commands
  }

  return Number.isFinite(totalLength) ? totalLength : null
}

function areaPx2(el: ParsedSvgElement): { value: number | null; estimated: boolean } {
  switch (el.type) {
    case 'rect': {
      const w = numberAttr(el.attributes.width ?? null)
      const h = numberAttr(el.attributes.height ?? null)
      return { value: w != null && h != null ? w * h : null, estimated: false }
    }
    case 'circle': {
      const r = numberAttr(el.attributes.r ?? null)
      return { value: r != null ? Math.PI * r * r : null, estimated: false }
    }
    case 'ellipse': {
      const rx = numberAttr(el.attributes.rx ?? null)
      const ry = numberAttr(el.attributes.ry ?? null)
      return { value: rx != null && ry != null ? Math.PI * rx * ry : null, estimated: false }
    }
    case 'polygon': {
      const pts = parsePoints(el.points)
      if (pts.length < 3) {
        return { value: null, estimated: true }
      }
      let sum = 0
      for (let i = 0; i < pts.length; i += 1) {
        const p1 = pts[i]
        const p2 = pts[(i + 1) % pts.length]
        sum += p1[0] * p2[1] - p2[0] * p1[1]
      }
      return { value: Math.abs(sum / 2), estimated: false }
    }
    default:
      return { value: null, estimated: true }
  }
}

function isOutsideViewBox(bbox: BoundingBox | null, doc: ParsedSvgDocument): boolean {
  if (!bbox || !doc.viewBox) {
    return false
  }

  const vb = doc.viewBox
  const right = bbox.x + bbox.width
  const bottom = bbox.y + bbox.height
  return right < vb.minX || bottom < vb.minY || bbox.x > vb.minX + vb.width || bbox.y > vb.minY + vb.height
}

export function analyzeGeometry(doc: ParsedSvgDocument): GeometrySummary {
  // Compute mm-per-viewBox-unit correctly.
  // conversionToMm.factor only converts the unit (e.g. cm→mm = 10).
  // For an SVG with width="205cm" and viewBox="0 0 198.61 33.91",
  // 1 viewBox unit = 2050mm / 198.61 = 10.3217 mm — NOT 10.
  // Using the wrong factor causes ~3.2% perimeter underestimate.
  let mmFactor: number
  let scaleX: number | null = null
  let scaleY: number | null = null
  let uniformScale: boolean | null = null

  if (doc.viewBox && doc.width && doc.height && doc.conversionToMm.factor != null) {
    const widthMm = doc.width.value * doc.conversionToMm.factor
    const heightMm = doc.height.value * doc.conversionToMm.factor
    scaleX = widthMm / doc.viewBox.width
    scaleY = heightMm / doc.viewBox.height
    const relDiff = Math.abs(scaleX - scaleY) / Math.max(scaleX, scaleY)
    uniformScale = relDiff < 0.01
    mmFactor = (scaleX + scaleY) * 0.5
  } else {
    mmFactor = doc.conversionToMm.factor ?? convertToMm(1, 'px') ?? 1
  }

  const drawableElements = doc.elements.filter((el) => el.type !== 'group' && el.type !== 'unknown')
  const pathElements = drawableElements.filter((el) => el.type === 'path')

  // Aggregate sub-path counts across all path elements
  let totalSubPaths = 0
  let totalClosedSubPaths = 0
  let totalOpenSubPaths = 0
  for (const el of pathElements) {
    if (el.d) {
      const sp = countSubPaths(el.d)
      totalSubPaths += sp.subPathCount
      totalClosedSubPaths += sp.closedSubPathCount
      totalOpenSubPaths += sp.openSubPathCount
    }
  }

  const elementGeometries = drawableElements.map((el): ElementGeometry => {
    const shapeBbox = bboxFromElement(el)
    const area = areaPx2(el)
    const perimeter = perimeterPx(el)
    const spInfo =
      el.type === 'path' && el.d
        ? countSubPaths(el.d)
        : { subPathCount: 0, closedSubPathCount: 0, openSubPathCount: 0 }
    const warnings: string[] = []

    if (!el.fill && !el.stroke) {
      warnings.push('Element has no fill and no stroke.')
    }

    if (el.strokeWidth != null && el.strokeWidth > 0 && el.strokeWidth < 0.2) {
      warnings.push('Very thin stroke detected (<0.2 units).')
    }

    if (el.transform && /matrix\(/i.test(el.transform)) {
      warnings.push('Complex matrix transform detected.')
    }

    if (isOutsideViewBox(shapeBbox.bbox, doc)) {
      warnings.push('Element appears outside viewBox.')
    }

    if (shapeBbox.bbox && shapeBbox.bbox.width * mmFactor < 0.5 && shapeBbox.bbox.height * mmFactor < 0.5) {
      warnings.push('Very small element detected (<0.5mm).')
    }

    return {
      elementId: el.elementId,
      bbox: shapeBbox.bbox,
      areaMm2: area.value == null ? null : area.value * mmFactor * mmFactor,
      perimeterMm: perimeter.value == null ? null : perimeter.value * mmFactor,
      isClosed: isPathClosed(el),
      estimated: shapeBbox.estimated || area.estimated || perimeter.estimated,
      confidence: shapeBbox.confidence,
      warnings,
      subPathCount: spInfo.subPathCount,
      closedSubPathCount: spInfo.closedSubPathCount,
      openSubPathCount: spInfo.openSubPathCount,
    }
  })

  const totalBbox = mergeBoxes(elementGeometries.map((e) => e.bbox))

  // Fix: start accumulators at null — do NOT use 0.
  // If no element has a calculable area/perimeter, result is null (not 0.0000).
  const totalAreaMm2 = elementGeometries.reduce<number | null>((acc, e) => {
    if (e.areaMm2 == null) return acc
    return (acc ?? 0) + e.areaMm2
  }, null)

  const totalPerimeterMm = elementGeometries.reduce<number | null>((acc, e) => {
    if (e.perimeterMm == null) return acc
    return (acc ?? 0) + e.perimeterMm
  }, null)

  const openPathCount = elementGeometries.filter((e) => e.isClosed === false).length
  const closedPathCount = elementGeometries.filter((e) => e.isClosed === true).length
  const transformedElementCount = doc.elements.filter((e) => !!e.transform).length
  const tinyElementCount = elementGeometries.filter((e) => e.warnings.some((w) => w.includes('Very small'))).length
  const outsideViewBoxCount = elementGeometries.filter((e) => e.warnings.some((w) => w.includes('outside viewBox'))).length

  return {
    totalBbox,
    totalAreaMm2,
    totalPerimeterMm,
    elementGeometries,
    openPathCount,
    closedPathCount,
    transformedElementCount,
    tinyElementCount,
    outsideViewBoxCount,
    pathElementCount: pathElements.length,
    subPathCount: totalSubPaths,
    closedSubPathCount: totalClosedSubPaths,
    openSubPathCount: totalOpenSubPaths,
    mmPerVbu: mmFactor,
    scaleX,
    scaleY,
    uniformScale,
  }
}
