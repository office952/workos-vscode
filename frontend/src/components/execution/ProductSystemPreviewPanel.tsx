/**
 * S30 — ProductSystem Execution Preview Panel (read-only).
 *
 * Displays operations, task requirements, and trace from the preview endpoint.
 * Read-only: no mutations, no forms, no POST/PUT/PATCH/DELETE.
 */

import { useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  Layers,
  Database,
} from "lucide-react";
import type { ProductSystemExecutionPreview } from "@/types/preview.types";

interface ProductSystemPreviewPanelProps {
  preview: ProductSystemExecutionPreview;
}

export function ProductSystemPreviewPanel({ preview }: ProductSystemPreviewPanelProps) {
  const [opsExpanded, setOpsExpanded] = useState(true);
  const [tasksExpanded, setTasksExpanded] = useState(false);
  const [traceExpanded, setTraceExpanded] = useState(false);

  return (
    <section className="bg-wo-surface-raised border border-wo-border-strong rounded-lg">
      <header className="flex items-center justify-between px-4 py-3 border-b border-wo-border-strong">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400" />
          <h2 className="text-[13px] font-bold text-slate-200 uppercase tracking-wide">
            ProductSystem Preview
          </h2>
        </div>
        <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full font-mono">
          {preview.template_code}
          {preview.template_version ? ` v${preview.template_version}` : ""}
        </span>
      </header>

      <div className="p-4 space-y-4">
        {/* Summary stats */}
        <div className="grid grid-cols-4 gap-2 text-[11px]">
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Operații</p>
            <p className="mt-1 text-purple-300 font-bold">
              {preview.generated_operations.length}
            </p>
          </div>
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Task Req.</p>
            <p className="mt-1 text-purple-300 font-bold">
              {preview.generated_task_requirements.length}
            </p>
          </div>
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Linkage BLK</p>
            <p className={`mt-1 font-bold ${preview.trace_source.linkage_blockers_count > 0 ? "text-red-300" : "text-emerald-300"}`}>
              {preview.trace_source.linkage_blockers_count}
            </p>
          </div>
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Linkage WRN</p>
            <p className={`mt-1 font-bold ${preview.trace_source.linkage_warnings_count > 0 ? "text-amber-300" : "text-slate-400"}`}>
              {preview.trace_source.linkage_warnings_count}
            </p>
          </div>
        </div>

        {/* Operations table (collapsible) */}
        <div className="border border-wo-border-strong rounded-md">
          <button
            type="button"
            onClick={() => setOpsExpanded(!opsExpanded)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
          >
            {opsExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">
              Operații ({preview.generated_operations.length})
            </span>
          </button>
          {opsExpanded && preview.generated_operations.length > 0 && (
            <div className="border-t border-wo-border-strong overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead className="bg-wo-surface-raised text-slate-400 uppercase text-[9px] tracking-wide">
                  <tr>
                    <th className="text-left px-3 py-1.5">#</th>
                    <th className="text-left px-3 py-1.5">Operation ID</th>
                    <th className="text-left px-3 py-1.5">Task Type</th>
                    <th className="text-left px-3 py-1.5">Component</th>
                    <th className="text-left px-3 py-1.5">Depends On</th>
                    <th className="text-left px-3 py-1.5">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.generated_operations.map((op) => (
                    <tr key={op.operation_id} className="border-t border-[#1F2A44] hover:bg-wo-surface-raised/40">
                      <td className="px-3 py-1.5 text-slate-400 tabular-nums">{op.sequence_index}</td>
                      <td className="px-3 py-1.5 font-mono text-slate-200">{op.operation_id}</td>
                      <td className="px-3 py-1.5 text-slate-300">{op.task_type}</td>
                      <td className="px-3 py-1.5 text-slate-400">{op.component_id ?? "—"}</td>
                      <td className="px-3 py-1.5 text-slate-400 font-mono text-[10px]">
                        {op.depends_on_operation_ids.length > 0
                          ? op.depends_on_operation_ids.join(", ")
                          : "—"}
                      </td>
                      <td className="px-3 py-1.5 text-slate-400 max-w-[200px] truncate">
                        {op.description ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Task Requirements table (collapsible) */}
        <div className="border border-wo-border-strong rounded-md">
          <button
            type="button"
            onClick={() => setTasksExpanded(!tasksExpanded)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
          >
            {tasksExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-medium uppercase tracking-wide">
              Task Requirements ({preview.generated_task_requirements.length})
            </span>
          </button>
          {tasksExpanded && preview.generated_task_requirements.length > 0 && (
            <div className="border-t border-wo-border-strong overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead className="bg-wo-surface-raised text-slate-400 uppercase text-[9px] tracking-wide">
                  <tr>
                    <th className="text-left px-3 py-1.5">Task Template</th>
                    <th className="text-left px-3 py-1.5">Source Op.</th>
                    <th className="text-left px-3 py-1.5">Type</th>
                    <th className="text-left px-3 py-1.5">Skills</th>
                    <th className="text-left px-3 py-1.5">Workcenter</th>
                    <th className="text-left px-3 py-1.5">Machine</th>
                    <th className="text-right px-3 py-1.5">Materials</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.generated_task_requirements.map((tr) => (
                    <tr key={tr.task_template_id} className="border-t border-[#1F2A44] hover:bg-wo-surface-raised/40">
                      <td className="px-3 py-1.5 font-mono text-slate-200">{tr.task_template_id}</td>
                      <td className="px-3 py-1.5 font-mono text-slate-400 text-[10px]">{tr.source_operation_id}</td>
                      <td className="px-3 py-1.5 text-slate-300">{tr.task_type}</td>
                      <td className="px-3 py-1.5">
                        <div className="flex flex-wrap gap-1">
                          {tr.required_skill_ids.length > 0
                            ? tr.required_skill_ids.map((s) => (
                                <span key={s} className="inline-block px-1 py-0.5 text-[9px] rounded bg-blue-900/40 text-blue-300 border border-blue-800/40">
                                  {s}
                                </span>
                              ))
                            : <span className="text-slate-500">—</span>}
                        </div>
                      </td>
                      <td className="px-3 py-1.5 text-slate-400 font-mono text-[10px]">
                        {tr.required_workcenter_id ?? "—"}
                      </td>
                      <td className="px-3 py-1.5 text-slate-400 font-mono text-[10px]">
                        {tr.required_machine_type ?? "—"}
                      </td>
                      <td className="px-3 py-1.5 text-right">
                        <span className="inline-block px-1.5 py-0.5 text-[10px] rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {tr.material_requirements.length}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Missing links from preview */}
        {preview.missing_links.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] text-amber-400 uppercase tracking-wide font-bold">
              Missing Links ({preview.missing_links.length})
            </p>
            {preview.missing_links.map((ml, idx) => (
              <div
                key={`${ml.task_template_id}-${ml.field}-${idx}`}
                className="bg-amber-900/10 border border-amber-800/30 rounded-md px-3 py-2 text-[11px] space-y-0.5"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-amber-300">{ml.field}</span>
                  <span className="text-slate-500">pe</span>
                  <span className="font-mono text-slate-300">{ml.task_template_id}</span>
                </div>
                <p className="text-slate-400">{ml.reason}</p>
                <p className="text-[10px] text-slate-500">
                  Disponibil azi: {ml.available_today ? "Da" : "Nu"}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Preview trace source (collapsible) */}
        <div className="border border-wo-border-strong rounded-md">
          <button
            type="button"
            onClick={() => setTraceExpanded(!traceExpanded)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
          >
            {traceExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <Database className="w-3 h-3" />
            <span className="font-medium uppercase tracking-wide">Preview Trace</span>
          </button>
          {traceExpanded && (
            <div className="px-3 pb-3 space-y-2 text-[11px] border-t border-wo-border-strong pt-2">
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-wo-surface-inset rounded px-2 py-1.5 border border-[#1F2A44]">
                  <p className="text-slate-500 text-[9px] uppercase">Template Resolved</p>
                  <p className="text-slate-300 font-mono text-[10px]">
                    {preview.trace_source.template_resolved_at || "—"}
                  </p>
                </div>
                <div className="bg-wo-surface-inset rounded px-2 py-1.5 border border-[#1F2A44]">
                  <p className="text-slate-500 text-[9px] uppercase">Linkage Validation</p>
                  <p className="text-slate-300">
                    {preview.trace_source.linkage_validation_run ? "✅ Executată" : "❌ Nu"}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-slate-500 text-[9px] uppercase mb-1">Registre consultate</p>
                <div className="flex flex-wrap gap-1.5">
                  {preview.trace_source.registries_consulted.map((name) => (
                    <span
                      key={name}
                      className="inline-block px-1.5 py-0.5 text-[10px] font-mono rounded bg-emerald-900/30 text-emerald-300 border border-emerald-800/40"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              </div>
              {preview.trace_source.registries_unavailable.length > 0 && (
                <div>
                  <p className="text-slate-500 text-[9px] uppercase mb-1">Registre indisponibile</p>
                  <div className="flex flex-wrap gap-1.5">
                    {preview.trace_source.registries_unavailable.map((name) => (
                      <span
                        key={name}
                        className="inline-block px-1.5 py-0.5 text-[10px] font-mono rounded bg-amber-900/30 text-amber-300 border border-amber-800/40"
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}