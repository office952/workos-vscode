import { useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  blockEmployeeMobileTask,
  type EmployeeMobileTaskDTO,
} from "@/api/employeeMobileTasks";
import { useEmployeeMobileV2Tasks } from "@/hooks/useEmployeeMobileV2Tasks";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
  EmployeeMobileSuccessState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
import EmployeeMobileV2TaskRow from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskRow";
import {
  emV2PrimaryButtonClass,
  emV2SecondaryButtonClass,
  emV2SectionLabelClass,
  emV2Surface,
} from "@/lib/employeeMobileV2DesignTokens";
import { v2Motion } from "@/lib/employeeMobileV2Effects";
import {
  BLOCK_REASON_CATEGORIES,
  composeBlockedReason,
  type BlockReasonCategoryId,
} from "@/lib/employeeMobileShopFloorPresentation";
import { pickBlockedTasks } from "@/lib/employeeMobileTaskSummary";
import { cn } from "@/lib/utils";

function pickBlockEligibleTask(tasks: EmployeeMobileTaskDTO[]): EmployeeMobileTaskDTO | null {
  return tasks.find((task) => task.status === "in_progress") ?? null;
}

export default function EmployeeMobileV2BlockersPage() {
  const { tasks, loading, error, reload } = useEmployeeMobileV2Tasks();
  const blockedTasks = useMemo(() => pickBlockedTasks(tasks), [tasks]);
  const eligibleTask = useMemo(() => pickBlockEligibleTask(tasks), [tasks]);

  const [showForm, setShowForm] = useState(false);
  const [blockCategory, setBlockCategory] = useState<BlockReasonCategoryId | "">("");
  const [blockReason, setBlockReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  const submitBlock = async () => {
    if (!eligibleTask || !blockCategory) return;
    setSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);
    try {
      await blockEmployeeMobileTask(
        eligibleTask.task_id,
        eligibleTask.order_id,
        composeBlockedReason(blockCategory, blockReason),
      );
      setSubmitSuccess("Blocaj raportat.");
      setShowForm(false);
      setBlockCategory("");
      setBlockReason("");
      await reload();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Nu am putut raporta blocajul.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div data-testid="employee-mobile-v2-blockers">
      <EmployeeMobileV2PageHeader
        backTo="/employee-app-v2"
        title="Blocaje"
        subtitle="Raportează sau vezi blocaje active"
        testId="employee-mobile-v2-blockers-header"
      />

      {loading ? (
        <EmployeeMobileLoadingState
          message="Se încarcă blocajele…"
          testId="employee-mobile-v2-blockers-loading"
        />
      ) : null}

      {!loading && error ? (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-blockers-error" />
      ) : null}

      {!loading && !error ? (
        <>
          <p className={cn(emV2SectionLabelClass(), "mb-3")}>Blocaje active</p>
          {blockedTasks.length === 0 ? (
            <EmployeeMobileEmptyState
              message="Nu ai blocaje active."
              testId="employee-mobile-v2-blockers-empty"
            />
          ) : (
            <div className="space-y-2 mb-6" data-testid="employee-mobile-v2-blockers-list">
              {blockedTasks.map((task) => (
                <div key={`${task.order_id}-${task.task_id}`} className="space-y-1">
                  <EmployeeMobileV2TaskRow task={task} />
                  {task.blocked_reason ? (
                    <p className="px-1 text-[12px] text-amber-300/90">{task.blocked_reason}</p>
                  ) : null}
                </div>
              ))}
            </div>
          )}

          {eligibleTask ? (
            <div className="space-y-3" data-testid="employee-mobile-v2-blockers-report">
              {!showForm ? (
                <button
                  type="button"
                  className={emV2SecondaryButtonClass()}
                  onClick={() => setShowForm(true)}
                  data-testid="employee-mobile-v2-blockers-report-open"
                >
                  Raportează blocaj nou
                </button>
              ) : (
                <div
                  className={cn(emV2Surface.panel, "p-4 space-y-3")}
                  data-testid="employee-mobile-v2-blockers-form"
                >
                  <p className="text-sm font-medium text-slate-200">
                    Raportează pentru: {eligibleTask.title || eligibleTask.task_id}
                  </p>
                  <label className="block text-sm text-slate-400" htmlFor="v2-block-category">
                    Motiv
                  </label>
                  <select
                    id="v2-block-category"
                    value={blockCategory}
                    onChange={(event) =>
                      setBlockCategory(event.target.value as BlockReasonCategoryId | "")
                    }
                    className="w-full min-h-[48px] rounded-lg border border-[#1E293B] bg-[#0B1120] px-3 text-base text-slate-100"
                    data-testid="employee-mobile-v2-blockers-category"
                  >
                    <option value="">Selectează motivul</option>
                    {BLOCK_REASON_CATEGORIES.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <label className="block text-sm text-slate-400" htmlFor="v2-block-message">
                    Mesaj scurt
                  </label>
                  <textarea
                    id="v2-block-message"
                    value={blockReason}
                    onChange={(event) => setBlockReason(event.target.value)}
                    rows={3}
                    placeholder="Descrie pe scurt blocajul…"
                    className="w-full rounded-lg border border-[#1E293B] bg-[#0B1120] px-3 py-2.5 text-base text-slate-100"
                    data-testid="employee-mobile-v2-blockers-message"
                  />
                  <button
                    type="button"
                    className={emV2PrimaryButtonClass()}
                    disabled={submitting || !blockCategory}
                    onClick={() => void submitBlock()}
                    data-testid="employee-mobile-v2-blockers-submit"
                  >
                    {submitting ? (
                      <span className="inline-flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                        Se trimite…
                      </span>
                    ) : (
                      "Trimite"
                    )}
                  </button>
                  <button
                    type="button"
                    className={cn(
                      "inline-flex min-h-[44px] w-full items-center justify-center text-sm text-slate-500 hover:text-slate-300",
                      v2Motion.tapTarget,
                    )}
                    onClick={() => {
                      setShowForm(false);
                      setBlockCategory("");
                      setBlockReason("");
                    }}
                    data-testid="employee-mobile-v2-blockers-cancel"
                  >
                    Anulează
                  </button>
                </div>
              )}
            </div>
          ) : null}

          {submitError ? (
            <EmployeeMobileErrorState
              message={submitError}
              testId="employee-mobile-v2-blockers-submit-error"
            />
          ) : null}
          {submitSuccess ? (
            <EmployeeMobileSuccessState
              message={submitSuccess}
              testId="employee-mobile-v2-blockers-submit-success"
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
