import { Lightbulb, Zap } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  LETTERS_LED_FAMILY_LABEL_RO,
  LETTERS_LED_MODULE_CODE,
  LETTERS_LED_MODULE_DISPLAY_NAME,
  LETTERS_LED_MODULE_UNIT_COST_EUR_BUC,
  LETTERS_LED_MOUNT_NOTE_RO,
  LETTERS_LED_PROCESS_STEPS,
  LETTERS_LED_PSU_SELECTOR_CODE,
  LETTERS_LED_PSU_VARIANTS,
  LETTERS_LED_STRIP_CODE,
  LETTERS_LED_STRIP_DISPLAY_NAME,
  LETTERS_LED_STRIP_UNIT_COST_EUR_ML,
  lettersLedPsuPricingLabel,
} from "@/lib/materials/lettersLedMaterialDisplay";

type LettersLedSystemPanelProps = {
  testId?: string;
  className?: string;
};

function formatEur(value: number, unit: string): string {
  return `${value.toLocaleString("ro-RO", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  })} €/${unit}`;
}

/**
 * Sistem LED — module (standard) + bandă (alt) + PSU wattage chips (display only).
 */
export function LettersLedSystemPanel({
  testId = "letters-led-system",
  className = "",
}: LettersLedSystemPanelProps) {
  return (
    <div
      className={`w-full rounded-md border border-yellow-800/35 bg-yellow-950/15 px-2.5 py-2 ${className}`}
      data-testid={testId}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5">
        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-yellow-400/90">
          Material · {LETTERS_LED_FAMILY_LABEL_RO}
        </p>
        <p className="text-[9px] text-yellow-700/80">{LETTERS_LED_MOUNT_NOTE_RO}</p>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        <Tooltip delayDuration={150}>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-yellow-500/45 bg-yellow-500/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-yellow-100 outline-none transition-colors hover:border-yellow-400/60 hover:bg-yellow-500/25 focus-visible:ring-2 focus-visible:ring-yellow-400/40"
              data-testid={`${testId}-module`}
              aria-label={`${LETTERS_LED_MODULE_DISPLAY_NAME} (standard)`}
            >
              <Lightbulb className="h-3.5 w-3.5 text-yellow-200" aria-hidden />
              {LETTERS_LED_MODULE_DISPLAY_NAME}
              <span className="text-[9px] font-normal normal-case tracking-normal text-yellow-200/70">
                standard
              </span>
            </button>
          </TooltipTrigger>
          <TooltipContent
            side="top"
            align="start"
            className="max-w-[16rem] border-yellow-700/40 bg-[#0F172A] px-3 py-2.5 text-slate-200 shadow-lg"
          >
            <p className="text-[11px] font-semibold tracking-wide text-yellow-200">
              {LETTERS_LED_MODULE_DISPLAY_NAME}
            </p>
            <p className="mt-1 font-mono text-[10px] text-yellow-300/80">{LETTERS_LED_MODULE_CODE}</p>
            <p className="mt-0.5 text-[10px] text-slate-400">
              {formatEur(LETTERS_LED_MODULE_UNIT_COST_EUR_BUC, "buc")} · fără TVA · Inventory / Pricing
            </p>
            <p className="mt-1.5 border-t border-yellow-900/40 pt-1.5 text-[11px] leading-snug text-slate-300">
              Standard litere (led_modules). Cantitate din perimetru — pitch 250 mm.
            </p>
          </TooltipContent>
        </Tooltip>

        <Tooltip delayDuration={150}>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-yellow-800/45 bg-[#0F172A]/80 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-yellow-100/90 outline-none transition-colors hover:border-yellow-600/50 focus-visible:ring-2 focus-visible:ring-yellow-400/40"
              data-testid={`${testId}-strip`}
              aria-label={`${LETTERS_LED_STRIP_DISPLAY_NAME} (alternativă)`}
            >
              {LETTERS_LED_STRIP_DISPLAY_NAME}
              <span className="text-[9px] font-normal normal-case tracking-normal text-slate-500">
                alt.
              </span>
            </button>
          </TooltipTrigger>
          <TooltipContent
            side="top"
            align="start"
            className="max-w-[16rem] border-yellow-700/40 bg-[#0F172A] px-3 py-2.5 text-slate-200 shadow-lg"
          >
            <p className="text-[11px] font-semibold tracking-wide text-yellow-200">
              {LETTERS_LED_STRIP_DISPLAY_NAME}
            </p>
            <p className="mt-1 font-mono text-[10px] text-yellow-300/80">{LETTERS_LED_STRIP_CODE}</p>
            <p className="mt-0.5 text-[10px] text-slate-400">
              {formatEur(LETTERS_LED_STRIP_UNIT_COST_EUR_ML, "ml")} · fără TVA · Inventory / Pricing
            </p>
            <p className="mt-1.5 border-t border-yellow-900/40 pt-1.5 text-[11px] leading-snug text-slate-300">
              Alternativă (lighting_system_type=led_strip) — nu înlocuiește modulele ca standard.
            </p>
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-yellow-900/40 pt-2">
        <span className="mr-0.5 text-[9px] font-semibold uppercase tracking-[0.1em] text-yellow-600/75">
          Surse 12V
        </span>
        {LETTERS_LED_PSU_VARIANTS.map((option) => (
          <Tooltip key={option.id} delayDuration={150}>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="inline-flex items-center gap-1 rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-amber-100 outline-none transition-colors hover:border-amber-400/55 hover:bg-amber-500/20 focus-visible:ring-2 focus-visible:ring-amber-400/40"
                data-testid={`${testId}-${option.id}`}
                aria-label={lettersLedPsuPricingLabel(option.watts)}
              >
                <Zap className="h-3 w-3 text-amber-200" aria-hidden />
                {option.labelRo}
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              align="start"
              className="max-w-[16rem] border-amber-700/40 bg-[#0F172A] px-3 py-2.5 text-slate-200 shadow-lg"
            >
              <p className="text-[11px] font-semibold tracking-wide text-amber-200">
                {lettersLedPsuPricingLabel(option.watts)}
              </p>
              <p className="mt-1 font-mono text-[10px] text-amber-300/80">{option.materialCode}</p>
              <p className="mt-0.5 text-[10px] text-slate-400">
                {formatEur(option.unitCostEurBuc, "buc")} · fără TVA · Inventory / Pricing
              </p>
              <p className="mt-1.5 border-t border-amber-900/40 pt-1.5 text-[11px] leading-snug text-slate-300">
                {option.meaningRo}
              </p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>

      <div
        className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-yellow-900/40 pt-2"
        data-testid={`${testId}-process`}
      >
        <span className="mr-0.5 text-[9px] font-semibold uppercase tracking-[0.1em] text-yellow-600/75">
          Procese
        </span>
        {LETTERS_LED_PROCESS_STEPS.map((step, index) => (
          <Tooltip key={step.id} delayDuration={150}>
            <TooltipTrigger asChild>
              <span
                className="inline-flex items-center gap-1 rounded-md border border-yellow-800/45 bg-[#0F172A]/80 px-2 py-1 text-[11px] font-medium text-yellow-100/95"
                data-testid={`${testId}-process-${index}`}
              >
                <span className="font-bold tabular-nums text-yellow-300/90">{index + 1}.</span>
                {step.labelRo}
              </span>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              align="start"
              className="max-w-[14rem] border-yellow-700/40 bg-[#0F172A] px-3 py-2 text-slate-200 shadow-lg"
            >
              <p className="text-[11px] leading-snug text-slate-300">{step.meaningRo}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>

      <p className="mt-2 font-mono text-[9px] text-slate-500" data-testid={`${testId}-selector`}>
        Selector sursă: {LETTERS_LED_PSU_SELECTOR_CODE} → W după selected_psu_watts
      </p>
    </div>
  );
}
