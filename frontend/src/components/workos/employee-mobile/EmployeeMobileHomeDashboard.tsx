import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CalendarClock,
  FileText,
  ListTodo,
  Package,
  User,
} from "lucide-react";
import { listEmployeeMobileTasks, type EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  buildEmployeeMobileOrderBlueprintPath,
} from "@/api/employeeMobileOrderBlueprint";
import EmployeeMobileHomeNowCard from "@/components/workos/employee-mobile/EmployeeMobileHomeNowCard";
import EmployeeMobileModuleTile from "@/components/workos/employee-mobile/EmployeeMobileModuleTile";
import {
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { pickBlockedTasks, pickHeroTask } from "@/lib/employeeMobileTaskSummary";
import {
  buildEmployeeMobileTasksPath,
  countUpcomingTasks,
} from "@/lib/employeeMobileTaskViews";

export default function EmployeeMobileHomeDashboard() {
  const [tasksLoading, setTasksLoading] = useState(true);
  const [tasksError, setTasksError] = useState<string | null>(null);
  const [upcomingCount, setUpcomingCount] = useState(0);
  const [blockedCount, setBlockedCount] = useState(0);
  const [hero, setHero] = useState(pickHeroTask([]));
  const [allTasks, setAllTasks] = useState<EmployeeMobileTaskDTO[]>([]);

  const documentsHref = useMemo(() => {
    if (hero.task?.order_id) {
      return buildEmployeeMobileOrderBlueprintPath(hero.task.order_id);
    }
    return buildEmployeeMobileTasksPath("all");
  }, [hero.task?.order_id]);

  const loadTasks = useCallback(async () => {
    setTasksLoading(true);
    setTasksError(null);
    try {
      const rows = await listEmployeeMobileTasks();
      setAllTasks(rows);
      setUpcomingCount(countUpcomingTasks(rows));
      setBlockedCount(pickBlockedTasks(rows).length);
      setHero(pickHeroTask(rows));
    } catch (err) {
      setUpcomingCount(0);
      setBlockedCount(0);
      setAllTasks([]);
      setHero(pickHeroTask([]));
      setTasksError(err instanceof Error ? err.message : "Nu am putut încărca taskurile.");
    } finally {
      setTasksLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  return (
    <div className="space-y-4" data-testid="employee-mobile-home">
      <section data-testid="employee-mobile-home-hero">
        {tasksLoading && (
          <EmployeeMobileLoadingState
            message="Se încarcă…"
            testId="employee-mobile-home-hero-loading"
          />
        )}

        {!tasksLoading && tasksError && (
          <EmployeeMobileErrorState message={tasksError} testId="employee-mobile-home-hero-error" />
        )}

        {!tasksLoading && !tasksError && (
          <EmployeeMobileHomeNowCard
            hero={hero}
            hasAnyTasks={allTasks.length > 0}
            testIdPrefix="employee-mobile-home-hero"
          />
        )}
      </section>

      <div
        className="grid grid-cols-2 gap-2.5"
        data-testid="employee-mobile-home-module-grid"
      >
        <EmployeeMobileModuleTile
          to={buildEmployeeMobileTasksPath("all")}
          title="Taskurile mele"
          icon={ListTodo}
          testId="employee-mobile-home-module-tasks"
        />
        <EmployeeMobileModuleTile
          to={buildEmployeeMobileTasksPath("pipeline")}
          title="Lucrarea curentă"
          icon={Package}
          testId="employee-mobile-home-module-pipeline"
        />
        <EmployeeMobileModuleTile
          to={documentsHref}
          title="Documente"
          icon={FileText}
          testId="employee-mobile-home-module-documents"
        />
        <EmployeeMobileModuleTile
          to={buildEmployeeMobileTasksPath("blocked")}
          title="Blocaje"
          icon={AlertTriangle}
          badge={tasksLoading ? "…" : blockedCount > 0 ? blockedCount : undefined}
          testId="employee-mobile-home-module-blocked"
        />
        <EmployeeMobileModuleTile
          to={buildEmployeeMobileTasksPath("upcoming")}
          title="Urmează"
          icon={CalendarClock}
          badge={tasksLoading ? "…" : upcomingCount > 0 ? upcomingCount : undefined}
          testId="employee-mobile-home-module-upcoming"
        />
        <EmployeeMobileModuleTile
          to="/employee-app/personal"
          title="Personal"
          icon={User}
          testId="employee-mobile-home-module-personal"
        />
      </div>

      <div className="space-y-2 pt-0.5" data-testid="employee-mobile-home-secondary">
        <Link
          to="/employee-app/info"
          className="inline-flex w-full min-h-[44px] items-center text-sm font-medium text-slate-500 hover:text-slate-300 px-1"
          data-testid="employee-mobile-home-info"
        >
          Info & acces →
        </Link>
      </div>
    </div>
  );
}
