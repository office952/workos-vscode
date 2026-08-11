export type IntakeV6ReviewDirtyDomain =
  | "lighting"
  | "face_finish"
  | "artwork_finish"
  | "backing"
  | "mounting"
  | "template"
  | "commercial_preview"
  | "sheet_footprint";

export type IntakeV6ReviewRefetchGroup =
  | "breakdown"
  | "pricing"
  | "pricedQuote"
  | "productionDryRun"
  | "productionHandoff"
  | "quoteHandoff"
  | "taskGeneration"
  | "taskPreview"
  | "orderBoundReadiness";

/**
 * Step 2 (configure) offer-critical refetch groups.
 * Production / task / order-bound diagnostics refresh only when the diagnostic
 * drawer opens (or Confirm loads its own handoff batch) — not on every finish save.
 */
export const INTAKE_V6_STEP2_OFFER_CRITICAL_GROUPS = [
  "breakdown",
  "pricing",
  "pricedQuote",
  "quoteHandoff",
] as const satisfies readonly IntakeV6ReviewRefetchGroup[];

/** Production / execution diagnostics — lazy / on-demand only. */
export const INTAKE_V6_STEP2_PRODUCTION_DIAGNOSTIC_GROUPS = [
  "productionDryRun",
  "productionHandoff",
  "taskGeneration",
  "taskPreview",
  "orderBoundReadiness",
] as const satisfies readonly IntakeV6ReviewRefetchGroup[];

const STEP2_OFFER_CRITICAL: readonly IntakeV6ReviewRefetchGroup[] = INTAKE_V6_STEP2_OFFER_CRITICAL_GROUPS;

const DOMAIN_TO_GROUPS: Record<IntakeV6ReviewDirtyDomain, readonly IntakeV6ReviewRefetchGroup[]> = {
  lighting: STEP2_OFFER_CRITICAL,
  face_finish: STEP2_OFFER_CRITICAL,
  artwork_finish: STEP2_OFFER_CRITICAL,
  backing: STEP2_OFFER_CRITICAL,
  mounting: STEP2_OFFER_CRITICAL,
  template: STEP2_OFFER_CRITICAL,
  commercial_preview: ["pricing", "pricedQuote"],
  sheet_footprint: STEP2_OFFER_CRITICAL,
};

export function resolveIntakeV6ReviewRefetchGroups(
  domains: Iterable<IntakeV6ReviewDirtyDomain>,
): IntakeV6ReviewRefetchGroup[] {
  const groups = new Set<IntakeV6ReviewRefetchGroup>();
  for (const domain of domains) {
    for (const group of DOMAIN_TO_GROUPS[domain] ?? []) {
      groups.add(group);
    }
  }
  return [...groups];
}
