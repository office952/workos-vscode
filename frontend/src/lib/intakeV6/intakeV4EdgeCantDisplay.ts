import type { SvgAnalysisCoreReport, SvgAnalysisLayer } from "@/lib/svgAnalyzer";

import type { IntakeV4FinishSetup, IntakeV4MaterialBreakdownResponse } from "./intakeV4Api";

import type { IntakeV4ArtworkFinish } from "./intakeV4ArtworkFinish";

import { formatFaceBackPrepMoney } from "./intakeV4FaceBackPrepCostDraftDisplay";

import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";

import { formatIntakeV6ReturnFinishLabel as formatIntakeV4ReturnFinishLabel } from "./intakeV6ReturnFinishOptions";



export interface IntakeV4EdgeCantOperationPreview {

  key: string;

  label: string;

  quantity: number;

  unit: string;

  pricingStatus: string;

  estimatedCost: number | null;

  source: string | null;

  priceSource: string | null;

  consumesStockNow: boolean;

  createsTaskNow: boolean;

}



export interface IntakeV4EdgeCantOracalImpact {

  present: boolean;

  areaM2: number | null;

  unitPrice: number | null;

  estimatedCost: number | null;

  currency: string;

  priceSource: string | null;

  pricingMissing: boolean;

  basisNote: string | null;

}



export interface IntakeV4EdgeCantLayerRow {

  key: string;

  label: string;

  scope: "letters" | "artwork";

  perimeterM: number | null;

  cantActive: boolean;

  finishLabel: string;

  depthMm: number | null;

}



export interface IntakeV4EdgeCantGroupedRow {

  key: string;

  label: string;

  scope: "letters" | "artwork" | "mixed";

  perimeterM: number;

  finishLabel: string;

  depthMm: number | null;

  layerCount: number;

}



export interface IntakeV4EdgeCantLayerBreakdown {

  layers: IntakeV4EdgeCantLayerRow[];

  groups: IntakeV4EdgeCantGroupedRow[];

  totalLettersM: number;

  totalEmblemM: number;

  totalCantM: number;

}

export interface IntakeV4EdgeCantGroupNormalization {

  groups: IntakeV4EdgeCantGroupedRow[];

  rawTotalM: number | null;

  targetTotalM: number | null;

  normalized: boolean;

}



export interface IntakeV4EdgeCantViewModel {

  finishLabel: string;

  cantMaterialLabel: string;

  returnDepthMm: number | null;

  /** Unit rate label — e.g. "12.50 EUR/ml" or "tarif lipsă". */

  cantPriceLabel: string;

  cantUnitPrice: number | null;

  cantEstimatedCost: number | null;

  cantPricingMissing: boolean;

  cantCurrency: string;

  calculatedCantM: number | null;

  pricedCantM: number | null;

  wastePercent: number | null;

  adhesiveMl: number | null;

  oracal651: IntakeV4EdgeCantOracalImpact;

  operations: IntakeV4EdgeCantOperationPreview[];

  hasEdgeCantData: boolean;

}



const DEFAULT_RETURN_DEPTH_MM = 60;



const RETURN_MATERIAL_KEY = "return_material";

const ORACAL_CANT_KEY = "edge_cant_oracal_651";

const ADHESIVE_CANT_KEY = "adhesive_return_to_face";



const RETURN_INACTIVE = new Set(["", "none", "no_return", "without_return"]);

type ReturnMaterialQuantityField =
  | "base_quantity"
  | "quantity"
  | "priced_quantity"
  | "quantity_with_waste";

function isArtworkReturnMaterialKey(key: string): boolean {
  return key.startsWith("artwork_return_");
}

function isReturnMaterialKey(key: string): boolean {
  return key === RETURN_MATERIAL_KEY || isArtworkReturnMaterialKey(key);
}

function firstPositiveRowNumber(
  row: IntakeV4MaterialBreakdownResponse["material_rows"][number],
  fields: ReturnMaterialQuantityField[],
): number | null {
  for (const field of fields) {
    const value = row[field];
    if (typeof value === "number" && Number.isFinite(value) && value > 0) return value;
  }
  return null;
}

function roundReturnM(value: number): number {
  return Math.round(value * 10000) / 10000;
}

function sumReturnRowsWhenArtworkIsPresent(
  breakdown: IntakeV4MaterialBreakdownResponse | null,
  fields: ReturnMaterialQuantityField[],
): number | null {
  if (!breakdown) return null;
  let total = 0;
  let hasAnyReturn = false;
  let hasArtworkReturn = false;

  for (const row of breakdown.material_rows) {
    const key = row.material_key.toLowerCase();
    if (!isReturnMaterialKey(key)) continue;
    hasAnyReturn = true;
    if (isArtworkReturnMaterialKey(key)) hasArtworkReturn = true;
    total += firstPositiveRowNumber(row, fields) ?? 0;
  }

  return hasAnyReturn && hasArtworkReturn && total > 0 ? roundReturnM(total) : null;
}

function sumReturnRowCostsWhenArtworkIsPresent(
  breakdown: IntakeV4MaterialBreakdownResponse | null,
): number | null {
  if (!breakdown) return null;
  let total = 0;
  let hasAnyReturn = false;
  let hasArtworkReturn = false;
  let hasAnyCost = false;

  for (const row of breakdown.material_rows) {
    const key = row.material_key.toLowerCase();
    if (!isReturnMaterialKey(key)) continue;
    hasAnyReturn = true;
    if (isArtworkReturnMaterialKey(key)) hasArtworkReturn = true;
    const cost = row.estimated_cost ?? row.material_cost ?? null;
    if (typeof cost === "number" && Number.isFinite(cost) && cost > 0) {
      total += cost;
      hasAnyCost = true;
    }
  }

  return hasAnyReturn && hasArtworkReturn && hasAnyCost ? total : null;
}

export function resolveIntakeV4EffectiveReturnPerimeterM(args: {
  breakdown: IntakeV4MaterialBreakdownResponse | null;
  geometryReturnPerimeterM?: number | null;
}): number | null {
  const returnRow = args.breakdown?.material_rows.find((item) => item.material_key === RETURN_MATERIAL_KEY);
  return (
    sumReturnRowsWhenArtworkIsPresent(args.breakdown, ["base_quantity", "quantity"]) ??
    args.geometryReturnPerimeterM ??
    returnRow?.base_quantity ??
    returnRow?.quantity ??
    null
  );
}

export function resolveIntakeV4EffectivePricedReturnPerimeterM(args: {
  breakdown: IntakeV4MaterialBreakdownResponse | null;
  calculatedCantM?: number | null;
}): number | null {
  const returnRow = args.breakdown?.material_rows.find((item) => item.material_key === RETURN_MATERIAL_KEY);
  return (
    sumReturnRowsWhenArtworkIsPresent(args.breakdown, [
      "priced_quantity",
      "quantity_with_waste",
      "base_quantity",
      "quantity",
    ]) ??
    returnRow?.priced_quantity ??
    returnRow?.quantity_with_waste ??
    args.calculatedCantM ??
    null
  );
}



function fmtM(value: number | null | undefined): string {

  if (value == null || !Number.isFinite(value)) return "n/a";

  return `${value.toFixed(2)} m`;

}



function fmtM2(value: number | null | undefined): string {

  if (value == null || !Number.isFinite(value)) return "n/a";

  return `${value.toFixed(4)} m²`;

}



function fmtMl(value: number | null | undefined): string {

  if (value == null || !Number.isFinite(value)) return "n/a";

  return `${value.toFixed(2)} ml`;

}



export function formatEdgeCantM(value: number | null | undefined): string {

  return fmtM(value);

}



export function formatEdgeCantM2(value: number | null | undefined): string {

  return fmtM2(value);

}



export function formatEdgeCantMl(value: number | null | undefined): string {

  return fmtMl(value);

}



export function isIntakeV4ReturnFinishActive(finishType: string | null | undefined): boolean {

  const token = String(finishType ?? "").trim().toLowerCase();

  return !RETURN_INACTIVE.has(token);

}



function layerPerimeterM(layer: SvgAnalysisLayer): number | null {

  if (layer.perimeterMl != null && layer.perimeterMl > 0) return layer.perimeterMl;

  if (layer.perimeterMm != null && layer.perimeterMm > 0) return layer.perimeterMm / 1000;

  return null;

}



function findReportLayer(

  report: SvgAnalysisCoreReport | null | undefined,

  layerKey: string,

): SvgAnalysisLayer | undefined {

  if (!report) return undefined;

  return report.layers.find((layer) => layer.id === layerKey || layer.name === layerKey);

}



function resolveFinishLabel(finish: IntakeV4FinishSetup | null | undefined): string {

  if (!finish) return "necesită decizie";

  const groups = finish.letter_group_finishes;

  if (Array.isArray(groups) && groups.length > 0) {

    const labels = groups.map((group) =>

      formatIntakeV4ReturnFinishLabel({

        finishType: group.return_finish_type ?? finish.return_finish_type,

        colorCode: group.return_oracal_code,

        colorName: group.return_oracal_name,

      }),

    );

    const unique = [...new Set(labels)];

    return unique.join(" · ");

  }

  return formatIntakeV4ReturnFinishLabel({

    finishType: finish.return_finish_type,

    colorCode: finish.return_oracal_code,

    colorName: finish.return_oracal_name,

  });

}



function resolveReturnDepthMm(finish: IntakeV4FinishSetup | null | undefined): number | null {

  const raw = finish?.return_depth_mm;

  if (typeof raw === "number" && Number.isFinite(raw) && raw > 0) return raw;

  return DEFAULT_RETURN_DEPTH_MM;

}



function rounded3(value: number): number {

  return Math.round(value * 1000) / 1000;

}

function roundedDisplayMeters(value: number): number {

  return Math.round(value * 100) / 100;

}



function resolveDepthMm(value: number | null | undefined, fallback: number | null | undefined): number | null {

  if (typeof value === "number" && Number.isFinite(value) && value > 0) return value;

  if (typeof fallback === "number" && Number.isFinite(fallback) && fallback > 0) return fallback;

  return DEFAULT_RETURN_DEPTH_MM;

}



function groupEdgeCantRows(rows: IntakeV4EdgeCantLayerRow[]): IntakeV4EdgeCantGroupedRow[] {

  const groups = new Map<string, IntakeV4EdgeCantGroupedRow>();

  for (const row of rows) {

    if (!row.cantActive || row.perimeterM == null || row.perimeterM <= 0) continue;

    const depthKey = row.depthMm != null ? String(Math.round(row.depthMm)) : "unknown";

    const key = `${row.scope}|${depthKey}|${row.finishLabel}`;

    const prior = groups.get(key);

    if (prior) {

      prior.perimeterM = rounded3(prior.perimeterM + row.perimeterM);

      prior.layerCount += 1;

      continue;

    }

    groups.set(key, {

      key,

      label: `${row.finishLabel} · ${formatEdgeCantDepthMm(row.depthMm)}`,

      scope: row.scope,

      perimeterM: rounded3(row.perimeterM),

      finishLabel: row.finishLabel,

      depthMm: row.depthMm,

      layerCount: 1,

    });

  }

  return [...groups.values()].sort((a, b) => {

    const scopeOrder = a.scope.localeCompare(b.scope);

    if (scopeOrder !== 0) return scopeOrder;

    return (a.depthMm ?? 0) - (b.depthMm ?? 0) || a.finishLabel.localeCompare(b.finishLabel);

  });

}

export function normalizeIntakeV4EdgeCantGroupsToTotal(args: {

  groups: IntakeV4EdgeCantGroupedRow[];

  targetTotalM: number | null | undefined;

}): IntakeV4EdgeCantGroupNormalization {

  const rawTotal = args.groups.reduce((sum, group) => sum + group.perimeterM, 0);

  const target =
    typeof args.targetTotalM === "number" && Number.isFinite(args.targetTotalM) && args.targetTotalM > 0
      ? args.targetTotalM
      : null;

  if (args.groups.length === 0 || rawTotal <= 0 || target == null) {
    return {
      groups: args.groups,
      rawTotalM: rawTotal > 0 ? rounded3(rawTotal) : null,
      targetTotalM: target,
      normalized: false,
    };
  }

  if (Math.abs(rawTotal - target) < 0.01) {
    return {
      groups: args.groups.map((group) => ({ ...group, perimeterM: roundedDisplayMeters(group.perimeterM) })),
      rawTotalM: rounded3(rawTotal),
      targetTotalM: rounded3(target),
      normalized: false,
    };
  }

  const factor = target / rawTotal;
  const groups = args.groups.map((group) => ({
    ...group,
    perimeterM: roundedDisplayMeters(group.perimeterM * factor),
  }));

  const roundedTotal = groups.reduce((sum, group) => sum + group.perimeterM, 0);
  const delta = roundedDisplayMeters(target - roundedTotal);
  if (Math.abs(delta) >= 0.01 && groups.length > 0) {
    const last = groups[groups.length - 1]!;
    groups[groups.length - 1] = {
      ...last,
      perimeterM: roundedDisplayMeters(Math.max(0, last.perimeterM + delta)),
    };
  }

  return {
    groups,
    rawTotalM: rounded3(rawTotal),
    targetTotalM: rounded3(target),
    normalized: true,
  };

}



export function formatEdgeCantUnitPriceLabel(args: {

  unitPrice: number | null | undefined;

  currency?: string;

  pricingMissing: boolean;

}): string {

  if (args.pricingMissing || args.unitPrice == null) return "tarif lipsă";

  return `${args.unitPrice.toFixed(2)} ${args.currency ?? "EUR"}/ml`;

}



/** @deprecated Use formatEdgeCantUnitPriceLabel for operator card unit rate. */

export function formatEdgeCantPriceLabel(args: {

  estimatedCost: number | null | undefined;

  currency?: string;

  pricingMissing: boolean;

}): string {

  return formatEdgeCantUnitPriceLabel({

    unitPrice: args.estimatedCost,

    currency: args.currency,

    pricingMissing: args.pricingMissing,

  });

}



export function formatEdgeCantDepthMm(value: number | null | undefined): string {

  if (value == null || !Number.isFinite(value) || value <= 0) return "—";

  return `${Math.round(value)} mm`;

}



export function formatEdgeCantOperatorPerimeter(value: number | null | undefined): string {

  if (value == null || !Number.isFinite(value) || value <= 0) return "necesită verificare";

  return `${value.toFixed(2)} m`;

}



export function formatEdgeCantCostFormula(args: {

  perimeterM: number | null | undefined;

  unitPrice: number | null | undefined;

  currency?: string;

  pricingMissing: boolean;

}): string {

  if (

    args.pricingMissing ||

    args.perimeterM == null ||

    !Number.isFinite(args.perimeterM) ||

    args.perimeterM <= 0 ||

    args.unitPrice == null

  ) {

    return "indisponibil — tarif lipsă";

  }

  const currency = args.currency ?? "EUR";

  const cost = args.perimeterM * args.unitPrice;

  return `${args.perimeterM.toFixed(2)} m × ${args.unitPrice.toFixed(2)} ${currency}/ml = ${cost.toFixed(2)} ${currency}`;

}



export function formatEdgeCantLayerPerimeter(row: IntakeV4EdgeCantLayerRow): string {

  if (!row.cantActive) return "fără cant";

  if (row.perimeterM == null || row.perimeterM <= 0) return "n/a";

  return `${row.perimeterM.toFixed(2)} m`;

}



export function buildIntakeV4EdgeCantLayerBreakdown(args: {

  letterGroups: IntakeV4LetterGroupFinish[];

  artworkFinishes: IntakeV4ArtworkFinish[];

  report: SvgAnalysisCoreReport | null | undefined;

}): IntakeV4EdgeCantLayerBreakdown {

  const layers: IntakeV4EdgeCantLayerRow[] = [];

  let totalLettersM = 0;

  let totalEmblemM = 0;



  for (const group of args.letterGroups) {

    const cantActive = isIntakeV4ReturnFinishActive(group.return_finish_type);

    const perimeterM = group.perimeter_m ?? null;

    if (cantActive && perimeterM != null && perimeterM > 0) {

      totalLettersM += perimeterM;

    }

    layers.push({

      key: group.group_key,

      label: group.layer_name || group.group_key,

      scope: "letters",

      perimeterM,

      cantActive,

      finishLabel: formatIntakeV4ReturnFinishLabel({

        finishType: group.return_finish_type,

        colorCode: group.return_oracal_code,

      }),

      depthMm: resolveDepthMm(group.return_depth_mm, null),

    });

  }



  for (const artwork of args.artworkFinishes) {

    const cantActive = isIntakeV4ReturnFinishActive(artwork.return_finish_type);

    if (!cantActive) continue;

    const reportLayer = findReportLayer(args.report, artwork.layer_key);

    const perimeterM = reportLayer ? layerPerimeterM(reportLayer) : null;

    if (perimeterM != null && perimeterM > 0) {

      totalEmblemM += perimeterM;

    }

    layers.push({

      key: artwork.layer_key,

      label: artwork.layer_name || artwork.layer_key,

      scope: "artwork",

      perimeterM,

      cantActive: true,

      finishLabel: formatIntakeV4ReturnFinishLabel({

        finishType: artwork.return_finish_type,

        colorCode: artwork.return_oracal_code,

        colorName: artwork.return_oracal_name,

      }),

      depthMm: resolveDepthMm(artwork.return_depth_mm, null),

    });

  }



  return {

    layers,

    groups: groupEdgeCantRows(layers),

    totalLettersM: rounded3(totalLettersM),

    totalEmblemM: rounded3(totalEmblemM),

    totalCantM: rounded3(totalLettersM + totalEmblemM),

  };

}



function resolveCantMaterialLabel(breakdown: IntakeV4MaterialBreakdownResponse | null): string {

  if (!breakdown) return "calcul indisponibil";

  const row = breakdown.material_rows.find((item) => item.material_key === RETURN_MATERIAL_KEY);

  if (!row) return "aluminiu / conform setup";

  return row.display_name ?? row.material_name ?? "aluminiu / conform setup";

}



export function buildIntakeV4EdgeCantViewModel(args: {

  finish: IntakeV4FinishSetup | null | undefined;

  breakdown: IntakeV4MaterialBreakdownResponse | null;

  geometryReturnPerimeterM?: number | null;

}): IntakeV4EdgeCantViewModel {

  const { finish, breakdown } = args;

  const returnRow = breakdown?.material_rows.find((item) => item.material_key === RETURN_MATERIAL_KEY);

  const oracalRow = breakdown?.material_rows.find((item) => item.material_key === ORACAL_CANT_KEY);

  const adhesiveRow = breakdown?.consumable_rows.find((item) => item.material_key === ADHESIVE_CANT_KEY);



  const calculatedCantM = resolveIntakeV4EffectiveReturnPerimeterM({
    breakdown,
    geometryReturnPerimeterM: args.geometryReturnPerimeterM ?? null,
  });

  const pricedCantM = resolveIntakeV4EffectivePricedReturnPerimeterM({
    breakdown,
    calculatedCantM,
  });

  const wastePercent = returnRow?.waste_percent ?? breakdown?.quote_waste_percent_default ?? null;

  const cantUnitPrice = returnRow?.unit_price ?? null;

  const cantEstimatedCost =
    sumReturnRowCostsWhenArtworkIsPresent(breakdown) ??
    returnRow?.estimated_cost ??
    returnRow?.material_cost ??
    null;

  const cantCurrency = returnRow?.currency ?? breakdown?.totals.currency ?? "EUR";

  const cantPricingMissing = !returnRow || returnRow.price_source === "missing" || cantUnitPrice == null;



  const operations: IntakeV4EdgeCantOperationPreview[] = (breakdown?.edge_cant_operation_rows ?? []).map(

    (row) => ({

      key: row.key,

      label: row.display_name,

      quantity: row.quantity,

      unit: row.unit,

      pricingStatus: row.pricing_status ?? "missing_rate",

      estimatedCost: row.estimated_cost ?? null,

      source: row.source ?? null,

      priceSource: row.pricing_rate_key ?? null,

      consumesStockNow: row.consumes_stock_now === true,

      createsTaskNow: row.creates_task_now === true,

    }),

  );



  const oracal651: IntakeV4EdgeCantOracalImpact = {

    present: Boolean(oracalRow),

    areaM2: oracalRow?.base_quantity ?? oracalRow?.quantity ?? null,

    unitPrice: oracalRow?.unit_price ?? null,

    estimatedCost: oracalRow?.estimated_cost ?? oracalRow?.material_cost ?? null,

    currency: oracalRow?.currency ?? "EUR",

    priceSource: oracalRow?.price_source ?? null,

    pricingMissing: oracalRow?.price_source === "missing" || oracalRow?.unit_price == null,

    basisNote: oracalRow?.quantity_basis

      ? "Baza: cant pentru aplicare + adâncime cant + adaos 10 mm"

      : null,

  };



  const hasEdgeCantData =

    calculatedCantM != null ||

    pricedCantM != null ||

    adhesiveRow != null ||

    operations.length > 0 ||

    oracal651.present;



  return {

    finishLabel: resolveFinishLabel(finish),

    cantMaterialLabel: resolveCantMaterialLabel(breakdown),

    returnDepthMm: resolveReturnDepthMm(finish),

    cantPriceLabel: formatEdgeCantUnitPriceLabel({

      unitPrice: cantUnitPrice,

      currency: cantCurrency,

      pricingMissing: cantPricingMissing,

    }),

    cantUnitPrice,

    cantEstimatedCost,

    cantPricingMissing,

    cantCurrency,

    calculatedCantM,

    pricedCantM,

    wastePercent,

    adhesiveMl: adhesiveRow?.quantity ?? adhesiveRow?.base_quantity ?? null,

    oracal651,

    operations,

    hasEdgeCantData,

  };

}


