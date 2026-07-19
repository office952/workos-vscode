import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Circle } from "lucide-react";
import { v6 } from "./atoms/intakeV6Presentation";

function ChecklistControlRow({
  done,
  warning = false,
  label,
  testId,
  control,
}: {
  done: boolean;
  warning?: boolean;
  label: string;
  testId: string;
  control?: ReactNode;
}) {
  const Icon = done ? CheckCircle2 : warning ? AlertCircle : Circle;
  const iconClass = done
    ? "text-emerald-400"
    : warning
      ? "text-amber-400"
      : "text-slate-500";

  return (
    <li
      className="flex items-start gap-2 rounded-md border border-[#243044]/70 bg-[#0A0F1A]/40 px-2.5 py-2"
      data-testid={testId}
    >
      <Icon className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${iconClass}`} aria-hidden />
      <div className="min-w-0 flex-1">
        {control ?? <span className="text-[11px] text-slate-300">{label}</span>}
      </div>
    </li>
  );
}

export default function IntakeV6ConfirmHandoffPanel({
  compositionConfirmed = true,
  finishSetupIncomplete,
  operatorConfirmationComplete,
  confirmInternalDraft,
  confirmDraftBoundary,
  showHandoffCheckboxes,
  canResolveInternalDraftConfirmation,
  savingInternalConfirmation,
  confirmationHydrationPending = false,
  confirmationLoadError = null,
  allFatalBlockers,
  showBlockerList,
  resultMessage,
  errorMessage,
  fallbackBlockerMessage,
  onInternalDraftChange,
  onDraftBoundaryChange,
}: {
  compositionConfirmed?: boolean;
  finishSetupIncomplete: boolean;
  operatorConfirmationComplete: boolean;
  confirmInternalDraft: boolean;
  confirmDraftBoundary: boolean;
  showHandoffCheckboxes: boolean;
  canResolveInternalDraftConfirmation: boolean;
  savingInternalConfirmation: boolean;
  /** True while persisted confirmation truth has not been resolved yet. */
  confirmationHydrationPending?: boolean;
  /** Load failure for confirmation / handoff preview (do not assume unchecked). */
  confirmationLoadError?: string | null;
  allFatalBlockers: string[];
  showBlockerList: boolean;
  resultMessage: string | null;
  errorMessage: string | null;
  fallbackBlockerMessage: string | null;
  onInternalDraftChange: (checked: boolean) => void;
  onDraftBoundaryChange: (checked: boolean) => void;
}) {
  const confirmationSettled = !confirmationHydrationPending;
  const confirmationChecked =
    confirmationSettled && confirmInternalDraft && operatorConfirmationComplete;
  const confirmationDisabled =
    confirmationHydrationPending ||
    savingInternalConfirmation ||
    !canResolveInternalDraftConfirmation ||
    !compositionConfirmed ||
    finishSetupIncomplete;

  return (
    <div
      className={`${v6.cardCompact} !p-3`}
      data-testid="intake-v6-quote-handoff"
      data-fatal-blocker-count={allFatalBlockers.length}
      data-show-blocker-list={showBlockerList ? "true" : "false"}
    >
      <h3 className={`mb-2 ${v6.sectionTitle}`}>Confirmare finală</h3>
      <p className={`mb-3 ${v6.helper}`}>
        Creează doar draft intern — fără comandă, producție sau stoc.
      </p>

      {/* Status/blocker narrative lives in ConsolidatedBlockersList (first paint). Handoff owns checklist + draft action. */}
      {fallbackBlockerMessage && allFatalBlockers.length === 0 ? (
        <p
          className="mb-3 text-[12px] leading-snug text-amber-100/90"
          data-testid="intake-v6-confirm-handoff-fallback-blocker"
        >
          {fallbackBlockerMessage}
        </p>
      ) : null}

      <ul className="mb-3 space-y-1.5" data-testid="intake-v6-confirm-handoff-checklist">
        <ChecklistControlRow
          done={compositionConfirmed}
          warning={!compositionConfirmed}
          label={
            compositionConfirmed
              ? "Compoziție produs confirmată"
              : "Compoziție produs — confirmă în Configurare"
          }
          testId="intake-v6-confirm-checklist-composition"
        />
        <ChecklistControlRow
          done={!finishSetupIncomplete}
          warning={finishSetupIncomplete}
          label="Finisaje confirmate în Configurare"
          testId="intake-v6-confirm-checklist-finish"
        />
        <ChecklistControlRow
          done={confirmationChecked}
          warning={confirmationSettled && !operatorConfirmationComplete}
          label="Confirm finisajele și datele de ofertare pentru draft intern"
          testId="intake-v6-confirm-checklist-operator"
          control={
            compositionConfirmed && !finishSetupIncomplete ? (
              <label
                className="flex cursor-pointer items-start gap-2 text-[11px] text-slate-300"
                data-testid="intake-v6-internal-draft-confirmation"
              >
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={confirmationChecked}
                  disabled={confirmationDisabled}
                  aria-busy={confirmationHydrationPending || undefined}
                  onChange={(event) => onInternalDraftChange(event.target.checked)}
                  data-testid="intake-v6-confirm-internal-draft"
                />
                <span>
                  {confirmationHydrationPending
                    ? "Se verifică confirmarea persistată…"
                    : "Confirm finisajele și datele de ofertare pentru draft intern"}
                </span>
              </label>
            ) : undefined
          }
        />
        {showHandoffCheckboxes ? (
          <ChecklistControlRow
            done={confirmDraftBoundary}
            label="Am înțeles limitele draftului intern (fără order / execuție / stoc)"
            testId="intake-v6-confirm-checklist-boundary"
            control={
              <label className="flex cursor-pointer items-start gap-2 text-[11px] text-slate-300">
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={confirmDraftBoundary}
                  onChange={(event) => onDraftBoundaryChange(event.target.checked)}
                  data-testid="intake-v6-confirm-draft-boundary"
                />
                <span>Am înțeles limitele draftului intern (fără order / execuție / stoc)</span>
              </label>
            }
          />
        ) : null}
      </ul>

      {finishSetupIncomplete ? (
        <p className="mb-3 text-[11px] text-amber-200" data-testid="intake-v6-finish-setup-incomplete">
          Finalizează finisajele în Review înainte de draft.
        </p>
      ) : null}

      {confirmationLoadError ? (
        <p className="mb-3 text-[11px] text-amber-200" data-testid="intake-v6-confirmation-load-error">
          Starea de confirmare nu a putut fi verificată. Reîncarcă sau revino pe acest pas.
        </p>
      ) : null}

      {resultMessage ? (
        <p className="text-[11px] text-emerald-300" data-testid="intake-v6-quote-created">
          {resultMessage}
        </p>
      ) : null}

      {errorMessage ? (
        <p className="mt-2 text-[11px] text-red-300" data-testid="intake-v6-quote-handoff-error">
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
