import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, CircleDot, Clock3, OctagonAlert } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { HeroTaskMode, HeroTaskSelection } from "@/lib/employeeMobileTaskSummary";
import EmployeeMobileV2StatusIndicator from "@/components/workos/employee-mobile-v2/EmployeeMobileV2StatusIndicator";
import {
  buildEmployeeMobileV2TaskPath,
  emV2PrimaryButtonClass,
  emV2Surface,
} from "@/lib/employeeMobileV2DesignTokens";
import { v2Effects } from "@/lib/employeeMobileV2Effects";
import type { EmV2StatusPresentation } from "@/lib/employeeMobileV2Status";
import { cn } from "@/lib/utils";

type NowStatus = "working" | "ready" | "blocked" | "empty";

function resolveNowStatus(mode: HeroTaskMode, task: EmployeeMobileTaskDTO | null): NowStatus {
  if (mode === "working") return "working";
  if (mode === "blocked") return "blocked";
  if (mode === "next" && task) return "ready";
  return "empty";
}

const STATUS_PRESENTATION: Record<NowStatus, EmV2StatusPresentation> = {
  working: {
    shortLabel: "În lucru",
    detailLine: null,
    tone: "active",
    Icon: CircleDot,
  },
  ready: {
    shortLabel: "Pregătit",
    detailLine: null,
    tone: "ready",
    Icon: CheckCircle2,
  },
  blocked: {
    shortLabel: "Blocat",
    detailLine: null,
    tone: "warning",
    Icon: OctagonAlert,
  },
  empty: {
    shortLabel: "Fără task activ",
    detailLine: null,
    tone: "neutral",
    Icon: Clock3,
  },
};

function buildContextLine(task: EmployeeMobileTaskDTO | null): string | null {
  if (!task) return null;
  const parts = [
    task.client,
    task.order_code || (task.order_id != null ? `Comandă #${task.order_id}` : null),
    task.product,
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}

function resolveCta(
  hero: HeroTaskSelection,
  hasAnyTasks: boolean,
): { label: string; href: string } | null {
  const { task, mode } = hero;
  if (task && (mode === "working" || mode === "blocked" || mode === "next")) {
    return {
      label:
        mode === "working"
          ? "Continuă"
          : mode === "blocked"
            ? "Deschide"
            : task.is_startable
              ? "Începe"
              : "Deschide",
      href: buildEmployeeMobileV2TaskPath(task.task_id, task.order_id),
    };
  }
  if (hasAnyTasks) {
    return { label: "Vezi taskurile", href: "/employee-app-v2/tasks" };
  }
  return null;
}

export default function EmployeeMobileV2NowCard({
  hero,
  hasAnyTasks,
  testIdPrefix = "employee-mobile-v2-home-hero",
}: {
  hero: HeroTaskSelection;
  hasAnyTasks: boolean;
  testIdPrefix?: string;
}) {
  const status = resolveNowStatus(hero.mode, hero.task);
  const presentation = STATUS_PRESENTATION[status];
  const contextLine = buildContextLine(hero.task);
  const cta = resolveCta(hero, hasAnyTasks);
  const title =
    hero.task?.title?.trim() ||
    (status === "empty" ? "Niciun task activ acum" : hero.task?.task_id ?? "—");

  return (
    <section
      className={cn(emV2Surface.panel, "p-4 mb-6 space-y-3")}
      data-testid={`${testIdPrefix}-now`}
    >
      <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-emerald-400">
        <span className={v2Effects.activeDot} aria-hidden />
        Acum
      </div>

      <p
        className="text-[17px] font-semibold text-slate-100 leading-snug line-clamp-2"
        data-testid={`${testIdPrefix}-task`}
      >
        {title}
      </p>

      {contextLine ? (
        <p className="text-[13px] text-slate-400 truncate" data-testid={`${testIdPrefix}-context`}>
          {contextLine}
        </p>
      ) : null}

      <EmployeeMobileV2StatusIndicator
        presentation={presentation}
        align="start"
        testId={`${testIdPrefix}-status`}
      />

      {cta ? (
        <Link
          to={cta.href}
          className={emV2PrimaryButtonClass()}
          data-testid={`${testIdPrefix}-cta`}
        >
          {cta.label}
          <ArrowRight className="w-4 h-4" aria-hidden />
        </Link>
      ) : null}
    </section>
  );
}
