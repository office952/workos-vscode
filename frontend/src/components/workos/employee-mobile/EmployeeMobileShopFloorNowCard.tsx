import { Link } from "react-router-dom";
import { ArrowRight, ChevronDown, FileText } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";
import EmployeeMobileHomeBriefStrip from "@/components/workos/employee-mobile/EmployeeMobileHomeBriefStrip";
import EmployeeMobileTaskActionBar from "@/components/workos/employee-mobile/EmployeeMobileTaskActionBar";
import {
  buildRecommendationReason,
  formatWorkContextLine,
  pickUpcomingMineTasks,
  SHOP_FLOOR_GENERIC_STEPS,
  simplifyStatusLabel,
  type HomeBriefLine,
} from "@/lib/employeeMobileShopFloorPresentation";
import { buildEmployeeMobileTasksPath } from "@/lib/employeeMobileTaskViews";

const PRIMARY_BUTTON_CLASS =
  "inline-flex w-full min-h-[48px] items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-base font-semibold text-white hover:bg-emerald-500 transition-colors disabled:opacity-50";

const DOCUMENT_LINK_CLASS =
  "inline-flex w-full min-h-[44px] items-center gap-2 rounded-xl px-1 py-2 text-sm font-medium text-blue-300 hover:text-blue-200";

const FULL_FLOW_LINK_CLASS =
  "inline-flex w-full min-h-[44px] items-center text-sm font-medium text-blue-300 hover:text-blue-200";

export default function EmployeeMobileShopFloorNowCard({
  userName,
  personalTask,
  blueprintTask,
  blueprintTasks = [],
  currentTaskId = null,
  orderLabel,
  clientLabel,
  briefLines = [],
  onOpenTask,
  onActionComplete,
  showFullFlowLink = true,
  variant = "execution",
  testIdPrefix = "employee-mobile-shop-floor",
}: {
  userName?: string | null;
  personalTask: EmployeeMobileTaskDTO | null;
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null;
  blueprintTasks?: EmployeeMobileOrderBlueprintTask[];
  currentTaskId?: string | null;
  orderLabel?: string | null;
  clientLabel?: string | null;
  briefLines?: HomeBriefLine[];
  onOpenTask?: (task: EmployeeMobileTaskDTO) => void;
  onActionComplete?: () => Promise<void>;
  showFullFlowLink?: boolean;
  variant?: "home" | "execution";
  testIdPrefix?: string;
}) {
  const isHome = variant === "home";
  const firstName = userName?.split(/\s+/)[0] || "coleg";
  const workContext = formatWorkContextLine(personalTask);
  const taskTitle =
    personalTask?.title ||
    blueprintTask?.name ||
    "Niciun task activ";

  const statusLabel = simplifyStatusLabel({
    readinessStatus: blueprintTask?.readiness_status ?? personalTask?.readiness_status,
    readinessLabel: blueprintTask?.readiness_label ?? personalTask?.readiness_label,
    statusDisplay: blueprintTask?.status_display,
    status: personalTask?.status,
  });

  const recommendationReason = buildRecommendationReason({ blueprintTask, personalTask });
  const upcoming = pickUpcomingMineTasks(blueprintTasks, currentTaskId, 2);

  const showInlineStart =
    !isHome &&
    personalTask &&
    personalTask.status === "assigned" &&
    personalTask.is_startable === true &&
    onActionComplete;

  const showInlineComplete =
    !isHome &&
    personalTask &&
    personalTask.status === "in_progress" &&
    onActionComplete;

  const hasDocuments =
    blueprintTask?.has_documents ||
    (personalTask?.documents && personalTask.documents.length > 0);

  const openTaskHref = buildEmployeeMobileTasksPath("today");

  const homeCtaLabel =
    personalTask?.status === "in_progress" ? "Continuă task" : "Deschide task";

  return (
    <section
      className="rounded-2xl border border-emerald-800/40 bg-gradient-to-br from-emerald-950/30 to-[#0A1020]/90 px-4 py-4 space-y-4"
      data-testid={`${testIdPrefix}-now`}
    >
      {isHome ? (
        <p className="text-sm text-slate-400" data-testid={`${testIdPrefix}-greeting`}>
          Bună, {firstName}
        </p>
      ) : null}

      {isHome ? (
        <div
          className="rounded-xl border border-blue-900/35 bg-blue-950/20 px-3 py-2.5 space-y-1"
          data-testid={`${testIdPrefix}-work-context`}
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-300/90">
            Lucrarea ta acum
          </p>
          <p className="text-base font-semibold text-slate-100">{workContext.title}</p>
          {workContext.subtitle ? (
            <p className="text-sm text-slate-400">{workContext.subtitle}</p>
          ) : null}
        </div>
      ) : null}

      {isHome && briefLines.length > 0 ? (
        <EmployeeMobileHomeBriefStrip
          lines={briefLines}
          testId={`${testIdPrefix}-brief`}
        />
      ) : null}

      <div className="space-y-2">
        <p
          className="text-xs font-semibold uppercase tracking-wide text-emerald-300/90"
          data-testid={`${testIdPrefix}-heading`}
        >
          {isHome ? "Recomandat acum" : "Ce am de făcut acum"}
        </p>
        <h2
          className="text-xl font-semibold text-slate-50 leading-snug"
          data-testid={
            testIdPrefix === "employee-mobile-home-hero"
              ? "employee-mobile-home-hero-task"
              : `${testIdPrefix}-task-title`
          }
        >
          {taskTitle}
        </h2>
        {!isHome && (orderLabel || clientLabel || personalTask?.client) ? (
          <p className="text-sm text-slate-400" data-testid={`${testIdPrefix}-order-client`}>
            Lucrare: {[orderLabel || personalTask?.order_code, clientLabel || personalTask?.client]
              .filter(Boolean)
              .join(" · ")}
          </p>
        ) : null}
        <div className="rounded-xl border border-[#243044]/80 bg-[#070B14]/60 px-3 py-2.5 space-y-1">
          <p className="text-xs uppercase tracking-wide text-slate-500">Status</p>
          <p className="text-base font-medium text-emerald-100" data-testid={`${testIdPrefix}-status`}>
            {statusLabel}
          </p>
          {recommendationReason ? (
            <p
              className="text-sm text-amber-200/90 leading-snug"
              data-testid={`${testIdPrefix}-recommendation-reason`}
            >
              {recommendationReason}
            </p>
          ) : null}
        </div>
      </div>

      {isHome ? (
        <details className="rounded-lg border border-[#243044]/60 bg-[#070B14]/40 px-3 py-2">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2 text-sm text-slate-400 min-h-[44px]">
            Pași rapizi
            <ChevronDown className="w-4 h-4" aria-hidden />
          </summary>
          <ol className="list-decimal pl-5 pt-1 space-y-1 text-sm text-slate-400 leading-relaxed">
            {SHOP_FLOOR_GENERIC_STEPS.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </details>
      ) : null}

      <div className="space-y-2">
        {showInlineStart && personalTask ? (
          <EmployeeMobileTaskActionBar
            task={personalTask}
            onActionComplete={onActionComplete!}
            layout="shopFloor"
            testIdPrefix={`${testIdPrefix}-actions`}
          />
        ) : null}

        {showInlineComplete && personalTask ? (
          <>
            <EmployeeMobileTaskActionBar
              task={personalTask}
              onActionComplete={onActionComplete!}
              layout="shopFloor"
              testIdPrefix={`${testIdPrefix}-actions`}
            />
            {hasDocuments && onOpenTask ? (
              <button
                type="button"
                onClick={() => onOpenTask(personalTask)}
                className={DOCUMENT_LINK_CLASS}
                data-testid={`${testIdPrefix}-documents`}
              >
                <FileText className="w-4 h-4 shrink-0" aria-hidden />
                Documente și schiță
              </button>
            ) : null}
          </>
        ) : null}

        {isHome && personalTask ? (
          <Link
            to={openTaskHref}
            className={PRIMARY_BUTTON_CLASS}
            data-testid="employee-mobile-home-hero-cta"
          >
            {homeCtaLabel}
            <ArrowRight className="w-4 h-4" aria-hidden />
          </Link>
        ) : null}

        {!isHome && personalTask && onOpenTask && personalTask.status !== "in_progress" ? (
          <button
            type="button"
            onClick={() => onOpenTask(personalTask)}
            className={PRIMARY_BUTTON_CLASS}
            data-testid={`${testIdPrefix}-open-task`}
          >
            Deschide task
            <ArrowRight className="w-4 h-4" aria-hidden />
          </button>
        ) : null}

        {!personalTask ? (
          <Link
            to={openTaskHref}
            className={PRIMARY_BUTTON_CLASS}
            data-testid={`${testIdPrefix}-see-tasks`}
          >
            Vezi taskurile
          </Link>
        ) : null}
      </div>

      {!isHome && upcoming.length > 0 ? (
        <div className="space-y-1.5 pt-1" data-testid={`${testIdPrefix}-upcoming`}>
          <p className="text-sm font-semibold text-slate-300">Urmează</p>
          <ul className="space-y-1 text-sm text-slate-400">
            {upcoming.map((task) => (
              <li key={task.task_id}>
                {task.name}
                {task.readiness_label ? ` — ${task.readiness_label.toLowerCase()}` : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {showFullFlowLink ? (
        <Link
          to={buildEmployeeMobileTasksPath("pipeline")}
          className={FULL_FLOW_LINK_CLASS}
          data-testid={`${testIdPrefix}-full-flow-link`}
        >
          Vezi tot fluxul comenzii →
        </Link>
      ) : null}
    </section>
  );
}
