/**
 * Product System → Prețuri template (TEMPLATE_PRICING_STUDIO_V1).
 * Composes catalog rates + template recipe. Read-only — does not invent prices.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  templatePricingRecipeApi,
  type TemplateLaborRecipeItem,
  type TemplatePricingRecipeItem,
  type TemplatePricingRecipeResponse,
  type TemplateRecipeKind,
} from "@/api/templatePricingRecipe";
import { PS_SURFACE_INSET, PS_SURFACE_PANEL } from "./productSystemSurfaces";

type KindFilter = "all" | TemplateRecipeKind;

const KIND_LABELS: Record<TemplateRecipeKind, string> = {
  material: "Materiale",
  machine_operation: "Operații utilaje",
  labor: "Manoperă",
  service: "Servicii",
  commercial_line: "Linii CPP",
  minimum: "Minime",
  adjustment: "Ajustări",
  unknown: "Necunoscut",
};

function statusChip(status: TemplatePricingRecipeItem["status"]): string {
  switch (status) {
    case "active":
      return "border-emerald-800/40 bg-emerald-950/25 text-emerald-200";
    case "missing":
      return "border-rose-800/40 bg-rose-950/25 text-rose-200";
    case "blocked":
      return "border-amber-800/40 bg-amber-950/25 text-amber-200";
    case "warning":
      return "border-amber-800/30 bg-amber-950/15 text-amber-100";
    case "inactive":
      return "border-slate-700/50 bg-slate-900/40 text-slate-400";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

function statusLabel(status: TemplatePricingRecipeItem["status"]): string {
  switch (status) {
    case "active":
      return "Activ";
    case "missing":
      return "Tarif lipsă";
    case "blocked":
      return "Blocat";
    case "warning":
      return "Atenție";
    case "inactive":
      return "Inactiv";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

export function TemplatePricingStudioPanel({ templateCode }: { templateCode: string }) {
  const [data, setData] = useState<TemplatePricingRecipeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<KindFilter>("all");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    templatePricingRecipeApi
      .getRecipe(templateCode)
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
    if (filter === "all") return data.recipe;
    return data.recipe.filter((r) => r.recipe_kind === filter);
  }, [data, filter]);

  if (loading) {
    return (
      <div
        data-testid="template-pricing-studio-loading"
        className={`${PS_SURFACE_PANEL} px-4 py-6 text-sm text-slate-400`}
      >
        Se încarcă rețeta de preț…
      </div>
    );
  }

  if (error) {
    return (
      <div
        data-testid="template-pricing-studio-error"
        className={`${PS_SURFACE_PANEL} space-y-2 border-rose-900/40 px-4 py-4 text-sm text-rose-200`}
      >
        <p className="font-medium">Nu pot încărca Prețuri template</p>
        <p className="text-xs text-rose-200/80">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const filters: Array<{ id: KindFilter; label: string; count: number }> = [
    { id: "all", label: "Toate", count: data.summary.total_items },
    { id: "material", label: "Materiale", count: data.summary.materials },
    {
      id: "machine_operation",
      label: "Operații utilaje",
      count: data.summary.machine_operations,
    },
    { id: "labor", label: "Manoperă", count: data.summary.labor },
    { id: "service", label: "Servicii", count: data.summary.services },
    {
      id: "commercial_line",
      label: "Linii CPP",
      count: data.summary.commercial_lines,
    },
  ];

  return (
    <div data-testid="template-pricing-studio" className="space-y-4">
      <section className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              Prețuri template
            </p>
            <h3 className="mt-0.5 text-base font-semibold text-slate-100">
              Din ce este format prețul acestui template?
            </h3>
            <p className="mt-1 max-w-2xl text-[12px] leading-relaxed text-slate-400">
              {data.ownership_note_ro}
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <span
              className={`rounded border px-2 py-0.5 text-[10px] font-medium ${
                data.readiness.technical_ready
                  ? "border-emerald-800/40 text-emerald-200"
                  : "border-slate-700 text-slate-400"
              }`}
            >
              Tehnic: {data.readiness.technical_ready ? "pregătit" : "parțial"}
            </span>
            <span
              className={`rounded border px-2 py-0.5 text-[10px] font-medium ${
                data.readiness.commercial_ready
                  ? "border-emerald-800/40 text-emerald-200"
                  : "border-amber-800/40 text-amber-200"
              }`}
            >
              Comercial: {data.readiness.commercial_ready ? "pregătit" : "blocat / incomplet"}
            </span>
            <span className="rounded border border-slate-700 px-2 py-0.5 text-[10px] text-slate-400">
              Editare: read-only
            </span>
          </div>
        </div>

        <div
          className={`${PS_SURFACE_INSET} grid gap-2 px-3 py-2 sm:grid-cols-4`}
          data-testid="template-pricing-studio-summary"
        >
          <SummaryStat label="Materiale" value={data.summary.materials} />
          <SummaryStat label="Operații" value={data.summary.machine_operations} />
          <SummaryStat label="Manoperă / servicii" value={data.summary.labor + data.summary.services} />
          <SummaryStat label="Linii CPP" value={data.summary.commercial_lines} />
          <SummaryStat label="Rezolvate" value={data.summary.resolved} />
          <SummaryStat label="Tarif lipsă" value={data.summary.missing} tone="warn" />
          <SummaryStat label="Avertismente" value={data.summary.warnings} tone="warn" />
          <SummaryStat
            label="Registry"
            value={`${data.summary.registry_confirmed}/${data.summary.registry_missing_price}`}
          />
        </div>

        {data.acm_acceptance.applies ? (
          <div
            data-testid="template-pricing-studio-acm"
            className="rounded-lg border border-sky-900/40 bg-sky-950/20 px-3 py-2 text-[12px] text-sky-100/90"
          >
            <p className="font-medium text-sky-100">
              ACM acceptance — shell {data.acm_acceptance.shell_registry_confirmed}/
              {data.acm_acceptance.shell_registry_missing} (confirmed/missing)
            </p>
            <p className="mt-1 text-sky-100/70">
              treatment_commercial_lines_allowed=
              {String(data.acm_acceptance.treatment_commercial_lines_allowed)}
            </p>
            {data.acm_acceptance.policy_ro ? (
              <p className="mt-1 text-[11px] text-sky-100/60">{data.acm_acceptance.policy_ro}</p>
            ) : null}
            {data.acm_acceptance.blockers.length > 0 ? (
              <p className="mt-1 font-mono text-[10px] text-amber-200/80">
                {data.acm_acceptance.blockers.join(" · ")}
              </p>
            ) : null}
          </div>
        ) : null}
      </section>

      <LaborRecipeSection
        items={data.labor_recipes ?? []}
        summary={data.labor_summary}
        ownershipNote={data.labor_ownership_note_ro}
      />

      <div className="flex flex-wrap gap-1" role="tablist" aria-label="Filtru tip rețetă">
        {filters.map((f) => (
          <button
            key={f.id}
            type="button"
            role="tab"
            aria-selected={filter === f.id}
            data-testid={`template-pricing-filter-${f.id}`}
            onClick={() => setFilter(f.id)}
            className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
              filter === f.id
                ? "bg-slate-800/80 text-slate-100 ring-1 ring-slate-600/50"
                : "text-slate-500 hover:bg-slate-900/50 hover:text-slate-300"
            }`}
          >
            {f.label} ({f.count})
          </button>
        ))}
      </div>

      <section
        data-testid="template-pricing-studio-table"
        className="overflow-hidden rounded-xl border border-slate-800/70"
      >
        <div className="grid grid-cols-[minmax(0,1.4fr)_minmax(0,0.8fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/70 bg-slate-950/40 px-3 py-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
          <span>Element</span>
          <span>Cost / rată sursă</span>
          <span>Cantitate</span>
          <span>Pregătire</span>
          <span>Status</span>
        </div>
        {filtered.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-500">Nicio linie în acest filtru.</p>
        ) : (
          filtered.map((row) => <RecipeRow key={row.recipe_item_id} row={row} />)
        )}
      </section>

      <section className={`${PS_SURFACE_PANEL} grid gap-3 px-4 py-4 sm:grid-cols-2`}>
        <div data-testid="template-pricing-cpp-preview">
          <p className="text-[10px] font-semibold uppercase text-slate-500">CPP preview</p>
          <p className="mt-1 text-[12px] text-slate-300">{data.cpp_preview.note_ro}</p>
          <p className="mt-2 font-mono text-[10px] text-slate-500">
            status={data.cpp_preview.status} · lines={data.cpp_preview.line_codes.length}
          </p>
          {data.cpp_preview.line_codes.length > 0 ? (
            <p className="mt-1 line-clamp-3 font-mono text-[10px] text-slate-400">
              {data.cpp_preview.line_codes.join(", ")}
            </p>
          ) : null}
        </div>
        <div data-testid="template-pricing-eic-preview">
          <p className="text-[10px] font-semibold uppercase text-slate-500">EIC proveniență</p>
          <p className="mt-1 text-[12px] text-slate-300">{data.eic_preview.note_ro}</p>
          {data.eic_preview.provenance_notes.map((n) => (
            <p key={n} className="mt-1 text-[11px] text-slate-500">
              {n}
            </p>
          ))}
        </div>
      </section>

      <details className={`${PS_SURFACE_INSET} px-3 py-2`}>
        <summary className="cursor-pointer select-none text-[11px] text-slate-500 hover:text-slate-300">
          Note readiness (tehnic / comercial / stoc)
        </summary>
        <ul className="mt-2 space-y-1 text-[11px] text-slate-400">
          {data.readiness.technical_notes_ro.map((n) => (
            <li key={`t-${n}`}>Tehnic: {n}</li>
          ))}
          {data.readiness.commercial_notes_ro.map((n) => (
            <li key={`c-${n}`}>Comercial: {n}</li>
          ))}
          {data.readiness.inventory_notes_ro.map((n) => (
            <li key={`i-${n}`}>Inventar: {n}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: "warn";
}) {
  return (
    <div>
      <p className="text-[10px] uppercase text-slate-500">{label}</p>
      <p
        className={`text-sm font-semibold ${
          tone === "warn" && Number(value) > 0 ? "text-amber-200" : "text-slate-100"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function LaborRecipeSection({
  items,
  summary,
  ownershipNote,
}: {
  items: TemplateLaborRecipeItem[];
  summary?: TemplatePricingRecipeResponse["labor_summary"];
  ownershipNote?: string;
}) {
  return (
    <section
      data-testid="template-labor-recipe-section"
      className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Manoperă specifică template-ului
          </p>
          <p className="mt-1 max-w-2xl text-[12px] text-slate-400">
            {ownershipNote ||
              "Tarif central în catalog + rețetă (formulă / cantitate) pe template."}
          </p>
        </div>
        {summary ? (
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            <span className="rounded border border-slate-700 px-2 py-0.5 text-slate-300">
              Rețete: {summary.total}
            </span>
            <span className="rounded border border-emerald-900/40 px-2 py-0.5 text-emerald-200/90">
              Tehnic: {summary.technical_ready}
            </span>
            <span className="rounded border border-amber-900/40 px-2 py-0.5 text-amber-200/90">
              Tarif lipsă: {summary.missing_rate}
            </span>
          </div>
        ) : null}
      </div>

      {items.length === 0 ? (
        <p
          data-testid="template-labor-recipe-empty"
          className="text-[12px] text-slate-500"
        >
          Nicio rețetă de manoperă derivabilă din operațiile template-ului.
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-800/70">
          <div className="grid grid-cols-[minmax(0,1.3fr)_minmax(0,0.9fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/70 bg-slate-950/40 px-3 py-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
            <span>Operație</span>
            <span>Formulă / cantitate</span>
            <span>Cost intern</span>
            <span>Tarif comercial</span>
            <span>Status</span>
          </div>
          {items.map((row) => (
            <div
              key={row.labor_recipe_id}
              data-testid={`template-labor-row-${row.operation_code}`}
              className="grid grid-cols-[minmax(0,1.3fr)_minmax(0,0.9fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/50 px-3 py-2.5 text-[12px] text-slate-200 last:border-b-0"
            >
              <div className="min-w-0">
                <p className="truncate font-medium text-slate-100">{row.operator_name}</p>
                <p className="mt-0.5 font-mono text-[10px] text-slate-500">
                  {row.recipe_role} · {row.catalog_code}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-500">{row.labor_class}</p>
                {row.data_quality_message_ro ? (
                  <p className="mt-1 text-[10px] text-amber-200/80">{row.data_quality_message_ro}</p>
                ) : null}
              </div>
              <div>
                <p className="font-mono text-[10px] text-slate-400">
                  {row.formula_id || "—"}
                </p>
                <p className="mt-0.5 font-mono text-[10px] text-slate-500">
                  {row.quantity_keys.length ? row.quantity_keys.join(", ") : "qty —"}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-500">bază: {row.basis}</p>
              </div>
              <div>
                <p className="text-[11px] text-slate-300">
                  {row.internal_cost_rate != null
                    ? `${row.internal_cost_rate}${row.currency ? ` ${row.currency}` : ""}`
                    : "indisponibil"}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-500">{row.unit || "—"}</p>
              </div>
              <div>
                <p className="text-[11px] text-slate-300">
                  {row.commercial_rate_status === "available" && row.commercial_rate != null
                    ? `${row.commercial_rate}${row.currency ? ` ${row.currency}` : ""}`
                    : row.commercial_rate_status}
                </p>
                {row.cpp_line_code ? (
                  <p className="mt-0.5 font-mono text-[10px] text-slate-500">
                    CPP: {row.cpp_line_code}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1 text-right">
                <span className={`rounded border px-1.5 py-0.5 text-[10px] ${statusChip(row.status)}`}>
                  {statusLabel(row.status)}
                </span>
                <p className="text-[10px] text-slate-500">
                  T:{row.technical_ready ? "da" : "nu"} · C:{row.commercial_ready ? "da" : "nu"}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function RecipeRow({ row }: { row: TemplatePricingRecipeItem }) {
  const primaryLink =
    row.source_links.pricing_materiale ||
    row.source_links.pricing_operatii ||
    row.source_links.pricing_manopera ||
    row.source_links.pricing_registry ||
    row.source_links.inventory;

  return (
    <div
      data-testid={`template-pricing-row-${row.stable_code}`}
      className="grid grid-cols-[minmax(0,1.4fr)_minmax(0,0.8fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/50 px-3 py-2.5 text-[12px] text-slate-200 last:border-b-0"
    >
      <div className="min-w-0">
        <p className="truncate font-medium text-slate-100">{row.operator_name}</p>
        <p className="mt-0.5 font-mono text-[10px] text-slate-500">
          {KIND_LABELS[row.recipe_kind]} · {row.stable_code}
          {row.catalog_code && row.catalog_code !== row.stable_code
            ? ` → ${row.catalog_code}`
            : ""}
        </p>
        {primaryLink ? (
          <Link
            to={primaryLink}
            className="mt-1 inline-block text-[10px] text-sky-400/90 hover:text-sky-300"
          >
            Deschide sursa catalog
          </Link>
        ) : null}
        {row.data_quality_message_ro ? (
          <p className="mt-1 text-[10px] text-amber-200/80">{row.data_quality_message_ro}</p>
        ) : null}
      </div>
      <div>
        <p className="text-[11px] text-slate-300">
          {row.cost_label_ro || "—"}
          {row.current_value != null
            ? `: ${row.current_value}${row.currency ? ` ${row.currency}` : ""}`
            : ""}
        </p>
        <p className="mt-0.5 text-[10px] text-slate-500">{row.unit || "—"}</p>
      </div>
      <div>
        <p className="font-mono text-[10px] text-slate-400">
          {row.quantity_keys.length ? row.quantity_keys.join(", ") : "—"}
        </p>
        {row.cpp_line_code ? (
          <p className="mt-0.5 text-[10px] text-slate-500">CPP: {row.cpp_line_code}</p>
        ) : null}
      </div>
      <div className="text-[10px] text-slate-400">
        <p>Tehnic: {row.technical_ready ? "da" : "nu"}</p>
        <p>Comercial: {row.commercial_ready ? "da" : "nu"}</p>
      </div>
      <div>
        <span className={`rounded border px-1.5 py-0.5 text-[10px] ${statusChip(row.status)}`}>
          {statusLabel(row.status)}
        </span>
      </div>
    </div>
  );
}
