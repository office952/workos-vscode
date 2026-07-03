import type {
  IntakeV6MaterialBreakdownResponse,
  IntakeV6CncOperationRow,
  IntakeV6MaterialQuantityRow,
  IntakeV6PricingInputPreviewResponse,
} from "@/lib/intakeV6/intakeV6Api";
import { DEFAULT_EUR_TO_RON_RATE } from "@/lib/companyCommercialSettings";
import { splitIntakeV6MaterialBreakdownOperationRows } from "@/lib/intakeV6/intakeV6OperatorUiDisplay";

export interface IntakeV6OfferCommercialInputs {
  markupPercent: number;
  discountPercent: number;
  vatPercent: number;
  manualAdjustmentRon: number;
}

export interface IntakeV6OfferCommercialPayload {
  markup_percent: number;
  discount_percent: number;
  vat_percent: number;
  manual_adjustment_ron: number;
}

export interface IntakeV6OfferCostLine {
  key: string;
  label: string;
  amount: number;
  source: "payload" | "fallback";
  groupKey?: string;
  groupLabel?: string;
}

export interface IntakeV6OfferModel {
  letterCount: number | null;
  perimeterM: number;
  faceAreaM2: number;
  illuminated: boolean;
  costLines: IntakeV6OfferCostLine[];
  productionBase: number;
  markupValue: number;
  discountValue: number;
  manualAdjustmentRon: number;
  subtotalNet: number;
  vatValue: number;
  totalGross: number;
  fallbackCount: number;
  internalEstimateTotal: number | null;
  internalEstimateCurrency: string;
  offerCurrency: "RON";
  eurToRonRate: number;
  productionBaseInternal: number;
  productionBaseInternalCurrency: string;
}

type QuoteInputPayload = Record<string, unknown>;

const DEFAULT_COMMERCIAL_INPUTS: IntakeV6OfferCommercialInputs = {
  markupPercent: 35,
  discountPercent: 0,
  vatPercent: 19,
  manualAdjustmentRon: 0,
};

const ELECTRICAL_TOKENS = /led|psu|power|electric|electr|cablu|cable|wire|driver|traf|aliment/i;
const BOARD_TOKENS = /plex|plexi|acryl|forex|dibond|acm|backing|plac|sheet|panel/i;
const FILM_TOKENS = /oracal|vinyl|folie|film|laminat|laminare|print|autocolant|sticker/i;
const ACCESSORY_TOKENS = /adhes|adez|tape|banda|mount|fix|surub|șurub|screw|spacer|distanti|conector|connector|profile/i;
const FINISH_TOKENS = /cant|bevel|șanfren|sanfren|paint|vops|finish|finis/i;
const PROFILE_FINISH_TOKENS = /profil|profile|return|lateral/i;

interface OfferCategoryConfig {
  key: string;
  label: string;
}

const OFFER_CATEGORY_ORDER: OfferCategoryConfig[] = [
  { key: "electrical", label: "Materiale electrice" },
  { key: "boards", label: "Placi" },
  { key: "films", label: "Folii" },
  { key: "accessories", label: "Accesorii" },
  { key: "finishes", label: "Finisaje" },
];

function roundOfferMoney(amount: number): number {
  return Math.round(amount * 100) / 100;
}

export function normalizeIntakeV6EurToRonRate(rate: number | null | undefined): number {
  if (rate == null || !Number.isFinite(rate) || rate <= 0) {
    return DEFAULT_EUR_TO_RON_RATE;
  }
  return rate;
}

export function normalizeIntakeV6CurrencyCode(raw: string | null | undefined, fallback = "EUR"): string {
  const value = (raw ?? fallback).trim().toUpperCase();
  if (value === "LEI") return "RON";
  return value || fallback;
}

/** Convert internal cost amounts into RON offer base using company EUR/RON rate. */
export function convertIntakeV6InternalCostToRon(
  amount: number,
  sourceCurrency: string | null | undefined,
  eurToRonRate: number,
): number {
  if (!Number.isFinite(amount)) return 0;
  const currency = normalizeIntakeV6CurrencyCode(sourceCurrency);
  if (currency === "RON") return roundOfferMoney(amount);
  if (currency === "EUR") {
    return roundOfferMoney(amount * normalizeIntakeV6EurToRonRate(eurToRonRate));
  }
  return roundOfferMoney(amount);
}

function aggregateCostBucket(
  buckets: Map<string, number>,
  key: string,
  amount: number | null | undefined,
) {
  if (amount == null || !Number.isFinite(amount) || amount <= 0) {
    return;
  }
  buckets.set(key, (buckets.get(key) ?? 0) + amount);
}

function convertOfferCostLinesToRon(
  lines: IntakeV6OfferCostLine[],
  sourceCurrency: string,
  eurToRonRate: number,
): IntakeV6OfferCostLine[] {
  return lines.map((line) => ({
    ...line,
    amount: convertIntakeV6InternalCostToRon(line.amount, sourceCurrency, eurToRonRate),
  }));
}

function classifyMaterialLikeRow(row: IntakeV6MaterialQuantityRow): string {
  const haystack = [
    row.material_key,
    row.display_name,
    row.material_name,
    row.material_code,
    row.quantity_basis,
  ]
    .filter((value): value is string => typeof value === "string" && value.length > 0)
    .join(" ");
  if (ELECTRICAL_TOKENS.test(haystack)) return "electrical";
  if (FILM_TOKENS.test(haystack)) return "films";
  if (BOARD_TOKENS.test(haystack)) return "boards";
  if (PROFILE_FINISH_TOKENS.test(haystack) && /cant|return|lateral/i.test(haystack)) return "finishes";
  if (FINISH_TOKENS.test(haystack)) return "finishes";
  if (ACCESSORY_TOKENS.test(haystack)) return "accessories";
  if (row.category === "consumable") return "accessories";
  return "boards";
}

function classifyOperationRow(row: IntakeV6CncOperationRow): string {
  const haystack = [row.key, row.display_name, row.operation_type]
    .filter((value): value is string => typeof value === "string" && value.length > 0)
    .join(" ");
  if (FILM_TOKENS.test(haystack)) return "films";
  if (FINISH_TOKENS.test(haystack)) return "finishes";
  return "finishes";
}

function buildCostLinesFromBreakdown(
  breakdown: IntakeV6MaterialBreakdownResponse,
): IntakeV6OfferCostLine[] {
  const buckets = new Map<string, number>();
  for (const row of breakdown.material_rows) {
    aggregateCostBucket(buckets, classifyMaterialLikeRow(row), row.material_cost ?? row.estimated_cost ?? null);
  }
  for (const row of breakdown.consumable_rows) {
    aggregateCostBucket(buckets, classifyMaterialLikeRow(row), row.material_cost ?? row.estimated_cost ?? null);
  }
  const { cncRows, printRows } = splitIntakeV6MaterialBreakdownOperationRows(breakdown.operation_rows);
  for (const row of printRows) {
    aggregateCostBucket(buckets, classifyOperationRow(row), row.estimated_cost ?? null);
  }
  for (const row of cncRows) {
    aggregateCostBucket(buckets, classifyOperationRow(row), row.estimated_cost ?? null);
  }
  for (const row of breakdown.edge_cant_operation_rows ?? []) {
    aggregateCostBucket(buckets, "finishes", row.estimated_cost ?? null);
  }
  return OFFER_CATEGORY_ORDER.flatMap((category) => {
    const amount = buckets.get(category.key);
    if (amount == null || amount <= 0) return [];
    return [{
      key: category.key,
      label: category.label,
      amount,
      source: "payload" as const,
      groupKey: category.key,
      groupLabel: category.label,
    }];
  });
}

function readNumber(payload: QuoteInputPayload, keys: string[]): number | null {
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string") {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) return parsed;
    }
  }
  return null;
}

function readBoolean(payload: QuoteInputPayload, keys: string[]): boolean | null {
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === "boolean") return value;
    if (typeof value === "string") {
      const normalized = value.toLowerCase();
      if (normalized === "true") return true;
      if (normalized === "false") return false;
    }
  }
  return null;
}

export function resolveIntakeV6OfferCommercialDefaults(
  preview: IntakeV6PricingInputPreviewResponse | null,
  persisted?: unknown,
): IntakeV6OfferCommercialInputs {
  const persistedInputs = readIntakeV6OfferCommercialInputs(persisted);
  if (persistedInputs) {
    return persistedInputs;
  }
  const quoteInput = preview?.quote_input_payload ?? {};
  return {
    markupPercent:
      readNumber(quoteInput, ["markup_percent", "commercial_markup_percent", "margin_percent"]) ??
      DEFAULT_COMMERCIAL_INPUTS.markupPercent,
    discountPercent: readNumber(quoteInput, ["discount_percent", "commercial_discount_percent"]) ?? 0,
    vatPercent: readNumber(quoteInput, ["vat_percent", "tva_percent", "tax_percent"]) ?? 19,
    manualAdjustmentRon:
      readNumber(quoteInput, ["manual_adjustment_ron", "commercial_adjustment_ron", "extra_charge_ron"]) ??
      DEFAULT_COMMERCIAL_INPUTS.manualAdjustmentRon,
  };
}

export function readIntakeV6OfferCommercialInputs(raw: unknown): IntakeV6OfferCommercialInputs | null {
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) {
    return null;
  }
  const payload = raw as QuoteInputPayload;
  const markupPercent =
    readNumber(payload, ["markup_percent", "markupPercent", "commercial_markup_percent", "margin_percent"]) ??
    DEFAULT_COMMERCIAL_INPUTS.markupPercent;
  const discountPercent =
    readNumber(payload, ["discount_percent", "discountPercent", "commercial_discount_percent"]) ??
    DEFAULT_COMMERCIAL_INPUTS.discountPercent;
  const vatPercent =
    readNumber(payload, ["vat_percent", "vatPercent", "tva_percent", "tax_percent"]) ??
    DEFAULT_COMMERCIAL_INPUTS.vatPercent;
  const manualAdjustmentRon =
    readNumber(payload, ["manual_adjustment_ron", "manualAdjustmentRon", "commercial_adjustment_ron"]) ??
    DEFAULT_COMMERCIAL_INPUTS.manualAdjustmentRon;
  return {
    markupPercent,
    discountPercent,
    vatPercent,
    manualAdjustmentRon,
  };
}

export function serializeIntakeV6OfferCommercialInputs(
  inputs: IntakeV6OfferCommercialInputs,
): IntakeV6OfferCommercialPayload {
  return {
    markup_percent: inputs.markupPercent,
    discount_percent: inputs.discountPercent,
    vat_percent: inputs.vatPercent,
    manual_adjustment_ron: inputs.manualAdjustmentRon,
  };
}

export function buildIntakeV6OfferModel(args: {
  preview: IntakeV6PricingInputPreviewResponse | null;
  breakdown?: IntakeV6MaterialBreakdownResponse | null;
  commercialInputs: IntakeV6OfferCommercialInputs;
  eurToRonRate?: number | null;
}): IntakeV6OfferModel | null {
  const { preview, breakdown, commercialInputs, eurToRonRate } = args;
  if (!preview) return null;

  const quoteInput = preview.quote_input_payload;
  const letterCountValue = quoteInput.letter_count ?? preview.production_counts.letter_count;
  const perimeterValue = quoteInput.letter_perimeter_m ?? quoteInput.total_letter_perimeter_ml;
  const faceAreaValue = quoteInput.face_area_m2 ?? quoteInput.letter_face_area_m2;
  const letterCount =
    typeof letterCountValue === "number"
      ? letterCountValue
      : typeof letterCountValue === "string"
        ? Number(letterCountValue)
        : null;
  const perimeterM =
    typeof perimeterValue === "number" ? perimeterValue : typeof perimeterValue === "string" ? Number(perimeterValue) : 0;
  const faceAreaM2 =
    typeof faceAreaValue === "number" ? faceAreaValue : typeof faceAreaValue === "string" ? Number(faceAreaValue) : 0;
  const illuminated = readBoolean(quoteInput, ["illuminated", "is_illuminated", "lighting_required"]) ?? true;

  const materialCostValue = readNumber(quoteInput, [
    "material_cost",
    "material_cost_total",
    "estimated_material_cost",
    "materials_total",
    "subtotal_materials",
  ]);
  const operationCostValue = readNumber(quoteInput, [
    "operation_cost",
    "operations_cost_total",
    "estimated_operation_cost",
    "processing_total",
    "labor_cost",
  ]);
  const lightingCostValue = readNumber(quoteInput, [
    "lighting_cost",
    "led_cost",
    "illumination_cost",
    "power_supply_cost",
  ]);
  const finishingCostValue = readNumber(quoteInput, [
    "finish_cost",
    "finishing_cost",
    "paint_cost",
    "surface_finish_cost",
  ]);

  const safeLetterCount = Number.isFinite(letterCount ?? NaN) ? Math.max(letterCount ?? 0, 1) : 1;
  const safePerimeter = Number.isFinite(perimeterM) ? Math.max(perimeterM, 0.5) : 0.5;
  const safeFaceArea = Number.isFinite(faceAreaM2) ? Math.max(faceAreaM2, 0.18) : 0.18;

  const breakdownCostLines = breakdown ? buildCostLinesFromBreakdown(breakdown) : [];
  const internalCurrency = normalizeIntakeV6CurrencyCode(breakdown?.totals.currency ?? "EUR");
  const resolvedEurToRonRate = normalizeIntakeV6EurToRonRate(eurToRonRate);
  const rawCostLines: IntakeV6OfferCostLine[] =
    breakdownCostLines.length > 0
      ? breakdownCostLines
      : [
          {
            key: "materials",
            label: "Materiale",
            amount: materialCostValue ?? safeFaceArea * 165,
            source: materialCostValue == null ? "fallback" : "payload",
            groupKey: "boards",
            groupLabel: "Materiale",
          },
          {
            key: "operations",
            label: "Finisaje si operatii productie",
            amount: operationCostValue ?? safePerimeter * 42 + safeLetterCount * 18,
            source: operationCostValue == null ? "fallback" : "payload",
            groupKey: "finishes",
            groupLabel: "Finisaje",
          },
          {
            key: "lighting",
            label: "Iluminare",
            amount: lightingCostValue ?? (illuminated ? safeLetterCount * 34 + safePerimeter * 16 : 0),
            source: lightingCostValue == null ? "fallback" : "payload",
            groupKey: "electrical",
            groupLabel: "Materiale electrice",
          },
          {
            key: "finishing",
            label: "Finisaje si montaj pregatit",
            amount: finishingCostValue ?? safeFaceArea * (preview.requires_grouped_finish_review ? 85 : 52),
            source: finishingCostValue == null ? "fallback" : "payload",
            groupKey: "finishes",
            groupLabel: "Finisaje",
          },
        ];
  const productionBaseInternal = rawCostLines.reduce((sum, line) => sum + line.amount, 0);
  const costLines = convertOfferCostLinesToRon(rawCostLines, internalCurrency, resolvedEurToRonRate);

  const productionBase = costLines.reduce((sum, line) => sum + line.amount, 0);
  const markupValue = productionBase * (commercialInputs.markupPercent / 100);
  const subtotalBeforeDiscount = productionBase + markupValue + commercialInputs.manualAdjustmentRon;
  const discountValue = subtotalBeforeDiscount * (commercialInputs.discountPercent / 100);
  const subtotalNet = subtotalBeforeDiscount - discountValue;
  const vatValue = subtotalNet * (commercialInputs.vatPercent / 100);
  const totalGross = subtotalNet + vatValue;
  const fallbackCount = costLines.filter((line) => line.source === "fallback").length;

  return {
    letterCount,
    perimeterM,
    faceAreaM2,
    illuminated,
    costLines,
    productionBase,
    markupValue,
    discountValue,
    manualAdjustmentRon: commercialInputs.manualAdjustmentRon,
    subtotalNet,
    vatValue,
    totalGross,
    fallbackCount,
    internalEstimateTotal: breakdown?.totals.estimated_cost_total ?? breakdown?.totals.material_cost_total ?? null,
    internalEstimateCurrency: internalCurrency,
    offerCurrency: "RON",
    eurToRonRate: resolvedEurToRonRate,
    productionBaseInternal,
    productionBaseInternalCurrency: internalCurrency,
  };
}