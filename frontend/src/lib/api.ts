/* eslint-disable @typescript-eslint/no-explicit-any */
import { createClient } from '@metagptx/web-sdk';
import type { IntakeProductSpec } from './intakeProductSpec';

// Create client instance
export const client: any = createClient({ withCredentials: true });

// ============================================================
// TYPES
// ============================================================
export interface ClientEntity {
  id: number;
  name: string;
  identity_type: 'temp' | 'fiscal';
  temp_ref?: string;
  cui?: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface IntakeRequestEntity {
  id: number;
  code: string;
  client_id?: number;
  client_name: string;
  contact_person?: string;
  channel: string;
  product_family: string;
  description: string;
  dimensions: string;
  quantity: number;
  status: 'new' | 'in_review' | 'needs_info' | 'ready_for_quote' | 'blocked' | 'cancelled';
  assigned_to?: string;
  notes?: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  delivery_type?: string;
  product_spec_json?: IntakeProductSpec | null;
  confirmed_template_code?: string | null;
  confirmed_template_name?: string | null;
  site_audit_json?: import("@/lib/intakeSiteAudit").IntakeSiteAuditJson | null;
  created_at?: string;
  updated_at?: string;
}

export interface QuoteLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
  notes?: string;
}

export interface QuoteEntity {
  id: number;
  code: string;
  intake_id?: number;
  intake_code?: string;
  client_id?: number;
  client_name: string;
  contact_person?: string;
  status: 'draft' | 'priced' | 'sent' | 'viewed' | 'negotiating' | 'accepted' | 'rejected' | 'expired';
  version: number;
  valid_until?: string;
  line_items: string; // JSON-encoded QuoteLineItem[]
  subtotal: number;
  discount?: number;
  discount_pct?: number;
  total_before_vat?: number;
  vat?: number;
  grand_total: number;
  margin_pct?: number;
  notes?: string;
  assigned_to?: string;
  created_at?: string;
  updated_at?: string;
}

export interface OrderEntity {
  id: number;
  code: string;
  quote_id?: number;
  quote_code?: string;
  client_id?: number;
  client_name: string;
  contact_person?: string;
  status: 'created' | 'confirmed' | 'locked' | 'in_execution' | 'completed' | 'cancelled';
  product_summary?: string;
  total_amount: number;
  locked_at?: string;
  promised_delivery?: string;
  job_id?: string;
  payment_status: 'pending' | 'partial' | 'paid';
  snapshot_version?: number;
  snapshot_line_items?: string; // JSON-encoded
  readiness_snapshot?: ReadinessSnapshot | null;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ReadinessSnapshot {
  source: 'backend' | string;
  snapshot_type: string;
  snapshot_at: string;
  readiness_result?: {
    entity_type: string;
    entity_id: string;
    overall_status: string;
    ready_for_quote: boolean;
    contract_version: string;
    policy: Record<string, unknown>;
    source: string;
  } | null;
  warnings_acknowledged?: boolean;
  warnings_acknowledged_at?: string;
  quote_status?: string;
  requires_production_handoff_build?: boolean;
  production_started?: boolean;
  execution_plan_created?: boolean;
  inventory_mutated?: boolean;
  no_execution_plan_created?: boolean;
}

export interface InventoryMaterialEntity {
  id: number;
  code: string;
  name: string;
  category: string;
  unit: string;
  stock_current: number;
  stock_min: number;
  stock_max: number;
  unit_cost: number;
  supplier?: string;
  last_restocked?: string;
  consumption_rate?: number;
  location?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SupplierEntity {
  id: number;
  code: string;
  name: string;
  category: string;
  lead_time_days: number;
  rating: number;
  active_orders: number;
  last_delivery?: string;
  created_at?: string;
  updated_at?: string;
}

// ProductTemplateComponent — structured entity (v2, sprint #14 hardening).
// Legacy shape was `string[]`. Parser in `parseTemplateComponents` below
// performs backward-compat migration: plain strings are lifted to
// { component_id, type: "STRUCTURA", name: <string> } with a warning flag.
// Sprint #27 — canonical 6-type vocabulary from the approved ProductSystem
// spec (Panouri ACP Iluminate). MUST stay in sync with
// ALLOWED_COMPONENT_TYPES in app/backend/services/product_template_contract.py.
// Validation is strict on both sides: unknown values are rejected, never
// coerced or treated as free-text.
export type ProductComponentType =
  | "STRUCTURA"
  | "FATA_ACP_ROUTATA"
  | "DIFUZIE_PLEXI"
  | "ILUMINARE"
  | "RELIEF_PLEXI_10MM"
  | "FINISAJ"
  // BUILD 4: Advertising production types
  | "PRINT_SUBSTRATE"
  | "VINYL_APPLICATION"
  | "PLEXI_PANEL"
  | "FRAME_PROFILE"
  | "LITERE_3D"
  | "ELECTRIC_LED"
  | "EXTERNALIZARE"
  | "TAIERE_CNC_LASER"
  | "LAMINARE";

export const PRODUCT_COMPONENT_TYPES: ProductComponentType[] = [
  "STRUCTURA",
  "FATA_ACP_ROUTATA",
  "DIFUZIE_PLEXI",
  "ILUMINARE",
  "RELIEF_PLEXI_10MM",
  "FINISAJ",
  // BUILD 4: Advertising production types
  "PRINT_SUBSTRATE",
  "VINYL_APPLICATION",
  "PLEXI_PANEL",
  "FRAME_PROFILE",
  "LITERE_3D",
  "ELECTRIC_LED",
  "EXTERNALIZARE",
  "TAIERE_CNC_LASER",
  "LAMINARE",
];

// ProductTemplateOperation — flat shape kept unchanged for backward compat with
// backend (CostEngine, Quote Orchestrator, product_system_service). Sprint #15
// moves operations under components in the UI/draft, but the serialized payload
// continues to include a flat `operations_json` mirror (see draftToPayload).
//
// Sprint #27 — Strict Contract Hardening:
//   - Dual-name fields: the backend (CostEngine v2) canonically accepts BOTH
//     `estimatedMinutes`/`estimated_minutes` and `materialCode`/`material_code`.
//     We carry both for lossless round-trip and surface them via the parser so
//     legacy rows stored with snake_case names are not silently dropped.
//   - Formula fields: `calculation_type`, `formula_id`, `formula_params`,
//     `requires_quote_input` are now first-class on operations AND materials.
//     They MUST be preserved across read -> edit -> save so formula-based lines
//     are not silently downgraded to static zero-cost lines.
//   - `_extras`: any unknown/extra keys in a stored row are preserved verbatim
//     under `_extras` and re-emitted on save. This prevents information loss
//     when a row was written by a newer schema version.
export type CalculationType = "static" | "formula_based";

export interface ProductTemplateOperation {
  code: string;
  name: string;
  workcenter: string;
  // Canonical field is `estimatedMinutes` (camelCase, v15+). Backend also
  // reads `estimated_minutes` (snake_case). Both are carried for parity.
  estimatedMinutes: number;
  estimated_minutes?: number;
  sequence: number;
  // component_ref MUST point to a ProductTemplateComponent.component_id.
  // Empty string = not yet assigned (invalid on save).
  component_ref: string;
  // Sprint #27 — formula fields (optional; ignored for static lines).
  calculation_type?: CalculationType;
  formula_id?: string;
  formula_params?: Record<string, unknown>;
  requires_quote_input?: string[];
  // Unknown/extra keys preserved across round-trips.
  _extras?: Record<string, unknown>;
}

export interface ProductTemplateMaterial {
  // Canonical name is `materialCode` (camelCase, v15+). Backend also accepts
  // `material_code` (snake_case). Both are carried for parity.
  materialCode: string; // MUST match an InventoryMaterialEntity.code from the registry
  material_code?: string;
  name: string;
  quantity: number;
  unit: string;
  // component_ref: which component owns this material. Empty = legacy (global)
  // material distributed to the first component by the parser.
  component_ref?: string;
  // Sprint #27 — formula fields (optional; ignored for static lines).
  calculation_type?: CalculationType;
  formula_id?: string;
  formula_params?: Record<string, unknown>;
  requires_quote_input?: string[];
  // Unknown/extra keys preserved across round-trips.
  _extras?: Record<string, unknown>;
}

// Sprint #15 — Component is the canonical logical container. It owns both
// `operations` and `materials`. The editor exposes add/remove only through
// the owning component. The serialized payload keeps flat top-level mirrors
// (`operations_json`, `required_materials_json`) so the backend remains
// completely untouched — see `draftToPayload` in pages/ProductSystem.tsx.
export interface ProductTemplateComponent {
  component_id: string; // stable id used by operations/materials to reference this component
  type: ProductComponentType;
  name: string;
  operations: ProductTemplateOperation[]; // owned by this component
  materials: ProductTemplateMaterial[]; // owned by this component
  // _legacy=true marks components that were auto-migrated from a bare string
  // or whose `type` was not in the enum. The UI surfaces them so the user
  // must explicitly confirm type+name before saving.
  _legacy?: boolean;
  // _needs_review=true is set by the on-read parser for components that
  // received legacy global materials without `component_ref`. The UI shows
  // an amber banner asking the user to review the distribution.
  _needs_review?: boolean;
}

export interface ProductTemplateEntity {
  id: number;
  template_code: string;
  family_id?: string;
  family_name: string;
  description?: string;
  components_json?: string; // JSON-encoded string[]
  operations_json?: string; // JSON-encoded ProductTemplateOperation[]
  required_materials_json?: string; // JSON-encoded ProductTemplateMaterial[]
  estimated_hours?: number;
  base_labor_rate?: number;
  base_margin_pct?: number;
  active?: boolean;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ProductSystemReadinessBlocker {
  code: string;
  dimension: "technical" | "pricing" | "execution" | "commercial";
  severity: "blocking" | "warning" | "diagnostic";
  owner: string;
  message: string;
  source_code?: string | null;
  target_route?: string | null;
}

export interface ProductSystemReadinessDimension {
  status: string;
  blockers?: ProductSystemReadinessBlocker[];
}

export interface ProductSystemTemplateCapabilities {
  root_offerable: boolean;
  linked_child_offerable: boolean;
  internal_only: boolean;
}

export interface ProductSystemTemplateReadiness {
  technical: ProductSystemReadinessDimension;
  pricing: ProductSystemReadinessDimension;
  execution: ProductSystemReadinessDimension;
  commercial: ProductSystemReadinessDimension;
  rollup:
    | "READY"
    | "PARTIALLY_READY"
    | "BLOCKED"
    | "INTERNAL"
    | "DEPRECATED"
    | string;
}

export interface ProductTemplateAvailabilityItem {
  template_id: number;
  template_code: string;
  family_id?: string | null;
  family_name?: string | null;
  description?: string | null;
  db_active: boolean;
  quote_offerable: boolean;
  runtime_module: boolean;
  is_parent: boolean;
  has_modules: boolean;
  parent_codes: string[];
  module_codes: string[];
  status: string;
  status_reason: string;
  product_system_role:
    | "offerable_product"
    | "candidate_product"
    | "internal_module"
    | "shared_component"
    | "archived_experimental"
    | string;
  display_group:
    | "active_products"
    | "candidate_products"
    | "internal_modules"
    | "shared_components"
    | "archived_experimental"
    | string;
  importance_rank: number;
  owner_decision_required: boolean;
  readiness_reason: string;
  ui_label: string;
  ui_description: string;
  parent_product_codes: string[];
  child_module_codes: string[];
  shared_with_product_codes: string[];
  composition_modules: ProductTemplateCompositionModule[];
  /** Product System SVG-bindable components (optional; Intake consumes later). */
  svg_bindable_components?: SvgBindableComponent[];
  shared_component_contracts: SharedVolumetricComponentSummary[];
  capabilities?: ProductSystemTemplateCapabilities | null;
  readiness?: ProductSystemTemplateReadiness | null;
}

export interface SvgBindableComponent {
  component_template_code: string;
  process_component_code?: string | null;
  owner_label: string;
  accepted_geometry_roles: string[];
  selection_mode: string;
  cardinality: string;
  required: boolean;
  available: boolean;
  active: boolean;
  active_by_default: boolean;
  technical_role?: string | null;
  guards?: string[];
  product_definition_targets?: string[];
  capabilities?: string[];
  svg_binding?: Record<string, unknown>;
}

export interface ProductTemplateCompositionModule {
  role_key: string;
  role_label: string;
  module_template_code: string;
  module_product_system_role?: string | null;
  relation_type?: string | null;
  is_required: boolean;
  sort_order: number;
  ui_hint?: string | null;
  status_label?: string | null;
}

export interface SharedVolumetricComponentSummary {
  component_key: string;
  display_name: string;
  profile_key: "letters" | "logo" | string;
  module_template_code: string;
  confidence: "HIGH" | "MEDIUM" | "LOW" | "PARTIAL" | "NOT_CONFIRMED" | string;
  owner_decision: "APPROVE_AS_DIRECTION" | "KEEP_SEPARATE_NOW" | "NEEDS_MORE_AUDIT" | "FORBIDDEN_NOW" | string;
  shared_truth_fields: string[];
  not_confirmed: string[];
  calculation_strategy_key?: string | null;
  strategy_source_template_code?: string | null;
  strategy_status?: string | null;
  strategy_meaning?: string | null;
  required_truth?: string[];
  shared_module_template_code?: string | null;
  legacy_replaced_by?: string | null;
  reserved_module_template_code?: string | null;
}

export interface ProductTemplateAvailabilityResponse {
  items: ProductTemplateAvailabilityItem[];
  total: number;
  offerable_count: number;
  runtime_module_count: number;
}

// ============================================================
// Helpers for product template JSON fields
// ============================================================

/**
 * Parse the raw `components_json` field WITHOUT legacy-ops/materials
 * distribution. Returns components with EMPTY `operations`/`materials` arrays.
 * For editor-level reads that need a fully populated container, use
 * `parseTemplateComponentsWithLegacy` instead.
 *
 * Backward-compat:
 *   - legacy `string[]` entries are lifted to a minimal component shape with
 *     `_legacy=true` so the UI forces the user to confirm type + name.
 *   - object entries with an unknown `type` also get `_legacy=true`.
 *   - if the stored entries already include nested `operations`/`materials`
 *     (new v15 shape), they are read verbatim; otherwise the arrays start empty
 *     and are populated by the legacy distributor.
 */
export function parseTemplateComponents(
  jsonStr: string | undefined | null
): ProductTemplateComponent[] {
  if (!jsonStr) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonStr);
  } catch {
    return [];
  }
  if (!Array.isArray(parsed)) return [];
  const out: ProductTemplateComponent[] = [];
  parsed.forEach((c, idx) => {
    if (typeof c === "string") {
      const trimmed = c.trim();
      if (!trimmed) return;
      out.push({
        component_id: `comp_legacy_${idx + 1}`,
        type: "STRUCTURA",
        name: trimmed,
        operations: [],
        materials: [],
        _legacy: true,
      });
      return;
    }
    if (c && typeof c === "object") {
      const obj = c as Record<string, unknown>;
      const rawType = String(obj.type ?? "").toUpperCase();
      const typeKnown = (PRODUCT_COMPONENT_TYPES as string[]).includes(rawType);
      const typeSafe: ProductComponentType = typeKnown
        ? (rawType as ProductComponentType)
        : "STRUCTURA";
      // Read nested v15 arrays if present; otherwise empty (legacy distributor
      // will fill them in parseTemplateComponentsWithLegacy).
      const nestedOps = Array.isArray(obj.operations)
        ? normalizeOperationsArray(obj.operations)
        : [];
      const nestedMats = Array.isArray(obj.materials)
        ? normalizeMaterialsArray(obj.materials)
        : [];
      out.push({
        component_id:
          String(obj.component_id ?? obj.id ?? `comp_${idx + 1}`) || `comp_${idx + 1}`,
        type: typeSafe,
        name: String(obj.name ?? ""),
        operations: nestedOps,
        materials: nestedMats,
        _legacy: obj._legacy === true || !typeKnown,
      });
    }
  });
  return out;
}

/**
 * Sprint #15 — On-read backward-compat distributor.
 *
 * Combines the three flat JSON fields of a `ProductTemplateEntity` into the
 * new hierarchical shape where each component owns its own `operations`
 * and `materials`.
 *
 * Distribution rules (legacy rows only — i.e. rows NOT already nested inside
 * a component):
 *   1. Operations with a valid `component_ref` → attached to that component.
 *   2. Operations with empty/unknown `component_ref` → attached to the FIRST
 *      component, and the component is marked `_needs_review=true`.
 *   3. Materials with a `component_ref` matching a component → attached there.
 *   4. Materials without `component_ref` → attached to the FIRST component,
 *      and the component is marked `_needs_review=true`.
 *   5. If there are legacy ops/mats but ZERO components, a synthetic
 *      `comp_auto_1` of type `STRUCTURA` is created to host them, flagged
 *      both `_legacy=true` and `_needs_review=true`.
 *
 * De-dup: nested ops/mats already present inside a component (new v15 shape)
 * are kept as the source of truth; flat rows that match by identity
 * (op.code+op.sequence for ops; material.materialCode for mats) are SKIPPED
 * to avoid doubling after a round-trip (since draftToPayload emits both
 * representations).
 */
export function parseTemplateComponentsWithLegacy(
  componentsJson: string | undefined | null,
  operationsJson: string | undefined | null,
  materialsJson: string | undefined | null
): ProductTemplateComponent[] {
  const components = parseTemplateComponents(componentsJson);
  const flatOps = parseTemplateOperations(operationsJson);
  const flatMats = parseTemplateMaterials(materialsJson);

  // Synthesize a host component if legacy data exists but no components.
  let working = components;
  if (working.length === 0 && (flatOps.length > 0 || flatMats.length > 0)) {
    working = [
      {
        component_id: "comp_auto_1",
        type: "STRUCTURA",
        name: "Componentă auto-generată (revizuiește)",
        operations: [],
        materials: [],
        _legacy: true,
        _needs_review: true,
      },
    ];
  }

  if (working.length === 0) return working;

  const byId = new Map<string, ProductTemplateComponent>();
  working.forEach((c) => byId.set(c.component_id, c));
  const first = working[0];

  // --- Operations distribution ---
  const opKey = (op: ProductTemplateOperation): string =>
    `${op.code}::${op.sequence}`;
  // De-dup against ops already nested inside components.
  const existingOpKeys = new Set<string>();
  working.forEach((c) =>
    c.operations.forEach((op) => existingOpKeys.add(opKey(op)))
  );
  flatOps.forEach((op) => {
    if (existingOpKeys.has(opKey(op))) return; // already nested — skip
    const target = op.component_ref && byId.has(op.component_ref)
      ? byId.get(op.component_ref)!
      : first;
    target.operations.push(op);
    if (!op.component_ref || !byId.has(op.component_ref)) {
      target._needs_review = true;
    }
  });

  // --- Materials distribution ---
  const matKey = (m: ProductTemplateMaterial): string => m.materialCode;
  const existingMatKeys = new Set<string>();
  working.forEach((c) =>
    c.materials.forEach((m) => existingMatKeys.add(matKey(m)))
  );
  flatMats.forEach((m) => {
    if (m.materialCode && existingMatKeys.has(matKey(m))) return;
    const target =
      m.component_ref && byId.has(m.component_ref)
        ? byId.get(m.component_ref)!
        : first;
    target.materials.push(m);
    if (!m.component_ref || !byId.has(m.component_ref)) {
      target._needs_review = true;
    }
  });

  // BUILD 4 nested components_json rows often omit component_ref on child lines;
  // default to the owning component_id so strict save validation can pass.
  working.forEach((c) => {
    const cid = (c.component_id || "").trim();
    if (!cid) return;
    c.operations.forEach((op) => {
      if (!(op.component_ref || "").trim()) op.component_ref = cid;
    });
    c.materials.forEach((m) => {
      if (!(m.component_ref || "").trim()) m.component_ref = cid;
    });
  });

  return working;
}

// Sprint #27 — known keys lists. Everything NOT in the known-set is preserved
// under `_extras` so a newer backend schema never loses data on a frontend
// round-trip.
const KNOWN_OP_KEYS = new Set<string>([
  "code",
  "name",
  "workcenter",
  "estimatedMinutes",
  "estimated_minutes",
  "sequence",
  "component_ref",
  "calculation_type",
  "formula_id",
  "formula_params",
  "requires_quote_input",
]);

const KNOWN_MAT_KEYS = new Set<string>([
  "materialCode",
  "material_code",
  "name",
  "quantity",
  "unit",
  "component_ref",
  "calculation_type",
  "formula_id",
  "formula_params",
  "requires_quote_input",
]);

function pickExtras(
  obj: Record<string, unknown>,
  known: Set<string>
): Record<string, unknown> | undefined {
  const out: Record<string, unknown> = {};
  let hasAny = false;
  for (const k of Object.keys(obj)) {
    if (!known.has(k) && k !== "_extras") {
      out[k] = obj[k];
      hasAny = true;
    }
  }
  return hasAny ? out : undefined;
}

function coerceCalculationType(v: unknown): CalculationType | undefined {
  if (typeof v !== "string") return undefined;
  const s = v.trim().toLowerCase();
  if (s === "formula_based") return "formula_based";
  if (s === "static") return "static";
  return undefined;
}

function coerceStringArray(v: unknown): string[] | undefined {
  if (!Array.isArray(v)) return undefined;
  const out = v.filter((x): x is string => typeof x === "string" && x.length > 0);
  return out.length > 0 ? out : undefined;
}

function coerceObject(v: unknown): Record<string, unknown> | undefined {
  if (v && typeof v === "object" && !Array.isArray(v)) {
    return v as Record<string, unknown>;
  }
  return undefined;
}

function normalizeOperationsArray(arr: unknown[]): ProductTemplateOperation[] {
  return arr
    .filter((op): op is Record<string, unknown> => !!op && typeof op === "object")
    .map((op) => {
      // Dual-name: prefer camelCase, fall back to snake_case.
      const minsCamel = op.estimatedMinutes;
      const minsSnake = op.estimated_minutes;
      const mins =
        minsCamel !== undefined && minsCamel !== null
          ? Number(minsCamel) || 0
          : Number(minsSnake ?? 0) || 0;
      const calcType = coerceCalculationType(op.calculation_type);
      // BUILD 4 seeds use `label` for the visible title; hydrate `name` when missing.
      const operationName = String(op.name || op.label || "");
      const out: ProductTemplateOperation = {
        code: String(op.code ?? ""),
        name: operationName,
        workcenter: String(op.workcenter ?? ""),
        estimatedMinutes: mins,
        estimated_minutes: mins,
        sequence: Number(op.sequence ?? 0) || 0,
        component_ref: String(op.component_ref ?? ""),
      };
      if (calcType) out.calculation_type = calcType;
      const fid = op.formula_id;
      if (typeof fid === "string" && fid.length > 0) out.formula_id = fid;
      const fparams = coerceObject(op.formula_params);
      if (fparams) out.formula_params = fparams;
      const req = coerceStringArray(op.requires_quote_input);
      if (req) out.requires_quote_input = req;
      // Preserve pre-existing _extras (from a prior round-trip) merged with
      // any newly-unknown keys seen on this read.
      const prevExtras = coerceObject(op._extras);
      const newExtras = pickExtras(op, KNOWN_OP_KEYS);
      const merged = { ...(prevExtras || {}), ...(newExtras || {}) };
      if (Object.keys(merged).length > 0) out._extras = merged;
      return out;
    });
}

function normalizeMaterialsArray(arr: unknown[]): ProductTemplateMaterial[] {
  return arr
    .filter((m): m is Record<string, unknown> => !!m && typeof m === "object")
    .map((m) => {
      // Dual-name: prefer camelCase, fall back to snake_case.
      const codeCamel = m.materialCode;
      const codeSnake = m.material_code;
      const code =
        codeCamel !== undefined && codeCamel !== null && String(codeCamel).length > 0
          ? String(codeCamel)
          : String(codeSnake ?? "");
      const calcType = coerceCalculationType(m.calculation_type);
      const out: ProductTemplateMaterial = {
        materialCode: code,
        material_code: code,
        name: String(m.name ?? ""),
        quantity: Number(m.quantity ?? 0) || 0,
        unit: String(m.unit ?? ""),
        component_ref: m.component_ref ? String(m.component_ref) : undefined,
      };
      if (calcType) out.calculation_type = calcType;
      const fid = m.formula_id;
      if (typeof fid === "string" && fid.length > 0) out.formula_id = fid;
      const fparams = coerceObject(m.formula_params);
      if (fparams) out.formula_params = fparams;
      const req = coerceStringArray(m.requires_quote_input);
      if (req) out.requires_quote_input = req;
      const prevExtras = coerceObject(m._extras);
      const newExtras = pickExtras(m, KNOWN_MAT_KEYS);
      const merged = { ...(prevExtras || {}), ...(newExtras || {}) };
      if (Object.keys(merged).length > 0) out._extras = merged;
      return out;
    });
}

// ============================================================
// Sprint #27 — STRICT VALIDATION (pre-save parity with backend 422s)
// ============================================================
export interface TemplateStructuralError {
  path: string;
  code:
    | "COMPONENT_ID_EMPTY"
    | "COMPONENT_ID_DUPLICATE"
    | "COMPONENT_TYPE_INVALID"
    | "COMPONENT_NAME_EMPTY"
    | "OPERATION_CODE_EMPTY"
    | "OPERATION_WORKCENTER_EMPTY"
    | "OPERATION_MINUTES_NON_POSITIVE"
    | "OPERATION_SEQUENCE_NON_POSITIVE"
    | "OPERATION_FORMULA_ID_EMPTY"
    | "MATERIAL_CODE_EMPTY"
    | "MATERIAL_QUANTITY_NON_POSITIVE"
    | "MATERIAL_UNIT_EMPTY"
    | "MATERIAL_FORMULA_ID_EMPTY"
    | "COMPONENT_REF_ORPHAN"
    | "COMPONENT_LEGACY_UNCONFIRMED";
  detail: string;
}

/**
 * Strict structural validator — MUST match backend router 422s byte-for-byte.
 *
 * Rules (Sprint #27 canonical):
 *   - Each component has non-empty `component_id`, valid `type` from
 *     PRODUCT_COMPONENT_TYPES, non-empty `name`.
 *   - `component_id`s are unique.
 *   - No `_legacy` components (must be confirmed before save).
 *   - Each operation has non-empty `code`, non-empty `workcenter`,
 *     `estimatedMinutes > 0` (unless formula_based with a formula_id),
 *     `sequence > 0`, `component_ref` resolving to an existing component_id.
 *   - Each material has non-empty `materialCode`, `quantity > 0` (unless
 *     formula_based), non-empty `unit`, `component_ref` resolving to an
 *     existing component_id.
 *   - Formula-based lines MUST declare a non-empty `formula_id`.
 */
export function validateTemplateComponentsStrict(
  components: ProductTemplateComponent[]
): TemplateStructuralError[] {
  const errors: TemplateStructuralError[] = [];
  const knownTypes = new Set<string>(PRODUCT_COMPONENT_TYPES);
  const seenIds = new Set<string>();

  components.forEach((c, i) => {
    const cPath = `components[${i}]`;
    const cid = (c.component_id || "").trim();
    if (!cid) {
      errors.push({
        path: `${cPath}.component_id`,
        code: "COMPONENT_ID_EMPTY",
        detail: "component_id must be a non-empty string",
      });
    } else if (seenIds.has(cid)) {
      errors.push({
        path: `${cPath}.component_id`,
        code: "COMPONENT_ID_DUPLICATE",
        detail: `component_id '${cid}' is not unique`,
      });
    } else {
      seenIds.add(cid);
    }
    if (!knownTypes.has(String(c.type))) {
      errors.push({
        path: `${cPath}.type`,
        code: "COMPONENT_TYPE_INVALID",
        detail: `type must be one of ${PRODUCT_COMPONENT_TYPES.join(", ")}`,
      });
    }
    if (!(c.name || "").trim()) {
      errors.push({
        path: `${cPath}.name`,
        code: "COMPONENT_NAME_EMPTY",
        detail: "component name must be a non-empty string",
      });
    }
    if (c._legacy === true) {
      errors.push({
        path: cPath,
        code: "COMPONENT_LEGACY_UNCONFIRMED",
        detail: "legacy-imported component must be confirmed (type + name) before save",
      });
    }
  });

  const compIds = new Set<string>(
    components.map((c) => (c.component_id || "").trim()).filter((x) => x.length > 0)
  );

  components.forEach((c, i) => {
    const cPath = `components[${i}]`;
    c.operations.forEach((op, j) => {
      const opPath = `${cPath}.operations[${j}]`;
      if (!(op.code || "").trim()) {
        errors.push({
          path: `${opPath}.code`,
          code: "OPERATION_CODE_EMPTY",
          detail: "operation.code must be a non-empty string",
        });
      }
      if (!(op.workcenter || "").trim()) {
        errors.push({
          path: `${opPath}.workcenter`,
          code: "OPERATION_WORKCENTER_EMPTY",
          detail: "operation.workcenter must be a non-empty string",
        });
      }
      const isFormula = op.calculation_type === "formula_based";
      if (isFormula) {
        if (!(op.formula_id || "").trim()) {
          errors.push({
            path: `${opPath}.formula_id`,
            code: "OPERATION_FORMULA_ID_EMPTY",
            detail: "formula_based operation must declare a non-empty formula_id",
          });
        }
      } else {
        if (!(Number(op.estimatedMinutes) > 0)) {
          errors.push({
            path: `${opPath}.estimatedMinutes`,
            code: "OPERATION_MINUTES_NON_POSITIVE",
            detail: "static operation must have estimatedMinutes > 0",
          });
        }
      }
      if (!(Number(op.sequence) > 0)) {
        errors.push({
          path: `${opPath}.sequence`,
          code: "OPERATION_SEQUENCE_NON_POSITIVE",
          detail: "operation.sequence must be > 0",
        });
      }
      const ref = (op.component_ref || "").trim();
      if (!ref || !compIds.has(ref)) {
        errors.push({
          path: `${opPath}.component_ref`,
          code: "COMPONENT_REF_ORPHAN",
          detail: `operation.component_ref '${ref}' does not resolve to a component_id`,
        });
      }
    });
    c.materials.forEach((m, j) => {
      const mPath = `${cPath}.materials[${j}]`;
      if (!(m.materialCode || "").trim()) {
        errors.push({
          path: `${mPath}.materialCode`,
          code: "MATERIAL_CODE_EMPTY",
          detail: "material.materialCode must be a non-empty string",
        });
      }
      if (!(m.unit || "").trim()) {
        errors.push({
          path: `${mPath}.unit`,
          code: "MATERIAL_UNIT_EMPTY",
          detail: "material.unit must be a non-empty string",
        });
      }
      const isFormula = m.calculation_type === "formula_based";
      if (isFormula) {
        if (!(m.formula_id || "").trim()) {
          errors.push({
            path: `${mPath}.formula_id`,
            code: "MATERIAL_FORMULA_ID_EMPTY",
            detail: "formula_based material must declare a non-empty formula_id",
          });
        }
      } else {
        if (!(Number(m.quantity) > 0)) {
          errors.push({
            path: `${mPath}.quantity`,
            code: "MATERIAL_QUANTITY_NON_POSITIVE",
            detail: "static material must have quantity > 0",
          });
        }
      }
      const ref = (m.component_ref || "").trim();
      if (!ref || !compIds.has(ref)) {
        errors.push({
          path: `${mPath}.component_ref`,
          code: "COMPONENT_REF_ORPHAN",
          detail: `material.component_ref '${ref}' does not resolve to a component_id`,
        });
      }
    });
  });

  return errors;
}

export function parseTemplateOperations(
  jsonStr: string | undefined | null
): ProductTemplateOperation[] {
  if (!jsonStr) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonStr);
  } catch {
    return [];
  }
  if (!Array.isArray(parsed)) return [];
  return normalizeOperationsArray(parsed);
}

export function parseTemplateMaterials(
  jsonStr: string | undefined | null
): ProductTemplateMaterial[] {
  if (!jsonStr) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonStr);
  } catch {
    return [];
  }
  if (!Array.isArray(parsed)) return [];
  return normalizeMaterialsArray(parsed);
}

// ============================================================
// HELPERS — LINE ITEMS
// ============================================================
export function parseLineItems(jsonStr: string | undefined | null): QuoteLineItem[] {
  if (!jsonStr) return [];
  try {
    const parsed = JSON.parse(jsonStr);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function stringifyLineItems(items: QuoteLineItem[]): string {
  return JSON.stringify(items);
}

// ============================================================
// GENERIC CRUD FACTORY
// ============================================================
function makeCrud<T>(tableName: string) {
  return {
    list: async (query: Record<string, unknown> = {}, opts: { sort?: string; limit?: number; skip?: number } = {}): Promise<T[]> => {
      const res = await client.entities[tableName].query({
        query,
        sort: opts.sort ?? '-created_at',
        limit: opts.limit ?? 500,
        skip: opts.skip ?? 0,
      });
      return (res?.data?.items ?? []) as T[];
    },
    get: async (id: number): Promise<T | null> => {
      try {
        const res = await client.entities[tableName].get({ id });
        return (res?.data ?? null) as T | null;
      } catch {
        return null;
      }
    },
    create: async (data: Partial<T>): Promise<T> => {
      const res = await client.entities[tableName].create({ data });
      return res?.data as T;
    },
    update: async (id: number, data: Partial<T>): Promise<T> => {
      const res = await client.entities[tableName].update({ id, data });
      return res?.data as T;
    },
    remove: async (id: number): Promise<void> => {
      await client.entities[tableName].delete({ id });
    },
  };
}

// ============================================================
// ENTITY APIS
// ============================================================
export const clientsApi = makeCrud<ClientEntity>('clients');
export const intakesApi = makeCrud<IntakeRequestEntity>('intake_requests');
export const quotesApi = makeCrud<QuoteEntity>('quotes');
export const ordersApi = makeCrud<OrderEntity>('orders');
export const materialsApi = makeCrud<InventoryMaterialEntity>('inventory_materials');
export const suppliersApi = makeCrud<SupplierEntity>('suppliers');
export const productTemplatesApi = makeCrud<ProductTemplateEntity>('product_templates');

export const productTemplateAvailabilityApi = {
  list: async (
    opts: {
      offerable_only?: boolean;
      include_runtime_modules?: boolean;
      include_archived?: boolean;
    } = {}
  ): Promise<ProductTemplateAvailabilityResponse> => {
    const { getAPIBaseURL } = await import('./config');
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(opts)) {
      if (typeof value === 'boolean') params.set(key, String(value));
    }
    const qs = params.toString();
    const response = await fetch(
      `${getAPIBaseURL()}/api/v1/product-system/template-availability${qs ? `?${qs}` : ''}`,
      { credentials: 'include' }
    );
    if (!response.ok) {
      throw new Error(`Product template availability lookup failed (${response.status}).`);
    }
    return (await response.json()) as ProductTemplateAvailabilityResponse;
  },
};

// Shortcut helpers
export const listIntakes = () => intakesApi.list();
export const getIntake = (id: number) => intakesApi.get(id);
export const createIntake = (data: Partial<IntakeRequestEntity>) => intakesApi.create(data);
export const updateIntake = (id: number, data: Partial<IntakeRequestEntity>) => intakesApi.update(id, data);
export const deleteIntake = (id: number) => intakesApi.remove(id);

export const listQuotes = () => quotesApi.list();
export const getQuote = (id: number) => quotesApi.get(id);
export const createQuote = (data: Partial<QuoteEntity>) => quotesApi.create(data);
export const updateQuote = (id: number, data: Partial<QuoteEntity>) => quotesApi.update(id, data);
export const deleteQuote = (id: number) => quotesApi.remove(id);

export const listOrders = () => ordersApi.list();
export const getOrder = (id: number) => ordersApi.get(id);
export const createOrder = (data: Partial<OrderEntity>) => ordersApi.create(data);
export const updateOrder = (id: number, data: Partial<OrderEntity>) => ordersApi.update(id, data);
export const deleteOrder = (id: number) => ordersApi.remove(id);

export const listClients = () => clientsApi.list();
export const getClient = (id: number) => clientsApi.get(id);
export const createClientEntity = (data: Partial<ClientEntity>) => clientsApi.create(data);
export const updateClient = (id: number, data: Partial<ClientEntity>) => clientsApi.update(id, data);

export type ClientTaxIdLookupStatus = 'invalid_input' | 'none' | 'single' | 'conflict';

export interface ClientTaxIdLookupResponse {
  status: ClientTaxIdLookupStatus;
  normalized_tax_id: string | null;
  matches: ClientEntity[];
  message: string;
}

type FiscalNormalizedClientFields = {
  tax_id: string;
  company_name: string;
  address?: string | null;
  city?: string | null;
  county?: string | null;
  registration_number?: string | null;
};

const EMPTY_LOOKUP_MARKERS = new Set(['—', '-', 'n/a', 'na']);

function cleanLookupText(value: string | null | undefined): string | null {
  if (!value) return null;
  const text = value.trim();
  if (!text) return null;
  if (EMPTY_LOOKUP_MARKERS.has(text.toLowerCase())) return null;
  return text;
}

export function buildClientCreateFromFiscalNormalized(
  normalized: FiscalNormalizedClientFields
): Partial<ClientEntity> {
  const taxId = cleanLookupText(normalized.tax_id);
  const companyName = cleanLookupText(normalized.company_name);
  if (!taxId || !companyName) {
    throw new Error('Missing valid tax_id or company_name for client create.');
  }

  const payload: Partial<ClientEntity> = {
    name: companyName,
    identity_type: 'fiscal',
    cui: taxId,
  };
  const address = cleanLookupText(normalized.address);
  const city = cleanLookupText(normalized.city);
  if (address) payload.address = address;
  if (city) payload.city = city;
  return payload;
}

export function buildClientUpdateFromFiscalNormalized(
  existing: ClientEntity,
  normalized: FiscalNormalizedClientFields
): Partial<ClientEntity> {
  const updates: Partial<ClientEntity> = {};
  const companyName = cleanLookupText(normalized.company_name);
  const taxId = cleanLookupText(normalized.tax_id);
  const address = cleanLookupText(normalized.address);
  const city = cleanLookupText(normalized.city);

  if (companyName) updates.name = companyName;
  if (taxId) updates.cui = taxId;
  if (existing.identity_type !== 'fiscal') updates.identity_type = 'fiscal';
  if (address) updates.address = address;
  if (city) updates.city = city;
  return updates;
}

export type ClientFiscalDisplayStatus = 'saved' | 'missing_cui' | 'non_fiscal';

export function getClientFiscalDisplayStatus(
  client: Pick<ClientEntity, 'identity_type' | 'cui'>
): ClientFiscalDisplayStatus {
  if (client.identity_type === 'fiscal' && client.cui) return 'saved';
  if (client.identity_type === 'fiscal' && !client.cui) return 'missing_cui';
  return 'non_fiscal';
}

export function getClientFiscalDisplayLabel(status: ClientFiscalDisplayStatus): string {
  switch (status) {
    case 'saved':
      return 'Date fiscale salvate';
    case 'missing_cui':
      return 'CUI lipsă';
    case 'non_fiscal':
      return 'Client fără identificare fiscală';
  }
}

export async function lookupClientsByTaxId(taxId: string): Promise<ClientTaxIdLookupResponse> {
  const { getAPIBaseURL } = await import('./config');
  const response = await fetch(
    `${getAPIBaseURL()}/api/v1/entities/clients/by-tax-id?tax_id=${encodeURIComponent(taxId)}`,
    { credentials: 'include' }
  );
  if (!response.ok) {
    throw new Error(`Client tax id lookup failed (${response.status}).`);
  }
  return (await response.json()) as ClientTaxIdLookupResponse;
}

export const listMaterials = () => materialsApi.list();
export const updateMaterial = (id: number, data: Partial<InventoryMaterialEntity>) => materialsApi.update(id, data);

export const listSuppliers = () => suppliersApi.list();