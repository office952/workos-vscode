import type { SvgPartWarning } from './partTypes'

export function createPartWarning(
  code: string,
  severity: SvgPartWarning['severity'],
  message: string,
  targetId?: string,
  details?: SvgPartWarning['details'],
): SvgPartWarning {
  return {
    code,
    severity,
    message,
    scope: targetId ? 'part' : 'parts',
    targetId,
    details,
  }
}
