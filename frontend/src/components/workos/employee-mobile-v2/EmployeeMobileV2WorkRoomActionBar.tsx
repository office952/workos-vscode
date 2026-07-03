import { useState } from "react";
import {
  CheckCircle2,
  Loader2,
  OctagonAlert,
  PauseCircle,
  Play,
  PlayCircle,
} from "lucide-react";
import {
  blockEmployeeMobileTask,
  completeEmployeeMobileTask,
  pauseEmployeeMobileTask,
  resumeEmployeeMobileTask,
  startEmployeeMobileTask,
  unblockEmployeeMobileTask,
  type EmployeeMobileTaskDTO,
} from "@/api/employeeMobileTasks";
import {
  EmployeeMobileErrorState,
  EmployeeMobileSuccessState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import {
  BLOCK_REASON_CATEGORIES,
  composeBlockedReason,
  type BlockReasonCategoryId,
} from "@/lib/employeeMobileShopFloorPresentation";
import { emV2Controls, emV2SecondaryButtonClass } from "@/lib/employeeMobileV2DesignTokens";
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
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [blockReason, setBlockReason] = useState("");
  const [blockCategory, setBlockCategory] = useState<BlockReasonCategoryId | "">("");
  const [showBlockForm, setShowBlockForm] = useState(false);

  const runAction = async (action: () => Promise<unknown>, successMessage: string) => {
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await action();
      setActionSuccess(successMessage);
      setShowBlockForm(false);
      setBlockReason("");
      setBlockCategory("");
      await onActionComplete();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Acțiunea a eșuat.");
    } finally {
      setActionLoading(false);
    }
  };

  const canStart = task.status === "assigned" && task.is_startable === true;
  const canComplete = task.status === "in_progress";
  const canPause = task.status === "in_progress";
  const canResume = task.status === "paused";
  const canUnblock = task.status === "blocked";

  const primaryButtonClass = (destructive = false) =>
    cn(emV2Controls.primaryAction, destructive && "bg-red-900/70 hover:bg-red-900/85");

  const blockForm = showBlockForm ? (
    <div
      className="rounded-lg border border-[#1E293B] bg-[#111827] p-3 space-y-3"
      data-testid={`${testIdPrefix}-block-form`}
    >
      <p className="text-sm font-medium text-slate-200">Motiv blocaj</p>
      <p className="text-xs text-slate-500">
        Blochează doar când există un impediment real care oprește lucrul.
      </p>
      <div className="space-y-1.5">
        {BLOCK_REASON_CATEGORIES.map((option) => (
          <label
            key={option.id}
            className={cn(
              "flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm",
              blockCategory === option.id
                ? "border-red-600/60 bg-red-950/30 text-red-100"
                : "border-[#243044] text-slate-300",
            )}
          >
            <input
              type="radio"
              name={`${testIdPrefix}-block-category`}
              value={option.id}
              checked={blockCategory === option.id}
              onChange={() => setBlockCategory(option.id)}
              className="accent-red-500"
              data-testid={`${testIdPrefix}-block-category-${option.id}`}
            />
            {option.label}
          </label>
        ))}
      </div>
      <textarea
        value={blockReason}
        onChange={(event) => setBlockReason(event.target.value)}
        rows={3}
        placeholder="Descrie pe scurt problema…"
        className="w-full rounded-lg border border-[#243044] bg-[#070B14] px-3 py-2 text-sm text-slate-100"
        data-testid={`${testIdPrefix}-block-reason`}
      />
      <button
        type="button"
        className={primaryButtonClass(true)}
        disabled={actionLoading || !blockCategory}
        onClick={() =>
          runAction(
            () =>
              blockEmployeeMobileTask(
                task.task_id,
                task.order_id,
                composeBlockedReason(blockCategory as BlockReasonCategoryId, blockReason),
              ),
            "Task blocat.",
          )
        }
        data-testid={`${testIdPrefix}-block-submit`}
      >
        Trimite blocaj
      </button>
    </div>
  ) : null;

  return (
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

      {canStart ? (
        <button
          type="button"
          className={primaryButtonClass()}
          disabled={actionLoading}
          onClick={() =>
            runAction(async () => {
              await startEmployeeMobileTask(task.task_id, task.order_id);
              onStartSuccess?.();
            }, "Task pornit.")
          }
          data-testid={`${testIdPrefix}-start`}
        >
          {actionLoading ? (
            <span className="inline-flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              Se pornește…
            </span>
          ) : (
            <span className="inline-flex items-center justify-center gap-2">
              <Play className="w-4 h-4" aria-hidden />
              Încep task
            </span>
          )}
        </button>
      ) : null}

      {canComplete ? (
        <>
          <button
            type="button"
            className={primaryButtonClass()}
            disabled={actionLoading}
            onClick={() =>
              runAction(
                () => completeEmployeeMobileTask(task.task_id, task.order_id),
                "Task finalizat.",
              )
            }
            data-testid={`${testIdPrefix}-complete`}
          >
            <span className="inline-flex items-center justify-center gap-2">
              {actionLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              ) : (
                <CheckCircle2 className="w-4 h-4" aria-hidden />
              )}
              Finalizez
            </span>
          </button>

          <div className={emV2Controls.actionSecondaryRow}>
            {!showBlockForm ? (
              <button
                type="button"
                className={emV2Controls.destructiveTextAction}
                disabled={actionLoading}
                onClick={() => setShowBlockForm(true)}
                data-testid={`${testIdPrefix}-block-open`}
              >
                <OctagonAlert className="w-3.5 h-3.5" aria-hidden />
                Blochez
              </button>
            ) : null}
            <button
              type="button"
              className={emV2Controls.destructiveTextAction}
              disabled={actionLoading}
              onClick={() =>
                runAction(
                  () => pauseEmployeeMobileTask(task.task_id, task.order_id),
                  "Lucrul a fost întrerupt.",
                )
              }
              data-testid={`${testIdPrefix}-pause`}
            >
              <PauseCircle className="w-3.5 h-3.5" aria-hidden />
              Întrerup lucrul
            </button>
          </div>
          <p className="text-[11px] text-slate-500 px-0.5" data-testid={`${testIdPrefix}-pause-hint`}>
            Întreruperea nu marchează taskul ca blocat.
          </p>
          {blockForm}
        </>
      ) : null}

      {canResume ? (
        <>
          <button
            type="button"
            className={cn(emV2SecondaryButtonClass())}
            disabled={actionLoading}
            onClick={() =>
              runAction(
                () => resumeEmployeeMobileTask(task.task_id, task.order_id),
                "Lucrul a fost reluat.",
              )
            }
            data-testid={`${testIdPrefix}-resume`}
          >
            <span className="inline-flex items-center justify-center gap-2">
              <PlayCircle className="w-4 h-4" aria-hidden />
              Reiau lucrul
            </span>
          </button>
          {!showBlockForm ? (
            <button
              type="button"
              className={emV2Controls.destructiveTextAction}
              disabled={actionLoading}
              onClick={() => setShowBlockForm(true)}
              data-testid={`${testIdPrefix}-block-open`}
            >
              <OctagonAlert className="w-3.5 h-3.5" aria-hidden />
              Blochez
            </button>
          ) : null}
          {blockForm}
        </>
      ) : null}

      {canUnblock ? (
        <button
          type="button"
          className={cn(emV2SecondaryButtonClass())}
          disabled={actionLoading}
          onClick={() =>
            runAction(
              () => unblockEmployeeMobileTask(task.task_id, task.order_id),
              "Blocaj eliminat.",
            )
          }
          data-testid={`${testIdPrefix}-unblock`}
        >
          Deblochez task
        </button>
      ) : null}
    </div>
  );
}
