/**
 * Management read-only panel for Profitability Actual Read Model V1.
 * Does not invent labor cost or display fake "Profit real".
 */
import { useEffect, useState } from "react";
import {
  getProfitabilityActualReadModel,
  type ProfitabilityActualReadModel,
} from "@/api/profitabilityActualReadModel";

function FieldRow({
  label,
  available,
  value,
  reason,
}: {
  label: string;
  available?: boolean;
  value?: unknown;
  reason?: string | null;
}) {
  return (
    <div className="flex flex-col gap-0.5 text-[11px]">
      <span className="text-wo-text-muted">{label}</span>
      {available ? (
        <span className="font-semibold text-wo-text-primary">{String(value)}</span>
      ) : (
        <span className="text-wo-warning">
          Indisponibil{reason ? ` — ${reason}` : ""}
        </span>
      )}
    </div>
  );
}

export function ProfitabilityActualReadPanel({ orderId }: { orderId: number }) {
  const [model, setModel] = useState<ProfitabilityActualReadModel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openTech, setOpenTech] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    void getProfitabilityActualReadModel(orderId)
      .then((m) => {
        if (!cancelled) setModel(m);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "load_failed");
          setModel(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  const commercial = model?.commercial_truth as Record<string, any> | undefined;
  const estimated = model?.estimated_internal_truth as Record<string, any> | undefined;
  const operational = model?.actual_operational_truth as Record<string, any> | undefined;
  const costs = model?.actual_cost_truth as Record<string, any> | undefined;
  const result = model?.profitability_result as Record<string, any> | undefined;

  return (
    <section
      className="rounded-lg border border-wo-border-subtle bg-wo-surface p-3 space-y-3"
      data-testid="profitability-actual-read-panel"
    >
      <header>
        <h2 className="text-sm font-semibold text-wo-text-primary">
          Profitabilitate — adevăruri separate
        </h2>
        <p className="text-[10px] text-wo-text-muted">
          Read-only. Minutele reale nu sunt convertite automat în lei. Lipsa datelor ≠ 0.
        </p>
      </header>

      {error && (
        <p className="text-[11px] text-wo-danger" data-testid="profitability-actual-error">
          {error === "actor_not_authorized"
            ? "Vizibil doar pentru management (admin/manager)."
            : error}
        </p>
      )}

      {model && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <FieldRow
            label="Venit comercial acceptat"
            available={Boolean(commercial?.accepted_revenue?.available)}
            value={`${commercial?.accepted_revenue?.value} ${commercial?.currency?.value ?? ""}`}
            reason={commercial?.accepted_revenue?.reason}
          />
          <FieldRow
            label="Cost intern estimat"
            available={Boolean(estimated?.estimated_total_cost?.available)}
            value={estimated?.estimated_total_cost?.value}
            reason={estimated?.estimated_total_cost?.reason}
          />
          <FieldRow
            label="Durată reală (minute)"
            available={Boolean(operational?.actual_duration_minutes?.available)}
            value={operational?.actual_duration_minutes?.value}
            reason={operational?.actual_duration_minutes?.reason}
          />
          <FieldRow
            label="Marjă estimată"
            available={Boolean(result?.estimated_margin?.amount?.available)}
            value={result?.estimated_margin?.amount?.value}
            reason={result?.estimated_margin?.amount?.reason}
          />
          <FieldRow
            label="Cost muncă real (lei)"
            available={Boolean(costs?.labor_actual_cost?.available)}
            value={costs?.labor_actual_cost?.value}
            reason={costs?.labor_actual_cost?.reason}
          />
          <FieldRow
            label="Marjă reală"
            available={Boolean(result?.actual_margin?.amount?.available)}
            value={result?.actual_margin?.amount?.value}
            reason={result?.actual_margin?.amount?.reason}
          />
        </div>
      )}

      {Array.isArray(result?.unavailable_reasons) && result.unavailable_reasons.length > 0 && (
        <ul className="text-[10px] text-wo-text-secondary list-disc pl-4 space-y-0.5">
          {(result.unavailable_reasons as string[]).map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      <button
        type="button"
        className="text-[10px] font-semibold text-wo-text-secondary hover:text-wo-text-primary"
        onClick={() => setOpenTech((v) => !v)}
      >
        {openTech ? "Ascunde detalii tehnice" : "Detalii tehnice"}
      </button>
      {openTech && model && (
        <pre className="text-[9px] font-mono overflow-auto max-h-48 bg-wo-surface-inset p-2 rounded border border-wo-border-subtle">
          {JSON.stringify(model, null, 2)}
        </pre>
      )}
    </section>
  );
}
