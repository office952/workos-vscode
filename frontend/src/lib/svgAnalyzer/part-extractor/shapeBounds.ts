import type { ConfidenceLevel } from '../analyzer/types'

export interface MeasuredPathShape {
  bboxMm: { x: number; y: number; width: number; height: number } | null
  perimeterMm: number | null
  confidence: ConfidenceLevel
}

const MIN_BBOX_MM = 1e-6

export function isDegenerateBbox(bbox: { width: number; height: number } | null | undefined): boolean {
  if (!bbox) return true
  return !(bbox.width > MIN_BBOX_MM && bbox.height > MIN_BBOX_MM)
}

function pickBetterMeasurement(
  primary: MeasuredPathShape | null,
  fallback: MeasuredPathShape,
): MeasuredPathShape {
  if (!primary || isDegenerateBbox(primary.bboxMm)) {
    return fallback
  }

  if (isDegenerateBbox(fallback.bboxMm)) {
    return primary
  }

  const primaryArea = (primary.bboxMm?.width ?? 0) * (primary.bboxMm?.height ?? 0)
  const fallbackArea = (fallback.bboxMm?.width ?? 0) * (fallback.bboxMm?.height ?? 0)
  if (fallbackArea > primaryArea * 1.05) {
    return {
      bboxMm: fallback.bboxMm,
      perimeterMm: fallback.perimeterMm ?? primary.perimeterMm,
      confidence: fallback.confidence === 'low' ? primary.confidence : fallback.confidence,
    }
  }

  return primary
}

function fromSvgApi(pathData: string, mmPerVbu: number | null): MeasuredPathShape | null {
  if (typeof document === 'undefined') {
    return null
  }

  try {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
    path.setAttribute('d', pathData)
    svg.appendChild(path)
    svg.style.position = 'absolute'
    svg.style.left = '-10000px'
    svg.style.top = '-10000px'
    document.body.appendChild(svg)

    const bbox = typeof (path as unknown as { getBBox?: () => DOMRect }).getBBox === 'function' ? (path as unknown as { getBBox: () => DOMRect }).getBBox() : null
    const length = typeof (path as unknown as { getTotalLength?: () => number }).getTotalLength === 'function'
      ? (path as unknown as { getTotalLength: () => number }).getTotalLength()
      : null

    document.body.removeChild(svg)

    if (!bbox) {
      return null
    }

    const factor = mmPerVbu ?? 1
    return {
      bboxMm: {
        x: bbox.x * factor,
        y: bbox.y * factor,
        width: bbox.width * factor,
        height: bbox.height * factor,
      },
      perimeterMm: length == null ? null : length * factor,
      confidence: mmPerVbu == null ? 'medium' : 'high',
    }
  } catch {
    return null
  }
}

function parseTokens(d: string): string[] {
  return d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g) ?? []
}

interface PlanarPoint {
  x: number
  y: number
}

function toMm(value: number, mmPerVbu: number | null): number {
  return value * (mmPerVbu ?? 1)
}

function cubicBezierPoints(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  x3: number,
  y3: number,
  steps = 6,
): PlanarPoint[] {
  const points: PlanarPoint[] = []
  for (let step = 1; step <= steps; step += 1) {
    const t = step / steps
    const u = 1 - t
    points.push({
      x: u * u * u * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3,
      y: u * u * u * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3,
    })
  }
  return points
}

function quadraticBezierPoints(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  steps = 5,
): PlanarPoint[] {
  const points: PlanarPoint[] = []
  for (let step = 1; step <= steps; step += 1) {
    const t = step / steps
    const u = 1 - t
    points.push({
      x: u * u * x0 + 2 * u * t * x1 + t * t * x2,
      y: u * u * y0 + 2 * u * t * y1 + t * t * y2,
    })
  }
  return points
}

export function extractPathVerticesMm(pathData: string, mmPerVbu: number | null): PlanarPoint[] {
  const tokens = parseTokens(pathData)
  if (!tokens.length) {
    return []
  }

  let x = 0
  let y = 0
  let startX = 0
  let startY = 0
  let cmd = ''
  let i = 0
  const points: PlanarPoint[] = []

  const n = (offset: number): number | null => {
    const value = Number(tokens[i + offset])
    return Number.isFinite(value) ? value : null
  }

  const push = (nx: number, ny: number): void => {
    x = nx
    y = ny
    points.push({ x: toMm(nx, mmPerVbu), y: toMm(ny, mmPerVbu) })
  }

  while (i < tokens.length) {
    const token = tokens[i]
    if (/^[a-zA-Z]$/.test(token)) {
      cmd = token
      i += 1
      if (cmd === 'Z' || cmd === 'z') {
        x = startX
        y = startY
        continue
      }
    }

    if (!cmd) {
      i += 1
      continue
    }

    const rel = cmd === cmd.toLowerCase()

    if (cmd.toLowerCase() === 'm' || cmd.toLowerCase() === 'l' || cmd.toLowerCase() === 't') {
      const nx = n(0)
      const ny = n(1)
      if (nx == null || ny == null) break
      const absX = rel ? x + nx : nx
      const absY = rel ? y + ny : ny
      if (cmd.toLowerCase() === 'm') {
        x = absX
        y = absY
        startX = absX
        startY = absY
        points.push({ x: toMm(absX, mmPerVbu), y: toMm(absY, mmPerVbu) })
      } else {
        push(absX, absY)
      }
      i += 2
      continue
    }

    if (cmd.toLowerCase() === 'h') {
      const nx = n(0)
      if (nx == null) break
      push(rel ? x + nx : nx, y)
      i += 1
      continue
    }

    if (cmd.toLowerCase() === 'v') {
      const ny = n(0)
      if (ny == null) break
      push(x, rel ? y + ny : ny)
      i += 1
      continue
    }

    if (cmd.toLowerCase() === 'c') {
      const x1 = n(0)
      const y1 = n(1)
      const x2 = n(2)
      const y2 = n(3)
      const nx = n(4)
      const ny = n(5)
      if (x1 == null || y1 == null || x2 == null || y2 == null || nx == null || ny == null) break
      const absX1 = rel ? x + x1 : x1
      const absY1 = rel ? y + y1 : y1
      const absX2 = rel ? x + x2 : x2
      const absY2 = rel ? y + y2 : y2
      const absX = rel ? x + nx : nx
      const absY = rel ? y + ny : ny
      for (const point of cubicBezierPoints(x, y, absX1, absY1, absX2, absY2, absX, absY)) {
        points.push({ x: toMm(point.x, mmPerVbu), y: toMm(point.y, mmPerVbu) })
      }
      x = absX
      y = absY
      i += 6
      continue
    }

    if (cmd.toLowerCase() === 's' || cmd.toLowerCase() === 'q') {
      const x1 = n(0)
      const y1 = n(1)
      const nx = n(2)
      const ny = n(3)
      if (x1 == null || y1 == null || nx == null || ny == null) break
      const absX1 = rel ? x + x1 : x1
      const absY1 = rel ? y + y1 : y1
      const absX = rel ? x + nx : nx
      const absY = rel ? y + ny : ny
      for (const point of quadraticBezierPoints(x, y, absX1, absY1, absX, absY)) {
        points.push({ x: toMm(point.x, mmPerVbu), y: toMm(point.y, mmPerVbu) })
      }
      x = absX
      y = absY
      i += 4
      continue
    }

    if (cmd.toLowerCase() === 'a') {
      const nx = n(5)
      const ny = n(6)
      if (nx == null || ny == null) break
      push(rel ? x + nx : nx, rel ? y + ny : ny)
      i += 7
      continue
    }

    i += 1
  }

  return points
}

export function isPointInPolygonEvenOdd(xMm: number, yMm: number, ring: PlanarPoint[]): boolean {
  if (ring.length < 3) {
    return false
  }

  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const xi = ring[i].x
    const yi = ring[i].y
    const xj = ring[j].x
    const yj = ring[j].y
    const intersects = yi > yMm !== yj > yMm && xMm < ((xj - xi) * (yMm - yi)) / (yj - yi + 1e-12) + xi
    if (intersects) {
      inside = !inside
    }
  }
  return inside
}

function sampleBboxPointsMm(
  bboxMm: { x: number; y: number; width: number; height: number },
  grid = 3,
): PlanarPoint[] {
  const points: PlanarPoint[] = []
  for (let row = 0; row < grid; row += 1) {
    for (let col = 0; col < grid; col += 1) {
      points.push({
        x: bboxMm.x + (bboxMm.width * (col + 0.5)) / grid,
        y: bboxMm.y + (bboxMm.height * (row + 0.5)) / grid,
      })
    }
  }
  return points
}

export function isPointInEvenOddRings(rings: PlanarPoint[][], xMm: number, yMm: number): boolean {
  let crossings = 0
  for (const ring of rings) {
    if (ring.length < 3) {
      continue
    }
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
      const xi = ring[i].x
      const yi = ring[i].y
      const xj = ring[j].x
      const yj = ring[j].y
      const intersects = yi > yMm !== yj > yMm && xMm < ((xj - xi) * (yMm - yi)) / (yj - yi + 1e-12) + xi
      if (intersects) {
        crossings += 1
      }
    }
  }
  return crossings % 2 === 1
}

function isPointInsideCompoundPathEvenOdd(
  pathData: string,
  xMm: number,
  yMm: number,
  mmPerVbu: number | null,
): boolean {
  if (typeof document !== 'undefined') {
    try {
      const factor = mmPerVbu && mmPerVbu > 0 ? mmPerVbu : 1
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
      path.setAttribute('d', pathData)
      path.setAttribute('fill-rule', 'evenodd')
      svg.appendChild(path)
      svg.style.position = 'absolute'
      svg.style.left = '-10000px'
      svg.style.top = '-10000px'
      document.body.appendChild(svg)

      const isInside =
        typeof (path as unknown as { isPointInFill?: (p: DOMPoint) => boolean }).isPointInFill === 'function'
          ? (path as unknown as { isPointInFill: (p: DOMPoint) => boolean }).isPointInFill(
              new DOMPoint(xMm / factor, yMm / factor),
            )
          : null

      document.body.removeChild(svg)
      if (isInside === true || isInside === false) {
        return isInside
      }
    } catch {
      // fall through to polygon even-odd rings
    }
  }

  const starts = [...pathData.matchAll(/[Mm]/g)].map((match) => match.index ?? 0)
  const rings: PlanarPoint[][] = []
  for (let index = 0; index < starts.length; index += 1) {
    const start = starts[index]
    const end = index + 1 < starts.length ? starts[index + 1] : pathData.length
    const segment = pathData.slice(start, end).trim()
    if (segment.length > 0) {
      rings.push(extractPathVerticesMm(segment, mmPerVbu))
    }
  }
  if (!rings.length) {
    rings.push(extractPathVerticesMm(pathData, mmPerVbu))
  }
  return isPointInEvenOddRings(rings, xMm, yMm)
}

export function isInnerContourHoleOfOuter(
  outerPathData: string,
  innerPathData: string,
  innerBboxMm: { x: number; y: number; width: number; height: number },
  mmPerVbu: number | null,
  minHollowRatio = 0.32,
): boolean {
  const samples = sampleBboxPointsMm(innerBboxMm)
  if (!samples.length) {
    return false
  }

  const compoundPath = `${outerPathData} ${innerPathData}`
  let hollowHits = 0
  let outerHits = 0
  for (const sample of samples) {
    const inOuter = isPointInsidePathFill(outerPathData, sample.x, sample.y, mmPerVbu)
    const inCompound = isPointInsidePathFill(compoundPath, sample.x, sample.y, mmPerVbu)
    if (inOuter) {
      outerHits += 1
    }
    if (inOuter && !inCompound) {
      hollowHits += 1
    }
  }

  if (outerHits / samples.length < minHollowRatio) {
    return false
  }

  return hollowHits / samples.length >= minHollowRatio
}

export function isPointInsidePathFill(
  pathData: string,
  xMm: number,
  yMm: number,
  mmPerVbu: number | null,
): boolean {
  if (typeof document !== 'undefined') {
    try {
      const factor = mmPerVbu && mmPerVbu > 0 ? mmPerVbu : 1
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
      path.setAttribute('d', pathData)
      path.setAttribute('fill-rule', 'evenodd')
      svg.appendChild(path)
      svg.style.position = 'absolute'
      svg.style.left = '-10000px'
      svg.style.top = '-10000px'
      document.body.appendChild(svg)

      const isInside =
        typeof (path as unknown as { isPointInFill?: (p: DOMPoint) => boolean }).isPointInFill === 'function'
          ? (path as unknown as { isPointInFill: (p: DOMPoint) => boolean }).isPointInFill(
              new DOMPoint(xMm / factor, yMm / factor),
            )
          : null

      document.body.removeChild(svg)
      if (isInside === true || isInside === false) {
        return isInside
      }
    } catch {
      // fall through to polygon ray cast
    }
  }

  const moveCount = (pathData.match(/[Mm]/g) ?? []).length
  if (moveCount > 1) {
    return isPointInsideCompoundPathEvenOdd(pathData, xMm, yMm, mmPerVbu)
  }

  const ring = extractPathVerticesMm(pathData, mmPerVbu)
  return isPointInPolygonEvenOdd(xMm, yMm, ring)
}

export function isHoleInsideOuterPathFill(
  outerPathData: string,
  innerBboxMm: { x: number; y: number; width: number; height: number },
  mmPerVbu: number | null,
  minHitRatio = 0.34,
): boolean {
  const samples = sampleBboxPointsMm(innerBboxMm)
  if (!samples.length) {
    return false
  }
  let hits = 0
  for (const sample of samples) {
    if (isPointInsidePathFill(outerPathData, sample.x, sample.y, mmPerVbu)) {
      hits += 1
    }
  }
  return hits / samples.length >= minHitRatio
}

function estimateBBoxAndLength(pathData: string, mmPerVbu: number | null): MeasuredPathShape {
  const tokens = parseTokens(pathData)
  if (!tokens.length) {
    return { bboxMm: null, perimeterMm: null, confidence: 'low' }
  }

  let x = 0
  let y = 0
  let startX = 0
  let startY = 0
  let cmd = ''
  let i = 0
  let lengthPx = 0
  const xs: number[] = []
  const ys: number[] = []

  const n = (offset: number): number | null => {
    const value = Number(tokens[i + offset])
    return Number.isFinite(value) ? value : null
  }

  while (i < tokens.length) {
    const token = tokens[i]
    if (/^[a-zA-Z]$/.test(token)) {
      cmd = token
      i += 1
      if (cmd === 'Z' || cmd === 'z') {
        lengthPx += Math.hypot(startX - x, startY - y)
        x = startX
        y = startY
        continue
      }
    }

    if (!cmd) {
      i += 1
      continue
    }

    const rel = cmd === cmd.toLowerCase()
    const push = (nx: number, ny: number): void => {
      lengthPx += Math.hypot(nx - x, ny - y)
      x = nx
      y = ny
      xs.push(nx)
      ys.push(ny)
    }

    if (cmd.toLowerCase() === 'm' || cmd.toLowerCase() === 'l' || cmd.toLowerCase() === 't') {
      const nx = n(0)
      const ny = n(1)
      if (nx == null || ny == null) break
      const absX = rel ? x + nx : nx
      const absY = rel ? y + ny : ny
      if (cmd.toLowerCase() === 'm') {
        x = absX
        y = absY
        startX = absX
        startY = absY
        xs.push(absX)
        ys.push(absY)
      } else {
        push(absX, absY)
      }
      i += 2
      continue
    }

    if (cmd.toLowerCase() === 'h') {
      const nx = n(0)
      if (nx == null) break
      push(rel ? x + nx : nx, y)
      i += 1
      continue
    }

    if (cmd.toLowerCase() === 'v') {
      const ny = n(0)
      if (ny == null) break
      push(x, rel ? y + ny : ny)
      i += 1
      continue
    }

    if (cmd.toLowerCase() === 'c') {
      const nx = n(4)
      const ny = n(5)
      if (nx == null || ny == null) break
      push(rel ? x + nx : nx, rel ? y + ny : ny)
      i += 6
      continue
    }

    if (cmd.toLowerCase() === 's' || cmd.toLowerCase() === 'q') {
      const nx = n(2)
      const ny = n(3)
      if (nx == null || ny == null) break
      push(rel ? x + nx : nx, rel ? y + ny : ny)
      i += 4
      continue
    }

    if (cmd.toLowerCase() === 'a') {
      const nx = n(5)
      const ny = n(6)
      if (nx == null || ny == null) break
      push(rel ? x + nx : nx, rel ? y + ny : ny)
      i += 7
      continue
    }

    i += 1
  }

  if (!xs.length || !ys.length) {
    return { bboxMm: null, perimeterMm: null, confidence: 'low' }
  }

  const factor = mmPerVbu ?? 1
  return {
    bboxMm: {
      x: Math.min(...xs) * factor,
      y: Math.min(...ys) * factor,
      width: (Math.max(...xs) - Math.min(...xs)) * factor,
      height: (Math.max(...ys) - Math.min(...ys)) * factor,
    },
    perimeterMm: lengthPx * factor,
    confidence: mmPerVbu == null ? 'low' : 'medium',
  }
}

export function measurePathShape(pathData: string, mmPerVbu: number | null): MeasuredPathShape {
  const estimated = estimateBBoxAndLength(pathData, mmPerVbu)
  const apiResult = fromSvgApi(pathData, mmPerVbu)
  return pickBetterMeasurement(apiResult, estimated)
}

export function subPathCentroidMm(
  bboxMm: { x: number; y: number; width: number; height: number } | null,
): { xMm: number; yMm: number } | null {
  if (!bboxMm || isDegenerateBbox(bboxMm)) {
    return null
  }
  return {
    xMm: bboxMm.x + bboxMm.width / 2,
    yMm: bboxMm.y + bboxMm.height / 2,
  }
}
