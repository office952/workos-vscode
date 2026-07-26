import type { IntakeV6CncOperationDryRunCandidate } from "@/lib/intakeV6/intakeV6Api";
import {
  formatIntakeV6CncPreviewSource,
  formatIntakeV6CncPricingStatus,
  formatIntakeV6CncQuantity,
  formatIntakeV6CncWorkstation,
  formatIntakeV6CncCandidateTitle,
} from "@/lib/intakeV6/intakeV6CncDryRunDisplay";

export default function IntakeV6CncOperationPreviewSection({
  candidates,
  cncTaskSource,
  compatMappingUsed,
  legacyCncMappingUsed,
  testIdPrefix = "intake-v6-cnc-preview",
}: {
  candidates: IntakeV6CncOperationDryRunCandidate[];
  cncTaskSource?: string | null;
  compatMappingUsed?: boolean;
  legacyCncMappingUsed?: boolean;
  testIdPrefix?: string;
}) {
  if (candidates.length === 0 && !cncTaskSource) {
    return null;
  }

  const usesCompatFallback = compatMappingUsed ?? legacyCncMappingUsed;

  return (
    <div className="mb-4" data-testid={testIdPrefix}>
      <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">
        Operații CNC (preview)
      </h4>
      <p className="mb-2 text-[10px] text-slate-500" data-testid={`${testIdPrefix}-source`}>
        Sursă preview: {formatIntakeV6CncPreviewSource(cncTaskSource)}
        {usesCompatFallback ? " · compat fallback" : ""}
      </p>
      <ul className="space-y-2 text-[11px] text-slate-300">
        {candidates.map((candidate) => (
          <li
            key={candidate.candidate_key}
            className="rounded border border-wo-border-strong/60 px-3 py-2"
            data-testid={`${testIdPrefix}-row-${candidate.operation_key}`}
          >
            <p className="font-medium text-slate-200">{formatIntakeV6CncCandidateTitle(candidate.title)}</p>
            <p data-testid={`${testIdPrefix}-quantity-${candidate.operation_key}`}>
              Cantitate: {formatIntakeV6CncQuantity(candidate.quantity, candidate.unit)}
            </p>
            {candidate.passes > 1 ? (
              <p data-testid={`${testIdPrefix}-passes-${candidate.operation_key}`}>
                Treceri: {candidate.passes}
              </p>
            ) : null}
            {candidate.operation_equivalent_quantity != null ? (
              <p data-testid={`${testIdPrefix}-equiv-${candidate.operation_key}`}>
                Echivalent utilaj:{" "}
                {candidate.operation_equivalent_quantity.toFixed(2)} m-pass
              </p>
            ) : null}
            {candidate.workstation_key ? (
              <p>
                Stație: {formatIntakeV6CncWorkstation(candidate.workstation_key)}
              </p>
            ) : null}
            {candidate.required_machine_key ? (
              <p>Utilaj: {candidate.required_machine_key}</p>
            ) : null}
            {candidate.required_skill_key ? (
              <p>Skill: {candidate.required_skill_key}</p>
            ) : null}
            <p data-testid={`${testIdPrefix}-pricing-${candidate.operation_key}`}>
              Status preț: {formatIntakeV6CncPricingStatus(candidate.pricing_status, candidate.operation_type)}
            </p>
            {candidate.mapping_gaps.length > 0 ? (
              <p className="text-[10px] text-slate-500" data-testid={`${testIdPrefix}-mapping-${candidate.operation_key}`}>
                Lipsuri mapare tehnică: {candidate.mapping_gaps.length}
              </p>
            ) : null}
            <p className="text-[10px] text-slate-500">
              Sursă: {formatIntakeV6CncPreviewSource(candidate.source)}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}



