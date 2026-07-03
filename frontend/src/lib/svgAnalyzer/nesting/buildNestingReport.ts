import { DEFAULT_ROLL_CONFIGS, DEFAULT_SHEET_CONFIGS } from './nestingConfigs'
import { SHEET_CONFIG_LARGE_PANEL } from '../part-extractor/innerHolePackageConstants'
import { runRollNesting } from './rollNesting'
import { runSheetNesting } from './sheetNesting'
import { createNestingWarning } from './nestingWarnings'
import type {
  NestingInputItem,
  NestingJobInput,
  NestingPreparedPart,
  NestingReport,
  NestingRollLayout,
} from './nestingTypes'
import type { SvgPartExtractionReport } from '../part-extractor/partTypes'

/** Nesting always packs individual child parts — never whole layers. */
export const NESTING_GRANULARITY = 'child-parts' as const

function pickColorKey(values: string[]): string | null {
  const color = values.find((value) => /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value))
  return color?.toLowerCase() ?? null
}

function prepareChildParts(partsReport: SvgPartExtractionReport): NestingPreparedPart[] {
  const prepared: NestingPreparedPart[] = []

  for (const item of partsReport.items) {
    const copies = Math.max(1, item.quantity)
    for (let i = 0; i < copies; i += 1) {
      prepared.push({
        partId: copies === 1 ? item.id : `${item.id}_q${i + 1}`,
        partName: item.name,
        itemType: 'child-part',
        sourceLayerId: item.source.layerId,
        sourceLayerName: item.source.layerName,
        colorKey: pickColorKey(item.colors),
        widthMm: item.bounds.widthMm ?? 0,
        heightMm: item.bounds.heightMm ?? 0,
        boundingAreaSqm: item.bounds.boundingAreaSqm ?? 0,
        canNest: item.canNest,
        preferredSheetConfigId: item.preferredSheetConfigId ?? null,
        materialLabel: item.materialLabel ?? null,
        sourceWarnings: item.warnings,
      })
    }
  }

  return prepared
}

function isRollEligible(part: NestingPreparedPart): boolean {
  return part.canNest && !part.preferredSheetConfigId
}

function isSheetEligible(part: NestingPreparedPart, configId: string): boolean {
  if (!part.canNest) return false
  if (part.preferredSheetConfigId) return part.preferredSheetConfigId === configId
  return configId === SHEET_CONFIG_LARGE_PANEL
}

function buildRollJobKey(configId: string, layerName: string | null, colorKey: string | null): string {
  return `roll:${configId}:${NESTING_GRANULARITY}:${layerName ?? 'unassigned'}:${colorKey ?? 'unknown'}`
}

function buildSheetJobKey(configId: string): string {
  return `sheet:${configId}:${NESTING_GRANULARITY}:global`
}

function groupByLayerColor(items: NestingPreparedPart[]): Map<string, NestingPreparedPart[]> {
  const groups = new Map<string, NestingPreparedPart[]>()

  for (const item of items) {
    const key = `${item.sourceLayerName ?? 'unassigned'}|${item.colorKey ?? 'unknown'}`
    const existing = groups.get(key) ?? []
    existing.push(item)
    groups.set(key, existing)
  }

  return groups
}

function toInputItems(source: NestingPreparedPart[]): NestingInputItem[] {
  return source.map((item) => ({
    itemId: item.partId,
    itemName: item.partName,
    sourceLayerName: item.sourceLayerName,
    colorKey: item.colorKey,
    widthMm: item.widthMm,
    heightMm: item.heightMm,
    bounds: {
      widthMm: item.widthMm,
      heightMm: item.heightMm,
      boundingAreaSqm: item.boundingAreaSqm,
    },
    sourceType: 'part',
    roleAssignment: null,
    canNest: item.canNest,
    preferredSheetConfigId: item.preferredSheetConfigId,
    materialLabel: item.materialLabel,
    sourceWarnings: item.sourceWarnings,
  }))
}

function buildJobInputs(preparedChildParts: NestingPreparedPart[]): NestingJobInput[] {
  const jobs: NestingJobInput[] = []
  const rollEligible = preparedChildParts.filter(isRollEligible)

  for (const config of DEFAULT_ROLL_CONFIGS) {
    const groups = groupByLayerColor(rollEligible)
    for (const group of groups.values()) {
      const first = group[0]
      jobs.push({
        jobId: buildRollJobKey(config.configId, first.sourceLayerName, first.colorKey),
        jobKind: 'roll',
        materialKey: config.configId,
        materialLabel: config.configId,
        sourceLayerName: first.sourceLayerName,
        colorKey: first.colorKey,
        granularity: NESTING_GRANULARITY,
        itemType: 'child-part',
        separationKey: `${first.sourceLayerName ?? 'unassigned'}|${first.colorKey ?? 'unknown'}`,
        items: toInputItems(group),
        materialFrame: {
          materialType: 'roll',
          rollWidthMm: config.rollWidthMm,
          usableWidthMm: config.usableWidthMm,
          feedAxis: 'length',
          crossAxis: 'width',
          packingDirection: 'width-first',
          optimizeFor: 'minimize-consumed-length',
        },
        assignmentSource: 'auto-from-layer-color',
        separationReason: 'source-layer-color-preview',
      })
    }
  }

  for (const config of DEFAULT_SHEET_CONFIGS) {
    const sheetParts = preparedChildParts.filter((part) => isSheetEligible(part, config.configId))
    jobs.push({
      jobId: buildSheetJobKey(config.configId),
      jobKind: 'sheet',
      materialKey: config.configId,
      materialLabel: config.configId,
      sourceLayerName: null,
      colorKey: null,
      granularity: NESTING_GRANULARITY,
      itemType: 'child-part',
      separationKey: `sheet-${config.configId}-preview`,
      items: toInputItems(sheetParts),
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
      assignmentSource: 'default-preview',
      separationReason: 'sheet-config-routing',
    })
  }

  return jobs
}

function buildRollLayout(
  config: (typeof DEFAULT_ROLL_CONFIGS)[number],
  jobs: NestingJobInput[],
): NestingRollLayout {
  const jobLayouts = jobs.map((job) => {
    const prepared = job.items.map((item) => ({
      partId: item.itemId,
      partName: item.itemName,
      itemType: 'child-part' as const,
      sourceLayerId: null,
      sourceLayerName: item.sourceLayerName,
      colorKey: item.colorKey,
      widthMm: item.widthMm,
      heightMm: item.heightMm,
      boundingAreaSqm: item.bounds.boundingAreaSqm,
      canNest: item.canNest,
      preferredSheetConfigId: item.preferredSheetConfigId ?? null,
      materialLabel: item.materialLabel ?? null,
      sourceWarnings: item.sourceWarnings,
    }))

    return runRollNesting(config, prepared, {
      jobId: job.jobId,
      assignmentSource: job.assignmentSource,
      jobKey: job.jobId,
      sourceLayerName: job.sourceLayerName,
      colorKey: job.colorKey,
      itemType: 'child-part',
      separationReason: job.separationReason,
    })
  })

  for (const job of jobLayouts) {
    job.warnings.unshift(
      createNestingWarning(
        'NESTING_ROLL_SEPARATED_BY_LAYER_COLOR',
        'info',
        'Roll nesting is separated by source layer/color so different vinyl colors are not mixed in the same roll job.',
        undefined,
        {
          sourceLayerName: job.sourceLayerName,
          colorKey: job.colorKey,
          separationReason: job.separationReason,
        },
      ),
    )
  }

  return {
    configId: config.configId,
    materialType: 'roll',
    granularity: NESTING_GRANULARITY,
    assignmentSource: 'auto-from-layer-color',
    materialFrame: {
      materialType: 'roll',
      rollWidthMm: config.rollWidthMm,
      usableWidthMm: config.usableWidthMm,
      feedAxis: 'length',
      crossAxis: 'width',
      packingDirection: 'width-first',
      optimizeFor: 'minimize-consumed-length',
    },
    rollWidthMm: config.rollWidthMm,
    usableWidthMm: config.usableWidthMm,
    leftMarginMm: config.leftMarginMm,
    rightMarginMm: config.rightMarginMm,
    partSpacingMm: config.partSpacingMm,
    allowRotation: config.allowRotation,
    jobs: jobLayouts,
    aggregate: {
      jobsCount: jobLayouts.length,
      totalSourceItemsCount: jobLayouts.reduce((acc, job) => acc + job.sourceItemsCount, 0),
      totalPlacedItemsCount: jobLayouts.reduce((acc, job) => acc + job.placedItemsCount, 0),
      totalUnplacedItemsCount: jobLayouts.reduce((acc, job) => acc + job.unplacedItemsCount, 0),
      totalUsedLengthMm: jobLayouts.reduce((acc, job) => acc + job.consumedLengthMm, 0),
    },
  }
}

export function buildNestingReport(partsReport: SvgPartExtractionReport): NestingReport {
  const warnings: NestingReport['warnings'] = [
    createNestingWarning('NESTING_USES_BOUNDING_BOX_ONLY', 'info', 'Nesting MVP uses bounding-box shelf placement only.'),
    createNestingWarning(
      'NESTING_CHILD_PARTS_ONLY',
      'info',
      'Nesting always uses individual child parts. Layer roles (face/backing/cut) are confirmed separately on the layer table.',
    ),
  ]

  const preparedChildParts = prepareChildParts(partsReport)
  const jobInputs = buildJobInputs(preparedChildParts)

  if (partsReport.count === 0) {
    warnings.push(createNestingWarning('NESTING_NO_PARTS', 'warning', 'No parts available for nesting.'))
  }

  const rolls = DEFAULT_ROLL_CONFIGS.map((config) => {
    const rollJobs = jobInputs.filter((job) => job.jobKind === 'roll' && job.materialKey === config.configId)
    return buildRollLayout(config, rollJobs)
  })

  const sheets = DEFAULT_SHEET_CONFIGS.map((config) => {
    const sheetJob = jobInputs.find((job) => job.jobKind === 'sheet' && job.materialKey === config.configId)
    const source = (sheetJob?.items ?? []).map((item) => ({
      partId: item.itemId,
      partName: item.itemName,
      itemType: 'child-part' as const,
      sourceLayerId: null,
      sourceLayerName: item.sourceLayerName,
      colorKey: item.colorKey,
      widthMm: item.widthMm,
      heightMm: item.heightMm,
      boundingAreaSqm: item.bounds.boundingAreaSqm,
      canNest: item.canNest,
      preferredSheetConfigId: item.preferredSheetConfigId ?? null,
      materialLabel: item.materialLabel ?? null,
      sourceWarnings: item.sourceWarnings,
    }))
    const layout = runSheetNesting(config, source)
    layout.assignmentSource = sheetJob?.assignmentSource ?? 'default-preview'
    layout.materialFrame =
      sheetJob?.materialFrame && sheetJob.materialFrame.materialType === 'sheet'
        ? sheetJob.materialFrame
        : {
            materialType: 'sheet',
            sheetLengthMm: config.sheetLengthMm,
            sheetWidthMm: config.sheetWidthMm,
            usableLengthMm: config.usableLengthMm,
            usableWidthMm: config.usableWidthMm,
            feedAxis: 'length',
            crossAxis: 'width',
            packingDirection: 'width-first',
            optimizeFor: 'preserve-continuous-length',
          }
    return layout
  })

  warnings.push(
    createNestingWarning(
      'NESTING_ROLL_SEPARATED_BY_LAYER_COLOR',
      'info',
      'Roll nesting is separated by source layer/color so different vinyl colors are not mixed in the same roll job.',
    ),
  )

  if (preparedChildParts.some((part) => !part.canNest)) {
    warnings.push(createNestingWarning('NESTING_PART_NOT_NESTABLE', 'warning', 'At least one part is marked not nestable.'))
  }

  return {
    strategy: 'bounding-box-shelf',
    generatedAt: new Date().toISOString(),
    inputs: {
      partsCount: preparedChildParts.length,
      nestablePartsCount: preparedChildParts.filter((part) => part.canNest).length,
    },
    jobInputs,
    rolls,
    sheets,
    warnings,
  }
}
