/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Data Store — thin wrapper that coordinates DB-backed data with mockData fallback.
 *
 * Strategy (MVP):
 *  - On first app load, check DB counts. If empty, return empty (production)
 *    or seed from mockData (only when VITE_ENABLE_MOCK_DATA=true).
 *  - Expose fetchers that return DB data mapped into the existing mockData shapes,
 *    so current UI components keep working without large rewrites.
 *  - If DB fetch fails AND mock flag is enabled, fall back to mockData.
 *  - If DB fetch fails AND mock flag is NOT enabled, return empty with error.
 */

import {
  intakeRequests as mockIntakes,
  quotes as mockQuotes,
  orders as mockOrders,
  inventoryMaterials as mockMaterials,
  suppliers as mockSuppliers,
  type IntakeRequest,
  type IntakeStatus,
  type Quote,
  type QuoteStatus,
  type Order,
  type OrderStatus,
  type InventoryMaterial,
  type Supplier,
  type DeliveryType,
  type IdentityType,
} from "./mockData";

import {
  intakesApi,
  quotesApi,
  ordersApi,
  materialsApi,
  suppliersApi,
  stringifyLineItems,
  type IntakeRequestEntity,
  type QuoteEntity,
  type OrderEntity,
  type InventoryMaterialEntity,
  type SupplierEntity,
} from "./api";
import { extractQuoteReadinessFromLineItems } from "./volumetricQuoteReady";
import type { OrderCommercialCurrencyHandoff } from "./orderCurrency";
import { extractOrderCommercialHandoff } from "./orderCurrency";
import { extractQuoteCurrencyFromLineItems } from "./quoteCurrency";
import { extractQuoteRevisionHistory } from "./quoteRevision";

// ============================================================
// MOCK DATA FLAG — controls whether mock/demo data is used
// ============================================================

/**
 * Returns true ONLY when the explicit VITE_ENABLE_MOCK_DATA flag is set to "true".
 * In production (flag absent or any other value), mock data is NEVER used:
 *  - Empty DB remains empty (no seeding)
 *  - Failed fetches return empty arrays with error, not mock fallback
 */
function isMockDataEnabled(): boolean {
  return import.meta.env.VITE_ENABLE_MOCK_DATA === "true";
}

// ============================================================
// MAPPERS — DB entity <-> UI model
// ============================================================

function mapIntakeFromDB(e: IntakeRequestEntity): IntakeRequest {
  return {
    id: e.code,
    client: e.client_name ?? "—",
    contactPerson: e.contact_person ?? "—",
    channel: (e.channel as IntakeRequest["channel"]) ?? "email",
    productFamily: e.product_family ?? "",
    description: e.description ?? "",
    dimensions: e.dimensions ?? "—",
    quantity: e.quantity,
    status: e.status as IntakeStatus,
    assignedTo: e.assigned_to ?? "—",
    createdAt: e.created_at ?? new Date().toISOString(),
    updatedAt: e.updated_at ?? new Date().toISOString(),
    notes: e.notes ?? "",
    priority: (e.priority as IntakeRequest["priority"]) ?? "normal",
    deliveryType: (e.delivery_type as DeliveryType) ?? "delivery_standard",
    identity: {
      type: "temp" as IdentityType,
      tempRef: `TEMP-${e.code}`,
    },
    productSpec: e.product_spec_json ?? null,
    confirmedTemplateCode: e.confirmed_template_code ?? null,
    confirmedTemplateName: e.confirmed_template_name ?? null,
    siteAudit: e.site_audit_json ?? null,
    dbId: e.id,
  };
}

/**
 * Sprint #18 — line_items parser that also extracts component_breakdown.
 *
 * Two supported shapes of `quote.line_items`:
 *   (A) Legacy / flat  — a JSON-encoded ARRAY of line items. Breakdown = undefined.
 *   (B) Wrapped        — a JSON-encoded OBJECT of shape:
 *         {
 *           "line_items":          [ ... legacy line items ... ],
 *           "component_breakdown": [ ... ComponentBreakdownItem[] ... ]
 *         }
 *
 * The frontend accepts BOTH without guessing or recomputing.  When the
 * wrapper object is absent (legacy quotes, and current backend state where
 * the router has not yet been extended), `componentBreakdown` is left
 * `undefined` and the old flat UI keeps rendering — ZERO regression.
 */
/**
 * Derives line items from a canonical QuoteCalculationSnapshot object.
 *
 * Canonical shape (from product_contracts.py):
 *   { product_definition, cost_result, pricing, price, status?, blocked_reasons? }
 *
 * We derive view-model line items from `cost_result.breakdown[]` which contains:
 *   { type, name, quantity, unit, unit_cost, total }
 *
 * If breakdown is empty/missing, we create a single summary line from cost_result totals.
 */
function deriveLineItemsFromCanonical(snapshot: any): any[] {
  const costResult = snapshot.cost_result;
  if (!costResult) return [];

  const breakdown: any[] = Array.isArray(costResult.breakdown) ? costResult.breakdown : [];

  if (breakdown.length > 0) {
    return breakdown.map((bl: any, i: number) => ({
      productCode: bl.type ?? `COST-${i + 1}`,
      description: bl.name ?? bl.type ?? "Cost line",
      quantity: Number(bl.quantity ?? 1),
      unit_price: Number(bl.unit_cost ?? 0),
      unitPrice: Number(bl.unit_cost ?? 0),
      total: Number(bl.total ?? 0),
    }));
  }

  // No breakdown — create summary line from totals
  if (costResult.total_cost > 0) {
    return [
      {
        productCode: "TOTAL-COST",
        description: `Total cost (${costResult.currency ?? "RON"})`,
        quantity: 1,
        unit_price: Number(costResult.total_cost),
        unitPrice: Number(costResult.total_cost),
        total: Number(costResult.total_cost),
      },
    ];
  }

  return [];
}

/**
 * Legacy fallback — splits aggregate cost_result totals evenly across
 * product_definition.layers (synthetic proxy rows, not CostEngine v2 output).
 */
function deriveBreakdownFromCanonical(snapshot: any): import("./mockData").ComponentBreakdownItem[] | undefined {
  const costResult = snapshot.cost_result;
  if (!costResult) return undefined;

  // If the snapshot has product_definition with layers, derive components from layers
  const productDef = snapshot.product_definition;
  if (productDef && Array.isArray(productDef.layers) && productDef.layers.length > 0) {
    const components: import("./mockData").ComponentBreakdownItem[] = productDef.layers.map((layer: any) => ({
      component_id: layer.layer_id ?? layer.id ?? "unknown",
      type: layer.layer_type ?? "layer",
      name: layer.layer_type ?? "Layer",
      material_cost: Number(costResult.materials_cost ?? 0) / productDef.layers.length,
      operation_cost: Number(costResult.labour_cost ?? 0) / productDef.layers.length,
      total_component_cost:
        (Number(costResult.materials_cost ?? 0) + Number(costResult.labour_cost ?? 0)) /
        productDef.layers.length,
      materials_detail: [],
      operations_detail: [],
      errors: [],
      warnings: [],
    }));
    return components.length > 0 ? components : undefined;
  }

  return undefined;
}

function normalizeComponentBreakdownItem(
  raw: unknown,
): import("./mockData").ComponentBreakdownItem | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;

  const component_id =
    (r.component_id as string | undefined) ??
    (r.componentId as string | undefined);
  const type =
    (r.type as string | undefined) ??
    (r.component_type as string | undefined);
  const name =
    (r.name as string | undefined) ??
    (r.component_name as string | undefined);

  const materialRaw = r.material_cost ?? r.materialCost;
  const operationRaw = r.operation_cost ?? r.operationCost ?? r.labor_cost ?? r.laborCost;
  const totalRaw = r.total_component_cost ?? r.totalComponentCost;

  const item: import("./mockData").ComponentBreakdownItem = {
    component_id,
    type,
    name,
  };

  if (materialRaw !== undefined && materialRaw !== null && materialRaw !== "") {
    item.material_cost = Number(materialRaw);
  }
  if (operationRaw !== undefined && operationRaw !== null && operationRaw !== "") {
    item.operation_cost = Number(operationRaw);
  }
  if (totalRaw !== undefined && totalRaw !== null && totalRaw !== "") {
    item.total_component_cost = Number(totalRaw);
  }

  const materialsDetail = r.materials_detail ?? r.materials;
  if (Array.isArray(materialsDetail)) {
    item.materials_detail = materialsDetail as import("./mockData").ComponentBreakdownItem["materials_detail"];
  }
  const operationsDetail = r.operations_detail ?? r.operations;
  if (Array.isArray(operationsDetail)) {
    item.operations_detail = operationsDetail as import("./mockData").ComponentBreakdownItem["operations_detail"];
  }
  if (Array.isArray(r.errors)) {
    item.errors = r.errors as import("./mockData").ComponentBreakdownItem["errors"];
  }
  if (Array.isArray(r.warnings)) {
    item.warnings = r.warnings as import("./mockData").ComponentBreakdownItem["warnings"];
  }

  return item;
}

function normalizeComponentBreakdown(
  raw: unknown,
): import("./mockData").ComponentBreakdownItem[] | undefined {
  if (!Array.isArray(raw) || raw.length === 0) return undefined;
  const items = raw
    .map(normalizeComponentBreakdownItem)
    .filter((item): item is import("./mockData").ComponentBreakdownItem => item !== null);
  return items.length > 0 ? items : undefined;
}

/** Prefer persisted CostEngine v2 breakdown; legacy layer split only when absent. */
function resolveComponentBreakdown(
  persisted: unknown,
  snapshot?: unknown,
): import("./mockData").ComponentBreakdownItem[] | undefined {
  const fromPersisted = normalizeComponentBreakdown(persisted);
  if (fromPersisted) return fromPersisted;
  if (snapshot && typeof snapshot === "object") {
    return deriveBreakdownFromCanonical(snapshot);
  }
  return undefined;
}

/**
 * Checks if an object is a canonical QuoteCalculationSnapshot.
 * Canonical shape has: product_definition AND (cost_result OR pricing OR price).
 */
function isCanonicalSnapshot(obj: any): boolean {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return false;
  return (
    "product_definition" in obj &&
    ("cost_result" in obj || "pricing" in obj || "price" in obj)
  );
}

export function extractQuotePayload(raw?: string): {
  lineItemsRaw: any[];
  componentBreakdown?: import("./mockData").ComponentBreakdownItem[];
} {
  if (!raw) return { lineItemsRaw: [] };
  let parsed: any;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return { lineItemsRaw: [] };
  }

  // Shape C — Canonical QuoteCalculationSnapshot object at top level.
  // Has product_definition + cost_result + pricing + price.
  // Derive line items from cost_result.breakdown.
  if (isCanonicalSnapshot(parsed)) {
    const lineItemsRaw = deriveLineItemsFromCanonical(parsed);
    const componentBreakdown = deriveBreakdownFromCanonical(parsed);
    return { lineItemsRaw, componentBreakdown };
  }

  // Shape B — wrapper object with line_items + optional component_breakdown.
  if (parsed && !Array.isArray(parsed) && typeof parsed === "object") {
    // Check if line_items is a canonical snapshot object (not array)
    if (parsed.line_items && !Array.isArray(parsed.line_items) && isCanonicalSnapshot(parsed.line_items)) {
      const lineItemsRaw = deriveLineItemsFromCanonical(parsed.line_items);
      const componentBreakdown = resolveComponentBreakdown(
        parsed.component_breakdown,
        parsed.line_items,
      );
      return { lineItemsRaw, componentBreakdown };
    }

    // line_items is a normal array
    const lineItemsRaw = Array.isArray(parsed.line_items) ? parsed.line_items : [];
    const componentBreakdown = normalizeComponentBreakdown(parsed.component_breakdown);

    // If lineItemsRaw is empty but the wrapper itself looks canonical, try deriving
    if (lineItemsRaw.length === 0 && isCanonicalSnapshot(parsed)) {
      return {
        lineItemsRaw: deriveLineItemsFromCanonical(parsed),
        componentBreakdown: resolveComponentBreakdown(parsed.component_breakdown, parsed),
      };
    }

    return { lineItemsRaw, componentBreakdown };
  }

  // Shape A — legacy flat array.
  if (Array.isArray(parsed)) {
    return { lineItemsRaw: parsed };
  }

  return { lineItemsRaw: [] };
}

function extractFlatMaterialNestingSummaryFromLineItems(
  raw?: string,
): import("./mockData").Quote["flatMaterialNestingSummary"] {
  if (!raw) return undefined;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return undefined;
    const summary = parsed.flat_material_nesting_summary;
    if (!summary || typeof summary !== "object") return undefined;
    return summary as import("./mockData").Quote["flatMaterialNestingSummary"];
  } catch {
    return undefined;
  }
}

function normalizeVatPct(value: unknown): number | undefined {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) return undefined;
  const normalized = numeric <= 1 ? numeric * 100 : numeric;
  return Number(normalized.toFixed(2));
}

function deriveVatPctFromTotals(e: QuoteEntity): number | undefined {
  const net = Number(e.total_before_vat ?? e.subtotal ?? 0);
  const vat = Number(e.vat ?? 0);
  if (net > 0 && vat >= 0) {
    return normalizeVatPct((vat / net) * 100);
  }
  return undefined;
}

function extractQuoteVatPct(notes?: string): number | undefined {
  if (!notes) return undefined;
  try {
    const parsed = JSON.parse(notes);
    return (
      normalizeVatPct(
        parsed?.intake_v6_linkage_v1?.snapshot?.workspace_payload_snapshot?.finish_setup?.commercial_inputs?.vat_percent,
      ) ??
      normalizeVatPct(
        parsed?.intake_v6_linkage_v1?.snapshot?.finish_setup?.commercial_inputs?.vat_percent,
      )
    );
  } catch {
    return undefined;
  }
}

function deriveQuoteVatPct(e: QuoteEntity): number | undefined {
  const fromNotes = extractQuoteVatPct(e.notes);
  const fromTotals = deriveVatPctFromTotals(e);

  if (fromNotes !== undefined) {
    if (fromTotals === undefined) return fromNotes;
    if (Math.abs(fromNotes - fromTotals) <= 0.5) return fromNotes;
  }

  return fromTotals;
}

function mapQuoteFromDB(e: QuoteEntity): Quote {
  const volumetricReadiness =
    extractQuoteReadinessFromLineItems(e.line_items) ?? undefined;
  const revisionHistory = extractQuoteRevisionHistory(e.line_items);
  const { lineItemsRaw, componentBreakdown } = extractQuotePayload(e.line_items);
  const lineItems = lineItemsRaw.map((li: any, i: number) => ({
    id: `LI-${e.code}-${i + 1}`,
    productCode: li.productCode ?? li.code ?? "SRV-001",
    description: li.description ?? "",
    quantity: Number(li.quantity ?? 1),
    unitCost: Number(li.unit_cost ?? li.unitCost ?? 0),
    unitPrice: Number(li.unit_price ?? li.unitPrice ?? 0),
    total: Number(li.total ?? 0),
  }));
  return {
    id: e.code,
    dbId: e.id,
    intakeId: e.intake_code ?? "",
    client: e.client_name,
    contactPerson: e.contact_person ?? "—",
    status: e.status as QuoteStatus,
    version: e.version ?? 1,
    createdAt: e.created_at ?? new Date().toISOString(),
    validUntil: e.valid_until ?? "",
    lineItems,
    subtotal: Number(e.subtotal ?? 0),
    discount: Number(e.discount ?? 0),
    discountPct: Number(e.discount_pct ?? 0),
    totalBeforeVAT: Number(e.total_before_vat ?? e.subtotal ?? 0),
    vatPct: deriveQuoteVatPct(e),
    vat: Number(e.vat ?? 0),
    grandTotal: Number(e.grand_total ?? 0),
    marginPct: Number(e.margin_pct ?? 0),
    notes: e.notes ?? "",
    assignedTo: e.assigned_to ?? "—",
    componentBreakdown,
    volumetricReadiness,
    revisionHistory: revisionHistory.length > 0 ? revisionHistory : undefined,
    currency: extractQuoteCurrencyFromLineItems(e.line_items),
    flatMaterialNestingSummary: extractFlatMaterialNestingSummaryFromLineItems(e.line_items),
  };
}

const KNOWN_ORDER_STATUSES = new Set<OrderStatus>([
  "created",
  "confirmed",
  "locked",
  "in_execution",
  "completed",
  "cancelled",
]);

const ORDER_STATUS_ALIASES: Record<string, OrderStatus> = {
  in_production: "in_execution",
};

export function normalizeOrderStatus(raw: string | null | undefined): OrderStatus {
  const value = (raw ?? "").trim().toLowerCase();
  if (ORDER_STATUS_ALIASES[value]) {
    return ORDER_STATUS_ALIASES[value];
  }
  if (KNOWN_ORDER_STATUSES.has(value as OrderStatus)) {
    return value as OrderStatus;
  }
  return "created";
}

export function normalizeOrderPaymentStatus(raw: string | null | undefined): Order["paymentStatus"] {
  const value = (raw ?? "").trim().toLowerCase();
  if (value === "pending" || value === "partial" || value === "paid") {
    return value;
  }
  return "pending";
}

function mapOrderFromDB(e: OrderEntity): Order {
  const commercialCurrencyHandoff = extractOrderCommercialHandoff(e.snapshot_line_items);
  return {
    id: e.code,
    dbId: e.id,
    quoteId: e.quote_code ?? "",
    client: e.client_name,
    contactPerson: e.contact_person ?? "—",
    status: normalizeOrderStatus(e.status),
    lockedAt: e.locked_at ?? "",
    createdAt: e.created_at ?? new Date().toISOString(),
    promisedDelivery: e.promised_delivery ?? "",
    totalAmount: Number(commercialCurrencyHandoff?.base_total_ron ?? e.total_amount ?? 0),
    jobId: e.job_id ?? "",
    productSummary: e.product_summary ?? "",
    paymentStatus: normalizeOrderPaymentStatus(e.payment_status),
    snapshotVersion: e.snapshot_version ?? 1,
    readinessSnapshot: e.readiness_snapshot ?? null,
    commercialCurrencyHandoff,
    baseCurrency: commercialCurrencyHandoff?.base_currency ?? "RON",
    notes: e.notes ?? "",
  };
}

function mapMaterialFromDB(e: InventoryMaterialEntity): InventoryMaterial {
  const computedStatus =
    e.stock_current <= 0
      ? "out_of_stock"
      : e.stock_current < e.stock_min
        ? "critical"
        : e.stock_current < e.stock_min * 1.5
          ? "low"
          : "ok";
  return {
    id: e.code,
    name: e.name,
    category: e.category,
    unit: e.unit,
    stockCurrent: Number(e.stock_current ?? 0),
    stockMin: Number(e.stock_min ?? 0),
    stockMax: Number(e.stock_max ?? 0),
    unitCost: Number(e.unit_cost ?? 0),
    supplier: e.supplier ?? "",
    lastRestocked: e.last_restocked ?? "",
    consumptionRate: Number(e.consumption_rate ?? 0),
    stockStatus: computedStatus,
    daysUntilEmpty: 0,
    location: e.location ?? "",
  };
}

function mapSupplierFromDB(e: SupplierEntity): Supplier {
  return {
    id: e.code,
    name: e.name,
    category: e.category,
    leadTimeDays: Number(e.lead_time_days ?? 7),
    rating: Number(e.rating ?? 4),
    activeOrders: Number(e.active_orders ?? 0),
    lastDelivery: e.last_delivery ?? "",
  };
}

// ============================================================
// LOADERS — fetch from DB; mock fallback ONLY when flag enabled
// ============================================================

// AUDIT FIX (Task 8): safeLoad now returns source truth alongside data.
export type DataSource = "db" | "mock" | "empty" | "error";

export interface SafeLoadResult<TUi> {
  rows: TUi[];
  source: DataSource;
  error?: string;
}

/**
 * Safe loader with conditional mock fallback.
 *
 * BLOCKER FIX: Mock data is NEVER used unless VITE_ENABLE_MOCK_DATA=true.
 * - DB empty + mock disabled → returns empty array, source="empty"
 * - DB fetch fails + mock disabled → returns empty array, source="error"
 * - DB empty + mock enabled → returns mock data, source="mock"
 * - DB fetch fails + mock enabled → returns mock data, source="mock" (with error logged)
 */
async function safeLoad<TDb, TUi>(
  loader: () => Promise<TDb[]>,
  mapper: (e: TDb) => TUi,
  fallback: TUi[],
  label: string
): Promise<SafeLoadResult<TUi>> {
  const mockEnabled = isMockDataEnabled();

  try {
    const rows = await loader();
    if (!rows || rows.length === 0) {
      if (mockEnabled && fallback.length > 0) {
        console.info(`[dataStore] ${label}: DB empty, mock flag enabled — using mockData.`);
        return { rows: fallback, source: "mock" };
      }
      // Production: DB empty stays empty
      return { rows: [], source: "empty" };
    }
    return { rows: rows.map(mapper), source: "db" };
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err);
    if (mockEnabled) {
      console.warn(`[dataStore] ${label}: DB fetch failed, mock flag enabled — using mockData.`, err);
      return { rows: fallback, source: "mock", error: errMsg };
    }
    // Production: fetch failed, no fallback
    console.warn(`[dataStore] ${label}: DB fetch failed, no mock fallback.`, err);
    return { rows: [], source: "error", error: errMsg };
  }
}

export async function loadIntakes(): Promise<SafeLoadResult<IntakeRequest>> {
  return safeLoad(
    () => intakesApi.list({}, { sort: "-created_at", limit: 500 }),
    mapIntakeFromDB,
    mockIntakes,
    "intakes"
  );
}

export async function loadQuotes(): Promise<SafeLoadResult<Quote>> {
  return safeLoad(
    () => quotesApi.list({}, { sort: "-created_at", limit: 500 }),
    mapQuoteFromDB,
    mockQuotes,
    "quotes"
  );
}

export async function loadOrders(): Promise<SafeLoadResult<Order>> {
  return safeLoad(
    () => ordersApi.list({}, { sort: "-created_at", limit: 500 }),
    mapOrderFromDB,
    mockOrders,
    "orders"
  );
}

export async function loadMaterials(): Promise<SafeLoadResult<InventoryMaterial>> {
  return safeLoad(
    () => materialsApi.list({}, { sort: "-created_at", limit: 500 }),
    mapMaterialFromDB,
    mockMaterials,
    "materials"
  );
}

export async function loadSuppliers(): Promise<SafeLoadResult<Supplier>> {
  return safeLoad(
    () => suppliersApi.list({}, { sort: "-created_at", limit: 500 }),
    mapSupplierFromDB,
    mockSuppliers,
    "suppliers"
  );
}

// ============================================================
// WRITERS — update DB by code (UI uses code as id)
// ============================================================

async function findByCode<T extends { id: number; code: string }>(
  api: {
    list: (q: Record<string, unknown>, opts?: Record<string, unknown>) => Promise<T[]>;
  },
  code: string
): Promise<T | null> {
  const rows = await api.list({ code }, { limit: 1 });
  return rows[0] ?? null;
}

export async function updateIntakeStatus(
  code: string,
  status: IntakeStatus,
  extra: Partial<IntakeRequestEntity> = {}
): Promise<boolean> {
  try {
    const row = await findByCode(intakesApi as any, code);
    if (!row) return false;
    await intakesApi.update(row.id, { status, ...extra });
    return true;
  } catch (err) {
    console.warn("[dataStore] updateIntakeStatus failed", err);
    return false;
  }
}

export type CreateDraftQuoteSuccess = {
  ok: true;
  quoteCode: string;
  openedExisting?: boolean;
};

export type CreateDraftQuoteFailure = {
  ok: false;
  error: string;
};

export type CreateDraftQuoteResult = CreateDraftQuoteSuccess | CreateDraftQuoteFailure;

function parseFromIntakeError(status: number, bodyText: string): string {
  try {
    const parsed = JSON.parse(bodyText) as {
      detail?: string | { error?: string; existing_quote_code?: string };
    };
    const detail = parsed.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (detail && typeof detail === "object") {
      if (detail.error === "quote_already_exists_for_intake" && detail.existing_quote_code) {
        return `Oferta draft există deja: ${detail.existing_quote_code}`;
      }
      if (typeof detail.error === "string") return detail.error;
    }
  } catch {
    /* plain text fallback */
  }
  if (bodyText.trim()) return bodyText.trim();
  return `Crearea ofertei draft a eșuat (HTTP ${status}).`;
}

export async function createDraftQuoteFromIntake(
  intake: IntakeRequest
): Promise<CreateDraftQuoteResult> {
  // BUILD SET 3A: Use canonical backend endpoint POST /from-intake/{intake_id}
  // Frontend does NOT construct quote payload manually.
  // Backend validates intake status and creates draft quote with proper link.
  try {
    const intakeRows = await intakesApi.list({ code: intake.id }, { limit: 1 });
    if (!intakeRows || intakeRows.length === 0) {
      console.warn("[dataStore] createDraftQuoteFromIntake: intake not found in DB by code", intake.id);
      return { ok: false, error: `Cererea ${intake.id} nu a fost găsită în baza de date.` };
    }
    const intakeDbId = intakeRows[0].id;

    const { getAPIBaseURL } = await import("@/lib/config");
    const base = getAPIBaseURL();
    const res = await fetch(`${base}/api/v1/entities/quotes/from-intake/${intakeDbId}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });

    if (res.status === 409) {
      const bodyText = await res.text().catch(() => "");
      try {
        const parsed = JSON.parse(bodyText) as {
          detail?: { error?: string; existing_quote_code?: string };
        };
        const detail = parsed.detail;
        if (
          detail &&
          typeof detail === "object" &&
          detail.error === "quote_already_exists_for_intake" &&
          detail.existing_quote_code
        ) {
          return {
            ok: true,
            quoteCode: detail.existing_quote_code,
            openedExisting: true,
          };
        }
      } catch {
        /* fall through */
      }
      console.warn("[dataStore] createDraftQuoteFromIntake: conflict", bodyText);
      return { ok: false, error: parseFromIntakeError(res.status, bodyText) };
    }

    if (!res.ok) {
      const bodyText = await res.text().catch(() => "");
      console.warn("[dataStore] createDraftQuoteFromIntake: backend returned", res.status, bodyText);
      return { ok: false, error: parseFromIntakeError(res.status, bodyText) };
    }

    const result = (await res.json()) as { quote_code?: string };
    const quoteCode = result.quote_code?.trim();
    if (!quoteCode) {
      return { ok: false, error: "Backend nu a returnat codul ofertei draft." };
    }
    return { ok: true, quoteCode };
  } catch (err) {
    console.warn("[dataStore] createDraftQuoteFromIntake failed", err);
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Eroare la crearea ofertei draft.",
    };
  }
}

export async function updateMaterialStock(
  code: string,
  newStock: number
): Promise<boolean> {
  try {
    const row = await findByCode(materialsApi as any, code);
    if (!row) return false;
    await materialsApi.update(row.id, { stock_current: newStock });
    return true;
  } catch (err) {
    console.warn("[dataStore] updateMaterialStock failed", err);
    return false;
  }
}

export async function updateQuoteStatus(
  code: string,
  status: QuoteStatus,
  extra: Partial<QuoteEntity> = {}
): Promise<boolean> {
  try {
    const row = await findByCode(quotesApi as any, code);
    if (!row) return false;
    await quotesApi.update(row.id, { status, ...extra });
    return true;
  } catch (err) {
    console.warn("[dataStore] updateQuoteStatus failed", err);
    return false;
  }
}

export async function createOrderFromQuote(
  quoteId: string,
  options?: {
    acknowledge_readiness_warnings?: boolean;
    readiness_warning_acknowledgement_reason?: string;
  }
): Promise<string | null> {
  try {
    // AUDIT FIX (Task 5): Quote -> Order conversion MUST use the canonical
    // backend endpoint POST /api/v1/entities/orders/from-quote/{quote_id}.
    // Frontend is NOT allowed to construct Order manually from quote data.
    // First, resolve the quote's numeric DB id from its code.
    const quoteRows = await quotesApi.list({ code: quoteId }, { limit: 1 });
    if (!quoteRows || quoteRows.length === 0) {
      console.warn("[dataStore] createOrderFromQuote: quote not found in DB by code", quoteId);
      return null;
    }
    const quoteDbId = quoteRows[0].id;

    // Call the canonical backend endpoint using fetch (same pattern as other API calls)
    const { getAPIBaseURL } = await import("@/lib/config");
    const base = getAPIBaseURL();
    const requestBody: Record<string, unknown> = {};
    if (options?.acknowledge_readiness_warnings) {
      requestBody.acknowledge_readiness_warnings = true;
      // Only send reason when acknowledgement is explicitly true
      if (options?.readiness_warning_acknowledgement_reason) {
        requestBody.readiness_warning_acknowledgement_reason = options.readiness_warning_acknowledgement_reason;
      }
    }

    const res = await fetch(`${base}/api/v1/entities/orders/from-quote/${quoteDbId}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: Object.keys(requestBody).length > 0 ? JSON.stringify(requestBody) : undefined,
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      console.warn("[dataStore] createOrderFromQuote: backend returned", res.status, detail);
      // Throw with full error detail so caller can handle warnings/blockers
      throw new Error(JSON.stringify(detail));
    }

    const data = await res.json();
    const orderCode: string | null = data?.order_code ?? null;

    // Mark quote as accepted if not already
    // Note: We don't update here anymore since quote status should be managed separately
    return orderCode;
  } catch (err) {
    console.warn("[dataStore] createOrderFromQuote failed", err);
    throw err; // Re-throw so caller can handle specific errors
  }
}

// ============================================================
// SEEDING — run ONLY when VITE_ENABLE_MOCK_DATA=true
// ============================================================

/**
 * Seeds the database from mockData ONLY when the mock flag is enabled.
 * In production (flag disabled), this is a no-op that returns immediately.
 */
export async function seedIfEmpty(): Promise<{
  seeded: boolean;
  details: Record<string, number>;
}> {
  // BLOCKER FIX: Never seed in production
  if (!isMockDataEnabled()) {
    return { seeded: false, details: {} };
  }

  const details: Record<string, number> = {};
  let seeded = false;

  try {
    const existing = await intakesApi.list({}, { limit: 1 });
    if (existing.length === 0) {
      for (const it of mockIntakes) {
        await intakesApi.create({
          code: it.id,
          client_name: it.client,
          contact_person: it.contactPerson,
          channel: it.channel,
          product_family: it.productFamily,
          description: it.description,
          dimensions: it.dimensions,
          quantity: it.quantity,
          status: it.status,
          assigned_to: it.assignedTo,
          notes: it.notes,
          priority: it.priority,
          delivery_type: it.deliveryType,
        });
      }
      details.intakes = mockIntakes.length;
      seeded = true;
    }
  } catch (err) {
    console.warn("[dataStore] seedIfEmpty/intakes error", err);
  }

  try {
    const existing = await quotesApi.list({}, { limit: 1 });
    if (existing.length === 0) {
      for (const q of mockQuotes) {
        await quotesApi.create({
          code: q.id,
          intake_code: q.intakeId,
          client_name: q.client,
          contact_person: q.contactPerson,
          status: q.status,
          version: q.version,
          valid_until: q.validUntil,
          line_items: JSON.stringify(
            q.lineItems.map((li) => ({
              productCode: li.productCode,
              description: li.description,
              quantity: li.quantity,
              unit_price: li.unitPrice,
              total: li.total,
            }))
          ),
          subtotal: q.subtotal,
          discount: q.discount,
          discount_pct: q.discountPct,
          total_before_vat: q.totalBeforeVAT,
          vat: q.vat,
          grand_total: q.grandTotal,
          margin_pct: q.marginPct,
          notes: q.notes,
          assigned_to: q.assignedTo,
        });
      }
      details.quotes = mockQuotes.length;
      seeded = true;
    }
  } catch (err) {
    console.warn("[dataStore] seedIfEmpty/quotes error", err);
  }

  return { seeded, details };
}