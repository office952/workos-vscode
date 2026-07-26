import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { analyzeSvgString } from '../../svgAnalyzer'
import { GOLDEN_GRADI_SVG_FACTS } from './goldenSvgFacts.expect'

const FIXTURE_SVG = path.resolve(
  __dirname,
  '../../../../../backend/tests/fixtures/intake_v6_golden_gradi/gradi-curat.svg',
)

describe('Build1 golden SVG facts (gradi-curat nest2)', () => {
  it('matches file identity', () => {
    const bytes = readFileSync(FIXTURE_SVG)
    const hash = createHash('sha256').update(bytes).digest('hex')
    expect(bytes.length).toBe(GOLDEN_GRADI_SVG_FACTS.source.fileSizeBytes)
    expect(hash).toBe(GOLDEN_GRADI_SVG_FACTS.source.fileHash)
  })

  it('analyzer emits golden layer/color/geometry counts without ACM', () => {
    const text = readFileSync(FIXTURE_SVG, 'utf8')
    const { report } = analyzeSvgString(
      text,
      GOLDEN_GRADI_SVG_FACTS.source.fileName,
      GOLDEN_GRADI_SVG_FACTS.source.fileSizeBytes,
    )
    expect(report.layers).toHaveLength(GOLDEN_GRADI_SVG_FACTS.report.layersCount)
    expect(report.colors.unique).toHaveLength(GOLDEN_GRADI_SVG_FACTS.report.colorsUniqueCount)
    expect(report.colors.unique).toEqual([...GOLDEN_GRADI_SVG_FACTS.report.colorsUnique])
    expect(report.geometry.closedSubPathCount).toBe(GOLDEN_GRADI_SVG_FACTS.report.closedSubpathCount)
    expect(Math.round(report.document.widthMm)).toBe(GOLDEN_GRADI_SVG_FACTS.report.widthMmApprox)
    expect(Math.round(report.document.heightMm)).toBe(GOLDEN_GRADI_SVG_FACTS.report.heightMmApprox)
    expect(report.layers.map((l) => l.id)).toEqual([...GOLDEN_GRADI_SVG_FACTS.report.layerIds])

    const buckets: Record<string, number> = {}
    for (const layer of report.layers) {
      const role = layer.autoRole || 'unknown'
      buckets[role] = (buckets[role] || 0) + 1
    }
    expect(buckets).toEqual(GOLDEN_GRADI_SVG_FACTS.report.autoRoleBuckets)
    expect(buckets.support_panel).toBeUndefined()
    expect(GOLDEN_GRADI_SVG_FACTS.report.acmDeclared).toBe(false)
  })
})
