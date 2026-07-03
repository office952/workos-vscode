import { DEFAULT_SHEET_CONFIGS } from './nestingConfigs'
import type { SheetNestingConfig } from './nestingTypes'

/** Standard ACM/Bond stock — 3000×1500 first, then 4000×1500 overflow. */
export const SHEET_CONFIG_ACM_3000x1500 = 'sheet_3000x1500'
export const SHEET_CONFIG_ACM_4000x1500 = 'sheet_4000x1500'

export const ACM_PANEL_SHEET_CONFIG_IDS = [SHEET_CONFIG_ACM_3000x1500, SHEET_CONFIG_ACM_4000x1500] as const

const acmConfigById = new Map<string, SheetNestingConfig>(
  DEFAULT_SHEET_CONFIGS.filter((config) =>
    (ACM_PANEL_SHEET_CONFIG_IDS as readonly string[]).includes(config.configId),
  ).map((config) => [config.configId, config]),
)

/** Face letters and general sheet nesting — not ACM bond panels. */
export const SHEET_CONFIG_FACE_LETTERS = 'sheet_3000x2000'

export function partFitsSheetBounds(
  partWidthMm: number,
  partHeightMm: number,
  config: SheetNestingConfig,
): boolean {
  if (partWidthMm <= 0 || partHeightMm <= 0) return false

  const orientations: [number, number][] = [[partWidthMm, partHeightMm]]
  if (config.allowRotation && Math.abs(partWidthMm - partHeightMm) > 0.0001) {
    orientations.push([partHeightMm, partWidthMm])
  }

  return orientations.some(
    ([widthMm, lengthMm]) => widthMm <= config.usableWidthMm && lengthMm <= config.usableLengthMm,
  )
}

export function pickAcmPanelSheetConfigId(partWidthMm: number, partHeightMm: number): string | null {
  for (const configId of ACM_PANEL_SHEET_CONFIG_IDS) {
    const config = acmConfigById.get(configId)
    if (config && partFitsSheetBounds(partWidthMm, partHeightMm, config)) {
      return configId
    }
  }
  return null
}

export function isBondPlatePart(part: {
  name?: string
  derivedPartKind?: string | null
  materialLabel?: string | null
}): boolean {
  if (part.name?.includes('placă Bond')) return true
  if (part.materialLabel?.includes('Bond')) return true
  return false
}

/** @deprecated Use isBondPlatePart — iluminarea nu mai folosește foile ACM Bond. */
export function isAcmPanelPart(part: {
  name?: string
  derivedPartKind?: string | null
  materialLabel?: string | null
}): boolean {
  return isBondPlatePart(part)
}

/** Pick smallest ACM stock sheet that fits the bond plate alone. */
export function pickAcmPanelSheetForParts(
  parts: Array<{ bounds: { widthMm?: number | null; heightMm?: number | null } }>,
): string | null {
  let maxWidth = 0
  let maxHeight = 0

  for (const part of parts) {
    const w = part.bounds.widthMm ?? 0
    const h = part.bounds.heightMm ?? 0
    maxWidth = Math.max(maxWidth, w)
    maxHeight = Math.max(maxHeight, h)
  }

  if (maxWidth <= 0 || maxHeight <= 0) return null
  return pickAcmPanelSheetConfigId(maxWidth, maxHeight)
}
