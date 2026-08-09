import { useEffect, useState } from "react";
import {
  getProfitabilityActualReadModel,
  type ProfitabilityActualReadModel,
} from "@/api/profitabilityActualReadModel";
import { formatMoney, isManagementRole, type ExecutionResultRole } from "./executionResultWorkspace";

export function FinalResultPanel({ orderId, role }: { orderId: number; role: ExecutionResultRole }) {
  const [model, setModel] = useState<ProfitabilityActualReadModel | null>(null);
  useEffect(() => {
    if (isManagementRole(role)) {
      void getProfitabilityActualReadModel(orderId)
        .then(setModel)
        .catch(() => setModel(null));
    }
  }, [orderId, role]);
  if (!isManagementRole(role)) return null;

  const monetary = model?.monetary_v1 as Record<string, unknown> | undefined;
  const result = model?.profitability_result as
    | Record<string, { amount?: Record<string, unknown>; label?: string }>
    | undefined;
  const commercial = model?.commercial_truth as Record<string, Record<string, unknown>> | undefined;
  const contribution = (monetary?.known_contribution ?? result?.actual_margin?.amount) as
    | Record<string, unknown>
    | undefined;
  const compositionCurrency =
    (typeof monetary?.composition_currency === "string" && monetary.composition_currency) ||
    commercial?.currency?.value;
  const scope =
    typeof monetary?.scope_status === "string"
      ? monetary.scope_status
      : typeof result?.scope_status === "string"
        ? result.scope_status
        : null;
  const label =
    typeof result?.actual_margin?.label === "string"
      ? result.actual_margin.label
      : "Contribuție cunoscută V1";

  return (
    <section
      className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
      data-testid="execution-final-result"
    >
      <h2 className="text-sm font-semibold text-wo-text-primary">Profitabilitate V1 — rezultat cunoscut</h2>
      <p className="mt-1 text-[11px] text-wo-text-muted">
        Venit − manoperă realizată − material realizat. Cost utilaj și alte costuri directe = N/A pentru
        V1 (nu zero). Nu este profit contabil complet.
      </p>
      <div className="mt-3 rounded-md bg-wo-surface-raised px-3 py-2">
        <p className="text-[10px] uppercase text-wo-text-muted">{label}</p>
        <p className="mt-1 font-semibold text-wo-text-primary">
          {contribution?.available === true
            ? formatMoney(contribution.value, compositionCurrency)
            : "Indisponibilă"}
        </p>
        {contribution?.available !== true && typeof contribution?.reason === "string" ? (
          <p className="mt-1 text-[10px] text-wo-text-muted">{String(contribution.reason)}</p>
        ) : null}
        {scope ? (
          <p className="mt-1 text-[10px] text-wo-text-muted">Status domeniu: {scope}</p>
        ) : null}
      </div>
    </section>
  );
}
