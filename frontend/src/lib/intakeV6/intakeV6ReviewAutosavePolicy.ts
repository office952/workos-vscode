/**
 * Intake V6 Step 2 Review autosave timing policy.
 *
 * Discrete selectors (dropdown / radio / toggle / catalog) must not wait on the
 * legacy 700–1400 ms floors before PUT finish-setup. Continuous numeric typing
 * keeps a safer debounce so keystrokes do not storm the network.
 */

export type IntakeV6ReviewAutosavePolicy = "short" | "long";

/** Discrete selector coalescing window (ms). Target: 0–150. */
export const INTAKE_V6_SELECTOR_AUTOSAVE_SHORT_MS = 100;

/**
 * Continuous numeric / template-area typing debounce (ms).
 * Prefer 500–800; long sticky latch uses this value (not the legacy 1400 floor).
 */
export const INTAKE_V6_SELECTOR_AUTOSAVE_LONG_MS = 700;

/** Commercial slider (markup / discount / manual) debounce (ms). */
export const INTAKE_V6_COMMERCIAL_INPUTS_AUTOSAVE_MS = 700;

/** Resolve debounce for the selector autosave effect from the sticky policy latch. */
export function resolveIntakeV6ReviewAutosaveDebounceMs(
  policy: IntakeV6ReviewAutosavePolicy,
): number {
  return policy === "long"
    ? INTAKE_V6_SELECTOR_AUTOSAVE_LONG_MS
    : INTAKE_V6_SELECTOR_AUTOSAVE_SHORT_MS;
}
