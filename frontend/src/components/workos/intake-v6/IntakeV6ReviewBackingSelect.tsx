import type { IntakeV6BackingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import { INTAKE_V6_BACKING_MODE_OPTIONS } from "@/lib/intakeV6/intakeV6BackingMode";
import IntakeV6ReviewBackingFinishRow from "./IntakeV6ReviewBackingFinishRow";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6ReviewBackingSelect({
  backingMode,
  onBackingChange,
  embedded = false,
}: {
  backingMode: IntakeV6BackingMode;
  onBackingChange: (mode: IntakeV6BackingMode) => void;
  /** Fallback Finisaje panel when no letter groups are present. */
  embedded?: boolean;
}) {
  const select = (
    <select
      className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-3 py-2 text-[12px]"
      value={backingMode}
      onChange={(event) => onBackingChange(event.target.value as IntakeV6BackingMode)}
      data-testid="intake-v6-backing-mode"
    >
      {INTAKE_V6_BACKING_MODE_OPTIONS.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );

  if (embedded) {
    return (
      <div
        className={`${v6.cardCompact} mt-2 !p-3`}
        data-testid="intake-v6-backing-finish-block"
      >
        <p className="mb-1 text-[10px] font-semibold text-slate-400">Spate litere</p>
        <p
          className="mb-2 text-[10px] leading-snug text-slate-500"
          data-testid="intake-v6-backing-finish-helper"
        >
          Material Forex pentru corpul literelor.
        </p>
        <IntakeV6ReviewBackingFinishRow backingMode={backingMode} onBackingChange={onBackingChange} />
      </div>
    );
  }

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-backing-section">
      <label className="block">
        <span className="mb-2 block text-[13px] font-bold uppercase tracking-wide text-wo-text-primary">
          Spate litere
        </span>
        {select}
      </label>
    </div>
  );
}
