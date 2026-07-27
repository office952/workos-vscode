/**
 * Production-release blocker presentation (W6-T03).
 * Display-only mapping — backend remains authority for blocking classification.
 */
import type { OwnerDecisionSummaryItem, OperatorTaskTruthResponse } from "@/api/operatorTaskTruth";

export type OwnerDecisionDisplayItem = OwnerDecisionSummaryItem;

/** Display labels when backend label is generic. Never used to reclassify blocking. */
export const OWNER_DECISION_DISPLAY_FALLBACK: Record<
  string,
  { label: string; requiredAction?: string; impact?: string }
> = {
  INTERNAL_SABLON_FOREX_COST: {
    label: "Cost / regula sablon Forex neconfirmata",
    requiredAction: "Necesita rezolvare inainte de productie",
  },
  INTERNAL_MONTAJ_RULE: {
    label: "Regula de montaj neconfirmata",
    requiredAction: "Necesita rezolvare inainte de productie",
  },
  INTERNAL_CONSUMABLES_RULE: {
    label: "Regula consumabile neconfirmata",
    requiredAction: "Necesita rezolvare inainte de productie",
  },
  INTERNAL_AMBALARE_RULE: {
    label: "Regula de ambalare nefinalizata",
    impact: "Informativ intern — nu blocheaza pornirea",
  },
  OVERHEAD_ALLOCATION_PENDING: {
    label: "Alocare costuri indirecte in asteptare",
    impact: "Informativ intern — nu blocheaza pornirea",
  },
};

export function decisionDisplayLabel(item: OwnerDecisionSummaryItem): string {
  const backend = item.label?.trim();
  if (backend && !backend.startsWith("INTERNAL_")) return backend;
  const fallback = OWNER_DECISION_DISPLAY_FALLBACK[item.code];
  return fallback?.label || backend || item.code;
}

export function decisionRequiredAction(item: OwnerDecisionSummaryItem): string | null {
  if (item.required_action?.trim()) return item.required_action;
  const fallback = OWNER_DECISION_DISPLAY_FALLBACK[item.code];
  if (item.blocking) return fallback?.requiredAction || "Necesita rezolvare inainte de productie";
  return fallback?.impact || null;
}

export function splitOwnerDecisions(decisions: OwnerDecisionSummaryItem[]) {
  const blocking = decisions.filter((d) => d.blocking);
  const nonblocking = decisions.filter((d) => !d.blocking);
  return { blocking, nonblocking };
}

export function unresolvedBlockingCount(decisions: OwnerDecisionSummaryItem[]): number {
  return decisions.filter(
    (d) => d.blocking && d.operational_status !== "resolved" && d.operational_status !== "acknowledged",
  ).length;
}

export function productionReleaseStatusLabel(status: string, blocked: boolean): string {
  if (blocked || status === "RELEASE_BLOCKED_OWNER_DECISIONS") {
    return "Producție blocată";
  }
  if (status === "RELEASE_ALLOWED") return "Producție permisă";
  return status.replace(/_/g, " ");
}

export function frozenStatusLabel(status: string): string {
  const normalized = status?.trim() || "present";
  if (normalized === "present") return "Decizie initiala: prezenta in snapshot";
  return `Decizie initiala: ${normalized}`;
}

export function operationalStatusLabel(status: string): string {
  const map: Record<string, string> = {
    unresolved: "Stare operationala: nerezolvata",
    acknowledged: "Stare operationala: confirmata",
    resolved: "Stare operationala: rezolvata",
  };
  return map[status] || `Stare operationala: ${status}`;
}

export function productionScopeLabel(scope?: string | null): string {
  if (scope === "ORDER_SCOPE" || scope === "order") return "Intreaga comanda";
  return scope || "Intreaga comanda";
}

export function productionPolicyExplanation(policy: string): string {
  if (policy === "ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED") {
    return "Comanda si planul pot exista, dar pornirea task-urilor de productie este blocata pana la rezolvarea deciziilor.";
  }
  return policy;
}

export type StructuredActionError = {
  code: string;
  rawCode: string;
  httpStatus: number;
  message: string;
  detail: string | null;
  blockers: Array<Record<string, unknown>>;
  readinessLabel?: string | null;
  raw: unknown;
};

export function parseStructuredActionError(
  httpStatus: number,
  body: unknown,
): StructuredActionError {
  const envelope =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail: unknown }).detail
      : body;

  let rawCode = "unknown";
  let message = `Actiune esuata (${httpStatus})`;
  let detail: string | null = null;
  let blockers: Array<Record<string, unknown>> = [];
  let readinessLabel: string | null = null;

  if (envelope && typeof envelope === "object") {
    const rec = envelope as Record<string, unknown>;
    const err = typeof rec.error === "string" ? rec.error : null;
    const innerCode = typeof rec.code === "string" ? rec.code : null;
    rawCode = innerCode || err || "unknown";
    if (typeof rec.message === "string") message = rec.message;
    if (typeof rec.detail === "string") detail = rec.detail;
    if (Array.isArray(rec.blockers)) {
      blockers = rec.blockers.filter((b) => b && typeof b === "object") as Array<
        Record<string, unknown>
      >;
    }
    if (typeof rec.readiness_label === "string") readinessLabel = rec.readiness_label;
  }

  return {
    code: rawCode,
    rawCode,
    httpStatus,
    message,
    detail,
    blockers,
    readinessLabel,
    raw: body,
  };
}

export function structuredErrorHeadline(error: StructuredActionError): string {
  if (error.code === "production_release_blocked") {
    return "Pornire blocata — decizii owner de productie nerezolvate";
  }
  if (error.code === "task_not_ready") {
    return "Pornire blocata — task nepregatit operational";
  }
  if (error.code === "ORDER_SNAPSHOT_V2_MISSING") {
    return "Snapshot V2 lipsa — productia nu poate continua";
  }
  if (error.code === "ORDER_SNAPSHOT_V2_CORRUPT") {
    return "Snapshot V2 corupt — contactati administratorul";
  }
  if (error.httpStatus === 403) return "Actiune nepermisa pentru rolul curent";
  return error.message;
}

export function blockerLabelFromStructured(blocker: Record<string, unknown>): string {
  const code = typeof blocker.code === "string" ? blocker.code : "";
  const label = typeof blocker.label === "string" ? blocker.label : "";
  if (label && !label.startsWith("INTERNAL_")) return label;
  return OWNER_DECISION_DISPLAY_FALLBACK[code]?.label || label || code || "Blocaj necunoscut";
}

export function summarizeTaskTruthProduction(truth: OperatorTaskTruthResponse | null) {
  if (!truth) return null;
  const { blocking, nonblocking } = splitOwnerDecisions(truth.owner_decisions_summary);
  return {
    blocked: truth.production_release_blocked,
    status: truth.production_release_status,
    policy: truth.production_release_policy,
    unresolvedCount: unresolvedBlockingCount(truth.owner_decisions_summary),
    blocking,
    nonblocking,
    capabilities: truth.role_capabilities,
  };
}
