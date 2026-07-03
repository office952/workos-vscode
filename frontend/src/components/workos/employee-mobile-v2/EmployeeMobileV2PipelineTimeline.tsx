import { useMemo } from "react";
import { AlertTriangle, Check, ChevronRight } from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintDTO } from "@/api/employeeMobileOrderBlueprint";
import {
  emV2Controls,
  emV2PipelineScrollPad,
  emV2PrimaryButtonClass,
  emV2SectionLabelClass,
  emV2Surface,
  pipelineAxisMarkerClass,
  pipelineAxisMarkerLegendClass,
  pipelineStepLabelClass,
  pipelineVerticalRowStateClass,
} from "@/lib/employeeMobileV2DesignTokens";
import {
  buildPersonalTasksById,
  buildPipelineTaskPresentation,
  resolvePipelineCurrentTaskId,
} from "@/lib/employeeMobilePipelineEligibility";
import { getTaskWaitingDetailShort } from "@/lib/employeeMobileV2TaskGrouping";
import {
  getPipelineDependencyWarningShort,
  getPipelineLegendLabel,
  getPipelineRowContextLine,
  getPipelineStepLabel,
  PIPELINE_LEGEND_REFERENCE,
  pipelineMarkerToRowState,
  resolveEmployeeMobileV2PipelineMarkerPresentation,
  resolvePipelineRowVisualState,
  type PipelineRowVisualState,
} from "@/lib/employeeMobileV2Status";
import { cn } from "@/lib/utils";

function pipelineTitleClass(rowState: PipelineRowVisualState): string {
  switch (rowState) {
    case "current":
      return emV2Controls.pipelineTitleCurrent;
    case "blocked":
      return emV2Controls.pipelineTitleBlocked;
    case "completed":
      return emV2Controls.pipelineTitleCompleted;
    case "alt-post":
      return emV2Controls.pipelineTitleAltPost;
    case "waiting":
      return emV2Controls.pipelineTitleWaiting;
    default:
      return emV2Controls.pipelineTitleNeutral;
  }
}

function pipelineContextSubtextClass(rowState: PipelineRowVisualState): string {
  switch (rowState) {
    case "blocked":
      return emV2Controls.pipelineSubtextBlocked;
    case "waiting":
      return emV2Controls.pipelineSubtextWaiting;
    default:
      return emV2Controls.pipelineSubtextDefault;
  }
}

function pipelineMaterialHintClass(): string {
  return emV2Controls.pipelineSubtextDefault;
}

function axisMarkerIconClass(rowState: PipelineRowVisualState): string {
  if (rowState === "current") return "h-3.5 w-3.5";
  if (rowState === "alt-post") return "h-3 w-3 opacity-70";
  if (rowState === "neutral") return "h-2 w-2";
  return "h-3 w-3";
}

function isPipelineRowTappable(rowState: PipelineRowVisualState): boolean {
  return rowState !== "completed" && rowState !== "alt-post";
}

export default function EmployeeMobileV2PipelineTimeline({
  blueprint,
  personalTasks = [],
  onOpenTask,
  listHeading = "Timeline",
  listTestId = "employee-mobile-v2-pipeline-timeline",
}: {
  blueprint: EmployeeMobileOrderBlueprintDTO;
  personalTasks?: EmployeeMobileTaskDTO[];
  onOpenTask?: (task: EmployeeMobileTaskDTO) => void;
  listHeading?: string;
  listTestId?: string;
}) {
  const personalById = useMemo(() => buildPersonalTasksById(personalTasks), [personalTasks]);
  const currentTaskId = useMemo(
    () => resolvePipelineCurrentTaskId(blueprint.tasks, personalById),
    [blueprint.tasks, personalById],
  );
  const currentPersonalTask = currentTaskId ? personalById.get(currentTaskId) ?? null : null;

  const taskPresentations = useMemo(
    () =>
      blueprint.tasks.map((task, index) => ({
        task,
        presentation: buildPipelineTaskPresentation(task, index, currentTaskId, personalById),
        personal: personalById.get(task.task_id),
      })),
    [blueprint.tasks, currentTaskId, personalById],
  );

  return (
    <div
      className={cn("space-y-3", emV2PipelineScrollPad)}
      data-testid="employee-mobile-v2-pipeline-timeline-root"
    >
      <p className={emV2SectionLabelClass()}>{listHeading}</p>

      <ol className={cn(emV2Surface.panel, "overflow-hidden p-0")} data-testid={listTestId}>
        {taskPresentations.map(({ task, presentation, personal }, index) => {
          const isCurrent = presentation.isCurrent && task.is_mine;
          const rowState = resolvePipelineRowVisualState({
            isCurrent,
            marker: presentation.marker,
          });
          const canOpen = Boolean(task.is_mine && personal && onOpenTask);
          const showChevron = canOpen && isPipelineRowTappable(rowState);
          const markerPresentation = resolveEmployeeMobileV2PipelineMarkerPresentation(
            presentation.marker,
            presentation.markerLabel,
            isCurrent,
          );
          const AxisIcon = markerPresentation?.Icon;
          const waitingDetail =
            personal && presentation.marker === "asteapta"
              ? getTaskWaitingDetailShort(personal)
              : null;
          const statusContextLine = getPipelineRowContextLine(
            presentation.marker,
            presentation.markerLabel,
            waitingDetail,
            personal?.blocked_reason ?? null,
          );
          const dependencyWarningShort = getPipelineDependencyWarningShort(
            presentation.dependencyWarning,
          );
          const hasWarning = Boolean(dependencyWarningShort);
          const hasMaterialHint = (task.material_hints?.length ?? 0) > 0;
          const isFirst = index === 0;
          const isLast = index === taskPresentations.length - 1;

          return (
            <li
              key={task.task_id}
              data-testid={`employee-mobile-pipeline-task-${task.task_id}`}
              data-pipeline-state={rowState}
            >
              <button
                type="button"
                disabled={!canOpen}
                onClick={() => personal && onOpenTask?.(personal)}
                className={cn(
                  emV2Controls.pipelineVerticalRow,
                  pipelineVerticalRowStateClass(rowState),
                  canOpen && isPipelineRowTappable(rowState)
                    ? cn(emV2Controls.pipelineRowHoverTappable, "cursor-pointer")
                    : "cursor-default",
                )}
              >
                <span className={emV2Controls.pipelineVerticalAxis} aria-hidden>
                  <span
                    className={cn(
                      emV2Controls.pipelineVerticalLine,
                      isFirst && emV2Controls.pipelineVerticalLineHidden,
                    )}
                  />
                  <span
                    className={pipelineAxisMarkerClass(rowState)}
                    data-testid={`employee-mobile-pipeline-axis-marker-${task.task_id}`}
                    data-pipeline-axis-pulse={rowState === "current" ? "true" : undefined}
                  >
                    {rowState === "current" ? (
                      <span
                        className={emV2Controls.pipelineCurrentMarkerPulseRing}
                        data-testid={`employee-mobile-pipeline-axis-pulse-${task.task_id}`}
                        aria-hidden
                      />
                    ) : null}
                    {rowState === "completed" ? (
                      <Check className="h-3 w-3 stroke-[2.5]" aria-hidden />
                    ) : AxisIcon ? (
                      <AxisIcon className={axisMarkerIconClass(rowState)} aria-hidden />
                    ) : null}
                  </span>
                  <span
                    className={cn(
                      emV2Controls.pipelineVerticalLine,
                      isLast && emV2Controls.pipelineVerticalLineHidden,
                    )}
                  />
                </span>

                <span className="min-w-0 flex-1 overflow-hidden text-left">
                  <span className="flex flex-wrap items-center gap-x-1">
                    <span
                      className={pipelineStepLabelClass(rowState)}
                      data-testid={`employee-mobile-pipeline-task-number-${task.task_id}`}
                    >
                      {getPipelineStepLabel(presentation.taskNumber)}
                    </span>
                    {rowState === "alt-post" ? (
                      <span className={emV2Controls.pipelineAltPostBadge}>Alt post</span>
                    ) : null}
                  </span>

                  <span
                    className={cn(
                      "mt-0.5 block text-[14px] font-medium leading-snug",
                      isCurrent ? "line-clamp-2" : "line-clamp-1",
                      pipelineTitleClass(rowState),
                    )}
                  >
                    {task.name}
                  </span>

                  {hasWarning ? (
                    <span
                      className={cn(emV2Controls.attentionLine, "mt-1 max-w-full")}
                      data-testid={`employee-mobile-pipeline-dependency-warning-${task.task_id}`}
                    >
                      <AlertTriangle className="h-3 w-3 shrink-0" aria-hidden />
                      <span className="truncate">{dependencyWarningShort}</span>
                    </span>
                  ) : null}

                  {statusContextLine ? (
                    <span
                      className={cn(
                        "mt-0.5 block text-[11px]",
                        pipelineContextSubtextClass(rowState),
                        isCurrent ? "line-clamp-2" : "line-clamp-1",
                      )}
                      data-testid={`employee-mobile-pipeline-status-context-${task.task_id}`}
                    >
                      {statusContextLine}
                    </span>
                  ) : null}

                  {hasMaterialHint && task.material_hints?.[0] ? (
                    <span
                      className={cn(
                        "mt-0.5 block text-[11px]",
                        pipelineMaterialHintClass(),
                        isCurrent ? "line-clamp-2" : "line-clamp-1",
                      )}
                      data-testid={`employee-mobile-pipeline-material-hints-${task.task_id}`}
                    >
                      {task.material_hints[0].name}
                      {task.material_hints[0].label
                        ? ` · ${task.material_hints[0].label.toLowerCase()}`
                        : ""}
                    </span>
                  ) : null}
                </span>

                {showChevron ? (
                  <ChevronRight
                    className={
                      rowState === "current"
                        ? emV2Controls.pipelineChevronCurrent
                        : emV2Controls.pipelineChevronNeutral
                    }
                    aria-hidden
                  />
                ) : null}
              </button>
            </li>
          );
        })}
      </ol>

      <div
        className={emV2Controls.pipelineLegend}
        data-testid="employee-mobile-v2-pipeline-legend"
      >
        <span className={emV2Controls.pipelineLegendLabel}>Legendă:</span>
        {PIPELINE_LEGEND_REFERENCE.map((marker) => {
          const legendPresentation = resolveEmployeeMobileV2PipelineMarkerPresentation(
            marker,
            null,
            marker === "acum",
          );
          if (!legendPresentation) return null;
          const legendState = pipelineMarkerToRowState(marker);
          const { Icon } = legendPresentation;
          return (
            <span
              key={marker}
              className={emV2Controls.pipelineLegendItem}
              data-testid={`employee-mobile-v2-pipeline-legend-${marker}`}
            >
              <span className={pipelineAxisMarkerLegendClass(legendState)}>
                {legendState === "completed" ? (
                  <Check className="h-2.5 w-2.5 stroke-[2.5]" aria-hidden />
                ) : (
                  <Icon className="h-2.5 w-2.5" aria-hidden />
                )}
              </span>
              <span>{getPipelineLegendLabel(marker)}</span>
            </span>
          );
        })}
      </div>

      {currentPersonalTask && onOpenTask ? (
        <button
          type="button"
          onClick={() => onOpenTask(currentPersonalTask)}
          className={emV2PrimaryButtonClass()}
          data-testid={`employee-mobile-pipeline-open-${currentTaskId}`}
        >
          Deschide taskul curent
        </button>
      ) : null}

      <span className="sr-only" data-testid="employee-mobile-pipeline-order-card">
        {blueprint.order_label}
      </span>
    </div>
  );
}
