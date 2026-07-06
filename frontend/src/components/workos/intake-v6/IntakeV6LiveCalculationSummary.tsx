import type {
  IntakeV6ArtworkFinish,
  IntakeV6LogicalListLineTrace,
  IntakeV6LogicalListReadModelResponse,
  IntakeV6MaterialBreakdownResponse,
  IntakeV6PricedQuoteDryRunResponse,
  IntakeV6PricingInputPreviewResponse,
} from "@/lib/intakeV6/intakeV6Api";
import { formatFaceBackPrepMoney } from "@/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay";
import { INTAKE_V6_PENDING_SAVE_BANNER } from "@/lib/intakeV6/intakeV6FinishHydration";
import { buildIntakeV6LiveMaterialsUsedRows } from "@/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay";
import {
  filterLiveCalcRows,
  resolveLiveCalcFilterOptions,
  sumFilteredLiveCalcRows,
  type LiveCalcFilterId,
} from "@/lib/intakeV6/intakeV6LiveCalculationRowFilters";
import {
  buildIntakeV6OfferModel,
  type IntakeV6OfferCommercialInputs,
} from "@/lib/intakeV6/intakeV6OfferCalculator";
import type { IntakeV6FaceBackPrepCostDraftResponse } from "@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { AlertTriangle, Calculator, ChevronRight, Ruler } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { formatEdgeCantOperatorPerimeter } from "@/lib/intakeV6/intakeV4EdgeCantDisplay";
import { v6 } from "./atoms/intakeV6Presentation";

const RIGHT_PANEL_PREVIEW_LINES = 5;

type LiveCalcDisplayRow = ReturnType<typeof buildIntakeV6LiveMaterialsUsedRows>[number] & {
  category?: string;
  formulaText?: string;
  gapText?: string;
  childCount?: number;
  source?: "logical-list" | "material-breakdown";
};

function joinClassNames(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

function totalCostLabel(value: number | null | undefined, currency: string): string {
  if (value == null || !Number.isFinite(value)) return "tarif lipsă";
  return formatFaceBackPrepMoney(value, currency);
}

function normalizeLogicalCategory(category: string | null | undefined): string {
  if (!category) return "FARA_CATEGORIE";
  return category === "SERVICII / OPERATII" ? "SERVICII_OPERATII" : category;
}

function logicalCategoryLabel(category: string | null | undefined): string {
  const normalized = normalizeLogicalCategory(category);
  if (normalized === "MATERIALE") return "Materiale";
  if (normalized === "SERVICII_OPERATII") return "Servicii / Operații";
  if (normalized === "MANOPERA") return "Manoperă";
  return normalized.replace(/_/g, " ");
}

function formatLogicalQuantity(row: IntakeV6LogicalListLineTrace): string {
  if (row.quantity == null || !Number.isFinite(row.quantity)) return "cantitate lipsă";
  const quantity = Math.round(row.quantity * 10000) / 10000;
  return `${quantity} ${row.unit ?? ""}`.trim();
}

function resolveLogicalStatus(row: IntakeV6LogicalListLineTrace): string {
  if ((row.blockers?.length ?? 0) > 0) return "blocat";
  if ((row.gaps?.length ?? 0) > 0) return "gap explicit";
  if (row.formula_status === "legacy_unversioned") return "legacy";
  if (row.status?.includes("PARTIAL")) return "estimat";
  if (row.status === "MATCHED") return "priced";
  return row.status?.toLowerCase().replace(/_/g, " ") || "read-only";
}

function buildLogicalDisplayRows(logicalList: IntakeV6LogicalListReadModelResponse | null | undefined): LiveCalcDisplayRow[] {
  const rows = logicalList?.rows ?? [];
  return rows.map((row) => {
    const formula = [row.formula_code_proposed, row.formula_version_proposed].filter(Boolean).join(" @ ");
    const gaps = [...(row.gaps ?? []), ...(row.warnings ?? []), ...(row.blockers ?? [])];
    return {
      groupKey: row.line_id,
      label: row.display_label,
      quantityText: formatLogicalQuantity(row),
      costText: resolveLogicalStatus(row),
      muted: (row.gaps?.length ?? 0) > 0 || (row.blockers?.length ?? 0) > 0,
      category: normalizeLogicalCategory(row.category),
      formulaText: formula || "formula lipsă",
      gapText: gaps.length > 0 ? gaps.join(" · ") : "fără gap",
      childCount: row.child_rows?.length ?? 0,
      source: "logical-list",
    } satisfies LiveCalcDisplayRow;
  });
}

function LiveCalcLineList({
  filteredRows,
  activeFilter,
  filterTotals,
  currency,
  logicalMode = false,
}: {
  filteredRows: LiveCalcDisplayRow[];
  activeFilter: LiveCalcFilterId;
  filterTotals: ReturnType<typeof sumFilteredLiveCalcRows>;
  currency: string;
  logicalMode?: boolean;
}) {
  const groups = logicalMode
    ? Array.from(
        filteredRows.reduce((map, row) => {
          const category = row.category ?? "FARA_CATEGORIE";
          const existing = map.get(category) ?? [];
          existing.push(row);
          map.set(category, existing);
          return map;
        }, new Map<string, LiveCalcDisplayRow[]>()),
      )
    : [["", filteredRows] as [string, LiveCalcDisplayRow[]]];

  return (
    <div className="overflow-hidden rounded border border-[#1F2A3D]/90">
      <div className="grid grid-cols-[minmax(0,1fr)_80px_84px] border-b border-[#1F2A3D] bg-[#101827] px-2.5 py-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        <span>Linie</span>
        <span className="text-right">Consum</span>
        <span className="text-right">{logicalMode ? "Status" : "Preț"}</span>
      </div>
      <ul className="divide-y divide-[#1F2A3D]/80 text-[12px]" data-testid="intake-v6-live-materials-list">
        {filteredRows.length === 0 ? (
          <li className="px-2.5 py-2.5 text-[12px] text-slate-400">Nicio linie pentru filtrul selectat.</li>
        ) : (
          groups.map(([category, items]) => (
            <li key={category || "breakdown"} className="contents">
              {logicalMode ? (
                <div
                  className="bg-[#0d1420] px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-cyan-200/80"
                  data-testid={`intake-v6-logical-list-category-${category}`}
                >
                  {logicalCategoryLabel(category)} · {items.length}
                </div>
              ) : null}
              {items.map((item) => (
                <div
                  key={item.groupKey}
                  className="grid grid-cols-[minmax(0,1fr)_80px_84px] items-start gap-2 px-2.5 py-2"
                  data-testid={`intake-v6-live-material-used-${item.groupKey}`}
                >
                  <span className="min-w-0 leading-relaxed text-slate-200" title={item.label}>
                    <span className="block truncate">{item.label}</span>
                    {logicalMode ? (
                      <span className="mt-0.5 block space-y-0.5 text-[10px] leading-snug text-slate-500">
                        <span data-testid={`intake-v6-logical-formula-${item.groupKey}`}>{item.formulaText}</span>
                        <span data-testid={`intake-v6-logical-gaps-${item.groupKey}`}>{item.gapText}</span>
                        <span data-testid={`intake-v6-logical-children-${item.groupKey}`}>
                          child rows: {item.childCount ?? 0}
                        </span>
                      </span>
                    ) : null}
                  </span>
                  <span className="text-right font-mono text-[12px] tabular-nums text-slate-300">{item.quantityText}</span>
                  <span
                    className={joinClassNames(
                      "text-right text-[12px] tabular-nums",
                      logicalMode ? "font-semibold" : "font-mono",
                      item.muted ? "text-amber-200/90" : "text-slate-100",
                    )}
                    data-testid={`intake-v6-live-material-cost-${item.groupKey}`}
                  >
                    {item.costText}
                  </span>
                </div>
              ))}
            </li>
          ))
        )}
      </ul>
      {activeFilter !== "all" && !logicalMode ? (
        <div
          className="flex flex-wrap items-center justify-between gap-2 border-t border-[#1F2A3D] bg-[#0d1420]/80 px-2.5 py-2 text-[11px] text-slate-300"
          data-testid="intake-v6-live-filter-subtotal"
        >
          <span>
            Subtotal filtru:{" "}
            <strong className="font-semibold tabular-nums text-slate-200">
              {formatFaceBackPrepMoney(filterTotals.subtotal, currency)}
            </strong>
          </span>
          <span data-testid="intake-v6-live-filter-line-count">
            Nr. linii: {filterTotals.lineCount}
          </span>
        </div>
      ) : null}
    </div>
  );
}

function CantMetricsStrip({ operatorCantPerimeterM }: { operatorCantPerimeterM?: number | null }) {
  if (operatorCantPerimeterM == null || operatorCantPerimeterM <= 0) return null;
  return (
    <div
      className="mb-2 flex items-center justify-between gap-2 rounded border border-[#243044]/80 bg-[#101827]/60 px-2 py-1.5"
      data-testid="intake-v6-live-cant-metrics"
    >
      <span className="inline-flex items-center gap-1.5">
        <Ruler className="h-3 w-3 shrink-0 text-slate-500" aria-hidden />
        <span className="text-[11px] font-medium text-slate-500">Perimetru cant operator</span>
      </span>
      <span className="font-mono text-[12px] font-semibold tabular-nums text-slate-200">
        {formatEdgeCantOperatorPerimeter(operatorCantPerimeterM)}
      </span>
    </div>
  );
}

function DetailsSheet({
  detailsBody,
  missingRateLabels,
  triggerLabel,
  testId = "intake-v6-price-spine-details",
}: {
  detailsBody: ReactNode;
  missingRateLabels: string[];
  triggerLabel: string;
  testId?: string;
}) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          type="button"
          className="inline-flex w-full items-center justify-center gap-0.5 rounded border border-[#2A3548] bg-[#111827] px-2 py-1.5 text-[12px] font-semibold text-slate-200 hover:border-cyan-500/30"
          data-testid={testId}
        >
          {triggerLabel}
          <ChevronRight className="h-3 w-3" aria-hidden />
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full overflow-y-auto border-[#2A3548] bg-[#0A0F1A] sm:max-w-lg">
        <SheetHeader>
          <SheetTitle className="text-left text-[13px] text-slate-100">Calcul live — detalii</SheetTitle>
          <SheetDescription className="mt-2 text-[10px] leading-relaxed text-slate-500">
            Breakdown intern pe materiale, operații și consumabile. Nu este preț final comercial.
          </SheetDescription>
        </SheetHeader>
        <div className="mt-4">{detailsBody}</div>
        {missingRateLabels.length > 0 ? (
          <ul className="sr-only" data-testid="intake-v6-live-missing-rates-list">
            {missingRateLabels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

export default function IntakeV6LiveCalculationSummary({
  breakdown,
  faceBackDraft,
  loading,
  layout = "sidebar",
  className,
  operatorCantPerimeterM,
  pendingSave = false,
  letterGroups = [],
  artworkFinishes = [],
  pricingPreview = null,
  officialPricing = null,
  logicalList = null,
  commercialInputs = null,
  eurToRonRate = null,
  hideTitle = false,
  artworkOnlyBlocked = false,
}: {
  breakdown: IntakeV6MaterialBreakdownResponse | null;
  faceBackDraft: IntakeV6FaceBackPrepCostDraftResponse | null;
  loading?: boolean;
  layout?: "sidebar" | "bar" | "rightPanel";
  className?: string;
  operatorCantPerimeterM?: number | null;
  pendingSave?: boolean;
  letterGroups?: IntakeV6LetterGroupFinish[];
  artworkFinishes?: IntakeV6ArtworkFinish[];
  pricingPreview?: IntakeV6PricingInputPreviewResponse | null;
  officialPricing?: IntakeV6PricedQuoteDryRunResponse | null;
  logicalList?: IntakeV6LogicalListReadModelResponse | null;
  commercialInputs?: IntakeV6OfferCommercialInputs | null;
  eurToRonRate?: number | null;
  hideTitle?: boolean;
  artworkOnlyBlocked?: boolean;
}) {
  const currency = breakdown?.totals.currency ?? faceBackDraft?.currency ?? "EUR";
  const total = artworkOnlyBlocked
    ? null
    : breakdown?.totals.estimated_cost_total ?? breakdown?.totals.material_cost_total ?? null;
  const missingPrices = artworkOnlyBlocked ? false : breakdown?.totals.contains_missing_prices === true;
  const isBar = layout === "bar";
  const isRightPanel = layout === "rightPanel";
  const breakdownRows = buildIntakeV6LiveMaterialsUsedRows({
    breakdown,
    operatorCantPerimeterM,
    letterGroups,
    artworkFinishes,
    currency,
  });
  const logicalRows = useMemo(() => buildLogicalDisplayRows(logicalList), [logicalList]);
  const usesLogicalList = logicalRows.length > 0;
  const rows: LiveCalcDisplayRow[] = usesLogicalList ? logicalRows : breakdownRows.map((row) => ({ ...row, source: "material-breakdown" }));
  const logicalRowCount = logicalList?.core_row_count ?? logicalRows.length;
  const logicalTargetRowCount = logicalList?.target_core_row_count ?? null;
  const [materialsOpen, setMaterialsOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<LiveCalcFilterId>("all");
  const offerModel =
    !artworkOnlyBlocked && pricingPreview && commercialInputs
      ? buildIntakeV6OfferModel({
          preview: pricingPreview,
          breakdown,
          commercialInputs,
          eurToRonRate,
        })
      : null;
  const officialTotals = officialPricing?.commercial_totals ?? null;
  const hasOfficialTotals =
    officialPricing?.pricing_status === "V6_PRICED_DRY_RUN_READY" &&
    officialTotals?.subtotal_net != null &&
    officialTotals?.total_gross != null;
  const displayGrossRon = hasOfficialTotals ? officialTotals.total_gross : offerModel?.totalGross ?? null;
  const displayNetRon = hasOfficialTotals ? officialTotals.subtotal_net : offerModel?.subtotalNet ?? null;
  const filteredRows = useMemo(
    () => filterLiveCalcRows(rows, activeFilter),
    [rows, activeFilter],
  );
  const filterOptions = useMemo(() => resolveLiveCalcFilterOptions(rows), [rows]);
  const filterTotals = useMemo(() => sumFilteredLiveCalcRows(filteredRows), [filteredRows]);
  const previewRows = isRightPanel && !usesLogicalList ? filteredRows.slice(0, RIGHT_PANEL_PREVIEW_LINES) : filteredRows;
  const hiddenPreviewCount = Math.max(0, filteredRows.length - previewRows.length);
  const missingRateLabels = rows
    .filter((row) => row.muted || row.costText === "tarif lipsă")
    .map((row) => row.label);
  const visibleMissingRateLabels = missingRateLabels.slice(0, 2);
  const hiddenMissingRateCount = Math.max(0, missingRateLabels.length - visibleMissingRateLabels.length);

  useEffect(() => {
    if (activeFilter === "missing_rates" && !filterOptions.some((opt) => opt.id === "missing_rates")) {
      setActiveFilter("all");
    }
  }, [activeFilter, filterOptions]);

  const filterChips = (
    <div
      className={joinClassNames("flex flex-wrap gap-1", isBar ? "" : "mb-2")}
      data-testid="intake-v6-live-calc-filters"
      role="group"
      aria-label="Filtre calcul live"
    >
      {filterOptions.map((option) => {
        const active = activeFilter === option.id;
        return (
          <button
            key={option.id}
            type="button"
            className={joinClassNames(
              "rounded border px-2 py-1 text-[11px] font-semibold uppercase tracking-wide transition",
              active
                ? "border-cyan-500/40 bg-cyan-500/15 text-cyan-200"
                : "border-[#2A3548] bg-[#111827] text-slate-400 hover:border-slate-500/40 hover:text-slate-200",
            )}
            onClick={() => setActiveFilter(option.id)}
            data-testid={`intake-v6-live-filter-${option.id}`}
            aria-pressed={active}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );

  const detailsBody = (
    <>
      <CantMetricsStrip operatorCantPerimeterM={operatorCantPerimeterM} />
      {artworkOnlyBlocked ? (
        <p
          className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1.5 text-[11px] leading-relaxed text-amber-100/90"
          data-testid="intake-v6-live-artwork-only-blocked"
        >
          Nu există straturi de litere confirmate. Artwork-only necesită decizie operator.
        </p>
      ) : null}
      {pendingSave ? (
        <p
          className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1.5 text-[11px] text-amber-100/90"
          data-testid="intake-v6-live-pending-save"
        >
          {INTAKE_V6_PENDING_SAVE_BANNER}
        </p>
      ) : null}
      {filterChips}
      {usesLogicalList ? (
        <p
          className="mb-2 rounded border border-cyan-500/20 bg-cyan-500/5 px-2 py-1.5 text-[11px] text-cyan-100/85"
          data-testid="intake-v6-logical-list-summary"
        >
          Lista logică read-model · {logicalRowCount}{logicalTargetRowCount ? `/${logicalTargetRowCount}` : ""} rânduri · material breakdown în detalii tehnice.
        </p>
      ) : null}
      {loading ? (
        <p className="text-[11px] text-slate-400">Actualizez estimările…</p>
      ) : rows.length > 0 ? (
        <LiveCalcLineList
          filteredRows={filteredRows}
          activeFilter={activeFilter}
          filterTotals={filterTotals}
          currency={currency}
          logicalMode={usesLogicalList}
        />
      ) : (
        <p className="text-[11px] text-slate-400">Nu există încă breakdown live.</p>
      )}
    </>
  );

  if (isBar) {
    return (
      <div
        className={joinClassNames(
          "sticky top-0 z-10 rounded-md border border-[#2A3548]/90 bg-[#0A0F1A]/95 backdrop-blur-sm",
          className,
        )}
        data-testid="intake-v6-live-calculation-summary"
        data-layout={layout}
        data-price-spine="true"
      >
        <div
          className="flex flex-wrap items-center gap-x-4 gap-y-2 px-3 py-2"
          data-testid="intake-v6-price-spine-bar"
        >
          <Calculator className="h-4 w-4 shrink-0 text-cyan-400/80" aria-hidden />

          <div className="min-w-0" data-testid="intake-v6-live-totals-summary">
            <span className="block text-[11px] text-slate-500">Cost intern referință</span>
            <span
              className="text-[13px] font-semibold tabular-nums text-slate-200"
              data-testid="intake-v6-live-material-total"
            >
              {artworkOnlyBlocked ? "indisponibil" : totalCostLabel(total, currency)}
            </span>
          </div>

          {displayGrossRon != null && displayNetRon != null ? (
            <div className="min-w-0 border-l border-[#243044]/70 pl-4">
              <span className="block text-[11px] text-slate-500">
                {hasOfficialTotals ? "Preț oficial cu TVA" : "Total cu TVA"}
              </span>
              <span
                className="text-[22px] font-bold tabular-nums leading-none text-emerald-300"
                data-testid="intake-v6-live-offer-gross"
              >
                {formatFaceBackPrepMoney(displayGrossRon, "RON")}
              </span>
              <span
                className="ml-2 text-[11px] tabular-nums text-cyan-200/80"
                data-testid="intake-v6-live-offer-net"
              >
                net {formatFaceBackPrepMoney(displayNetRon, "RON")}
              </span>
            </div>
          ) : null}

          {missingPrices || missingRateLabels.length > 0 ? (
            <span
              className="inline-flex items-center gap-1 rounded border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-200"
              data-testid="intake-v6-live-missing-rates-banner"
            >
              <AlertTriangle className="h-3 w-3 shrink-0" aria-hidden />
              {missingRateLabels.length > 0
                ? `${missingRateLabels.length} tarif${missingRateLabels.length === 1 ? "" : "e"} lipsă`
                : "Tarife lipsă"}
            </span>
          ) : null}

          {pendingSave ? (
            <span className="text-[11px] text-amber-200/90" data-testid="intake-v6-live-pending-save-inline">
              Salvare…
            </span>
          ) : null}

          <div className="ml-auto flex flex-wrap items-center gap-2">
            {filterOptions.slice(0, 4).map((option) => (
              <button
                key={option.id}
                type="button"
                className={joinClassNames(
                  "rounded border px-2 py-1 text-[11px] font-semibold transition",
                  activeFilter === option.id
                    ? "border-cyan-500/40 bg-cyan-500/15 text-cyan-200"
                    : "border-[#2A3548] text-slate-400 hover:text-slate-200",
                )}
                onClick={() => setActiveFilter(option.id)}
                data-testid={`intake-v6-live-filter-${option.id}`}
              >
                {option.label}
              </button>
            ))}

            <DetailsSheet
              detailsBody={detailsBody}
              missingRateLabels={missingRateLabels}
              triggerLabel="Detalii"
            />
          </div>
        </div>
      </div>
    );
  }

  if (isRightPanel) {
    return (
      <aside
        className={joinClassNames(
          "rounded-md border border-[#2A3548]/90 bg-[#0A0F1A]/90 p-2.5",
          className,
        )}
        data-testid="intake-v6-review-calculator-panel"
        data-layout={layout}
      >
        <div className="mb-2 flex items-center gap-1.5">
          <Calculator className="h-3.5 w-3.5 text-cyan-400/80" aria-hidden />
          <h3 className="text-[12px] font-semibold text-slate-100">Calcul live</h3>
        </div>

        <div
          className="mb-2 rounded-md border border-[#243044]/80 bg-[#101827]/90 px-2.5 py-2"
          data-testid="intake-v6-live-totals-summary"
        >
          {displayGrossRon != null && displayNetRon != null ? (
            <>
              <span className="block text-[11px] text-slate-500">
                {hasOfficialTotals ? "Preț oficial cu TVA" : "Total cu TVA"}
              </span>
              <span
                className="mt-0.5 block text-[24px] font-bold tabular-nums leading-none text-emerald-300"
                data-testid="intake-v6-live-offer-gross"
              >
                {formatFaceBackPrepMoney(displayGrossRon, "RON")}
              </span>
              <div className="mt-2 flex items-baseline justify-between gap-2 border-t border-[#243044]/60 pt-2 text-[11px]">
                <span className="text-slate-500">Net</span>
                <span className="tabular-nums text-cyan-200" data-testid="intake-v6-live-offer-net">
                  {formatFaceBackPrepMoney(displayNetRon, "RON")}
                </span>
              </div>
            </>
          ) : null}
          <div
            className={joinClassNames(
              "flex items-baseline justify-between gap-2",
              displayGrossRon != null && displayNetRon != null ? "mt-1.5" : "",
            )}
          >
            <span className="text-[11px] text-slate-500">Cost intern referință</span>
            <span
              className="text-[12px] font-semibold tabular-nums text-slate-200"
              data-testid="intake-v6-live-material-total"
            >
              {totalCostLabel(total, currency)}
            </span>
          </div>
        </div>

        {pendingSave ? (
          <p
            className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1.5 text-[11px] text-amber-100/90"
            data-testid="intake-v6-live-pending-save"
          >
            {INTAKE_V6_PENDING_SAVE_BANNER}
          </p>
        ) : null}

        {missingPrices || missingRateLabels.length > 0 ? (
          <div
            className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1.5 text-[11px] text-amber-100/85"
            data-testid="intake-v6-live-missing-rates-banner"
          >
            <span className="font-medium">Tarife lipsă</span>
            {visibleMissingRateLabels.length > 0 ? (
              <span className="text-amber-100/75">
                {" "}
                — {visibleMissingRateLabels.join("; ")}
                {hiddenMissingRateCount > 0 ? ` (+${hiddenMissingRateCount})` : ""}
              </span>
            ) : null}
          </div>
        ) : null}

        {loading ? (
          <p className="mb-2 text-[11px] text-slate-400">Actualizez estimările…</p>
        ) : rows.length > 0 ? (
          <div data-testid="intake-v6-live-materials-used">
            {usesLogicalList ? (
              <p
                className="mb-2 rounded border border-cyan-500/20 bg-cyan-500/5 px-2 py-1.5 text-[11px] text-cyan-100/85"
                data-testid="intake-v6-logical-list-summary"
              >
                Lista logică read-model · {logicalRowCount}{logicalTargetRowCount ? `/${logicalTargetRowCount}` : ""} rânduri
              </p>
            ) : null}
            {filterChips}
            <LiveCalcLineList
              filteredRows={previewRows}
              activeFilter={activeFilter}
              filterTotals={filterTotals}
              currency={currency}
              logicalMode={usesLogicalList}
            />
            {hiddenPreviewCount > 0 ? (
              <p className="mt-1.5 text-[11px] text-slate-400" data-testid="intake-v6-live-preview-more">
                +{hiddenPreviewCount} linii în detaliu
              </p>
            ) : null}
            <div className="mt-2">
              <DetailsSheet
                detailsBody={detailsBody}
                missingRateLabels={missingRateLabels}
                triggerLabel={`Detalii (${filteredRows.length} linii)`}
                testId="intake-v6-review-calculator-details"
              />
            </div>
          </div>
        ) : (
          <p className="text-[11px] text-slate-400">Nu există încă breakdown live.</p>
        )}
      </aside>
    );
  }

  return (
    <aside
      className={joinClassNames(
        "rounded-md border border-[#2A3548]/90 bg-[#0A0F1A]/90 p-2.5",
        className,
      )}
      data-testid="intake-v6-live-calculation-summary"
      data-layout={layout}
    >
      {!hideTitle ? (
        <div className="mb-2">
          <h3 className="text-[12px] font-bold uppercase tracking-wide text-slate-200">Calcul live</h3>
          <p className="mt-0.5 text-[11px] text-slate-500">Materiale, consumabile și operații estimate</p>
        </div>
      ) : null}

      <div
        className="mb-2 rounded-md border border-[#243044]/80 bg-[#101827]/90 px-2.5 py-2"
        data-testid="intake-v6-live-totals-summary"
      >
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Total intern
          </span>
          <span
            className="text-[15px] font-bold tabular-nums text-slate-50"
            data-testid="intake-v6-live-material-total"
          >
            {totalCostLabel(total, currency)}
          </span>
        </div>
        {displayGrossRon != null && displayNetRon != null ? (
          <>
            <div className="mt-1.5 flex items-baseline justify-between gap-2 border-t border-[#243044]/60 pt-1.5">
              <span className="text-[11px] uppercase tracking-wide text-slate-500">Total net</span>
              <span
                className="text-[13px] font-semibold tabular-nums text-cyan-200"
                data-testid="intake-v6-live-offer-net"
              >
                {formatFaceBackPrepMoney(displayNetRon, "RON")}
              </span>
            </div>
            <div className="mt-1 flex items-baseline justify-between gap-2">
              <span className="text-[11px] uppercase tracking-wide text-slate-500">
                {hasOfficialTotals ? "Preț oficial cu TVA" : "Total cu TVA"}
              </span>
              <span
                className="text-[14px] font-bold tabular-nums text-emerald-300"
                data-testid="intake-v6-live-offer-gross"
              >
                {formatFaceBackPrepMoney(displayGrossRon, "RON")}
              </span>
            </div>
          </>
        ) : null}
      </div>

      {pendingSave ? (
        <p
          className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1.5 text-[11px] text-amber-100/90"
          data-testid="intake-v6-live-pending-save"
        >
          {INTAKE_V6_PENDING_SAVE_BANNER}
        </p>
      ) : null}

      {missingPrices || missingRateLabels.length > 0 ? (
        <div
          className="mb-2 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1.5 text-[11px] text-amber-100/85"
          data-testid="intake-v6-live-missing-rates-banner"
        >
          <p>
            <span className="font-medium">Tarife lipsă</span>
            {visibleMissingRateLabels.length > 0 ? (
              <span className="text-amber-100/75">
                {" "}
                — {visibleMissingRateLabels.join("; ")}
                {hiddenMissingRateCount > 0 ? ` (+${hiddenMissingRateCount})` : ""}
              </span>
            ) : null}
          </p>
          {visibleMissingRateLabels.length > 0 ? (
            <ul className="sr-only" data-testid="intake-v6-live-missing-rates-list">
              {missingRateLabels.map((label) => (
                <li key={label}>{label}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {loading ? (
        <p className="text-[11px] text-slate-400">Actualizez estimările…</p>
      ) : rows.length > 0 ? (
        <div data-testid="intake-v6-live-materials-used">
          {usesLogicalList ? (
            <p
              className="mb-2 rounded border border-cyan-500/20 bg-cyan-500/5 px-2 py-1.5 text-[11px] text-cyan-100/85"
              data-testid="intake-v6-logical-list-summary"
            >
              Lista logică read-model · {logicalRowCount}{logicalTargetRowCount ? `/${logicalTargetRowCount}` : ""} rânduri
            </p>
          ) : null}
          {filterChips}

          <button
            type="button"
            className="mb-2 flex w-full items-center justify-between text-left lg:hidden"
            onClick={() => setMaterialsOpen((open) => !open)}
            data-testid="intake-v6-live-materials-used-toggle"
            aria-expanded={materialsOpen}
          >
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-300">
              Detalii linii ({filteredRows.length})
            </span>
            <span className="text-[11px] text-slate-400">{materialsOpen ? "−" : "+"}</span>
          </button>

          <div className={joinClassNames(materialsOpen ? "block" : "hidden lg:block")}>
            <LiveCalcLineList
              filteredRows={filteredRows}
              activeFilter={activeFilter}
              filterTotals={filterTotals}
              currency={currency}
              logicalMode={usesLogicalList}
            />
          </div>
        </div>
      ) : (
        <p className="text-[11px] text-slate-400">Nu există încă breakdown live.</p>
      )}
    </aside>
  );
}
