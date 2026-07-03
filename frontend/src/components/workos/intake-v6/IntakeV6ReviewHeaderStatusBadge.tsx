import { ChevronDown } from "lucide-react";
import type { ReviewHeaderStatusModel } from "@/lib/intakeV6/intakeV6ReviewHeaderStatus";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

const TONE_CLASS: Record<ReviewHeaderStatusModel["tone"], string> = {
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/15",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-200 hover:bg-amber-500/15",
  danger: "border-red-500/30 bg-red-500/10 text-red-200 hover:bg-red-500/15",
  neutral: "border-[#2A3548] bg-[#111827] text-slate-400 hover:border-slate-500/40",
};

const DETAIL_TONE_CLASS = {
  ok: "text-emerald-300/90",
  warn: "text-amber-200/90",
  bad: "text-red-300/90",
  muted: "text-slate-400",
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
        className="w-72 border-[#2A3548] bg-[#0f172a] p-0 text-slate-200 shadow-xl"
        align="end"
        data-testid={`${testIdPrefix}-popover`}
      >
        <div className="border-b border-[#2A3548] px-3 py-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
            Stare lucrare
          </p>
        </div>
        <ul
          className="space-y-1 px-3 py-2 text-[11px]"
          data-testid={`${testIdPrefix}-details`}
        >
          {status.details.map((row) => (
            <li key={row.id} className="flex items-baseline justify-between gap-2">
              <span className="text-slate-500">{row.label}</span>
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
            className="border-t border-[#2A3548] px-3 py-2"
            data-testid={`${testIdPrefix}-actions`}
          >
            <p className="mb-1.5 text-[9px] font-bold uppercase tracking-wide text-slate-500">
              Acțiuni
            </p>
            <ul className="space-y-1">
              {status.actions.map((action) => (
                <li key={action.id}>
                  <button
                    type="button"
                    className="w-full rounded border border-cyan-500/25 bg-cyan-500/10 px-2 py-1 text-left text-[10px] font-semibold text-cyan-200 hover:bg-cyan-500/15"
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
