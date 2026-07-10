import type {
  IntakeV6ProductTruthPromotionPlannerResponse,
  IntakeV6RuntimeCaptureReadModelResponse,
} from "./intakeV6Api";
import type { ReviewHandoffSurfacing } from "./intakeV6QuoteHandoffReadiness";

export const INTAKE_V6_REVIEW_DIAGNOSTIC_ANCHOR_ID = "intake-v6-review-diagnostic-tehnic";

export const OPERATOR_BLOCKER_BANNER_MAX_MESSAGES = 3;

const GENERIC_TECHNICAL_BLOCKER_MESSAGE =
  "Există blocaje tehnice care trebuie verificate în Diagnostic tehnic.";

const RUNTIME_BLOCKER_OPERATOR_MESSAGES: Record<string, string> = {
  SELECTED_LAYER_REFS_MISSING:
    "Referințele straturilor selectate lipsesc. Verifică selecția straturilor în Pasul 1.",
  SELECTED_LAYER_REFS_UNCONFIRMED:
    "Referințele straturilor selectate nu sunt confirmate. Revino la Pasul 1.",
  SELECTED_LAYER_REFS_AMBIGUOUS:
    "Referințele straturilor selectate sunt ambigue. Clarifică selecția în Pasul 1.",
  SUPPORT_TYPE_MISSING:
    "Tipul de suport/montaj lipsește. Completează setările relevante în Review.",
  PRODUCT_TRUTH_INCOMPLETE:
    "Product Truth incomplet. Verifică câmpurile obligatorii înainte de confirmare.",
  LAYER_ROLES_INCOMPLETE:
    "Rolurile straturilor trebuie confirmate în Pasul 1.",
};

export type OperatorBlockerBannerSeverity = "blocked" | "attention";

export type OperatorBlockerBannerDisplay = {
  show: boolean;
  loading: boolean;
  messages: string[];
  severity: OperatorBlockerBannerSeverity;
  hasTechnicalBlockers: boolean;
};

export type OperatorBlockerBannerInput = {
  surfacing: ReviewHandoffSurfacing;
  handoffLoading?: boolean;
  runtimeModel?: IntakeV6RuntimeCaptureReadModelResponse | null;
  runtimeLoading?: boolean;
  plannerModel?: IntakeV6ProductTruthPromotionPlannerResponse | null;
  plannerLoading?: boolean;
};

function mapRuntimeBlockerCode(code: string): string {
  const trimmed = code.trim();
  if (!trimmed) return "";
  return RUNTIME_BLOCKER_OPERATOR_MESSAGES[trimmed] ?? "";
}

function collectRuntimeBlockerCodes(
  model: IntakeV6RuntimeCaptureReadModelResponse | null | undefined,
): string[] {
  if (!model) return [];
  const codes = new Set<string>();
  for (const field of model.fields) {
    for (const code of field.blockers) {
      if (code.trim()) codes.add(code.trim());
    }
  }
  for (const row of model.blockers) {
    for (const code of row.blockers) {
      if (code.trim()) codes.add(code.trim());
    }
  }
  return [...codes];
}

function collectPlannerBlockerCodes(
  model: IntakeV6ProductTruthPromotionPlannerResponse | null | undefined,
): string[] {
  if (!model) return [];
  const codes = new Set<string>();
  for (const row of model.blockers) {
    for (const code of row.blockers) {
      if (code.trim()) codes.add(code.trim());
    }
  }
  for (const entry of model.blocked_entries) {
    for (const code of entry.blockers) {
      if (code.trim()) codes.add(code.trim());
    }
  }
  return [...codes];
}

function pushUniqueMessage(messages: string[], seen: Set<string>, message: string): boolean {
  const normalized = message.trim();
  if (!normalized || seen.has(normalized)) return false;
  if (messages.length >= OPERATOR_BLOCKER_BANNER_MAX_MESSAGES) return false;
  seen.add(normalized);
  messages.push(normalized);
  return true;
}

export function buildOperatorBlockerBannerDisplay(
  input: OperatorBlockerBannerInput,
): OperatorBlockerBannerDisplay {
  const {
    surfacing,
    handoffLoading = false,
    runtimeModel = null,
    runtimeLoading = false,
    plannerModel = null,
    plannerLoading = false,
  } = input;

  const messages: string[] = [];
  const seen = new Set<string>();

  if (surfacing.showBanner) {
    for (const reason of surfacing.reasons) {
      if (!pushUniqueMessage(messages, seen, reason)) break;
    }
  }

  const runtimeCodes = collectRuntimeBlockerCodes(runtimeModel);
  const plannerCodes = collectPlannerBlockerCodes(plannerModel);
  const technicalCodes = [...new Set([...runtimeCodes, ...plannerCodes])];
  let mappedTechnicalCount = 0;

  for (const code of technicalCodes) {
    const mapped = mapRuntimeBlockerCode(code);
    if (mapped && pushUniqueMessage(messages, seen, mapped)) {
      mappedTechnicalCount += 1;
    }
    if (messages.length >= OPERATOR_BLOCKER_BANNER_MAX_MESSAGES) break;
  }

  const hasUnmappedTechnical = technicalCodes.some((code) => !mapRuntimeBlockerCode(code));
  if (
    technicalCodes.length > 0 &&
    mappedTechnicalCount === 0 &&
    messages.length < OPERATOR_BLOCKER_BANNER_MAX_MESSAGES
  ) {
    pushUniqueMessage(messages, seen, GENERIC_TECHNICAL_BLOCKER_MESSAGE);
  } else if (
    hasUnmappedTechnical &&
    mappedTechnicalCount > 0 &&
    messages.length < OPERATOR_BLOCKER_BANNER_MAX_MESSAGES &&
    !seen.has(GENERIC_TECHNICAL_BLOCKER_MESSAGE)
  ) {
    pushUniqueMessage(messages, seen, GENERIC_TECHNICAL_BLOCKER_MESSAGE);
  }

  const hasTechnicalBlockers = technicalCodes.length > 0;
  const show = messages.length > 0;
  const loading =
    !show &&
    ((handoffLoading && !surfacing.showBanner && surfacing.reasons.length === 0) ||
      (runtimeLoading && runtimeModel == null));
  const severity: OperatorBlockerBannerSeverity =
    hasTechnicalBlockers || surfacing.showBanner ? "blocked" : "attention";

  return {
    show,
    loading: loading && !show,
    messages,
    severity,
    hasTechnicalBlockers,
  };
}
