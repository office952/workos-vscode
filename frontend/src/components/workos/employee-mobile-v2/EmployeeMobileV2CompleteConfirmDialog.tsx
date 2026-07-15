import { Loader2 } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  buildActiveSessionSummary,
  formatSessionStartTime,
} from "@/lib/employeeMobileV2ActiveSessionPresentation";
import { emV2Controls, emV2SecondaryButtonClass } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2CompleteConfirmDialog({
  task,
  open,
  pending,
  onConfirm,
  onCancel,
  testIdPrefix = "employee-mobile-v2-complete-confirm",
}: {
  task: EmployeeMobileTaskDTO;
  open: boolean;
  pending: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  testIdPrefix?: string;
}) {
  if (!open) return null;

  const summary = buildActiveSessionSummary(task);
  const startedLabel = formatSessionStartTime(task.started_at);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 px-4 pb-[calc(5rem+env(safe-area-inset-bottom,0px))]"
      role="dialog"
      aria-modal="true"
      aria-labelledby={`${testIdPrefix}-title`}
      data-testid={testIdPrefix}
    >
      <div className="w-full max-w-[430px] rounded-2xl border border-[#1E293B] bg-[#111827] p-4 shadow-xl">
        <h3
          id={`${testIdPrefix}-title`}
          className="text-base font-semibold text-slate-100"
          data-testid={`${testIdPrefix}-title`}
        >
          Finalizezi taskul?
        </h3>
        <p className="mt-2 text-sm text-slate-300" data-testid={`${testIdPrefix}-task-label`}>
          {summary.title}
        </p>
        {summary.component ? (
          <p className="mt-1 text-[13px] text-slate-500" data-testid={`${testIdPrefix}-component`}>
            {summary.component}
          </p>
        ) : null}
        {startedLabel ? (
          <p className="mt-2 text-[13px] text-sky-300/90" data-testid={`${testIdPrefix}-session`}>
            Sesiune activă · început {startedLabel}
          </p>
        ) : null}
        <p className="mt-3 text-[13px] text-amber-200/90 leading-snug" data-testid={`${testIdPrefix}-warning`}>
          Taskul va fi marcat ca finalizat. Verifică că lucrarea este completă înainte de confirmare.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            className={cn(emV2SecondaryButtonClass(), "min-h-[44px]")}
            disabled={pending}
            onClick={onCancel}
            data-testid={`${testIdPrefix}-cancel`}
          >
            Anulez
          </button>
          <button
            type="button"
            className={cn(emV2Controls.primaryAction, "min-h-[44px]")}
            disabled={pending}
            onClick={onConfirm}
            data-testid={`${testIdPrefix}-confirm`}
          >
            {pending ? (
              <span className="inline-flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                Se finalizează…
              </span>
            ) : (
              "Confirm finalizarea"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
