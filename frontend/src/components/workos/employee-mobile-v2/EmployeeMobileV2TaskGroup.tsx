import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";
import EmployeeMobileV2TaskRow from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskRow";
import { emV2SectionLabelClass } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2TaskGroup({
  title,
  subtitle,
  count,
  summaryStatus,
  pipelineHref,
  tasks,
  blueprintById,
  testId,
}: {
  title: string;
  subtitle?: string | null;
  count: number;
  summaryStatus?: string | null;
  pipelineHref?: string | null;
  tasks: EmployeeMobileTaskDTO[];
  blueprintById: Map<string, EmployeeMobileOrderBlueprintTask>;
  testId: string;
}) {
  return (
    <section className={cn(tasks.length === 1 ? "mb-3" : "mb-5")} data-testid={testId}>
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-[14px] font-semibold text-slate-100">{title}</h3>
            <span className="text-[11px] font-medium text-slate-500">{count}</span>
          </div>
          {subtitle ? (
            <p className="mt-0.5 text-[12px] text-slate-500 line-clamp-2">{subtitle}</p>
          ) : null}
          {summaryStatus ? (
            <p className="mt-0.5 text-[11px] font-medium text-slate-400">{summaryStatus}</p>
          ) : null}
        </div>
        {pipelineHref ? (
          <Link
            to={pipelineHref}
            className="inline-flex min-h-[44px] shrink-0 items-center gap-1 text-[12px] font-medium text-blue-400 hover:text-blue-300"
            data-testid={`${testId}-pipeline-link`}
          >
            Vezi lucrarea
            <ChevronRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
        ) : null}
      </div>

      <div className="space-y-2" data-testid={`${testId}-list`}>
        {tasks.map((task) => (
          <EmployeeMobileV2TaskRow
            key={`${task.order_id}-${task.task_id}`}
            task={task}
            blueprintTask={blueprintById.get(task.task_id) ?? null}
            highlighted={task.status === "in_progress"}
            testIdPrefix="employee-mobile-v2-task-row"
          />
        ))}
      </div>
    </section>
  );
}

export function EmployeeMobileV2TasksMiniSummary({
  title,
  line,
}: {
  title: string;
  line: string;
}) {
  return (
    <div className="mb-4" data-testid="employee-mobile-v2-tasks-mini-summary">
      <p className={cn(emV2SectionLabelClass(), "mb-1")}>{title}</p>
      <p className="text-[13px] text-slate-400 leading-snug">{line}</p>
    </div>
  );
}
