import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileTruthTaskNested } from "@/lib/employeeMobileV2TaskTruth";
import {
  resolveTaskComponentLine,
  resolveTaskDisplayTitle,
  resolveTaskOperationLine,
} from "@/lib/employeeMobileV2TaskTruth";
import { emV2Surface } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

function DetailRow({ label, value, testId }: { label: string; value: string; testId?: string }) {
  if (!value.trim()) return null;
  return (
    <div className="flex justify-between gap-3 text-sm" data-testid={testId}>
      <dt className="text-slate-500 shrink-0">{label}</dt>
      <dd className="font-medium text-slate-200 text-right break-words">{value}</dd>
    </div>
  );
}

export default function EmployeeMobileV2TaskTruthPanels({ task }: { task: EmployeeMobileTaskDTO }) {
  const title = resolveTaskDisplayTitle(task);
  const component = resolveTaskComponentLine(task);
  const operation = resolveTaskOperationLine(task);
  const orderLabel = task.order_code || `Comandă #${task.order_id}`;
  const readinessLabel = task.readiness_label?.trim() || "—";
  const blockingTasks = task.blocking_tasks ?? [];
  const productionBlocked = Boolean(task.production_release_blocked);
  const productionSummary =
    task.production_blocker_summary?.trim() ||
    (productionBlocked ? "Necesită rezolvare de către manager" : null);

  return (
    <div className="mt-4 space-y-3" data-testid="employee-mobile-v2-task-truth-panels">
      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-identity">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">Identitate</p>
        <dl className="space-y-1.5">
          <DetailRow label="Task" value={title} testId="employee-mobile-v2-detail-task-label" />
          <DetailRow label="Componentă" value={component ?? "—"} testId="employee-mobile-v2-detail-component" />
          <DetailRow label="Operație" value={operation ?? "—"} testId="employee-mobile-v2-detail-operation" />
          <DetailRow label="Comandă" value={orderLabel} testId="employee-mobile-v2-detail-order" />
        </dl>
        <details className="mt-3 text-[11px] text-slate-600">
          <summary className="cursor-pointer">ID diagnostic</summary>
          <p className="mt-1 font-mono break-all">{task.task_id}</p>
        </details>
      </section>

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-state">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">Stare</p>
        <dl className="space-y-1.5">
          <DetailRow label="Status" value={task.status} />
          <DetailRow
            label="Atribuire"
            value={
              task.is_assigned_to_current_employee
                ? "Atribuit ție"
                : task.is_available_for_claim
                  ? "Disponibil de preluat"
                  : "Neatribuit"
            }
          />
          <DetailRow
            label="Poți începe"
            value={task.is_startable ? "Da" : "Nu"}
            testId="employee-mobile-v2-detail-startable"
          />
          <DetailRow
            label="Poți prelua"
            value={task.can_claim || task.claimable ? "Da" : "Nu"}
            testId="employee-mobile-v2-detail-claimable"
          />
        </dl>
      </section>

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-readiness">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">Pregătire</p>
        <p className="text-sm font-medium text-slate-200" data-testid="employee-mobile-v2-detail-readiness-label">
          {readinessLabel}
        </p>
        {task.material_warning ? (
          <p className="mt-2 text-[13px] text-amber-200/90">{task.material_warning}</p>
        ) : null}
        {task.dependency_warning ? (
          <p className="mt-2 text-[13px] text-amber-200/90">{task.dependency_warning}</p>
        ) : null}
      </section>

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-production">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">Producție</p>
        {productionBlocked ? (
          <>
            <p className="text-sm font-medium text-rose-300">Producție blocată</p>
            {productionSummary ? (
              <p className="mt-2 text-[13px] text-slate-400 leading-snug">{productionSummary}</p>
            ) : null}
            <p className="mt-2 text-[12px] text-slate-500">Necesită rezolvare de către manager (desktop).</p>
          </>
        ) : (
          <p className="text-sm text-emerald-300/90">Producție permisă</p>
        )}
      </section>

      {blockingTasks.length > 0 ? (
        <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-dependencies">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">Dependențe</p>
          <ul className="space-y-1 text-sm text-slate-300">
            {blockingTasks.map((blocker) => (
              <li key={blocker.task_id} className="break-words">
                {blocker.name || blocker.task_id}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

export function flatTaskToTruthNested(task: EmployeeMobileTaskDTO): EmployeeMobileTruthTaskNested {
  return {
    identity: {
      task_id: task.task_id,
      deterministic_task_key: task.deterministic_task_key,
      display_label: task.display_label || task.title || task.task_id,
      component_label: task.component_label,
      component_role: task.component_role,
      operation_label: task.operation_label || task.process_type,
      operation_code: task.operation_label || task.process_type,
      logo_segment_label: task.logo_segment_label,
      identity_source: task.identity_source,
      identity_classification: task.identity_classification,
    },
    assignment: {
      assigned_employee_id: task.assigned_employee_id,
      assigned_employee_name: task.employee_name,
      is_assigned_to_current_employee: Boolean(task.is_assigned_to_current_employee),
      is_available_for_claim: Boolean(task.is_available_for_claim),
      can_claim: Boolean(task.can_claim ?? task.claimable),
      assignment_source: task.assignment_source,
    },
    readiness: {
      is_startable: Boolean(task.is_startable),
      readiness_label: task.readiness_label,
      readiness_status: task.readiness_status,
      readiness_reasons: task.readiness_reasons as Array<Record<string, unknown>> | undefined,
      blocking_task_ids: task.blocking_task_ids,
      blocking_tasks: task.blocking_tasks,
      material_warning: task.material_warning,
      dependency_warning: task.dependency_warning,
      production_release_blocked: Boolean(task.production_release_blocked),
      production_blocker_summary: task.production_blocker_summary,
      can_start: Boolean(task.can_start),
      can_complete: Boolean(task.can_complete),
    },
    order_id: task.order_id,
    order_code: task.order_code,
    client_label: task.client,
    execution_plan_id: task.execution_plan_id,
    plan_sequence: task.plan_sequence,
    status: task.status,
    started_at: task.started_at,
    completed_at: task.completed_at,
    blocked_at: task.blocked_at,
    blocked_reason: task.blocked_reason,
    access_mode: task.access_mode,
    preview_only: task.preview_only,
  };
}

export function buildTruthResponseFromSections(
  assigned: EmployeeMobileTaskDTO[],
  available: EmployeeMobileTaskDTO[],
) {
  const assignedNested = assigned.map((task) =>
    flatTaskToTruthNested({
      ...task,
      is_assigned_to_current_employee: true,
      is_available_for_claim: false,
    }),
  );
  const availableNested = available.map((task) =>
    flatTaskToTruthNested({
      ...task,
      is_assigned_to_current_employee: false,
      is_available_for_claim: true,
    }),
  );
  const tasks = [...assignedNested, ...availableNested];
  return {
    contract_version: "employee_mobile_task_truth/v1",
    employee_id: 4,
    employee_display_name: "Angajat Test",
    generated_at: "2026-07-15T00:00:00Z",
    legacy_mode: false,
    tasks,
    summary: {
      total_tasks: tasks.length,
      assigned_count: assigned.length,
      available_count: available.length,
      startable_count: available.filter((t) => t.is_startable).length,
      blocked_count: [...assigned, ...available].filter((t) => t.production_release_blocked).length,
    },
    capabilities: { can_claim_available: true },
  };
}
