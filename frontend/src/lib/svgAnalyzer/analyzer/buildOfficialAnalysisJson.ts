import { ANALYSIS_SCHEMA_NAME, ANALYSIS_SCHEMA_VERSION } from './buildAnalysisReport'
import type { SvgAnalysisCoreReport, SvgAnalysisJson } from './types'
import type { ArtworkComplexityReport } from './artworkComplexityAssessment'
import type { SvgPartExtractionReport } from '../part-extractor/partTypes'
import type { NestingReport } from '../nesting/nestingTypes'

export function buildOfficialAnalysisJson(
  report: SvgAnalysisCoreReport,
  partsReport: SvgPartExtractionReport,
  nestingReport: NestingReport,
  artworkComplexity?: ArtworkComplexityReport,
  exportedBy = 'local-user',
): SvgAnalysisJson {
  return {
    ...report,
    artworkComplexity,
    parts: partsReport,
    nesting: nestingReport,
    schemaName: ANALYSIS_SCHEMA_NAME,
    schemaVersion: ANALYSIS_SCHEMA_VERSION,
    exportMeta: {
      ...report.exportMeta,
      exportedAt: new Date().toISOString(),
      exportedBy,
      schemaVersion: ANALYSIS_SCHEMA_VERSION,
    },
  }
}
