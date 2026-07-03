import { useState } from "react";
import { CheckCircle2, Loader2, MoreHorizontal, OctagonAlert, Play } from "lucide-react";
import {
  blockEmployeeMobileTask,
  completeEmployeeMobileTask,
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
import {
  emPrimaryButtonClass,
  emSecondaryLinkClass,
  emSurface,
} from "@/lib/employeeMobileDesignTokens";
import { emV2Controls, emV2SecondaryButtonClass } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

export default function EmployeeMobileTaskActionBar({
  task,
  onActionComplete,
  layout = "default",
  visualVariant = "v1",
  testIdPrefix = "employee-mobile-task",
}: {
  task: EmployeeMobileTaskDTO;
  onActionComplete: () => Promise<void>;
  layout?: "default" | "shopFloor" | "sticky" | "embedded";
  visualVariant?: "v1" | "v2";
  testIdPrefix?: string;
}) {
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [blockReason, setBlockReason] = useState("");
  const [blockCategory, setBlockCategory] = useState<BlockReasonCategoryId | "">("");
  const [showBlockForm, setShowBlockForm] = useState(false);
  const [showOverflow, setShowOverflow] = useState(false);
  const compact = layout === "shopFloor" || layout === "sticky" || layout === "embedded";
  const sticky = layout === "sticky";
  const isV2 = visualVariant === "v2";

  const primaryButtonClass = (destructive = false) => {
    if (isV2) {
      return cn(
        emV2Controls.primaryAction,
        destructive && "bg-red-900/70 hover:bg-red-900/85",
      );
    }
    return cn(
      emPrimaryButtonClass(compact),
      destructive && "bg-red-900/40 text-red-100 border border-red-700/50 hover:bg-red-900/60",
    );
  };

  const secondaryLinkClass = () => (isV2 ? emV2Controls.destructiveTextAction : emSecondaryLinkClass());

  const runAction = async (action: () => Promise<unknown>, successMessage: string) => {
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await action();
      setActionSuccess(successMessage);
      setShowBlockForm(false);
      setShowOverflow(false);
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
  const canUnblock = task.status === "blocked";

  const blockForm = showBlockForm ? (
    <div
      className={cn(
        isV2 ? "rounded-lg border border-[#1E293B] bg-[#111827] p-3" : emSurface.panel,
        "space-y-3",
        !isV2 && "border-red-800/30",
      )}
      data-testid={`${testIdPrefix}-block-form`}
    >
      <p className="text-sm font-medium text-slate-200">Motiv blocaj</p>
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
      <label className="block text-sm text-slate-300" htmlFor={`${testIdPrefix}-block-reason`}>
        Mesaj (opțional)
      </label>
      <textarea
        id={`${testIdPrefix}-block-reason`}
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

  const wrapperClass = sticky
    ? "fixed bottom-[calc(52px+env(safe-area-inset-bottom,0px))] inset-x-0 z-30 border-t border-[#243044] bg-[#0A1020]/95 backdrop-blur-md px-4 py-3 space-y-2 max-w-lg mx-auto"
    : isV2
      ? emV2Controls.actionGroup
      : "space-y-2";

  return (
    <div className={wrapperClass} data-testid={`${testIdPrefix}-actions`}>
      {actionError && (
        <EmployeeMobileErrorState message={actionError} testId={`${testIdPrefix}-action-error`} />
      )}
      {actionSuccess && (
        <EmployeeMobileSuccessState message={actionSuccess} testId={`${testIdPrefix}-action-success`} />
      )}

      {canStart && (
        <button
          type="button"
          className={primaryButtonClass()}
          disabled={actionLoading}
          onClick={() =>
            runAction(
              () => startEmployeeMobileTask(task.task_id, task.order_id),
              "Task pornit.",
            )
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
      )}

      {canComplete && (
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
            {actionLoading ? (
              <span className="inline-flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                Se finalizează…
              </span>
            ) : (
              <span className="inline-flex items-center justify-center gap-2">
                <CheckCircle2 className="w-4 h-4" aria-hidden />
                Finalizez
              </span>
            )}
          </button>

          {compact ? (
            <div className={isV2 ? emV2Controls.actionSecondaryRow : "flex items-center justify-between gap-2"}>
              {!showBlockForm ? (
                <button
                  type="button"
                  className={secondaryLinkClass()}
                  disabled={actionLoading}
                  onClick={() => {
                    setShowBlockForm(true);
                    setShowOverflow(false);
                  }}
                  data-testid={`${testIdPrefix}-block-open`}
                >
                  <OctagonAlert className="w-3.5 h-3.5" aria-hidden />
                  Raportez blocaj
                </button>
              ) : null}
              {sticky ? (
                <button
                  type="button"
                  className={emSecondaryLinkClass()}
                  onClick={() => setShowOverflow((current) => !current)}
                  aria-expanded={showOverflow}
                  data-testid={`${testIdPrefix}-overflow-toggle`}
                >
                  <MoreHorizontal className="w-4 h-4" aria-hidden />
                </button>
              ) : null}
            </div>
          ) : !showBlockForm ? (
            <button
              type="button"
              className={isV2 ? secondaryLinkClass() : cn(primaryButtonClass(true))}
              disabled={actionLoading}
              onClick={() => setShowBlockForm(true)}
              data-testid={`${testIdPrefix}-block-open`}
            >
              <span className="inline-flex items-center justify-center gap-2">
                <OctagonAlert className="w-4 h-4" aria-hidden />
                Raportez blocaj
              </span>
            </button>
          ) : null}

          {blockForm}
        </>
      )}

      {canUnblock && (
        <button
          type="button"
          className={
            isV2
              ? cn(emV2SecondaryButtonClass())
              : cn(emPrimaryButtonClass(compact), "bg-[#0A1020] text-slate-200 border border-[#243044] hover:border-slate-500")
          }
          disabled={actionLoading}
          onClick={() =>
            runAction(
              () => unblockEmployeeMobileTask(task.task_id, task.order_id),
              "Task reluat.",
            )
          }
          data-testid={`${testIdPrefix}-unblock`}
        >
          Reiau task
        </button>
      )}
    </div>
  );
}
