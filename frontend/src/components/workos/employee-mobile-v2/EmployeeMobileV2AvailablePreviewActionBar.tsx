import { Loader2, Play } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import { EmployeeMobileErrorState } from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { useEmployeeMobileV2StartAction } from "@/hooks/useEmployeeMobileV2StartAction";
import { emV2Controls } from "@/lib/employeeMobileV2DesignTokens";
import {
  canShowAvailableStart,
  AVAILABLE_START_LABEL,
  START_PENDING_LABEL,
} from "@/lib/employeeMobileV2StartAction";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2AvailablePreviewActionBar({
  task,
  onStarted,
  testIdPrefix = "employee-mobile-v2-available-preview",
}: {
  task: EmployeeMobileTaskDTO;
  onStarted: () => void | Promise<void>;
  testIdPrefix?: string;
}) {
  const { startTask, isPending, error } = useEmployeeMobileV2StartAction();
  const canStart = canShowAvailableStart(task);
  const starting = isPending(task);

  return (
    <div className={emV2Controls.actionGroup} data-testid={`${testIdPrefix}-actions`}>
      {error ? (
        <EmployeeMobileErrorState message={error} testId={`${testIdPrefix}-start-error`} />
      ) : null}
      <button
        type="button"
        className={cn(emV2Controls.primaryAction)}
        disabled={starting || !canStart}
        onClick={() =>
          void startTask(task, async () => {
            await onStarted();
          })
        }
        data-testid={`${testIdPrefix}-start`}
      >
        {starting ? (
          <span className="inline-flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
            {START_PENDING_LABEL}
          </span>
        ) : (
          <span className="inline-flex items-center justify-center gap-2">
            <Play className="w-4 h-4" aria-hidden />
            {AVAILABLE_START_LABEL}
          </span>
        )}
      </button>
    </div>
  );
}
