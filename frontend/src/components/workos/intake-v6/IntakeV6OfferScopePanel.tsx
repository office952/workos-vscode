import { CheckCircle2, Package } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  normalizeSoldModules,
  readPersistedOfferScope,
  serializeOfferScopeState,
  type OfferScopeMode,
  type SoldModuleCode,
} from "@/lib/intakeV6/intakeV6OfferScopeState";
import {
  previewSoldScopeDependencyValidation,
  readDependencyConfirmations,
  readPersistedDependencyValidation,
} from "@/lib/intakeV6/intakeV6OfferScopeDependency";
import {
  describeOfferScopeSummary,
  OFFER_SCOPE_PRESETS,
  resolveActiveOfferScopePreset,
  type OfferScopePreset,
} from "@/lib/intakeV6/intakeV6OfferScopePresets";
import IntakeV6OfferScopeDependencyFeedback from "./IntakeV6OfferScopeDependencyFeedback";
import { v6 } from "./atoms/intakeV6Presentation";

const PRIMARY_MODULES: Array<{ code: SoldModuleCode; label: string; testId: string }> = [
  { code: "FACE", label: "Față", testId: "intake-v6-offer-scope-face" },
  { code: "RETURN-CANT", label: "Cant", testId: "intake-v6-offer-scope-cant" },
  { code: "BACK", label: "Spate", testId: "intake-v6-offer-scope-back" },
];

const ADVANCED_LED_MODULES: Array<{ code: SoldModuleCode; label: string; testId: string }> = [
  { code: "LIGHTING", label: "Iluminare", testId: "intake-v6-offer-scope-lighting" },
  { code: "ELECTRICAL", label: "Electrică", testId: "intake-v6-offer-scope-electrical" },
];

const SYSTEM_LED_BUNDLE = {
  label: "Sistem LED complet",
  testId: "intake-v6-offer-scope-system-led",
};

function isSystemLedSelected(modules: readonly SoldModuleCode[]): boolean {
  return modules.includes("LIGHTING") && modules.includes("ELECTRICAL");
}

function isSystemLedPartial(modules: readonly SoldModuleCode[]): boolean {
  const hasLighting = modules.includes("LIGHTING");
  const hasElectrical = modules.includes("ELECTRICAL");
  return (hasLighting || hasElectrical) && !isSystemLedSelected(modules);
}

type OfferScopeIntent = {
  mode: OfferScopeMode;
  soldModules: SoldModuleCode[];
};

function normalizeIntent(next: OfferScopeIntent): OfferScopeIntent {
  return {
    mode: next.mode,
    soldModules: next.mode === "full_product" ? [] : normalizeSoldModules(next.soldModules),
  };
}

function serializeIntent(intent: OfferScopeIntent): string {
  return serializeOfferScopeState(intent.mode, intent.soldModules);
}

function canPersistIntent(intent: OfferScopeIntent, acknowledgedSerialized: string): boolean {
  if (intent.mode === "component_subset" && intent.soldModules.length === 0) {
    return false;
  }
  return serializeIntent(intent) !== acknowledgedSerialized;
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
    dependencyConfirmationCodes?: string[];
  }) => Promise<boolean>;
  disabled?: boolean;
}) {
  const persisted = useMemo(() => readPersistedOfferScope(payload), [payload]);
  const [mode, setMode] = useState<OfferScopeMode>(persisted.mode);
  const [soldModules, setSoldModules] = useState<SoldModuleCode[]>(persisted.soldModules);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [confirmingDependencyCode, setConfirmingDependencyCode] = useState<string | null>(null);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const systemLedBundleRef = useRef<HTMLInputElement>(null);
  const [acknowledgedSerialized, setAcknowledgedSerialized] = useState(persisted.serialized);
  const onSaveRef = useRef(onSave);
  const soldModulesRef = useRef(soldModules);
  const latestIntentRef = useRef<OfferScopeIntent | null>(null);
  const persistChainRef = useRef<Promise<void>>(Promise.resolve());
  const persistInFlightRef = useRef(false);
  const acknowledgedSerializedRef = useRef(persisted.serialized);
  const hydratingSerializedRef = useRef(persisted.serialized);
  const enqueuePersistRef = useRef<(next: OfferScopeIntent) => void>(() => undefined);

  useEffect(() => {
    onSaveRef.current = onSave;
  }, [onSave]);

  useEffect(() => {
    soldModulesRef.current = soldModules;
  }, [soldModules]);

  useEffect(() => {
    if (persisted.serialized === hydratingSerializedRef.current) {
      return;
    }
    const pending = latestIntentRef.current;
    if (pending) {
      const pendingSerialized = serializeIntent(normalizeIntent(pending));
      if (pendingSerialized !== persisted.serialized) {
        return;
      }
    }
    hydratingSerializedRef.current = persisted.serialized;
    acknowledgedSerializedRef.current = persisted.serialized;
    setAcknowledgedSerialized(persisted.serialized);
    latestIntentRef.current = null;
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

  const localSerialized = useMemo(
    () => serializeOfferScopeState(localState.mode, localState.soldModules),
    [localState.mode, localState.soldModules],
  );

  const subsetInvalid = localState.mode === "component_subset" && localState.soldModules.length === 0;
  const dirty = localSerialized !== acknowledgedSerialized;
  const confirmed =
    !dirty && !subsetInvalid && (persisted.confirmed || localSerialized === acknowledgedSerialized);

  const dependencyValidation = useMemo(() => {
    const confirmations = readDependencyConfirmations(payload);
    const preview = previewSoldScopeDependencyValidation({
      mode: localState.mode,
      soldModules: localState.soldModules,
      dependencyConfirmations: confirmations,
    });
    if (!dirty && localSerialized === acknowledgedSerialized) {
      const persisted = readPersistedDependencyValidation(payload);
      if (persisted) {
        return {
          ...persisted,
          satisfied_capabilities:
            persisted.satisfied_capabilities.length > 0
              ? persisted.satisfied_capabilities
              : preview.satisfied_capabilities,
        };
      }
    }
    return preview;
  }, [acknowledgedSerialized, dirty, localSerialized, localState.mode, localState.soldModules, payload]);

  const handleConfirmDependency = useCallback(
    async (code: string) => {
      setConfirmingDependencyCode(code);
      setSaveError(null);
      try {
        const ok = await onSaveRef.current({
          mode: localState.mode,
          soldModules: localState.soldModules,
          confirmed: true,
          dependencyConfirmationCodes: [code],
        });
        if (!ok) {
          setSaveError("Confirmarea dependenței a eșuat.");
        }
      } finally {
        setConfirmingDependencyCode(null);
      }
    },
    [localState.mode, localState.soldModules],
  );

  const flushPersistQueue = useCallback(async () => {
    const intent = latestIntentRef.current;
    if (!intent) {
      return;
    }

    const normalized = normalizeIntent(intent);
    const serialized = serializeIntent(normalized);
    if (!canPersistIntent(normalized, acknowledgedSerializedRef.current)) {
      latestIntentRef.current = null;
      return;
    }

    if (persistInFlightRef.current) {
      return;
    }

    persistInFlightRef.current = true;
    setSaving(true);
    setSaveError(null);
    try {
      const ok = await onSaveRef.current({
        mode: normalized.mode,
        soldModules: normalized.soldModules,
        confirmed: true,
      });
      if (ok) {
        acknowledgedSerializedRef.current = serialized;
        hydratingSerializedRef.current = serialized;
        setAcknowledgedSerialized(serialized);
        if (latestIntentRef.current && serializeIntent(normalizeIntent(latestIntentRef.current)) === serialized) {
          latestIntentRef.current = null;
        }

        const trailing = latestIntentRef.current;
        if (
          trailing &&
          canPersistIntent(normalizeIntent(trailing), acknowledgedSerializedRef.current)
        ) {
          queueMicrotask(() => {
            enqueuePersistRef.current(trailing);
          });
        }
      } else {
        setSaveError("Salvarea selecției a eșuat.");
      }
    } catch {
      setSaveError("Salvarea selecției a eșuat.");
    } finally {
      persistInFlightRef.current = false;
      setSaving(false);
    }
  }, []);

  const schedulePersist = useCallback(
    (next: OfferScopeIntent) => {
      latestIntentRef.current = normalizeIntent(next);
      persistChainRef.current = persistChainRef.current
        .then(() => flushPersistQueue())
        .catch(() => {
          persistInFlightRef.current = false;
          setSaving(false);
          setSaveError("Salvarea selecției a eșuat.");
        });
    },
    [flushPersistQueue],
  );

  useEffect(() => {
    enqueuePersistRef.current = schedulePersist;
  }, [schedulePersist]);

  const selectFullProduct = () => {
    const next: OfferScopeIntent = { mode: "full_product", soldModules: [] };
    setMode(next.mode);
    setSoldModules([]);
    setSaveError(null);
    schedulePersist(next);
  };

  const selectSubsetMode = () => {
    setMode("component_subset");
    setSaveError(null);
  };

  const applySubsetModules = useCallback(
    (nextModules: SoldModuleCode[]) => {
      setMode("component_subset");
      setSoldModules(nextModules);
      setSaveError(null);
      schedulePersist({ mode: "component_subset", soldModules: nextModules });
    },
    [schedulePersist],
  );

  const applyPreset = useCallback(
    (preset: OfferScopePreset) => {
      if (preset.mode === "full_product") {
        const next: OfferScopeIntent = { mode: "full_product", soldModules: [] };
        setMode(next.mode);
        setSoldModules([]);
        setSaveError(null);
        schedulePersist(next);
        return;
      }
      applySubsetModules(preset.soldModules);
    },
    [applySubsetModules, schedulePersist],
  );

  const activePreset = resolveActiveOfferScopePreset(localState.mode, localState.soldModules);
  const scopeSummary = describeOfferScopeSummary(localState.mode, localState.soldModules);

  const toggleModule = (code: SoldModuleCode) => {
    const nextModules = normalizeSoldModules(
      soldModulesRef.current.includes(code)
        ? soldModulesRef.current.filter((item) => item !== code)
        : [...soldModulesRef.current, code],
    );
    applySubsetModules(nextModules);
  };

  const toggleSystemLedBundle = () => {
    const current = soldModulesRef.current;
    const nextModules = isSystemLedSelected(current)
      ? normalizeSoldModules(current.filter((item) => item !== "LIGHTING" && item !== "ELECTRICAL"))
      : normalizeSoldModules([...current, "LIGHTING", "ELECTRICAL"]);
    applySubsetModules(nextModules);
  };

  useEffect(() => {
    if (systemLedBundleRef.current) {
      systemLedBundleRef.current.indeterminate = isSystemLedPartial(soldModules);
    }
  }, [soldModules]);

  useEffect(() => {
    if (isSystemLedPartial(soldModules)) {
      setAdvancedOpen(true);
    }
  }, [soldModules]);

  return (
    <section
      className={`${v6.cardCompact} ${confirmed ? "border-emerald-500/30 bg-emerald-500/5" : "border-violet-500/30 bg-violet-500/5"}`}
      data-testid="intake-v6-offer-scope-panel"
    >
      <p className="flex items-center gap-2 text-[12px] font-semibold text-slate-100">
        <Package className="h-3.5 w-3.5 text-violet-300" aria-hidden />
        Ce producem?
      </p>

      <div
        className="mt-3 flex flex-wrap gap-2"
        data-testid="intake-v6-offer-scope-presets"
        role="group"
        aria-label="Preseturi scope"
      >
        {OFFER_SCOPE_PRESETS.map((preset) => {
          const selected = activePreset === preset.id;
          return (
            <button
              key={preset.id}
              type="button"
              disabled={disabled || saving}
              onClick={() => applyPreset(preset)}
              data-testid={preset.testId}
              aria-pressed={selected}
              className={
                selected
                  ? "rounded border border-violet-400/50 bg-violet-500/20 px-2.5 py-1 text-[11px] text-violet-100"
                  : "rounded border border-slate-600/70 bg-slate-950/40 px-2.5 py-1 text-[11px] text-slate-300 hover:border-slate-500"
              }
            >
              {preset.labelRo}
            </button>
          );
        })}
      </div>

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
        <div className="mt-3 space-y-2" data-testid="intake-v6-offer-scope-subset-options">
          <div className="flex flex-wrap gap-3">
            {PRIMARY_MODULES.map((item) => (
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
            <label className="flex items-center gap-2 text-[11px] text-slate-200">
              <input
                ref={systemLedBundleRef}
                type="checkbox"
                checked={isSystemLedSelected(soldModules)}
                onChange={toggleSystemLedBundle}
                data-testid={SYSTEM_LED_BUNDLE.testId}
              />
              {SYSTEM_LED_BUNDLE.label}
            </label>
          </div>
          <button
            type="button"
            className="text-[10px] text-violet-300 hover:text-violet-200"
            aria-expanded={advancedOpen}
            data-testid="intake-v6-offer-scope-advanced-toggle"
            onClick={() => setAdvancedOpen((open) => !open)}
          >
            Configurare avansată {advancedOpen ? "▾" : "▸"}
          </button>
          {advancedOpen ? (
            <div
              className="flex flex-wrap gap-3 pl-2"
              data-testid="intake-v6-offer-scope-advanced-options"
            >
              {ADVANCED_LED_MODULES.map((item) => (
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
        </div>
      ) : null}

      {subsetInvalid ? (
        <p className="mt-2 text-[11px] text-amber-200" data-testid="intake-v6-offer-scope-empty-subset-error">
          Selectează cel puțin o componentă (Față, Cant, Spate sau Sistem LED complet).
        </p>
      ) : null}

      <IntakeV6OfferScopeDependencyFeedback
        validation={dependencyValidation}
        onConfirmCode={handleConfirmDependency}
        confirmingCode={confirmingDependencyCode}
        dependencyConfirmations={readDependencyConfirmations(payload)}
      />

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

      <div
        className="mt-2 space-y-0.5 rounded border border-slate-700/50 bg-slate-950/30 px-2 py-1.5 text-[10px] text-slate-400"
        data-testid="intake-v6-offer-scope-summary"
      >
        <p data-testid="intake-v6-offer-scope-summary-mode">
          Mod: {scopeSummary.requestModeLabelRo}
        </p>
        {scopeSummary.activeLabelsRo.length > 0 ? (
          <p data-testid="intake-v6-offer-scope-summary-active">
            Componente active: {scopeSummary.activeLabelsRo.join(", ")}
          </p>
        ) : null}
        {scopeSummary.excludedLabelsRo.length > 0 ? (
          <p data-testid="intake-v6-offer-scope-summary-excluded">
            Nu sunt incluse: {scopeSummary.excludedLabelsRo.join(", ")}
          </p>
        ) : null}
      </div>
    </section>
  );
}
