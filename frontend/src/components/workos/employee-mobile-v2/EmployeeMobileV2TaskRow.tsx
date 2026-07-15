import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";
import EmployeeMobileV2StatusIndicator from "@/components/workos/employee-mobile-v2/EmployeeMobileV2StatusIndicator";
import {
  buildEmployeeMobileV2TaskPath,
  emV2TaskRowClass,
} from "@/lib/employeeMobileV2DesignTokens";
import {
  buildTaskRowContextLine,
  suppressDuplicateWaitingDetail,
} from "@/lib/employeeMobileV2TaskGrouping";
import {
  resolveTaskComponentLine,
  resolveTaskDisplayTitle,
  resolveTaskOperationLine,
} from "@/lib/employeeMobileV2TaskTruth";
import { resolveEmployeeMobileV2StatusPresentation } from "@/lib/employeeMobileV2Status";
import { cn } from "@/lib/utils";

function productionBlockLine(task: EmployeeMobileTaskDTO): string | null {
  if (!task.production_release_blocked) return null;
  const summary = task.production_blocker_summary?.trim();
  if (summary) {
    const short = summary.length > 72 ? `${summary.slice(0, 70)}…` : summary;
    return `Producție blocată — ${short}`;
  }
  return "Producție blocată — necesită rezolvare de către manager";
}

export default function EmployeeMobileV2TaskRow({
  task,
  blueprintTask,
  highlighted = false,
  testIdPrefix = "employee-mobile-v2-task-row",
}: {
  task: EmployeeMobileTaskDTO;
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null;
  highlighted?: boolean;
  testIdPrefix?: string;
}) {
  const navigate = useNavigate();
  const presentation = useMemo(
    () => resolveEmployeeMobileV2StatusPresentation(task, blueprintTask),
    [task, blueprintTask],
  );

  const title = resolveTaskDisplayTitle(task);
  const componentLine = resolveTaskComponentLine(task);
  const operationLine = resolveTaskOperationLine(task);
  const orderLine = [task.order_code || `Comandă #${task.order_id}`, task.client]
    .filter(Boolean)
    .join(" · ");
  const productionLine = productionBlockLine(task);

  const contextLine = useMemo(() => buildTaskRowContextLine(task), [task]);
  const secondaryLine = contextLine;

  const rowPresentation = useMemo(
    () => suppressDuplicateWaitingDetail(presentation, secondaryLine),
    [presentation, secondaryLine],
  );

  return (
    <button
      type="button"
      onClick={() => navigate(buildEmployeeMobileV2TaskPath(task.task_id, task.order_id))}
      className={cn(emV2TaskRowClass(highlighted), "w-full min-h-[56px]")}
      data-testid={`${testIdPrefix}-${task.task_id}`}
    >
      <span className="min-w-0 flex-1 text-left">
        <span
          className="block text-[15px] font-medium text-slate-100 leading-snug line-clamp-2"
          data-testid={`${testIdPrefix}-${task.task_id}-title`}
        >
          {title}
        </span>
        {componentLine ? (
          <span
            className="mt-0.5 block text-[12px] text-slate-400 line-clamp-1"
            data-testid={`${testIdPrefix}-${task.task_id}-component`}
          >
            {componentLine}
          </span>
        ) : null}
        {orderLine ? (
          <span
            className="mt-0.5 block text-[12px] text-slate-500 line-clamp-2"
            data-testid={`${testIdPrefix}-${task.task_id}-order`}
          >
            {orderLine}
          </span>
        ) : null}
        {operationLine ? (
          <span className="mt-0.5 block text-[11px] text-slate-600 line-clamp-1">{operationLine}</span>
        ) : null}
        {productionLine ? (
          <span
            className="mt-1 block text-[11px] text-rose-300/90 line-clamp-2"
            data-testid={`${testIdPrefix}-${task.task_id}-production-block`}
          >
            {productionLine}
          </span>
        ) : secondaryLine ? (
          <span className="mt-0.5 block text-[12px] text-slate-500 line-clamp-2">{secondaryLine}</span>
        ) : null}
      </span>
      <EmployeeMobileV2StatusIndicator
        presentation={rowPresentation}
        testId={`${testIdPrefix}-${task.task_id}-status`}
      />
    </button>
  );
}
