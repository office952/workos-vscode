import { effectiveBondReturnDepths } from './bondProductionDefaults'

export interface BondFlatPatternPoint {
  xMm: number
  yMm: number
}

export type BondFlatPatternLayerKind = 'cut-outside' | 'fold-lip' | 'fold-wall' | 'face'

export interface BondFlatPatternLineSegment {
  kind: 'fold-line'
  foldRole: 'lip' | 'wall'
  x1Mm: number
  y1Mm: number
  x2Mm: number
  y2Mm: number
}

/** @deprecated Preview-only; prefer cutOutline + foldLines. */
export interface BondFlatPatternPolyline {
  kind: BondFlatPatternLayerKind
  closed: boolean
  points: BondFlatPatternPoint[]
  label?: string
}

export interface BondFlatPatternGeometry {
  faceWidthMm: number
  faceHeightMm: number
  wallMm: number
  lipMm: number
  outerWidthMm: number
  outerHeightMm: number
  /** Contur decupare CNC — model Corel (colțuri cu trepte lip/wall). */
  cutOutline: BondFlatPatternPoint[]
  /** Linii gravare pliu — segmente deschise ca în CorelDRAW. */
  foldLines: BondFlatPatternLineSegment[]
  /** Față vizibilă (referință preview). */
  faceOutline: BondFlatPatternPoint[]
  polylines: BondFlatPatternPolyline[]
}

export interface BuildBondFlatPatternInput {
  faceWidthMm: number
  faceHeightMm: number
  returnDepthMm?: number | null
  returnDepth2Mm?: number | null
  useReturnDefaults?: boolean
}

function pt(xMm: number, yMm: number): BondFlatPatternPoint {
  return { xMm, yMm }
}

function seg(
  foldRole: 'lip' | 'wall',
  x1Mm: number,
  y1Mm: number,
  x2Mm: number,
  y2Mm: number,
): BondFlatPatternLineSegment {
  return { kind: 'fold-line', foldRole, x1Mm, y1Mm, x2Mm, y2Mm }
}

/**
 * Contur exterior Corel — 2 întoarceri (perete + buză).
 * Origine: colț stânga-jos; axa Y în sus (CAD).
 * Aliniat la acm-2intoarceri-50mm+30mm.svg (față 3000×1000 → 3160×1160).
 */
export function buildCorelDoubleReturnCutOutline(
  faceWidthMm: number,
  faceHeightMm: number,
  wallMm: number,
  lipMm: number,
): BondFlatPatternPoint[] {
  const bandMm = wallMm + lipMm
  const tabMm = bandMm + lipMm
  const outerWidthMm = faceWidthMm + bandMm * 2
  const outerHeightMm = faceHeightMm + bandMm * 2

  const l = lipMm
  const b = bandMm
  const t = tabMm
  const ow = outerWidthMm
  const oh = outerHeightMm

  return [
    pt(ow - t, 0),
    pt(t, 0),
    pt(b, l),
    pt(b, b),
    pt(l, b),
    pt(0, t),
    pt(0, oh - t),
    pt(l, oh - b),
    pt(b, oh - b),
    pt(b, oh - l),
    pt(t, oh),
    pt(ow - t, oh),
    pt(ow - b, oh - l),
    pt(ow - b, oh - b),
    pt(ow - l, oh - b),
    pt(ow, oh - t),
    pt(ow, t),
    pt(ow - l, b),
    pt(ow - b, b),
    pt(ow - b, l),
  ]
}

/** Gravare pliu — 8 linii ca în layer gravare-cnc-135gr Corel. */
export function buildCorelDoubleReturnFoldLines(
  faceWidthMm: number,
  faceHeightMm: number,
  wallMm: number,
  lipMm: number,
): BondFlatPatternLineSegment[] {
  const bandMm = wallMm + lipMm
  const outerWidthMm = faceWidthMm + bandMm * 2
  const outerHeightMm = faceHeightMm + bandMm * 2

  const l = lipMm
  const b = bandMm
  const ow = outerWidthMm
  const oh = outerHeightMm

  return [
    // Pliu perete (80 mm)
    seg('wall', l, b, ow - l, b),
    seg('wall', b, l, b, oh - l),
    seg('wall', ow - b, l, ow - b, oh - l),
    seg('wall', l, oh - b, ow - l, oh - b),
    // Pliu buză (30 mm)
    seg('lip', b, l, ow - b, l),
    seg('lip', b, oh - l, ow - b, oh - l),
    seg('lip', l, b, l, oh - b),
    seg('lip', ow - l, b, ow - l, oh - b),
  ]
}

/** O singură întoarcere — model acm-intoarcere-50mm.svg. */
export function buildCorelSingleReturnCutOutline(
  faceWidthMm: number,
  faceHeightMm: number,
  returnMm: number,
): BondFlatPatternPoint[] {
  const r = returnMm
  const ow = faceWidthMm + r * 2
  const oh = faceHeightMm + r * 2

  return [
    pt(ow - r, r),
    pt(ow - r, 0),
    pt(r, 0),
    pt(r, r),
    pt(0, r),
    pt(0, oh - r),
    pt(r, oh - r),
    pt(r, oh),
    pt(ow - r, oh),
    pt(ow - r, oh - r),
    pt(ow, oh - r),
    pt(ow, r),
  ]
}

export function buildCorelSingleReturnFoldLines(
  faceWidthMm: number,
  faceHeightMm: number,
  returnMm: number,
): BondFlatPatternLineSegment[] {
  const r = returnMm
  const ow = faceWidthMm + r * 2
  const oh = faceHeightMm + r * 2

  return [
    seg('wall', 0, r, ow, r),
    seg('wall', r, 0, r, oh),
    seg('wall', ow - r, 0, ow - r, oh),
    seg('wall', 0, oh - r, ow, oh - r),
  ]
}

function faceOutlineRect(
  faceWidthMm: number,
  faceHeightMm: number,
  wallMm: number,
  lipMm: number,
): BondFlatPatternPoint[] {
  const bandMm = wallMm + lipMm
  const x = bandMm
  const y = bandMm
  return [
    pt(x, y),
    pt(x + faceWidthMm, y),
    pt(x + faceWidthMm, y + faceHeightMm),
    pt(x, y + faceHeightMm),
  ]
}

function buildPreviewPolylines(
  cutOutline: BondFlatPatternPoint[],
  foldLines: BondFlatPatternLineSegment[],
  faceOutline: BondFlatPatternPoint[],
): BondFlatPatternPolyline[] {
  const lipLines = foldLines.filter((line) => line.foldRole === 'lip')
  const wallLines = foldLines.filter((line) => line.foldRole === 'wall')

  return [
    { kind: 'cut-outside', closed: true, label: 'decupare-cnc-outside', points: cutOutline },
    ...wallLines.map((line, index) => ({
      kind: 'fold-wall' as const,
      closed: false,
      label: `gravare pliu perete ${index + 1}`,
      points: [pt(line.x1Mm, line.y1Mm), pt(line.x2Mm, line.y2Mm)],
    })),
    ...lipLines.map((line, index) => ({
      kind: 'fold-lip' as const,
      closed: false,
      label: `gravare pliu buză ${index + 1}`,
      points: [pt(line.x1Mm, line.y1Mm), pt(line.x2Mm, line.y2Mm)],
    })),
    { kind: 'face', closed: true, label: 'față Bond vizibilă', points: faceOutline },
  ]
}

export function buildBondFlatPatternGeometry(input: BuildBondFlatPatternInput): BondFlatPatternGeometry {
  const { wallMm, lipMm } = effectiveBondReturnDepths(
    input.returnDepthMm,
    input.returnDepth2Mm,
    input.useReturnDefaults !== false,
  )

  const faceWidthMm = input.faceWidthMm
  const faceHeightMm = input.faceHeightMm
  const bandMm = wallMm + lipMm
  const outerWidthMm = faceWidthMm + bandMm * 2
  const outerHeightMm = faceHeightMm + bandMm * 2

  let cutOutline: BondFlatPatternPoint[]
  let foldLines: BondFlatPatternLineSegment[]
  let faceOutline: BondFlatPatternPoint[]

  if (lipMm > 0.001) {
    cutOutline = buildCorelDoubleReturnCutOutline(faceWidthMm, faceHeightMm, wallMm, lipMm)
    foldLines = buildCorelDoubleReturnFoldLines(faceWidthMm, faceHeightMm, wallMm, lipMm)
    faceOutline = faceOutlineRect(faceWidthMm, faceHeightMm, wallMm, lipMm)
  } else {
    cutOutline = buildCorelSingleReturnCutOutline(faceWidthMm, faceHeightMm, wallMm)
    foldLines = buildCorelSingleReturnFoldLines(faceWidthMm, faceHeightMm, wallMm)
    const r = wallMm
    faceOutline = [
      pt(r, r),
      pt(r + faceWidthMm, r),
      pt(r + faceWidthMm, r + faceHeightMm),
      pt(r, r + faceHeightMm),
    ]
  }

  return {
    faceWidthMm,
    faceHeightMm,
    wallMm,
    lipMm,
    outerWidthMm: lipMm > 0.001 ? outerWidthMm : faceWidthMm + wallMm * 2,
    outerHeightMm: lipMm > 0.001 ? outerHeightMm : faceHeightMm + wallMm * 2,
    cutOutline,
    foldLines,
    faceOutline,
    polylines: buildPreviewPolylines(cutOutline, foldLines, faceOutline),
  }
}

export function bondFlatPatternToPreviewSvg(geometry: BondFlatPatternGeometry, scale = 0.08): string {
  const stroke: Record<BondFlatPatternLayerKind, string> = {
    'cut-outside': '#2B2A29',
    'fold-lip': '#E31E24',
    'fold-wall': '#E31E24',
    face: '#0066CC',
  }

  const paths = geometry.polylines
    .map((polyline) => {
      const pts = polyline.points
      if (pts.length < 2) return ''
      const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.xMm * scale} ${p.yMm * scale}`).join(' ')
      const pathD = polyline.closed ? `${d} Z` : d
      const dash = polyline.kind === 'face' ? ' stroke-dasharray="4 2"' : ''
      return `<path d="${pathD}" fill="none" stroke="${stroke[polyline.kind]}" stroke-width="0.6"${dash} data-label="${polyline.label ?? polyline.kind}"/>`
    })
    .filter(Boolean)
    .join('\n')

  const w = geometry.outerWidthMm * scale
  const h = geometry.outerHeightMm * scale

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">
  <g transform="scale(1,-1) translate(0,${-h})">
  ${paths}
  </g>
</svg>`
}
