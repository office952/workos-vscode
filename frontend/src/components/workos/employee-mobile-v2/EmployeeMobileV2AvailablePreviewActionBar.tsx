import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Play } from "lucide-react";
import {
  mapEmployeeMobileStartFromAvailableError,
  startEmployeeMobileTaskFromAvailable,
  type EmployeeMobileTaskDTO,
} from "@/api/employeeMobileTasks";
import { EmployeeMobileErrorState } from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { buildEmployeeMobileV2TaskPath, emV2Controls } from "@/lib/employeeMobileV2DesignTokens";
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
  const navigate = useNavigate();
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  async function handleStart() {
    setStarting(true);
    setStartError(null);
    try {
      await startEmployeeMobileTaskFromAvailable(task.task_id, task.order_id);
      await onStarted();
      navigate(buildEmployeeMobileV2TaskPath(task.task_id, task.order_id));
    } catch (err) {
      setStartError(mapEmployeeMobileStartFromAvailableError(err));
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className={emV2Controls.actionGroup} data-testid={`${testIdPrefix}-actions`}>
      {startError ? (
        <EmployeeMobileErrorState message={startError} testId={`${testIdPrefix}-start-error`} />
      ) : null}
      <button
        type="button"
        className={cn(emV2Controls.primaryAction)}
        disabled={starting || task.is_startable !== true}
        onClick={() => void handleStart()}
        data-testid={`${testIdPrefix}-start`}
      >
        {starting ? (
          <span className="inline-flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
            Se pornește…
          </span>
        ) : (
          <span className="inline-flex items-center justify-center gap-2">
            <Play className="w-4 h-4" aria-hidden />
            Încep lucrul
          </span>
        )}
      </button>
    </div>
  );
}
