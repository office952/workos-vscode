import type { IntakeV6BackingMode, IntakeV6EmblemLightingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import {
  INTAKE_V6_BACKING_MODE_OPTIONS,
  INTAKE_V6_EMBLEM_LIGHTING_OPTIONS,
} from "@/lib/intakeV6/intakeV6BackingMode";
import { ledAreaLayoutRuleLabel } from "@/lib/intakeV6/sharedLedLightingDensity";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6BackingAndEmblemSection({
  backingMode,
  emblemLightingMode,
  returnDepthMm,
  onBackingChange,
  onEmblemLightingChange,
}: {
  backingMode: IntakeV6BackingMode;
  emblemLightingMode: IntakeV6EmblemLightingMode;
  returnDepthMm?: number | null;
  onBackingChange: (mode: IntakeV6BackingMode) => void;
  onEmblemLightingChange: (mode: IntakeV6EmblemLightingMode) => void;
}) {
  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-backing-section">
      <h2 className="mb-3 text-[13px] font-bold uppercase tracking-wide">Spate / backing litere</h2>
      <p className="mb-3 text-[11px] text-slate-500">
        Față litere: <strong className="text-slate-300">plexiglas 3mm PMMA - opal</strong> - șanfren față
        obligatoriu (operații CNC separate în breakdown).
      </p>
      <label className="mb-4 block">
        <span className={v6.label}>Backing Forex</span>
        <select
          className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-3 py-2 text-[12px]"
          value={backingMode}
          onChange={(e) => onBackingChange(e.target.value as IntakeV6BackingMode)}
          data-testid="intake-v6-backing-mode"
        >
          {INTAKE_V6_BACKING_MODE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className={v6.label}>Iluminare emblemă</span>
        <select
          className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-3 py-2 text-[12px]"
          value={emblemLightingMode}
          onChange={(e) => onEmblemLightingChange(e.target.value as IntakeV6EmblemLightingMode)}
          data-testid="intake-v6-emblem-lighting-mode"
        >
          {INTAKE_V6_EMBLEM_LIGHTING_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <span className="mt-1 block text-[10px] text-slate-500">
          Regula ProductSystem: {ledAreaLayoutRuleLabel(returnDepthMm)} pe aria emblemei.
        </span>
      </label>
    </div>
  );
}



