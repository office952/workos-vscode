import type { IntakeV6OrderBoundTaskReadinessResponse } from "@/lib/intakeV6/intakeV6Api";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6OrderBoundTaskReadinessPanel({
  readiness,
  loading,
}: {
  readiness: IntakeV6OrderBoundTaskReadinessResponse | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className={v6.card} data-testid="intake-v6-order-bound-task-readiness">
        <p className="text-[12px] text-slate-400">Calculez pregătirea generării taskurilor…</p>
      </div>
    );
  }
  if (!readiness) {
    return (
      <div className={v6.card} data-testid="intake-v6-order-bound-task-readiness">
        <p className="text-[12px] text-slate-400">Readiness indisponibil.</p>
      </div>
    );
  }

  const blockers = readiness.blockers.filter((b) => b.severity === "blocking");
  const contract = readiness.future_generation_contract;

  return (
    <div className={v6.card} data-testid="intake-v6-order-bound-task-readiness">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-[12px] font-bold uppercase tracking-wide">
            Pregătire generare taskuri producție
          </h3>
          <p className="mt-1 text-[10px] text-slate-500">
            Acest pas nu creează taskuri reale. Nu scrie în producție. Nu consumă stoc.
          </p>
        </div>
        <AtomsBadge tone="muted">{readiness.readiness_mode}</AtomsBadge>
      </div>

      <dl className="mb-4 grid grid-cols-2 gap-3 text-[11px] sm:grid-cols-4">
        <div>
          <dt className="text-slate-500">Quote linked</dt>
          <dd data-testid="intake-v6-readiness-quote-linked">
            {readiness.linked_quote.exists ? "yes" : "no"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Order linked</dt>
          <dd data-testid="intake-v6-readiness-order-linked">
            {readiness.linked_order.exists ? "yes" : "no"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Can generate real tasks</dt>
          <dd data-testid="intake-v6-readiness-can-generate">
            {readiness.can_generate_real_tasks ? "yes" : "no"}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Owner confirmation</dt>
          <dd data-testid="intake-v6-readiness-owner-confirmation">
            {readiness.owner_confirmation_required ? "required" : "not required"}
          </dd>
        </div>
      </dl>

      {readiness.can_generate_reason ? (
        <p className="mb-3 text-[10px] text-slate-400" data-testid="intake-v6-readiness-reason">
          Motiv blocare: {readiness.can_generate_reason}
        </p>
      ) : null}

      {blockers.length > 0 ? (
        <ul
          className="mb-3 space-y-1 text-[10px] text-red-300"
          data-testid="intake-v6-readiness-blockers"
        >
          {blockers.slice(0, 8).map((item) => (
            <li key={`${item.code}-${item.source}`}>• {item.message}</li>
          ))}
        </ul>
      ) : null}

      {readiness.warnings.length > 0 ? (
        <ul className="mb-3 space-y-1 text-[10px] text-amber-200" data-testid="intake-v6-readiness-warnings">
          {readiness.warnings.slice(0, 4).map((item) => (
            <li key={`${item.code}-${item.source}`}>• {item.message}</li>
          ))}
        </ul>
      ) : null}

      <div className="border-t border-[#2A3548]/60 pt-3 text-[10px] text-slate-500">
        <p data-testid="intake-v6-readiness-next-action">
          Următorul pas: {contract.next_action_label} —{" "}
          {contract.next_action_enabled ? "activ" : "dezactivat"}
        </p>
        <p className="mt-1">Contract: {contract.contract_version}</p>
      </div>
    </div>
  );
}



