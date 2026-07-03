import type { IntakeV6MaterialBreakdownResponse } from "@/lib/intakeV6/intakeV6Api";
import {
  formatIntakeV6MaterialRowConfidenceLabel,
  formatIntakeV6QuantityBasisLabel,
  INTAKE_V6_SHEET_NESTING_FLOOR_HINT,
  shouldUseSheetNestingFloorConfidenceLabel,
} from "@/lib/intakeV6/intakeV6QuantityBasisLabels";
import {
  formatIntakeV6PricingQuantity,
  formatIntakeV6Quantity,
} from "@/lib/intakeV6/intakeV6QuantityDisplay";
import { INTAKE_V6_PENDING_SAVE_BANNER } from "@/lib/intakeV6/intakeV6FinishHydration";
import {
  dedupeExternalRasterWarnings,
  formatGroupedWarningLine,
  formatIntakeV6LinearQuantityDisplay,
  formatOperationPricingMissingLabel,
  groupIntakeV6Warnings,
  INTAKE_V6_MATERIAL_ESTIMATE_DISCLAIMER,
  sanitizeOperatorDisplayText,
  splitMaterialBreakdownOperationRows,
} from "@/lib/intakeV6/intakeV6OperatorUiDisplay";
import {
  resolveSheetQuoteReviewStatus,
  SHEET_QUOTE_REVIEW_STATUS_LABELS,
  SHEET_QUOTE_SELECTED_QUANTITY_EXPLANATION,
} from "@/lib/intakeV6/intakeV6SheetQuoteReviewDisplay";
import type { IntakeV6SheetFootprintOverride } from "@/lib/intakeV6/intakeV6SheetFootprintOverride";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";
import IntakeV6SheetQuoteReviewPanel from "./IntakeV6SheetQuoteReviewPanel";
import IntakeV6NestingPreviewPanel from "./IntakeV6NestingPreviewPanel";
import IntakeV6EdgeCantQuoteImpactPanel from "./IntakeV6EdgeCantQuoteImpactPanel";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";
import { buildIntakeV6EdgeCantViewModel } from "@/lib/intakeV6/intakeV6EdgeCantDisplay";
import {
  INTAKE_V6_ANALYSIS_BUNDLE_PENDING_MESSAGE,
  isIntakeV6MaterialBreakdownEffectivelyEmpty,
} from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";

function formatUnitPrice(row: IntakeV6MaterialBreakdownResponse["material_rows"][number]): string {
  if (row.unit_price == null) {
    if (row.price_source === "missing") {
      return "lipsă — /inventory/pricing";
    }
    return "—";
  }
  const isOwnerConsumable = /^intake_v\d+_owner_consumable/.test(row.price_source ?? "");
  const decimals = isOwnerConsumable ? 1 : undefined;
  const price =
    decimals != null ? row.unit_price.toFixed(decimals) : String(row.unit_price);
  const unitSuffix = row.unit === "ml" ? "/ml" : row.unit === "m2" ? "/m²" : `/${row.unit}`;
  return `${price} ${row.currency}${unitSuffix}`;
}

const SHEET_FLOOR_MATERIAL_KEYS = new Set(["plexiglas_face", "forex_backing"]);

function MaterialTable({
  title,
  rows,
  testId,
  sheetNestingFloorApplied,
}: {
  title: string;
  rows: IntakeV6MaterialBreakdownResponse["material_rows"];
  testId: string;
  sheetNestingFloorApplied: boolean;
}) {
  if (rows.length === 0) return null;
  return (
    <div className="mb-4" data-testid={testId}>
      <h4 className="mb-2 text-[12px] font-bold uppercase tracking-wide text-slate-300">{title}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-[12px] leading-relaxed">
          <thead>
            <tr className="border-b border-[#2A3548] text-left text-[11px] text-slate-400">
              <th className="py-2 pr-3">Material</th>
              <th className="py-2 pr-3">Cantitate calculată</th>
              <th className="py-2 pr-3">Pentru preț</th>
              <th className="py-2 pr-3">Preț unit.</th>
              <th className="py-2">Cost est. ofertă</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.material_key} className="border-b border-[#2A3548]/60">
                <td className="py-2.5 pr-3 text-slate-100">
                  <div className="font-medium">{sanitizeOperatorDisplayText(row.display_name)}</div>
                  {row.material_code ?? row.registry_code ? (
                    <div className={v6.mono + " text-[11px] text-slate-400"}>
                      {row.material_code ?? row.registry_code}
                    </div>
                  ) : null}
                  {SHEET_FLOOR_MATERIAL_KEYS.has(row.material_key) && sheetNestingFloorApplied ? (
                    <div
                      className="text-[11px] leading-relaxed text-slate-400"
                      data-testid={`intake-v6-selected-qty-explainer-${row.material_key}`}
                    >
                      {SHEET_QUOTE_SELECTED_QUANTITY_EXPLANATION}
                    </div>
                  ) : null}
                  {row.quantity_basis ? (
                    <div className="text-[11px] leading-relaxed text-slate-500" data-testid={`intake-v6-basis-${row.material_key}`}>
                      {formatIntakeV6QuantityBasisLabel(row.quantity_basis)}
                      {row.confidence
                        ? ` · ${formatIntakeV6MaterialRowConfidenceLabel(row.confidence, {
                            sheetNestingFloorApplied,
                            quantityBasis: row.quantity_basis,
                            quantitySource: row.quantity_source,
                            materialKey: row.material_key,
                          })}`
                        : ""}
                    </div>
                  ) : null}
                  {shouldUseSheetNestingFloorConfidenceLabel({
                    sheetNestingFloorApplied,
                    confidence: row.confidence,
                    quantityBasis: row.quantity_basis,
                    quantitySource: row.quantity_source,
                    materialKey: row.material_key,
                  }) ? (
                    <div
                      className="text-[11px] leading-relaxed text-slate-400"
                      data-testid={`intake-v6-floor-hint-${row.material_key}`}
                      title={INTAKE_V6_SHEET_NESTING_FLOOR_HINT}
                    >
                      {INTAKE_V6_SHEET_NESTING_FLOOR_HINT}
                    </div>
                  ) : null}
                  {row.quantity_source?.includes("shared_edge_cant_rules") ? (
                    <div
                      className="text-[11px] leading-relaxed text-slate-500"
                      data-testid={`intake-v6-source-${row.material_key}`}
                    >
                      {row.quantity_source.split("|")[0]}
                    </div>
                  ) : null}
                  {row.warnings.length > 0 ? (
                    <div className="text-[11px] leading-relaxed text-slate-400" data-testid={`intake-v6-row-warnings-${row.material_key}`}>
                      {row.warnings.join(" · ")}
                    </div>
                  ) : null}
                </td>
                <td className="py-2.5 pr-3 text-slate-200">
                  {formatIntakeV6Quantity(row.base_quantity ?? row.quantity, row.unit, {
                    materialKey: row.material_key,
                    displayName: row.display_name,
                  })}
                </td>
                <td className="py-2.5 pr-3 text-slate-200">
                  {formatIntakeV6PricingQuantity(
                    row.base_quantity ?? row.quantity,
                    row.priced_quantity ?? row.quantity_with_waste,
                    row.unit,
                    row.waste_percent,
                    { materialKey: row.material_key, displayName: row.display_name },
                  )}
                </td>
                <td className="py-2.5 pr-3 text-slate-200" data-testid={`intake-v6-material-price-${row.material_key}`}>
                  {row.unit_price != null ? (
                    formatUnitPrice(row)
                  ) : row.price_source === "missing" ? (
                    <span className="text-amber-300" title="Completează în /inventory/pricing">
                      lipsă — /inventory/pricing
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="py-2.5 font-medium text-slate-100">
                  {row.estimated_cost ?? row.material_cost != null ? (
                    <span>{(row.estimated_cost ?? row.material_cost)!.toFixed(2)} {row.currency}</span>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function IntakeV6MaterialBreakdownPanel({
  breakdown,
  loading,
  pendingSave,
  analysisBundlePending,
  workspaceId,
  workspaceTitle,
  templateCode,
  sheetQuoteOverride,
  onSheetFootprintOverrideSaved,
}: {
  breakdown: IntakeV6MaterialBreakdownResponse | null;
  loading: boolean;
  pendingSave?: boolean;
  analysisBundlePending?: boolean;
  workspaceId?: string;
  workspaceTitle?: string | null;
  templateCode?: string | null;
  sheetQuoteOverride?: IntakeV6SheetFootprintOverride | null;
  onSheetFootprintOverrideSaved?: () => void;
}) {
  if (loading) {
    return (
      <div className={v6.card} data-testid="intake-v6-material-breakdown">
        <p className="text-[12px] text-slate-400">Calculez cost materiale pentru ofertă…</p>
      </div>
    );
  }
  if (!breakdown) {
    return (
      <div className={v6.card} data-testid="intake-v6-material-breakdown">
        {analysisBundlePending ? (
          <p
            className="rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[12px] text-amber-100"
            data-testid="intake-v6-breakdown-analysis-bundle-pending"
          >
            {INTAKE_V6_ANALYSIS_BUNDLE_PENDING_MESSAGE}
          </p>
        ) : (
          <p className="text-[12px] text-slate-400">Cost materiale pentru ofertă indisponibil.</p>
        )}
      </div>
    );
  }

  const effectivelyEmpty = isIntakeV6MaterialBreakdownEffectivelyEmpty(breakdown);

  const scopeLabel = breakdown.costing_purpose ?? breakdown.breakdown_scope;

  const mainMaterialRows = breakdown.material_rows.filter(
    (row) => row.material_key !== "edge_cant_oracal_651",
  );
  const oracalCantRow = breakdown.material_rows.find((row) => row.material_key === "edge_cant_oracal_651");
  const cantAdhesiveRows = breakdown.consumable_rows.filter(
    (row) => row.material_key === "adhesive_return_to_face",
  );
  const otherConsumableRows = breakdown.consumable_rows.filter(
    (row) => row.material_key !== "adhesive_return_to_face",
  );

  const sheetNestingFloorApplied = breakdown.warnings.some(
    (warning) => warning.code === "sheet_nesting_quantity_floor_applied",
  );

  const edgeCantModel = buildIntakeV6EdgeCantViewModel({ finish: null, breakdown });
  const { cncRows, printRows } = splitMaterialBreakdownOperationRows(breakdown.operation_rows);
  const groupedWarnings = groupIntakeV6Warnings(breakdown.warnings);
  const operatorWarnings = dedupeExternalRasterWarnings(
    groupedWarnings
      .filter((item) => item.group === "operator")
      .map(formatGroupedWarningLine),
  );
  const quotingWarnings = groupedWarnings
    .filter((item) => item.group === "quoting")
    .map(formatGroupedWarningLine);
  const technicalWarnings = groupedWarnings
    .filter((item) => item.group === "technical")
    .map(formatGroupedWarningLine);
  const sheetQuoteCandidates = breakdown.sheet_quote_material_candidates;
  const ownerReviewStatus = resolveSheetQuoteReviewStatus(sheetQuoteCandidates);

  function renderOperationRows(
    rows: NonNullable<IntakeV6MaterialBreakdownResponse["operation_rows"]>,
    testId: string,
    quantityContext: "cnc" | "cant",
  ) {
    return (
      <ul className="space-y-2 text-[12px] leading-relaxed">
        {rows.map((row) => (
          <li
            key={row.key}
            className="flex flex-wrap items-start justify-between gap-2 border-b border-[#2A3548]/60 py-2.5"
            data-testid={`${testId}-${row.key}`}
          >
            <span className="min-w-0 text-slate-100">
              {sanitizeOperatorDisplayText(row.display_name)}
              {row.passes != null && row.passes > 1 ? (
                <span className="block text-[11px] text-slate-400">
                  {formatIntakeV6LinearQuantityDisplay(row.quantity, row.unit, quantityContext)} ×{" "}
                  {row.passes} treceri
                  {row.operation_equivalent_quantity != null
                    ? ` → ${formatIntakeV6LinearQuantityDisplay(
                        row.operation_equivalent_quantity,
                        row.operation_equivalent_unit ?? "m",
                        "machine_pass",
                      )}`
                    : ""}
                </span>
              ) : (
                <span className="block text-[11px] text-slate-400">
                  {formatIntakeV6LinearQuantityDisplay(row.quantity, row.unit, quantityContext)}
                </span>
              )}
            </span>
            <span className="font-medium tabular-nums text-slate-200">
              {row.estimated_cost != null
                ? `${row.estimated_cost.toFixed(2)} EUR`
                : formatOperationPricingMissingLabel(row.operation_type)}
            </span>
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className={v6.card} data-testid="intake-v6-material-breakdown">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-[12px] font-bold uppercase tracking-wide" data-testid="intake-v6-quote-material-costing">
            Estimare internă materiale — informativ
          </h3>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-400">
            {INTAKE_V6_MATERIAL_ESTIMATE_DISCLAIMER} Nesting = estimare, nu consum stoc.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <AtomsBadge tone="muted">{scopeLabel}</AtomsBadge>
          {breakdown.totals.contains_missing_prices ? (
            <span data-testid="intake-v6-missing-prices-badge">
              <AtomsBadge tone="pending">prețuri lipsă — /inventory/pricing</AtomsBadge>
            </span>
          ) : null}
        </div>
      </div>

      {pendingSave ? (
        <p
          className="mb-3 rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100"
          data-testid="intake-v6-breakdown-pending-save"
        >
          {INTAKE_V6_PENDING_SAVE_BANNER}
        </p>
      ) : null}

      {effectivelyEmpty && analysisBundlePending ? (
        <p
          className="mb-3 rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100"
          data-testid="intake-v6-breakdown-analysis-bundle-pending"
        >
          {INTAKE_V6_ANALYSIS_BUNDLE_PENDING_MESSAGE}
        </p>
      ) : null}

      {breakdown.nesting_rows.length > 0 ? (
        <IntakeV6TechnicalDetailsAccordion testId="intake-v6-nesting-technical">
          <div data-testid="intake-v6-nesting-summary">
            <h4 className="mb-2 text-[12px] font-bold uppercase tracking-wide text-slate-300">
              Nesting nest2 (comparație — nu consum stoc)
            </h4>
            <ul className="space-y-2 text-[12px] leading-relaxed">
              {breakdown.nesting_rows.map((row) => (
                <li
                  key={row.material_key}
                  className="flex flex-wrap items-center justify-between gap-2 border-b border-[#2A3548]/60 py-2.5"
                >
                  <span className="text-slate-100">{sanitizeOperatorDisplayText(row.display_name)}</span>
                  <span className="tabular-nums text-slate-300">
                    {formatIntakeV6Quantity(row.quantity, row.unit, {
                      materialKey: row.material_key,
                      displayName: row.display_name,
                    })}
                    {row.efficiency_percent != null ? ` · ${row.efficiency_percent.toFixed(0)}% eff` : ""}
                    {row.sheets_used != null ? ` · ${row.sheets_used} plăci` : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <IntakeV6NestingPreviewPanel preview={breakdown.nesting_preview} />
        </IntakeV6TechnicalDetailsAccordion>
      ) : null}

      {sheetQuoteCandidates ? (
        <div
          className="mb-3 rounded border border-[#2A3548] bg-[#0A0F1A]/40 px-3 py-2"
          data-testid="intake-v6-owner-review-banner"
        >
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Status review material placă
          </p>
          <p className="mt-1 text-[12px] font-semibold text-slate-100">
            {SHEET_QUOTE_REVIEW_STATUS_LABELS[ownerReviewStatus]}
          </p>
        </div>
      ) : null}

      {sheetQuoteCandidates ? (
        <IntakeV6SheetQuoteReviewPanel
          candidates={sheetQuoteCandidates}
          workspaceId={workspaceId}
          workspaceTitle={workspaceTitle}
          templateCode={templateCode}
          sheetQuoteOverride={sheetQuoteOverride}
          onSheetFootprintOverrideSaved={onSheetFootprintOverrideSaved}
        />
      ) : null}

      <MaterialTable
        title="Materiale"
        rows={mainMaterialRows}
        testId="intake-v6-material-rows"
        sheetNestingFloorApplied={sheetNestingFloorApplied}
      />
      {oracalCantRow ? (
        <MaterialTable
          title="Materiale — Oracal 651 cant / volum"
          rows={[oracalCantRow]}
          testId="intake-v6-oracal-cant-material-rows"
          sheetNestingFloorApplied={sheetNestingFloorApplied}
        />
      ) : null}
      {edgeCantModel.oracal651.present ? (
        <IntakeV6EdgeCantQuoteImpactPanel oracal={edgeCantModel.oracal651} className="mb-4" />
      ) : null}
      {cantAdhesiveRows.length > 0 ? (
        <MaterialTable
          title="Consumabile — adeziv cant"
          rows={cantAdhesiveRows}
          testId="intake-v6-cant-adhesive-rows"
          sheetNestingFloorApplied={sheetNestingFloorApplied}
        />
      ) : null}
      {otherConsumableRows.length > 0 ? (
        <MaterialTable
          title="Consumabile (LED, PSU, cabluri…)"
          rows={otherConsumableRows}
          testId="intake-v6-consumable-rows"
          sheetNestingFloorApplied={sheetNestingFloorApplied}
        />
      ) : null}

      {cncRows.length > 0 ? (
        <div className="mb-4" data-testid="intake-v6-cnc-operation-rows">
          <h4 className="mb-2 text-[12px] font-bold uppercase tracking-wide text-slate-300">
            Operații CNC — preview ofertare
          </h4>
          {renderOperationRows(cncRows, "intake-v6-cnc-op", "cnc")}
        </div>
      ) : null}

      {printRows.length > 0 ? (
        <div className="mb-4" data-testid="intake-v6-print-operation-rows">
          <h4 className="mb-2 text-[12px] font-bold uppercase tracking-wide text-slate-300">
            Operații print / laminare / colantare — preview ofertare
          </h4>
          {renderOperationRows(printRows, "intake-v6-print-op", "cnc")}
        </div>
      ) : null}

      {(breakdown.edge_cant_operation_rows?.length ?? 0) > 0 ? (
        <div className="mb-4" data-testid="intake-v6-edge-cant-operation-rows">
          <h4 className="mb-2 text-[12px] font-bold uppercase tracking-wide text-slate-300">
            Operații cant / volum — preview ofertare
          </h4>
          {renderOperationRows(breakdown.edge_cant_operation_rows!, "intake-v6-edge-cant-op", "cant")}
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#2A3548] pt-3 text-[12px]">
        <span className="text-slate-400">Total estimare internă materiale</span>
        <strong className="text-slate-100" data-testid="intake-v6-material-cost-total">
          {(breakdown.totals.estimated_cost_total ?? breakdown.totals.material_cost_total).toFixed(2)}{" "}
          {breakdown.totals.currency} estimare materiale
          {breakdown.totals.contains_estimates ? " (estimări/fallback)" : ""}
        </strong>
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-slate-400">{INTAKE_V6_MATERIAL_ESTIMATE_DISCLAIMER}</p>

      {operatorWarnings.length > 0 ? (
        <ul
          className="mt-3 space-y-1 rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] leading-relaxed text-amber-100"
          data-testid="intake-v6-operator-warnings"
        >
          <li className="font-semibold uppercase tracking-wide text-amber-200/90">Atenție operator</li>
          {operatorWarnings.map((warning) => (
            <li key={warning}>• {warning}</li>
          ))}
        </ul>
      ) : null}

      {quotingWarnings.length > 0 ? (
        <ul className="mt-3 space-y-1 text-[11px] leading-relaxed text-amber-200" data-testid="intake-v6-quoting-warnings">
          <li className="font-semibold uppercase tracking-wide text-slate-400">Atenție ofertare</li>
          {quotingWarnings.map((warning) => (
            <li key={warning}>• {warning}</li>
          ))}
        </ul>
      ) : null}

      {technicalWarnings.length > 0 ? (
        <IntakeV6TechnicalDetailsAccordion testId="intake-v6-technical-warnings" defaultOpen={false}>
          <ul className="space-y-1 text-[11px] leading-relaxed text-slate-400" data-testid="intake-v6-debug-warnings">
            <li className="font-semibold uppercase tracking-wide text-slate-500">Debug tehnic</li>
            {technicalWarnings.map((warning) => (
              <li key={warning}>• {warning}</li>
            ))}
          </ul>
        </IntakeV6TechnicalDetailsAccordion>
      ) : null}
    </div>
  );
}



