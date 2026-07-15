import { useState } from "react";
import { CheckCircle2, Loader2, Play, PlayCircle } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  EmployeeMobileErrorState,
  EmployeeMobileSuccessState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import EmployeeMobileV2CompleteConfirmDialog from "@/components/workos/employee-mobile-v2/EmployeeMobileV2CompleteConfirmDialog";
import { useEmployeeMobileV2RuntimeAction } from "@/hooks/useEmployeeMobileV2RuntimeAction";
import { useEmployeeMobileV2StartAction } from "@/hooks/useEmployeeMobileV2StartAction";
import { buildEmployeeMobileV2BlockerPresentation } from "@/lib/employeeMobileV2BlockerPresentation";
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

  const blockerPresentation = buildEmployeeMobileV2BlockerPresentation(task);
  const canStartAssigned = canShowAssignedStart(task);
  const canStartAvailable = canShowAvailableStart(task);
  const canComplete = canShowComplete(task);
  const startPending = startIsPending(task);
  const completePending = completeIsPending(task);
  const actionError = runtimeError || startError;
  const showDisabledStart =
    !canStartAssigned &&
    !canStartAvailable &&
    task.status !== "in_progress" &&
    task.status !== "done" &&
    (task.is_assigned_to_current_employee || task.is_available_for_claim);
  const startLabel = canStartAvailable ? AVAILABLE_START_LABEL : ASSIGNED_START_LABEL;

  const handleStart = async () => {
    clearRuntimeError();
    clearStartError();
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

  const handleCompleteConfirm = async () => {
    clearStartError();
    clearRuntimeError();
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

        {canStartAssigned || canStartAvailable ? (
          <button
            type="button"
            className={emV2Controls.primaryAction}
            disabled={startPending || completePending}
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

        {canComplete ? (
          <button
            type="button"
            className={emV2Controls.primaryAction}
            disabled={completePending || startPending}
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
