/**
 * Operational Registry operation-code resolution — shared bridge for
 * ProductSystem aliases → registry mappings (read-only display/eligibility).
 */
import type {
  EligibleEmployeePool,
  OperationResourceMapping,
} from "@/api/operationalRegistry";

export type OperationResolutionKind = "direct" | "alias" | "missing";

export interface OperationResolutionResult {
  originalOperationCode: string;
  resolvedOperationCode: string | null;
  resolution: OperationResolutionKind;
  matchedAlias: string | null;
  mapping: OperationResourceMapping | null;
  warning: string | null;
}

export function normalizeOperationCode(code: string): string {
  return (code || "").toLowerCase().replace(/[-\s]/g, "_");
}

export function resolveMappingFromList(
  operationCode: string,
  mappings: OperationResourceMapping[]
): OperationResolutionResult {
  const original = (operationCode || "").trim();
  const norm = normalizeOperationCode(original);

  if (!norm) {
    return {
      originalOperationCode: original,
      resolvedOperationCode: null,
      resolution: "missing",
      matchedAlias: null,
      mapping: null,
      warning: "Cod operație lipsă — mapping registry neconfirmat.",
    };
  }

  const direct = mappings.find(
    (m) => normalizeOperationCode(m.operation_code) === norm
  );
  if (direct) {
    return {
      originalOperationCode: original,
      resolvedOperationCode: direct.operation_code,
      resolution: "direct",
      matchedAlias: null,
      mapping: direct,
      warning: null,
    };
  }

  for (const m of mappings) {
    const aliases = m.product_system_aliases ?? [];
    const matched = aliases.find((a) => normalizeOperationCode(a) === norm);
    if (matched) {
      return {
        originalOperationCode: original,
        resolvedOperationCode: m.operation_code,
        resolution: "alias",
        matchedAlias: matched,
        mapping: m,
        warning: null,
      };
    }
  }

  return {
    originalOperationCode: original,
    resolvedOperationCode: null,
    resolution: "missing",
    matchedAlias: null,
    mapping: null,
    warning: `Mapping registry lipsă pentru ${original} — eligibilitate neconfirmată (guard soft).`,
  };
}

export function resolveOperationFromPool(
  pool: EligibleEmployeePool
): OperationResolutionResult {
  const original = pool.operation_code;
  const resolved = pool.resolved_operation_code;
  const resolutionRaw = (pool.resolution || "").toLowerCase();

  if (resolutionRaw === "not_found" || !resolved) {
    return {
      originalOperationCode: original,
      resolvedOperationCode: null,
      resolution: "missing",
      matchedAlias: null,
      mapping: null,
      warning: `Mapping registry lipsă pentru ${original} — eligibilitate neconfirmată (guard soft).`,
    };
  }

  const resolution: OperationResolutionKind =
    resolutionRaw === "alias" ? "alias" : "direct";

  return {
    originalOperationCode: original,
    resolvedOperationCode: resolved,
    resolution,
    matchedAlias: resolution === "alias" ? original : null,
    mapping: null,
    warning: null,
  };
}

export function formatOperationResolutionLabel(params: {
  originalOperationCode: string;
  resolvedOperationCode?: string | null;
  authorizationMode?: string | null;
  eligibleCount?: number | null;
}): string {
  const {
    originalOperationCode,
    resolvedOperationCode,
    authorizationMode,
    eligibleCount,
  } = params;

  const parts: string[] = [`Operație: ${originalOperationCode}`];

  if (
    resolvedOperationCode &&
    normalizeOperationCode(resolvedOperationCode) !==
      normalizeOperationCode(originalOperationCode)
  ) {
    parts[0] = `Operație: ${originalOperationCode} → ${resolvedOperationCode}`;
  }

  if (authorizationMode) {
    parts.push(`mode: ${authorizationMode}`);
  }

  if (eligibleCount != null) {
    parts.push(`${eligibleCount} eligibili`);
  }

  return parts.join(" · ");
}
