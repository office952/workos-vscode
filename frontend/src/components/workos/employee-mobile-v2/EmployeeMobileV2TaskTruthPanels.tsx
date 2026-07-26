import { useMemo } from "react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileTruthTaskNested } from "@/lib/employeeMobileV2TaskTruth";
import EmployeeMobileV2BlockerBadges from "@/components/workos/employee-mobile-v2/EmployeeMobileV2BlockerBadges";
import {
  buildEmployeeMobileV2BlockerPresentation,
  categorySectionLabel,
  type EmV2BlockerCategory,
} from "@/lib/employeeMobileV2BlockerPresentation";
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

function BlockerCategorySection({
  category,
  items,
}: {
  category: EmV2BlockerCategory;
  items: Array<{ label: string; detail?: string; code?: string }>;
}) {
  if (items.length === 0) return null;
  return (
    <ul className="mt-2 space-y-1.5 text-sm text-slate-300">
      {items.map((item, index) => (
        <li key={`${item.code || item.label}-${index}`} className="break-words">
          <span className="font-medium text-slate-200">{item.label}</span>
          {item.detail && item.detail !== item.label ? (
            <span className="block text-[13px] text-slate-500 mt-0.5">{item.detail}</span>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export default function EmployeeMobileV2TaskTruthPanels({ task }: { task: EmployeeMobileTaskDTO }) {
  const blockerPresentation = useMemo(
    () => buildEmployeeMobileV2BlockerPresentation(task),
    [task],
  );

  const title = resolveTaskDisplayTitle(task);
  const component = resolveTaskComponentLine(task);
  const operation = resolveTaskOperationLine(task);
  const orderLabel = task.order_code || `Comandă #${task.order_id}`;

  const assignmentLabel = task.is_assigned_to_current_employee
    ? "Atribuit ție"
    : task.is_available_for_claim
      ? task.can_claim || task.claimable
        ? "Disponibil de preluat"
        : "Vizibil, dar nu poate fi preluat"
      : task.employee_name
        ? `Atribuit lui ${task.employee_name}`
        : "Neatribuit";

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
        <EmployeeMobileV2BlockerBadges
          presentation={blockerPresentation}
          testIdPrefix="employee-mobile-v2-detail"
        />
      </section>

      <section
        className={cn(emV2Surface.panel, "p-4")}
        data-testid="employee-mobile-v2-detail-can-start"
      >
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
          Poate începe?
        </p>
        <p
          className={cn(
            "text-sm font-medium",
            blockerPresentation.canStartFromBackend ? "text-emerald-300" : "text-rose-300",
          )}
          data-testid="employee-mobile-v2-detail-startable"
        >
          {blockerPresentation.canStartFromBackend ? "Da" : "Nu"}
        </p>
        <p className="mt-2 text-[13px] text-slate-400 leading-snug">
          {blockerPresentation.canStartExplanation}
        </p>
        {blockerPresentation.activeSessionLabel ? (
          <p
            className="mt-2 text-[13px] text-sky-300/90"
            data-testid="employee-mobile-v2-detail-active-session"
          >
            {blockerPresentation.activeSessionLabel}
          </p>
        ) : null}
      </section>

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-production">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
          {categorySectionLabel("productie")}
        </p>
        {blockerPresentation.showProductionBadge ? (
          <>
            <p className="text-sm font-medium text-rose-300">Producție blocată</p>
            {task.production_blocker_summary ? (
              <p className="mt-2 text-[13px] text-slate-400 leading-snug">
                {task.production_blocker_summary}
              </p>
            ) : null}
            <BlockerCategorySection
              category="productie"
              items={blockerPresentation.categories.productie}
            />
            <p
              className="mt-3 text-[12px] text-amber-200/90 leading-snug"
              data-testid="employee-mobile-v2-detail-manager-escalation"
            >
              {blockerPresentation.managerEscalationText}
            </p>
          </>
        ) : (
          <p className="text-sm text-emerald-300/90">Producție permisă</p>
        )}
      </section>

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-readiness">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
          {categorySectionLabel("pregatire")}
        </p>
        <p className="text-sm font-medium text-slate-200" data-testid="employee-mobile-v2-detail-readiness-label">
          {task.readiness_label?.trim() || blockerPresentation.primaryLabel}
        </p>
        <BlockerCategorySection
          category="pregatire"
          items={blockerPresentation.categories.pregatire}
        />
        {(task.blocking_tasks ?? []).length > 0 ? (
          <div className="mt-3" data-testid="employee-mobile-v2-detail-dependencies">
            <p className="text-[11px] uppercase tracking-wide text-slate-600 mb-1">Predecesori</p>
            <ul className="space-y-1 text-sm text-slate-300">
              {task.blocking_tasks?.map((blocker) => (
                <li key={blocker.task_id} className="break-words">
                  {blocker.name || blocker.task_id}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-materials">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
          {categorySectionLabel("materiale")}
        </p>
        {blockerPresentation.categories.materiale.length > 0 ? (
          <BlockerCategorySection
            category="materiale"
            items={blockerPresentation.categories.materiale}
          />
        ) : (
          <p className="text-sm text-slate-500">Fără blocaje materiale raportate.</p>
        )}
      </section>

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-allocation">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
          {categorySectionLabel("alocare")}
        </p>
        <dl className="space-y-1.5">
          <DetailRow label="Stare" value={assignmentLabel} />
          <DetailRow
            label="Poți prelua"
            value={task.can_claim || task.claimable ? "Da" : "Nu"}
            testId="employee-mobile-v2-detail-claimable"
          />
        </dl>
        <BlockerCategorySection
          category="alocare"
          items={blockerPresentation.categories.alocare}
        />
      </section>

      {blockerPresentation.categories.stare_task.length > 0 ? (
        <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-state">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
            {categorySectionLabel("stare_task")}
          </p>
          <BlockerCategorySection
            category="stare_task"
            items={blockerPresentation.categories.stare_task}
          />
        </section>
      ) : null}

      <section className={cn(emV2Surface.panel, "p-4")} data-testid="employee-mobile-v2-detail-diagnostic">
        <details>
          <summary className="cursor-pointer text-[12px] font-semibold uppercase tracking-wide text-slate-500">
            Diagnostic
          </summary>
          <ul className="mt-2 space-y-1 font-mono text-[11px] text-slate-500 break-all">
            {blockerPresentation.diagnosticCodes.map((code) => (
              <li key={code}>{code}</li>
            ))}
            <li>task_id:{task.task_id}</li>
            <li>status:{task.status}</li>
          </ul>
        </details>
      </section>
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
      can_start_from_available: Boolean(task.can_start_from_available),
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
