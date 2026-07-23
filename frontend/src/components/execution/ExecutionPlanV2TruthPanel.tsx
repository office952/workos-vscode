import { useState } from "react";
import { ChevronDown, ChevronRight, FileSearch, ShieldAlert } from "lucide-react";
import type {
  ExecutionPlanV2MaterializationAuditResponse,
  ExecutionPlanV2PreviewResponse,
} from "@/api/execution";
import { ExecutionPlanStatesStrip } from "@/components/execution/ExecutionPlanStatesStrip";
import { EXECUTION_PLAN_LABEL } from "@/features/product-system/productTemplateModulesVocabulary";

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
    return "Planning minutes source required";
  }
  if (code === "READINESS_GATE_RULES_EXCLUDED_FROM_V2_PREVIEW") {
    return "Readiness gate excluded";
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

  return (
    <section className="bg-[#1A2236] border border-[#2A3548] rounded-lg">
      <header className="flex items-center justify-between px-4 py-3 border-b border-[#2A3548]">
        <div className="flex items-center gap-2">
          <FileSearch className="w-4 h-4 text-cyan-400" />
          <h2 className="text-[13px] font-bold text-slate-200 uppercase tracking-wide">
            {EXECUTION_PLAN_LABEL}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block px-2.5 py-0.5 text-[11px] font-bold rounded border ${toneForStatus(preview.status)}`}>
            {preview.status}
          </span>
          <span className="inline-block px-2 py-0.5 text-[10px] rounded border bg-slate-800 text-slate-300 border-slate-700">
            read-only
          </span>
        </div>
      </header>

      <div className="p-4 space-y-4">
        <ExecutionPlanStatesStrip
          hasPreview
          hasDraftPlan={Boolean(preview.planned_tasks.length)}
          hasOperationalTasks={false}
          operationalBlocked
        />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
          <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Draft Plan · tasks</p>
            <p className="mt-1 text-cyan-300 font-bold">{preview.planned_tasks.length}</p>
          </div>
          <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Preview · ops</p>
            <p className="mt-1 text-cyan-300 font-bold">{preview.planned_operations.length}</p>
          </div>
          <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Operational Plan</p>
            <p className="mt-1 text-slate-300 font-semibold">{audit?.materialization_status ?? "blocked"}</p>
          </div>
          <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Snapshot source</p>
            <p className="mt-1 text-slate-300 font-mono text-[10px]">{preview.source_snapshot_code ?? "—"}</p>
          </div>
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

        <div className="border border-[#2A3548] rounded-md overflow-hidden">
          <button
            type="button"
            onClick={() => setTasksExpanded((prev) => !prev)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
          >
            {tasksExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">Planned Tasks ({preview.planned_tasks.length})</span>
          </button>
          {tasksExpanded && (
            <div className="border-t border-[#2A3548] overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead className="bg-[#111827] text-slate-400 uppercase text-[9px] tracking-wide">
                  <tr>
                    <th className="text-left px-3 py-1.5">Task</th>
                    <th className="text-left px-3 py-1.5">Op source</th>
                    <th className="text-left px-3 py-1.5">Workcenter</th>
                    <th className="text-right px-3 py-1.5">Minutes</th>
                    <th className="text-left px-3 py-1.5">Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.planned_tasks.map((task) => (
                    <tr key={task.task_key} className="border-t border-[#1F2A44] hover:bg-[#111827]/40 align-top">
                      <td className="px-3 py-2">
                        <div className="font-mono text-slate-200">{task.task_key}</div>
                        <div className="text-slate-400">{task.label}</div>
                        <div className="text-[10px] text-slate-500">{task.canonical_task_type}</div>
                      </td>
                      <td className="px-3 py-2 font-mono text-[10px] text-slate-400">
                        {task.source_operation_code ?? "—"}
                      </td>
                      <td className="px-3 py-2">
                        {task.machine_requirement?.workcenter ? (
                          <span className="font-mono text-slate-300 text-[10px]">{task.machine_requirement.workcenter}</span>
                        ) : (
                          <span className="inline-block px-1.5 py-0.5 text-[10px] rounded border bg-red-900/30 text-red-300 border-red-800/50">
                            missing
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {task.estimated_minutes === null ? (
                          <span className="inline-block px-1.5 py-0.5 text-[10px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/50">
                            null
                          </span>
                        ) : (
                          <span className="text-slate-200">{task.estimated_minutes.toFixed(1)}</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap gap-1">
                          {task.warnings.length > 0 ? task.warnings.map((warning) => (
                            <span key={warning} className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/40">
                              {warningBadgeLabel(warning)}
                            </span>
                          )) : <span className="text-slate-500">—</span>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="border border-[#2A3548] rounded-md overflow-hidden">
          <button
            type="button"
            onClick={() => setOpsExpanded((prev) => !prev)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
          >
            {opsExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">Planned Operations ({preview.planned_operations.length})</span>
          </button>
          {opsExpanded && (
            <div className="border-t border-[#2A3548] overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead className="bg-[#111827] text-slate-400 uppercase text-[9px] tracking-wide">
                  <tr>
                    <th className="text-left px-3 py-1.5">Operation</th>
                    <th className="text-left px-3 py-1.5">Template</th>
                    <th className="text-left px-3 py-1.5">Workcenter</th>
                    <th className="text-left px-3 py-1.5">Flags</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.planned_operations.map((op) => (
                    <tr key={`${op.operation_code}-${op.sequence_index ?? "na"}`} className="border-t border-[#1F2A44] hover:bg-[#111827]/40">
                      <td className="px-3 py-2">
                        <div className="font-mono text-slate-200">{op.operation_code}</div>
                        <div className="text-slate-500">{op.label ?? "—"}</div>
                      </td>
                      <td className="px-3 py-2 font-mono text-[10px] text-slate-400">{op.source_template_code ?? "—"}</td>
                      <td className="px-3 py-2">
                        {op.workcenter ? (
                          <span className="font-mono text-[10px] text-slate-300">{op.workcenter}</span>
                        ) : (
                          <span className="inline-block px-1.5 py-0.5 text-[10px] rounded border bg-slate-800 text-slate-400 border-slate-700">
                            null
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap gap-1">
                          {!op.priced && (
                            <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-slate-800 text-slate-300 border-slate-700">
                              non-priced
                            </span>
                          )}
                          {op.workcenter === null && (
                            <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/40">
                              missing workcenter
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

        <div className="border border-[#2A3548] rounded-md overflow-hidden">
          <button
            type="button"
            onClick={() => setAuditExpanded((prev) => !prev)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
          >
            {auditExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">Materialization Audit</span>
          </button>
          {auditExpanded && (
            <div className="border-t border-[#2A3548] p-3 space-y-3">
              {loading && !audit ? (
                <p className="text-[11px] text-slate-500">Se încarcă auditul V2...</p>
              ) : auditError ? (
                <div className="flex items-start gap-2 bg-amber-900/20 border border-amber-800/60 rounded-md px-3 py-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div className="text-[12px] text-amber-300">
                    <p className="font-semibold">Audit indisponibil</p>
                    <p className="text-[11px] text-amber-300/70 mt-0.5">{auditError}</p>
                  </div>
                </div>
              ) : audit ? (
                <>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
                    <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                      <p className="text-slate-500 uppercase text-[9px] tracking-wide">Dry run</p>
                      <p className="mt-1 text-slate-300 font-semibold">{audit.dry_run_status}</p>
                    </div>
                    <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                      <p className="text-slate-500 uppercase text-[9px] tracking-wide">Candidates</p>
                      <p className="mt-1 text-cyan-300 font-bold">{audit.materializable_task_candidates.length}</p>
                    </div>
                    <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                      <p className="text-slate-500 uppercase text-[9px] tracking-wide">Non-operational</p>
                      <p className="mt-1 text-slate-300 font-bold">{audit.non_operational_items.length}</p>
                    </div>
                    <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                      <p className="text-slate-500 uppercase text-[9px] tracking-wide">Writes DB</p>
                      <p className="mt-1 text-slate-300 font-semibold">{audit.guards.writes_database ? "yes" : "no"}</p>
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
                    <div className="text-[10px] text-slate-500 uppercase tracking-wide">Materializable candidates</div>
                    <div className="space-y-2">
                      {audit.materializable_task_candidates.map((candidate) => (
                        <div key={candidate.task_key} className="bg-[#111827] border border-[#1F2A44] rounded-md px-3 py-2 text-[11px]">
                          <div className="flex items-center justify-between gap-2">
                            <div>
                              <div className="font-mono text-slate-200">{candidate.task_key}</div>
                              <div className="text-slate-400">{candidate.label ?? candidate.canonical_task_type ?? "—"}</div>
                            </div>
                            <div className="flex flex-wrap gap-1 justify-end">
                              <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-slate-800 text-slate-300 border-slate-700">
                                {candidate.operational_status_preview}
                              </span>
                              {candidate.estimated_minutes === null && (
                                <span className="inline-block px-1.5 py-0.5 text-[9px] rounded border bg-amber-900/30 text-amber-300 border-amber-800/40">
                                  null minutes
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

                  {audit.non_operational_items.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-[10px] text-slate-500 uppercase tracking-wide">Non-operational items</div>
                      <div className="space-y-2">
                        {audit.non_operational_items.map((item) => (
                          <div key={`${item.task_name}-${item.task_type}`} className="bg-[#111827] border border-[#1F2A44] rounded-md px-3 py-2 text-[11px]">
                            <div className="font-mono text-slate-200">{item.task_name}</div>
                            <div className="text-slate-400">{item.task_type}</div>
                            <div className="text-slate-500 mt-1">{item.reason}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-[11px] text-slate-500">Auditul V2 nu este disponibil pentru această comandă.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}