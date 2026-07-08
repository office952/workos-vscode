import type { FormSystemBackboneFieldProjection } from "./formSystemBackboneFieldProjection";
import type { FormSystemBackboneBlocker, FormSystemBackboneReadiness } from "./intakeV6ModularFormContractTypes";

export interface RuntimeReadinessPolicyDecision {
  fieldKey: string;
  originalState: string;
  overlayState: string;
  fieldStateChanged: boolean;
  canRelaxFieldWarning: boolean;
  canRelaxGlobalBlocker: boolean;
  reason: string;
  trace: Record<string, unknown>;
}

export interface EvaluateRuntimeOverlayReadinessPolicyInput {
  originalProjection: FormSystemBackboneFieldProjection[];
  overlaidProjection: FormSystemBackboneFieldProjection[];
  backboneReadiness?: FormSystemBackboneReadiness | null;
}

const EXCLUDED_FIELD_KEYS = new Set([
  "lighting.psu_configuration",
  "material.led_psu",
  "materials.led_psu",
]);

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function blockerList(readiness: FormSystemBackboneReadiness | null | undefined): FormSystemBackboneBlocker[] {
  return Array.isArray(readiness?.blockers) ? readiness!.blockers! : [];
}

function isBroadGlobalBlocker(blocker: FormSystemBackboneBlocker): boolean {
  const fieldKey = text(blocker.field_key);
  if (!fieldKey) return true;
  return fieldKey === "readiness.product_truth_blockers";
}

function isStateConfirmable(originalState: string, overlayState: string): boolean {
  return (originalState === "missing" || originalState === "suggested") && overlayState === "confirmed";
}

function canRelaxFieldWarningFor(
  originalProjection: FormSystemBackboneFieldProjection,
  overlaidProjection: FormSystemBackboneFieldProjection,
): boolean {
  if (originalProjection.isConfirmedTruth || !overlaidProjection.isConfirmedTruth) return false;
  if (originalProjection.state === "hydrated" || originalProjection.state === "fallback") return false;
  return isStateConfirmable(originalProjection.state, overlaidProjection.state);
}

function decisionReason(params: {
  canRelaxFieldWarning: boolean;
  canRelaxGlobalBlocker: boolean;
  matchingBlockers: FormSystemBackboneBlocker[];
  broadBlockers: FormSystemBackboneBlocker[];
  changed: boolean;
}): string {
  if (!params.changed) return "Overlay did not change this field state; keep readiness unchanged.";
  if (!params.canRelaxFieldWarning) return "Overlay does not establish confirmed truth for this field; keep warnings active.";
  if (params.canRelaxGlobalBlocker && params.matchingBlockers.length > 0) {
    return "Overlay confirms the same field key; matching field-addressed blocker may be visually relaxed, but backbone remains source.";
  }
  if (params.broadBlockers.length > 0) {
    return "Overlay confirms the field row, but broad/global backbone blockers remain active by default.";
  }
  if (params.matchingBlockers.length > 0) {
    return "Overlay confirms the field row, but blocker relaxation still requires explicit field-addressed handling by the caller.";
  }
  return "Overlay confirms the field row only; no blocker relaxation is implied.";
}

export function evaluateRuntimeOverlayReadinessPolicy(
  input: EvaluateRuntimeOverlayReadinessPolicyInput,
): RuntimeReadinessPolicyDecision[] {
  const originalByKey = new Map<string, FormSystemBackboneFieldProjection>();
  for (const projection of input.originalProjection) {
    if (!EXCLUDED_FIELD_KEYS.has(projection.fieldKey)) {
      originalByKey.set(projection.fieldKey, projection);
    }
  }

  const blockers = blockerList(input.backboneReadiness);

  return input.overlaidProjection.flatMap((overlaidProjection) => {
    if (EXCLUDED_FIELD_KEYS.has(overlaidProjection.fieldKey)) return [];
    const originalProjection = originalByKey.get(overlaidProjection.fieldKey);
    if (!originalProjection) return [];

    const matchingBlockers = blockers.filter((blocker) => text(blocker.field_key) === overlaidProjection.fieldKey);
    const broadBlockers = blockers.filter((blocker) => isBroadGlobalBlocker(blocker));
    const fieldStateChanged = originalProjection.state !== overlaidProjection.state;
    const canRelaxFieldWarning = canRelaxFieldWarningFor(originalProjection, overlaidProjection);
    const canRelaxGlobalBlocker =
      canRelaxFieldWarning &&
      matchingBlockers.length > 0 &&
      broadBlockers.length === 0;

    return [
      {
        fieldKey: overlaidProjection.fieldKey,
        originalState: originalProjection.state,
        overlayState: overlaidProjection.state,
        fieldStateChanged,
        canRelaxFieldWarning,
        canRelaxGlobalBlocker,
        reason: decisionReason({
          canRelaxFieldWarning,
          canRelaxGlobalBlocker,
          matchingBlockers,
          broadBlockers,
          changed: fieldStateChanged,
        }),
        trace: {
          originalSourceKind: originalProjection.sourceKind,
          overlaySourceKind: overlaidProjection.sourceKind,
          originalConfirmedTruth: originalProjection.isConfirmedTruth,
          overlayConfirmedTruth: overlaidProjection.isConfirmedTruth,
          matchingBlockerCodes: matchingBlockers
            .map((blocker) => text(blocker.blocker_code))
            .filter((value): value is string => Boolean(value)),
          broadBlockerCodes: broadBlockers
            .map((blocker) => text(blocker.blocker_code))
            .filter((value): value is string => Boolean(value)),
          blockerFieldKeys: blockers
            .map((blocker) => text(blocker.field_key))
            .filter((value): value is string => Boolean(value)),
        },
      },
    ];
  });
}