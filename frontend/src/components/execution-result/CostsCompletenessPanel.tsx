import { useEffect, useState } from "react";
import {
  getProfitabilityActualReadModel,
  type ProfitabilityActualReadModel,
} from "@/api/profitabilityActualReadModel";
import {
  formatMoney,
  humanReason,
  isManagementRole,
  type ExecutionResultRole,
} from "./executionResultWorkspace";

const COST_REASON_RO: Record<string, string> = {
  machine_not_applicable_by_job_profile: "Cost utilaj — neaplicabil pentru acest profil de lucrare",
  machine_cost_na_for_v1: "Cost utilaj — N/A pentru V1 (decizie Owner)",
  machine_actual_not_captured: "Cost utilaj — indisponibil (utilizare reală neînregistrată)",
  machine_policy_missing: "Cost utilaj — politică de cost lipsă",
  other_direct_not_declared: "Alte costuri directe — neaplicabile (nedeclarate)",
  other_direct_na_for_v1: "Alte costuri directe — N/A pentru V1 (decizie Owner)",
  employee_cost_policy_missing: "Cost intern standard al muncii incomplet",
  actual_material_cost_missing: "Cost material realizat incomplet",
  material_valuation_unavailable: "Valoare materială înghețată lipsă",
  currency_mismatch_no_fx: "Monede incompatibile — fără conversie FX inventată",
  profitability_fx_stamp_missing:
    "Lipsește cursul FX înghețat la convertirea comenzii (Policy A)",
};

export function CostsCompletenessPanel({ orderId, role }: { orderId: number; role: ExecutionResultRole }) {
  const [model, setModel] = useState<ProfitabilityActualReadModel | null>(null);
  useEffect(() => {
    if (!isManagementRole(role)) {
      setModel(null);
      return;
    }
    void getProfitabilityActualReadModel(orderId).then(setModel).catch(() => setModel(null));
  }, [orderId, role]);
  if (!isManagementRole(role)) {
    if (role === "operator") {
      return (
        <section
          className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
          data-testid="execution-costs-operator"
        >
          <h2 className="text-sm font-semibold text-wo-text-primary">Costuri realizate</h2>
          <p className="mt-1 text-[12px] text-wo-text-muted">
            Ratele brute și marja nu sunt expuse operatorului. Pregătirea operațională de închidere este
            vizibilă fără rate interne.
          </p>
        </section>
      );
    }
    return null;
  }
  const costs = model?.actual_cost_truth as Record<string, Record<string, unknown>> | undefined;
  const monetary = model?.monetary_v1 as Record<string, Record<string, unknown>> | undefined;
  const commercial = model?.commercial_truth as Record<string, Record<string, unknown>> | undefined;
  const revenueCurrency = commercial?.currency?.value;
  const laborCurrency = costs?.labor_actual_cost?.currency ?? monetary?.labor?.currency;
  const materialCurrency = costs?.actual_material_cost?.currency ?? monetary?.materials?.currency;
  const knownCost = costs?.actual_total_cost;
  const knownCostEur = monetary?.known_actual_cost_normalized as Record<string, unknown> | undefined;
  const fx = (model?.monetary_v1 as Record<string, unknown> | undefined)?.fx as
    | Record<string, unknown>
    | undefined;

  return (
    <section
      className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
      data-testid="execution-costs-completeness"
    >
      <h2 className="text-sm font-semibold text-wo-text-primary">Completitudinea costurilor realizate</h2>
      <p className="mt-1 text-[11px] text-wo-text-muted">
        Domeniu V1: venit + manoperă + material. Utilaj și alte directe = N/A pentru V1 (nu zero).
        {fx?.applied === true
          ? ` Costuri RON→EUR cu curs înghețat la convert (${String(fx.eur_to_ron_rate)}).`
          : ""}
      </p>
      <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 text-[12px]">
        <Cost
          label="Venit comercial acceptat"
          fact={commercial?.accepted_revenue}
          currency={revenueCurrency}
        />
        <Cost label="Cost intern standard al muncii" fact={costs?.labor_actual_cost} currency={laborCurrency} />
        <Cost label="Cost material realizat" fact={costs?.actual_material_cost} currency={materialCurrency} />
        <Cost
          label="Cost cunoscut V1 (manoperă + material)"
          fact={knownCost}
          currency={knownCost?.currency ?? laborCurrency}
        />
        {knownCostEur?.available === true ? (
          <Cost
            label="Cost cunoscut normalizat (Policy A)"
            fact={knownCostEur}
            currency={knownCostEur.currency ?? "EUR"}
          />
        ) : null}
        <Cost label="Cost utilaj" fact={costs?.machine_actual_cost} currency={revenueCurrency} />
        <Cost label="Alte costuri directe" fact={costs?.other_actual_cost} currency={revenueCurrency} />
      </div>
    </section>
  );
}

function Cost({
  label,
  fact,
  currency,
}: {
  label: string;
  fact: Record<string, unknown> | undefined;
  currency: unknown;
}) {
  const available = fact?.available === true;
  const status = typeof fact?.status === "string" ? fact.status : null;
  const applicability = typeof fact?.applicability === "string" ? fact.applicability : null;
  let display = "Indisponibil";
  if (available) display = formatMoney(fact?.value, currency);
  else if (
    status === "not_applicable" ||
    status === "N_A_FOR_V1" ||
    applicability === "not_applicable"
  ) {
    display = "N/A pentru V1";
  } else if (status === "complete") display = "Complet";
  const reasonCode = typeof fact?.reason === "string" ? fact.reason : null;
  const reasonText = reasonCode ? COST_REASON_RO[reasonCode] ?? humanReason(reasonCode) : null;
  return (
    <div className="rounded-md bg-wo-surface-raised px-3 py-2">
      <p className="text-[10px] uppercase text-wo-text-muted">{label}</p>
      <p className="mt-1 font-semibold text-wo-text-primary">{display}</p>
      {reasonText ? <p className="mt-1 text-[10px] text-wo-text-muted">{reasonText}</p> : null}
    </div>
  );
}
