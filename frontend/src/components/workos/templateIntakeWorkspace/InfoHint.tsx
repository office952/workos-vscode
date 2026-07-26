import { Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export interface InfoHintProps {
  /** Accessible label for the trigger. */
  label: string;
  /** Tooltip body — secondary explanations only. */
  children: React.ReactNode;
  className?: string;
}

/** Small info icon; explanations live in tooltip, not on the page. */
export default function InfoHint({ label, children, className }: InfoHintProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className={`inline-flex items-center justify-center w-4 h-4 rounded-full text-slate-500 hover:text-blue-400 focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500/50 ${className ?? ""}`}
            aria-label={label}
            data-testid="info-hint-trigger"
          >
            <Info className="w-3.5 h-3.5" />
          </button>
        </TooltipTrigger>
        <TooltipContent
          side="top"
          className="max-w-xs text-[11px] leading-relaxed bg-[#1a2332] border-wo-border-strong text-slate-300"
        >
          {children}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
