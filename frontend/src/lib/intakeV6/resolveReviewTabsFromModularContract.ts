import { Layers, Lightbulb, Wrench, type LucideIcon } from "lucide-react";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";
import type { IntakeV6ReviewTabDefinition, IntakeV6ReviewTabId } from "./intakeV6ProductPlugin";

const TAB_ICONS: Record<IntakeV6ReviewTabId, LucideIcon> = {
  finisaje: Layers,
  iluminare: Lightbulb,
  montaj: Wrench,
};

const FALLBACK_HINTS: Record<IntakeV6ReviewTabId, string> = {
  finisaje: "Față · cant · Vector Logo",
  iluminare: "LED · surse litere",
  montaj: "Fundal · carcasă · site",
};

const CANONICAL_TAB_LABELS: Record<IntakeV6ReviewTabId, string> = {
  finisaje: "Finisaje",
  iluminare: "Iluminare și surse",
  montaj: "Montaj",
};

/**
 * Build 2 — Review tabs composed from modular form contract render_sections.
 * Returns null when composition_authority is absent so callers can fall back to plugin tabs.
 */
export function resolveReviewTabsFromModularContract(
  contract: IntakeV6ModularFormContractResponse | null | undefined,
): IntakeV6ReviewTabDefinition[] | null {
  if (!contract?.summary?.composition_authority) {
    return null;
  }
  const sections = [...(contract.render_sections ?? [])]
    .filter((section) => section.drives_review_tab && section.ui_tab_id)
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  const tabs: IntakeV6ReviewTabDefinition[] = [];
  const seen = new Set<string>();
  for (const section of sections) {
    const id = section.ui_tab_id as IntakeV6ReviewTabId | undefined;
    if (!id || seen.has(id)) continue;
    if (id !== "finisaje" && id !== "iluminare" && id !== "montaj") continue;
    seen.add(id);
    // Page-2 IA: iluminare tab always uses the operator-facing rename.
    const label =
      id === "iluminare"
        ? CANONICAL_TAB_LABELS.iluminare
        : section.tab_label_ro?.trim() || section.title_ro || CANONICAL_TAB_LABELS[id] || id;
    tabs.push({
      id,
      label,
      hint: id === "iluminare" || id === "montaj" ? FALLBACK_HINTS[id] : section.tab_hint_ro?.trim() || FALLBACK_HINTS[id],
      icon: TAB_ICONS[id],
      moduleCodes: [...(section.module_codes ?? []), ...(section.component_owners ?? [])],
    });
  }

  if (tabs.length === 0) {
    return null;
  }

  // Golden parity: full-product Letters always exposes exactly these three tabs, in order.
  const ids = tabs.map((tab) => tab.id);
  if (ids.join(",") !== "finisaje,iluminare,montaj") {
    return null;
  }
  return tabs;
}

export function contractCompositionProvenance(
  contract: IntakeV6ModularFormContractResponse | null | undefined,
): {
  compositionAuthority: boolean;
  subsetActivationEnabled: boolean;
  sectionKeys: string[];
  componentOwners: string[];
} {
  return {
    compositionAuthority: Boolean(contract?.summary?.composition_authority),
    subsetActivationEnabled: Boolean(
      contract?.full_product_composition?.subset_activation_enabled,
    ),
    sectionKeys: (contract?.render_sections ?? []).map((section) => section.section_key),
    componentOwners: contract?.full_product_composition?.component_owners ?? [],
  };
}
