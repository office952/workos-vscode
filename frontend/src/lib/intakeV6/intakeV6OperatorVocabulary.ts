/**
 * Operator-facing Romanian vocabulary for Intake V6 (Page 1 + Page 2).
 * Raw internal tokens may remain in advanced/debug contexts only.
 */

export type OperatorSeverityTone =
  | "informational"
  | "needs_check"
  | "warning"
  | "blocker"
  | "confirmed"
  | "unconfirmed"
  | "owner_decision";

const READINESS_LABELS: Record<string, string> = {
  LOCAL_CONFIGURATION_REQUIRED: "Necesită configurare locală",
  OWNER_GATE_REQUIRED: "Necesită confirmarea administratorului",
  READY: "Pregătit",
  CONFIRMED: "Confirmat",
  COMPLETE: "Complet",
  INCOMPLETE: "Incomplet",
  PENDING: "În așteptare",
  DRAFT: "Ciornă",
  ACTIVE: "Activ",
  INACTIVE: "Inactiv",
  PROPOSED: "Propus",
  REJECTED: "Respins",
  UNCONFIRMED: "Neconfirmat",
  INFORMATIONAL_ONLY: "Informativ",
  PREVIEW_ONLY: "Doar previzualizare",
  MANUAL_CONFIRMATION_REQUIRED: "Necesită confirmare manuală",
  PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED: "Necesită setarea inițială a profilului (admin)",
  SHELL_COMMON_WITH_ZONE_INTENTS: "Shell comun cu intenții pe zonă",
  DIRECT_220V: "Alimentare directă 220V",
  SHARED_FROM_PANEL: "Alimentare din alt panou",
  SEGMENT_PROPOSED: "Propunere segmentare",
  SEGMENT_CONFIRMED: "Ansamblu segmentat confirmat",
};

const GATE_PATH_LABELS: Record<string, string> = {
  mounting_method_status: "Metodă de montaj",
  cable_passage_status: "Trecere cablu",
  electrical_interface_status: "Interfață electrică",
  led_configuration_status: "Configurație LED",
  psu_configuration_status: "Sursă LED (putere)",
  plexiglas_status: "Plexiglas",
  tolerance_status: "Toleranțe",
};

const SEVERITY_LABELS: Record<OperatorSeverityTone, string> = {
  informational: "Informativ",
  needs_check: "Necesită verificare",
  warning: "Avertizare",
  blocker: "Blocant",
  confirmed: "Confirmat",
  unconfirmed: "Neconfirmat",
  owner_decision: "Necesită decizie owner/admin",
};

function humanizeToken(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "—";
  if (READINESS_LABELS[trimmed]) return READINESS_LABELS[trimmed];
  if (GATE_PATH_LABELS[trimmed]) return GATE_PATH_LABELS[trimmed];
  // Snake / screaming-snake → spaced Romanian-ish fallback without leaking all-caps.
  if (/^[A-Z0-9_]+$/.test(trimmed) && trimmed.includes("_")) {
    return trimmed
      .toLowerCase()
      .split("_")
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  }
  return trimmed;
}

/** Map readiness / status tokens for primary operator UI. */
export function operatorReadinessLabelRo(raw: string | null | undefined): string {
  if (raw == null || !String(raw).trim()) return "—";
  return humanizeToken(String(raw));
}

/** Map owner-gate path keys for primary UI. */
export function operatorGatePathLabelRo(raw: string | null | undefined): string {
  if (raw == null || !String(raw).trim()) return "—";
  const key = String(raw).trim();
  return GATE_PATH_LABELS[key] || humanizeToken(key);
}

/** Map gate status for primary UI. */
export function operatorGateStatusLabelRo(raw: string | null | undefined): string {
  return operatorReadinessLabelRo(raw);
}

export function operatorSeverityLabelRo(tone: OperatorSeverityTone): string {
  return SEVERITY_LABELS[tone];
}

export function looksLikeRawInternalToken(value: string | null | undefined): boolean {
  if (!value) return false;
  const v = value.trim();
  if (!v) return false;
  if (v.includes("OWNER_GATE")) return true;
  if (/^[A-Z][A-Z0-9_]{2,}$/.test(v) && v.includes("_")) return true;
  return false;
}

/** True when a readiness/status implies owner/admin decision (not a technical failure). */
export function isOwnerDecisionStatus(raw: string | null | undefined): boolean {
  const v = String(raw || "").toUpperCase();
  return v.includes("OWNER_GATE") || v === "OWNER_GATE_REQUIRED";
}

export const OPERATOR_VOCAB_SEVERITY = SEVERITY_LABELS;

const BINDING_STATUS_LABELS: Record<string, string> = {
  suggested: "Propunere",
  confirmed: "Confirmat",
  draft: "Ciornă",
  reconfirm_required: "Necesită reconfirmare",
  unbound: "Neasociat",
  selected: "Selectat",
};

const COMPOSITION_ROLE_LABELS: Record<string, string> = {
  linked_logo_segment: "Segment logo legat",
  volumetric_letters: "Litere volumetrice",
  volumetric_logo: "Logo volumetric",
  support_panel: "Fundal / suport",
};

/** Binding / component association status for primary UI. */
export function operatorBindingStatusLabelRo(raw: string | null | undefined): string {
  if (raw == null || !String(raw).trim()) return "—";
  const key = String(raw).trim().toLowerCase();
  return BINDING_STATUS_LABELS[key] || operatorReadinessLabelRo(raw);
}

export function operatorCompositionRoleLabelRo(raw: string | null | undefined): string {
  if (raw == null || !String(raw).trim()) return "Componentă";
  const key = String(raw).trim();
  return COMPOSITION_ROLE_LABELS[key] || COMPOSITION_ROLE_LABELS[key.toLowerCase()] || key;
}

/** Guard flag on bindables — not a failure; optional technical constraint. */
export function operatorGuardedLabelRo(): string {
  return "Necesită verificare tehnică";
}

export function page1HandoffReadyMessage(): string {
  return "Analiza este pregătită. Pe Pagina 2 vei configura finisajele, iluminarea și montajul pentru componentele confirmate.";
}

export function page1HandoffPendingMessage(pendingCount: number): string {
  const n = Math.max(0, pendingCount);
  if (n === 1) {
    return "Mai este 1 element care necesită confirmare înainte de configurare.";
  }
  return `Mai sunt ${n} elemente care necesită confirmare înainte de configurare.`;
}

export function page1HandoffBlockedMessage(): string {
  return "Nu poți continua până când rezolvi elementele marcate ca blocante.";
}
