import { Cpu } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  CNC_PROCESSABLE_BADGE_CODE,
  CNC_PROCESSABLE_BADGE_LABEL,
  CNC_PROCESSABLE_BADGE_MEANING_RO,
  CNC_PROCESSABLE_BADGE_TITLE_RO,
  CNC_PROCESSABLE_LETTER_FACE_SERVICES,
  CNC_PROCESSABLE_MATERIAL_DISPLAY_NAME,
  CNC_PROCESSABLE_MATERIAL_REGISTRY_CODE,
} from "@/lib/cnc/cncProcessableBadge";

type CncProcessableBadgeProps = {
  size?: "sm" | "md";
  showServices?: boolean;
  showMaterial?: boolean;
  /** When false, only services/material strip (badge already shown elsewhere). */
  showBadgeMark?: boolean;
  testId?: string;
  className?: string;
};

const sizeClass = {
  sm: "gap-1 rounded border px-1.5 py-0.5 text-[10px] tracking-[0.12em]",
  md: "gap-1.5 rounded-md border px-2.5 py-1 text-[11px] tracking-[0.14em]",
} as const;

const iconClass = {
  sm: "h-3 w-3",
  md: "h-3.5 w-3.5",
} as const;

/**
 * Shared CNC capability badge — same identifier on materials and CNC machines.
 */
export function CncProcessableBadge({
  size = "md",
  showServices = false,
  showMaterial = false,
  showBadgeMark = true,
  testId = "cnc-processable-badge",
  className = "",
}: CncProcessableBadgeProps) {
  return (
    <div className={`inline-flex flex-col items-start gap-1.5 ${className}`}>
      <div className="inline-flex flex-wrap items-center gap-1.5">
        {showBadgeMark ? (
          <Tooltip delayDuration={150}>
            <TooltipTrigger asChild>
              <button
                type="button"
                className={`inline-flex items-center border-violet-400/50 bg-violet-500/20 font-bold uppercase text-violet-100 outline-none transition-colors hover:border-violet-300/70 hover:bg-violet-500/30 focus-visible:ring-2 focus-visible:ring-violet-400/50 ${sizeClass[size]}`}
                data-testid={testId}
                data-badge-code={CNC_PROCESSABLE_BADGE_CODE}
                aria-label={`${CNC_PROCESSABLE_BADGE_TITLE_RO} (${CNC_PROCESSABLE_BADGE_CODE})`}
              >
                <Cpu className={`${iconClass[size]} text-violet-200`} aria-hidden />
                {CNC_PROCESSABLE_BADGE_LABEL}
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              align="start"
              className="max-w-[16rem] border-violet-600/50 bg-wo-surface-inset px-3 py-2.5 text-slate-200 shadow-lg shadow-violet-950/50"
              data-testid={`${testId}-tooltip`}
            >
              <p className="text-[11px] font-semibold tracking-wide text-violet-200">
                {CNC_PROCESSABLE_BADGE_TITLE_RO}
              </p>
              <p className="mt-1 font-mono text-[10px] text-violet-300/80">{CNC_PROCESSABLE_BADGE_CODE}</p>
              <p className="mt-1.5 border-t border-violet-800/40 pt-1.5 text-[11px] leading-snug text-slate-300">
                {CNC_PROCESSABLE_BADGE_MEANING_RO}
              </p>
              <ol className="mt-1.5 space-y-1 text-[11px] leading-snug text-slate-300">
                {CNC_PROCESSABLE_LETTER_FACE_SERVICES.map((service, index) => (
                  <li key={service} className="flex gap-1.5">
                    <span className="font-semibold tabular-nums text-violet-300/90">{index + 1}.</span>
                    <span>{service}</span>
                  </li>
                ))}
              </ol>
              <p className="mt-1.5 border-t border-violet-800/40 pt-1.5 text-[10px] text-slate-400">
                Material: {CNC_PROCESSABLE_MATERIAL_DISPLAY_NAME}{" "}
                <span className="font-mono text-violet-300/70">
                  ({CNC_PROCESSABLE_MATERIAL_REGISTRY_CODE})
                </span>
              </p>
            </TooltipContent>
          </Tooltip>
        ) : null}
        {showServices
          ? CNC_PROCESSABLE_LETTER_FACE_SERVICES.map((service, index) => (
              <span
                key={service}
                className="inline-flex items-center gap-1 rounded-md border border-violet-700/40 bg-wo-surface-inset/80 px-2 py-1 text-[11px] font-medium text-violet-100/95"
                data-testid={`${testId}-service-${index}`}
              >
                <span className="font-bold tabular-nums text-violet-300/90">{index + 1}.</span>
                {service}
              </span>
            ))
          : null}
      </div>
      {showMaterial ? (
        <p
          className="text-[10px] leading-snug text-violet-200/85"
          data-testid={`${testId}-material`}
        >
          <span className="font-medium text-violet-100">{CNC_PROCESSABLE_MATERIAL_DISPLAY_NAME}</span>
          <span className="text-slate-600"> · </span>
          <span className="font-mono text-[9px] text-slate-500">{CNC_PROCESSABLE_MATERIAL_REGISTRY_CODE}</span>
          <span className="text-slate-600"> · </span>
          <span className="text-slate-500">material procesabil pe acest utilaj</span>
        </p>
      ) : null}
    </div>
  );
}
