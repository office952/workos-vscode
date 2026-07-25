import { Link } from "react-router-dom";
import { ExternalLink, Sticker } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  LETTERS_FACE_AUTOCOLANT_OPTIONS,
  LETTERS_FACE_FINISH_LABOR_STEPS,
  LETTERS_FACE_FINISH_SECTION_LABEL_RO,
} from "@/lib/materials/lettersAutocolantDisplay";
import {
  buildMaterialPriceVerifyHref,
  MATERIAL_PRICE_VERIFY_LABEL_RO,
} from "@/lib/pricing/materialPriceVerifyLink";

type LettersFaceFinishOptionBadgesProps = {
  size?: "sm" | "md";
  showLabor?: boolean;
  testId?: string;
  className?: string;
};

const sizeClass = {
  sm: "gap-1 rounded border px-1.5 py-0.5 text-[10px] tracking-[0.08em]",
  md: "gap-1.5 rounded-md border px-2 py-1 text-[11px] tracking-[0.1em]",
} as const;

const iconClass = {
  sm: "h-3 w-3",
  md: "h-3.5 w-3.5",
} as const;

/**
 * Face finish options + shared labor — one FINISH block (not CNC peer).
 * Identity = label + MAT-* (no BADGE-FACE-* codes).
 */
export function LettersFaceFinishOptionBadges({
  size = "md",
  showLabor = true,
  testId = "letters-face-finish-options",
  className = "",
}: LettersFaceFinishOptionBadgesProps) {
  return (
    <div
      className={`w-full rounded-md border border-emerald-800/35 bg-emerald-950/15 px-2.5 py-2 ${className}`}
      data-testid={testId}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5">
        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-emerald-500/90">
          {LETTERS_FACE_FINISH_SECTION_LABEL_RO}
        </p>
        <p className="text-[9px] text-emerald-700/80">după asamblare · orice opțiune</p>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {LETTERS_FACE_AUTOCOLANT_OPTIONS.map((option) => (
          <Tooltip key={option.id} delayDuration={150}>
            <TooltipTrigger asChild>
              <button
                type="button"
                className={`inline-flex items-center border-emerald-500/45 bg-emerald-500/15 font-semibold uppercase text-emerald-100 outline-none transition-colors hover:border-emerald-400/60 hover:bg-emerald-500/25 focus-visible:ring-2 focus-visible:ring-emerald-400/40 ${sizeClass[size]}`}
                data-testid={`${testId}-${option.id}`}
                aria-label={`${LETTERS_FACE_FINISH_SECTION_LABEL_RO}: ${option.labelRo}`}
              >
                <Sticker className={`${iconClass[size]} text-emerald-200`} aria-hidden />
                {option.labelRo}
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              align="start"
              className="max-w-[16rem] border-emerald-700/40 bg-[#0F172A] px-3 py-2.5 text-slate-200 shadow-lg"
              data-testid={`${testId}-${option.id}-tooltip`}
            >
              <p className="text-[11px] font-semibold tracking-wide text-emerald-200">
                {option.labelRo}
              </p>
              <p className="mt-1 font-mono text-[10px] text-emerald-300/80">{option.materialCode}</p>
              <Link
                to={buildMaterialPriceVerifyHref(option.materialCode)}
                className="mt-1 inline-flex items-center gap-1 text-[10px] font-medium text-cyan-300/90 underline-offset-2 hover:text-cyan-200 hover:underline"
                data-testid={`${testId}-${option.id}-price-verify`}
                onClick={(event) => event.stopPropagation()}
              >
                {MATERIAL_PRICE_VERIFY_LABEL_RO}
                <ExternalLink className="h-3 w-3" aria-hidden />
              </Link>
              <p className="mt-1.5 border-t border-emerald-900/40 pt-1.5 text-[11px] leading-snug text-slate-300">
                {option.meaningRo}
              </p>
              <p className="mt-1 text-[10px] text-slate-500">
                Manoperă:{" "}
                {LETTERS_FACE_FINISH_LABOR_STEPS.map((step) => step.labelRo).join(" · ")}
              </p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>

      {showLabor ? (
        <div
          className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-emerald-900/40 pt-2"
          data-testid={`${testId}-labor`}
        >
          <span className="mr-0.5 text-[9px] font-semibold uppercase tracking-[0.1em] text-emerald-600/75">
            Manoperă
          </span>
          {LETTERS_FACE_FINISH_LABOR_STEPS.map((step, index) => (
            <Tooltip key={step.id} delayDuration={150}>
              <TooltipTrigger asChild>
                <span
                  className="inline-flex items-center gap-1 rounded-md border border-emerald-800/45 bg-[#0F172A]/80 px-2 py-1 text-[11px] font-medium text-emerald-100/95"
                  data-testid={`${testId}-labor-${index}`}
                >
                  <span className="font-bold tabular-nums text-emerald-300/90">{index + 1}.</span>
                  {step.labelRo}
                </span>
              </TooltipTrigger>
              <TooltipContent
                side="top"
                align="start"
                className="max-w-[14rem] border-emerald-700/40 bg-[#0F172A] px-3 py-2 text-slate-200 shadow-lg"
              >
                <p className="text-[11px] leading-snug text-slate-300">{step.meaningRo}</p>
              </TooltipContent>
            </Tooltip>
          ))}
        </div>
      ) : null}
    </div>
  );
}
