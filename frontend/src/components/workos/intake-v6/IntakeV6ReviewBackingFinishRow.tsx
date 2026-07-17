import type { IntakeV6BackingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import { INTAKE_V6_BACKING_MODE_OPTIONS } from "@/lib/intakeV6/intakeV6BackingMode";
import {
  REVIEW_CANT_COLUMN_CLASS,
  REVIEW_FACE_COLUMN_CLASS,
  REVIEW_FIELD_BLOCK_CLASS,
  REVIEW_FIELD_LABEL_CLASS,
  REVIEW_LAYER_CARD_GRID_CLASS,
  REVIEW_SELECT_CLASS,
} from "./reviewFieldLayout";

/** Forex backing row — same grid/controls as letter layer face/cant fields. */
export default function IntakeV6ReviewBackingFinishRow({
  backingMode,
  onBackingChange,
  embedded = false,
  testIdSuffix,
  backingLabel,
}: {
  backingMode: IntakeV6BackingMode;
  onBackingChange: (mode: IntakeV6BackingMode) => void;
  embedded?: boolean;
  testIdSuffix?: string;
  backingLabel?: string;
}) {
  const rowTestId = testIdSuffix
    ? `intake-v6-backing-finish-row-${testIdSuffix}`
    : "intake-v6-backing-finish-row";
  const modeTestId = testIdSuffix ? `intake-v6-backing-mode-${testIdSuffix}` : "intake-v6-backing-mode";

  return (
    <div
      className={
        embedded
          ? "mt-1.5"
          : "mt-1.5 overflow-hidden rounded-md border border-[#2A3548] bg-[#0A0F1A]/55"
      }
      style={embedded ? undefined : { borderLeftWidth: 3, borderLeftColor: "#475569" }}
      data-testid={rowTestId}
    >
      <div className={REVIEW_LAYER_CARD_GRID_CLASS}>
        <div className={REVIEW_FACE_COLUMN_CLASS} data-testid="intake-v6-backing-finish-zone">
          <label className={REVIEW_FIELD_BLOCK_CLASS}>
            <span className={REVIEW_FIELD_LABEL_CLASS}>{backingLabel ?? "Finisaj spate"}</span>
            <select
              className={REVIEW_SELECT_CLASS}
              value={backingMode}
              onChange={(event) => onBackingChange(event.target.value as IntakeV6BackingMode)}
              data-testid={modeTestId}
            >
              {INTAKE_V6_BACKING_MODE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className={REVIEW_CANT_COLUMN_CLASS} aria-hidden />
      </div>
    </div>
  );
}
