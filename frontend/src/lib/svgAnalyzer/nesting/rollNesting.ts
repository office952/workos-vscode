import { createNestingWarning } from './nestingWarnings'
import type {
  NestingItemType,
  NestingPlacement,
  NestingPreparedPart,
  NestingRollJobLayout,
  NestingRotation,
  NestingSeparationReason,
  RollNestingConfig,
} from './nestingTypes'

interface Oriented {
  width: number
  height: number
  rotation: NestingRotation
}

interface RollJobMeta {
  jobId: string
  assignmentSource: 'auto-from-layer-color' | 'manual-future' | 'default-preview'
  jobKey: string
  sourceLayerName: string | null
  colorKey: string | null
  itemType: NestingItemType
  separationReason: NestingSeparationReason
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

function chooseOrientation(
  options: Oriented[],
  currentX: number,
  shelfHeight: number,
  usableRight: number,
  usableWidthMm: number,
): { chosen: Oriented | null; startsNewShelf: boolean; rotationReason: 'fit-width' | 'reduce-consumed-length' | null } {
  const fitCurrent = options.filter((o) => currentX + o.width <= usableRight)
  const fitNewShelf = options.filter((o) => o.width <= usableWidthMm)

  const original = options.find((o) => o.rotation === 0)
  const rotated = options.find((o) => o.rotation === 90)

  if (fitCurrent.length > 0) {
    const scored = fitCurrent
      .map((o) => ({
        option: o,
        addedLength: Math.max(shelfHeight, o.height) - shelfHeight,
      }))
      .sort((a, b) => {
        if (a.addedLength !== b.addedLength) return a.addedLength - b.addedLength
        if (a.option.height !== b.option.height) return a.option.height - b.option.height
        return a.option.width - b.option.width
      })

    const chosen = scored[0].option
    let reason: 'fit-width' | 'reduce-consumed-length' | null = null

    if (chosen.rotation === 90 && original) {
      const originalFits = currentX + original.width <= usableRight
      if (!originalFits) {
        reason = 'fit-width'
      } else {
        const originalAdded = Math.max(shelfHeight, original.height) - shelfHeight
        const rotatedAdded = Math.max(shelfHeight, chosen.height) - shelfHeight
        if (rotatedAdded < originalAdded) {
          reason = 'reduce-consumed-length'
        }
      }
    }

    return { chosen, startsNewShelf: false, rotationReason: reason }
  }

  const fitOnNewShelf = fitNewShelf.sort((a, b) => {
      if (a.height !== b.height) return a.height - b.height
      return a.width - b.width
    })

  if (fitOnNewShelf.length === 0) {
    return { chosen: null, startsNewShelf: true, rotationReason: null }
  }

  const chosen = fitOnNewShelf[0]
  let reason: 'fit-width' | 'reduce-consumed-length' | null = null

  if (chosen.rotation === 90 && original) {
    const originalFits = original.width <= usableWidthMm
    if (!originalFits) {
      reason = 'fit-width'
    } else if (chosen.height < original.height) {
      reason = 'reduce-consumed-length'
    }
  } else if (chosen.rotation === 90 && !original && rotated) {
    reason = 'fit-width'
  }

  return { chosen, startsNewShelf: true, rotationReason: reason }
}

export function runRollNesting(config: RollNestingConfig, parts: NestingPreparedPart[], jobMeta: RollJobMeta): NestingRollJobLayout {
  const placements: NestingPlacement[] = []
  const warnings: NestingRollJobLayout['warnings'] = []
  const unplaced: NestingRollJobLayout['unplaced'] = []

  let currentY = 0
  let currentX = config.leftMarginMm
  let shelfHeight = 0
  let usedLengthMm = 0
  let usedWidthRightMm = config.leftMarginMm

  const usableRight = config.leftMarginMm + config.usableWidthMm

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

    const options = orientations(part, config.allowRotation)
    const decision = chooseOrientation(options, currentX, shelfHeight, usableRight, config.usableWidthMm)

    if (decision.startsNewShelf) {
      if (shelfHeight > 0) {
        currentY += shelfHeight + config.partSpacingMm
      }
      currentX = config.leftMarginMm
      shelfHeight = 0
    }

    const chosen = decision.chosen

    if (!chosen) {
      unplaced.push({ partId: part.partId, partName: part.partName, reason: 'DOES_NOT_FIT_USABLE_WIDTH' })
      warnings.push(
        createNestingWarning(
          'NESTING_PART_UNPLACED',
          'warning',
          `Part does not fit roll usable width ${config.usableWidthMm}mm.`,
          part.partId,
          { usableWidthMm: config.usableWidthMm },
        ),
      )
      continue
    }

    const placement: NestingPlacement = {
      partId: part.partId,
      partName: part.partName,
      sourceLayerName: part.sourceLayerName,
      materialType: 'roll',
      containerId: config.configId,
      xMm: currentX,
      yMm: currentY,
      placedWidthMm: chosen.width,
      placedHeightMm: chosen.height,
      rotationDeg: chosen.rotation,
      spacingMm: config.partSpacingMm,
    }

    placements.push(placement)

    if (chosen.rotation === 90) {
      if (decision.rotationReason) {
        warnings.push(
          createNestingWarning(
            'NESTING_PART_ROTATED_TO_FIT',
            'info',
            'Part rotated 90 degrees by width-first decision.',
            part.partId,
            {
              configId: config.configId,
              reason: decision.rotationReason,
              originalWidthMm: part.widthMm,
              originalHeightMm: part.heightMm,
              rotatedWidthMm: chosen.width,
              rotatedHeightMm: chosen.height,
            },
          ),
        )
      }
    }

    currentX += chosen.width + config.partSpacingMm
    shelfHeight = Math.max(shelfHeight, chosen.height)
    usedLengthMm = Math.max(usedLengthMm, currentY + shelfHeight)
    usedWidthRightMm = Math.max(usedWidthRightMm, placement.xMm + placement.placedWidthMm)
  }

  const usedRollAreaSqm = (config.rollWidthMm * usedLengthMm) / 1_000_000
  const partsBoundingAreaSqm = placements.reduce((acc, placement) => acc + (placement.placedWidthMm * placement.placedHeightMm) / 1_000_000, 0)
  const wasteAreaSqm = Math.max(0, usedRollAreaSqm - partsBoundingAreaSqm)
  const efficiencyPercent = usedRollAreaSqm > 0 ? (partsBoundingAreaSqm / usedRollAreaSqm) * 100 : 0

  if (efficiencyPercent > 0 && efficiencyPercent < 30) {
    warnings.push(
      createNestingWarning('NESTING_LOW_EFFICIENCY', 'info', 'Roll nesting efficiency is below 30%.', undefined, {
        configId: config.configId,
        efficiencyPercent,
      }),
    )
  }

  return {
    jobId: jobMeta.jobId,
    assignmentSource: jobMeta.assignmentSource,
    jobKey: jobMeta.jobKey,
    sourceLayerName: jobMeta.sourceLayerName,
    colorKey: jobMeta.colorKey,
    separationReason: jobMeta.separationReason,
    itemType: jobMeta.itemType,
    sourceItemsCount: parts.length,
    placedItemsCount: placements.length,
    unplacedItemsCount: unplaced.length,
    consumedLengthMm: usedLengthMm,
    usedWidthMm: Math.max(0, usedWidthRightMm - config.leftMarginMm),
    usedLengthMm,
    usedRollAreaSqm,
    partsBoundingAreaSqm,
    wasteAreaSqm,
    efficiencyPercent,
    placements,
    unplaced,
    warnings,
  }
}
