import { Layers } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  LETTERS_BACK_FOREX_10MM_DISPLAY_NAME,
  LETTERS_BACK_FOREX_10MM_REGISTRY_CODE,
  LETTERS_BACK_FOREX_10MM_UNIT_COST_EUR_MP,
  LETTERS_BACK_FOREX_MEANING_RO,
  LETTERS_BACK_FOREX_PROCESS_STEPS,
} from "@/lib/materials/lettersBackForexMaterialDisplay";

type LettersBackForexMaterialPanelProps = {
  testId?: string;
  className?: string;
};

/**
 * Capac spate — Forex 10 mm material + CNC process chips (display only).
 */
export function LettersBackForexMaterialPanel({
  testId = "letters-back-forex",
  className = "",
}: LettersBackForexMaterialPanelProps) {
  return (
    <div
      className={`w-full rounded-md border border-amber-800/35 bg-amber-950/15 px-2.5 py-2 ${className}`}
      data-testid={testId}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5">
        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-amber-400/90">
          Material · Capac spate
        </p>
        <p className="font-mono text-[9px] text-slate-500">{LETTERS_BACK_FOREX_10MM_REGISTRY_CODE}</p>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        <Tooltip delayDuration={150}>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-amber-500/45 bg-amber-500/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-amber-100 outline-none transition-colors hover:border-amber-400/60 hover:bg-amber-500/25 focus-visible:ring-2 focus-visible:ring-amber-400/40"
              data-testid={`${testId}-material`}
              aria-label={`${LETTERS_BACK_FOREX_10MM_DISPLAY_NAME} (${LETTERS_BACK_FOREX_10MM_REGISTRY_CODE})`}
            >
              <Layers className="h-3.5 w-3.5 text-amber-200" aria-hidden />
              {LETTERS_BACK_FOREX_10MM_DISPLAY_NAME}
            </button>
          </TooltipTrigger>
          <TooltipContent
            side="top"
            align="start"
            className="max-w-[16rem] border-amber-700/40 bg-wo-surface-inset px-3 py-2.5 text-slate-200 shadow-lg"
          >
            <p className="text-[11px] font-semibold tracking-wide text-amber-200">
              {LETTERS_BACK_FOREX_10MM_DISPLAY_NAME}
            </p>
            <p className="mt-1 font-mono text-[10px] text-amber-300/80">
              {LETTERS_BACK_FOREX_10MM_REGISTRY_CODE}
            </p>
            <p className="mt-0.5 text-[10px] text-slate-400">
              {LETTERS_BACK_FOREX_10MM_UNIT_COST_EUR_MP.toLocaleString("ro-RO", {
                minimumFractionDigits: 1,
              })}{" "}
              €/mp · fără TVA · Inventory / Pricing
            </p>
            <p className="mt-1.5 border-t border-amber-900/40 pt-1.5 text-[11px] leading-snug text-slate-300">
              {LETTERS_BACK_FOREX_MEANING_RO}
            </p>
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-amber-900/40 pt-2">
        <span className="mr-0.5 text-[9px] font-semibold uppercase tracking-[0.1em] text-amber-600/75">
          Procese CNC
        </span>
        {LETTERS_BACK_FOREX_PROCESS_STEPS.map((step, index) => (
          <Tooltip key={step.id} delayDuration={150}>
            <TooltipTrigger asChild>
              <span
                className="inline-flex items-center gap-1 rounded-md border border-amber-800/45 bg-wo-surface-inset/80 px-2 py-1 text-[11px] font-medium text-amber-100/95"
                data-testid={`${testId}-process-${index}`}
              >
                <span className="font-bold tabular-nums text-amber-300/90">{index + 1}.</span>
                {step.labelRo}
                {!step.required ? (
                  <span className="text-[9px] font-normal text-slate-500">opț.</span>
                ) : null}
              </span>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              align="start"
              className="max-w-[14rem] border-amber-700/40 bg-wo-surface-inset px-3 py-2 text-slate-200 shadow-lg"
            >
              <p className="text-[11px] leading-snug text-slate-300">{step.meaningRo}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}
