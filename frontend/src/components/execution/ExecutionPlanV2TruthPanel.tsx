import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, FileSearch, ShieldAlert } from "lucide-react";
import type {
  ExecutionPlanV2MaterializationAuditResponse,
  ExecutionPlanV2PreviewResponse,
} from "@/api/execution";
import { ExecutionPlanStatesStrip } from "@/components/execution/ExecutionPlanStatesStrip";
import {
  countMissingMinutes,
  countMissingWorkcenters,
  deriveOrphanOperations,
  hasOperationalTasksInEnvelope,
  planLifecycleLabel,
} from "@/components/execution/executionPlanV2Readiness";
import { EXECUTION_PLAN_LABEL } from "@/features/product-system/productTemplateModulesVocabulary";
import { AuditOnlyNotice, OwnerGoNotice } from "@/components/workos/design-system";

interface ExecutionPlanV2TruthPanelProps {
  preview: ExecutionPlanV2PreviewResponse;
  audit: ExecutionPlanV2MaterializationAuditResponse | null;
  auditError: string | null;
  loading: boolean;
}

function toneForStatus(status: string): string {
  if (status.includes("blocked")) {
    return "bg-red-900/40 text-red-300 border-red-700";
  }
  if (status.includes("partial") || status.includes("warning")) {
    return "bg-amber-900/40 text-amber-300 border-amber-700";
  }
  return "bg-emerald-900/40 text-emerald-300 border-emerald-700";
}

function warningBadgeLabel(code: string): string {
  if (code === "PLANNING_MINUTES_SOURCE_REQUIRED") {
    return "MISSING_ESTIMATED_MINUTES";
  }
  if (code === "READINESS_GATE_RULES_EXCLUDED_FROM_V2_PREVIEW") {
    return "ORPHAN_NON_OPERATIONAL";
  }
  if (code.includes("WORKCENTER")) {
    return "MISSING_WORKCENTER";
  }
  if (code.includes("DEPENDENC") || code.includes("DAG")) {
    return "DEPENDENCY_REVIEW_REQUIRED";
  }
  if (code.includes("DUPLICATE")) {
    return "DUPLICATE_OPERATION_RISK";
  }
  return code;
}

export function ExecutionPlanV2TruthPanel({
  preview,
  audit,
  auditError,
  loading,
}: ExecutionPlanV2TruthPanelProps) {
  const [tasksExpanded, setTasksExpanded] = useState(true);
  const [opsExpanded, setOpsExpanded] = useState(false);
  const [auditExpanded, setAuditExpanded] = useState(true);

  const operationalPresent = hasOperationalTasksInEnvelope(audit);
  const orphans = useMemo(
    () => deriveOrphanOperations(preview.planned_operations, preview.planned_tasks),
    [preview.planned_operations, preview.planned_tasks],
  );
  const missingWc = countMissingWorkcenters(preview.planned_tasks);
  const missingMinutes = countMissingMinutes(preview.planned_tasks);
  const dependencyCount =
    preview.dependencies?.length ??
    preview.planned_tasks.reduce((n, task) => n + (task.depends_on_task_keys?.length ?? 0), 0);
  const lifecycle = planLifecycleLabel({
    hasPreview: true,
    audit,
    persistStatus: preview.persist_status,
  });
  const materializationBadge = operationalPresent
    ? "MATERIALIZED_IN_ENVELOPE · SESSIONS_FROZEN"
    : lifecycle.materializationLabel;

  return (
    <section
      className="bg-wo-surface-raised border border-wo-border-strong rounded-lg"
      data-testid="execution-plan-v2-truth-panel"
    >
      <header className="flex items-center justify-between px-4 py-3 border-b border-wo-border-strong">
        <div className="flex items-center gap-2">
          <FileSearch className="w-4 h-4 text-cyan-400" />
          <h2 className="text-[13px] font-bold text-foreground uppercase tracking-wide">
            {EXECUTION_PLAN_LABEL}
          </h2>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <span
            className={`inline-block px-2.5 py-0.5 text-[11px] font-bold rounded border ${toneForStatus(preview.status)}`}
            data-testid="execution-plan-v2-preview-status"
          >
            {preview.status}
          </span>
          <span
            className="inline-block px-2 py-0.5 text-[10px] rounded border bg-amber-900/30 text-amber-200 border-amber-800/50"
            data-testid="execution-plan-v2-draft-badge"
          >
            {operationalPresent ? "AUDIT_ONLY" : "DRAFT"}
          </span>
          <span
            className="inline-block px-2 py-0.5 text-[10px] rounded border bg-muted text-muted-foreground border-border"
            data-testid="execution-plan-v2-not-materialized-badge"
          >
            {materializationBadge}
          </span>
        </div>
      </header>

      <div className="p-4 space-y-4">
        <AuditOnlyNotice
          compact
          detail="Previzualizare read-only · planned_tasks ≠ taskuri de atelier"
        />
        <div
          className="rounded-md border border-cyan-800/40 bg-cyan-950/20 px-3 py-2 text-[12px] text-cyan-100"
          data-testid="execution-plan-v2-lifecycle-banner"
        >
          <p className="font-semibold">{lifecycle.draftLabel}</p>
          <p className="mt-1 text-[11px] text-cyan-100/80">{lifecycle.nextStepLabel}</p>
        </div>

        <ExecutionPlanStatesStrip
          hasPreview
          hasDraftPlan={Boolean(preview.planned_tasks.length) || audit?.execution_plan_id != null}
          hasOperationalTasks={operationalPresent}
          operationalBlocked={!operationalPresent}
        />
        <OwnerGoNotice
          detail="Lansarea în producție este blocată (DEC-009=A). Nu există acțiune Materializează / Asignează / Pornește pe această suprafață."
          compact
        />

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
          <div className="bg-card rounded px-2.5 py-2 border border-border">
            <p className="text-muted-foreground uppercase text-[9px] tracking-wide">order_id</p>
            <p className="mt-1 text-foreground font-mono" data-testid="execution-plan-v2-order-id">
              {preview.order_id ?? "unknown"}
            </p>
          </div>
          <div className="bg-card rounded px-2.5 py-2 border border-border">
            <p className="text-muted-foreground uppercase text-[9px] tracking-wide">execution_plan_id</p>
            <p className="mt-1 text-foreground font-mono" data-testid="execution-plan-v2-plan-id">
              {audit?.execution_plan_id ?? "not_persisted"}
            </p>
          </div>
          <div className="bg-card rounded px-2.5 py-2 border border-border">
            <p className="text-muted-foreground uppercase text-[9px] tracking-wide">planned_tasks</p>
            <p className="mt-1 text-cyan-300 font-bold" data-testid="execution-plan-v2-task-count">
              {preview.planned_tasks.length}
            </p>
          </div>
          <div className="bg-card rounded px-2.5 py-2 border border-border">
            <p className="text-muted-foreground uppercase text-[9px] tracking-wide">planned_operations</p>
            <p className="mt-1 text-cyan-300 font-bold" data-testid="execution-plan-v2-op-count">
              {preview.planned_operations.length}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5" data-testid="execution-plan-v2-gap-badges">
          <span className="inline-block px-2 py-0.5 text-[10px] rounded border bg-muted text-muted-foreground border-border">
            persist: {preview.persist_status ?? (audit?.execution_plan_id != null ? "persisted_draft" : "not_persisted")}
          </span>
          <span className="inline-block px-2 py-0.5 text-[10px] rounded border bg-muted text-muted-foreground border-border">
            dependencies: {dependencyCount}
          </span>
          {orphans.length > 0 ? (
            <span className="inline-block px-2 py-0.5 text-[10px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/50">
              ORPHAN_NON_OPERATIONAL · {orphans.length}
            </span>
          ) : null}
          {missingWc > 0 ? (
            <span className="inline-block px-2 py-0.5 text-[10px] rounded border bg-red-900/30 text-red-300 border-red-800/50">
              MISSING_WORKCENTER · {missingWc}
            </span>
          ) : null}
          {missingMinutes > 0 ? (
            <span className="inline-block px-2 py-0.5 text-[10px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/50">
              MISSING_ESTIMATED_MINUTES · {missingMinutes}
            </span>
          ) : null}
          {audit?.guards?.post_materialize_allowed === false ? (
            <span className="inline-block px-2 py-0.5 text-[10px] rounded border bg-red-900/30 text-red-300 border-red-800/50">
              MATERIALIZATION · CLOSED
            </span>
          ) : null}
        </div>

        {(preview.warnings.length > 0 || preview.blockers.length > 0) && (
          <div className="space-y-2">
            {preview.warnings.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {preview.warnings.map((warning) => (
                  <span
                    key={warning}
                    className="inline-flex items-center px-2 py-0.5 text-[10px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/50"
                  >
                    {warningBadgeLabel(warning)}
                  </span>
                ))}
              </div>
            )}
            {preview.blockers.length > 0 && (
              <div className="bg-red-900/10 border border-red-800/40 rounded-md px-3 py-2 text-[11px] text-red-200">
                <div className="font-semibold mb-1">Blockers</div>
                <div className="flex flex-wrap gap-1.5">
                  {preview.blockers.map((blocker) => (
                    <span key={blocker} className="font-mono text-[10px] px-2 py-0.5 rounded bg-red-900/40 border border-red-800/50">
                      {blocker}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="border border-wo-border-strong rounded-md overflow-hidden">
          <button
            type="button"
            onClick={() => setTasksExpanded((prev) => !prev)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            {tasksExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">Planned Tasks ({preview.planned_tasks.length})</span>
          </button>
          {tasksExpanded && (
            <div className="border-t border-wo-border-strong overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead className="bg-card text-muted-foreground uppercase text-[9px] tracking-wide">
                  <tr>
                    <th className="text-left px-3 py-1.5">Task</th>
                    <th className="text-left px-3 py-1.5">Op source</th>
                    <th className="text-left px-3 py-1.5">Workcenter</th>
                    <th className="text-right px-3 py-1.5">Minutes</th>
                    <th className="text-left px-3 py-1.5">Depends</th>
                    <th className="text-left px-3 py-1.5">Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.planned_tasks.map((task) => (
                    <tr key={task.task_key} className="border-t border-border hover:bg-card/40 align-top">
                      <td className="px-3 py-2">
                        <div className="font-mono text-foreground">{task.task_key}</div>
                        <div className="text-muted-foreground">{task.label}</div>
                        <div className="text-[10px] text-muted-foreground">{task.canonical_task_type}</div>
                      </td>
                      <td className="px-3 py-2 font-mono text-[10px] text-muted-foreground">
                        {task.source_operation_code ?? "unknown"}
                      </td>
                      <td className="px-3 py-2">
                        {task.machine_requirement?.workcenter ? (
                          <span className="font-mono text-muted-foreground text-[10px]">{task.machine_requirement.workcenter}</span>
                        ) : (
                          <span className="inline-block px-1.5 py-0.5 text-[10px] rounded border bg-red-900/30 text-red-300 border-red-800/50">
                            MISSING_WORKCENTER
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {task.estimated_minutes === null || task.estimated_minutes === undefined ? (
                          <span className="inline-block px-1.5 py-0.5 text-[10px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/50">
                            MISSING_ESTIMATED_MINUTES
                          </span>
                        ) : (
                          <span className="text-foreground">{task.estimated_minutes.toFixed(1)}</span>
                        )}
                      </td>
                      <td className="px-3 py-2 font-mono text-[10px] text-muted-foreground">
                        {(task.depends_on_task_keys?.length ?? 0) > 0
                          ? task.depends_on_task_keys?.join(", ")
                          : "none"}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap gap-1">
                          {task.warnings.length > 0 ? task.warnings.map((warning) => (
                            <span key={warning} className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/40">
                              {warningBadgeLabel(warning)}
                            </span>
                          )) : <span className="text-muted-foreground">none</span>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {orphans.length > 0 ? (
          <div
            className="rounded-md border border-amber-800/40 bg-amber-950/20 px-3 py-2 text-[11px] text-amber-100"
            data-testid="execution-plan-v2-orphan-ops"
          >
            <p className="font-semibold">Operații fără planned_task (orphan)</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {orphans.map((op) => (
                <span key={op.operation_code} className="font-mono text-[10px] px-2 py-0.5 rounded border border-amber-800/50 bg-amber-900/30">
                  {op.operation_code}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        <div className="border border-wo-border-strong rounded-md overflow-hidden">
          <button
            type="button"
            onClick={() => setOpsExpanded((prev) => !prev)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            {opsExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">Planned Operations ({preview.planned_operations.length})</span>
          </button>
          {opsExpanded && (
            <div className="border-t border-wo-border-strong overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead className="bg-card text-muted-foreground uppercase text-[9px] tracking-wide">
                  <tr>
                    <th className="text-left px-3 py-1.5">Operation</th>
                    <th className="text-left px-3 py-1.5">Template</th>
                    <th className="text-left px-3 py-1.5">Workcenter</th>
                    <th className="text-left px-3 py-1.5">Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.planned_operations.map((op) => (
                    <tr key={`${op.operation_code}-${op.sequence_index ?? "na"}`} className="border-t border-border hover:bg-card/40">
                      <td className="px-3 py-2">
                        <div className="font-mono text-foreground">{op.operation_code}</div>
                        <div className="text-muted-foreground">{op.label ?? "unknown"}</div>
                      </td>
                      <td className="px-3 py-2 font-mono text-[10px] text-muted-foreground">{op.source_template_code ?? "unknown"}</td>
                      <td className="px-3 py-2">
                        {op.workcenter ? (
                          <span className="font-mono text-[10px] text-muted-foreground">{op.workcenter}</span>
                        ) : (
                          <span className="inline-block px-1.5 py-0.5 text-[10px] rounded border bg-muted text-muted-foreground border-border">
                            unknown
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap gap-1">
                          {!op.priced && (
                            <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-muted text-muted-foreground border-border">
                              non-priced
                            </span>
                          )}
                          {op.workcenter == null && (
                            <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/40">
                              MISSING_WORKCENTER
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="border border-wo-border-strong rounded-md overflow-hidden">
          <button
            type="button"
            onClick={() => setAuditExpanded((prev) => !prev)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            {auditExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">Materialization Audit</span>
          </button>
          {auditExpanded && (
            <div className="border-t border-wo-border-strong p-3 space-y-3">
              {loading && !audit ? (
                <p className="text-[11px] text-muted-foreground" data-testid="execution-plan-v2-audit-loading">
                  Se încarcă auditul V2...
                </p>
              ) : auditError ? (
                <div
                  className="flex items-start gap-2 bg-amber-900/20 border border-amber-800/60 rounded-md px-3 py-2"
                  data-testid="execution-plan-v2-audit-error"
                >
                  <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div className="text-[12px] text-amber-300">
                    <p className="font-semibold">Audit indisponibil</p>
                    <p className="text-[11px] text-amber-300/70 mt-0.5">{auditError}</p>
                  </div>
                </div>
              ) : audit ? (
                <>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
                    <div className="bg-card rounded px-2.5 py-2 border border-border">
                      <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Dry run</p>
                      <p className="mt-1 text-muted-foreground font-semibold">{audit.dry_run_status}</p>
                    </div>
                    <div className="bg-card rounded px-2.5 py-2 border border-border">
                      <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Candidates</p>
                      <p className="mt-1 text-cyan-300 font-bold">{audit.materializable_task_candidates.length}</p>
                    </div>
                    <div className="bg-card rounded px-2.5 py-2 border border-border">
                      <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Non-operational</p>
                      <p className="mt-1 text-muted-foreground font-bold">{audit.non_operational_items?.length ?? 0}</p>
                    </div>
                    <div className="bg-card rounded px-2.5 py-2 border border-border">
                      <p className="text-muted-foreground uppercase text-[9px] tracking-wide">Ops in envelope</p>
                      <p className="mt-1 text-muted-foreground font-semibold">{audit.operational_tasks_in_envelope_count}</p>
                    </div>
                  </div>

                  {(audit.blockers.length > 0 || audit.warnings.length > 0) && (
                    <div className="space-y-2">
                      {audit.blockers.length > 0 && (
                        <div className="bg-red-900/10 border border-red-800/40 rounded-md px-3 py-2">
                          <div className="text-[11px] font-semibold text-red-200 mb-1">Audit blockers</div>
                          <div className="flex flex-wrap gap-1.5">
                            {audit.blockers.map((blocker) => (
                              <span key={blocker} className="font-mono text-[10px] px-2 py-0.5 rounded bg-red-900/40 border border-red-800/50 text-red-300">
                                {blocker}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {audit.warnings.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {audit.warnings.map((warning) => (
                            <span key={warning} className="inline-block px-2 py-0.5 text-[10px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/50">
                              {warning}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="space-y-2">
                    <div className="text-[10px] text-muted-foreground uppercase tracking-wide">Materializable candidates</div>
                    <div className="space-y-2">
                      {audit.materializable_task_candidates.map((candidate) => (
                        <div key={candidate.task_key} className="bg-card border border-border rounded-md px-3 py-2 text-[11px]">
                          <div className="flex items-center justify-between gap-2">
                            <div>
                              <div className="font-mono text-foreground">{candidate.task_key}</div>
                              <div className="text-muted-foreground">{candidate.label ?? candidate.canonical_task_type ?? "unknown"}</div>
                            </div>
                            <div className="flex flex-wrap gap-1 justify-end">
                              <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-muted text-muted-foreground border-border">
                                {candidate.operational_status_preview}
                              </span>
                              {candidate.estimated_minutes === null && (
                                <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/40">
                                  MISSING_ESTIMATED_MINUTES
                                </span>
                              )}
                            </div>
                          </div>
                          {candidate.warnings.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {candidate.warnings.map((warning) => (
                                <span key={warning} className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/40">
                                  {warning}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {(audit.non_operational_items?.length ?? 0) > 0 && (
                    <div className="space-y-2">
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wide">Non-operational items</div>
                      <div className="space-y-2">
                        {audit.non_operational_items?.map((item) => (
                          <div key={`${item.task_name}-${item.task_type}`} className="bg-card border border-border rounded-md px-3 py-2 text-[11px]">
                            <div className="font-mono text-foreground">{item.task_name}</div>
                            <div className="text-muted-foreground">{item.task_type}</div>
                            <div className="text-muted-foreground mt-1">{item.reason}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-[11px] text-muted-foreground">Auditul V2 nu este disponibil pentru această comandă.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
