import { NESTING_GRANULARITY } from './buildNestingReport'
import { createNestingWarning } from './nestingWarnings'
import type {
  NestingPlacement,
  NestingPreparedPart,
  NestingRotation,
  NestingSheetLayout,
  SheetNestingConfig,
} from './nestingTypes'

interface Oriented {
  width: number
  height: number
  rotation: NestingRotation
}

interface SheetState {
  id: string
  currentX: number
  currentY: number
  shelfHeight: number
}

function sortPartsForShelves(parts: NestingPreparedPart[]): NestingPreparedPart[] {
  return [...parts].sort((a, b) => {
    const aKey = Math.max(a.widthMm, a.heightMm)
    const bKey = Math.max(b.widthMm, b.heightMm)
    if (bKey !== aKey) return bKey - aKey
    return b.boundingAreaSqm - a.boundingAreaSqm
  })
}

function orientations(part: NestingPreparedPart, allowRotation: boolean): Oriented[] {
  const list: Oriented[] = [{ width: part.widthMm, height: part.heightMm, rotation: 0 }]
  if (allowRotation && Math.abs(part.widthMm - part.heightMm) > 0.0001) {
    list.push({ width: part.heightMm, height: part.widthMm, rotation: 90 })
  }
  return list
}

function tryPlaceInSheet(
  part: NestingPreparedPart,
  sheet: SheetState,
  config: SheetNestingConfig,
): { placement: NestingPlacement | null; rotationReason: 'fit-width' | 'reduce-consumed-length' | null } {
  const usableRight = config.edgeMarginMm + config.usableWidthMm
  const usableBottom = config.edgeMarginMm + config.usableLengthMm

  const options = orientations(part, config.allowRotation)
  const original = options.find((o) => o.rotation === 0)

  const fitCurrent = options.filter((o) => sheet.currentX + o.width <= usableRight && sheet.currentY + o.height <= usableBottom)
  if (fitCurrent.length > 0) {
    const chosen = fitCurrent
      .map((o) => ({
        option: o,
        addedLength: Math.max(sheet.shelfHeight, o.height) - sheet.shelfHeight,
      }))
      .sort((a, b) => {
        if (a.addedLength !== b.addedLength) return a.addedLength - b.addedLength
        if (a.option.height !== b.option.height) return a.option.height - b.option.height
        return a.option.width - b.option.width
      })[0].option

    const placement: NestingPlacement = {
      partId: part.partId,
      partName: part.partName,
      sourceLayerName: part.sourceLayerName,
      materialType: 'sheet',
      containerId: sheet.id,
      xMm: sheet.currentX,
      yMm: sheet.currentY,
      placedWidthMm: chosen.width,
      placedHeightMm: chosen.height,
      rotationDeg: chosen.rotation,
      spacingMm: config.partSpacingMm,
    }
    sheet.currentX += chosen.width + config.partSpacingMm
    sheet.shelfHeight = Math.max(sheet.shelfHeight, chosen.height)

    let rotationReason: 'fit-width' | 'reduce-consumed-length' | null = null
    if (chosen.rotation === 90 && original) {
      const originalFits = sheet.currentX - chosen.width - config.partSpacingMm + original.width <= usableRight
      if (!originalFits) {
        rotationReason = 'fit-width'
      } else {
        const originalAdded = Math.max(sheet.shelfHeight, original.height) - sheet.shelfHeight
        const rotatedAdded = Math.max(sheet.shelfHeight, chosen.height) - sheet.shelfHeight
        if (rotatedAdded < originalAdded) {
          rotationReason = 'reduce-consumed-length'
        }
      }
    }

    return { placement, rotationReason }
  }

  const nextRowY = sheet.currentY + (sheet.shelfHeight > 0 ? sheet.shelfHeight + config.partSpacingMm : 0)
  const fitNextRow = options.filter((o) => config.edgeMarginMm + o.width <= usableRight && nextRowY + o.height <= usableBottom)
  if (fitNextRow.length > 0) {
    sheet.currentY = nextRowY
    sheet.currentX = config.edgeMarginMm
    sheet.shelfHeight = 0
    const chosen = fitNextRow.sort((a, b) => a.height - b.height)[0]
    const placement: NestingPlacement = {
      partId: part.partId,
      partName: part.partName,
      sourceLayerName: part.sourceLayerName,
      materialType: 'sheet',
      containerId: sheet.id,
      xMm: sheet.currentX,
      yMm: sheet.currentY,
      placedWidthMm: chosen.width,
      placedHeightMm: chosen.height,
      rotationDeg: chosen.rotation,
      spacingMm: config.partSpacingMm,
    }
    sheet.currentX += chosen.width + config.partSpacingMm
    sheet.shelfHeight = Math.max(sheet.shelfHeight, chosen.height)

    let rotationReason: 'fit-width' | 'reduce-consumed-length' | null = null
    if (chosen.rotation === 90 && original) {
      const originalFits = config.edgeMarginMm + original.width <= usableRight
      if (!originalFits) {
        rotationReason = 'fit-width'
      } else if (chosen.height < original.height) {
        rotationReason = 'reduce-consumed-length'
      }
    }

    return { placement, rotationReason }
  }

  return { placement: null, rotationReason: null }
}

function fitsOnEmptySheet(part: NestingPreparedPart, config: SheetNestingConfig): boolean {
  return orientations(part, config.allowRotation).some((o) => o.width <= config.usableWidthMm && o.height <= config.usableLengthMm)
}

export function runSheetNesting(config: SheetNestingConfig, parts: NestingPreparedPart[]): NestingSheetLayout {
  const placements: NestingPlacement[] = []
  const warnings: NestingSheetLayout['warnings'] = []
  const unplaced: NestingSheetLayout['unplaced'] = []

  const sheets: SheetState[] = [{ id: 'sheet_1', currentX: config.edgeMarginMm, currentY: config.edgeMarginMm, shelfHeight: 0 }]

  for (const part of sortPartsForShelves(parts)) {
    if (!part.canNest) {
      unplaced.push({ partId: part.partId, partName: part.partName, reason: 'NOT_NESTABLE' })
      warnings.push(createNestingWarning('NESTING_PART_NOT_NESTABLE', 'warning', 'Part marked as not nestable.', part.partId))
      continue
    }

    if (!(part.widthMm > 0 && part.heightMm > 0)) {
      unplaced.push({ partId: part.partId, partName: part.partName, reason: 'MISSING_BOUNDS' })
      warnings.push(createNestingWarning('NESTING_PART_MISSING_BOUNDS', 'warning', 'Part has missing bounds.', part.partId))
      continue
    }

    let placed = false

    for (const sheet of sheets) {
      const outcome = tryPlaceInSheet(part, sheet, config)
      if (outcome.placement) {
        placements.push(outcome.placement)
        if (outcome.rotationReason) {
          warnings.push(
            createNestingWarning('NESTING_PART_ROTATED_TO_FIT', 'info', 'Part rotated 90 degrees by width-first decision.', part.partId, {
              configId: config.configId,
              reason: outcome.rotationReason,
              originalWidthMm: part.widthMm,
              originalHeightMm: part.heightMm,
              rotatedWidthMm: outcome.placement.placedWidthMm,
              rotatedHeightMm: outcome.placement.placedHeightMm,
            }),
          )
        }
        placed = true
        break
      }
    }

    if (!placed) {
      if (!fitsOnEmptySheet(part, config)) {
        unplaced.push({ partId: part.partId, partName: part.partName, reason: 'DOES_NOT_FIT_SHEET' })
        warnings.push(createNestingWarning('NESTING_PART_UNPLACED', 'warning', 'Part does not fit sheet usable area.', part.partId))
        continue
      }

      const newSheet: SheetState = {
        id: `sheet_${sheets.length + 1}`,
        currentX: config.edgeMarginMm,
        currentY: config.edgeMarginMm,
        shelfHeight: 0,
      }
      sheets.push(newSheet)

      const outcome = tryPlaceInSheet(part, newSheet, config)
      if (outcome.placement) {
        placements.push(outcome.placement)
        if (outcome.rotationReason) {
          warnings.push(
            createNestingWarning('NESTING_PART_ROTATED_TO_FIT', 'info', 'Part rotated 90 degrees by width-first decision.', part.partId, {
              configId: config.configId,
              reason: outcome.rotationReason,
              originalWidthMm: part.widthMm,
              originalHeightMm: part.heightMm,
              rotatedWidthMm: outcome.placement.placedWidthMm,
              rotatedHeightMm: outcome.placement.placedHeightMm,
            }),
          )
        }
      } else {
        unplaced.push({ partId: part.partId, partName: part.partName, reason: 'DOES_NOT_FIT_SHEET' })
        warnings.push(createNestingWarning('NESTING_PART_UNPLACED', 'warning', 'Part does not fit even on new sheet.', part.partId))
      }
    }
  }

  const sheetsUsed = sheets.length
  const consumedLengthMm = placements.length > 0 ? Math.max(...placements.map((placement) => placement.yMm + placement.placedHeightMm)) - config.edgeMarginMm : 0
  const usedWidthMm = placements.length > 0 ? Math.max(...placements.map((placement) => placement.xMm + placement.placedWidthMm)) - config.edgeMarginMm : 0
  const preservedLengthMm = Math.max(0, config.usableLengthMm - consumedLengthMm)

  const usedSheetAreaSqm = (sheetsUsed * config.sheetWidthMm * config.sheetLengthMm) / 1_000_000
  const partsBoundingAreaSqm = placements.reduce((acc, placement) => acc + (placement.placedWidthMm * placement.placedHeightMm) / 1_000_000, 0)
  const wasteAreaSqm = Math.max(0, usedSheetAreaSqm - partsBoundingAreaSqm)
  const efficiencyPercent = usedSheetAreaSqm > 0 ? (partsBoundingAreaSqm / usedSheetAreaSqm) * 100 : 0

  if (efficiencyPercent > 0 && efficiencyPercent < 30) {
    warnings.push(
      createNestingWarning('NESTING_LOW_EFFICIENCY', 'info', 'Sheet nesting efficiency is below 30%.', undefined, {
        configId: config.configId,
        efficiencyPercent,
      }),
    )
  }

  return {
    configId: config.configId,
    materialType: 'sheet',
    granularity: NESTING_GRANULARITY,
    assignmentSource: 'default-preview',
    materialFrame: {
      materialType: 'sheet',
      sheetLengthMm: config.sheetLengthMm,
      sheetWidthMm: config.sheetWidthMm,
      usableLengthMm: config.usableLengthMm,
      usableWidthMm: config.usableWidthMm,
      feedAxis: 'length',
      crossAxis: 'width',
      packingDirection: 'width-first',
      optimizeFor: 'preserve-continuous-length',
    },
    itemType: 'child-part',
    sourceItemsCount: parts.length,
    placedItemsCount: placements.length,
    unplacedItemsCount: unplaced.length,
    sheetWidthMm: config.sheetWidthMm,
    sheetLengthMm: config.sheetLengthMm,
    usableWidthMm: config.usableWidthMm,
    usableLengthMm: config.usableLengthMm,
    edgeMarginMm: config.edgeMarginMm,
    partSpacingMm: config.partSpacingMm,
    allowRotation: config.allowRotation,
    sheetsUsed,
    consumedLengthMm,
    usedWidthMm,
    preservedLengthMm,
    usedSheetAreaSqm,
    partsBoundingAreaSqm,
    wasteAreaSqm,
    efficiencyPercent,
    placements,
    unplaced,
    warnings,
  }
}
