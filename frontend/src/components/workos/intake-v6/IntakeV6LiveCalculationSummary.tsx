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
  LIVE_CALC_BASE_FILTER_OPTIONS,
  filterLiveCalcRows,
  parseLiveCalcRowCost,
  sumFilteredLiveCalcRows,
  type LiveCalcFilterId,
} from "@/lib/intakeV6/intakeV6LiveCalculationRowFilters";
import {
  buildIntakeV6OfferModel,
  type IntakeV6OfferCommercialInputs,
} from "@/lib/intakeV6/intakeV6OfferCalculator";
import {
  intakeV6HasOfficialCommercialTotals,
  intakeV6OfficialPricingBlockerMessage,
} from "@/lib/intakeV6/intakeV6OfficialPricing";
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
import AcmPanelProvisionalPricingBlock from "./AcmPanelProvisionalPricingBlock";
import { v6 } from "./atoms/intakeV6Presentation";
import {
  COST_INTERN_ESTIMATIV_LABEL,
  OFERTA_CLIENT_HELP,
  OFERTA_CLIENT_LABEL,
  OFERTA_VS_COST_BOUNDARY_HELP,
} from "@/lib/intakeV6/intakeV6OfferCostChromeVocabulary";

const RIGHT_PANEL_PREVIEW_LINES = 5;

export const INTAKE_V6_LIVE_CALC_TITLE = OFERTA_CLIENT_LABEL;
export const INTAKE_V6_LIVE_CALC_PREVIEW_HINT =
  `${OFERTA_CLIENT_HELP} Detaliile de linii se deschid la cerere.`;
export const INTAKE_V6_LIVE_CALC_GROSS_LABEL = "Ofertă client cu TVA";
export const INTAKE_V6_LIVE_CALC_NET_LABEL = "Ofertă client netă";
export const INTAKE_V6_LIVE_CALC_INTERNAL_LABEL = COST_INTERN_ESTIMATIV_LABEL;
export const INTAKE_V6_LIVE_CALC_ESTIMATE_UNAVAILABLE =
  "Oferta client necesită completarea configurației curente.";
export const INTAKE_V6_LIVE_CALC_DETAILS_TITLE = "Ofertă client — detalii estimate";
export const INTAKE_V6_LIVE_CALC_BOUNDARY_HINT = OFERTA_VS_COST_BOUNDARY_HELP;

/** Pricing reports availability only — Produs CTA owns the composition action. */
function shortenOperatorPricingBlocker(message: string | null | undefined): string | null {
  if (!message) return null;
  const lower = message.toLowerCase();
  if (
    lower.includes("compozit") ||
    lower.includes("composition") ||
    lower.includes("analyzer") ||
    lower.includes("dry-run") ||
    lower.includes("dry run")
  ) {
    return "Preț disponibil după confirmarea produsului.";
  }
  if (message.length > 96) return `${message.slice(0, 93).trim()}…`;
  return message;
}

type LiveCalcDisplayBucket = "included" | "diagnostic" | "missing" | "legacy" | "excluded";

type LogicalChildRowDisplay = {
  key: string;
  label: string;
  quantityText: string;
  costText: string | null;
};

type LiveCalcDisplayRow = ReturnType<typeof buildIntakeV6LiveMaterialsUsedRows>[number] & {
  category?: string;
  formulaText?: string;
  gapText?: string;
  childCount?: number;
  childRows?: LogicalChildRowDisplay[];
  technicalDetails?: string[];
  quantityValue?: number | null;
  quantityUnit?: string | null;
  source?: "logical-list" | "material-breakdown";
  amountValue?: number | null;
  amountCurrency?: string | null;
  statusLabel?: string;
  displayBucket: LiveCalcDisplayBucket;
  diagnosticReason?: string;
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

function dedupeStrings(values: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const trimmed = value?.trim();
    if (!trimmed || seen.has(trimmed)) continue;
    seen.add(trimmed);
    result.push(trimmed);
  }
  return result;
}

function resolveLogicalVisibleKey(row: IntakeV6LogicalListLineTrace): string {
  if (row.line_id === "material.plexiglas_face" || row.line_id === "material.logo_plexiglas_face") {
    return "material.plexiglas_shared";
  }
  return row.line_id;
}

function resolveLogicalVisibleLabel(row: IntakeV6LogicalListLineTrace): string {
  if (row.line_id === "material.plexiglas_face" || row.line_id === "material.logo_plexiglas_face") {
    return "Plexiglas 3 mm";
  }
  if (row.line_id === "material.forex_backing") return "Forex 10 mm";
  if (row.line_id === "material.return_profile") return "Cant / volum";
  if (row.line_id === "labor.cant_glue") return "Lipire cant / volum";
  return row.display_label;
}

function buildLogicalTechnicalDetails(row: IntakeV6LogicalListLineTrace): string[] {
  const details: Array<string | null> = [];
  if (row.display_label) details.push(`Sursă: ${row.display_label}`);
  const childRows = Array.isArray(row.child_rows) ? row.child_rows : [];
  for (const child of childRows) {
    if (!child || typeof child !== "object") continue;
    const displayName = typeof child.display_name === "string" ? child.display_name : null;
    const materialCode = typeof child.material_code === "string" ? child.material_code : null;
    if (displayName) details.push(`Rând runtime: ${displayName}`);
    if (materialCode) details.push(`Cod runtime: ${materialCode}`);
  }
  return dedupeStrings(details);
}

function formatLogicalChildLabel(child: Record<string, unknown>): string {
  const materialCode = typeof child.material_code === "string" ? child.material_code.trim() : "";
  const displayName = typeof child.display_name === "string" ? child.display_name.trim() : "";
  const label = typeof child.label === "string" ? child.label.trim() : "";
  const key = typeof child.key === "string" ? child.key.trim() : "";
  const psuMatch = materialCode.match(/^MAT-LED-PSU-(\d+V)-(\d+W)$/i);
  if (psuMatch) {
    return `Sursa ${psuMatch[1]} ${psuMatch[2]}`;
  }
  return displayName || label || materialCode || key || "Child row";
}

function formatLogicalChildQuantity(child: Record<string, unknown>): string {
  const quantity = typeof child.quantity === "number" && Number.isFinite(child.quantity) ? child.quantity : null;
  const unit = typeof child.unit === "string" ? child.unit.trim() : "";
  if (quantity == null) return unit || "cantitate lipsă";
  const normalized = Math.round(quantity * 10000) / 10000;
  return `${normalized} ${unit}`.trim();
}

function formatLogicalChildCost(child: Record<string, unknown>): string | null {
  const subtotal = typeof child.subtotal === "number" && Number.isFinite(child.subtotal) ? child.subtotal : null;
  const currency = typeof child.currency === "string" && child.currency.trim() ? child.currency.trim() : null;
  if (subtotal == null || currency == null) return null;
  return formatFaceBackPrepMoney(subtotal, currency);
}

function buildLogicalChildRows(row: IntakeV6LogicalListLineTrace): LogicalChildRowDisplay[] {
  const childRows = Array.isArray(row.child_rows) ? row.child_rows : [];
  return childRows.flatMap((child, index) => {
    if (!child || typeof child !== "object") return [];
    const childRecord = child as Record<string, unknown>;
    const identity =
      (typeof childRecord.key === "string" && childRecord.key.trim()) ||
      (typeof childRecord.material_code === "string" && childRecord.material_code.trim()) ||
      (typeof childRecord.display_name === "string" && childRecord.display_name.trim()) ||
      `child-${index + 1}`;
    return [{
      key: identity,
      label: formatLogicalChildLabel(childRecord),
      quantityText: formatLogicalChildQuantity(childRecord),
      costText: formatLogicalChildCost(childRecord),
    }];
  });
}

function mergeLogicalChildRows(
  existingRows: LogicalChildRowDisplay[] | undefined,
  nextRows: LogicalChildRowDisplay[],
): LogicalChildRowDisplay[] {
  const merged = new Map<string, LogicalChildRowDisplay>();
  for (const row of [...(existingRows ?? []), ...nextRows]) {
    if (!merged.has(row.key)) merged.set(row.key, row);
  }
  return Array.from(merged.values());
}

function resolveLogicalStatus(row: IntakeV6LogicalListLineTrace): string {
  if (row.quantity == null || !Number.isFinite(row.quantity) || row.quantity <= 0) return "cantitate lipsă";
  if ((row.blockers?.length ?? 0) > 0) return "blocat";
  if ((row.gaps?.length ?? 0) > 0) return "gap explicit";
  if (row.formula_status === "legacy_unversioned") return "legacy";
  if (row.status?.includes("PARTIAL")) return "estimat";
  if (row.status === "MATCHED") return "priced";
  return row.status?.toLowerCase().replace(/_/g, " ") || "read-only";
}

function hasFinitePositiveNumber(value: number | null | undefined): value is number {
  return value != null && Number.isFinite(value) && value > 0;
}

const NON_BLOCKING_LOGICAL_GAPS = new Set([
  "FORMULA_TRACE_MISSING",
  "COMMERCIAL_FORMULA_UNVERSIONED",
]);

function hasBlockingLogicalGaps(row: IntakeV6LogicalListLineTrace): boolean {
  return (row.gaps ?? []).some((gap) => !NON_BLOCKING_LOGICAL_GAPS.has(gap));
}

function hasRealLogicalRoute(row: IntakeV6LogicalListLineTrace): boolean {
  return Boolean(row.line_id && (row.formula_code_proposed || row.display_label));
}

function hasVisiblePricedLogicalContribution(
  row: IntakeV6LogicalListLineTrace,
  amountValue: number | null,
): boolean {
  return hasFinitePositiveNumber(row.quantity) && hasFinitePositiveNumber(amountValue) && hasRealLogicalRoute(row);
}

function shouldHighlightLogicalRow(
  row: IntakeV6LogicalListLineTrace,
  statusLabel: string,
  amountValue: number | null,
): boolean {
  if (!hasVisiblePricedLogicalContribution(row, amountValue)) return false;
  return statusLabel !== "priced";
}

function hasExplicitLogicalGap(row: IntakeV6LogicalListLineTrace): boolean {
  return (row.gaps?.length ?? 0) > 0;
}

function hasFallbackLogicalTrace(row: IntakeV6LogicalListLineTrace): boolean {
  const tokens = [
    ...(row.gaps ?? []),
    ...(row.warnings ?? []),
    row.status ?? null,
  ]
    .filter(Boolean)
    .map((token) => String(token).toLowerCase());
  return tokens.some((token) => token.includes("fallback"));
}

function hasPartialLogicalTrace(row: IntakeV6LogicalListLineTrace): boolean {
  if (row.status === "SPLIT_IN_RUNTIME") return false;
  const tokens = [
    row.status ?? null,
    ...(row.warnings ?? []),
    ...(row.gaps ?? []),
  ]
    .filter(Boolean)
    .map((token) => String(token).toLowerCase());
  return tokens.some(
    (token) =>
      token.includes("partial") ||
      token.includes("trace") ||
      token.includes("aggregated_for_logical_list"),
  );
}

function hasMissingLogicalPrice(
  row: IntakeV6LogicalListLineTrace,
  amountValue: number | null,
): boolean {
  if (row.quantity == null || !Number.isFinite(row.quantity) || row.quantity <= 0) return false;
  if (resolveLogicalStatus(row) === "priced" && amountValue == null) return true;
  const tokens = [
    row.status ?? null,
    ...(row.gaps ?? []),
    ...(row.blockers ?? []),
    ...(row.warnings ?? []),
  ]
    .filter(Boolean)
    .map((token) => String(token).toLowerCase());
  return tokens.some(
    (token) =>
      token.includes("missing_rate") ||
      token.includes("missing_price") ||
      token.includes("tarif"),
  );
}

function hasBreakdownFallback(row: ReturnType<typeof buildIntakeV6LiveMaterialsUsedRows>[number]): boolean {
  const text = `${row.debugSource ?? ""} ${row.subLabel ?? ""} ${row.label ?? ""}`.toLowerCase();
  return text.includes("fallback");
}

function hasBreakdownExplicitGap(row: ReturnType<typeof buildIntakeV6LiveMaterialsUsedRows>[number]): boolean {
  const text = `${row.label ?? ""} ${row.subLabel ?? ""}`.toLowerCase();
  return text.includes("gap explicit");
}

function hasBreakdownPartialTrace(row: ReturnType<typeof buildIntakeV6LiveMaterialsUsedRows>[number]): boolean {
  const text = `${row.debugSource ?? ""} ${row.subLabel ?? ""} ${row.label ?? ""}`.toLowerCase();
  return text.includes("partial") || text.includes("split_in_runtime") || text.includes("trace partial");
}

function resolveLogicalDiagnosticReason(
  row: IntakeV6LogicalListLineTrace,
  statusLabel: string,
  amountValue: number | null,
): string {
  if (row.formula_status === "legacy_unversioned" && amountValue == null) return "Legacy";
  if (row.quantity == null || !Number.isFinite(row.quantity) || row.quantity <= 0) return "Lipsa cantitate";
  if (hasMissingLogicalPrice(row, amountValue)) return "Fără tarif";
  if (hasExplicitLogicalGap(row)) return "Gap explicit";
  if (hasFallbackLogicalTrace(row)) return "Fallback";
  if ((row.blockers?.length ?? 0) > 0) return "Diagnostic tehnic";
  if (statusLabel === "priced" && amountValue == null) return "Fără tarif";
  if (hasPartialLogicalTrace(row)) return "Trace partial";
  if (row.status === "SPLIT_IN_RUNTIME") return "Neactiv în template curent";
  return "Diagnostic tehnic";
}

function classifyLogicalRow(
  row: IntakeV6LogicalListLineTrace,
  statusLabel: string,
  amountValue: number | null,
): LiveCalcDisplayBucket {
  if (hasVisiblePricedLogicalContribution(row, amountValue)) return "included";
  if (row.quantity == null || !Number.isFinite(row.quantity) || row.quantity <= 0) return "missing";
  if (hasMissingLogicalPrice(row, amountValue)) return "missing";
  if ((row.blockers?.length ?? 0) > 0) return "missing";
  if (row.status === "SPLIT_IN_RUNTIME") return "excluded";
  if (row.formula_status === "legacy_unversioned") return "legacy";
  if (hasExplicitLogicalGap(row) || hasFallbackLogicalTrace(row) || hasPartialLogicalTrace(row)) return "diagnostic";
  if (row.status === "MATCHED") return "missing";
  return "diagnostic";
}

function classifyBreakdownRow(row: ReturnType<typeof buildIntakeV6LiveMaterialsUsedRows>[number]): Pick<LiveCalcDisplayRow, "amountValue" | "amountCurrency" | "statusLabel" | "displayBucket" | "diagnosticReason"> {
  const amountValue = parseLiveCalcRowCost(row.costText);
  if (row.muted === true || amountValue == null) {
    const quantityMissing = row.quantityText === "cantitate lipsă";
    const explicitGap = hasBreakdownExplicitGap(row);
    const fallback = hasBreakdownFallback(row);
    const partialTrace = hasBreakdownPartialTrace(row);
    const diagnosticReason = quantityMissing
      ? "Lipsa cantitate"
      : explicitGap
        ? "Gap explicit"
        : fallback
          ? "Fallback"
          : partialTrace
            ? "Trace partial"
            : "Fără tarif";
    return {
      amountValue,
      amountCurrency: null,
      statusLabel:
        quantityMissing
          ? "cantitate lipsă"
          : diagnosticReason === "Gap explicit"
            ? "gap explicit"
            : diagnosticReason === "Fallback"
              ? "fallback"
              : diagnosticReason === "Trace partial"
                ? "trace partial"
                : "fără tarif",
      displayBucket: quantityMissing ? "missing" : "diagnostic",
      diagnosticReason,
    };
  }
  return {
    amountValue,
    amountCurrency: null,
    statusLabel: undefined,
    displayBucket: "included",
    diagnosticReason: undefined,
  };
}

function buildLogicalDisplayRows(
  logicalList: IntakeV6LogicalListReadModelResponse | null | undefined,
  fallbackCurrency: string,
): LiveCalcDisplayRow[] {
  const rows = logicalList?.rows ?? [];
  const grouped = new Map<string, LiveCalcDisplayRow>();
  rows.forEach((row) => {
    const formula = [row.formula_code_proposed, row.formula_version_proposed].filter(Boolean).join(" @ ");
    const gaps = [...(row.gaps ?? []), ...(row.warnings ?? []), ...(row.blockers ?? [])];
    const amountValue = hasFinitePositiveNumber(row.subtotal) ? row.subtotal : null;
    const amountCurrency = row.currency ?? fallbackCurrency;
    const statusLabel = resolveLogicalStatus(row);
    const displayBucket = classifyLogicalRow(row, statusLabel, amountValue);
    const highlightedRow = shouldHighlightLogicalRow(row, statusLabel, amountValue);
    const visiblePricedContribution = hasVisiblePricedLogicalContribution(row, amountValue);
    const groupKey = resolveLogicalVisibleKey(row);
    const technicalDetails = buildLogicalTechnicalDetails(row);
    const childRows = buildLogicalChildRows(row);
    const existing = grouped.get(groupKey);
    if (!existing) {
      grouped.set(groupKey, {
        groupKey,
        label: resolveLogicalVisibleLabel(row),
        quantityText: formatLogicalQuantity(row),
        quantityValue: row.quantity ?? null,
        quantityUnit: row.unit ?? null,
        costText: amountValue != null ? formatFaceBackPrepMoney(amountValue, amountCurrency) : "fără preț",
        muted: displayBucket !== "included" || highlightedRow,
        category: normalizeLogicalCategory(row.category),
        formulaText: formula || "formula lipsă",
        gapText: gaps.length > 0 ? gaps.join(" · ") : "fără gap",
        childCount: row.child_rows?.length ?? 0,
        childRows,
        technicalDetails,
        source: "logical-list",
        amountValue,
        amountCurrency,
        statusLabel,
        displayBucket,
        diagnosticReason:
          displayBucket === "included"
            ? undefined
            : resolveLogicalDiagnosticReason(row, statusLabel, amountValue),
      } satisfies LiveCalcDisplayRow);
      return;
    }
    const existingVisibleContribution = hasFinitePositiveNumber(existing.quantityValue) && hasFinitePositiveNumber(existing.amountValue);
    if (visiblePricedContribution) {
      const mergedAmount = existingVisibleContribution ? (existing.amountValue ?? 0) + (amountValue ?? 0) : amountValue;
      const mergedQuantity = existingVisibleContribution ? (existing.quantityValue ?? 0) + (row.quantity ?? 0) : row.quantity;
      existing.quantityValue = mergedQuantity ?? null;
      existing.quantityUnit = row.unit ?? existing.quantityUnit ?? null;
      existing.quantityText = formatLogicalQuantity({
        ...row,
        quantity: mergedQuantity ?? row.quantity,
        unit: existing.quantityUnit ?? row.unit,
      } as IntakeV6LogicalListLineTrace);
      existing.costText = mergedAmount != null ? formatFaceBackPrepMoney(mergedAmount, amountCurrency) : existing.costText;
      existing.amountValue = mergedAmount;
      existing.amountCurrency = amountCurrency;
    } else if (!existingVisibleContribution) {
      const mergedAmount = (existing.amountValue ?? 0) + (amountValue ?? 0);
      const mergedQuantity = (existing.quantityValue ?? 0) + (row.quantity ?? 0);
      existing.quantityValue = mergedQuantity;
      existing.quantityUnit = row.unit ?? existing.quantityUnit ?? null;
      existing.quantityText = formatLogicalQuantity({
        ...row,
        quantity: mergedQuantity,
        unit: existing.quantityUnit ?? row.unit,
      } as IntakeV6LogicalListLineTrace);
      existing.costText = mergedAmount > 0 ? formatFaceBackPrepMoney(mergedAmount, amountCurrency) : existing.costText;
      existing.amountValue = mergedAmount > 0 ? mergedAmount : existing.amountValue;
      existing.amountCurrency = amountCurrency;
    }
    existing.childCount = (existing.childCount ?? 0) + (row.child_rows?.length ?? 0);
    existing.childRows = mergeLogicalChildRows(existing.childRows, childRows);
    existing.technicalDetails = dedupeStrings([...(existing.technicalDetails ?? []), ...technicalDetails]);
    existing.gapText = dedupeStrings([existing.gapText, gaps.length > 0 ? gaps.join(" · ") : null]).join(" · ") || "fără gap";
    if (visiblePricedContribution) {
      existing.displayBucket = "included";
      existing.muted = Boolean(existing.muted) || highlightedRow;
      existing.diagnosticReason = undefined;
      if (!existingVisibleContribution || existing.statusLabel === "priced" || !existing.statusLabel) {
        existing.statusLabel = statusLabel;
      }
      return;
    }
    if (existing.displayBucket !== "included" && existing.displayBucket !== "missing" && displayBucket !== "included") {
      existing.displayBucket = displayBucket;
      existing.muted = true;
      existing.statusLabel = statusLabel;
      existing.diagnosticReason = resolveLogicalDiagnosticReason(row, statusLabel, amountValue);
    }
  });
  return Array.from(grouped.values()).map((row) => {
    if (row.amountValue != null && row.amountCurrency) {
      row.costText = formatFaceBackPrepMoney(row.amountValue, row.amountCurrency);
    }
    return row;
  });
}

function DiagnosticBadge({ label }: { label: string }) {
  return (
    <span className="inline-flex rounded border border-[#2A3548] bg-[#111827] px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-300">
      {label}
    </span>
  );
}

function isActionableStatusLabel(label: string | undefined): boolean {
  const token = String(label ?? "").trim().toLowerCase();
  return token === "cantitate lipsă" || token === "fără tarif" || token === "blocat";
}

function DiagnosticSection({ rows }: { rows: LiveCalcDisplayRow[] }) {
  const grouped = rows.reduce((map, row) => {
    const key = row.diagnosticReason ?? "Diagnostic tehnic";
    const existing = map.get(key) ?? [];
    existing.push(row);
    map.set(key, existing);
    return map;
  }, new Map<string, LiveCalcDisplayRow[]>());

  if (grouped.size === 0) return null;

  return (
    <details
      className="mt-3 rounded border border-[#2A3548] bg-[#0d1420]/80"
      data-testid="intake-v6-live-diagnostics"
    >
      <summary className="cursor-pointer list-none px-2.5 py-2 text-[11px] font-semibold uppercase tracking-wide text-amber-200">
        Neincluse / necesită configurare ({rows.length})
      </summary>
      <div className="border-t border-[#1F2A3D]/80 px-2.5 py-2">
        {Array.from(grouped.entries()).map(([reason, items]) => (
          <div key={reason} className="mb-3 last:mb-0" data-testid={`intake-v6-live-diagnostic-group-${reason}`}>
            <p className="mb-1 text-[11px] font-semibold text-amber-100/90">
              {reason} · {items.length}
            </p>
            <ul className="space-y-1 text-[11px] text-slate-300">
              {items.map((item) => (
                <li key={item.groupKey} className="rounded border border-[#1F2A3D]/80 bg-[#0A0F1A]/70 px-2 py-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <span className="min-w-0 truncate">{item.label}</span>
                    <span className="shrink-0 font-mono text-slate-400">{item.quantityText}</span>
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500">
                    {item.statusLabel ? <DiagnosticBadge label={item.statusLabel} /> : null}
                    {item.costText && item.costText !== "fără preț" ? <span>{item.costText}</span> : null}
                    {item.gapText ? <span>{item.gapText}</span> : null}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </details>
  );
}

function LiveCalcLineList({
  filteredRows,
  activeFilter,
  filterTotals,
  currency,
  logicalMode = false,
  showTechnicalDetails = false,
}: {
  filteredRows: LiveCalcDisplayRow[];
  activeFilter: LiveCalcFilterId;
  filterTotals: ReturnType<typeof sumFilteredLiveCalcRows>;
  currency: string;
  logicalMode?: boolean;
  showTechnicalDetails?: boolean;
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
        <span className="text-right">{logicalMode ? "Preț / status" : "Preț"}</span>
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
                    {logicalMode && showTechnicalDetails ? (
                      <span className="mt-0.5 block space-y-0.5 text-[10px] leading-snug text-slate-500">
                        {(item.technicalDetails ?? []).map((detail, index) => (
                          <span key={detail} data-testid={`intake-v6-logical-source-${item.groupKey}-${index}`}>{detail}</span>
                        ))}
                        <span data-testid={`intake-v6-logical-formula-${item.groupKey}`}>{item.formulaText}</span>
                        <span data-testid={`intake-v6-logical-gaps-${item.groupKey}`}>{item.gapText}</span>
                        <span data-testid={`intake-v6-logical-children-${item.groupKey}`}>
                          child rows: {item.childCount ?? 0}
                        </span>
                        {(item.childRows?.length ?? 0) > 0 ? (
                          <span
                            className="mt-1 block rounded border border-[#1F2A3D]/80 bg-[#0A0F1A]/70 px-2 py-1"
                            data-testid={`intake-v6-logical-child-rows-${item.groupKey}`}
                          >
                            {(item.childRows ?? []).map((childRow) => (
                              <span
                                key={childRow.key}
                                className="flex items-center justify-between gap-2"
                                data-testid={`intake-v6-logical-child-row-${item.groupKey}-${childRow.key}`}
                              >
                                <span className="truncate text-slate-400">{childRow.label}</span>
                                <span className="shrink-0 font-mono text-slate-500">
                                  {childRow.quantityText}{childRow.costText ? ` · ${childRow.costText}` : ""}
                                </span>
                              </span>
                            ))}
                          </span>
                        ) : null}
                      </span>
                    ) : !logicalMode && showTechnicalDetails && (item.technicalDetails?.length ?? 0) > 0 ? (
                      <span className="mt-0.5 block space-y-0.5 text-[10px] leading-snug text-slate-500">
                        {(item.technicalDetails ?? []).map((detail, index) => (
                          <span key={detail} data-testid={`intake-v6-breakdown-source-${item.groupKey}-${index}`}>{detail}</span>
                        ))}
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
                    <span className="block">{item.costText}</span>
                    {logicalMode && item.statusLabel && (showTechnicalDetails || isActionableStatusLabel(item.statusLabel)) ? (
                      <span className="mt-1 inline-flex justify-end">
                        <DiagnosticBadge label={item.statusLabel} />
                      </span>
                    ) : null}
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

function LiveCalcPreviewHeader({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? "mb-1 min-w-0" : "mb-1.5"} data-testid="intake-v6-live-calc-preview-header">
      <div className="flex items-center gap-1.5">
        <Calculator className="h-3.5 w-3.5 shrink-0 text-slate-600" aria-hidden />
        <h3 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          {INTAKE_V6_LIVE_CALC_TITLE}
        </h3>
      </div>
      {!compact ? (
        <>
          <p
            className="mt-1 text-[10px] leading-relaxed text-slate-600"
            data-testid="intake-v6-live-calc-preview-hint"
          >
            {INTAKE_V6_LIVE_CALC_PREVIEW_HINT}
          </p>
          <p
            className="mt-1 text-[10px] leading-relaxed text-cyan-700/80"
            data-testid="intake-v6-live-calc-boundary-hint"
          >
            {INTAKE_V6_LIVE_CALC_BOUNDARY_HINT}
          </p>
        </>
      ) : null}
    </div>
  );
}

function LiveCalcEstimateTotalsBlock({
  displayGrossRon,
  displayNetRon,
  total,
  currency,
  artworkOnlyBlocked,
  officialPricingBlocker = null,
  emphasis = "balanced",
}: {
  displayGrossRon: number | null;
  displayNetRon: number | null;
  total: number | null;
  currency: string;
  artworkOnlyBlocked: boolean;
  officialPricingBlocker?: string | null;
  emphasis?: "balanced" | "compact" | "sidebar";
}) {
  const showCommercialEstimate =
    !artworkOnlyBlocked && displayGrossRon != null && displayNetRon != null;
  const grossClassName =
    emphasis === "compact"
      ? "text-[14px] font-semibold tabular-nums leading-none text-slate-200"
      : emphasis === "sidebar"
        ? "text-[16px] font-semibold tabular-nums leading-tight text-slate-200"
        : "mt-0.5 block text-[18px] font-semibold tabular-nums leading-tight text-slate-200";
  const containerClassName =
    emphasis === "compact"
      ? "min-w-0"
      : "rounded-md border border-[#243044]/50 bg-[#101827]/50 px-2.5 py-2";

  return (
    <div className={containerClassName} data-testid="intake-v6-live-totals-summary">
      {showCommercialEstimate ? (
        <>
          <span className="block text-[11px] text-slate-500">{INTAKE_V6_LIVE_CALC_GROSS_LABEL}</span>
          <span className={grossClassName} data-testid="intake-v6-live-offer-gross">
            {formatFaceBackPrepMoney(displayGrossRon, "RON")}
          </span>
          <div
            className={joinClassNames(
              "flex items-baseline justify-between gap-2 text-[11px]",
              emphasis === "compact" ? "mt-0.5" : "mt-1.5",
            )}
          >
            <span className="text-slate-500">{INTAKE_V6_LIVE_CALC_NET_LABEL}</span>
            <span className="tabular-nums text-slate-400" data-testid="intake-v6-live-offer-net">
              {formatFaceBackPrepMoney(displayNetRon, "RON")}
            </span>
          </div>
        </>
      ) : !artworkOnlyBlocked ? (
        <p className="text-[11px] leading-relaxed text-slate-400" data-testid="intake-v6-live-estimate-unavailable">
          {shortenOperatorPricingBlocker(officialPricingBlocker) ?? INTAKE_V6_LIVE_CALC_ESTIMATE_UNAVAILABLE}
        </p>
      ) : null}
      <div
        className={joinClassNames(
          "flex items-baseline justify-between gap-2 text-[11px]",
          showCommercialEstimate ? "mt-1.5 border-t border-[#243044]/40 pt-1.5" : "",
        )}
      >
        <span className="text-slate-500">{INTAKE_V6_LIVE_CALC_INTERNAL_LABEL}</span>
        <span
          className={joinClassNames(
            "tabular-nums text-slate-300",
            emphasis === "sidebar" ? "text-[13px] font-medium" : "text-[12px] font-medium",
          )}
          data-testid="intake-v6-live-material-total"
        >
          {artworkOnlyBlocked ? "indisponibil" : totalCostLabel(total, currency)}
        </span>
      </div>
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
          <SheetTitle className="text-left text-[13px] text-slate-100">{INTAKE_V6_LIVE_CALC_DETAILS_TITLE}</SheetTitle>
          <SheetDescription className="mt-2 text-[10px] leading-relaxed text-slate-500">
            Breakdown pe materiale, operații și consumabile. Preview derivat — nu este ofertă finală.
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
  const logicalRows = useMemo(() => buildLogicalDisplayRows(logicalList, currency), [logicalList, currency]);
  const usesLogicalList = logicalRows.length > 0;
  const rows: LiveCalcDisplayRow[] = usesLogicalList
    ? logicalRows
    : breakdownRows.map((row) => {
        const classification = classifyBreakdownRow(row);
        return { ...row, source: "material-breakdown", ...classification };
      });
  const logicalRowCount = logicalList?.core_row_count ?? logicalRows.length;
  const logicalTargetRowCount = logicalList?.target_core_row_count ?? null;
  const [materialsOpen, setMaterialsOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<LiveCalcFilterId>("all");
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
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
  const hasOfficialTotals = intakeV6HasOfficialCommercialTotals(officialPricing);
  const officialPricingBlocker = intakeV6OfficialPricingBlockerMessage(officialPricing);
  const acmPanelCommercialPreview = officialPricing?.acm_panel_commercial_preview ?? null;
  const displayGrossRon = hasOfficialTotals ? officialTotals?.total_gross ?? null : null;
  const displayNetRon = hasOfficialTotals ? officialTotals?.subtotal_net ?? null : null;
  const includedRows = useMemo(() => rows.filter((row) => row.displayBucket === "included"), [rows]);
  const diagnosticRows = useMemo(() => rows.filter((row) => row.displayBucket !== "included"), [rows]);
  const filteredRows = useMemo(() => {
    if (activeFilter === "missing_rates") return diagnosticRows;
    return filterLiveCalcRows(includedRows, activeFilter);
  }, [activeFilter, diagnosticRows, includedRows]);
  const filterOptions = useMemo(() => {
    if (diagnosticRows.length === 0) return LIVE_CALC_BASE_FILTER_OPTIONS;
    return [...LIVE_CALC_BASE_FILTER_OPTIONS, { id: "missing_rates" as const, label: "Diagnostic / trace" }];
  }, [diagnosticRows.length]);
  const filterTotals = useMemo(() => sumFilteredLiveCalcRows(filteredRows), [filteredRows]);
  const previewRows = isRightPanel && !usesLogicalList ? filteredRows.slice(0, RIGHT_PANEL_PREVIEW_LINES) : filteredRows;
  const hiddenPreviewCount = Math.max(0, filteredRows.length - previewRows.length);
  const missingRateLabels = diagnosticRows.map((row) => {
    const label = row.label ?? "";
    // D4: do not present manufacturing accessories as a Montaj commercial-field error.
    if (/Accesorii montaj\s*\/\s*conectori/i.test(label)) {
      return label.replace(
        /Accesorii montaj\s*\/\s*conectori/i,
        "Consumabile producție — accesorii / conectori",
      );
    }
    return label;
  });
  const visibleMissingRateLabels = missingRateLabels.slice(0, 2);
  const hiddenMissingRateCount = Math.max(0, missingRateLabels.length - visibleMissingRateLabels.length);

  useEffect(() => {
    if (activeFilter === "missing_rates" && diagnosticRows.length === 0) {
      setActiveFilter("all");
    }
  }, [activeFilter, diagnosticRows.length]);

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

  const technicalDetailsToggle = (
    <label
      className="mb-2 flex items-center gap-2 rounded border border-[#243044]/80 bg-[#101827]/60 px-2.5 py-2 text-[11px] text-slate-300"
      data-testid="intake-v6-live-technical-toggle"
    >
      <input
        type="checkbox"
        checked={showTechnicalDetails}
        onChange={(event) => setShowTechnicalDetails(event.target.checked)}
      />
      <span>Afișează detalii tehnice</span>
    </label>
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
      {technicalDetailsToggle}
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
        <>
          <LiveCalcLineList
            filteredRows={filteredRows}
            activeFilter={activeFilter}
            filterTotals={filterTotals}
            currency={currency}
            logicalMode={usesLogicalList}
            showTechnicalDetails={showTechnicalDetails}
          />
          {activeFilter !== "missing_rates" ? <DiagnosticSection rows={diagnosticRows} /> : null}
        </>
      ) : (
        <p className="text-[11px] text-slate-400">Nu există încă breakdown live.</p>
      )}
    </>
  );

  if (isBar) {
    return (
      <div
        className={joinClassNames(
          "sticky top-0 z-10 rounded-md border border-[#243044]/70 bg-[#0A0F1A]/95 backdrop-blur-sm",
          className,
        )}
        data-testid="intake-v6-live-calculation-summary"
        data-layout={layout}
        data-price-spine="true"
      >
        <div
          className="flex flex-wrap items-center gap-x-3 gap-y-2 px-3 py-2"
          data-testid="intake-v6-price-spine-bar"
        >
          <LiveCalcPreviewHeader compact />

          {displayGrossRon != null && displayNetRon != null && !artworkOnlyBlocked ? (
            <div className="min-w-0 border-l border-[#243044]/60 pl-3">
              <span className="block text-[10px] text-slate-500">{INTAKE_V6_LIVE_CALC_GROSS_LABEL}</span>
              <span
                className="text-[14px] font-semibold tabular-nums leading-none text-slate-200"
                data-testid="intake-v6-live-offer-gross"
              >
                {formatFaceBackPrepMoney(displayGrossRon, "RON")}
              </span>
              <span
                className="ml-2 text-[10px] tabular-nums text-slate-400"
                data-testid="intake-v6-live-offer-net"
              >
                {INTAKE_V6_LIVE_CALC_NET_LABEL} {formatFaceBackPrepMoney(displayNetRon, "RON")}
              </span>
            </div>
          ) : null}

          <div className="min-w-0 border-l border-[#243044]/60 pl-3">
            <span className="block text-[10px] text-slate-500">{INTAKE_V6_LIVE_CALC_INTERNAL_LABEL}</span>
            <span
              className="text-[12px] font-medium tabular-nums text-slate-300"
              data-testid="intake-v6-live-material-total"
            >
              {artworkOnlyBlocked ? "indisponibil" : totalCostLabel(total, currency)}
            </span>
          </div>

          {missingPrices || missingRateLabels.length > 0 ? (
            <span
              className="inline-flex items-center gap-1 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-0.5 text-[10px] text-amber-200/90"
              data-testid="intake-v6-live-missing-rates-banner"
            >
              <AlertTriangle className="h-3 w-3 shrink-0" aria-hidden />
              {missingRateLabels.length > 0
                ? `${missingRateLabels.length} tarif${missingRateLabels.length === 1 ? "" : "e"} lipsă`
                : "Tarife lipsă"}
            </span>
          ) : null}

          {pendingSave ? (
            <span className="text-[10px] text-amber-200/90" data-testid="intake-v6-live-pending-save-inline">
              Salvare…
            </span>
          ) : null}

          <div className="ml-auto">
            <DetailsSheet
              detailsBody={detailsBody}
              missingRateLabels={missingRateLabels}
              triggerLabel="Detalii linii"
            />
          </div>
        </div>
        {/* Confirm continuity: same AcmPanel provisional contract as Review live-calc */}
        <div className="border-t border-[#243044]/50 px-3 pb-2">
          <AcmPanelProvisionalPricingBlock preview={acmPanelCommercialPreview} compact />
        </div>
      </div>
    );
  }

  if (isRightPanel) {
    return (
      <aside
        className={joinClassNames(
          "rounded-md border border-[#2A3548]/45 bg-[#0A0F1A]/55 p-2.5",
          className,
        )}
        data-testid="intake-v6-review-calculator-panel"
        data-layout={layout}
        data-pricing-weight="secondary"
      >
        <LiveCalcPreviewHeader />

        <LiveCalcEstimateTotalsBlock
          displayGrossRon={displayGrossRon}
          displayNetRon={displayNetRon}
          total={total}
          currency={currency}
          artworkOnlyBlocked={artworkOnlyBlocked}
          officialPricingBlocker={officialPricingBlocker}
          emphasis="compact"
        />

        <AcmPanelProvisionalPricingBlock preview={acmPanelCommercialPreview} compact />

        {pendingSave ? (
          <p
            className="mb-2 mt-2 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1.5 text-[11px] text-amber-100/90"
            data-testid="intake-v6-live-pending-save"
          >
            {INTAKE_V6_PENDING_SAVE_BANNER}
          </p>
        ) : null}

        {missingPrices || missingRateLabels.length > 0 ? (
          <div
            className="mb-2 mt-2 rounded border border-amber-500/20 bg-amber-500/5 px-2 py-1.5 text-[10px] text-amber-100/80"
            data-testid="intake-v6-live-missing-rates-banner"
          >
            <span className="font-medium">Tarife lipsă</span>
            {visibleMissingRateLabels.length > 0 ? (
              <span className="text-amber-100/70">
                {" "}
                — {visibleMissingRateLabels.join("; ")}
                {hiddenMissingRateCount > 0 ? ` (+${hiddenMissingRateCount})` : ""}
              </span>
            ) : null}
          </div>
        ) : null}

        {loading ? (
          <p className="mb-2 mt-2 text-[11px] text-slate-500">Actualizez estimările…</p>
        ) : rows.length > 0 ? (
          <div className="mt-2" data-testid="intake-v6-live-materials-used">
            {/* Line detail is opt-in so commercial result stays secondary to product decisions. */}
            <div className="mt-1">
              <DetailsSheet
                detailsBody={detailsBody}
                missingRateLabels={missingRateLabels}
                triggerLabel={`Detalii linii (${filteredRows.length})`}
                testId="intake-v6-review-calculator-details"
              />
            </div>
            {hiddenPreviewCount > 0 ? (
              <p className="sr-only" data-testid="intake-v6-live-preview-more">
                +{hiddenPreviewCount} linii în detaliu
              </p>
            ) : (
              <p className="sr-only" data-testid="intake-v6-live-preview-more">
                Detalii linii disponibile la cerere
              </p>
            )}
          </div>
        ) : (
          <p className="mt-2 text-[11px] text-slate-500">Nu există încă breakdown live.</p>
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
          <LiveCalcPreviewHeader />
          <p className="mt-1 text-[11px] text-slate-500">Materiale, consumabile și operații estimate</p>
        </div>
      ) : null}

      <LiveCalcEstimateTotalsBlock
        displayGrossRon={displayGrossRon}
        displayNetRon={displayNetRon}
        total={total}
        currency={currency}
        artworkOnlyBlocked={artworkOnlyBlocked}
        officialPricingBlocker={officialPricingBlocker}
        emphasis="sidebar"
      />

      <AcmPanelProvisionalPricingBlock preview={acmPanelCommercialPreview} />

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
          {technicalDetailsToggle}

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
              showTechnicalDetails={showTechnicalDetails}
            />
            {activeFilter !== "missing_rates" ? <DiagnosticSection rows={diagnosticRows} /> : null}
          </div>
        </div>
      ) : (
        <p className="text-[11px] text-slate-400">Nu există încă breakdown live.</p>
      )}
    </aside>
  );
}
