import { useMemo, useState } from "react";
import type { IntakeV6StepId, IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";
import { buildWorkspaceHeaderStatus } from "@/lib/intakeV6/intakeV6WorkspaceHeaderStatus";
import { useIntakeV6WorkspaceHeaderStatusOptional } from "./IntakeV6WorkspaceHeaderStatusContext";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6OperatorWorkspaceFooter({
  currentStep,
  stepIndex,
  stepOrderLength,
  footerBlocker,
  nextDisabled,
  nextLabel,
  nextButtonClassName,
  onBack,
  onNext,
  persisting,
  workspaceState,
}: {
  currentStep: IntakeV6StepId;
  stepIndex: number;
  stepOrderLength: number;
  footerBlocker: string | null;
  nextDisabled: boolean;
  nextLabel: string;
  nextButtonClassName: string;
  onBack: () => void;
  onNext: () => void;
  persisting: boolean;
  workspaceState: IntakeV6WorkspaceState;
}) {
  const statusCtx = useIntakeV6WorkspaceHeaderStatusOptional();
  const [issuesOpen, setIssuesOpen] = useState(false);
  const confirmFooter = currentStep === "confirm" ? statusCtx?.confirmFooter : null;
  const isConfirmStep = currentStep === "confirm";
  const status = useMemo(
    () => buildWorkspaceHeaderStatus(workspaceState, statusCtx?.overlay ?? {}),
    [workspaceState, statusCtx?.overlay],
  );

  const centerLabel = isConfirmStep && confirmFooter
    ? `Confirmări ${confirmFooter.checklistDone}/${confirmFooter.checklistTotal}`
    : `Pasul ${stepIndex + 1} din ${stepOrderLength} - ${
        currentStep === "layers" ? "straturi" : currentStep === "review" ? "review" : "confirmare"
      }`;

  const footerReason =
    isConfirmStep && confirmFooter?.disabledReason && !confirmFooter.canSubmit
      ? confirmFooter.disabledReason
      : footerBlocker;

  const problemDetails = status.details.filter((row) => row.tone === "warn" || row.tone === "bad");
  const reviewWarnings = statusCtx?.overlay.reviewWarnings ?? [];
  const issueCount =
    (footerReason ? 1 : 0) +
    problemDetails.length +
    reviewWarnings.length +
    status.actions.length;
  const showIssuesDrawer =
    Boolean(footerReason) ||
    status.actions.length > 0 ||
    problemDetails.length > 0 ||
    reviewWarnings.length > 0;

  function handleStatusAction(actionId: string) {
    const handlers = statusCtx?.handlers;
    if (actionId === "confirm-step") handlers?.onJumpToConfirm?.();
    else if (actionId === "jump-artwork" || actionId === "jump-actions") handlers?.onJumpToPending?.();
    else if (actionId === "jump-layers") handlers?.onJumpToLayers?.();
    else if (actionId === "jump-live-calc") handlers?.onJumpToLiveCalc?.();
  }

  return (
    <footer
      className="sticky bottom-0 z-10 mt-auto border-t border-[#2A3548] bg-[#111827]/95 px-7 py-3 shadow-[0_-8px_24px_rgba(0,0,0,0.35)] backdrop-blur-sm"
      data-testid="intake-v6-operator-workspace-footer"
    >
      {showIssuesDrawer ? (
        <div className="mb-2 rounded border border-[#2A3548] bg-[#0A0F1A]/60" data-testid="intake-v6-footer-issues">
          <button
            type="button"
            className="flex w-full items-center justify-between px-3 py-2 text-left text-[11px] font-semibold text-slate-300"
            onClick={() => setIssuesOpen((value) => !value)}
            data-testid="intake-v6-footer-issues-toggle"
            aria-expanded={issuesOpen}
          >
            <span>
              Probleme & atenționări
              {issueCount > 0 ? ` (${issueCount})` : ""}
            </span>
            <span className="text-slate-500">{issuesOpen ? "▾" : "▸"}</span>
          </button>
          {issuesOpen ? (
            <div className="border-t border-[#2A3548] px-3 py-2 text-[11px]" data-testid="intake-v6-footer-issues-content">
              {footerReason ? (
                <p className="mb-2 rounded border border-amber-500/20 bg-amber-500/5 px-2 py-1.5 text-amber-200/90">
                  {footerReason}
                </p>
              ) : null}
              {problemDetails.length > 0 ? (
                <ul className="mb-2 space-y-1">
                  {problemDetails.map((row) => (
                    <li key={row.id} className="flex items-start justify-between gap-3 rounded border border-[#2A3548] px-2 py-1.5">
                      <span className="text-slate-400">{row.label}</span>
                      <span className={row.tone === "bad" ? "text-red-300" : "text-amber-200"}>{row.value}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
              {reviewWarnings.length > 0 ? (
                <ul className="mb-2 space-y-1 text-slate-300">
                  {reviewWarnings.slice(0, 5).map((warning) => (
                    <li key={warning} className="rounded border border-[#2A3548] px-2 py-1.5">
                      {warning}
                    </li>
                  ))}
                </ul>
              ) : null}
              {status.actions.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {status.actions.map((action) => (
                    <button
                      key={action.id}
                      type="button"
                      className="rounded border border-cyan-500/25 bg-cyan-500/10 px-2 py-1 text-[10px] font-semibold text-cyan-200 hover:bg-cyan-500/15"
                      onClick={() => handleStatusAction(action.id)}
                      data-testid={`intake-v6-footer-issue-action-${action.id}`}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="flex items-center justify-between gap-3">
        <button type="button" className={v6.btnGhost} disabled={stepIndex === 0} onClick={onBack}>
          Înapoi
        </button>

        <span className="text-center text-[11px] text-slate-500" data-testid="intake-v6-footer-step-label">
          {centerLabel}
        </span>

        {isConfirmStep && confirmFooter ? (
          <button
            type="button"
            className={`${v6.btnConfirm} min-w-[11rem]`}
            disabled={!confirmFooter.canSubmit || confirmFooter.submitting}
            onClick={confirmFooter.onSubmit}
            data-testid="intake-v6-create-internal-draft"
          >
            {confirmFooter.submitting ? confirmFooter.submittingLabel : confirmFooter.submitLabel}
          </button>
        ) : (
          <button
            type="button"
            className={nextButtonClassName}
            disabled={nextDisabled || persisting}
            onClick={onNext}
            data-testid="intake-v6-footer-next"
          >
            {nextLabel}
          </button>
        )}
      </div>
    </footer>
  );
}

