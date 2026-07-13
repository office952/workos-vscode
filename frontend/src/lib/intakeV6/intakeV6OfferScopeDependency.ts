import type { OfferScopeMode, SoldModuleCode } from "./intakeV6OfferScopeState";

export type SoldScopeDependencySeverity = "blocker" | "confirmation_required" | "warning";

export type SoldScopeDependencyIssue = {
  severity: SoldScopeDependencySeverity;
  code: string;
  message: string;
  capability?: string | null;
};

export type SoldScopeDependencyValidation = {
  valid: boolean;
  valid_for_save: boolean;
  valid_for_confirmation: boolean;
  blockers: SoldScopeDependencyIssue[];
  confirmations_required: SoldScopeDependencyIssue[];
  warnings: SoldScopeDependencyIssue[];
  satisfied_capabilities: string[];
  missing_capabilities: string[];
  resolved_calc_modules: string[];
};

export const CODE_LED_MOUNT_SURFACE_NOT_SOLD = "LED_MOUNT_SURFACE_NOT_SOLD";
export const CODE_ELECTRICAL_LOAD_NOT_SOLD = "ELECTRICAL_LOAD_NOT_SOLD";

const LED_MOUNT_SURFACE = "LED_MOUNT_SURFACE";

function mountSatisfied(sold: Set<SoldModuleCode>): boolean {
  return sold.has("BACK") || (sold.has("FACE") && sold.has("RETURN-CANT"));
}

export function readDependencyConfirmations(payload: Record<string, unknown> | null | undefined): Set<string> {
  const confirmed = payload?.offer_scope_confirmed;
  if (confirmed == null || typeof confirmed !== "object" || Array.isArray(confirmed)) {
    return new Set();
  }
  const codes = (confirmed as Record<string, unknown>).dependency_confirmations;
  if (Array.isArray(codes)) {
    return new Set(codes.map((code) => String(code)).filter(Boolean));
  }
  return new Set();
}

export function readPersistedDependencyValidation(
  payload: Record<string, unknown> | null | undefined,
): SoldScopeDependencyValidation | null {
  const raw = payload?.offer_scope_dependency_validation;
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) {
    return null;
  }
  return raw as SoldScopeDependencyValidation;
}

/** Presentation-only preview for unsaved local scope (mirrors backend rules). */
export function previewSoldScopeDependencyValidation(input: {
  mode: OfferScopeMode;
  soldModules: SoldModuleCode[];
  dependencyConfirmations?: Set<string>;
}): SoldScopeDependencyValidation {
  const sold = new Set(input.soldModules);
  const confirmations = input.dependencyConfirmations ?? new Set<string>();
  const blockers: SoldScopeDependencyIssue[] = [];
  const confirmationsRequired: SoldScopeDependencyIssue[] = [];
  const warnings: SoldScopeDependencyIssue[] = [];
  const satisfiedCapabilities: string[] = [];
  const missingCapabilities: string[] = [];

  if (input.mode === "full_product") {
    return {
      valid: true,
      valid_for_save: true,
      valid_for_confirmation: true,
      blockers: [],
      confirmations_required: [],
      warnings: [],
      satisfied_capabilities: [],
      missing_capabilities: [],
      resolved_calc_modules: [],
    };
  }

  if (sold.size === 0) {
    blockers.push({
      severity: "blocker",
      code: "SOLD_MODULES_EMPTY",
      message: "Selectează cel puțin o componentă pentru scope parțial.",
    });
    return {
      valid: false,
      valid_for_save: false,
      valid_for_confirmation: false,
      blockers,
      confirmations_required: [],
      warnings: [],
      satisfied_capabilities: [],
      missing_capabilities: [],
      resolved_calc_modules: [],
    };
  }

  if (sold.has("LIGHTING")) {
    if (mountSatisfied(sold)) {
      satisfiedCapabilities.push(LED_MOUNT_SURFACE);
    } else {
      missingCapabilities.push(LED_MOUNT_SURFACE);
      if (!confirmations.has(CODE_LED_MOUNT_SURFACE_NOT_SOLD)) {
        confirmationsRequired.push({
          severity: "confirmation_required",
          code: CODE_LED_MOUNT_SURFACE_NOT_SOLD,
          message:
            "Iluminarea necesita un suport de montaj. Selecteaza Spate sau confirma ca suportul este existent/furnizat de client.",
          capability: LED_MOUNT_SURFACE,
        });
      }
    }
  }

  if (sold.has("ELECTRICAL") && !sold.has("LIGHTING")) {
    if (!confirmations.has(CODE_ELECTRICAL_LOAD_NOT_SOLD)) {
      const issue: SoldScopeDependencyIssue = {
        severity: "confirmation_required",
        code: CODE_ELECTRICAL_LOAD_NOT_SOLD,
        message:
          "Electrica este selectata fara Iluminare. Confirma ca sarcina LED este existenta sau furnizata separat.",
      };
      confirmationsRequired.push(issue);
      warnings.push({ ...issue, severity: "warning" });
    }
  }

  const validForConfirmation = blockers.length === 0 && confirmationsRequired.length === 0;
  return {
    valid: validForConfirmation,
    valid_for_save: blockers.length === 0,
    valid_for_confirmation: validForConfirmation,
    blockers,
    confirmations_required: confirmationsRequired,
    warnings,
    satisfied_capabilities: satisfiedCapabilities,
    missing_capabilities: missingCapabilities,
    resolved_calc_modules: [],
  };
}

export function isOfferScopeDependencyReady(payload: Record<string, unknown> | undefined): boolean {
  const persisted = readPersistedDependencyValidation(payload);
  if (persisted) {
    return persisted.valid_for_confirmation;
  }
  return true;
}

export function firstDependencyBlockerMessage(
  validation: SoldScopeDependencyValidation | null,
): string | null {
  if (!validation) return null;
  const issue = validation.blockers[0] ?? validation.confirmations_required[0];
  return issue?.message ?? null;
}
