import { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CalendarClock,
  FileText,
  ListTodo,
  Package,
  User,
} from "lucide-react";
import { pickBlockedTasks, pickHeroTask } from "@/lib/employeeMobileTaskSummary";
import { countStartableAvailableTasks } from "@/lib/employeeMobileV2AvailableTasks";
import { countUpcomingTasks } from "@/lib/employeeMobileTaskViews";
import { pickPrimaryOrderId } from "@/lib/employeeMobilePipelineEligibility";
import { useEmployeeMobileV2Tasks } from "@/hooks/useEmployeeMobileV2Tasks";
import { useEmployeeMobileV2AvailableTasks } from "@/hooks/useEmployeeMobileV2AvailableTasks";
import {
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { EmployeeMobileV2Header } from "@/components/workos/employee-mobile-v2/EmployeeMobileV2Shell";
import EmployeeMobileV2NowCard from "@/components/workos/employee-mobile-v2/EmployeeMobileV2NowCard";
import EmployeeMobileV2ModuleTile from "@/components/workos/employee-mobile-v2/EmployeeMobileV2ModuleTile";
import EmployeeMobileV2FutureModules from "@/components/workos/employee-mobile-v2/EmployeeMobileV2FutureModules";
import { emV2SectionLabelClass } from "@/lib/employeeMobileV2DesignTokens";

export default function EmployeeMobileV2Home() {
  const { tasks, loading, error } = useEmployeeMobileV2Tasks();
  const {
    tasks: availableTasks,
    loading: availableLoading,
  } = useEmployeeMobileV2AvailableTasks();
  const hero = useMemo(() => pickHeroTask(tasks), [tasks]);
  const startableAvailableCount = useMemo(
    () => countStartableAvailableTasks(availableTasks),
    [availableTasks],
  );
  const blockedCount = useMemo(() => pickBlockedTasks(tasks).length, [tasks]);
  const upcomingCount = useMemo(() => countUpcomingTasks(tasks), [tasks]);
  const primaryOrderId = useMemo(() => pickPrimaryOrderId(tasks), [tasks]);

  const documentsHref =
    primaryOrderId != null
      ? `/employee-app-v2/documents?orderId=${primaryOrderId}`
      : "/employee-app-v2/documents";

  return (
    <div data-testid="employee-mobile-v2-home">
      <EmployeeMobileV2Header />

      <section data-testid="employee-mobile-v2-home-hero">
        {loading ? (
          <EmployeeMobileLoadingState
            message="Se încarcă…"
            testId="employee-mobile-v2-home-hero-loading"
          />
        ) : null}
        {!loading && error ? (
          <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-home-hero-error" />
        ) : null}
        {!loading && !error ? (
          <EmployeeMobileV2NowCard
            hero={hero}
            hasAnyTasks={tasks.length > 0}
            testIdPrefix="employee-mobile-v2-home-hero"
          />
        ) : null}
      </section>

      {!loading && !error && !availableLoading && hero.mode === "empty" && startableAvailableCount > 0 ? (
        <div
          className="mb-4 rounded-lg border border-blue-500/30 bg-blue-950/20 px-4 py-3"
          data-testid="employee-mobile-v2-home-startable-teaser"
        >
          <p className="text-[14px] text-slate-100">
            Ai {startableAvailableCount} taskuri pe care le poți începe acum.
          </p>
          <Link
            to="/employee-app-v2/tasks"
            className="mt-2 inline-block text-[13px] font-medium text-blue-300 hover:text-blue-200"
            data-testid="employee-mobile-v2-home-startable-teaser-cta"
          >
            Vezi taskurile
          </Link>
        </div>
      ) : null}

      <p className={emV2SectionLabelClass()}>Module</p>
      <div
        className="mt-3 grid grid-cols-2 gap-3 mb-6"
        data-testid="employee-mobile-v2-home-module-grid"
      >
        <EmployeeMobileV2ModuleTile
          to="/employee-app-v2/tasks"
          title="Taskurile mele"
          icon={ListTodo}
          accent="blue"
          testId="employee-mobile-v2-home-module-tasks"
        />
        <EmployeeMobileV2ModuleTile
          to="/employee-app-v2/pipeline"
          title="Lucrarea curentă"
          icon={Package}
          accent="violet"
          testId="employee-mobile-v2-home-module-pipeline"
        />
        <EmployeeMobileV2ModuleTile
          to={documentsHref}
          title="Documente"
          icon={FileText}
          accent="amber"
          testId="employee-mobile-v2-home-module-documents"
        />
        <EmployeeMobileV2ModuleTile
          to="/employee-app-v2/blockers"
          title="Blocaje"
          icon={AlertTriangle}
          accent="red"
          badge={loading ? "…" : blockedCount > 0 ? blockedCount : undefined}
          testId="employee-mobile-v2-home-module-blocked"
        />
        <EmployeeMobileV2ModuleTile
          to="/employee-app-v2/upcoming"
          title="Urmează"
          icon={CalendarClock}
          accent="slate"
          badge={loading ? "…" : upcomingCount > 0 ? upcomingCount : undefined}
          testId="employee-mobile-v2-home-module-upcoming"
        />
        <EmployeeMobileV2ModuleTile
          to="/employee-app-v2/personal"
          title="Personal"
          icon={User}
          accent="slate"
          testId="employee-mobile-v2-home-module-personal"
        />
      </div>

      <EmployeeMobileV2FutureModules />
    </div>
  );
}
