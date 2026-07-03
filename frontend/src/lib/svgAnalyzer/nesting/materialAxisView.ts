import type { NestingPlacement } from './nestingTypes'

/**
 * Material axis convention (roll + sheet):
 *
 * Algorithm / nesting engine:
 * - placement.xMm, placedWidthMm  → cross axis (material width: 100 / 126 / 200 cm)
 * - placement.yMm, placedHeightMm → feed axis (length consumed along roll / sheet)
 *
 * Part bounds before nesting (SVG axis-aligned bbox):
 * - bounds.widthMm  → SVG X extent (horizontal in file)
 * - bounds.heightMm → SVG Y extent (vertical in file)
 * These are NOT swapped; rotation 0/90 maps them onto cross/feed at nest time.
 *
 * Operator preview (view space):
 * - horizontal → feed / length
 * - vertical   → cross / width
 */
export interface MaterialViewRect {
  xMm: number
  yMm: number
  widthMm: number
  heightMm: number
}

export function mapPlacementToMaterialView(placement: NestingPlacement): MaterialViewRect {
  return {
    xMm: placement.yMm,
    yMm: placement.xMm,
    widthMm: placement.placedHeightMm,
    heightMm: placement.placedWidthMm,
  }
}

export function crossExtentMm(widthMm: number, heightMm: number, rotationDeg: 0 | 90): number {
  return rotationDeg === 90 ? heightMm : widthMm
}

export function feedExtentMm(widthMm: number, heightMm: number, rotationDeg: 0 | 90): number {
  return rotationDeg === 90 ? widthMm : heightMm
}
