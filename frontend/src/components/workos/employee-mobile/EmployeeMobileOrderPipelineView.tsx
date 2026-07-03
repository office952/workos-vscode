import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Circle,
  CircleDot,
  Hourglass,
  RefreshCw,
} from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  buildEmployeeMobileOrderBlueprintPath,
  type EmployeeMobileOrderBlueprintDTO,
} from "@/api/employeeMobileOrderBlueprint";
import {
  buildPersonalTasksById,
  buildPipelineTaskPresentation,
  resolvePipelineCurrentTaskId,
} from "@/lib/employeeMobilePipelineEligibility";
import { emChipClass, emOutlineAccentClass, emSurface } from "@/lib/employeeMobileDesignTokens";
import { cn } from "@/lib/utils";

function markerChipTone(
  marker: string | null | undefined,
  isCurrent: boolean,
): "neutral" | "active" | "ready" | "warning" {
  if (isCurrent || marker === "acum") return "active";
  if (marker === "asteapta") return "warning";
  if (marker === "urmeaza") return "ready";
  return "neutral";
}

export default function EmployeeMobileOrderPipelineView({
  blueprint,
  personalTasks = [],
  onOpenTask,
  showSummaryChips = false,
  showRefresh = false,
  onRefresh,
  showBlueprintLink = false,
  listHeading = "Pașii comenzii",
  listTestId = "employee-mobile-pipeline-task-list",
  collapseDefault = false,
  hideContextLine = false,
}: {
  blueprint: EmployeeMobileOrderBlueprintDTO;
  personalTasks?: EmployeeMobileTaskDTO[];
  onOpenTask?: (task: EmployeeMobileTaskDTO) => void;
  onActionComplete?: () => Promise<void>;
  showSummaryChips?: boolean;
  showRefresh?: boolean;
  onRefresh?: () => void;
  showBlueprintLink?: boolean;
  listHeading?: string;
  listTestId?: string;
  compactCards?: boolean;
  collapseDefault?: boolean;
  hideContextLine?: boolean;
}) {
  const [showAllSteps, setShowAllSteps] = useState(!collapseDefault);
  const personalById = useMemo(() => buildPersonalTasksById(personalTasks), [personalTasks]);
  const currentTaskId = useMemo(
    () => resolvePipelineCurrentTaskId(blueprint.tasks, personalById),
    [blueprint.tasks, personalById],
  );
  const currentPersonalTask = currentTaskId ? personalById.get(currentTaskId) ?? null : null;
  const currentStepIndex = useMemo(() => {
    if (!currentTaskId) return null;
    const index = blueprint.tasks.findIndex((task) => task.task_id === currentTaskId);
    return index >= 0 ? index + 1 : null;
  }, [blueprint.tasks, currentTaskId]);

  const taskPresentations = useMemo(
    () =>
      blueprint.tasks.map((task, index) => ({
        task,
        index,
        presentation: buildPipelineTaskPresentation(
          task,
          index,
          currentTaskId,
          personalById,
        ),
        personal: personalById.get(task.task_id),
      })),
    [blueprint.tasks, currentTaskId, personalById],
  );

  const visibleTaskPresentations = useMemo(() => {
    if (showAllSteps) return taskPresentations;
    return taskPresentations.filter(({ presentation, personal }) => {
      if (presentation.isCurrent) return true;
      if (presentation.marker === "urmeaza") return true;
      if (presentation.marker === "asteapta") return true;
      if (personal?.status === "blocked") return true;
      if (personal?.status === "in_progress") return true;
      return false;
    });
  }, [showAllSteps, taskPresentations]);

  const contextLine = [
    blueprint.order_label,
    blueprint.client_label,
    currentStepIndex != null
      ? `pas ${currentStepIndex}/${blueprint.tasks.length}`
      : `${blueprint.tasks.length} pași`,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="space-y-3" data-testid="employee-mobile-order-pipeline">
      {!hideContextLine ? (
        <p
          className="text-sm text-slate-400 truncate"
          data-testid="employee-mobile-pipeline-context"
        >
          {contextLine}
        </p>
      ) : null}

      {showSummaryChips ? null : null}

      {showRefresh && onRefresh ? (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onRefresh}
            className="inline-flex min-h-[44px] items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 px-2"
            data-testid="employee-mobile-pipeline-refresh"
          >
            <RefreshCw className="w-4 h-4" aria-hidden />
            Reîmprospătează
          </button>
        </div>
      ) : null}

      <section className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-medium text-slate-400">{listHeading}</h3>
          {collapseDefault && blueprint.tasks.length > visibleTaskPresentations.length ? (
            <button
              type="button"
              onClick={() => setShowAllSteps((current) => !current)}
              className="inline-flex min-h-[44px] items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-300 shrink-0"
              data-testid="employee-mobile-pipeline-expand-toggle"
            >
              {showAllSteps ? "Arată mai puțin" : `Arată toți pașii (${blueprint.tasks.length})`}
              <ChevronDown
                className={cn("w-3.5 h-3.5 transition-transform", showAllSteps && "rotate-180")}
                aria-hidden
              />
            </button>
          ) : null}
        </div>

        <ol className={cn(emSurface.panel, "overflow-hidden")} data-testid={listTestId}>
          {visibleTaskPresentations.map(({ task, presentation, personal }) => {
            const isCurrent = presentation.isCurrent;
            const markerLabel = presentation.markerLabel;
            const tone = markerChipTone(presentation.marker, isCurrent);
            const hasWarning = Boolean(presentation.dependencyWarning);
            const hasMaterialHint = (task.material_hints?.length ?? 0) > 0;
            const canOpen = Boolean(task.is_mine && personal && onOpenTask);
            const StepIcon =
              presentation.marker === "asteapta"
                ? Hourglass
                : isCurrent
                  ? CircleDot
                  : Circle;

            return (
              <li key={task.task_id} className={emSurface.row} data-testid={`employee-mobile-pipeline-task-${task.task_id}`}>
                <button
                  type="button"
                  disabled={!canOpen}
                  onClick={() => personal && onOpenTask?.(personal)}
                  className={cn(
                    "flex w-full items-center gap-3 px-3 py-3 text-left transition-colors min-h-[52px]",
                    canOpen ? "hover:bg-[#111827]/60" : "cursor-default opacity-70",
                    isCurrent && task.is_mine && "bg-[#111827]/40",
                  )}
                >
                  <span
                    className={cn(
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold",
                      task.is_mine ? "bg-slate-800 text-slate-200" : "bg-slate-900 text-slate-500",
                    )}
                    data-testid={`employee-mobile-pipeline-task-number-${task.task_id}`}
                  >
                    {presentation.taskNumber}
                  </span>

                  <span className="min-w-0 flex-1">
                    <span className="flex items-start gap-2">
                      <StepIcon
                        className={cn(
                          "w-3.5 h-3.5 shrink-0 mt-0.5",
                          isCurrent ? "text-emerald-400" : "text-slate-600",
                        )}
                        aria-hidden
                      />
                      <span
                        className={cn(
                          "text-[14px] font-medium leading-snug line-clamp-2",
                          task.is_mine ? "text-slate-100" : "text-slate-400",
                        )}
                      >
                        {task.name}
                      </span>
                    </span>

                    {hasWarning ? (
                      <span
                        className="mt-1 inline-flex items-center gap-1 text-[11px] text-amber-300/80"
                        data-testid={`employee-mobile-pipeline-dependency-warning-${task.task_id}`}
                      >
                        <AlertTriangle className="w-3 h-3 shrink-0" aria-hidden />
                        <span className="truncate">{presentation.dependencyWarning}</span>
                      </span>
                    ) : null}

                    {hasMaterialHint && task.material_hints?.[0] ? (
                      <span
                        className="mt-0.5 block text-[11px] text-slate-500 truncate"
                        data-testid={`employee-mobile-pipeline-material-hints-${task.task_id}`}
                      >
                        {task.material_hints[0].name}
                        {task.material_hints[0].label
                          ? ` · ${task.material_hints[0].label.toLowerCase()}`
                          : ""}
                      </span>
                    ) : null}
                  </span>

                  <span className="flex shrink-0 flex-col items-end gap-1">
                    {markerLabel ? (
                      <span
                        className={emChipClass(tone)}
                        data-testid={`employee-mobile-pipeline-marker-${task.task_id}`}
                      >
                        {markerLabel}
                      </span>
                    ) : null}
                    {canOpen ? (
                      <ChevronRight className="w-4 h-4 text-slate-600" aria-hidden />
                    ) : null}
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
      </section>

      {currentPersonalTask && onOpenTask ? (
        <button
          type="button"
          onClick={() => onOpenTask(currentPersonalTask)}
          className={emOutlineAccentClass()}
          data-testid={`employee-mobile-pipeline-open-${currentTaskId}`}
        >
          Deschide taskul curent
        </button>
      ) : null}

      {showBlueprintLink ? (
        <Link
          to={buildEmployeeMobileOrderBlueprintPath(blueprint.order_id)}
          className="inline-flex min-h-[44px] items-center text-xs font-medium text-slate-500 hover:text-slate-300"
          data-testid={`employee-mobile-pipeline-blueprint-link-${blueprint.order_id}`}
        >
          Vezi blueprint complet →
        </Link>
      ) : null}

      {/* Legacy test hook — order card removed in pipeline visual reset */}
      <span className="sr-only" data-testid="employee-mobile-pipeline-order-card">
        {blueprint.order_label}
      </span>
    </div>
  );
}
