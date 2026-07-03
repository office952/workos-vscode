import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, ChevronRight, FileText, Package } from "lucide-react";
import {
  listEmployeeMobileTasks,
  type EmployeeMobileTaskDTO,
} from "@/api/employeeMobileTasks";
import {
  buildEmployeeMobileOrderBlueprintPath,
  fetchEmployeeMobileOrderBlueprint,
  type EmployeeMobileOrderBlueprintDTO,
  type EmployeeMobileOrderBlueprintTask,
} from "@/api/employeeMobileOrderBlueprint";
import EmployeeMobileTaskActionBar from "@/components/workos/employee-mobile/EmployeeMobileTaskActionBar";
import EmployeeMobileOrderPipelineView from "@/components/workos/employee-mobile/EmployeeMobileOrderPipelineView";
import EmployeeMobileTaskClarificationPanel from "@/components/workos/employee-mobile/EmployeeMobileTaskClarificationPanel";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { formatDateTime } from "@/lib/employeeMobileUiHelpers";
import {
  documentSourceLabel,
  documentTypeLabel,
  normalizeTaskDocuments,
  taskInstructionsText,
} from "@/lib/employeeMobileTaskDocuments";
import {
  formatOrderLabel,
  isActiveEmployeeMobileTask,
  type OrderTaskSummary,
} from "@/lib/employeeMobileTaskSummary";
import {
  EMPLOYEE_MOBILE_TASK_VIEW_DESCRIPTIONS,
  EMPLOYEE_MOBILE_TASK_VIEW_LABELS,
  filterTasksForView,
  listOrdersForTasksView,
  parseEmployeeMobileTaskView,
  summarizeEmployeeMobileTaskCounts,
  buildEmployeeMobileTasksPath,
  filterTodayActionableTasks,
  type EmployeeMobileTaskView,
} from "@/lib/employeeMobileTaskViews";
import {
  emChipClass,
  emMobileScrollPadClass,
  emStickyFooterClass,
  emSurface,
  emTaskTabClass,
} from "@/lib/employeeMobileDesignTokens";
import { pickPrimaryOrderId } from "@/lib/employeeMobilePipelineEligibility";
import {
  buildTaskCardExplanation,
  collectBeforeYouStartLines,
  formatInstructionsAsLines,
  getOperationalStatusLabel,
  getOperationalTaskBucket,
  sortTasksOperational,
} from "@/lib/employeeMobileShopFloorPresentation";
import { cn } from "@/lib/utils";

const PRIMARY_VISIBLE_TABS: EmployeeMobileTaskView[] = ["today", "all", "pipeline"];

const SECONDARY_TABS: EmployeeMobileTaskView[] = [
  "assigned",
  "in_progress",
  "blocked",
  "done",
  "orders",
  "installations",
  "upcoming",
];

const COMPACT_TASK_VIEWS: EmployeeMobileTaskView[] = [
  "today",
  "all",
  "pipeline",
  "blocked",
  "upcoming",
];

function TaskMetaRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs uppercase tracking-wide text-slate-500">{label}</span>
      <span className="text-sm text-slate-200">{value}</span>
    </div>
  );
}

function operationalChipTone(
  task: EmployeeMobileTaskDTO,
): "neutral" | "active" | "ready" | "warning" {
  if (task.status === "blocked") return "warning";
  if (task.status === "in_progress") return "active";
  if (task.status === "assigned" && task.is_startable === true) return "ready";
  return "neutral";
}

function OperationalTaskRow({
  task,
  blueprintTask,
  onSelect,
}: {
  task: EmployeeMobileTaskDTO;
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null;
  onSelect: (task: EmployeeMobileTaskDTO) => void;
}) {
  const bucket = getOperationalTaskBucket(task);
  const statusLabel = getOperationalStatusLabel(task, blueprintTask);
  const explanation =
    bucket === "waiting" ? null : buildTaskCardExplanation(task, blueprintTask);

  return (
    <button
      type="button"
      onClick={() => onSelect(task)}
      className={cn(
        "flex w-full items-center gap-3 px-3.5 py-3 text-left transition-colors min-h-[52px] hover:bg-[#111827]/50",
        emSurface.row,
      )}
      data-testid={`employee-mobile-task-card-${task.task_id}`}
    >
      <span className="min-w-0 flex-1">
        <span className="flex items-start justify-between gap-2">
          <span className="text-base font-medium text-slate-100 leading-snug line-clamp-2">
            {task.title || task.task_id}
          </span>
          <span className={emChipClass(operationalChipTone(task))}>{statusLabel}</span>
        </span>
        {explanation ? (
          <span className="mt-0.5 block text-xs text-slate-500 line-clamp-1">{explanation}</span>
        ) : null}
      </span>
      <ChevronRight className="w-4 h-4 shrink-0 text-slate-600" aria-hidden />
    </button>
  );
}

function TaskListCard({
  task,
  onSelect,
}: {
  task: EmployeeMobileTaskDTO;
  onSelect: (task: EmployeeMobileTaskDTO) => void;
}) {
  const subtitle = [
    task.order_code || `Comandă #${task.order_id}`,
    task.client,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <button
      type="button"
      onClick={() => onSelect(task)}
      className="w-full text-left rounded-xl border border-[#243044] bg-[#0A1020]/80 px-3.5 py-3.5 space-y-2 hover:border-slate-500 transition-colors min-h-[44px]"
      data-testid={`employee-mobile-task-card-${task.task_id}`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-lg font-semibold text-slate-100 leading-snug">{task.title || task.task_id}</p>
        <StatusBadge domain="executionTask" status={task.status} />
      </div>
      {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
      {task.estimated_time_minutes != null && (
        <p className="text-[10px] text-slate-500">{task.estimated_time_minutes} min estimate</p>
      )}
      {(task.description || task.instructions) && (
        <p className="text-[11px] text-slate-400 line-clamp-2">
          {task.description || task.instructions}
        </p>
      )}
      {task.documents && task.documents.length > 0 && (
        <p className="inline-flex items-center gap-1 text-[10px] text-blue-300">
          <FileText className="w-3 h-3" aria-hidden />
          Documente disponibile
        </p>
      )}
    </button>
  );
}

function OrderSummaryCard({
  order,
  onOpen,
}: {
  order: OrderTaskSummary;
  onOpen: (orderId: number) => void;
}) {
  const assigned = order.tasks.filter((task) => task.status === "assigned").length;
  const inProgress = order.tasks.filter((task) => task.status === "in_progress").length;
  const blocked = order.tasks.filter((task) => task.status === "blocked").length;

  return (
    <div
      className="rounded-xl border border-[#243044] bg-[#0A1020]/80 px-3.5 py-3 space-y-2"
      data-testid={`employee-mobile-tasks-order-${order.orderId}`}
    >
      <button
        type="button"
        onClick={() => onOpen(order.orderId)}
        className="w-full text-left hover:opacity-90 transition-opacity"
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2 min-w-0">
            <Package className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" aria-hidden />
            <div className="min-w-0">
              <p className="text-[13px] font-semibold text-slate-100">{formatOrderLabel(order)}</p>
              {order.product && <p className="text-[11px] text-slate-400 truncate">{order.product}</p>}
              <p className="text-[10px] text-slate-500 mt-1">
                {assigned} de făcut · {inProgress} în lucru · {blocked} blocate · {order.doneCount}{" "}
                finalizate
              </p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" aria-hidden />
        </div>
      </button>
      <Link
        to={buildEmployeeMobileOrderBlueprintPath(order.orderId)}
        className="inline-flex text-[11px] font-medium text-blue-300 hover:text-blue-200"
        data-testid={`employee-mobile-order-blueprint-link-${order.orderId}`}
      >
        Vezi tot fluxul comenzii
      </Link>
    </div>
  );
}

function TaskDetailBlock({
  title,
  testId,
  children,
}: {
  title: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <section className={cn("py-3", emSurface.row)} data-testid={testId}>
      <h3 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
        {title}
      </h3>
      {children}
    </section>
  );
}

function taskLiveStatusMessage(task: EmployeeMobileTaskDTO): string | null {
  if (task.status === "done" && task.completed_at) {
    return `Finalizat la ${formatDateTime(task.completed_at)}`;
  }
  if (task.status === "blocked") {
    if (task.blocked_reason) {
      return `Blocat: ${task.blocked_reason}`;
    }
    if (task.blocked_at) {
      return `Blocat la ${formatDateTime(task.blocked_at)}`;
    }
  }
  if (task.status === "in_progress" && task.started_at) {
    return `În lucru de la ${formatDateTime(task.started_at)}`;
  }
  return null;
}

function TaskDetailPanel({
  task,
  blueprintTask,
  onBack,
  onActionComplete,
}: {
  task: EmployeeMobileTaskDTO;
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null;
  onBack: () => void;
  onActionComplete: () => Promise<void>;
}) {
  const instructions = taskInstructionsText(task);
  const instructionLines = instructions ? formatInstructionsAsLines(instructions) : [];
  const documents = normalizeTaskDocuments(task.documents);
  const liveStatus = taskLiveStatusMessage(task);
  const beforeYouStart = collectBeforeYouStartLines({ task, blueprintTask });
  const materialHints = blueprintTask?.material_hints ?? [];

  const statusLabel = getOperationalStatusLabel(task, blueprintTask);

  return (
    <div className={cn("space-y-3", emMobileScrollPadClass)} data-testid="employee-mobile-task-detail">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-[12px] text-slate-400 hover:text-slate-200 min-h-[44px]"
        data-testid="employee-mobile-task-detail-back"
      >
        <ArrowLeft className="w-3.5 h-3.5" aria-hidden />
        Înapoi la listă
      </button>

      <div className="space-y-1.5">
        <div className="flex items-start justify-between gap-2">
          <h2 className="text-lg font-semibold text-slate-100 leading-snug">
            {task.title || task.task_id}
          </h2>
          <span className={emChipClass(operationalChipTone(task))}>{statusLabel}</span>
        </div>
        <p className="text-xs text-slate-500">
          {task.order_code || `Comandă #${task.order_id}`}
          {task.client ? ` · ${task.client}` : ""}
        </p>
        {liveStatus ? (
          <p
            className="text-[11px] text-slate-500"
            data-testid="employee-mobile-task-live-status"
          >
            {liveStatus}
          </p>
        ) : null}
      </div>

      <div
        className={cn(emSurface.panel, "px-3.5 overflow-hidden")}
        data-testid="employee-mobile-task-detail-body"
      >
      {beforeYouStart.length > 0 ? (
        <TaskDetailBlock title="Înainte să începi" testId="employee-mobile-task-before-start">
          <ul className="space-y-1.5 text-sm text-slate-300 leading-relaxed">
            {beforeYouStart.map((line) => (
              <li key={line} className="flex gap-2">
                <span className="text-emerald-400 shrink-0">•</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </TaskDetailBlock>
      ) : null}

      {instructionLines.length > 0 ? (
        <TaskDetailBlock title="Instrucțiuni" testId="employee-mobile-task-instructions">
          {instructionLines.length > 1 ? (
            <ol
              className="list-decimal pl-5 space-y-1 text-sm text-slate-300 leading-relaxed"
              data-testid="employee-mobile-task-instructions-content"
            >
              {instructionLines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ol>
          ) : (
            <p
              className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed"
              data-testid="employee-mobile-task-instructions-content"
            >
              {instructionLines[0]}
            </p>
          )}
        </TaskDetailBlock>
      ) : null}

      {materialHints.length > 0 ? (
        <TaskDetailBlock title="Materiale de verificat" testId="employee-mobile-task-materials">
          <ul className="space-y-1.5 text-sm text-slate-300">
            {materialHints.map((hint) => (
              <li key={`${hint.name}-${hint.label}`} className="flex gap-2">
                <span className="text-slate-500 shrink-0">•</span>
                <span>
                  {hint.name}
                  {hint.label ? ` · ${hint.label}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </TaskDetailBlock>
      ) : null}

      {documents.length > 0 ? (
        <TaskDetailBlock title="Documente utile" testId="employee-mobile-task-documents">
          <ul className="space-y-2" data-testid="employee-mobile-task-documents-list">
            {documents.map((doc) => (
              <li
                key={`${task.task_id}-${doc.id}`}
                className="flex items-start justify-between gap-2"
                data-testid={`employee-mobile-task-document-${doc.id}`}
              >
                <div className="min-w-0 flex-1">
                  <span className="inline-flex items-center gap-1.5 text-sm text-slate-200">
                    <FileText className="w-3.5 h-3.5 shrink-0 text-slate-400" aria-hidden />
                    <span className="truncate">{doc.name}</span>
                  </span>
                  <p className="text-xs text-slate-500 mt-0.5 pl-5">
                    {documentTypeLabel(doc.type)} · {documentSourceLabel(doc.source)}
                  </p>
                </div>
                {doc.url ? (
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 text-sm font-medium text-blue-300 hover:text-blue-200 min-h-[44px] inline-flex items-center"
                    data-testid={`employee-mobile-task-document-open-${doc.id}`}
                  >
                    Deschide
                  </a>
                ) : (
                  <span
                    className="shrink-0 text-xs text-slate-600 max-w-[8rem] text-right leading-snug"
                    data-testid={`employee-mobile-task-document-meta-${doc.id}`}
                  >
                    Disponibil în sistem, fără link mobil momentan
                  </span>
                )}
              </li>
            ))}
          </ul>
        </TaskDetailBlock>
      ) : null}

      {(task.process_type || task.machine_type || task.estimated_time_minutes != null) && (
        <details
          className={cn("py-3", emSurface.row)}
          data-testid="employee-mobile-task-technical-details"
        >
          <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-slate-500 min-h-[44px] flex items-center">
            Detalii tehnice
          </summary>
          <div className="mt-2 space-y-3">
            <TaskMetaRow label="Proces" value={task.process_type} />
            <TaskMetaRow label="Mașină" value={task.machine_type} />
            <TaskMetaRow
              label="Estimare"
              value={
                task.estimated_time_minutes != null ? `${task.estimated_time_minutes} min` : null
              }
            />
            <TaskMetaRow label="Cod task" value={task.task_id} />
          </div>
        </details>
      )}

      </div>

      <div className={emStickyFooterClass}>
        <EmployeeMobileTaskClarificationPanel
          task={task}
          onSubmitted={onActionComplete}
          variant="footer"
        />
        <EmployeeMobileTaskActionBar
          task={task}
          onActionComplete={onActionComplete}
          layout="embedded"
        />
      </div>
    </div>
  );
}

export default function EmployeeMobileTasksPanel() {
  const [searchParams, setSearchParams] = useSearchParams();
  const view = parseEmployeeMobileTaskView(searchParams.get("view"));
  const [showMoreTabs, setShowMoreTabs] = useState(false);
  const orderIdRaw = searchParams.get("orderId");
  const selectedOrderId =
    orderIdRaw && Number.isFinite(Number(orderIdRaw)) ? Number(orderIdRaw) : null;

  const [tasks, setTasks] = useState<EmployeeMobileTaskDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<EmployeeMobileTaskDTO | null>(null);
  const [blueprint, setBlueprint] = useState<EmployeeMobileOrderBlueprintDTO | null>(null);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listEmployeeMobileTasks();
      setTasks(rows);
      setSelected((current) => {
        if (!current) return null;
        return (
          rows.find(
            (row) => row.task_id === current.task_id && row.order_id === current.order_id,
          ) ?? null
        );
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nu am putut încărca taskurile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  useEffect(() => {
    if (PRIMARY_VISIBLE_TABS.includes(view) || view === "blocked" || view === "upcoming") {
      setShowMoreTabs(false);
    }
  }, [view]);

  const taskIdParam = searchParams.get("taskId");

  useEffect(() => {
    if (!taskIdParam || loading || tasks.length === 0) return;
    const orderIdParam = searchParams.get("orderId");
    const orderId = orderIdParam ? Number(orderIdParam) : null;
    const match = tasks.find(
      (row) =>
        row.task_id === taskIdParam &&
        (orderId == null || Number.isNaN(orderId) || row.order_id === orderId),
    );
    if (match) setSelected(match);
  }, [taskIdParam, loading, tasks, searchParams]);

  const primaryOrderId = useMemo(() => pickPrimaryOrderId(tasks), [tasks]);

  const loadPipeline = useCallback(async (orderId: number) => {
    setPipelineLoading(true);
    setPipelineError(null);
    try {
      const data = await fetchEmployeeMobileOrderBlueprint(orderId);
      setBlueprint(Array.isArray(data.tasks) ? data : null);
    } catch (err) {
      setPipelineError(err instanceof Error ? err.message : "Nu am putut încărca pipeline-ul.");
      setBlueprint(null);
    } finally {
      setPipelineLoading(false);
    }
  }, []);

  useEffect(() => {
    if (primaryOrderId == null) return;
    if (view === "pipeline" || view === "today" || view === "all" || selected) {
      void loadPipeline(primaryOrderId);
    }
  }, [view, primaryOrderId, loadPipeline, selected]);

  const refreshTasksAndPipeline = useCallback(async () => {
    await loadTasks();
    if (primaryOrderId != null) {
      await loadPipeline(primaryOrderId);
    }
  }, [loadTasks, loadPipeline, primaryOrderId]);

  const counts = useMemo(() => summarizeEmployeeMobileTaskCounts(tasks), [tasks]);
  const orders = useMemo(() => listOrdersForTasksView(tasks), [tasks]);
  const visibleTasks = useMemo(
    () => filterTasksForView(tasks, view, selectedOrderId),
    [tasks, view, selectedOrderId],
  );

  const blueprintById = useMemo(
    () => new Map((blueprint?.tasks ?? []).map((task) => [task.task_id, task])),
    [blueprint?.tasks],
  );

  const listTasks = useMemo(() => {
    if (view === "today") {
      return sortTasksOperational(filterTodayActionableTasks(tasks));
    }
    if (view === "all") {
      return sortTasksOperational(visibleTasks.filter(isActiveEmployeeMobileTask));
    }
    return visibleTasks;
  }, [view, visibleTasks, tasks]);

  const useOperationalCards = view === "all" || view === "today";

  const selectedBlueprintTask =
    selected != null ? blueprintById.get(selected.task_id) ?? null : null;

  const openOrder = (orderId: number) => {
    setSelected(null);
    setSearchParams(() => {
      const params = new URLSearchParams();
      params.set("view", "orders");
      params.set("orderId", String(orderId));
      return params;
    });
  };

  const clearOrderFilter = () => {
    setSelected(null);
    setSearchParams(() => {
      const params = new URLSearchParams();
      params.set("view", "orders");
      return params;
    });
  };

  const clearTaskSelection = () => {
    setSelected(null);
    setSearchParams((current) => {
      const params = new URLSearchParams(current);
      params.delete("taskId");
      if (params.get("orderId") && view !== "orders") {
        params.delete("orderId");
      }
      return params;
    });
  };

  if (selected) {
    return (
      <TaskDetailPanel
        task={selected}
        blueprintTask={selectedBlueprintTask}
        onBack={clearTaskSelection}
        onActionComplete={loadTasks}
      />
    );
  }

  const showOrdersList = view === "orders" && selectedOrderId == null;
  const emptyMessage =
    view === "today"
      ? "Niciun task de acționat acum."
      : view === "installations"
      ? "Nu ai montaje programate vizibile momentan."
      : view === "upcoming"
        ? "Niciun alt task pregătit pentru începere."
        : view === "blocked"
          ? "Nu ai blocaje active."
          : view === "orders" && selectedOrderId != null
            ? "Niciun task în această comandă."
            : "Nu ai taskuri în această categorie.";

  const isPipelineView = view === "pipeline" && selectedOrderId == null;
  const showCompactHeader =
    COMPACT_TASK_VIEWS.includes(view) && selectedOrderId == null;

  return (
    <div className="space-y-4" data-testid="employee-mobile-section-tasks">
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">Taskurile mele</h2>
            {!showCompactHeader ? (
              <p className="text-sm text-slate-400 mt-0.5">
                Începe, blochează sau finalizează taskurile atribuite.
              </p>
            ) : null}
          </div>
          <Link
            to="/employee-app"
            className="text-[11px] text-slate-500 hover:text-slate-300 shrink-0 min-h-[44px] inline-flex items-center"
            data-testid="employee-mobile-tasks-back-home"
          >
            Acasă
          </Link>
        </div>

        {!loading && !error && !showCompactHeader && (
          <p className="text-xs text-slate-500" data-testid="employee-mobile-tasks-summary">
            {counts.active} active · {counts.inProgress} în lucru · {counts.blocked} blocate ·{" "}
            {counts.done} finalizate
          </p>
        )}
      </div>

      {loading && (
        <EmployeeMobileLoadingState message="Se încarcă taskurile…" testId="employee-mobile-tasks-loading" />
      )}
      {!loading && error && (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-tasks-error" />
      )}

      {!loading && !error && tasks.length === 0 && (
        <EmployeeMobileEmptyState
          message="Nu ai taskuri atribuite momentan."
          hint="Când o comandă intră în producție și îți este atribuit un task, îl vei vedea aici."
          testId="employee-mobile-tasks-empty"
        />
      )}

      <div
        className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
        data-testid="employee-mobile-tasks-tabs"
      >
        {PRIMARY_VISIBLE_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => {
              setSelected(null);
              setShowMoreTabs(false);
              setSearchParams(() => {
                const params = new URLSearchParams();
                if (tab !== "today") params.set("view", tab);
                return params;
              });
            }}
            className={emTaskTabClass(view === tab && selectedOrderId == null)}
            data-testid={`employee-mobile-tasks-tab-${tab}`}
          >
            {EMPLOYEE_MOBILE_TASK_VIEW_LABELS[tab]}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setShowMoreTabs((current) => !current)}
          className={cn(
            "shrink-0 rounded-full px-4 py-2.5 min-h-[44px] text-sm font-medium border transition-colors",
            showMoreTabs || SECONDARY_TABS.includes(view)
              ? "bg-slate-800/60 border-slate-600/40 text-slate-200"
              : "bg-[#0A1020]/60 border-[#243044] text-slate-400 hover:text-slate-200",
          )}
          data-testid="employee-mobile-tasks-tab-more"
        >
          Mai multe
        </button>
      </div>

      {showMoreTabs && (
        <div
          className="flex flex-wrap gap-2"
          data-testid="employee-mobile-tasks-tabs-secondary"
        >
          {SECONDARY_TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => {
                setSelected(null);
                setSearchParams(() => {
                  const params = new URLSearchParams();
                  params.set("view", tab);
                  return params;
                });
              }}
              className={emTaskTabClass(view === tab && selectedOrderId == null)}
              data-testid={`employee-mobile-tasks-tab-${tab}`}
            >
              {EMPLOYEE_MOBILE_TASK_VIEW_LABELS[tab]}
            </button>
          ))}
        </div>
      )}

      {!showCompactHeader && (
        <p className="text-[11px] text-slate-500" data-testid="employee-mobile-tasks-view-description">
          {EMPLOYEE_MOBILE_TASK_VIEW_DESCRIPTIONS[view]}
        </p>
      )}

      {view === "orders" && selectedOrderId != null && (
        <button
          type="button"
          onClick={clearOrderFilter}
          className="inline-flex items-center gap-1 text-[11px] text-blue-300 hover:text-blue-200"
          data-testid="employee-mobile-tasks-order-back"
        >
          <ArrowLeft className="w-3.5 h-3.5" aria-hidden />
          Înapoi la comenzi
        </button>
      )}

      {!loading && !error && tasks.length > 0 && showOrdersList && (
        <div className="space-y-2" data-testid="employee-mobile-tasks-orders-list">
          {orders.length === 0 ? (
            <EmployeeMobileEmptyState
              message="Nicio comandă activă cu taskuri atribuite ție."
              testId="employee-mobile-tasks-orders-empty"
            />
          ) : (
            orders.map((order) => (
              <OrderSummaryCard key={order.orderId} order={order} onOpen={openOrder} />
            ))
          )}
        </div>
      )}

      {!loading &&
        !error &&
        tasks.length > 0 &&
        view !== "pipeline" &&
        !showOrdersList &&
        (view === "today" ? listTasks.length === 0 : visibleTasks.length === 0) && (
        <EmployeeMobileEmptyState message={emptyMessage} testId="employee-mobile-tasks-view-empty" />
      )}

      {!loading &&
        !error &&
        view === "pipeline" &&
        tasks.length > 0 &&
        primaryOrderId != null &&
        pipelineLoading &&
        !blueprint && (
          <EmployeeMobileLoadingState
            message="Se încarcă fluxul comenzii…"
            testId="employee-mobile-pipeline-loading"
          />
        )}

      {!loading &&
        !error &&
        view === "pipeline" &&
        tasks.length > 0 &&
        primaryOrderId != null &&
        pipelineError &&
        !blueprint && (
          <EmployeeMobileErrorState
            message={pipelineError}
            testId="employee-mobile-pipeline-error"
          />
        )}

      {!loading &&
        !error &&
        view === "pipeline" &&
        blueprint &&
        primaryOrderId != null && (
          <EmployeeMobileOrderPipelineView
            blueprint={blueprint}
            personalTasks={tasks.filter((task) => task.order_id === primaryOrderId)}
            onOpenTask={setSelected}
            onActionComplete={refreshTasksAndPipeline}
            showBlueprintLink
            listHeading="Tot fluxul comenzii"
            collapseDefault
          />
        )}

      {!loading && !error && view !== "pipeline" && !showOrdersList && listTasks.length > 0 && (
        <div className={cn(emSurface.panel, "overflow-hidden")} data-testid="employee-mobile-tasks-list">
          {listTasks.map((task) =>
            useOperationalCards ? (
              <OperationalTaskRow
                key={`${task.order_id}-${task.task_id}`}
                task={task}
                blueprintTask={blueprintById.get(task.task_id) ?? null}
                onSelect={setSelected}
              />
            ) : (
              <TaskListCard
                key={`${task.order_id}-${task.task_id}`}
                task={task}
                onSelect={setSelected}
              />
            ),
          )}
        </div>
      )}
    </div>
  );
}
