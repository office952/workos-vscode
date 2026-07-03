import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import {
  fetchEmployeeMobileOrderBlueprint,
  type EmployeeMobileOrderBlueprintTask,
} from "@/api/employeeMobileOrderBlueprint";
import EmployeeMobileTaskClarificationPanel from "@/components/workos/employee-mobile/EmployeeMobileTaskClarificationPanel";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import EmployeeMobileV2AvailablePreviewActionBar from "@/components/workos/employee-mobile-v2/EmployeeMobileV2AvailablePreviewActionBar";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
import EmployeeMobileV2StatusIndicator from "@/components/workos/employee-mobile-v2/EmployeeMobileV2StatusIndicator";
import EmployeeMobileV2WorkRoomActionBar from "@/components/workos/employee-mobile-v2/EmployeeMobileV2WorkRoomActionBar";
import {
  emV2Controls,
  emV2Surface,
  emV2TaskDetailScrollPad,
} from "@/lib/employeeMobileV2DesignTokens";
import { v2Effects } from "@/lib/employeeMobileV2Effects";
import { useEmployeeMobileV2TaskDetail } from "@/hooks/useEmployeeMobileV2TaskDetail";
import {
  collectBeforeYouStartLines,
  formatInstructionsAsLines,
} from "@/lib/employeeMobileShopFloorPresentation";
import { resolveEmployeeMobileV2StatusPresentation } from "@/lib/employeeMobileV2Status";
import {
  EMPLOYEE_MOBILE_TASK_NOT_ACCESSIBLE_MESSAGE,
  isEmployeeMobileV2TaskPreview,
} from "@/lib/resolveEmployeeMobileV2Task";
import {
  documentTypeLabel,
  normalizeTaskDocuments,
  taskInstructionsText,
} from "@/lib/employeeMobileTaskDocuments";
import {
  formatEmployeeMobileV2MachineLabel,
  formatEmployeeMobileV2ProcessLabel,
} from "@/lib/employeeMobileV2Labels";
import { cn } from "@/lib/utils";

function participantHint(task: { active_helper_count?: number }): string {
  const count = task.active_helper_count ?? 0;
  if (count <= 0) return "Lucrezi singur";
  return count === 1 ? "+1 coleg activ" : `+${count} colegi activi`;
}

export default function EmployeeMobileV2TaskDetailPage() {
  const { taskId } = useParams();
  const [searchParams] = useSearchParams();
  const orderIdParam = searchParams.get("orderId");
  const orderIdFilter =
    orderIdParam && Number.isFinite(Number(orderIdParam)) ? Number(orderIdParam) : null;

  const { task, loading, error, reload } = useEmployeeMobileV2TaskDetail(
    taskId,
    orderIdFilter,
  );
  const [blueprintTask, setBlueprintTask] = useState<EmployeeMobileOrderBlueprintTask | null>(
    null,
  );
  const isPreview = isEmployeeMobileV2TaskPreview(task);
  const [detailsOpen, setDetailsOpen] = useState(isPreview);

  useEffect(() => {
    setDetailsOpen(isPreview);
  }, [isPreview, task?.task_id, task?.order_id]);

  const loadBlueprint = useCallback(async () => {
    if (!task || isPreview) {
      setBlueprintTask(null);
      return;
    }
    try {
      const data = await fetchEmployeeMobileOrderBlueprint(task.order_id);
      const match = data.tasks?.find((row) => row.task_id === task.task_id) ?? null;
      setBlueprintTask(match);
    } catch {
      setBlueprintTask(null);
    }
  }, [task, isPreview]);

  useEffect(() => {
    void loadBlueprint();
  }, [loadBlueprint]);

  const refresh = useCallback(async () => {
    await reload();
    await loadBlueprint();
  }, [reload, loadBlueprint]);

  const missingMessage = useMemo(() => {
    if (orderIdFilter != null) {
      return EMPLOYEE_MOBILE_TASK_NOT_ACCESSIBLE_MESSAGE;
    }
    return "Taskul nu a fost găsit în lista ta.";
  }, [orderIdFilter]);

  if (loading) {
    return (
      <EmployeeMobileLoadingState
        message="Se încarcă camera de lucru…"
        testId="employee-mobile-v2-work-room-loading"
      />
    );
  }

  if (error && !task) {
    return (
      <div data-testid="employee-mobile-v2-work-room">
        <EmployeeMobileV2PageHeader
          backTo="/employee-app-v2/tasks"
          backLabel="Înapoi la taskuri"
          title="Work Room"
          testId="employee-mobile-v2-work-room-header"
        />
        <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-work-room-error" />
      </div>
    );
  }

  if (!task) {
    return (
      <div data-testid="employee-mobile-v2-work-room">
        <EmployeeMobileV2PageHeader
          backTo="/employee-app-v2/tasks"
          backLabel="Înapoi la taskuri"
          title="Task negăsit"
          testId="employee-mobile-v2-work-room-header"
        />
        <EmployeeMobileEmptyState
          message={missingMessage}
          testId="employee-mobile-v2-work-room-missing"
        />
      </div>
    );
  }

  const instructions = taskInstructionsText(task);
  const instructionLines = instructions ? formatInstructionsAsLines(instructions) : [];
  const documents = normalizeTaskDocuments(task.documents);
  const beforeYouStart = collectBeforeYouStartLines({ task, blueprintTask });
  const materialHints = blueprintTask?.material_hints ?? [];
  const statusPresentation = resolveEmployeeMobileV2StatusPresentation(task, blueprintTask);
  const processLabel = formatEmployeeMobileV2ProcessLabel(task.process_type);
  const machineLabel = formatEmployeeMobileV2MachineLabel(task.machine_type);
  const orderLabel = task.order_code || `Comandă #${task.order_id}`;
  const previewInstructionLines = isPreview ? instructionLines : instructionLines.slice(0, 3);
  const operationalLines = [...beforeYouStart, ...previewInstructionLines].filter(Boolean);
  const hasSecondaryDetails =
    (!isPreview && instructionLines.length > 3) ||
    materialHints.length > 0 ||
    documents.length > 0 ||
    Boolean(processLabel || machineLabel);

  return (
    <div
      className={cn("space-y-1", emV2TaskDetailScrollPad)}
      data-testid="employee-mobile-v2-work-room"
      data-preview-only={isPreview ? "true" : "false"}
    >
      <div data-testid="employee-mobile-v2-task-detail">
        <EmployeeMobileV2PageHeader
          backTo="/employee-app-v2/tasks"
          backLabel="Înapoi la taskuri"
          title={task.title || task.task_id}
          testId="employee-mobile-v2-work-room-header"
        />

        <EmployeeMobileV2StatusIndicator
          presentation={statusPresentation}
          align="start"
          testId="employee-mobile-v2-work-room-status"
        />

        <div className="mt-3 space-y-1" data-testid="employee-mobile-v2-work-room-context">
          <p className="text-[13px] text-slate-400">
            {[orderLabel, task.client, task.product].filter(Boolean).join(" · ")}
          </p>
          <p
            className="text-[12px] text-slate-500"
            data-testid="employee-mobile-v2-work-room-participants"
          >
            {participantHint(task)}
          </p>
          {task.blocked_reason ? (
            <p
              className="text-[12px] text-rose-300/90 mt-1"
              data-testid="employee-mobile-v2-work-room-block-reason"
            >
              Blocat: {task.blocked_reason}
            </p>
          ) : null}
        </div>

        <section
          className={cn(emV2Surface.panel, "mt-4 p-4")}
          data-testid="employee-mobile-v2-work-room-now"
        >
          <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Ce fac acum
          </p>
          {(processLabel || machineLabel) && !isPreview ? (
            <dl className="space-y-1.5 text-sm mb-3">
              {processLabel ? (
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Proces</dt>
                  <dd className="font-medium text-slate-200">{processLabel}</dd>
                </div>
              ) : null}
              {machineLabel ? (
                <div className="flex justify-between gap-3">
                  <dt className="text-slate-500">Post</dt>
                  <dd className="font-medium text-slate-200">{machineLabel}</dd>
                </div>
              ) : null}
            </dl>
          ) : null}
          {operationalLines.length > 0 ? (
            <ul className="space-y-1.5 text-sm text-slate-300 leading-relaxed">
              {operationalLines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Fără instrucțiuni suplimentare.</p>
          )}
        </section>

        {isPreview && instructionLines.length > 0 ? (
          <section
            className={cn(emV2Surface.panel, "mt-4 p-4")}
            data-testid="employee-mobile-v2-work-room-preview-instructions"
          >
            <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
              Instrucțiuni complete
            </p>
            <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
              {instructionLines.join("\n")}
            </p>
          </section>
        ) : null}

        {hasSecondaryDetails ? (
          <section className="mt-4" data-testid="employee-mobile-v2-work-room-details">
            <button
              type="button"
              className="flex w-full min-h-[44px] items-center justify-between rounded-lg border border-[#1E293B] bg-[#111827] px-4 py-3 text-sm font-medium text-slate-200"
              aria-expanded={detailsOpen}
              onClick={() => setDetailsOpen((open) => !open)}
              data-testid="employee-mobile-v2-work-room-details-toggle"
            >
              Detalii suplimentare
              <ChevronDown
                className={cn("h-4 w-4 transition-transform", detailsOpen && "rotate-180")}
                aria-hidden
              />
            </button>
            {detailsOpen ? (
              <div className="mt-3 space-y-4">
                {!isPreview && instructionLines.length > 3 ? (
                  <div className={cn(emV2Surface.panel, "p-4")}>
                    <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
                      Instrucțiuni complete
                    </p>
                    <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {instructionLines.join("\n")}
                    </p>
                  </div>
                ) : null}
                {materialHints.length > 0 ? (
                  <div className={cn(emV2Surface.panel, "p-4")}>
                    <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
                      Materiale
                    </p>
                    <ul className="space-y-1.5 text-sm text-slate-300">
                      {materialHints.map((hint) => (
                        <li key={`${hint.name}-${hint.label}`}>
                          {hint.name}
                          {hint.label ? ` — ${hint.label}` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {documents.length > 0 ? (
                  <div className={cn(emV2Surface.panel, "p-4")}>
                    <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
                      Documente
                    </p>
                    <ul className="space-y-2">
                      {documents.map((doc) => (
                        <li
                          key={doc.id}
                          className="flex items-center justify-between gap-3 min-h-[44px]"
                        >
                          <span className="min-w-0">
                            <span className="block text-sm font-medium text-slate-200 truncate">
                              {doc.name}
                            </span>
                            <span className="text-xs text-slate-500">
                              {documentTypeLabel(doc.type)}
                            </span>
                          </span>
                          {doc.url ? (
                            <a
                              href={doc.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="shrink-0 text-sm font-medium text-blue-400 min-h-[44px] inline-flex items-center"
                            >
                              Deschide
                            </a>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}
          </section>
        ) : null}
      </div>

      <div
        className={cn(
          "fixed bottom-[calc(72px+env(safe-area-inset-bottom,0px))] inset-x-0 z-30 px-4 py-3 max-w-[430px] mx-auto space-y-2",
          emV2Controls.actionGroup,
          v2Effects.stickyActionBar,
        )}
      >
        {isPreview ? (
          <EmployeeMobileV2AvailablePreviewActionBar task={task} onStarted={refresh} />
        ) : (
          <>
            <EmployeeMobileTaskClarificationPanel
              task={task}
              onSubmitted={refresh}
              variant="footer"
              visualVariant="v2"
            />
            <EmployeeMobileV2WorkRoomActionBar task={task} onActionComplete={refresh} />
          </>
        )}
      </div>
    </div>
  );
}
