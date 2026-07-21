/**
 * ACM / Bond Axis B — shell-local face treatments (routed cut-out + acrylic insert).
 * Distinct from volumetric applied_content XOR (Axis A). Authoring surface only.
 */

import { useState } from "react";
import { PS_SURFACE_INPUT, PS_SURFACE_PANEL } from "./productSystemSurfaces";

const ACM_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

export type AcmFaceTreatmentCoexistence =
  | "none"
  | "routed_only"
  | "insert_only"
  | "both";

export type AcmBoxedFaceTreatmentState = {
  routedEnabled: boolean;
  insertEnabled: boolean;
  insertThicknessMm: number;
  coexistence: AcmFaceTreatmentCoexistence;
};

function computeCoexistence(
  routed: boolean,
  insert: boolean,
): AcmFaceTreatmentCoexistence {
  if (routed && insert) return "both";
  if (routed) return "routed_only";
  if (insert) return "insert_only";
  return "none";
}

export function AcmBoxedFaceTreatmentPanel({
  templateCode,
  initial,
  onChange,
}: {
  templateCode: string;
  initial?: Partial<AcmBoxedFaceTreatmentState>;
  onChange?: (next: AcmBoxedFaceTreatmentState) => void;
}) {
  const [routedEnabled, setRoutedEnabled] = useState(Boolean(initial?.routedEnabled));
  const [insertEnabled, setInsertEnabled] = useState(Boolean(initial?.insertEnabled));
  const [insertThicknessMm, setInsertThicknessMm] = useState(
    initial?.insertThicknessMm ?? 10,
  );

  if (templateCode !== ACM_CODE) {
    return null;
  }

  const coexistence = computeCoexistence(routedEnabled, insertEnabled);
  const showReliefBadge = insertEnabled && Math.abs(insertThicknessMm - 10) < 0.01;

  // Mirror backend scoped_commercial_blockers — no invented rates.
  const scopedBlockers: string[] = [];
  if (coexistence !== "none") {
    scopedBlockers.push("FACE_TREATMENT_OPTICAL_CATALOG_MISSING");
    if (coexistence === "routed_only" || coexistence === "both") {
      scopedBlockers.push("FACE_TREATMENT_ILLUMINATION_RATES_MISSING");
    }
  }
  const treatmentLinesAllowed = false;
  const subtotalStatus = coexistence === "none" ? "NOT_APPLICABLE" : "BLOCKED";
  const readinessOverall =
    coexistence === "none" ? "NOT_APPLICABLE" : "LOCAL_CONFIGURATION_REQUIRED";

  const emit = (next: AcmBoxedFaceTreatmentState) => {
    onChange?.(next);
  };

  const setRouted = (enabled: boolean) => {
    setRoutedEnabled(enabled);
    emit({
      routedEnabled: enabled,
      insertEnabled,
      insertThicknessMm,
      coexistence: computeCoexistence(enabled, insertEnabled),
    });
  };

  const setInsert = (enabled: boolean) => {
    setInsertEnabled(enabled);
    emit({
      routedEnabled,
      insertEnabled: enabled,
      insertThicknessMm,
      coexistence: computeCoexistence(routedEnabled, enabled),
    });
  };

  const setThickness = (mm: number) => {
    setInsertThicknessMm(mm);
    emit({
      routedEnabled,
      insertEnabled,
      insertThicknessMm: mm,
      coexistence: computeCoexistence(routedEnabled, insertEnabled),
    });
  };

  return (
    <section
      className={`space-y-3 ${PS_SURFACE_PANEL} px-4 py-4`}
      data-testid="acm-boxed-face-treatment-panel"
    >
      <div>
        <h3 className="text-sm font-semibold text-slate-100">Tratarea feței Bond/ACM</h3>
        <p className="mt-0.5 text-[11px] text-slate-400">
          Axis B — tratamente locale pe carcasă (decupaj iluminat / insert plexiglas). Ortogonal
          față de conținutul volumetric aplicat. Fără catalog optic inventat.
        </p>
      </div>

      <label
        className="flex cursor-pointer items-start gap-2 text-[12px] text-slate-200"
        data-testid="acm-face-treatment-routed"
      >
        <input
          type="checkbox"
          className={`mt-0.5 ${PS_SURFACE_INPUT}`}
          checked={routedEnabled}
          onChange={(e) => setRouted(e.target.checked)}
          data-testid="acm-face-treatment-routed-checkbox"
        />
        <span>
          Decupaj iluminat (routed / backlit cut-out)
          <span className="mt-0.5 block font-mono text-[10px] text-slate-500">
            FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT · ACP-LOCAL-MODULE-ROUTED-BACKLIT
          </span>
          <span className="mt-0.5 block text-[11px] text-slate-500">
            Roluri geometrie: CUTOUT_TEXT / CUTOUT_LOGO. Iluminare / plexi spate — gated (fără rate
            inventate).
          </span>
        </span>
      </label>

      <label
        className="flex cursor-pointer items-start gap-2 text-[12px] text-slate-200"
        data-testid="acm-face-treatment-insert"
      >
        <input
          type="checkbox"
          className={`mt-0.5 ${PS_SURFACE_INPUT}`}
          checked={insertEnabled}
          onChange={(e) => setInsert(e.target.checked)}
          data-testid="acm-face-treatment-insert-checkbox"
        />
        <span>
          Insert plexiglas (relief)
          <span className="mt-0.5 block font-mono text-[10px] text-slate-500">
            FACE-TREATMENT-ACRYLIC-INSERT · ACP-LOCAL-MODULE-ACRYLIC-INSERT
          </span>
          <span className="mt-0.5 block text-[11px] text-slate-500">
            ~10 mm = variantă owner frecventă, nu unica grosime admisă.
          </span>
        </span>
      </label>

      {insertEnabled ? (
        <div className="ml-6 space-y-2" data-testid="acm-face-treatment-insert-config">
          <label className="flex items-center gap-2 text-[12px] text-slate-300">
            <span>Grosime insert (mm)</span>
            <input
              type="number"
              min={1}
              step={0.5}
              className={`w-20 ${PS_SURFACE_INPUT} px-2 py-1 text-[12px]`}
              value={insertThicknessMm}
              onChange={(e) => setThickness(Number(e.target.value) || 10)}
              data-testid="acm-face-treatment-insert-thickness"
            />
          </label>
          {showReliefBadge ? (
            <p
              className="rounded border border-sky-800/40 bg-sky-950/20 px-2 py-1.5 text-[11px] text-sky-100"
              data-testid="acm-face-treatment-relief-badge"
            >
              Badge UI: <span className="font-mono">RELIEF_PLEXI_10MM</span> — același produs insert,
              nu SKU separat.
            </p>
          ) : null}
        </div>
      ) : null}

      <p
        className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1.5 text-[11px] text-slate-300"
        data-testid="acm-face-treatment-coexistence"
      >
        Coexistență: <span className="font-mono text-slate-200">{coexistence}</span>
        {coexistence === "none"
          ? " — doar panou (tratamente opționale absente nu blochează)."
          : " — panoul ACM rămâne owner pentru tablă; tratamentele nu dublează foaia."}
      </p>

      <div
        className="space-y-1 rounded border border-slate-700 bg-slate-900/40 px-2 py-1.5 text-[11px] text-slate-300"
        data-testid="acm-face-treatment-commercial-readiness"
      >
        <p>
          Readiness tratamente:{" "}
          <span className="font-mono text-slate-200" data-testid="acm-face-treatment-readiness-overall">
            {readinessOverall}
          </span>
        </p>
        <p>
          treatment_commercial_lines_allowed:{" "}
          <span
            className="font-mono text-slate-200"
            data-testid="acm-face-treatment-lines-allowed"
          >
            {String(treatmentLinesAllowed)}
          </span>
        </p>
        <p>
          Subtotal tratamente:{" "}
          <span
            className="font-mono text-slate-200"
            data-testid="acm-face-treatment-subtotal"
          >
            {subtotalStatus === "BLOCKED" ? "BLOCKED" : "null"}
          </span>
          <span className="ml-1 text-slate-500">({subtotalStatus})</span>
        </p>
        <p data-testid="acm-face-treatment-scoped-blockers">
          Blockers:{" "}
          {scopedBlockers.length === 0 ? (
            <span className="font-mono text-slate-400">[]</span>
          ) : (
            <span className="font-mono text-amber-100">{scopedBlockers.join(", ")}</span>
          )}
        </p>
      </div>

      {(routedEnabled || insertEnabled) && (
        <p
          className="rounded border border-amber-800/40 bg-amber-950/20 px-2 py-1.5 text-[11px] text-amber-100"
          data-testid="acm-face-treatment-optical-blocked-note"
        >
          Comercial optic/electric: BLOCKED onest — lipsește catalogul optic/electrical RO. Nu se
          inventează prețuri. LIGHT-ROUTED nu este autoritate. Insert-only nu moștenește blocker-ul
          de iluminare routed.
        </p>
      )}
    </section>
  );
}
