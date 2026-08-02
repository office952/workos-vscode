/**
 * Compact next-step card for execution-flow surfaces — presentation only.
 */
import { Link } from "react-router-dom";
import type { ExecutionNextStepHint } from "@/lib/executionFlowUi";
import { cn } from "@/lib/utils";

interface ExecutionFlowNextStepProps {
  hint: ExecutionNextStepHint;
  className?: string;
  testId?: string;
}

export default function ExecutionFlowNextStep({
  hint,
  className,
  testId = "execution-flow-next-step",
}: ExecutionFlowNextStepProps) {
  return (
    <aside
      data-testid={testId}
      className={cn(
        "rounded-lg border border-wo-border-strong bg-wo-surface-raised px-3 py-2.5",
        className,
      )}
    >
      <p className="text-[12px] font-semibold text-wo-text-primary">{hint.title}</p>
      <p className="mt-1 text-[11px] leading-relaxed text-wo-text-secondary">
        {hint.description}
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {hint.primaryLabel && hint.primaryTo ? (
          <Link
            to={hint.primaryTo}
            className="inline-flex items-center rounded-md border border-wo-info/40 bg-wo-info-muted px-2.5 py-1 text-[11px] font-semibold text-wo-info hover:bg-wo-hover"
          >
            {hint.primaryLabel}
          </Link>
        ) : null}
        {hint.secondaryLabel && hint.secondaryTo ? (
          <Link
            to={hint.secondaryTo}
            className="inline-flex items-center rounded-md border border-wo-border-strong bg-wo-surface-inset px-2.5 py-1 text-[11px] font-medium text-wo-text-secondary hover:bg-wo-hover hover:text-wo-text-primary"
          >
            {hint.secondaryLabel}
          </Link>
        ) : null}
      </div>
    </aside>
  );
}
