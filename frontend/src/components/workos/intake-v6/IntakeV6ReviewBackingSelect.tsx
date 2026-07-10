import type { IntakeV6BackingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import { INTAKE_V6_BACKING_MODE_OPTIONS } from "@/lib/intakeV6/intakeV6BackingMode";
import { v6 } from "./atoms/intakeV6Presentation";
import {
  REVIEW_FIELD_BLOCK_CLASS,
  REVIEW_FIELD_LABEL_CLASS,
  REVIEW_SELECT_CLASS,
} from "./reviewFieldLayout";

export default function IntakeV6ReviewBackingSelect({
  backingMode,
  onBackingChange,
  embedded = false,
}: {
  backingMode: IntakeV6BackingMode;
  onBackingChange: (mode: IntakeV6BackingMode) => void;
  /** When true, matches Finisaje panel dropdown width/label styling. */
  embedded?: boolean;
}) {
  const select = (
    <select
      className={embedded ? REVIEW_SELECT_CLASS : "w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-3 py-2 text-[12px]"}
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
        className="mt-2 border-t border-[#2A3548]/50 pt-2"
        data-testid="intake-v6-backing-finish-row"
      >
        <label className={REVIEW_FIELD_BLOCK_CLASS}>
          <span className={REVIEW_FIELD_LABEL_CLASS}>Spate litere</span>
          {select}
        </label>
      </div>
    );
  }

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-backing-section">
      <label className="block">
        <span className="mb-2 block text-[13px] font-bold uppercase tracking-wide text-slate-100">
          Spate litere
        </span>
        {select}
      </label>
    </div>
  );
}
