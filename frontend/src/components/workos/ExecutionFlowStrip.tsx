/**
 * ExecutionFlowStrip — Comenzi → Execuție → Atelier → Control producție.
 * Presentation only; does not mutate business state.
 */
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import {
  EXECUTION_FLOW_STAGES,
  executionFlowStageIndex,
  type ExecutionFlowStage,
} from "@/lib/executionFlowUi";
import { cn } from "@/lib/utils";

interface ExecutionFlowStripProps {
  active: ExecutionFlowStage;
  className?: string;
  /** Optional order-scoped execution detail link when on Execuție. */
  orderExecutionPath?: string | null;
}

export default function ExecutionFlowStrip({
  active,
  className,
  orderExecutionPath,
}: ExecutionFlowStripProps) {
  const activeIndex = executionFlowStageIndex(active);

  return (
    <nav
      aria-label="Flux execuție"
      data-testid="execution-flow-strip"
      data-active-stage={active}
      className={cn(
        "flex flex-wrap items-center gap-1 rounded-lg border border-wo-border-strong bg-wo-surface-inset px-3 py-2",
        className,
      )}
    >
      <span className="mr-1 text-[10px] font-semibold uppercase tracking-wide text-wo-text-muted">
        Flux execuție
      </span>
      {EXECUTION_FLOW_STAGES.map((stage, index) => {
        const isActive =
          stage.id === active ||
          (active === "operator" && stage.id === "atelier");
        const isPast = index < activeIndex;
        const href =
          stage.id === "executie" && orderExecutionPath
            ? orderExecutionPath
            : stage.path;
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
                to={href}
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
