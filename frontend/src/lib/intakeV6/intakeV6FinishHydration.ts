export * from "./intakeV4FinishHydration";

// Legacy V4-compat exports. ReviewStep now uses intakeV6ReviewRefetchDomains.ts
// instead of the old workspace-revision refetch key.
export {
  INTAKE_V4_PENDING_SAVE_BANNER as INTAKE_V6_PENDING_SAVE_BANNER,
  intakeV4PersistedReviewRefetchKey as intakeV6PersistedReviewRefetchKey,
  isIntakeV4SelectorStatePendingSave as isIntakeV6SelectorStatePendingSave,
} from "./intakeV4FinishHydration";
