import { useEffect, useMemo, useState } from "react";

import type { IntakeV6SheetQuoteMaterialCandidates } from "@/lib/intakeV6/intakeV6Api";

import {

  putIntakeV6SheetFootprintOverride,

  type IntakeV6SheetFootprintOverrideRequest,

} from "@/lib/intakeV6/intakeV6Api";

import {

  formatSheetFootprintSqm,

  readSheetFootprintOverrideHeightCm,

  readSheetFootprintOverrideWidthCm,

  validateSheetFootprintOverrideInput,

  type IntakeV6SheetFootprintOverride,

  computeOperatorSheetFootprintAreaSqm,

} from "@/lib/intakeV6/intakeV6SheetFootprintOverride";

import {

  buildIntakeV6SheetFootprintSourceOptions,

  readFullSheetFootprintDetail,

  readPersistedSheetFootprintSource,

  resolveDefaultSheetFootprintSource,

  resolveSelectedFootprintDisplay,

  type IntakeV6SheetFootprintSourceKey,

} from "@/lib/intakeV6/intakeV6SheetFootprintSource";

import { v6 } from "./atoms/intakeV6Presentation";



const DEFAULT_MANUAL_REASON = "Dimensiuni măsurate în Corel";



function parsePositiveCm(value: string): number | null {

  const parsed = Number.parseFloat(value);

  if (!Number.isFinite(parsed) || parsed <= 0) return null;

  return parsed;

}



export default function IntakeV6SheetFootprintOverridePanel({

  workspaceId,

  candidates,

  initialOverride,

  onSaved,

  prominent = false,

}: {

  workspaceId: string;

  candidates: IntakeV6SheetQuoteMaterialCandidates | null | undefined;

  initialOverride?: IntakeV6SheetFootprintOverride | null;

  onSaved?: () => void;

  prominent?: boolean;

}) {

  const defaultSource = resolveDefaultSheetFootprintSource(candidates, initialOverride);

  const [selectedSource, setSelectedSource] = useState<IntakeV6SheetFootprintSourceKey>(defaultSource);

  const [widthCm, setWidthCm] = useState("");

  const [heightCm, setHeightCm] = useState("");

  const [reason, setReason] = useState("");

  const [saving, setSaving] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [savedAreaSqm, setSavedAreaSqm] = useState<number | null>(null);

  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);

  const [savedSource, setSavedSource] = useState<IntakeV6SheetFootprintSourceKey | null>(null);



  useEffect(() => {

    const w = readSheetFootprintOverrideWidthCm(initialOverride ?? null);

    const h = readSheetFootprintOverrideHeightCm(initialOverride ?? null);

    setWidthCm(w != null ? String(w) : "");

    setHeightCm(h != null ? String(h) : "");

    setReason(initialOverride?.reason ?? "");

    setSelectedSource(resolveDefaultSheetFootprintSource(candidates, initialOverride));

    const area = initialOverride?.areaSqm ?? initialOverride?.area_sqm;

    setSavedAreaSqm(typeof area === "number" ? area : null);

    setSavedSource(readPersistedSheetFootprintSource(initialOverride));

    setValidationWarnings([]);

    setError(null);

  }, [initialOverride, candidates]);



  const liveManualAreaSqm = useMemo(() => {

    const w = parsePositiveCm(widthCm);

    const h = parsePositiveCm(heightCm);

    if (w == null || h == null) return null;

    return computeOperatorSheetFootprintAreaSqm(w, h);

  }, [widthCm, heightCm]);



  const sourceOptions = useMemo(

    () =>

      buildIntakeV6SheetFootprintSourceOptions({

        candidates,

        manualAreaSqm: liveManualAreaSqm,

      }),

    [candidates, liveManualAreaSqm],

  );



  const activeFootprintDisplay =
    savedSource != null
      ? resolveSelectedFootprintDisplay({
          sourceKey: savedSource,
          candidates,
          manualAreaSqm: liveManualAreaSqm,
          persistedAreaSqm: savedAreaSqm,
        })
      : null;



  const manualDimensionsValid =

    parsePositiveCm(widthCm) != null && parsePositiveCm(heightCm) != null;



  async function persistSelection(sourceKey: IntakeV6SheetFootprintSourceKey) {

    setSaving(true);

    setError(null);

    setValidationWarnings([]);



    const payload: IntakeV6SheetFootprintOverrideRequest = {

      selected_footprint_source: sourceKey,

      use_for_quote_estimate: true,

      applies_to: ["plexiglas_face", "forex_backing"],

    };



    if (sourceKey === "operator_manual_footprint") {

      const w = parsePositiveCm(widthCm);

      const h = parsePositiveCm(heightCm);

      if (w == null || h == null) {

        setError("Introduce lățime și înălțime valide (cm).");

        setSaving(false);

        return false;

      }

      const validation = validateSheetFootprintOverrideInput({

        widthCm: w,

        heightCm: h,

        reason: reason.trim() || DEFAULT_MANUAL_REASON,

        useForQuoteEstimate: true,

        eligibleFaceAreaSqm: candidates?.eligible_face_area_sqm,

        fullSheetSqm: candidates?.full_sheet_allocation_sqm ?? 6.0,

      });

      if (validation.ok === false) {

        setError(validation.error);

        setSaving(false);

        return false;

      }

      setValidationWarnings(validation.warnings);

      payload.width_cm = w;

      payload.height_cm = h;

      payload.reason = reason.trim() || DEFAULT_MANUAL_REASON;

    } else {

      payload.reason = reason.trim() || `Sursă footprint: ${sourceKey}`;

    }



    try {

      const response = await putIntakeV6SheetFootprintOverride(workspaceId, payload);

      setSavedAreaSqm(response.area_sqm ?? null);

      setSavedSource(sourceKey);

      onSaved?.();

      return true;

    } catch (err) {

      setError(err instanceof Error ? err.message : "Salvare footprint eșuată.");

      return false;

    } finally {

      setSaving(false);

    }

  }



  const borderClass = prominent

    ? "border-amber-500/40 bg-amber-500/5"

    : "border-wo-border-strong bg-wo-surface-inset/30";



  const optionClass = (selected: boolean, disabled?: boolean) =>

    `rounded border px-3 py-3 transition-colors ${

      disabled

        ? "cursor-not-allowed border-wo-border-strong/60 bg-wo-surface-inset/20 opacity-60"

        : selected

          ? "cursor-pointer border-sky-500/50 bg-sky-500/10"

          : "cursor-pointer border-wo-border-strong bg-wo-surface-inset/40 hover:border-wo-border-strong"

    }`;



  const saveDisabled =

    saving ||

    (selectedSource === "operator_manual_footprint" && !manualDimensionsValid) ||

    sourceOptions.find((option) => option.key === selectedSource)?.disabled === true;



  return (

    <div

      className={`mb-3 space-y-4 rounded border p-4 ${borderClass}`}

      data-testid="intake-v6-sheet-footprint-override"

    >

      <div>

        <h4 className="text-[12px] font-bold uppercase tracking-wide text-slate-200">

          Verificare footprint material

        </h4>

        <p className="mt-1 text-[11px] text-slate-400">

          Alege sursa de suprafață pentru review intern (Plexi / Forex). Nu modifică oferta finală

          și nu schimbă CostEngine.

        </p>

        <p className="mt-1 text-[10px] text-slate-500" data-testid="intake-v6-footprint-preview-note">

          Preview intern — nu ofertă finală

        </p>

        {activeFootprintDisplay ? (

          <p

            className="mt-2 text-[11px] text-sky-200/90"

            data-testid="intake-v6-footprint-used-summary"

          >

            Footprint folosit:{" "}

            <strong>

              {activeFootprintDisplay.label} — {activeFootprintDisplay.areaText}

            </strong>

          </p>

        ) : null}

      </div>



      <details
        className="rounded border border-wo-border-strong bg-wo-surface-inset/30 p-3 text-[11px]"
        data-testid="intake-v6-footprint-source-selection"
      >
        <summary className="cursor-pointer font-semibold uppercase tracking-wide text-slate-400">
          Selectare sursă footprint (detaliu tehnic)
        </summary>

      <div className="mt-3 space-y-2" role="radiogroup" aria-label="Sursă footprint material">

        {sourceOptions.map((option) => (

          <label

            key={option.key}

            className={`block ${optionClass(selectedSource === option.key, option.disabled)}`}

          >

            <div className="flex items-start gap-2">

              <input

                type="radio"

                name="intake-v6-footprint-source"

                checked={selectedSource === option.key}

                disabled={option.disabled}

                onChange={() => {

                  if (!option.disabled) setSelectedSource(option.key);

                }}

                className="mt-0.5"

                data-testid={`intake-v6-footprint-source-${option.key}`}

              />

              <div className="min-w-0 flex-1">

                <span className="text-[12px] font-medium text-slate-200">

                  {option.label} — {formatSheetFootprintSqm(option.areaSqm)}

                </span>

                {option.disabled && option.disabledReason ? (

                  <p className="mt-0.5 text-[10px] text-slate-500">{option.disabledReason}</p>

                ) : null}

                {selectedSource === option.key && option.key === "operator_manual_footprint" ? (

                  <div className="mt-3 space-y-3">

                    <div className="grid gap-2 sm:grid-cols-2">

                      <label className="block text-[10px] text-slate-400">

                        Lățime (cm)

                        <input

                          type="number"

                          min="0"

                          step="0.01"

                          className={v6.input + " mt-1 w-full"}

                          value={widthCm}

                          onChange={(e) => setWidthCm(e.target.value)}

                          data-testid="intake-v6-sheet-footprint-width-cm"

                        />

                      </label>

                      <label className="block text-[10px] text-slate-400">

                        Înălțime (cm)

                        <input

                          type="number"

                          min="0"

                          step="0.01"

                          className={v6.input + " mt-1 w-full"}

                          value={heightCm}

                          onChange={(e) => setHeightCm(e.target.value)}

                          data-testid="intake-v6-sheet-footprint-height-cm"

                        />

                      </label>

                    </div>



                    {!manualDimensionsValid ? (

                      <p className="text-[10px] text-amber-200" data-testid="intake-v6-footprint-manual-hint">

                        Completează lățimea și înălțimea din Corel pentru a calcula footprint-ul.

                      </p>

                    ) : null}



                    <label className="block text-[10px] text-slate-400">

                      Notă operator

                      <textarea

                        className={v6.input + " mt-1 min-h-[52px] w-full"}

                        value={reason}

                        onChange={(e) => setReason(e.target.value)}

                        placeholder="Ex. măsurat pe placă 3000×2000 mm"

                        data-testid="intake-v6-sheet-footprint-reason"

                      />

                    </label>



                    {liveManualAreaSqm != null ? (

                      <p

                        className="text-[11px] text-slate-300"

                        data-testid="intake-v6-sheet-footprint-live-area"

                      >

                        Footprint manual calculat:{" "}

                        <strong>{formatSheetFootprintSqm(liveManualAreaSqm)}</strong>

                      </p>

                    ) : null}

                  </div>

                ) : null}

              </div>

            </div>

          </label>

        ))}

      </div>

      </details>



      {candidates ? (

        <details className="text-[10px] text-slate-500" data-testid="intake-v6-footprint-technical-details">

          <summary className="cursor-pointer font-semibold uppercase tracking-wide text-slate-400">

            Detalii tehnice footprint

          </summary>

          <ul

            className="mt-2 space-y-0.5 text-slate-400"

            data-testid="intake-v6-sheet-quote-candidates-summary"

          >

            <li>Placement face: {formatSheetFootprintSqm(candidates.placement_footprint_face_sqm)}</li>

            <li>Placă fizică: {readFullSheetFootprintDetail(candidates)}</li>

            {candidates.unknown_placement_sqm ? (

              <li>Placement necunoscut: {formatSheetFootprintSqm(candidates.unknown_placement_sqm)}</li>

            ) : null}

            <li>Aplică la: Plexiglas față, Forex spate</li>

          </ul>

        </details>

      ) : null}



      {validationWarnings.length > 0 ? (

        <ul className="text-[10px] text-amber-200" data-testid="intake-v6-sheet-footprint-warnings">

          {validationWarnings.map((warning) => (

            <li key={warning}>• {warning}</li>

          ))}

        </ul>

      ) : null}



      {error ? (

        <p className="text-[10px] text-amber-300" data-testid="intake-v6-sheet-footprint-error">

          {error}

        </p>

      ) : null}



      <button

        type="button"

        className={v6.btnGhost}

        disabled={saveDisabled}

        onClick={() => void persistSelection(selectedSource)}

        data-testid="intake-v6-sheet-footprint-save"

      >

        {saving ? "Salvez…" : "Confirmă sursa footprint"}

      </button>

    </div>

  );

}




