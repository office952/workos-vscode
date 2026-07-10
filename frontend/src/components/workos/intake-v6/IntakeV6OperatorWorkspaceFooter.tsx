import { useEffect, useMemo, useState } from "react";
import type { IntakeV6StepId, IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";
import { buildIntakeV6FooterIssuesDisplay } from "@/lib/intakeV6/intakeV6FooterIssuesDisplay";
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

  const confirmDisabledReason =
    isConfirmStep && confirmFooter?.disabledReason && !confirmFooter.canSubmit
      ? confirmFooter.disabledReason
      : null;

  const primaryActionReason =
    nextDisabled || isConfirmStep
      ? confirmDisabledReason ?? footerBlocker
      : footerBlocker;

  const issuesDisplay = useMemo(
    () =>
      buildIntakeV6FooterIssuesDisplay({
        primaryActionReason: nextDisabled ? null : primaryActionReason,
        problemDetails: status.details.filter((row) => row.tone === "warn" || row.tone === "bad"),
        reviewWarnings: statusCtx?.overlay.reviewWarnings,
        secondaryWarnings: statusCtx?.overlay.secondaryWarnings,
        statusActions: status.actions,
      }),
    [
      primaryActionReason,
      nextDisabled,
      status.details,
      status.actions,
      statusCtx?.overlay.reviewWarnings,
      statusCtx?.overlay.secondaryWarnings,
    ],
  );

  const showIssuesDrawer = issuesDisplay.totalCount > 0;

  useEffect(() => {
    statusCtx?.registerFooterIssuesOpener?.(() => setIssuesOpen(true));
    return () => statusCtx?.registerFooterIssuesOpener?.(null);
  }, [statusCtx]);

  function handleStatusAction(actionId: string) {
    const handlers = statusCtx?.handlers;
    if (actionId === "confirm-step") handlers?.onJumpToConfirm?.();
    else if (actionId === "jump-artwork" || actionId === "jump-actions") handlers?.onJumpToPending?.();
    else if (actionId === "jump-layers") handlers?.onJumpToLayers?.();
    else if (actionId === "jump-live-calc") handlers?.onJumpToLiveCalc?.();
  }

  const countLabel =
    issuesDisplay.totalCount > 0
      ? `Probleme și avertizări — ${issuesDisplay.totalCount}`
      : "Probleme, avertizări și detalii";

  return (
    <footer
      className="sticky bottom-0 z-10 mt-auto border-t border-[#2A3548] bg-[#111827]/95 px-7 py-3 shadow-[0_-8px_24px_rgba(0,0,0,0.35)] backdrop-blur-sm"
      data-testid="intake-v6-operator-workspace-footer"
    >
      {primaryActionReason && nextDisabled ? (
        <p
          className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-[11px] leading-relaxed text-amber-100/90"
          data-testid="intake-v6-footer-primary-action-reason"
        >
          {primaryActionReason}
        </p>
      ) : null}

      {showIssuesDrawer ? (
        <div className="mb-2 rounded border border-[#2A3548] bg-[#0A0F1A]/60" data-testid="intake-v6-footer-issues">
          <button
            type="button"
            className="flex w-full items-center justify-between px-3 py-2 text-left text-[11px] font-semibold text-slate-300"
            onClick={() => setIssuesOpen((value) => !value)}
            data-testid="intake-v6-footer-issues-toggle"
            aria-expanded={issuesOpen}
          >
            <span data-testid="intake-v6-footer-issues-count">{countLabel}</span>
            <span className="text-slate-500">{issuesOpen ? "▾" : "▸"}</span>
          </button>
          {issuesOpen ? (
            <div className="border-t border-[#2A3548] px-3 py-2 text-[11px]" data-testid="intake-v6-footer-issues-content">
              {issuesDisplay.actionCount + issuesDisplay.warningCount + issuesDisplay.technicalCount > 0 ? (
                <p className="mb-2 text-[10px] text-slate-500" data-testid="intake-v6-footer-issues-breakdown">
                  {issuesDisplay.actionCount > 0 ? `${issuesDisplay.actionCount} acțiuni` : null}
                  {issuesDisplay.actionCount > 0 && issuesDisplay.warningCount > 0 ? " · " : null}
                  {issuesDisplay.warningCount > 0 ? `${issuesDisplay.warningCount} avertizări` : null}
                  {(issuesDisplay.actionCount > 0 || issuesDisplay.warningCount > 0) &&
                  issuesDisplay.technicalCount > 0
                    ? " · "
                    : null}
                  {issuesDisplay.technicalCount > 0 ? `${issuesDisplay.technicalCount} detalii tehnice` : null}
                </p>
              ) : null}
              {issuesDisplay.groups.map((group) => (
                <div key={group.id} className="mb-3 last:mb-0" data-testid={`intake-v6-footer-group-${group.id}`}>
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                    {group.label}
                  </p>
                  <ul className="space-y-1">
                    {group.entries.map((entry) => (
                      <li
                        key={entry.id}
                        className="rounded border border-[#2A3548] px-2 py-1.5 text-slate-300"
                        data-testid={`intake-v6-footer-issue-${entry.id}`}
                      >
                        <span>{entry.title}</span>
                        {entry.actionId ? (
                          <button
                            type="button"
                            className="ml-2 text-[10px] font-semibold text-cyan-300 hover:text-cyan-200"
                            onClick={() => handleStatusAction(entry.actionId!)}
                            data-testid={`intake-v6-footer-issue-action-${entry.actionId}`}
                          >
                            Mergi
                          </button>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
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
