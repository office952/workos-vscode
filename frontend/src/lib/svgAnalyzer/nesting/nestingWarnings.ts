import type { NestingWarning } from './nestingTypes'

export function createNestingWarning(
  code: string,
  severity: NestingWarning['severity'],
  message: string,
  targetId?: string,
  details?: NestingWarning['details'],
): NestingWarning {
  return {
    code,
    severity,
    message,
    scope: targetId ? 'part' : 'nesting',
    targetId,
    details,
  }
}
