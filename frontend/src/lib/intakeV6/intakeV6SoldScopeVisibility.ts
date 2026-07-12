import {
  readPersistedOfferScope,
  type OfferScopeMode,
  type SoldModuleCode,
} from "./intakeV6OfferScopeState";

export type SoldScopeFieldVisibility = {
  mode: OfferScopeMode;
  soldModules: SoldModuleCode[];
  face: boolean;
  returnCant: boolean;
  back: boolean;
};

export function resolveSoldScopeFieldVisibility(
  payload: Record<string, unknown> | null | undefined,
): SoldScopeFieldVisibility {
  const persisted = readPersistedOfferScope(payload);
  if (persisted.mode === "full_product" || persisted.soldModules.length === 0) {
    return {
      mode: persisted.mode,
      soldModules: persisted.soldModules,
      face: true,
      returnCant: true,
      back: true,
    };
  }

  const sold = new Set(persisted.soldModules);
  return {
    mode: persisted.mode,
    soldModules: persisted.soldModules,
    face: sold.has("FACE"),
    returnCant: sold.has("RETURN-CANT"),
    back: sold.has("BACK"),
  };
}

export function isSoldModuleVisible(
  visibility: SoldScopeFieldVisibility,
  module: SoldModuleCode,
): boolean {
  if (module === "FACE") return visibility.face;
  if (module === "RETURN-CANT") return visibility.returnCant;
  return visibility.back;
}
