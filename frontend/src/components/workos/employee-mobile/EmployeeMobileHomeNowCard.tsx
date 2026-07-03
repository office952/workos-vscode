import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { HeroTaskMode, HeroTaskSelection } from "@/lib/employeeMobileTaskSummary";
import {
  buildEmployeeMobileTaskDetailPath,
  buildEmployeeMobileTasksPath,
} from "@/lib/employeeMobileTaskViews";
import { emChipClass, emOutlineAccentClass } from "@/lib/employeeMobileDesignTokens";
import { cn } from "@/lib/utils";

type NowStatus = "working" | "ready" | "blocked" | "empty";

function resolveNowStatus(mode: HeroTaskMode, task: EmployeeMobileTaskDTO | null): NowStatus {
  if (mode === "working") return "working";
  if (mode === "blocked") return "blocked";
  if (mode === "next" && task) return "ready";
  return "empty";
}

const STATUS_CHIP: Record<NowStatus, "active" | "ready" | "warning" | "neutral"> = {
  working: "active",
  ready: "ready",
  blocked: "warning",
  empty: "neutral",
};

const STATUS_LABEL: Record<NowStatus, string> = {
  working: "În lucru",
  ready: "Pregătit",
  blocked: "Blocat",
  empty: "Fără task activ",
};

function buildContextLine(task: EmployeeMobileTaskDTO | null): string | null {
  if (!task) return null;
  const parts = [
    task.client,
    task.order_code || (task.order_id != null ? `Comandă #${task.order_id}` : null),
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
      label: mode === "working" ? "Continuă" : mode === "blocked" ? "Deschide" : task.is_startable ? "Începe" : "Deschide",
      href: buildEmployeeMobileTaskDetailPath(task, mode === "next" ? "all" : "today"),
    };
  }
  if (hasAnyTasks) {
    return { label: "Vezi taskurile", href: buildEmployeeMobileTasksPath("all") };
  }
  return null;
}

export default function EmployeeMobileHomeNowCard({
  hero,
  hasAnyTasks,
  testIdPrefix = "employee-mobile-home-hero",
}: {
  hero: HeroTaskSelection;
  hasAnyTasks: boolean;
  testIdPrefix?: string;
}) {
  const status = resolveNowStatus(hero.mode, hero.task);
  const chipTone = STATUS_CHIP[status];
  const contextLine = buildContextLine(hero.task);
  const cta = resolveCta(hero, hasAnyTasks);
  const title =
    hero.task?.title?.trim() ||
    (status === "empty" ? "Niciun task activ acum" : hero.task?.task_id ?? "—");

  return (
    <section
      className="rounded-xl border border-[#243044] bg-[#0A1020]/80 px-4 py-3.5 space-y-2"
      data-testid={`${testIdPrefix}-now`}
    >
      <div className="flex items-start justify-between gap-2">
        <p
          className="text-[15px] font-semibold text-slate-100 leading-snug min-w-0 line-clamp-2"
          data-testid={`${testIdPrefix}-task`}
        >
          {title}
        </p>
        <span className={emChipClass(chipTone)} data-testid={`${testIdPrefix}-status`}>
          {STATUS_LABEL[status]}
        </span>
      </div>

      {contextLine ? (
        <p
          className="text-xs text-slate-500 truncate"
          data-testid={`${testIdPrefix}-context`}
        >
          {contextLine}
        </p>
      ) : null}

      {cta ? (
        <Link
          to={cta.href}
          className={emOutlineAccentClass()}
          data-testid={`${testIdPrefix}-cta`}
        >
          {cta.label}
          <ArrowRight className="w-4 h-4" aria-hidden />
        </Link>
      ) : null}
    </section>
  );
}
