import type { IntakeV6ProductionHandoffPreviewResponse } from "@/lib/intakeV6/intakeV6Api";
import {
  formatIntakeV6QuantityBasisLabel,
} from "@/lib/intakeV6/intakeV6QuantityBasisLabels";
import {
  formatIntakeV6PricingQuantity,
  formatIntakeV6Quantity,
} from "@/lib/intakeV6/intakeV6QuantityDisplay";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";
import IntakeV6CncOperationPreviewSection from "./IntakeV6CncOperationPreviewSection";
import IntakeV6EdgeCantOperationPreviewSection from "./IntakeV6EdgeCantOperationPreviewSection";

export default function IntakeV6ProductionHandoffPreviewPanel({
  preview,
  loading,
}: {
  preview: IntakeV6ProductionHandoffPreviewResponse | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className={v6.card} data-testid="intake-v6-production-handoff-preview">
        <p className="text-[12px] text-slate-400">Calculez preview producție…</p>
      </div>
    );
  }
  if (!preview) {
    return (
      <div className={v6.card} data-testid="intake-v6-production-handoff-preview">
        <p className="text-[12px] text-slate-400">Preview producție indisponibil.</p>
      </div>
    );
  }

  const summary = preview.summary ?? {};
  const compatMappingUsed =
    preview.compat_cnc_mapping_used ?? preview.legacy_cnc_mapping_used;

  return (
    <div className={v6.card} data-testid="intake-v6-production-handoff-preview">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-[12px] font-bold uppercase tracking-wide">Preview producție</h3>
          <p className="mt-1 text-[10px] text-slate-500">
            Nu creează taskuri reale. Nu consumă stoc. Estimare materiale = ofertă, nu execuție
            inventar.
          </p>
        </div>
        <AtomsBadge tone="muted">{preview.handoff_mode}</AtomsBadge>
      </div>

      <dl className="mb-4 grid grid-cols-2 gap-3 text-[11px] sm:grid-cols-4">
        <div>
          <dt className="text-slate-500">Material jobs</dt>
          <dd data-testid="intake-v6-handoff-material-jobs-count">
            {summary.material_jobs_count ?? preview.material_jobs.length}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Operation groups</dt>
          <dd data-testid="intake-v6-handoff-operation-groups-count">
            {summary.operation_groups_count ??
              preview.operation_groups.filter((g) => g.active).length}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Task seed preview</dt>
          <dd data-testid="intake-v6-handoff-task-seeds-count">
            {summary.task_seed_preview_count ??
              preview.task_seed_preview.filter((t) => t.active).length}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Blockers</dt>
          <dd data-testid="intake-v6-handoff-blockers-count">{preview.blockers.length}</dd>
        </div>
      </dl>

      {preview.material_jobs.length > 0 ? (
        <div className="mb-4">
          <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">
            Material jobs
          </h4>
          <ul className="space-y-1 text-[11px] text-slate-300">
            {preview.material_jobs.slice(0, 8).map((job) => {
              const pricedQty = job.priced_quantity ?? job.quantity;
              const quantityLabel =
                job.priced_quantity != null &&
                job.waste_percent != null &&
                pricedQty !== job.quantity
                  ? `${formatIntakeV6Quantity(job.quantity, job.unit)} · pentru preț: ${formatIntakeV6PricingQuantity(
                      job.quantity,
                      pricedQty,
                      job.unit,
                      job.waste_percent,
                    )}`
                  : formatIntakeV6Quantity(job.quantity, job.unit);
              return (
              <li key={job.job_key} className="border-b border-[#2A3548]/60 py-1">
                {job.display_name} — {quantityLabel}
                {job.quantity_basis ? (
                  <span
                    className="block text-[10px] text-slate-500"
                    data-testid={`intake-v6-handoff-basis-${job.job_key}`}
                  >
                    {formatIntakeV6QuantityBasisLabel(job.quantity_basis)}
                  </span>
                ) : null}
              </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <IntakeV6CncOperationPreviewSection
        candidates={preview.cnc_operation_candidates ?? []}
        cncTaskSource={preview.cnc_task_source}
        compatMappingUsed={compatMappingUsed}
        testIdPrefix="intake-v6-handoff-cnc"
      />

      <IntakeV6EdgeCantOperationPreviewSection
        candidates={preview.edge_cant_operation_candidates ?? []}
        edgeCantTaskSource={preview.edge_cant_task_source}
        testIdPrefix="intake-v6-handoff-edge-cant"
      />

      {preview.blockers.length > 0 ? (
        <ul className="mb-3 space-y-1 text-[10px] text-red-300" data-testid="intake-v6-handoff-blockers">
          {preview.blockers.map((item) => (
            <li key={`${item.code}-${item.source}`}>• {item.message}</li>
          ))}
        </ul>
      ) : null}

      {preview.warnings.length > 0 ? (
        <ul className="space-y-1 text-[10px] text-amber-200" data-testid="intake-v6-handoff-warnings">
          {preview.warnings.map((item) => (
            <li key={`${item.code}-${item.source}`}>• {item.message}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}



