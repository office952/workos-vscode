import type { IntakeV6TaskGenerationDryRunResponse } from "@/lib/intakeV6/intakeV6Api";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";
import IntakeV6CncOperationPreviewSection from "./IntakeV6CncOperationPreviewSection";
import IntakeV6EdgeCantOperationPreviewSection from "./IntakeV6EdgeCantOperationPreviewSection";

function readSummaryCount(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}

export default function IntakeV6TaskGenerationDryRunPanel({
  dryRun,
  loading,
}: {
  dryRun: IntakeV6TaskGenerationDryRunResponse | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className={v6.card} data-testid="intake-v6-task-generation-dry-run">
        <p className="text-[12px] text-slate-400">Calculez task generation dry-run…</p>
      </div>
    );
  }
  if (!dryRun) {
    return (
      <div className={v6.card} data-testid="intake-v6-task-generation-dry-run">
        <p className="text-[12px] text-slate-400">Dry-run indisponibil.</p>
      </div>
    );
  }

  const summary = dryRun.summary ?? {};
  const alignment = (summary.template_operation_alignment ?? {}) as {
    status?: string;
    aligned_count?: number;
    partial_count?: number;
    missing_count?: number;
    provisional_critical_tasks?: string[];
  };
  const templateBacked =
    typeof summary.template_backed_count === "number"
      ? summary.template_backed_count
      : dryRun.task_candidates.filter((t) => t.template_backed && !t.provisional).length;
  const provisional =
    typeof summary.provisional_count === "number"
      ? summary.provisional_count
      : dryRun.task_candidates.filter((t) => t.provisional).length;
  const blocked = dryRun.blockers.filter((b) => b.severity === "blocking").length;
  const compatMappingUsed =
    dryRun.compat_cnc_mapping_used ?? dryRun.legacy_cnc_mapping_used;
  const taskCandidatesCount = readSummaryCount(summary.task_candidates_count);
  const dependencyEdgesCount = readSummaryCount(summary.dependency_edges_count);

  return (
    <div className={v6.card} data-testid="intake-v6-task-generation-dry-run">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-[12px] font-bold uppercase tracking-wide">Task generation dry-run</h3>
          <p className="mt-1 text-[10px] text-slate-500">
            Nu creează taskuri reale. Nu scrie în producție. Nu consumă stoc.
          </p>
        </div>
        <AtomsBadge tone="muted">{dryRun.dry_run_mode}</AtomsBadge>
      </div>

      <dl className="mb-4 grid grid-cols-2 gap-3 text-[11px] sm:grid-cols-5">
        <div>
          <dt className="text-slate-500">Task candidates</dt>
          <dd data-testid="intake-v6-dry-run-candidates-count">
            {taskCandidatesCount ?? dryRun.task_candidates.length}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Template-backed</dt>
          <dd data-testid="intake-v6-dry-run-template-backed-count">{templateBacked}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Provisional</dt>
          <dd data-testid="intake-v6-dry-run-provisional-count">{provisional}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Dependencies</dt>
          <dd data-testid="intake-v6-dry-run-deps-count">
            {dependencyEdgesCount ?? dryRun.dependency_graph.length}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Blockers</dt>
          <dd data-testid="intake-v6-dry-run-blockers-count">{blocked}</dd>
        </div>
      </dl>

      {alignment.status ? (
        <div
          className="mb-4 rounded border border-wo-border-strong/60 px-3 py-2 text-[11px]"
          data-testid="intake-v6-dry-run-template-alignment"
        >
          <p className="font-semibold text-slate-300">
            Template operation alignment:{" "}
            <span className="text-wo-text-primary">{alignment.status}</span>
          </p>
          <p className="mt-1 text-slate-500">
            aligned {alignment.aligned_count ?? 0} · partial {alignment.partial_count ?? 0} · missing{" "}
            {alignment.missing_count ?? 0}
          </p>
          {(alignment.provisional_critical_tasks?.length ?? 0) > 0 ? (
            <p className="mt-1 text-amber-300">
              Critical provisional: {alignment.provisional_critical_tasks?.join(", ")}
            </p>
          ) : null}
        </div>
      ) : null}

      <IntakeV6CncOperationPreviewSection
        candidates={dryRun.cnc_operation_candidates ?? []}
        cncTaskSource={dryRun.cnc_task_source}
        compatMappingUsed={compatMappingUsed}
        testIdPrefix="intake-v6-dry-run-cnc"
      />

      <IntakeV6EdgeCantOperationPreviewSection
        candidates={dryRun.edge_cant_operation_candidates ?? []}
        edgeCantTaskSource={dryRun.edge_cant_task_source}
        testIdPrefix="intake-v6-dry-run-edge-cant"
      />

      {dryRun.task_candidates.length > 0 ? (
        <ul className="mb-4 space-y-1 text-[11px] text-slate-300">
          {dryRun.task_candidates
            .filter((task) => task.operation_group !== "cnc_cutting")
            .slice(0, 6)
            .map((task) => (
            <li key={task.task_key} className="border-b border-wo-border-strong/60 py-1">
              {task.title}
              {task.provisional ? (
                <span className="ml-2 text-[10px] text-amber-300">provisional</span>
              ) : null}
              {!task.template_backed ? (
                <span className="ml-2 text-[10px] text-amber-300">not template-backed</span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}

      {dryRun.blockers.length > 0 ? (
        <ul className="mb-3 space-y-1 text-[10px] text-red-300" data-testid="intake-v6-dry-run-blockers">
          {dryRun.blockers.slice(0, 6).map((item) => (
            <li key={`${item.code}-${item.source}`}>• {item.message}</li>
          ))}
        </ul>
      ) : null}

      {dryRun.warnings.length > 0 ? (
        <ul className="space-y-1 text-[10px] text-amber-200" data-testid="intake-v6-dry-run-warnings">
          {dryRun.warnings.slice(0, 4).map((item) => (
            <li key={`${item.code}-${item.source}`}>• {item.message}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}



