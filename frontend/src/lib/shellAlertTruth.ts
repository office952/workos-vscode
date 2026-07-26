/**
 * UI-TRUTH-01C — Shell alert badge honesty.
 * Without a real alerts source, never display mock critical counts as incidents.
 */

export interface ShellAlertLike {
  severity?: string;
  resolvedAt?: string | null;
}

export function resolveShellCriticalCount(
  mockModeEnabled: boolean,
  alerts: ShellAlertLike[],
): number {
  if (!mockModeEnabled) return 0;
  return alerts.filter((a) => a.severity === "critical" && !a.resolvedAt).length;
}
