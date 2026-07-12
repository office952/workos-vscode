import { CheckCircle2, Package } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  isOfferScopeStateDirty,
  normalizeSoldModules,
  readPersistedOfferScope,
  shouldPersistOfferScope,
  type OfferScopeMode,
  type SoldModuleCode,
} from "@/lib/intakeV6/intakeV6OfferScopeState";
import { v6 } from "./atoms/intakeV6Presentation";

const SLICE1_MODULES: Array<{ code: SoldModuleCode; label: string; testId: string }> = [
  { code: "FACE", label: "Față", testId: "intake-v6-offer-scope-face" },
  { code: "RETURN-CANT", label: "Cant", testId: "intake-v6-offer-scope-cant" },
  { code: "BACK", label: "Spate", testId: "intake-v6-offer-scope-back" },
];

export default function IntakeV6OfferScopePanel({
  payload,
  onSave,
  disabled = false,
}: {
  payload: Record<string, unknown> | null | undefined;
  onSave: (input: {
    mode: OfferScopeMode;
    soldModules: SoldModuleCode[];
    confirmed: boolean;
  }) => Promise<boolean>;
  disabled?: boolean;
}) {
  const persisted = useMemo(() => readPersistedOfferScope(payload), [payload]);
  const [mode, setMode] = useState<OfferScopeMode>(persisted.mode);
  const [soldModules, setSoldModules] = useState<SoldModuleCode[]>(persisted.soldModules);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const onSaveRef = useRef(onSave);
  const lastPersistedSerializedRef = useRef(persisted.serialized);
  const inFlightSerializedRef = useRef<string | null>(null);

  useEffect(() => {
    onSaveRef.current = onSave;
  }, [onSave]);

  useEffect(() => {
    if (persisted.serialized === lastPersistedSerializedRef.current) {
      return;
    }
    lastPersistedSerializedRef.current = persisted.serialized;
    inFlightSerializedRef.current = null;
    setMode(persisted.mode);
    setSoldModules(persisted.soldModules);
    setSaveError(null);
  }, [persisted.mode, persisted.serialized, persisted.soldModules]);

  const localState = useMemo(
    () => ({
      mode,
      soldModules: mode === "full_product" ? [] : normalizeSoldModules(soldModules),
    }),
    [mode, soldModules],
  );

  const subsetInvalid = localState.mode === "component_subset" && localState.soldModules.length === 0;
  const dirty = isOfferScopeStateDirty(localState, persisted);
  const confirmed = persisted.confirmed && !dirty && !subsetInvalid;

  const persistIfNeeded = useCallback(
    async (next: { mode: OfferScopeMode; soldModules: SoldModuleCode[] }) => {
      const normalized = {
        mode: next.mode,
        soldModules: next.mode === "full_product" ? [] : normalizeSoldModules(next.soldModules),
      };
      if (!shouldPersistOfferScope(normalized, persisted)) {
        return true;
      }

      const serialized = serializeLocalScope(normalized.mode, normalized.soldModules);
      if (inFlightSerializedRef.current === serialized) {
        return true;
      }

      inFlightSerializedRef.current = serialized;
      setSaving(true);
      setSaveError(null);
      try {
        const ok = await onSaveRef.current({
          mode: normalized.mode,
          soldModules: normalized.soldModules,
          confirmed: true,
        });
        if (!ok) {
          inFlightSerializedRef.current = null;
          setSaveError("Salvarea selecției a eșuat.");
        }
        return ok;
      } finally {
        setSaving(false);
      }
    },
    [persisted],
  );

  const selectFullProduct = () => {
    const next = { mode: "full_product" as const, soldModules: [] as SoldModuleCode[] };
    setMode(next.mode);
    setSoldModules([]);
    setSaveError(null);
    void persistIfNeeded(next);
  };

  const selectSubsetMode = () => {
    setMode("component_subset");
    setSaveError(null);
  };

  const toggleModule = (code: SoldModuleCode) => {
    const nextModules = normalizeSoldModules(
      soldModules.includes(code) ? soldModules.filter((item) => item !== code) : [...soldModules, code],
    );
    setMode("component_subset");
    setSoldModules(nextModules);
    setSaveError(null);
    void persistIfNeeded({ mode: "component_subset", soldModules: nextModules });
  };

  return (
    <section
      className={`${v6.cardCompact} ${confirmed ? "border-emerald-500/30 bg-emerald-500/5" : "border-violet-500/30 bg-violet-500/5"}`}
      data-testid="intake-v6-offer-scope-panel"
    >
      <p className="flex items-center gap-2 text-[12px] font-semibold text-slate-100">
        <Package className="h-3.5 w-3.5 text-violet-300" aria-hidden />
        Ce producem?
      </p>

      <fieldset className="mt-3 space-y-2" disabled={disabled || saving}>
        <label className="flex items-center gap-2 text-[11px] text-slate-200">
          <input
            type="radio"
            name="intake-v6-offer-scope-mode"
            checked={mode === "full_product"}
            onChange={selectFullProduct}
            data-testid="intake-v6-offer-scope-mode-full"
          />
          Produs complet
        </label>
        <label className="flex items-center gap-2 text-[11px] text-slate-200">
          <input
            type="radio"
            name="intake-v6-offer-scope-mode"
            checked={mode === "component_subset"}
            onChange={selectSubsetMode}
            data-testid="intake-v6-offer-scope-mode-subset"
          />
          Doar anumite componente
        </label>
      </fieldset>

      {mode === "component_subset" ? (
        <div className="mt-3 flex flex-wrap gap-3" data-testid="intake-v6-offer-scope-subset-options">
          {SLICE1_MODULES.map((item) => (
            <label key={item.code} className="flex items-center gap-2 text-[11px] text-slate-200">
              <input
                type="checkbox"
                checked={soldModules.includes(item.code)}
                onChange={() => toggleModule(item.code)}
                data-testid={item.testId}
              />
              {item.label}
            </label>
          ))}
        </div>
      ) : null}

      {subsetInvalid ? (
        <p className="mt-2 text-[11px] text-amber-200" data-testid="intake-v6-offer-scope-empty-subset-error">
          Selectează cel puțin o componentă (Față, Cant sau Spate).
        </p>
      ) : null}

      {saveError ? <p className="mt-2 text-[11px] text-rose-300">{saveError}</p> : null}

      <p className="mt-2 text-[10px] text-slate-500" data-testid="intake-v6-offer-scope-status">
        {saving
          ? "Salvez selecția…"
          : confirmed
            ? "Selecție confirmată"
            : mode === "component_subset" && localState.soldModules.length === 0
              ? "Selectează componentele de produs."
              : "Produs complet implicit dacă nu alegi altceva"}
      </p>

      {confirmed ? (
        <p className="mt-1 flex items-center gap-1.5 text-[10px] text-emerald-300">
          <CheckCircle2 className="h-3 w-3" aria-hidden />
          {mode === "full_product"
            ? "Ofertă pentru produs complet"
            : `Componente: ${localState.soldModules.join(", ")}`}
        </p>
      ) : null}
    </section>
  );
}

function serializeLocalScope(mode: OfferScopeMode, soldModules: readonly SoldModuleCode[]): string {
  if (mode === "full_product") {
    return "full_product";
  }
  return `component_subset:${normalizeSoldModules(soldModules).join("|")}`;
}
