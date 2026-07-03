import type { ProductTemplateComponent } from "@/lib/api";
import type { ProductAggregate } from "@/api/productAggregate";

export const PROVENANCE_LABELS: Record<string, string> = {
  parent: "Parent template",
  dossier: "Blueprint dossier",
  linked_module: "Linked module",
  derived: "Derived",
  registry: "Registry",
  missing: "Missing",
  conflict: "Conflict",
};

export function isSyntheticAutoComponent(component: ProductTemplateComponent): boolean {
  return component.component_id === "comp_auto_1" || Boolean(component._needs_review);
}

export function shouldPreferAggregateDisplay(
  draftComponents: ProductTemplateComponent[],
  aggregate: ProductAggregate | null | undefined
): boolean {
  if (!aggregate || aggregate.components.length === 0) {
    return false;
  }
  if (draftComponents.length === 0) {
    return true;
  }
  if (draftComponents.length === 1 && isSyntheticAutoComponent(draftComponents[0])) {
    return true;
  }
  return draftComponents.every(isSyntheticAutoComponent);
}

export function getAggregateDisplayCounts(aggregate: ProductAggregate) {
  const totals = aggregate.provenance_summary?.aggregate_totals ?? {};
  return {
    components: totals.components ?? aggregate.components.length,
    operations: totals.operations ?? aggregate.operations.length,
    materials: totals.materials ?? aggregate.materials.length,
  };
}

export function resolveDisplayCounts(
  draftCounts: { components: number; operations: number; materials: number },
  aggregate: ProductAggregate | null | undefined,
  preferAggregate: boolean
) {
  if (preferAggregate && aggregate) {
    return getAggregateDisplayCounts(aggregate);
  }
  return draftCounts;
}

export function hasParentComponentsEmptyWarning(aggregate: ProductAggregate | null | undefined): boolean {
  return Boolean(aggregate?.warnings?.some((w) => w.code === "PARENT_COMPONENTS_EMPTY"));
}

export function provenanceBadgeClass(provenance: string): string {
  switch (provenance) {
    case "dossier":
      return "bg-emerald-900/30 text-emerald-300 border-emerald-700/40";
    case "linked_module":
      return "bg-blue-900/30 text-blue-300 border-blue-700/40";
    case "parent":
      return "bg-amber-900/30 text-amber-300 border-amber-700/40";
    case "missing":
    case "conflict":
      return "bg-red-900/30 text-red-300 border-red-700/40";
    default:
      return "bg-slate-800 text-slate-400 border-slate-700/40";
  }
}
