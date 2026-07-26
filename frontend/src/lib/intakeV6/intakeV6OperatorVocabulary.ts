/**
 * Operator-facing Romanian vocabulary for Intake V6 (Page 1 + Page 2).
 * Raw internal tokens may remain in advanced/debug contexts only.
 *
 * Status presentation rule:
 *   internal state → IntakeV6StatusSemantic → operatorStatusSemanticRo → UI
 */

/** Canonical operator status meanings (presentation only — not domain contracts). */
export type IntakeV6StatusSemantic =
  | "proposal"
  | "needs_operator"
  | "missing_data"
  | "warning"
  | "blocker"
  | "owner_decision"
  | "confirmed"
  | "ready"
  | "rejected"
  | "inactive"
  | "informational";

const STATUS_SEMANTIC_LABELS: Record<IntakeV6StatusSemantic, string> = {
  proposal: "Propunere",
  needs_operator: "Necesită confirmare",
  missing_data: "Lipsă date",
  warning: "Avertizare",
  blocker: "Blocant",
  owner_decision: "Decizie administrator",
  confirmed: "Confirmat",
  ready: "Pregătit",
  rejected: "Respins",
  inactive: "Inactiv",
  informational: "Informativ",
};

/** Romanian label for a canonical status semantic. */
export function operatorStatusSemanticRo(semantic: IntakeV6StatusSemantic): string {
  return STATUS_SEMANTIC_LABELS[semantic];
}

/**
 * Map a known internal / readiness token to a canonical semantic.
 * Returns null when the token is not a status (domain config noun, unknown phrase).
 */
export function resolveOperatorStatusSemantic(
  raw: string | null | undefined,
): IntakeV6StatusSemantic | null {
  if (raw == null || !String(raw).trim()) return null;
  const key = String(raw).trim();
  const upper = key.toUpperCase();

  if (upper.includes("OWNER_GATE") || upper === "OWNER_GATE_REQUIRED") return "owner_decision";
  if (upper === "PROPOSED" || upper === "SEGMENT_PROPOSED" || key === "suggested") return "proposal";
  if (upper === "CONFIRMED" || upper === "SEGMENT_CONFIRMED" || key === "confirmed" || upper === "COMPLETE") {
    return "confirmed";
  }
  if (upper === "READY" || upper === "ACTIVE") return "ready";
  if (upper === "REJECTED" || key === "rejected") return "rejected";
  if (upper === "INACTIVE") return "inactive";
  if (
    upper === "UNCONFIRMED" ||
    upper === "PENDING" ||
    upper === "DRAFT" ||
    upper === "INCOMPLETE" ||
    upper === "MANUAL_CONFIRMATION_REQUIRED" ||
    upper === "LOCAL_CONFIGURATION_REQUIRED" ||
    key === "draft" ||
    key === "reconfirm_required" ||
    key === "pending"
  ) {
    return "needs_operator";
  }
  if (upper === "WARNING" || upper === "ATTENTION" || upper === "GUARDED") return "warning";
  if (upper === "BLOCKER" || upper === "BLOCKED" || upper === "CRITICAL" || upper === "FATAL") {
    return "blocker";
  }
  if (upper === "INFORMATIONAL_ONLY" || upper === "PREVIEW_ONLY" || upper === "INFO") {
    return "informational";
  }
  if (upper === "MISSING" || upper === "MISSING_DATA") return "missing_data";

  return null;
}

export type OperatorSeverityTone =
  | "informational"
  | "needs_check"
  | "warning"
  | "blocker"
  | "confirmed"
  | "unconfirmed"
  | "owner_decision";

const READINESS_LABELS: Record<string, string> = {
  LOCAL_CONFIGURATION_REQUIRED: STATUS_SEMANTIC_LABELS.needs_operator,
  OWNER_GATE_REQUIRED: STATUS_SEMANTIC_LABELS.owner_decision,
  READY: STATUS_SEMANTIC_LABELS.ready,
  CONFIRMED: STATUS_SEMANTIC_LABELS.confirmed,
  COMPLETE: STATUS_SEMANTIC_LABELS.confirmed,
  INCOMPLETE: STATUS_SEMANTIC_LABELS.needs_operator,
  PENDING: STATUS_SEMANTIC_LABELS.needs_operator,
  DRAFT: STATUS_SEMANTIC_LABELS.needs_operator,
  ACTIVE: STATUS_SEMANTIC_LABELS.ready,
  INACTIVE: STATUS_SEMANTIC_LABELS.inactive,
  PROPOSED: STATUS_SEMANTIC_LABELS.proposal,
  REJECTED: STATUS_SEMANTIC_LABELS.rejected,
  /** Select / config option wording — not a severity badge. */
  UNCONFIRMED: "Neconfirmat",
  INFORMATIONAL_ONLY: STATUS_SEMANTIC_LABELS.informational,
  PREVIEW_ONLY: "Doar previzualizare",
  MANUAL_CONFIRMATION_REQUIRED: STATUS_SEMANTIC_LABELS.needs_operator,
  PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED: STATUS_SEMANTIC_LABELS.owner_decision,
  SHELL_COMMON_WITH_ZONE_INTENTS: "Shell comun cu intenții pe zonă",
  DIRECT_220V: "Alimentare directă 220V",
  SHARED_FROM_PANEL: "Alimentare din alt panou",
  SEGMENT_PROPOSED: STATUS_SEMANTIC_LABELS.proposal,
  SEGMENT_CONFIRMED: STATUS_SEMANTIC_LABELS.confirmed,
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
  informational: STATUS_SEMANTIC_LABELS.informational,
  needs_check: STATUS_SEMANTIC_LABELS.warning,
  warning: STATUS_SEMANTIC_LABELS.warning,
  blocker: STATUS_SEMANTIC_LABELS.blocker,
  confirmed: STATUS_SEMANTIC_LABELS.confirmed,
  unconfirmed: STATUS_SEMANTIC_LABELS.needs_operator,
  owner_decision: STATUS_SEMANTIC_LABELS.owner_decision,
};

function humanizeToken(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "—";
  if (READINESS_LABELS[trimmed]) return READINESS_LABELS[trimmed];
  if (GATE_PATH_LABELS[trimmed]) return GATE_PATH_LABELS[trimmed];
  if (trimmed.toUpperCase().includes("OWNER_GATE")) {
    return STATUS_SEMANTIC_LABELS.owner_decision;
  }
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

/** Safe primary-UI label for an internal status token (never leaks raw OWNER_GATE_*). */
export function operatorStatusLabelRo(raw: string | null | undefined): string {
  if (raw == null || !String(raw).trim()) return "—";
  const key = String(raw).trim();
  // Domain config option: keep "Neconfirmat" (not a severity badge).
  if (key.toUpperCase() === "UNCONFIRMED") return READINESS_LABELS.UNCONFIRMED;
  const semantic = resolveOperatorStatusSemantic(key);
  if (semantic) return operatorStatusSemanticRo(semantic);
  return humanizeToken(key);
}

/** Map readiness / status tokens for primary operator UI. */
export function operatorReadinessLabelRo(raw: string | null | undefined): string {
  if (raw == null || !String(raw).trim()) return "—";
  const key = String(raw).trim();
  if (READINESS_LABELS[key]) return READINESS_LABELS[key];
  const semantic = resolveOperatorStatusSemantic(key);
  if (semantic) {
    // UNCONFIRMED as readiness option stays "Neconfirmat" via READINESS_LABELS above.
    if (key.toUpperCase() === "UNCONFIRMED") return READINESS_LABELS.UNCONFIRMED;
    return operatorStatusSemanticRo(semantic);
  }
  return humanizeToken(key);
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
  suggested: STATUS_SEMANTIC_LABELS.proposal,
  confirmed: STATUS_SEMANTIC_LABELS.confirmed,
  draft: STATUS_SEMANTIC_LABELS.needs_operator,
  reconfirm_required: STATUS_SEMANTIC_LABELS.needs_operator,
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
  return STATUS_SEMANTIC_LABELS.warning;
}

/** Page 1 layer confirmation text (proposal vs accepted). Icon aria uses needs_operator separately. */
export function layerConfirmationStateLabelRo(state: string | null | undefined): string {
  if (state === "confirmed") return operatorStatusSemanticRo("confirmed");
  if (state === "rejected") return operatorStatusSemanticRo("rejected");
  if (state === "ignored") return "Ignorat";
  return operatorStatusSemanticRo("proposal");
}

/** Page 1 status-icon aria: pending means operator action, not "proposal" wording. */
export function layerStatusIconLabelRo(state: string | null | undefined): string {
  if (state === "confirmed") return operatorStatusSemanticRo("confirmed");
  if (state === "ignored") return "Ignorat";
  return operatorStatusSemanticRo("needs_operator");
}

/** Finisaje letter-group card badge (`ok` = confirmed, `warning` = missing required color). */
export function finishLetterCardStatusLabelRo(status: "ok" | "warning" | null | undefined): string | null {
  if (status === "ok") return operatorStatusSemanticRo("confirmed");
  if (status === "warning") return operatorStatusSemanticRo("missing_data");
  return null;
}

/** Artwork finish card badge. */
export function artworkFinishStatusLabelRo(args: {
  confirmed: boolean;
  stepOneConfirmed: boolean;
}): { label: string; semantic: IntakeV6StatusSemantic } {
  if (args.confirmed) {
    return { label: operatorStatusSemanticRo("confirmed"), semantic: "confirmed" };
  }
  // Role done on Page 1 but finish still open — action required, not "already confirmed".
  if (args.stepOneConfirmed) {
    return { label: operatorStatusSemanticRo("needs_operator"), semantic: "needs_operator" };
  }
  return { label: operatorStatusSemanticRo("needs_operator"), semantic: "needs_operator" };
}

/** Segmented background assembly status badge. */
export function segmentedAssemblyStatusLabelRo(status: string | null | undefined): string {
  const upper = String(status || "").toUpperCase();
  if (upper === "PROPOSED") return operatorStatusSemanticRo("proposal");
  if (upper === "CONFIRMED") return operatorStatusSemanticRo("confirmed");
  if (upper === "REJECTED") return operatorStatusSemanticRo("rejected");
  if (upper === "INACTIVE") return operatorStatusSemanticRo("inactive");
  if (upper === "SINGLE_PANEL") return "Un panou";
  return "—";
}

/** Electrical assembly badge (not supply-mode select options). */
export function electricalAssemblyStatusLabelRo(status: string | null | undefined): string {
  const upper = String(status || "").toUpperCase();
  if (upper === "CONFIRMED") return operatorStatusSemanticRo("confirmed");
  return operatorStatusSemanticRo("needs_operator");
}

/** Confirmare consolidated indicator. */
export function confirmConsolidatedIndicatorLabelRo(
  tier: "blocked" | "attention" | "ready" | "informational",
): string {
  if (tier === "blocked") return operatorStatusSemanticRo("blocker");
  if (tier === "attention") return operatorStatusSemanticRo("warning");
  if (tier === "ready") return operatorStatusSemanticRo("ready");
  return "Recapitulare";
}

/** Workspace / review header aggregate when no problems. */
export function workspaceReadyAggregateLabelRo(): string {
  return operatorStatusSemanticRo("ready");
}

/** Detail row "all good" value (SVG/pricing ready — not business Confirmat). */
export function workspaceDetailReadyValueRo(): string {
  return operatorStatusSemanticRo("ready");
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

/** Finish ownership domain tokens — primary UI uses RO; raw stays in technical details. */
const FINISH_OWNERSHIP_DOMAIN_LABELS: Record<string, string> = {
  SURFACE_FINISH: "Finisaj suprafață",
  "RETURN-CANT": "Finisaj cant",
  RETURN_CANT: "Finisaj cant",
  WORKSPACE: "Valori din workspace",
  FINISH: "Finisaj (scope ofertă)",
};

export function operatorFinishOwnershipDomainLabelRo(raw: string | null | undefined): string {
  if (raw == null || !String(raw).trim()) return "—";
  const key = String(raw).trim();
  return FINISH_OWNERSHIP_DOMAIN_LABELS[key] || FINISH_OWNERSHIP_DOMAIN_LABELS[key.toUpperCase()] || "Necesită verificare";
}

export function finishOwnershipTechnicalHintRo(): string {
  return "Opțional — sursă de adevăr și mapări interne";
}

export function finishOwnershipTechnicalTitleRo(): string {
  return "Detalii tehnice despre finisaj";
}
