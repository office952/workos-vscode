import type { ProductFamily } from "@/api/productFamilies";
import { CheckCircle2 } from "lucide-react";
import {
  INTAKE_QUICK_START_WORK_TYPES,
  isWorkTypeSelectable,
  type IntakeQuickStartWorkType,
} from "@/lib/intakeQuickStartWorkTypes";

export interface IntakeWorkTypePickerProps {
  selectedWorkTypeId: string | null;
  onSelect: (workTypeId: string) => void;
  registry: ProductFamily[];
  loading?: boolean;
}

function workTypeCardState(
  workType: IntakeQuickStartWorkType,
  registry: ProductFamily[],
  selectedWorkTypeId: string | null
) {
  const selectable = isWorkTypeSelectable(workType, registry);
  const selected = selectedWorkTypeId === workType.id;
  return { selectable, selected };
}

export default function IntakeWorkTypePicker({
  selectedWorkTypeId,
  onSelect,
  registry,
  loading = false,
}: IntakeWorkTypePickerProps) {
  if (loading) {
    return (
      <p className="text-[11px] text-slate-500 py-4 text-center" data-testid="work-type-picker-loading">
        Se încarcă tipurile de lucrare...
      </p>
    );
  }

  return (
    <div
      className="grid grid-cols-1 sm:grid-cols-2 gap-2"
      role="radiogroup"
      aria-label="Tip lucrare"
      data-testid="work-type-picker"
    >
      {INTAKE_QUICK_START_WORK_TYPES.map((workType) => {
        const { selectable, selected } = workTypeCardState(workType, registry, selectedWorkTypeId);
        const disabled = !selectable;

        return (
          <button
            key={workType.id}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-disabled={disabled}
            data-work-type-id={workType.id}
            data-family-id={workType.familyId ?? "generic"}
            disabled={disabled}
            onClick={() => {
              if (selectable) onSelect(workType.id);
            }}
            className={`relative flex min-h-[72px] flex-col items-start justify-center rounded-lg border px-3 py-2.5 text-left transition-colors ${
              selected
                ? "border-emerald-500/60 bg-emerald-950/25 ring-1 ring-emerald-500/30"
                : disabled
                  ? "border-wo-border-strong bg-[#141c2e]/60 opacity-55 cursor-not-allowed"
                  : "border-wo-border-strong bg-wo-surface-raised hover:border-slate-500 cursor-pointer"
            }`}
          >
            <span className="text-[12px] font-semibold text-slate-100 leading-snug">
              {workType.label}
            </span>
            {workType.hint && selectable && (
              <span className="mt-1 text-[10px] text-slate-500 leading-snug">{workType.hint}</span>
            )}
            {disabled && workType.disabledReason && (
              <span className="mt-0.5 text-[10px] text-slate-500">{workType.disabledReason}</span>
            )}
            {disabled && !workType.disabledReason && !selectable && workType.familyId && (
              <span className="mt-0.5 text-[10px] text-slate-500">Indisponibil în registry</span>
            )}
            {selected && (
              <CheckCircle2
                className="absolute top-2 right-2 w-4 h-4 text-emerald-400"
                aria-hidden
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
