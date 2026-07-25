import { Box } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO,
  LETTERS_VOLUME_ALUMINUM_PROCESS_STEPS,
  LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE,
  LETTERS_VOLUME_ALUMINUM_THICKNESS_NOTE_RO,
  LETTERS_VOLUME_ALUMINUM_WIDTHS,
} from "@/lib/materials/lettersVolumeAluminumMaterialDisplay";

type LettersVolumeAluminumWidthBadgesProps = {
  size?: "sm" | "md";
  testId?: string;
  className?: string;
};

const sizeClass = {
  sm: "gap-1 rounded border px-1.5 py-0.5 text-[10px] tracking-[0.08em]",
  md: "gap-1.5 rounded-md border px-2 py-1 text-[11px] tracking-[0.1em]",
} as const;

function formatEurMl(value: number): string {
  return `${value.toLocaleString("ro-RO", { minimumFractionDigits: 1, maximumFractionDigits: 2 })} €/ml`;
}

/**
 * Four aluminum volume widths for the Volum aluminiu structure step.
 * Identity = label + MAT-* (no capability badge parallel to CNC).
 */
export function LettersVolumeAluminumWidthBadges({
  size = "md",
  testId = "letters-volume-aluminum-widths",
  className = "",
}: LettersVolumeAluminumWidthBadgesProps) {
  return (
    <div
      className={`w-full rounded-md border border-sky-800/35 bg-sky-950/15 px-2.5 py-2 ${className}`}
      data-testid={testId}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5">
        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-sky-400/90">
          Material · {LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO}
        </p>
        <p className="text-[9px] text-sky-700/80">
          {LETTERS_VOLUME_ALUMINUM_THICKNESS_NOTE_RO} · 4 lățimi
        </p>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {LETTERS_VOLUME_ALUMINUM_WIDTHS.map((option) => (
          <Tooltip key={option.id} delayDuration={150}>
            <TooltipTrigger asChild>
              <button
                type="button"
                className={`inline-flex items-center border-sky-500/45 bg-sky-500/15 font-semibold uppercase text-sky-100 outline-none transition-colors hover:border-sky-400/60 hover:bg-sky-500/25 focus-visible:ring-2 focus-visible:ring-sky-400/40 ${sizeClass[size]}`}
                data-testid={`${testId}-${option.id}`}
                aria-label={`${LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO} ${option.labelRo}`}
              >
                <Box className="h-3.5 w-3.5 text-sky-200" aria-hidden />
                {option.labelRo}
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              align="start"
              className="max-w-[16rem] border-sky-700/40 bg-[#0F172A] px-3 py-2.5 text-slate-200 shadow-lg"
              data-testid={`${testId}-${option.id}-tooltip`}
            >
              <p className="text-[11px] font-semibold tracking-wide text-sky-200">
                {LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO} {option.labelRo}
              </p>
              <p className="mt-1 font-mono text-[10px] text-sky-300/80">{option.materialCode}</p>
              <p className="mt-0.5 text-[10px] text-slate-400">
                {formatEurMl(option.unitCostEurMl)} · fără TVA · Inventory / Pricing
              </p>
              <p className="mt-1.5 border-t border-sky-900/40 pt-1.5 text-[11px] leading-snug text-slate-300">
                {option.meaningRo}
              </p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>

      <div
        className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-sky-900/40 pt-2"
        data-testid={`${testId}-process`}
      >
        <span className="mr-0.5 text-[9px] font-semibold uppercase tracking-[0.1em] text-sky-600/75">
          Procese
        </span>
        {LETTERS_VOLUME_ALUMINUM_PROCESS_STEPS.map((step, index) => (
          <Tooltip key={step.id} delayDuration={150}>
            <TooltipTrigger asChild>
              <span
                className="inline-flex items-center gap-1 rounded-md border border-sky-800/45 bg-[#0F172A]/80 px-2 py-1 text-[11px] font-medium text-sky-100/95"
                data-testid={`${testId}-process-${index}`}
              >
                <span className="font-bold tabular-nums text-sky-300/90">{index + 1}.</span>
                {step.labelRo}
              </span>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              align="start"
              className="max-w-[14rem] border-sky-700/40 bg-[#0F172A] px-3 py-2 text-slate-200 shadow-lg"
            >
              <p className="text-[11px] leading-snug text-slate-300">{step.meaningRo}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>

      <p className="mt-2 font-mono text-[9px] text-slate-500" data-testid={`${testId}-selector`}>
        Selector template: {LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE} → lățime după return_depth_mm
      </p>
    </div>
  );
}
