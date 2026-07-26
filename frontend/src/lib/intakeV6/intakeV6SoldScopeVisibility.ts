import { isAcmPanelOnlyComposition } from "./acmPanel/acmPanelOnlyComposition";
import {
  readPersistedOfferScope,
  type OfferScopeMode,
  type SoldModuleCode,
} from "./intakeV6OfferScopeState";
import type { IntakeV6ReviewTabDefinition, IntakeV6ReviewTabId } from "./intakeV6ProductPlugin";

export type SoldScopeFieldVisibility = {
  mode: OfferScopeMode;
  soldModules: SoldModuleCode[];
  face: boolean;
  returnCant: boolean;
  back: boolean;
  lighting: boolean;
  electrical: boolean;
};

/**
 * Build 3.1 — Configurare tabs visible only when at least one owner is in active sold scope.
 * Montaj / Iluminare stay full-product (or lighting/electrical sold) only.
 */
export function filterReviewTabsBySoldScope(
  tabs: IntakeV6ReviewTabDefinition[] | null | undefined,
  visibility: SoldScopeFieldVisibility,
): IntakeV6ReviewTabDefinition[] | null {
  if (!tabs || tabs.length === 0) return tabs ?? null;

  const keep = (id: IntakeV6ReviewTabId): boolean => {
    if (id === "finisaje") {
      return visibility.face || visibility.returnCant || visibility.back;
    }
    if (id === "iluminare") {
      return visibility.lighting || visibility.electrical;
    }
    if (id === "montaj") {
      // Slice-1 sold modules never include mounting; tab is full-product only.
      return visibility.mode === "full_product";
    }
    return false;
  };

  const filtered = tabs.filter((tab) => keep(tab.id));
  return filtered.length > 0 ? filtered : null;
}

export function resolveActiveReviewTabForScope(
  current: IntakeV6ReviewTabId,
  tabs: IntakeV6ReviewTabDefinition[] | null | undefined,
): IntakeV6ReviewTabId {
  const ids = (tabs ?? []).map((tab) => tab.id);
  if (ids.includes(current)) return current;
  return ids[0] ?? "finisaje";
}

export function resolveSoldScopeFieldVisibility(
  payload: Record<string, unknown> | null | undefined,
): SoldScopeFieldVisibility {
  const persisted = readPersistedOfferScope(payload);
  // Composition support_only (ACM panel-alone) outranks VL full_product teaching:
  // letter FACE/CANT/BACK/LED are not sold — do not require finish completeness.
  if (isAcmPanelOnlyComposition(payload)) {
    return {
      mode: persisted.mode,
      soldModules: persisted.soldModules,
      face: false,
      returnCant: false,
      back: false,
      lighting: false,
      electrical: false,
    };
  }
  if (persisted.mode === "full_product" || persisted.soldModules.length === 0) {
    return {
      mode: persisted.mode,
      soldModules: persisted.soldModules,
      face: true,
      returnCant: true,
      back: true,
      lighting: true,
      electrical: true,
    };
  }

  const sold = new Set(persisted.soldModules);
  return {
    mode: persisted.mode,
    soldModules: persisted.soldModules,
    face: sold.has("FACE"),
    returnCant: sold.has("RETURN-CANT"),
    back: sold.has("BACK"),
    lighting: sold.has("LIGHTING"),
    electrical: sold.has("ELECTRICAL"),
  };
}

export function isSoldModuleVisible(
  visibility: SoldScopeFieldVisibility,
  module: SoldModuleCode,
): boolean {
  if (module === "FACE") return visibility.face;
  if (module === "RETURN-CANT") return visibility.returnCant;
  if (module === "BACK") return visibility.back;
  if (module === "LIGHTING") return visibility.lighting;
  return visibility.electrical;
}
