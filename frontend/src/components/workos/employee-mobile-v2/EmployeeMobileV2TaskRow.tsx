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
import { resolveEmployeeMobileV2StatusPresentation } from "@/lib/employeeMobileV2Status";
import { cn } from "@/lib/utils";

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
        <span className="block text-[15px] font-medium text-slate-100 leading-snug line-clamp-2">
          {task.title || task.task_id}
        </span>
        {secondaryLine ? (
          <span className="mt-0.5 block text-[12px] text-slate-500 line-clamp-2">
            {secondaryLine}
          </span>
        ) : null}
      </span>
      <EmployeeMobileV2StatusIndicator
        presentation={rowPresentation}
        testId={`${testIdPrefix}-${task.task_id}-status`}
      />
    </button>
  );
}
