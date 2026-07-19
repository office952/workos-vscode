import { useEffect, useMemo, useState } from "react";
import type { IntakeV6StepId, IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";
import { buildIntakeV6FooterIssuesDisplay } from "@/lib/intakeV6/intakeV6FooterIssuesDisplay";
import {
  buildIntakeV6OperatorGuidanceModel,
  guidanceIssuesFromStickyIssues,
  normalizeGuidanceNextAction,
  type GuidanceAttentionIssue,
} from "@/lib/intakeV6/intakeV6OperatorGuidance";
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
  canContinueFromAnalyzer = false,
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
  canContinueFromAnalyzer?: boolean;
}) {
  const statusCtx = useIntakeV6WorkspaceHeaderStatusOptional();
  const [issuesOpen, setIssuesOpen] = useState(false);
  const isHandoffStep = currentStep === "confirm";
  const confirmFooter = isHandoffStep ? statusCtx?.confirmFooter : null;
  const status = useMemo(
    () => buildWorkspaceHeaderStatus(workspaceState, statusCtx?.overlay ?? {}),
    [workspaceState, statusCtx?.overlay],
  );

  const attentionIssues = useMemo(
    () =>
      guidanceIssuesFromStickyIssues(
        (statusCtx?.overlay.attentionIssues ?? []).map((issue) => ({
          id: issue.id,
          severity: issue.severity,
          message: issue.message,
          action: issue.action,
          focusTarget: issue.focusTarget,
          tabId: issue.tabId,
        })),
      ),
    [statusCtx?.overlay.attentionIssues],
  );

  /** Informational drawer rows — not counted as blockers/warnings in sticky/spine. */
  const informationIssues = useMemo((): GuidanceAttentionIssue[] => {
    const legacy = buildIntakeV6FooterIssuesDisplay({
      // Never duplicate footer primary action inside the inventory.
      primaryActionReason: null,
      problemDetails: status.details.filter((row) => row.tone === "warn" || row.tone === "bad"),
      reviewWarnings: statusCtx?.overlay.reviewWarnings,
      secondaryWarnings: statusCtx?.overlay.secondaryWarnings,
      statusActions: status.actions,
    });
    const known = new Set(
      attentionIssues.map((issue) => issue.message.trim().toLowerCase()),
    );
    const info: GuidanceAttentionIssue[] = [];
    for (const group of legacy.groups) {
      const severity: GuidanceAttentionIssue["severity"] =
        group.id === "actions" || group.id === "warnings"
          ? // When sticky inventory is present, blockers/warnings already live there.
            attentionIssues.length > 0
            ? "information"
            : group.id === "actions"
              ? "blocker"
              : "warning"
          : "information";
      for (const entry of group.entries) {
        if (known.has(entry.title.trim().toLowerCase())) continue;
        info.push({
          id: entry.id,
          severity,
          message: entry.title,
          action: entry.actionId ?? null,
        });
        known.add(entry.title.trim().toLowerCase());
      }
    }
    return info;
  }, [
    attentionIssues,
    status.details,
    status.actions,
    statusCtx?.overlay.reviewWarnings,
    statusCtx?.overlay.secondaryWarnings,
  ]);

  const guidance = useMemo(
    () =>
      buildIntakeV6OperatorGuidanceModel({
        state: workspaceState,
        canContinueFromAnalyzer,
        confirmChecklist: confirmFooter
          ? { done: confirmFooter.checklistDone, total: confirmFooter.checklistTotal }
          : null,
        confirmDisabledReason: confirmFooter?.disabledReason ?? null,
        confirmCanSubmit: confirmFooter?.canSubmit ?? false,
        attentionIssues: attentionIssues.length > 0 ? attentionIssues : null,
        informationIssues,
      }),
    [
      workspaceState,
      canContinueFromAnalyzer,
      confirmFooter,
      attentionIssues,
      informationIssues,
    ],
  );

  const stepLabel =
    currentStep === "layers" ? "straturi" : currentStep === "review" ? "configurare" : "confirmare";

  const centerLabel = isHandoffStep && confirmFooter
    ? `Confirmări ${confirmFooter.checklistDone}/${confirmFooter.checklistTotal}`
    : `Pasul ${stepIndex + 1} din ${stepOrderLength} - ${stepLabel}`;

  const confirmDisabledReason =
    isHandoffStep && confirmFooter?.disabledReason && !confirmFooter.canSubmit
      ? confirmFooter.disabledReason
      : null;

  const primaryActionReason =
    guidance.nextAction ??
    normalizeGuidanceNextAction(
      isHandoffStep || nextDisabled ? confirmDisabledReason ?? footerBlocker : footerBlocker,
    );

  const drawerGroups = useMemo(() => {
    const groups: Array<{
      id: "blockers" | "warnings" | "information";
      label: string;
      entries: GuidanceAttentionIssue[];
    }> = [];
    if (guidance.blockers.length > 0) {
      groups.push({ id: "blockers", label: "Blocante", entries: guidance.blockers });
    }
    if (guidance.warnings.length > 0) {
      groups.push({ id: "warnings", label: "Avertizări", entries: guidance.warnings });
    }
    if (guidance.information.length > 0) {
      groups.push({ id: "information", label: "Informații", entries: guidance.information });
    }
    return groups;
  }, [guidance.blockers, guidance.warnings, guidance.information]);

  const showIssuesDrawer =
    guidance.blockerCount + guidance.warningCount + guidance.informationCount > 0;

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

  const countLabel = guidance.drawerToggleLabel;

  return (
    <footer
      className="sticky bottom-0 z-10 mt-auto border-t border-[#2A3548] bg-[#111827]/95 px-5 py-2 shadow-[0_-6px_18px_rgba(0,0,0,0.28)] backdrop-blur-sm"
      data-testid="intake-v6-operator-workspace-footer"
      data-footer-weight="compact"
    >
      {(nextDisabled || isHandoffStep || guidance.nextAction || !guidance.canContinue) &&
      (primaryActionReason || guidance.progressLabel || guidance.countsLabel) ? (
        <div
          id="intake-v6-footer-primary-action-reason"
          className="mb-1.5 flex flex-wrap items-baseline gap-x-2 gap-y-0.5 px-0.5 text-[11px] leading-snug text-slate-300"
          data-testid="intake-v6-footer-primary-action-reason"
          data-guidance-status={guidance.statusLabel}
          role="status"
          aria-live="polite"
        >
          <span className="font-semibold text-slate-200" data-testid="intake-v6-guidance-status">
            {guidance.statusLabel}
          </span>
          {guidance.progressLabel ? (
            <span className="text-slate-500" data-testid="intake-v6-guidance-progress">
              · {guidance.progressLabel}
            </span>
          ) : null}
          {guidance.countsLabel ? (
            <span className="text-slate-500" data-testid="intake-v6-guidance-counts">
              · {guidance.countsLabel}
            </span>
          ) : null}
          {primaryActionReason ? (
            <span className="basis-full text-slate-200" data-testid="intake-v6-guidance-next-action">
              <span className="font-semibold text-slate-100">Următorul pas: </span>
              {primaryActionReason}
            </span>
          ) : guidance.canContinue ? (
            <span className="basis-full text-emerald-100/90" data-testid="intake-v6-guidance-next-action">
              <span className="font-semibold">Următorul pas: </span>
              {guidance.continueEnabledLabel}
            </span>
          ) : null}
          <span className="sr-only" data-testid="intake-v6-guidance-spine">
            {guidance.statusLabel}
          </span>
        </div>
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
              <p className="mb-2 text-[10px] text-slate-500" data-testid="intake-v6-footer-issues-breakdown">
                {guidance.drawerToggleLabel}
              </p>
              {drawerGroups.map((group) => (
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
                        data-issue-severity={entry.severity}
                      >
                        <span>{entry.message}</span>
                        {entry.action && !entry.action.startsWith("jump-") && entry.action.length > 2 ? (
                          <span className="mt-0.5 block text-[10px] text-slate-500">{entry.action}</span>
                        ) : null}
                        {entry.action && /^(confirm-step|jump-)/.test(entry.action) ? (
                          <button
                            type="button"
                            className="ml-2 text-[10px] font-semibold text-cyan-300 hover:text-cyan-200"
                            onClick={() => handleStatusAction(entry.action!)}
                            data-testid={`intake-v6-footer-issue-action-${entry.action}`}
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

        {isHandoffStep && confirmFooter ? (
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
            aria-describedby={
              nextDisabled && primaryActionReason
                ? "intake-v6-footer-primary-action-reason"
                : undefined
            }
          >
            {nextLabel}
          </button>
        )}
      </div>
    </footer>
  );
}
