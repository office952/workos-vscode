/**
 * CommercialFlowStrip — compact Cereri → Produse → Oferte → Comenzi continuity rail.
 * Presentation only; does not mutate business state.
 */
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import {
  COMMERCIAL_FLOW_STAGES,
  commercialFlowStageIndex,
  type CommercialFlowStage,
} from "@/lib/commercialFlowUi";
import { cn } from "@/lib/utils";

interface CommercialFlowStripProps {
  active: CommercialFlowStage;
  className?: string;
}

export default function CommercialFlowStrip({
  active,
  className,
}: CommercialFlowStripProps) {
  const activeIndex = commercialFlowStageIndex(active);

  return (
    <nav
      aria-label="Flux comercial"
      data-testid="commercial-flow-strip"
      data-active-stage={active}
      className={cn(
        "flex flex-wrap items-center gap-1 rounded-lg border border-wo-border-strong bg-wo-surface-inset px-3 py-2",
        className,
      )}
    >
      <span className="mr-1 text-[10px] font-semibold uppercase tracking-wide text-wo-text-muted">
        Flux
      </span>
      {COMMERCIAL_FLOW_STAGES.map((stage, index) => {
        const isActive = stage.id === active;
        const isPast = index < activeIndex;
        return (
          <span key={stage.id} className="flex items-center gap-1">
            {index > 0 ? (
              <ChevronRight
                className="h-3 w-3 shrink-0 text-wo-text-dim"
                aria-hidden
              />
            ) : null}
            {isActive ? (
              <span
                className="rounded-full border border-blue-300 bg-blue-50 px-2.5 py-0.5 text-[11px] font-semibold text-blue-700 dark:border-blue-600/50 dark:bg-blue-600/20 dark:text-blue-300"
                aria-current="step"
              >
                {stage.label}
              </span>
            ) : (
              <Link
                to={stage.path}
                className={cn(
                  "rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-colors",
                  isPast
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800 hover:border-emerald-300 dark:border-emerald-800/40 dark:bg-emerald-950/20 dark:text-emerald-200"
                    : "border-wo-border-strong bg-transparent text-wo-text-secondary hover:bg-wo-hover hover:text-wo-text-primary",
                )}
              >
                {stage.label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
