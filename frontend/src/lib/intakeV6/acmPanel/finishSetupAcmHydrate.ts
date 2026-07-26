/**
 * Hydrate AcmPanel-owned finish_setup fields for Review form round-trip.
 * Omitting these on hydrate → autosave wipes measured production_geometry bindings.
 */

function asObject(value: unknown): Record<string, unknown> | null {
  if (value != null && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

export type AcmPanelFinishHydrateFields = {
  acm_panel_instance: Record<string, unknown> | null;
  svg_support_selection: Record<string, unknown> | null;
  segmented_background: Record<string, unknown> | null;
};

/** Pick AcmPanel transport fields from raw finish_setup without inventing defaults. */
export function hydrateAcmPanelFinishFields(
  setup: Record<string, unknown> | null | undefined,
): AcmPanelFinishHydrateFields {
  const src = setup ?? {};
  return {
    acm_panel_instance: asObject(src.acm_panel_instance),
    svg_support_selection: asObject(src.svg_support_selection),
    segmented_background: asObject(src.segmented_background),
  };
}

/**
 * Merge hydrated AcmPanel fields onto a finish form draft.
 * Does not touch unrelated finish keys (face/return/lighting/etc.).
 */
export function mergeAcmPanelFinishHydrate<T extends Record<string, unknown>>(
  finishDraft: T,
  setup: Record<string, unknown> | null | undefined,
): T & AcmPanelFinishHydrateFields {
  const acm = hydrateAcmPanelFinishFields(setup);
  return {
    ...finishDraft,
    ...acm,
  };
}
