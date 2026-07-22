/**
 * Desfășurător preț — calibration surface over CPP + EIC (PRODUCT_PRICE_BREAKDOWN_V1).
 */

import { useEffect, useMemo, useState } from "react";
import {
  productPriceBreakdownApi,
  type PriceBreakdownLine,
  type PriceBreakdownLineGroup,
  type ProductPriceBreakdownResponse,
} from "@/api/productPriceBreakdown";
import { PS_SURFACE_INSET, PS_SURFACE_PANEL } from "./productSystemSurfaces";

type GroupFilter = "all" | PriceBreakdownLineGroup;

const GROUP_LABELS: Record<PriceBreakdownLineGroup, string> = {
  material: "Materiale",
  machine: "Utilaje",
  labor: "Manoperă",
  service: "Servicii",
  ai_decision: "Decizii AI",
  adjustment: "Ajustări",
  commercial: "Comercial",
  internal: "Intern",
};

function money(v: number | null | undefined, currency?: string | null): string {
  if (v == null || Number.isNaN(v)) return "—";
  const c = currency || "RON";
  return `${v.toFixed(2)} ${c}`;
}

function groupChip(group: PriceBreakdownLineGroup): string {
  switch (group) {
    case "material":
      return "border-emerald-800/40 text-emerald-200";
    case "machine":
      return "border-violet-800/40 text-violet-200";
    case "labor":
      return "border-sky-800/40 text-sky-200";
    case "service":
      return "border-teal-800/40 text-teal-200";
    case "ai_decision":
      return "border-amber-800/40 text-amber-200";
    case "adjustment":
      return "border-rose-800/40 text-rose-200";
    case "commercial":
      return "border-slate-600 text-slate-200";
    case "internal":
      return "border-slate-700 text-slate-400";
    default: {
      const _exhaustive: never = group;
      return _exhaustive;
    }
  }
}

function LineRow({ line }: { line: PriceBreakdownLine }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      data-testid={`price-breakdown-line-${line.resource_code}`}
      className="border-b border-slate-800/60 last:border-b-0"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="grid w-full grid-cols-[minmax(0,1.3fr)_minmax(0,1.1fr)_minmax(0,0.7fr)_minmax(0,0.7fr)] gap-2 px-3 py-2.5 text-left text-[12px] hover:bg-slate-900/40"
      >
        <span>
          <span
            className={`mr-1.5 inline-block rounded border px-1.5 py-0.5 text-[9px] font-medium ${groupChip(line.line_group)}`}
          >
            {GROUP_LABELS[line.line_group]}
          </span>
          <span className="font-medium text-slate-100">{line.display_name}</span>
          {line.warning ? (
            <span className="mt-0.5 block text-[10px] text-amber-200/90">{line.warning}</span>
          ) : null}
        </span>
        <span className="font-mono text-[11px] text-slate-300">{line.formula_display || "—"}</span>
        <span className="text-slate-300">
          {money(line.internal_cost, line.currency)}
          <span className="mt-0.5 block text-[10px] text-slate-500">intern</span>
        </span>
        <span className="text-slate-200">
          {money(line.commercial_value, line.currency)}
          <span className="mt-0.5 block text-[10px] text-slate-500">comercial</span>
        </span>
      </button>
      {open ? (
        <div className={`${PS_SURFACE_INSET} mx-3 mb-2 grid gap-1 px-3 py-2 text-[11px] text-slate-400 sm:grid-cols-2`}>
          <p>
            Surse: {line.source_type}
            {line.source_id ? ` · ${line.source_id}` : ""}
          </p>
          <p>
            Cantitate: {line.quantity ?? "—"} {line.unit || ""}
            {line.quantity_key ? ` · key=${line.quantity_key}` : ""}
          </p>
          <p>CPP: {line.cpp_line || "—"}</p>
          <p>EIC: {line.eic_rule || "—"}</p>
          {line.material_source_type ? (
            <p className="sm:col-span-2">
              Material: {line.material_source_type}
              {line.material_supplier ? ` · ${line.material_supplier}` : ""}
              {line.material_freshness ? ` · ${line.material_freshness}` : ""}
              {line.material_normalized_price != null
                ? ` · norm ${line.material_normalized_price} ${line.material_normalized_unit || ""}`
                : ""}
            </p>
          ) : null}
          {line.material_normalization_formula ? (
            <pre className="sm:col-span-2 whitespace-pre-wrap font-mono text-[10px] text-slate-500">
              {line.material_normalization_formula}
            </pre>
          ) : null}
          {line.rationale_ro ? <p className="sm:col-span-2">{line.rationale_ro}</p> : null}
          {line.configurable ? (
            <p className="text-sky-300/80 sm:col-span-2">Configurabil (AI) — vezi Decizii operaționale AI</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function PriceBreakdownSection({ templateCode }: { templateCode: string }) {
  const [data, setData] = useState<ProductPriceBreakdownResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<GroupFilter>("all");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    productPriceBreakdownApi
      .postBreakdown(templateCode, {})
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(null);
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (filter === "all") return data.lines;
    return data.lines.filter((l) => l.line_group === filter);
  }, [data, filter]);

  if (loading) {
    return (
      <section
        data-testid="price-breakdown-loading"
        className={`${PS_SURFACE_PANEL} px-4 py-4 text-sm text-slate-400`}
      >
        Se încarcă desfășurătorul de preț…
      </section>
    );
  }

  if (error) {
    return (
      <section
        data-testid="price-breakdown-error"
        className={`${PS_SURFACE_PANEL} space-y-1 border-rose-900/40 px-4 py-4 text-sm text-rose-200`}
      >
        <p className="font-medium">Desfășurător preț indisponibil</p>
        <p className="text-xs text-rose-200/80">{error}</p>
      </section>
    );
  }

  if (!data) return null;

  const filters: Array<{ id: GroupFilter; label: string }> = [
    { id: "all", label: `Toate (${data.lines.length})` },
    { id: "material", label: GROUP_LABELS.material },
    { id: "machine", label: GROUP_LABELS.machine },
    { id: "labor", label: GROUP_LABELS.labor },
    { id: "service", label: GROUP_LABELS.service },
    { id: "ai_decision", label: GROUP_LABELS.ai_decision },
    { id: "adjustment", label: GROUP_LABELS.adjustment },
  ];

  return (
    <section data-testid="price-breakdown-section" className="space-y-3">
      <div className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Desfășurător preț
            </p>
            <h3 className="mt-0.5 text-base font-semibold text-slate-100">
              Cum se construiește prețul pentru configurația curentă?
            </h3>
            <p className="mt-1 max-w-2xl text-[12px] leading-relaxed text-slate-400">
              {data.ownership_note_ro}
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {data.fixture_id ? (
              <span
                data-testid="price-breakdown-fixture"
                className="rounded border border-slate-700 px-2 py-0.5 text-[10px] text-slate-300"
              >
                Fixture: {data.fixture_id}
              </span>
            ) : null}
            {data.operational_readiness ? (
              <span className="rounded border border-sky-900/40 px-2 py-0.5 text-[10px] text-sky-200">
                {data.operational_readiness}
              </span>
            ) : null}
            {data.acm_treatments_blocked ? (
              <span
                data-testid="price-breakdown-acm-treatments-blocked"
                className="rounded border border-amber-800/40 px-2 py-0.5 text-[10px] text-amber-200"
              >
                Tratamente ACM blocate
              </span>
            ) : null}
          </div>
        </div>

        <div
          className={`${PS_SURFACE_INSET} grid gap-2 px-3 py-2 sm:grid-cols-4`}
          data-testid="price-breakdown-totals"
        >
          <TotalStat
            label="Intern (EIC)"
            value={money(data.totals.internal_total, data.totals.currency)}
          />
          <TotalStat
            label="Comercial (CPP)"
            value={money(data.totals.commercial_total, data.totals.currency)}
          />
          <TotalStat
            label="CPP reconcile"
            value={data.totals.cpp_total_matches ? "OK" : "DIFF"}
            tone={data.totals.cpp_total_matches ? "ok" : "warn"}
          />
          <TotalStat
            label="EIC reconcile"
            value={data.totals.eic_total_matches ? "OK" : "DIFF"}
            tone={data.totals.eic_total_matches ? "ok" : "warn"}
          />
        </div>

        {data.totals.ai_contribution_note_ro ? (
          <p className="text-[11px] text-slate-500">{data.totals.ai_contribution_note_ro}</p>
        ) : null}

        {data.warnings.length > 0 ? (
          <ul
            data-testid="price-breakdown-warnings"
            className="space-y-0.5 text-[11px] text-amber-200/85"
          >
            {data.warnings.slice(0, 8).map((w) => (
              <li key={w}>• {w}</li>
            ))}
          </ul>
        ) : null}

        {data.blockers.length > 0 ? (
          <ul
            data-testid="price-breakdown-blockers"
            className="space-y-0.5 text-[11px] text-rose-200/90"
          >
            {data.blockers.slice(0, 6).map((b) => (
              <li key={b}>• {b}</li>
            ))}
          </ul>
        ) : null}

        {data.calibration_hooks.length > 0 ? (
          <details className="text-[11px] text-slate-500">
            <summary className="cursor-pointer text-slate-400">
              Calibrare timp (secundar, exclus din total) — {data.calibration_hooks.length}
            </summary>
            <ul className="mt-1 space-y-0.5">
              {data.calibration_hooks.map((h) => (
                <li key={`${h.line_code}-${h.purpose}`}>
                  {h.line_code || "—"}: {h.estimated_minutes ?? "?"} min · {h.purpose || ""}
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-1" role="tablist" aria-label="Filtru grup desfășurător">
        {filters.map((f) => (
          <button
            key={f.id}
            type="button"
            role="tab"
            aria-selected={filter === f.id}
            data-testid={`price-breakdown-filter-${f.id}`}
            onClick={() => setFilter(f.id)}
            className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
              filter === f.id
                ? "bg-slate-800/80 text-slate-100 ring-1 ring-slate-600/50"
                : "text-slate-500 hover:bg-slate-900/50 hover:text-slate-300"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div
        data-testid="price-breakdown-lines"
        className="overflow-hidden rounded-xl border border-slate-800/70"
      >
        <div className="grid grid-cols-[minmax(0,1.3fr)_minmax(0,1.1fr)_minmax(0,0.7fr)_minmax(0,0.7fr)] gap-2 border-b border-slate-800/70 bg-slate-950/40 px-3 py-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
          <span>Linie</span>
          <span>Formulă</span>
          <span>Cost intern</span>
          <span>Valoare comercială</span>
        </div>
        {filtered.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-500">Nicio linie în acest filtru.</p>
        ) : (
          filtered.map((line) => <LineRow key={line.line_id} line={line} />)
        )}
      </div>

      {data.group_totals.length > 0 ? (
        <div
          data-testid="price-breakdown-group-totals"
          className={`${PS_SURFACE_PANEL} grid gap-2 px-4 py-3 sm:grid-cols-3`}
        >
          {data.group_totals.map((g) => (
            <div key={g.line_group} className="text-[11px] text-slate-400">
              <p className="font-medium text-slate-200">{GROUP_LABELS[g.line_group]}</p>
              <p>
                {g.line_count} linii · intern {money(g.internal_subtotal, g.currency)} · comercial{" "}
                {money(g.commercial_subtotal, g.currency)}
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function TotalStat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "ok" | "warn";
}) {
  const toneClass =
    tone === "ok"
      ? "text-emerald-200"
      : tone === "warn"
        ? "text-amber-200"
        : "text-slate-100";
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-0.5 text-sm font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}
