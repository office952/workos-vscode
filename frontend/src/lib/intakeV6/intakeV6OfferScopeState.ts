export type OfferScopeMode = "full_product" | "component_subset";
export type SoldModuleCode = "FACE" | "RETURN-CANT" | "BACK";

export const SOLD_MODULE_ORDER: readonly SoldModuleCode[] = ["FACE", "RETURN-CANT", "BACK"];

export type PersistedOfferScopeState = {
  mode: OfferScopeMode;
  soldModules: SoldModuleCode[];
  confirmed: boolean;
  serialized: string;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export function isSoldModuleCode(value: string): value is SoldModuleCode {
  return value === "FACE" || value === "RETURN-CANT" || value === "BACK";
}

export function normalizeSoldModules(codes: readonly string[]): SoldModuleCode[] {
  const selected = new Set<SoldModuleCode>();
  for (const code of codes) {
    if (isSoldModuleCode(code)) {
      selected.add(code);
    }
  }
  return SOLD_MODULE_ORDER.filter((code) => selected.has(code));
}

export function serializeOfferScopeState(mode: OfferScopeMode, soldModules: readonly SoldModuleCode[]): string {
  if (mode === "full_product") {
    return "full_product";
  }
  return `component_subset:${normalizeSoldModules(soldModules).join("|")}`;
}

export function readPersistedOfferScope(payload: Record<string, unknown> | null | undefined): PersistedOfferScopeState {
  const scope = asRecord(payload?.offer_scope);
  const confirmation = asRecord(payload?.offer_scope_confirmed);
  const mode: OfferScopeMode = scope?.mode === "component_subset" ? "component_subset" : "full_product";
  const soldModules = normalizeSoldModules(
    Array.isArray(scope?.sold_modules) ? scope.sold_modules.map((code) => String(code)) : [],
  );
  const hasPersistedScope = scope != null;
  const confirmed = hasPersistedScope ? confirmation?.confirmed === true : false;

  return {
    mode,
    soldModules,
    confirmed,
    serialized: serializeOfferScopeState(mode, soldModules),
  };
}

export function isOfferScopeStateDirty(
  local: { mode: OfferScopeMode; soldModules: readonly SoldModuleCode[] },
  persisted: PersistedOfferScopeState,
): boolean {
  return serializeOfferScopeState(local.mode, local.soldModules) !== persisted.serialized;
}

export function shouldPersistOfferScope(
  local: { mode: OfferScopeMode; soldModules: readonly SoldModuleCode[] },
  persisted: PersistedOfferScopeState,
): boolean {
  if (local.mode === "component_subset" && local.soldModules.length === 0) {
    return false;
  }
  return isOfferScopeStateDirty(local, persisted);
}
