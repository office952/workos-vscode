import { useEffect, useState } from "react";
import { getProfitabilityActualReadModel, type ProfitabilityActualReadModel } from "@/api/profitabilityActualReadModel";
import { formatMoney, isManagementRole, type ExecutionResultRole } from "./executionResultWorkspace";

export function FinalResultPanel({ orderId, role }: { orderId: number; role: ExecutionResultRole }) {
  const [model, setModel] = useState<ProfitabilityActualReadModel | null>(null);
  useEffect(() => { if (isManagementRole(role)) void getProfitabilityActualReadModel(orderId).then(setModel).catch(() => setModel(null)); }, [orderId, role]);
  if (!isManagementRole(role)) return null;
  const result = model?.profitability_result as Record<string, { amount?: Record<string, unknown> }> | undefined;
  const commercial = model?.commercial_truth as Record<string, Record<string, unknown>> | undefined;
  const currency = commercial?.currency?.value;
  const margin = result?.actual_margin?.amount;
  return <section className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4" data-testid="execution-final-result">
    <h2 className="text-sm font-semibold text-wo-text-primary">Rezultat operațional post-lucrare</h2>
    <div className="mt-3 rounded-md bg-wo-surface-raised px-3 py-2"><p className="text-[10px] uppercase text-wo-text-muted">Marjă operațională finală</p><p className="mt-1 font-semibold text-wo-text-primary">{margin?.available === true ? formatMoney(margin.value, currency) : "Indisponibilă până la completarea costurilor"}</p>{margin?.available !== true && typeof margin?.reason === "string" ? <p className="mt-1 text-[10px] text-wo-text-muted">{margin.reason}</p> : null}</div>
  </section>;
}
