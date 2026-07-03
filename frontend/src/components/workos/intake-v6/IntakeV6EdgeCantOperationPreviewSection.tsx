import type { IntakeV6EdgeCantOperationDryRunCandidate } from "@/lib/intakeV6/intakeV6Api";
import {
  formatIntakeV6EdgeCantPreviewSource,
  formatIntakeV6EdgeCantPricingStatus,
  formatIntakeV6EdgeCantQuantity,
} from "@/lib/intakeV6/intakeV6EdgeCantDryRunDisplay";

export default function IntakeV6EdgeCantOperationPreviewSection({
  candidates,
  edgeCantTaskSource,
  testIdPrefix = "intake-v6-edge-cant-preview",
}: {
  candidates: IntakeV6EdgeCantOperationDryRunCandidate[];
  edgeCantTaskSource?: string | null;
  testIdPrefix?: string;
}) {
  if (candidates.length === 0 && !edgeCantTaskSource) {
    return null;
  }

  return (
    <div className="mb-4" data-testid={testIdPrefix}>
      <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">
        Operații cant / volum (preview)
      </h4>
      <p className="mb-2 text-[10px] text-slate-500" data-testid={`${testIdPrefix}-source`}>
        edge_cant_task_source: {formatIntakeV6EdgeCantPreviewSource(edgeCantTaskSource)}
      </p>
      <ul className="space-y-2 text-[11px] text-slate-300">
        {candidates.map((candidate) => (
          <li
            key={candidate.candidate_key}
            className="rounded border border-[#2A3548]/60 px-3 py-2"
            data-testid={`${testIdPrefix}-row-${candidate.operation_key}`}
          >
            <p className="font-medium text-slate-200">{candidate.title}</p>
            <p data-testid={`${testIdPrefix}-quantity-${candidate.operation_key}`}>
              Cantitate: {formatIntakeV6EdgeCantQuantity(candidate.quantity, candidate.unit)}
            </p>
            <p data-testid={`${testIdPrefix}-pricing-${candidate.operation_key}`}>
              Status preț: {formatIntakeV6EdgeCantPricingStatus(candidate.pricing_status)}
            </p>
            <p className="text-[10px] text-slate-500">
              consumes_stock_now={candidate.consumes_stock_now} · creates_task_now=
              {candidate.creates_task_now}
            </p>
            {candidate.mapping_gaps.length > 0 ? (
              <p className="text-amber-300">Mapping gaps: {candidate.mapping_gaps.join(", ")}</p>
            ) : null}
            <p className="text-[10px] text-slate-500">
              Sursă: {formatIntakeV6EdgeCantPreviewSource(candidate.source)}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}



