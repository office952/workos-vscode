/**
 * Operator Configurare (Intake V6 page 2): hide confirmation/status badge chrome.
 *
 * Product Truth / confirm persistence stay intact — only UI chips, pills, and
 * field-level authority status lines are suppressed. Sticky confirm CTAs remain.
 */
export const INTAKE_V6_OPERATOR_CONFIG_HIDE_STATUS_BADGES = true;

export function intakeV6ShowOperatorConfigStatusBadges(): boolean {
  return !INTAKE_V6_OPERATOR_CONFIG_HIDE_STATUS_BADGES;
}
