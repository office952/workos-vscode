import { Link } from "react-router-dom";
import type { ActiveMachineRunByTask } from "@/api/machineRuns";
import { MACHINE_RUN_STATUS_LABEL } from "@/lib/machineRunUi";

/**
 * Compact contextual link only — no lifecycle controls.
 * Render nothing when membership is absent (no "Fără MachineRun" noise).
 */
export function MachineRunContextChip({
  membership,
  testId,
}: {
  membership: ActiveMachineRunByTask | null | undefined;
  testId?: string;
}) {
  if (!membership) return null;

  const statusLabel = MACHINE_RUN_STATUS_LABEL[membership.status] ?? membership.status;
  const machine =
    membership.machine_code?.trim() ||
    membership.machine_name?.trim() ||
    null;

  return (
    <div
      className="inline-flex max-w-full flex-wrap items-center gap-x-2 gap-y-0.5 rounded border border-wo-border bg-wo-surface-inset px-2 py-1 text-[11px]"
      data-testid={testId ?? `machine-run-context-chip-${membership.machine_run_id}`}
    >
      <span className="font-semibold text-wo-text-primary">
        Rulare utilaj MR-{membership.machine_run_id}
      </span>
      <span className="text-wo-text-muted">
        {statusLabel}
        {machine ? ` · ${machine}` : ""}
      </span>
      <Link
        to={`/execution/machine-runs/${membership.machine_run_id}`}
        className="font-medium text-wo-info underline-offset-2 hover:underline"
        data-testid={`machine-run-context-open-${membership.machine_run_id}`}
      >
        Deschide
      </Link>
    </div>
  );
}
