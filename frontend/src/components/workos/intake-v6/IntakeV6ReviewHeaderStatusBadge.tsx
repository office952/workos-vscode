import { ChevronDown } from "lucide-react";
import type { ReviewHeaderStatusModel } from "@/lib/intakeV6/intakeV6ReviewHeaderStatus";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

const TONE_CLASS: Record<ReviewHeaderStatusModel["tone"], string> = {
  success:
    "border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300 dark:hover:bg-emerald-500/15",
  warning:
    "border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200 dark:hover:bg-amber-500/15",
  danger:
    "border-red-200 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200 dark:hover:bg-red-500/15",
  neutral:
    "border-wo-border-strong bg-wo-surface-raised text-wo-text-muted hover:border-slate-400/50 dark:hover:border-slate-500/40",
};

const DETAIL_TONE_CLASS = {
  ok: "text-emerald-700 dark:text-emerald-300/90",
  warn: "text-amber-800 dark:text-amber-200/90",
  bad: "text-red-700 dark:text-red-300/90",
  muted: "text-wo-text-muted",
};

export default function IntakeV6ReviewHeaderStatusBadge({
  status,
  onAction,
  testIdPrefix = "intake-v6-review-header-status",
}: {
  status: ReviewHeaderStatusModel;
  onAction?: (actionId: string) => void;
  testIdPrefix?: string;
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={`inline-flex shrink-0 items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-semibold transition ${TONE_CLASS[status.tone]}`}
          data-testid={`${testIdPrefix}-badge`}
          aria-haspopup="dialog"
        >
          <span data-testid={`${testIdPrefix}-label`}>{status.label}</span>
          <ChevronDown className="h-3 w-3 opacity-70" aria-hidden />
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="w-72 border-wo-border-strong bg-wo-surface-raised p-0 text-wo-text-secondary shadow-xl"
        align="end"
        data-testid={`${testIdPrefix}-popover`}
      >
        <div className="border-b border-wo-border-strong px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-wo-text-dim">
            Stare lucrare
          </p>
        </div>
        <ul
          className="space-y-1 px-3 py-2 text-[11px]"
          data-testid={`${testIdPrefix}-details`}
        >
          {status.details.map((row) => (
            <li key={row.id} className="flex items-baseline justify-between gap-2">
              <span className="text-wo-text-dim">{row.label}</span>
              <span
                className={`text-right font-medium ${DETAIL_TONE_CLASS[row.tone]}`}
                data-testid={`${testIdPrefix}-detail-${row.id}`}
              >
                {row.value}
              </span>
            </li>
          ))}
        </ul>
        {status.actions.length > 0 ? (
          <div
            className="border-t border-wo-border-strong px-3 py-2"
            data-testid={`${testIdPrefix}-actions`}
          >
            <p className="mb-1.5 text-[9px] font-bold uppercase tracking-wide text-wo-text-dim">
              Acțiuni
            </p>
            <ul className="space-y-1">
              {status.actions.map((action) => (
                <li key={action.id}>
                  <button
                    type="button"
                    className="w-full rounded border border-cyan-300/50 bg-cyan-50 px-2 py-1 text-left text-[10px] font-semibold text-cyan-800 hover:bg-cyan-100 dark:border-cyan-500/25 dark:bg-cyan-500/10 dark:text-cyan-200 dark:hover:bg-cyan-500/15"
                    onClick={() => onAction?.(action.id)}
                    data-testid={`${testIdPrefix}-action-${action.id}`}
                  >
                    {action.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </PopoverContent>
    </Popover>
  );
}
