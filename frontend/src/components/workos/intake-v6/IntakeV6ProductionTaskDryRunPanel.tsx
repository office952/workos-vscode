import type { IntakeV6ProductionTaskDryRunResponse } from "@/lib/intakeV6/productionTaskDryRunContracts";
import {
  adaptBackingAbsentOperationLabel,
  formatTaskDryRunMaterialBreakdownStatus,
  INTAKE_V6_PREVIEW_ONLY_BANNER,
} from "@/lib/intakeV6/intakeV6OperatorUiDisplay";

interface IntakeV6ProductionTaskDryRunPanelProps {
  workspaceId: string | null;
  workspaceLoaded: boolean;
  productionTaskDryRun: IntakeV6ProductionTaskDryRunResponse | null;
  loading?: boolean;
  error?: string | null;
  backingMode?: string | null;
}

export default function IntakeV6ProductionTaskDryRunPanel({
  workspaceId,
  workspaceLoaded,
  productionTaskDryRun,
  loading = false,
  error = null,
  backingMode = null,
}: IntakeV6ProductionTaskDryRunPanelProps) {
  if (!workspaceLoaded || workspaceId == null) {
    return (
      <section
        className="rounded border border-slate-700 bg-slate-900/40 p-3"
        data-testid="intake-v6-production-task-dry-run-panel"
      >
        <p className="text-[11px] text-slate-500">Load a saved draft workspace first.</p>
      </section>
    );
  }

  const hasCncOperationRows = (productionTaskDryRun?.candidate_task_groups ?? []).some(
    (group) => group.group_key === "cnc_operation_rows",
  );
  const candidateTasksCount =
    productionTaskDryRun?.summary?.candidate_tasks_count ??
    productionTaskDryRun?.candidate_tasks?.length ??
    0;
  const visibleCandidateTasks = (productionTaskDryRun?.candidate_tasks ?? []).filter((task) => {
    if (!hasCncOperationRows) {
      return true;
    }
    if (task.group_key === "cnc_operation_rows") {
      return true;
    }
    if (task.seed_code === "face_and_backing_cnc_cut") {
      return false;
    }
    return true;
  });

  return (
    <section
      className="rounded border border-slate-700 bg-slate-900/40 p-3 space-y-3"
      data-testid="intake-v6-production-task-dry-run-panel"
    >
      <div>
        <p className="text-[12px] font-medium text-slate-200">Previzualizare generare taskuri</p>
        <p className="text-[11px] text-slate-400 mt-1" data-testid="intake-v6-task-dry-run-scope-copy">
          {INTAKE_V6_PREVIEW_ONLY_BANNER}
        </p>
      </div>

      {loading ? <p className="text-[11px] text-slate-500">Loading production task dry-run…</p> : null}
      {error ? (
        <p className="text-[11px] text-red-300" data-testid="intake-v6-task-dry-run-error">
          {error}
        </p>
      ) : null}

      {productionTaskDryRun ? (
        <>
          <p className="text-[11px] text-slate-400" data-testid="intake-v6-task-dry-run-material-breakdown">
            {formatTaskDryRunMaterialBreakdownStatus(productionTaskDryRun.material_breakdown_available)}
          </p>
          <p
            className="mb-2 text-[11px] text-slate-400"
            data-testid="intake-v6-task-dry-run-candidate-count"
            title="Număr tehnic din preview-ul de producție. Nu reprezintă piese, litere sau interioare."
          >
            Taskuri candidate dry-run: {candidateTasksCount}
          </p>
          <ul className="space-y-1 text-[11px] text-slate-300" data-testid="intake-v6-task-dry-run-list">
            {visibleCandidateTasks.slice(0, 10).map((task, index) => (
              <li key={task.candidate_task_id}>
                {index + 1}. {adaptBackingAbsentOperationLabel(task.title, backingMode)}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}



