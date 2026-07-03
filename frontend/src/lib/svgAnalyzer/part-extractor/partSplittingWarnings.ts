import { createPartWarning } from './partWarnings'
import type { SvgPartWarning } from './partTypes'

export function partSplitWarning(
  code:
    | 'PART_SPLIT_LOW_CONFIDENCE'
    | 'SUBPATH_BOUNDS_UNAVAILABLE'
    | 'SUBPATH_GROUPING_FALLBACK_USED'
    | 'SUBPATH_CONTAINMENT_AMBIGUOUS'
    | 'SUBPATH_AS_INNER_CONTOUR'
    | 'PART_SPLIT_PRODUCED_LAYER_ONLY'
    | 'PART_SPLIT_PERIMETER_MISMATCH',
  severity: SvgPartWarning['severity'],
  message: string,
  targetId?: string,
  details?: SvgPartWarning['details'],
): SvgPartWarning {
  return createPartWarning(code, severity, message, targetId, details)
}
