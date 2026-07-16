/**
 * Step 3 internal-draft confirmation hydration helpers.
 * Persisted backend truth is authoritative; local checkbox state must reconcile to it.
 */

export type InternalDraftConfirmationHydration = {
  /** True once at least one persisted source is available. */
  resolved: boolean;
  /** Persisted confirmation value (false only when resolved). */
  confirmed: boolean;
  /** Disable checkbox while truth is unresolved or a save is in flight. */
  disableInteraction: boolean;
};

export function resolveInternalDraftConfirmationHydration(args: {
  hasFinishSetup: boolean;
  finishSetupConfirmed: boolean | null | undefined;
  hasHandoffPreview: boolean;
  handoffOperatorComplete: boolean | null | undefined;
  previewLoading: boolean;
  saving: boolean;
}): InternalDraftConfirmationHydration {
  // While preview is loading/refreshing, prefer workspace finish_setup so upstream resets
  // apply immediately and stale handoff snapshots cannot keep a false-checked UI.
  if (args.previewLoading && args.hasFinishSetup) {
    return {
      resolved: true,
      confirmed: args.finishSetupConfirmed === true,
      disableInteraction: true,
    };
  }
  if (args.hasHandoffPreview) {
    return {
      resolved: true,
      confirmed: args.handoffOperatorComplete === true,
      disableInteraction: args.saving,
    };
  }
  if (args.hasFinishSetup) {
    return {
      resolved: true,
      confirmed: args.finishSetupConfirmed === true,
      disableInteraction: args.saving,
    };
  }
  return {
    resolved: false,
    confirmed: false,
    disableInteraction: true,
  };
}

/**
 * Whether a fetched confirmation snapshot may overwrite local checkbox state.
 * Blocks overwrite while saving and when the response generation is stale.
 */
export function shouldApplyConfirmationSnapshot(args: {
  saving: boolean;
  responseGeneration: number;
  latestGeneration: number;
}): boolean {
  if (args.saving) return false;
  if (args.responseGeneration !== args.latestGeneration) return false;
  return true;
}

/**
 * After a failed PUT, restore to the last known persisted value (never invent true).
 */
export function restoreConfirmationAfterFailedPut(args: {
  handoffOperatorComplete: boolean | null | undefined;
  finishSetupConfirmed: boolean | null | undefined;
  hasHandoffPreview: boolean;
  hasFinishSetup: boolean;
}): boolean {
  if (args.hasHandoffPreview) return args.handoffOperatorComplete === true;
  if (args.hasFinishSetup) return args.finishSetupConfirmed === true;
  return false;
}

/**
 * Effective checkbox checked state for display.
 * Unresolved hydration must not present unchecked as settled persisted truth.
 */
export function resolveConfirmationCheckboxChecked(args: {
  hydration: InternalDraftConfirmationHydration;
  localConfirmed: boolean;
}): boolean {
  if (!args.hydration.resolved) return false;
  return args.localConfirmed === true && args.hydration.confirmed === true
    ? true
    : args.localConfirmed;
}

/**
 * Prefer displaying hydrated persisted truth once resolved and local has been reconciled.
 * When local and persisted diverge briefly during optimistic save, local wins until save ends.
 */
export function reconcileLocalConfirmationWithPersisted(args: {
  saving: boolean;
  localConfirmed: boolean;
  persistedConfirmed: boolean;
  hydrationResolved: boolean;
}): boolean {
  if (!args.hydrationResolved) return args.localConfirmed;
  if (args.saving) return args.localConfirmed;
  return args.persistedConfirmed;
}
