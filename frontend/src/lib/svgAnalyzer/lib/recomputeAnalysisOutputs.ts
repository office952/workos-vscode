import type { SvgAnalysisCoreReport } from '../analyzer/types'
import type { LayerRoleConfirmation } from '../analyzer/layerRoleTypes'
import type { ParsedSvgDocument } from '../analyzer/types'
import { buildOfficialAnalysisJson } from '../analyzer/buildOfficialAnalysisJson'
import type { SvgAnalysisReport } from '../analyzer/types'
import { buildNestingReport } from '../nesting'
import { extractParts, type ExtractPartsOptions } from '../part-extractor'

export function recomputePartsAndNesting(
  coreReport: SvgAnalysisCoreReport,
  parsed: ParsedSvgDocument,
  layerRoleConfirmation: LayerRoleConfirmation,
  options?: ExtractPartsOptions,
): SvgAnalysisReport {
  const confirmationMerged: LayerRoleConfirmation = layerRoleConfirmation
  const partsReport = extractParts(coreReport, parsed, {
    ...options,
    layerRoleConfirmation: confirmationMerged,
  })
  const nestingReport = buildNestingReport(partsReport)
  return buildOfficialAnalysisJson(
    { ...coreReport, layerRoleConfirmation: confirmationMerged },
    partsReport,
    nestingReport,
  )
}

export function stripPartsAndNesting(report: SvgAnalysisReport): SvgAnalysisCoreReport {
  const { parts: _parts, nesting: _nesting, ...core } = report
  return core
}
