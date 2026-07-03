import { useMemo } from "react";
import { useEmployeeMobileV2Tasks } from "@/hooks/useEmployeeMobileV2Tasks";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
import EmployeeMobileV2TaskRow from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskRow";
import { emV2Surface } from "@/lib/employeeMobileV2DesignTokens";
import { pickHeroTask, pickUpcomingTasks } from "@/lib/employeeMobileTaskSummary";
import { pickPrimaryOrderId } from "@/lib/employeeMobilePipelineEligibility";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2UpcomingPage() {
  const { tasks, loading, error } = useEmployeeMobileV2Tasks();
  const hero = useMemo(() => pickHeroTask(tasks), [tasks]);
  const primaryOrderId = useMemo(() => pickPrimaryOrderId(tasks), [tasks]);

  const upcomingTasks = useMemo(() => {
    const rows = pickUpcomingTasks(tasks, hero.task);
    if (primaryOrderId == null) return rows;
    return rows.filter((task) => task.order_id === primaryOrderId);
  }, [tasks, hero.task, primaryOrderId]);

  return (
    <div data-testid="employee-mobile-v2-upcoming">
      <EmployeeMobileV2PageHeader
        backTo="/employee-app-v2"
        title="Urmează"
        subtitle="Ce vine după taskul curent"
        testId="employee-mobile-v2-upcoming-header"
      />

      {loading ? (
        <EmployeeMobileLoadingState
          message="Se încarcă…"
          testId="employee-mobile-v2-upcoming-loading"
        />
      ) : null}

      {!loading && error ? (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-upcoming-error" />
      ) : null}

      {!loading && !error && upcomingTasks.length === 0 ? (
        <EmployeeMobileEmptyState
          message="Niciun task viitor pregătit în comanda curentă."
          hint="Taskurile următoare apar când sunt alocate și disponibile."
          testId="employee-mobile-v2-upcoming-empty"
        />
      ) : null}

      {!loading && !error && upcomingTasks.length > 0 ? (
        <div className="space-y-2" data-testid="employee-mobile-v2-upcoming-list">
          {upcomingTasks.map((task) => (
            <div key={`${task.order_id}-${task.task_id}`} className={cn(emV2Surface.panel, "p-0 overflow-hidden")}>
              <EmployeeMobileV2TaskRow task={task} />
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
