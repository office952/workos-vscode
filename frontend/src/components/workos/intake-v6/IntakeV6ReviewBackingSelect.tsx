import type { IntakeV6BackingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import { INTAKE_V6_BACKING_MODE_OPTIONS } from "@/lib/intakeV6/intakeV6BackingMode";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6ReviewBackingSelect({
  backingMode,
  onBackingChange,
}: {
  backingMode: IntakeV6BackingMode;
  onBackingChange: (mode: IntakeV6BackingMode) => void;
}) {
  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-backing-section">
      <label className="block">
        <span className="mb-2 block text-[13px] font-bold uppercase tracking-wide text-slate-100">
          Spate litere
        </span>
        <select
          className="w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-3 py-2 text-[12px]"
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
      </label>
    </div>
  );
}



