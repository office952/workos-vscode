import type {
  IntakeV6ProductTruthPromotionPlannerResponse,
  IntakeV6RuntimeCaptureReadModelResponse,
} from "./intakeV6Api";
import { buildGuidanceStickySummaryTitle } from "./intakeV6OperatorGuidance";
import type { ReviewHandoffSurfacing } from "./intakeV6QuoteHandoffReadiness";

export const INTAKE_V6_REVIEW_DIAGNOSTIC_ANCHOR_ID = "intake-v6-review-diagnostic-tehnic";

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
  MOUNTING_SOLUTION_MISSING:
    "Soluția de montaj lipsește. Alege șablon montaj (fără ACM/metal) sau o structură de suport în tab-ul Montaj.",
  MOUNTING_SOLUTION_INVALID:
    "Soluția de montaj selectată nu este validă. Alege metal, ACM casetat sau șablon montaj.",
};

export type OperatorBlockerBannerSeverity = "blocked" | "attention";

export type OperatorBlockerBannerIssue = {
  id: string;
  severity: "blocker" | "warning";
  code: string | null;
  message: string;
  action: string | null;
  focusTarget: string | null;
  /** Optional Review tab to open before focusing a section. */
  tabId?: "finisaje" | "iluminare" | "montaj" | "layers" | null;
};

export type OperatorBlockerBannerDisplay = {
  show: boolean;
  loading: boolean;
  /** Compact title — same count language as footer guidance spine */
  summaryTitle: string;
  blockerCount: number;
  warningCount: number;
  severity: OperatorBlockerBannerSeverity;
  issues: OperatorBlockerBannerIssue[];
  /** @deprecated prefer issues — kept for transitional callers */
  messages: string[];
  hasTechnicalBlockers: boolean;
};

export type OperatorBlockerBannerInput = {
  surfacing: ReviewHandoffSurfacing;
  handoffLoading?: boolean;
  runtimeModel?: IntakeV6RuntimeCaptureReadModelResponse | null;
  runtimeLoading?: boolean;
  plannerModel?: IntakeV6ProductTruthPromotionPlannerResponse | null;
  plannerLoading?: boolean;
  /** When true with empty missing-line keys, surface diagnostic inconsistency (not critical). */
  missingPriceFlagWithoutRows?: boolean;
  missingPriceLineKeys?: string[];
  /** Extra final-confirmation issues (composition, segmented shell, …). */
  extraIssues?: OperatorBlockerBannerIssue[];
};

function mapRuntimeBlockerCode(code: string): string {
  const trimmed = code.trim();
  if (!trimmed) return "";
  if (RUNTIME_BLOCKER_OPERATOR_MESSAGES[trimmed]) {
    return RUNTIME_BLOCKER_OPERATOR_MESSAGES[trimmed];
  }
  if (trimmed.startsWith("runtime_capture:")) {
    const inner = trimmed.slice("runtime_capture:".length);
    if (RUNTIME_BLOCKER_OPERATOR_MESSAGES[inner]) {
      return RUNTIME_BLOCKER_OPERATOR_MESSAGES[inner];
    }
  }
  return "";
}

/** Runtime/API may omit or reshape nested blocker lists (e.g. backbone fail-closed rows). */
export function asBlockerCodeList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const codes: string[] = [];
  for (const item of value) {
    if (typeof item === "string" && item.trim()) {
      codes.push(item.trim());
    }
  }
  return codes;
}

function asObjectList(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is Record<string, unknown> => !!item && typeof item === "object");
}

export function collectRuntimeBlockerCodes(
  model: IntakeV6RuntimeCaptureReadModelResponse | null | undefined,
): string[] {
  if (!model) return [];
  const codes = new Set<string>();
  for (const field of asObjectList(model.fields)) {
    for (const code of asBlockerCodeList(field.blockers)) {
      codes.add(code);
    }
  }
  for (const row of asObjectList(model.blockers)) {
    for (const code of asBlockerCodeList(row.blockers)) {
      codes.add(code);
    }
  }
  return [...codes];
}

function collectPlannerBlockerCodes(
  model: IntakeV6ProductTruthPromotionPlannerResponse | null | undefined,
): string[] {
  if (!model) return [];
  const codes = new Set<string>();
  for (const row of asObjectList(model.blockers)) {
    for (const code of asBlockerCodeList(row.blockers)) {
      codes.add(code);
    }
  }
  for (const entry of asObjectList(model.blocked_entries)) {
    for (const code of asBlockerCodeList(entry.blockers)) {
      codes.add(code);
    }
  }
  return [...codes];
}

function focusForCode(code: string): string | null {
  if (code.includes("MOUNTING")) return "intake-v6-mounting-solution-selector";
  if (code.includes("LAYER_ROLES") || code.includes("SELECTED_LAYER")) return null;
  return INTAKE_V6_REVIEW_DIAGNOSTIC_ANCHOR_ID;
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
    missingPriceFlagWithoutRows = false,
    missingPriceLineKeys = [],
    extraIssues = [],
  } = input;

  const issues: OperatorBlockerBannerIssue[] = [];
  const seen = new Set<string>();

  const pushIssue = (issue: OperatorBlockerBannerIssue) => {
    const key = `${issue.severity}:${issue.code ?? ""}:${issue.message}`;
    if (seen.has(key)) return;
    seen.add(key);
    issues.push(issue);
  };

  for (const issue of extraIssues) {
    pushIssue(issue);
  }

  const runtimeCodes = collectRuntimeBlockerCodes(runtimeModel);
  const plannerCodes = collectPlannerBlockerCodes(plannerModel);
  const technicalCodes = [...new Set([...runtimeCodes, ...plannerCodes])];

  for (const code of technicalCodes) {
    const mapped = mapRuntimeBlockerCode(code);
    if (!mapped) {
      // Prefer exact code text over generic fallback when unmapped.
      pushIssue({
        id: `tech-${code}`,
        severity: "blocker",
        code,
        message: `Blocaj tehnic: ${code}`,
        action: "Deschide Detalii tehnice și diagnostic.",
        focusTarget: focusForCode(code),
      });
      continue;
    }
    pushIssue({
      id: `tech-${code}`,
      severity: "blocker",
      code,
      message: mapped,
      action: code.includes("MOUNTING")
        ? "Completează Montaj: șablon + soluție (sentinel sau ACM/metal)."
        : "Rezolvă câmpul marcat în Review / Pasul 1.",
      focusTarget: focusForCode(code),
    });
  }

  if (surfacing.showBanner) {
    const actions = surfacing.actions ?? [];
    surfacing.reasons.forEach((reason, index) => {
      const isMissingTariff = /fără tarif|fara tarif/i.test(reason);
      const isResidual = /neconfirmat|neclasificat|vector|artwork/i.test(reason);
      const severity: "blocker" | "warning" =
        isMissingTariff || isResidual || /avertisment|atenț/i.test(reason)
          ? "warning"
          : "blocker";
      // Missing-tariff with no concrete lines → diagnostic warning, not critical.
      if (isMissingTariff && missingPriceFlagWithoutRows && missingPriceLineKeys.length === 0) {
        pushIssue({
          id: `surf-tariff-diag-${index}`,
          severity: "warning",
          code: "contains_missing_prices_inconsistent",
          message:
            "Semnal tarif lipsă fără linii neprețuite identificate — verificare diagnostică (nu blochează ca tarif lipsă real).",
          action: "Verifică Calcul live; corectarea numerică este în auditul de pricing.",
          focusTarget: "intake-v6-live-calculation-summary",
        });
        return;
      }
      if (isMissingTariff && missingPriceLineKeys.length > 0) {
        pushIssue({
          id: `surf-tariff-${index}`,
          severity: "warning",
          code: "contains_missing_prices",
          message: `Linii fără tarif: ${missingPriceLineKeys.slice(0, 5).join(", ")}`,
          action: actions[index] ?? "Verifică liniile cu tarif lipsă în Calcul live.",
          focusTarget: "intake-v6-live-calculation-summary",
        });
        return;
      }
      pushIssue({
        id: `surf-${index}`,
        severity,
        code: isResidual ? "unclassified_vector_artwork_requires_decision" : null,
        message: reason,
        action: actions[index] ?? null,
        focusTarget: isResidual ? "intake-v6-artwork-finishes" : null,
      });
    });
  }

  const blockerCount = issues.filter((i) => i.severity === "blocker").length;
  const warningCount = issues.filter((i) => i.severity === "warning").length;
  const show = issues.length > 0;
  const loading =
    !show &&
    ((handoffLoading && !surfacing.showBanner && surfacing.reasons.length === 0) ||
      (runtimeLoading && runtimeModel == null));
  const severity: OperatorBlockerBannerSeverity =
    blockerCount > 0 ? "blocked" : "attention";

  return {
    show,
    loading: loading && !show,
    // Same count language as footer guidance spine (one model).
    summaryTitle: buildGuidanceStickySummaryTitle(blockerCount, warningCount),
    blockerCount,
    warningCount,
    severity,
    issues,
    messages: issues.map((i) => i.message),
    hasTechnicalBlockers: technicalCodes.length > 0,
  };
}

/** @deprecated — generic fallback removed; kept only for test migration detection */
export const OPERATOR_BLOCKER_BANNER_MAX_MESSAGES = 99;

type BreakdownPriceRow = {
  material_key?: string | null;
  key?: string | null;
  unit_price?: number | null;
  estimated_cost?: number | null;
  material_cost?: number | null;
};

/**
 * Concrete line keys with no unit/estimated price.
 * Used so `contains_missing_prices` only becomes "diagnostic inconsistent"
 * when the flag is true AND this list is empty (plan: empty-hit + flag).
 */
export function collectMissingPriceLineKeysFromBreakdown(breakdown: {
  material_rows?: BreakdownPriceRow[] | null;
  consumable_rows?: BreakdownPriceRow[] | null;
  operation_rows?: BreakdownPriceRow[] | null;
  edge_cant_operation_rows?: BreakdownPriceRow[] | null;
} | null | undefined): string[] {
  if (!breakdown) return [];
  const keys: string[] = [];
  const consider = (row: BreakdownPriceRow) => {
    const key = row.material_key ?? row.key ?? null;
    if (!key) return;
    const unit = row.unit_price;
    const cost = row.estimated_cost ?? row.material_cost;
    if (unit == null && cost == null) keys.push(key);
  };
  for (const row of breakdown.material_rows ?? []) consider(row);
  for (const row of breakdown.consumable_rows ?? []) consider(row);
  for (const row of breakdown.operation_rows ?? []) consider(row);
  for (const row of breakdown.edge_cant_operation_rows ?? []) consider(row);
  return [...new Set(keys)];
}
