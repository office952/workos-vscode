import { useEffect, useState } from "react";
import { getProfitabilityActualReadModel, type ProfitabilityActualReadModel } from "@/api/profitabilityActualReadModel";
import { formatMoney, type ExecutionResultRole } from "./executionResultWorkspace";

export function CostsCompletenessPanel({ orderId, role }: { orderId: number; role: ExecutionResultRole }) {
  const [model, setModel] = useState<ProfitabilityActualReadModel | null>(null);
  useEffect(() => { void getProfitabilityActualReadModel(orderId).then(setModel).catch(() => setModel(null)); }, [orderId]);
  if (role === "operator") return <section className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4" data-testid="execution-costs-operator"><h2 className="text-sm font-semibold text-wo-text-primary">Costuri realizate</h2><p className="mt-1 text-[12px] text-wo-text-muted">Costurile și marjele sunt disponibile managementului după confirmarea backend-ului.</p></section>;
  const costs = model?.actual_cost_truth as Record<string, Record<string, unknown>> | undefined;
  const currency = (model?.commercial_truth as Record<string, Record<string, unknown>> | undefined)?.currency?.value;
  return <section className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4" data-testid="execution-costs-completeness">
    <h2 className="text-sm font-semibold text-wo-text-primary">Completitudinea costurilor realizate</h2>
    <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3 text-[12px]">
      <Cost label="Cost intern standard al muncii" fact={costs?.labor_actual_cost} currency={currency} />
      <Cost label="Cost material realizat" fact={costs?.material_actual_cost} currency={currency} />
      <Cost label="Cost utilaj" fact={costs?.machine_actual_cost} currency={currency} />
      <Cost label="Alte costuri directe" fact={costs?.other_direct_actual_cost} currency={currency} />
    </div>
  </section>;
}
function Cost({ label, fact, currency }: { label: string; fact: Record<string, unknown> | undefined; currency: unknown }) {
  const available = fact?.available === true;
  return <div className="rounded-md bg-wo-surface-raised px-3 py-2"><p className="text-[10px] uppercase text-wo-text-muted">{label}</p><p className="mt-1 font-semibold text-wo-text-primary">{available ? formatMoney(fact?.value, currency) : "Indisponibil / neaplicabil"}</p>{!available && typeof fact?.reason === "string" ? <p className="mt-1 text-[10px] text-wo-text-muted">{fact.reason}</p> : null}</div>;
}
