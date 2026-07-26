/**
 * ACM boxed composition Decision A — applied_content XOR + optional metal frame.
 * Authoring surface only; does not publish or invent pricing.
 */

import { useState } from "react";
import { PS_SURFACE_INPUT, PS_SURFACE_PANEL } from "./productSystemSurfaces";

export type AcmAppliedContent = "none" | "letters" | "logo";

export type AcmBoxedAppliedContentState = {
  appliedContent: AcmAppliedContent;
  metalFrameEnabled: boolean;
};

const ACM_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
const LOGO_CODE = "TPL-VOLUMETRIC-LOGO_v1";

export function AcmBoxedAppliedContentPanel({
  templateCode,
  initial,
  onChange,
}: {
  templateCode: string;
  initial?: Partial<AcmBoxedAppliedContentState>;
  onChange?: (next: AcmBoxedAppliedContentState) => void;
}) {
  const [appliedContent, setAppliedContent] = useState<AcmAppliedContent>(
    initial?.appliedContent ?? "none",
  );
  const [metalFrameEnabled, setMetalFrameEnabled] = useState(
    Boolean(initial?.metalFrameEnabled),
  );

  if (templateCode !== ACM_CODE) {
    return null;
  }

  const emit = (next: AcmBoxedAppliedContentState) => {
    onChange?.(next);
  };

  const selectContent = (value: AcmAppliedContent) => {
    setAppliedContent(value);
    emit({ appliedContent: value, metalFrameEnabled });
  };

  const toggleFrame = (enabled: boolean) => {
    setMetalFrameEnabled(enabled);
    emit({ appliedContent, metalFrameEnabled: enabled });
  };

  return (
    <section
      className={`space-y-3 ${PS_SURFACE_PANEL} px-4 py-4`}
      data-testid="acm-boxed-applied-content-panel"
    >
      <div>
        <h3 className="text-sm font-semibold text-wo-text-primary">Conținut aplicat + cadru</h3>
        <p className="mt-0.5 text-[11px] text-slate-400">
          Decision A — litere <span className="text-slate-300">XOR</span> logo; cadru metalic opțional
          (operator). Fără praguri automate.
        </p>
      </div>

      <fieldset className="space-y-2" data-testid="acm-applied-content-radio-group">
        <legend className="text-[11px] font-medium text-slate-300">Conținut aplicat</legend>
        {(
          [
            { value: "none" as const, label: "Doar panou (fără conținut volumetric)" },
            { value: "letters" as const, label: "Litere volumetrice (reutilizare componente VL)" },
            { value: "logo" as const, label: "Logo volumetric (ramură candidată — blocată ofertare)" },
          ] as const
        ).map((opt) => (
          <label
            key={opt.value}
            className="flex cursor-pointer items-start gap-2 text-[12px] text-slate-200"
          >
            <input
              type="radio"
              name="acm-applied-content"
              className="mt-0.5"
              value={opt.value}
              checked={appliedContent === opt.value}
              onChange={() => selectContent(opt.value)}
              data-testid={`acm-applied-content-${opt.value}`}
            />
            <span>{opt.label}</span>
          </label>
        ))}
      </fieldset>

      {appliedContent === "logo" ? (
        <p
          className="rounded border border-amber-800/40 bg-amber-950/20 px-2 py-1.5 text-[11px] text-amber-100"
          data-testid="acm-logo-branch-blocked-note"
        >
          Ramura logo rămâne onest blocată: <span className="font-mono">{LOGO_CODE}</span> este
          candidate / root blocked. Nu se folosește RETURN/cant ca produs logo.
        </p>
      ) : null}

      {appliedContent === "letters" ? (
        <p
          className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1.5 text-[11px] text-slate-300"
          data-testid="acm-letters-branch-note"
        >
          Litere: reutilizare FACE / BACK / ALUMINIU / LED / FINISH. Rădăcina VL nu este legată sub ACM
          (protecție ciclu VL→ACM).
        </p>
      ) : null}

      <label
        className="flex cursor-pointer items-start gap-2 text-[12px] text-slate-200"
        data-testid="acm-metal-frame-optional"
      >
        <input
          type="checkbox"
          className={`mt-0.5 ${PS_SURFACE_INPUT}`}
          checked={metalFrameEnabled}
          onChange={(e) => toggleFrame(e.target.checked)}
          data-testid="acm-metal-frame-checkbox"
        />
        <span>
          Cadru metalic intern opțional{" "}
          <span className="font-mono text-[10px] text-slate-500">(acp_internal_frame)</span>
          <span className="mt-0.5 block text-[11px] text-slate-500">
            Selectare explicită operator — fără praguri automate de dimensiune.
          </span>
        </span>
      </label>
    </section>
  );
}
