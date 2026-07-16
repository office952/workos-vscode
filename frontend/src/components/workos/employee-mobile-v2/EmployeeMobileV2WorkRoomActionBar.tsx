import { useState } from "react";
import { CheckCircle2, Hand, Loader2, Play, PlayCircle, Square } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  CollaborationApiError,
  startMobileHelperSession,
  stopMobileHelperSession,
} from "@/api/collaboration";
import {
  EmployeeMobileErrorState,
  EmployeeMobileSuccessState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import EmployeeMobileV2CompleteConfirmDialog from "@/components/workos/employee-mobile-v2/EmployeeMobileV2CompleteConfirmDialog";
import { useEmployeeMobileV2ClaimAction } from "@/hooks/useEmployeeMobileV2ClaimAction";
import { useEmployeeMobileV2RuntimeAction } from "@/hooks/useEmployeeMobileV2RuntimeAction";
import { useEmployeeMobileV2StartAction } from "@/hooks/useEmployeeMobileV2StartAction";
import { buildEmployeeMobileV2BlockerPresentation } from "@/lib/employeeMobileV2BlockerPresentation";
import {
  canShowClaimOnly,
  CLAIM_ONLY_LABEL,
  CLAIM_PENDING_LABEL,
} from "@/lib/employeeMobileV2ClaimAction";
import { emV2Controls } from "@/lib/employeeMobileV2DesignTokens";
import {
  canShowAssignedStart,
  canShowAvailableStart,
  ASSIGNED_START_LABEL,
  AVAILABLE_START_LABEL,
  START_PENDING_LABEL,
} from "@/lib/employeeMobileV2StartAction";
import {
  canShowComplete,
  COMPLETE_LABEL,
  COMPLETE_PENDING_LABEL,
} from "@/lib/employeeMobileV2RuntimeAction";
import { isFlexCollabUiEnabled } from "@/lib/flexCollabUiFlag";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2WorkRoomActionBar({
  task,
  onActionComplete,
  onStartSuccess,
  testIdPrefix = "employee-mobile-v2-work-room",
}: {
  task: EmployeeMobileTaskDTO;
  onActionComplete: () => Promise<void>;
  onStartSuccess?: () => void;
  testIdPrefix?: string;
}) {
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [showCompleteConfirm, setShowCompleteConfirm] = useState(false);
  const [helperBusy, setHelperBusy] = useState(false);
  const [helperError, setHelperError] = useState<string | null>(null);
  const {
    startTask,
    isPending: startIsPending,
    error: startError,
    clearError: clearStartError,
  } = useEmployeeMobileV2StartAction();
  const {
    completeTask,
    isPending: completeIsPending,
    error: runtimeError,
    clearError: clearRuntimeError,
  } = useEmployeeMobileV2RuntimeAction();
  const {
    claimTask,
    isPending: claimIsPending,
    error: claimError,
    clearError: clearClaimError,
  } = useEmployeeMobileV2ClaimAction();

  const collabUi = isFlexCollabUiEnabled();
  const blockerPresentation = buildEmployeeMobileV2BlockerPresentation(task);
  const helperOnly =
    collabUi &&
    task.visible_as_helper === true &&
    task.visible_as_principal !== true;
  const canStartHelper = collabUi && helperOnly && task.can_start_helper_work === true;
  // Stop is helper-session only — never surface for principal-only active work.
  const canStopOwn =
    collabUi &&
    task.visible_as_helper === true &&
    task.can_stop_own_session === true;
  const canStartAssigned = !helperOnly && canShowAssignedStart(task);
  const canStartAvailable = !helperOnly && canShowAvailableStart(task);
  const canClaimOnly = !helperOnly && canShowClaimOnly(task);
  const canComplete =
    !helperOnly &&
    canShowComplete(task) &&
    (task.can_complete_operation !== false || !collabUi);
  const startPending = startIsPending(task);
  const completePending = completeIsPending(task);
  const claimPending = claimIsPending(task);
  const actionError = runtimeError || startError || claimError || helperError;
  const showDisabledStart =
    !canStartAssigned &&
    !canStartAvailable &&
    !canStartHelper &&
    task.status !== "in_progress" &&
    task.status !== "done" &&
    (task.is_assigned_to_current_employee || task.is_available_for_claim);
  const startLabel = canStartAvailable ? AVAILABLE_START_LABEL : ASSIGNED_START_LABEL;

  const handleStart = async () => {
    clearRuntimeError();
    clearStartError();
    clearClaimError();
    setHelperError(null);
    setActionSuccess(null);
    try {
      await startTask(task, async () => {
        setActionSuccess(canStartAvailable ? "Task preluat și pornit." : "Task pornit.");
        onStartSuccess?.();
        await onActionComplete();
      });
    } catch {
      // error surfaced via start hook
    }
  };

  const handleHelperStart = async () => {
    clearStartError();
    clearRuntimeError();
    clearClaimError();
    setHelperError(null);
    setActionSuccess(null);
    setHelperBusy(true);
    try {
      await startMobileHelperSession(task.order_id, task.task_id);
      setActionSuccess("Sesiune helper pornită.");
      onStartSuccess?.();
      await onActionComplete();
    } catch (e) {
      if (e instanceof CollaborationApiError) {
        setHelperError(`${e.code}: ${e.message}`);
      } else if (e instanceof Error) {
        setHelperError(e.message);
      } else {
        setHelperError("Nu am putut porni sesiunea helper.");
      }
    } finally {
      setHelperBusy(false);
    }
  };

  const handleHelperStop = async () => {
    clearStartError();
    clearRuntimeError();
    clearClaimError();
    setHelperError(null);
    setActionSuccess(null);
    setHelperBusy(true);
    try {
      await stopMobileHelperSession(task.order_id, task.task_id);
      setActionSuccess("Sesiune helper oprită. Operația rămâne incompletă.");
      await onActionComplete();
    } catch (e) {
      if (e instanceof CollaborationApiError) {
        setHelperError(`${e.code}: ${e.message}`);
      } else if (e instanceof Error) {
        setHelperError(e.message);
      } else {
        setHelperError("Nu am putut opri sesiunea helper.");
      }
    } finally {
      setHelperBusy(false);
    }
  };

  const handleClaim = async () => {
    clearStartError();
    clearRuntimeError();
    clearClaimError();
    setHelperError(null);
    setActionSuccess(null);
    try {
      await claimTask(task, async () => {
        setActionSuccess("Task preluat.");
        await onActionComplete();
      });
    } catch {
      // surfaced via claim hook
    }
  };

  const handleCompleteConfirm = async () => {
    clearStartError();
    clearRuntimeError();
    clearClaimError();
    setHelperError(null);
    setActionSuccess(null);
    try {
      await completeTask(task, async () => {
        setActionSuccess("Task finalizat.");
        setShowCompleteConfirm(false);
        await onActionComplete();
      });
    } catch {
      // error surfaced via runtime hook
    }
  };

  return (
    <>
      <div className={emV2Controls.actionGroup} data-testid={`${testIdPrefix}-actions`}>
        {actionError ? (
          <EmployeeMobileErrorState message={actionError} testId={`${testIdPrefix}-action-error`} />
        ) : null}
        {actionSuccess ? (
          <EmployeeMobileSuccessState
            message={actionSuccess}
            testId={`${testIdPrefix}-action-success`}
          />
        ) : null}

        {helperOnly ? (
          <p
            className="text-[12px] text-slate-500 leading-snug"
            data-testid={`${testIdPrefix}-helper-role-note`}
          >
            Rol helper: poți porni/opri doar sesiunea ta. Finalizarea rămâne la
            principal.
          </p>
        ) : null}

        {canStartHelper ? (
          <button
            type="button"
            className={emV2Controls.primaryAction}
            disabled={helperBusy || startPending || completePending}
            onClick={() => void handleHelperStart()}
            data-testid={`${testIdPrefix}-helper-start`}
          >
            <span className="inline-flex items-center justify-center gap-2">
              {helperBusy ? (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              ) : (
                <Play className="w-4 h-4" aria-hidden />
              )}
              Pornește ajutorul
            </span>
          </button>
        ) : null}

        {canStopOwn ? (
          <button
            type="button"
            className={emV2Controls.secondaryAction}
            disabled={helperBusy || startPending || completePending}
            onClick={() => void handleHelperStop()}
            data-testid={`${testIdPrefix}-helper-stop`}
          >
            <span className="inline-flex items-center justify-center gap-2">
              {helperBusy ? (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              ) : (
                <Square className="w-4 h-4" aria-hidden />
              )}
              Oprește sesiunea mea
            </span>
          </button>
        ) : null}

        {canStartAssigned || canStartAvailable ? (
          <button
            type="button"
            className={emV2Controls.primaryAction}
            disabled={startPending || completePending || claimPending || helperBusy}
            onClick={() => void handleStart()}
            data-testid={`${testIdPrefix}-start`}
          >
            {startPending ? (
              <span className="inline-flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                {START_PENDING_LABEL}
              </span>
            ) : (
              <span className="inline-flex items-center justify-center gap-2">
                <Play className="w-4 h-4" aria-hidden />
                {startLabel}
              </span>
            )}
          </button>
        ) : showDisabledStart ? (
          <div className="space-y-2" data-testid={`${testIdPrefix}-start-disabled`}>
            <button
              type="button"
              className={cn(emV2Controls.primaryAction, "opacity-50 cursor-not-allowed")}
              disabled
              data-testid={`${testIdPrefix}-start-blocked`}
            >
              <span className="inline-flex items-center justify-center gap-2">
                <PlayCircle className="w-4 h-4" aria-hidden />
                {startLabel}
              </span>
            </button>
            <p className="text-xs text-slate-500 leading-snug">
              {blockerPresentation.canStartExplanation}
            </p>
          </div>
        ) : null}

        {canClaimOnly ? (
          <button
            type="button"
            className={emV2Controls.secondaryAction}
            disabled={claimPending || startPending || completePending || helperBusy}
            onClick={() => void handleClaim()}
            data-testid={`${testIdPrefix}-claim`}
          >
            {claimPending ? (
              <span className="inline-flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                {CLAIM_PENDING_LABEL}
              </span>
            ) : (
              <span className="inline-flex items-center justify-center gap-2">
                <Hand className="w-4 h-4" aria-hidden />
                {CLAIM_ONLY_LABEL}
              </span>
            )}
          </button>
        ) : null}

        {canComplete ? (
          <button
            type="button"
            className={emV2Controls.primaryAction}
            disabled={completePending || startPending || claimPending || helperBusy}
            onClick={() => {
              clearStartError();
              clearRuntimeError();
              setShowCompleteConfirm(true);
            }}
            data-testid={`${testIdPrefix}-complete`}
          >
            <span className="inline-flex items-center justify-center gap-2">
              {completePending ? (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              ) : (
                <CheckCircle2 className="w-4 h-4" aria-hidden />
              )}
              {completePending ? COMPLETE_PENDING_LABEL : COMPLETE_LABEL}
            </span>
          </button>
        ) : null}
      </div>

      <EmployeeMobileV2CompleteConfirmDialog
        task={task}
        open={showCompleteConfirm}
        pending={completePending}
        onConfirm={() => void handleCompleteConfirm()}
        onCancel={() => {
          if (!completePending) setShowCompleteConfirm(false);
        }}
        testIdPrefix={`${testIdPrefix}-complete-confirm`}
      />
    </>
  );
}
