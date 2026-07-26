/**
 * Preturi materiale — purchase/market truth registry (MATERIAL_MARKET_PRICE_REGISTRY_V1).
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  materialMarketPriceRegistryApi,
  type MaterialFreshness,
  type MaterialMarketPriceRecord,
  type MaterialMarketPriceRegistryResponse,
  type MaterialSourceType,
} from "@/api/materialMarketPriceRegistry";

type StatusFilter = "all" | "priced" | "missing" | "stale";

function money(v: number | null | undefined, currency?: string | null): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${v.toFixed(2)} ${currency || ""}`.trim();
}

function freshnessChip(f: MaterialFreshness): string {
  switch (f) {
    case "CURRENT":
      return "border-emerald-800/40 text-emerald-200";
    case "REVIEW_SOON":
      return "border-sky-800/40 text-sky-200";
    case "STALE":
    case "EXPIRED":
      return "border-amber-800/40 text-amber-200";
    case "UNKNOWN_DATE":
      return "border-slate-700 text-slate-400";
    default: {
      const _exhaustive: never = f;
      return _exhaustive;
    }
  }
}

function sourceLabel(s: MaterialSourceType): string {
  switch (s) {
    case "MEASURED_LANDED_COST":
      return "Landed măsurat";
    case "PURCHASE_INVOICE":
      return "Factură / OC";
    case "SUPPLIER_OFFER":
      return "Ofertă furnizor";
    case "OWNER_CONFIRMED":
      return "Owner confirmat";
    case "SUPPLIER_CATALOG":
      return "Catalog furnizor";
    case "TEMPORARY_AI_FALLBACK":
      return "Fallback AI";
    case "LEGACY":
      return "Legacy";
    case "MISSING":
      return "Pret lipsa";
    default: {
      const _exhaustive: never = s;
      return _exhaustive;
    }
  }
}

function statusChip(row: MaterialMarketPriceRecord): { label: string; className: string } {
  if (row.material_role === "variant_selector" || row.requires_direct_price === false) {
    return { label: "Selector variantă", className: "border-sky-800/40 text-sky-200" };
  }
  if (row.temporary_ai_fallback) {
    return { label: "Fallback AI", className: "border-amber-800/40 text-amber-200" };
  }
  if (row.raw_price == null) {
    return { label: "Pret lipsa", className: "border-rose-800/40 text-rose-200" };
  }
  if (row.freshness === "STALE" || row.freshness === "EXPIRED") {
    return { label: "Pret expirat", className: "border-amber-800/40 text-amber-200" };
  }
  if (row.preferred) {
    return { label: "Pret confirmat", className: "border-emerald-800/40 text-emerald-200" };
  }
  return { label: "Activ", className: "border-slate-700 text-slate-300" };
}

export function MaterialMarketPriceRegistryPanel() {
  const [data, setData] = useState<MaterialMarketPriceRegistryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    materialMarketPriceRegistryApi
      .getRegistry({ include_history: true })
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
  }, []);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.items.filter((row) => {
      switch (filter) {
        case "priced":
          return row.raw_price != null;
        case "missing":
          return row.raw_price == null;
        case "stale":
          return row.freshness === "STALE" || row.freshness === "EXPIRED";
        case "all":
          return true;
        default: {
          const _exhaustive: never = filter;
          return _exhaustive;
        }
      }
    });
  }, [data, filter]);

  const selectedRow = filtered.find((r) => r.material_code === selected) || null;

  if (loading) {
    return (
      <div
        data-testid="material-market-price-loading"
        className="rounded-xl border border-slate-800/70 px-4 py-6 text-sm text-slate-400"
      >
        Se încarcă registrul de prețuri materiale…
      </div>
    );
  }

  if (error) {
    return (
      <div
        data-testid="material-market-price-error"
        className="rounded-xl border border-rose-900/40 px-4 py-4 text-sm text-rose-200"
      >
        {error}
      </div>
    );
  }

  if (!data) return null;

  return (
    <section data-testid="material-market-price-registry" className="space-y-3">
      <div className="rounded-xl border border-slate-800/70 bg-slate-950/30 px-4 py-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Preturi materiale
            </p>
            <h3 className="mt-0.5 text-base font-semibold text-slate-100">
              Surse reale de achiziție — fără preț inventat
            </h3>
            <p className="mt-1 max-w-3xl text-[12px] text-slate-400">{data.ownership_note_ro}</p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px] sm:grid-cols-4">
            <Stat label="Priced" value={String(data.summary.priced)} />
            <Stat label="Lipsa" value={String(data.summary.missing)} tone="warn" />
            <Stat label="Stale" value={String(data.summary.stale)} tone="warn" />
            <Stat
              label="Critical lipsa"
              value={String(data.summary.active_template_critical_missing)}
              tone="warn"
            />
          </div>
        </div>
        {data.critical_missing.length > 0 ? (
          <p
            data-testid="material-market-critical-missing"
            className="mt-2 font-mono text-[10px] text-amber-200/90"
          >
            Critical: {data.critical_missing.join(", ")}
          </p>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-1" role="tablist" aria-label="Filtru preț material">
        {(
          [
            ["all", `Toate (${data.summary.total})`],
            ["priced", "Cu pret"],
            ["missing", "Pret lipsa"],
            ["stale", "Stale / expirat"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={filter === id}
            data-testid={`material-market-filter-${id}`}
            onClick={() => setFilter(id)}
            className={`rounded-md px-2.5 py-1 text-[11px] font-medium ${
              filter === id
                ? "bg-slate-800/80 text-slate-100 ring-1 ring-slate-600/50"
                : "text-slate-500 hover:bg-slate-900/50 hover:text-slate-300"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <div
          data-testid="material-market-price-table"
          className="overflow-hidden rounded-xl border border-slate-800/70"
        >
          <div className="grid grid-cols-[minmax(0,1.2fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/70 bg-slate-950/40 px-3 py-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
            <span>Material</span>
            <span>Raw</span>
            <span>Normalizat</span>
            <span>Sursa</span>
            <span>Status</span>
          </div>
          {filtered.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">Niciun material în filtru.</p>
          ) : (
            filtered.map((row) => {
              const chip = statusChip(row);
              return (
                <button
                  key={row.material_code}
                  type="button"
                  data-testid={`material-market-row-${row.material_code}`}
                  onClick={() => setSelected(row.material_code)}
                  className={`grid w-full grid-cols-[minmax(0,1.2fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/50 px-3 py-2.5 text-left text-[12px] hover:bg-slate-900/40 ${
                    selected === row.material_code ? "bg-slate-900/50" : ""
                  }`}
                >
                  <span>
                    <span className="font-medium text-slate-100">{row.display_name}</span>
                    <span className="mt-0.5 block font-mono text-[10px] text-slate-500">
                      {row.material_code}
                      {row.variant ? ` · ${row.variant}` : ""}
                    </span>
                  </span>
                  <span className="text-slate-300">
                    {money(row.raw_price, row.currency)}
                    <span className="mt-0.5 block text-[10px] text-slate-500">
                      / {row.raw_unit || "?"}
                    </span>
                  </span>
                  <span className="text-slate-200">
                    {money(row.normalization.normalized_price, row.currency)}
                    <span className="mt-0.5 block text-[10px] text-slate-500">
                      / {row.normalization.normalized_unit || "?"}
                    </span>
                  </span>
                  <span>
                    <span className="text-slate-300">{sourceLabel(row.source_type)}</span>
                    <span
                      className={`mt-0.5 inline-block rounded border px-1 py-0.5 text-[9px] ${freshnessChip(row.freshness)}`}
                    >
                      {row.freshness}
                    </span>
                  </span>
                  <span
                    className={`self-start rounded border px-1.5 py-0.5 text-[9px] font-medium ${chip.className}`}
                  >
                    {chip.label}
                  </span>
                </button>
              );
            })
          )}
        </div>

        <div
          data-testid="material-market-price-detail"
          className="rounded-xl border border-slate-800/70 bg-slate-950/30 px-4 py-3 text-[12px] text-slate-300"
        >
          {!selectedRow ? (
            <p className="text-slate-500">Selectează un material pentru sursă, formulă și istoric.</p>
          ) : (
            <div className="space-y-2">
              <p className="text-sm font-semibold text-slate-100">{selectedRow.display_name}</p>
              <p className="font-mono text-[11px] text-slate-500">{selectedRow.material_code}</p>
              {selectedRow.material_role === "variant_selector" ? (
                <p
                  data-testid="material-market-selector-note"
                  className="rounded border border-sky-900/40 bg-sky-950/20 px-2 py-1.5 text-[11px] text-sky-100/90"
                >
                  Selector familie — fără preț direct. Variante:{" "}
                  {(selectedRow.variant_codes || []).join(", ") || "—"}
                </p>
              ) : null}
              <p>
                Furnizor: {selectedRow.supplier_name || "—"}
                {selectedRow.preferred ? " · preferat" : ""}
              </p>
              <p>
                Sursa: {sourceLabel(selectedRow.source_type)}
                {selectedRow.source_name ? ` · ${selectedRow.source_name}` : ""}
              </p>
              <p>Effective: {selectedRow.effective_from || "—"}</p>
              <p>
                Freshness: {selectedRow.freshness}
                {selectedRow.freshness_policy_ro
                  ? ` — ${selectedRow.freshness_policy_ro}`
                  : ""}
              </p>
              {selectedRow.normalization.formula_display ? (
                <pre
                  data-testid="material-market-normalization-formula"
                  className="whitespace-pre-wrap rounded border border-slate-800/70 bg-slate-950/50 px-2 py-2 font-mono text-[11px] text-slate-200"
                >
                  {selectedRow.normalization.formula_display}
                </pre>
              ) : null}
              {selectedRow.active_templates.length > 0 ? (
                <p className="text-[11px] text-slate-500">
                  Template-uri: {selectedRow.active_templates.join(", ")}
                </p>
              ) : null}
              <div className="flex flex-wrap gap-2 pt-1">
                <Link
                  to={selectedRow.inventory_href}
                  className="rounded border border-slate-700 px-2 py-1 text-[11px] text-sky-300 hover:bg-slate-900"
                >
                  Inventory material
                </Link>
                <Link
                  to="/product-system/products"
                  className="rounded border border-slate-700 px-2 py-1 text-[11px] text-sky-300 hover:bg-slate-900"
                >
                  Product System
                </Link>
              </div>
              {selectedRow.history.length > 0 ? (
                <div data-testid="material-market-history" className="pt-2">
                  <p className="text-[10px] font-semibold uppercase text-slate-500">Istoric</p>
                  <ul className="mt-1 space-y-1">
                    {selectedRow.history.slice(0, 6).map((h) => (
                      <li key={h.history_id} className="font-mono text-[10px] text-slate-400">
                        {h.changed_at || h.valid_from || "—"} ·{" "}
                        {money(h.unit_cost, h.currency)} · {h.snapshot_source || "?"}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "warn";
}) {
  return (
    <div className="rounded border border-slate-800/70 px-2 py-1">
      <p className="text-[9px] uppercase text-slate-500">{label}</p>
      <p className={`text-sm font-semibold ${tone === "warn" ? "text-amber-200" : "text-slate-100"}`}>
        {value}
      </p>
    </div>
  );
}
