import { CheckCircle2, Package } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { v6 } from "./atoms/intakeV6Presentation";

type OfferScopeMode = "full_product" | "component_subset";
type SoldModuleCode = "FACE" | "RETURN-CANT" | "BACK";

const SLICE1_MODULES: Array<{ code: SoldModuleCode; label: string; testId: string }> = [
  { code: "FACE", label: "Față", testId: "intake-v6-offer-scope-face" },
  { code: "RETURN-CANT", label: "Cant", testId: "intake-v6-offer-scope-cant" },
  { code: "BACK", label: "Spate", testId: "intake-v6-offer-scope-back" },
];

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function readPersistedScope(payload: Record<string, unknown> | null | undefined): {
  mode: OfferScopeMode;
  soldModules: SoldModuleCode[];
  confirmed: boolean;
} {
  const scope = asRecord(payload?.offer_scope);
  const confirmation = asRecord(payload?.offer_scope_confirmed);
  const mode = scope?.mode === "component_subset" ? "component_subset" : "full_product";
  const soldModules = Array.isArray(scope?.sold_modules)
    ? scope.sold_modules
        .map((code) => String(code))
        .filter((code): code is SoldModuleCode => code === "FACE" || code === "RETURN-CANT" || code === "BACK")
    : [];
  return {
    mode,
    soldModules,
    confirmed: confirmation?.confirmed === true,
  };
}

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
  const persisted = useMemo(() => readPersistedScope(payload), [payload]);
  const [mode, setMode] = useState<OfferScopeMode>(persisted.mode);
  const [soldModules, setSoldModules] = useState<SoldModuleCode[]>(persisted.soldModules);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const skipAutoSaveRef = useRef(true);

  useEffect(() => {
    setMode(persisted.mode);
    setSoldModules(persisted.soldModules);
    setSaveError(null);
    skipAutoSaveRef.current = true;
  }, [persisted.mode, persisted.soldModules, persisted.confirmed]);

  const subsetInvalid = mode === "component_subset" && soldModules.length === 0;
  const dirty =
    mode !== persisted.mode ||
    soldModules.join("|") !== persisted.soldModules.join("|") ||
    (mode === "full_product" && !persisted.confirmed);

  const confirmed = persisted.confirmed && !dirty && !subsetInvalid;

  useEffect(() => {
    if (skipAutoSaveRef.current) {
      skipAutoSaveRef.current = false;
      return;
    }
    if (disabled || saving) return;
    if (subsetInvalid) return;

    const timer = window.setTimeout(() => {
      void (async () => {
        setSaving(true);
        setSaveError(null);
        const ok = await onSave({
          mode,
          soldModules: mode === "full_product" ? [] : soldModules,
          confirmed: true,
        });
        if (!ok) {
          setSaveError("Salvarea selecției a eșuat.");
        }
        setSaving(false);
      })();
    }, 350);

    return () => window.clearTimeout(timer);
  }, [disabled, mode, onSave, saving, soldModules, subsetInvalid]);

  const toggleModule = (code: SoldModuleCode) => {
    setSoldModules((current) =>
      current.includes(code) ? current.filter((item) => item !== code) : [...current, code],
    );
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
            onChange={() => {
              setMode("full_product");
              setSoldModules([]);
              setSaveError(null);
            }}
            data-testid="intake-v6-offer-scope-mode-full"
          />
          Produs complet
        </label>
        <label className="flex items-center gap-2 text-[11px] text-slate-200">
          <input
            type="radio"
            name="intake-v6-offer-scope-mode"
            checked={mode === "component_subset"}
            onChange={() => {
              setMode("component_subset");
              setSaveError(null);
            }}
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
            : dirty && !subsetInvalid
              ? "Salvez selecția…"
              : "Produs complet implicit dacă nu alegi altceva"}
      </p>

      {confirmed ? (
        <p className="mt-1 flex items-center gap-1.5 text-[10px] text-emerald-300">
          <CheckCircle2 className="h-3 w-3" aria-hidden />
          {mode === "full_product"
            ? "Ofertă pentru produs complet"
            : `Componente: ${soldModules.join(", ")}`}
        </p>
      ) : null}
    </section>
  );
}
