import { DEFAULT_SHEET_CONFIGS } from './nestingConfigs'
import { partFitsSheetBounds, pickAcmPanelSheetConfigId } from './pickAcmPanelSheet'
import { SHEET_CONFIG_PLEXI_10MM } from '../part-extractor/innerHolePackageConstants'
import type { DerivedPartKind } from '../part-extractor/innerHolePackageConstants'

const smallSheet = DEFAULT_SHEET_CONFIGS.find((config) => config.configId === SHEET_CONFIG_PLEXI_10MM)!

export function isIlluminationPackagePart(part: {
  derivedPartKind?: DerivedPartKind | null | string
}): boolean {
  return (
    part.derivedPartKind === 'diffuser-plate' ||
    part.derivedPartKind === 'back-cover-plate' ||
    part.derivedPartKind === 'wall-strip-plate'
  )
}

export function pickIlluminationSheetConfigId(partWidthMm: number, partHeightMm: number): string | null {
  if (partFitsSheetBounds(partWidthMm, partHeightMm, smallSheet)) {
    return SHEET_CONFIG_PLEXI_10MM
  }

  const acm = pickAcmPanelSheetConfigId(partWidthMm, partHeightMm)
  if (acm) return acm

  return null
}

export function pickIlluminationSheetForParts(
  parts: Array<{ bounds: { widthMm?: number | null; heightMm?: number | null } }>,
): string | null {
  let maxWidth = 0
  let maxHeight = 0

  for (const part of parts) {
    maxWidth = Math.max(maxWidth, part.bounds.widthMm ?? 0)
    maxHeight = Math.max(maxHeight, part.bounds.heightMm ?? 0)
  }

  if (maxWidth <= 0 || maxHeight <= 0) return null
  return pickIlluminationSheetConfigId(maxWidth, maxHeight)
}
