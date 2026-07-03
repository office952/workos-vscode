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

const DOMAIN_TO_GROUPS: Record<IntakeV6ReviewDirtyDomain, readonly IntakeV6ReviewRefetchGroup[]> = {
  lighting: ["breakdown", "pricing", "pricedQuote", "productionDryRun", "productionHandoff", "quoteHandoff", "taskPreview", "orderBoundReadiness"],
  face_finish: ["breakdown", "pricing", "pricedQuote", "productionDryRun", "productionHandoff", "quoteHandoff", "taskPreview", "orderBoundReadiness"],
  artwork_finish: ["breakdown", "pricing", "pricedQuote", "productionDryRun", "productionHandoff", "quoteHandoff", "taskPreview", "orderBoundReadiness"],
  backing: ["breakdown", "pricing", "pricedQuote", "productionDryRun", "productionHandoff", "quoteHandoff", "taskPreview", "orderBoundReadiness"],
  mounting: ["breakdown", "pricing", "pricedQuote", "productionDryRun", "productionHandoff", "quoteHandoff", "taskGeneration", "orderBoundReadiness"],
  template: ["breakdown", "pricing", "pricedQuote", "productionDryRun", "productionHandoff", "quoteHandoff", "taskGeneration", "taskPreview", "orderBoundReadiness"],
  commercial_preview: ["pricing", "pricedQuote"],
  sheet_footprint: ["breakdown", "pricing", "pricedQuote", "productionDryRun", "productionHandoff", "quoteHandoff", "taskGeneration", "taskPreview", "orderBoundReadiness"],
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