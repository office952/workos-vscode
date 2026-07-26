/**
 * Pricing Registry — registry intern de referință.
 *
 * Pricing = Material / Reguli comerciale / Cost intern / Capacitate / Analytics.
 * NU este hub unic de ofertare. Oferta oficială = Snapshot V2, nu edit live aici.
 * Inventory = stoc, furnizori, achiziții (nu sursa de adevăr pentru ofertare).
 *
 * Date live din GET /api/v1/pricing/registry — doar rânduri folosite de template-uri.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Layers,
  FileText,
  Pencil,
  History,
  Info,
  X,
  Settings2,
  ShieldCheck,
  CircleDot,
  Ban,
} from "lucide-react";
import {
  inventoryMaterialsAdminApi,
  type InventoryMaterialDTO,
  type PriceHistoryEntryDTO,
} from "@/api/inventoryMaterialsAdmin";
import {
  commercialMarkupPoliciesAdminApi,
  type CommercialMarkupPolicy,
  type CommercialMarkupDryRunResult,
} from "@/api/commercialMarkupPoliciesAdmin";
import {
  pricingRegistryApi,
  type PricingRegistryItem,
  type PricingRegistryResponse,
} from "@/api/pricingRegistry";
import {
  workcenterRatesAdminApi,
  type WorkcenterRateDTO,
} from "@/api/workcenterRatesAdmin";
import { costEngineApi } from "@/api/costEngine";
import {
  MATERIAL_STATUS_OPTIONS,
  SOURCE_REVIEW_STATUS_OPTIONS,
  WORKCENTER_STATUS_OPTIONS,
  RATE_BASIS_OPTIONS,
  validateMaterialEditPayload,
  buildMaterialPatchPayload,
  validateWorkcenterEditPayload,
  buildWorkcenterPatchPayload,
  RECENT_TEMPLATES_STORAGE_KEY,
  pushRecentTemplate,
  resolveTemplateCode,
  confidenceBadgeLabel,
  statusBadgeLabel,
  type MaterialEditFormState,
  type WorkcenterEditFormState,
  type PricingMainView,
} from "@/lib/pricingRegistry";
import { StatusBadge } from "@/components/workos/design-system";
import { PricingRegistrySpaciousView } from "@/components/pricing/PricingRegistrySpaciousView";
import {
  FAVORITE_TEMPLATES_STORAGE_KEY,
  toggleFavoriteTemplate,
} from "@/components/pricing/pricingRegistryUi";
import type { InventoryMaterialPatchPayload } from "@/api/inventoryMaterialsAdmin";

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtCost(n: number | null | undefined, currency?: string | null): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "Lipsă";
  const formatted = n.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  return currency ? `${formatted} ${currency}` : `${formatted} RON`;
}

function fmtDate(d: string | null | undefined): string {
  if (!d) return "Lipsă";
  try {
    return new Date(d).toLocaleDateString("ro-RO", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return d;
  }
}

// ── Status / Gate helpers ─────────────────────────────────────────────────────

type ReadinessGate = "ready" | "blocked" | "needs_review" | "missing_source" | "no_price";

function computeGate(mat: InventoryMaterialDTO, hasMarkup: boolean): ReadinessGate {
  if (mat.unit_cost === null || mat.unit_cost === undefined) return "no_price";
  if (mat.source_review_status === "rejected") return "blocked";
  if (mat.source_review_status === "pending" || mat.source_review_status === "needs_review") return "needs_review";
  if (!mat.source_name && !mat.source_url) return "missing_source";
  if (!hasMarkup) return "needs_review";
  return "ready";
}

const gateConfig: Record<ReadinessGate, { label: string }> = {
  ready: { label: "Pregătit" },
  blocked: { label: "Blocat" },
  needs_review: { label: "Necesită verificare" },
  missing_source: { label: "Sursă lipsă" },
  no_price: { label: "Preț lipsă" },
};

// ── Markup matching ───────────────────────────────────────────────────────────

interface AppliedMarkupInfo {
  policy: CommercialMarkupPolicy;
  scope: string;
  displayValue: string;
}

function findApplicableMarkup(
  mat: InventoryMaterialDTO,
  policies: CommercialMarkupPolicy[]
): AppliedMarkupInfo | null {
  // Priority: material > subcategory > category > global (highest priority number wins)
  const activePolicies = policies.filter((p) => p.status === "active");

  // Material-level
  const materialMatch = activePolicies
    .filter((p) => p.scope_type === "material" && p.scope_value === mat.code)
    .sort((a, b) => b.priority - a.priority)[0];
  if (materialMatch) return formatPolicyInfo(materialMatch, "material");

  // Subcategory-level
  if (mat.subcategory) {
    const subMatch = activePolicies
      .filter((p) => p.scope_type === "subcategory" && p.scope_value === mat.subcategory)
      .sort((a, b) => b.priority - a.priority)[0];
    if (subMatch) return formatPolicyInfo(subMatch, "subcategory");
  }

  // Category-level
  if (mat.category) {
    const catMatch = activePolicies
      .filter((p) => p.scope_type === "category" && p.scope_value === mat.category)
      .sort((a, b) => b.priority - a.priority)[0];
    if (catMatch) return formatPolicyInfo(catMatch, "category");
  }

  // Global
  const globalMatch = activePolicies
    .filter((p) => p.scope_type === "global")
    .sort((a, b) => b.priority - a.priority)[0];
  if (globalMatch) return formatPolicyInfo(globalMatch, "global");

  return null;
}

function formatPolicyInfo(policy: CommercialMarkupPolicy, scope: string): AppliedMarkupInfo {
  let displayValue = "";
  if (policy.markup_type === "percent" && policy.markup_percent != null) {
    displayValue = `${policy.markup_percent}%`;
  } else if (policy.markup_type === "fixed" && policy.markup_fixed != null) {
    displayValue = `+${policy.markup_fixed} ${policy.currency || "RON"}`;
  } else if (policy.markup_type === "hybrid") {
    const parts: string[] = [];
    if (policy.markup_percent != null) parts.push(`${policy.markup_percent}%`);
    if (policy.markup_fixed != null) parts.push(`+${policy.markup_fixed}`);
    displayValue = parts.join(" ") || "Hybrid";
  }
  return { policy, scope, displayValue };
}

function computeEstimatedNetPrice(
  mat: InventoryMaterialDTO,
  markup: AppliedMarkupInfo | null
): { value: number | null; reason: string | null } {
  if (mat.unit_cost === null || mat.unit_cost === undefined) {
    return { value: null, reason: "Cost cumpărare lipsă" };
  }
  if (!markup) {
    return { value: null, reason: "Adaos lipsă" };
  }
  const cost = mat.unit_cost;
  let markupAmount = 0;
  if (markup.policy.markup_type === "percent" && markup.policy.markup_percent != null) {
    markupAmount = cost * (markup.policy.markup_percent / 100);
  } else if (markup.policy.markup_type === "fixed" && markup.policy.markup_fixed != null) {
    markupAmount = markup.policy.markup_fixed;
  } else if (markup.policy.markup_type === "hybrid") {
    if (markup.policy.markup_percent != null) markupAmount += cost * (markup.policy.markup_percent / 100);
    if (markup.policy.markup_fixed != null) markupAmount += markup.policy.markup_fixed;
  }
  return { value: cost + markupAmount, reason: null };
}

// ── Source review status display ──────────────────────────────────────────────

function sourceStatusLabel(status: string | null | undefined): string {
  if (!status) return "Neverificată";
  switch (status) {
    case "accepted": return "Verificată";
    case "pending": return "În așteptare";
    case "needs_review": return "Necesită verificare";
    case "rejected": return "Respinsă";
    default: return status;
  }
}

// ── Scope label ───────────────────────────────────────────────────────────────

function scopeLabel(scope: string): string {
  switch (scope) {
    case "global": return "Global";
    case "category": return "Categorie";
    case "subcategory": return "Subcategorie";
    case "material": return "Material";
    default: return scope;
  }
}

// ── Markup status label ───────────────────────────────────────────────────────

function markupStatusLabel(status: string): string {
  switch (status) {
    case "active": return "Activ";
    case "draft": return "Draft";
    case "archived": return "Arhivat";
    default: return status;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENT: registryItemToMatDto helper
// ══════════════════════════════════════════════════════════════════════════════

function registryItemToMatDto(item: PricingRegistryItem): InventoryMaterialDTO {
  return {
    id: 0,
    code: item.pricing_code,
    name: item.display_name,
    category: item.registry_category,
    unit: item.unit,
    unit_cost: item.base_cost,
    currency: item.currency,
    vat_percent: item.vat_percent ?? null,
    source_notes: item.source_notes ?? null,
    source_review_status:
      item.confidence === "owner_confirmed"
        ? "accepted_override"
        : item.confidence === "estimated"
          ? "needs_review"
          : null,
    status: item.status,
  };
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENT: GateBadge
// ══════════════════════════════════════════════════════════════════════════════

function GateBadge({ gate }: { gate: ReadinessGate }) {
  const cfg = gateConfig[gate];
  return (
    <StatusBadge
      domain="pricing"
      status={gate}
      label={cfg.label}
      size="sm"
      className="text-[11px] font-medium"
    />
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENT: MarkupRulesDrawer
// ══════════════════════════════════════════════════════════════════════════════

function MarkupRulesDrawer({
  open,
  onClose,
  policies,
}: {
  open: boolean;
  onClose: () => void;
  policies: CommercialMarkupPolicy[];
}) {
  if (!open) return null;

  const grouped = {
    active: policies.filter((p) => p.status === "active"),
    draft: policies.filter((p) => p.status === "draft"),
    archived: policies.filter((p) => p.status === "archived"),
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-lg bg-wo-surface-inset border-l border-border overflow-y-auto">
        {/* Drawer header */}
        <div className="sticky top-0 z-10 bg-wo-surface-inset border-b border-border px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h2 className="text-[16px] font-bold text-foreground">Reguli Adaos Comercial</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-muted transition-colors">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3 text-center">
              <p className="text-[18px] font-bold text-emerald-600 dark:text-emerald-400">{grouped.active.length}</p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Active</p>
            </div>
            <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3 text-center">
              <p className="text-[18px] font-bold text-muted-foreground">{grouped.draft.length}</p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Draft</p>
            </div>
            <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3 text-center">
              <p className="text-[18px] font-bold text-muted-foreground">{grouped.archived.length}</p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Arhivate</p>
            </div>
          </div>

          {/* Active policies */}
          {grouped.active.length > 0 && (
            <div>
              <h3 className="text-[12px] font-semibold text-foreground uppercase tracking-wide mb-3">Reguli Active</h3>
              <div className="space-y-2">
                {grouped.active.map((p) => (
                  <PolicyRow key={p.id} policy={p} />
                ))}
              </div>
            </div>
          )}

          {/* Draft policies */}
          {grouped.draft.length > 0 && (
            <div>
              <h3 className="text-[12px] font-semibold text-muted-foreground uppercase tracking-wide mb-3">Reguli Draft</h3>
              <div className="space-y-2">
                {grouped.draft.map((p) => (
                  <PolicyRow key={p.id} policy={p} />
                ))}
              </div>
            </div>
          )}

          {policies.length === 0 && (
            <div className="text-center py-8">
              <Settings2 className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
              <p className="text-[12px] text-muted-foreground">Nu există reguli de adaos configurate.</p>
            </div>
          )}

          <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-3">
            <p className="text-[11px] text-amber-200 leading-relaxed">
              <Ban className="w-3 h-3 inline mr-1" />
              Editare reguli adaos — build separat. Regulile sunt vizibile aici, dar modificarea se face într-un flux dedicat.
            </p>
          </div>

          {/* Notice */}
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              <Info className="w-3 h-3 inline mr-1 text-blue-600 dark:text-blue-400" />
              Regulile de adaos sunt aplicate automat la calculul prețului net estimat.
              Prioritatea determină regula câștigătoare: material &gt; subcategorie &gt; categorie &gt; global.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function PolicyRow({ policy }: { policy: CommercialMarkupPolicy }) {
  let valueDisplay = "";
  if (policy.markup_type === "percent" && policy.markup_percent != null) {
    valueDisplay = `${policy.markup_percent}%`;
  } else if (policy.markup_type === "fixed" && policy.markup_fixed != null) {
    valueDisplay = `+${policy.markup_fixed} ${policy.currency || "RON"}`;
  } else if (policy.markup_type === "hybrid") {
    const parts: string[] = [];
    if (policy.markup_percent != null) parts.push(`${policy.markup_percent}%`);
    if (policy.markup_fixed != null) parts.push(`+${policy.markup_fixed}`);
    valueDisplay = parts.join(" + ") || "Hybrid";
  }

  return (
    <div className="bg-card border border-border rounded-lg p-3">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <StatusBadge
            domain="pricing"
            status={policy.status}
            label={markupStatusLabel(policy.status)}
            className="text-[10px]"
          />
          <span className="text-[10px] text-muted-foreground uppercase">{scopeLabel(policy.scope_type)}</span>
        </div>
        <span className="text-[13px] font-bold text-foreground">{valueDisplay}</span>
      </div>
      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
        <span>Scop: <span className="text-foreground">{policy.scope_value || "—"}</span></span>
        <span>Prioritate: <span className="text-foreground">{policy.priority}</span></span>
        {policy.rounding_mode !== "none" && (
          <span>Rotunjire: <span className="text-foreground">{policy.rounding_mode}</span></span>
        )}
      </div>
      {policy.notes && (
        <p className="text-[10px] text-muted-foreground mt-1.5 italic">{policy.notes}</p>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENT: MaterialDetailDrawer
// ══════════════════════════════════════════════════════════════════════════════

function MaterialDetailDrawer({
  material,
  markup,
  onClose,
  dryRunResult,
  priceHistory,
  loadingHistory,
}: {
  material: InventoryMaterialDTO | null;
  markup: AppliedMarkupInfo | null;
  onClose: () => void;
  dryRunResult: CommercialMarkupDryRunResult | null;
  priceHistory: PriceHistoryEntryDTO[];
  loadingHistory: boolean;
}) {
  if (!material) return null;

  const estimated = computeEstimatedNetPrice(material, markup);
  const gate = computeGate(material, markup !== null);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-xl bg-wo-surface-inset border-l border-border overflow-y-auto">
        {/* Drawer header */}
        <div className="sticky top-0 z-10 bg-wo-surface-inset border-b border-border px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-[16px] font-bold text-foreground">{material.name}</h2>
            <p className="text-[12px] font-mono text-blue-600 dark:text-blue-400 mt-0.5">{material.code}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-muted transition-colors">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-5">
          {/* Gate */}
          <div className="flex items-center gap-3">
            <GateBadge gate={gate} />
            {material.category && (
              <span className="text-[11px] text-muted-foreground bg-muted px-2 py-0.5 rounded">
                {material.category}{material.subcategory ? ` / ${material.subcategory}` : ""}
              </span>
            )}
          </div>

          {/* Cost section */}
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
            <h3 className="text-[11px] text-muted-foreground uppercase tracking-wide mb-3">Cost Cumpărare Net</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-muted-foreground mb-0.5">Preț unitar</p>
                <p className="text-[16px] font-bold text-foreground">{fmtCost(material.unit_cost, material.currency)}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground mb-0.5">Unitate</p>
                <p className="text-[14px] text-foreground">{material.unit || "Lipsă"}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground mb-0.5">Furnizor</p>
                <p className="text-[12px] text-muted-foreground">{material.supplier || "Lipsă"}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground mb-0.5">Valid din</p>
                <p className="text-[12px] text-muted-foreground">{fmtDate(material.valid_from)}</p>
              </div>
            </div>
          </div>

          {/* Source section */}
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
            <h3 className="text-[11px] text-muted-foreground uppercase tracking-wide mb-3">Sursă & Verificare</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-muted-foreground mb-0.5">Status verificare</p>
                <StatusBadge
                  domain="pricing"
                  status={material.source_review_status || "unknown"}
                  label={sourceStatusLabel(material.source_review_status)}
                  size="sm"
                  className="text-[12px] font-medium"
                />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground mb-0.5">Verificat la</p>
                <p className="text-[12px] text-muted-foreground">{fmtDate(material.source_checked_at)}</p>
              </div>
              <div className="col-span-2">
                <p className="text-[10px] text-muted-foreground mb-0.5">Sursă</p>
                <p className="text-[12px] text-muted-foreground">{material.source_name || "Lipsă"}</p>
                {material.source_url && (
                  <a
                    href={material.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-blue-600 dark:text-blue-400 hover:underline mt-0.5 inline-block"
                  >
                    {material.source_url}
                  </a>
                )}
              </div>
              {material.source_notes && (
                <div className="col-span-2">
                  <p className="text-[10px] text-muted-foreground mb-0.5">Note sursă</p>
                  <p className="text-[11px] text-muted-foreground italic">{material.source_notes}</p>
                </div>
              )}
            </div>
          </div>

          {/* Markup section */}
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
            <h3 className="text-[11px] text-muted-foreground uppercase tracking-wide mb-3">Adaos Comercial Aplicat</h3>
            {markup ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] text-muted-foreground">Regulă</span>
                  <span className="text-[13px] font-bold text-foreground">{markup.displayValue}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[12px] text-muted-foreground">Scop</span>
                  <span className="text-[12px] text-foreground">{scopeLabel(markup.scope)} — {markup.policy.scope_value || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[12px] text-muted-foreground">Tip</span>
                  <span className="text-[12px] text-foreground">{markup.policy.markup_type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[12px] text-muted-foreground">Prioritate</span>
                  <span className="text-[12px] text-foreground">{markup.policy.priority}</span>
                </div>
              </div>
            ) : (
              <p className="text-[12px] text-muted-foreground">Adaos lipsă — nicio regulă aplicabilă.</p>
            )}
          </div>

          {/* Estimated net price */}
          <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-blue-500 rounded-lg p-4">
            <h3 className="text-[11px] text-muted-foreground uppercase tracking-wide mb-2">Preț Net Estimat</h3>
            {estimated.value !== null ? (
              <p className="text-[20px] font-bold text-blue-600 dark:text-blue-300">
                {fmtCost(estimated.value, material.currency)}
                <span className="text-[11px] text-muted-foreground ml-2 font-normal">/ {material.unit || "buc"}</span>
              </p>
            ) : (
              <p className="text-[13px] text-amber-600 dark:text-amber-400">Indisponibil — {estimated.reason}</p>
            )}
            <p className="text-[10px] text-muted-foreground mt-1">Calcul orientativ: cost net + adaos. Fără TVA.</p>
          </div>

          {/* Dry-run result from backend (if available) */}
          {dryRunResult && (
            <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
              <h3 className="text-[11px] text-muted-foreground uppercase tracking-wide mb-3">Verificare Backend (Dry-Run)</h3>
              <div className="space-y-2 text-[12px]">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Cost bază</span>
                  <span className="text-foreground">{fmtCost(dryRunResult.base_cost_total, dryRunResult.currency)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Adaos calculat</span>
                  <span className="text-foreground">{fmtCost(dryRunResult.markup_amount, dryRunResult.currency)}</span>
                </div>
                <div className="flex justify-between border-t border-wo-border-strong pt-2">
                  <span className="text-muted-foreground font-medium">Preț comercial unitar</span>
                  <span className="text-blue-600 dark:text-blue-300 font-bold">{fmtCost(dryRunResult.commercial_unit_price, dryRunResult.currency)}</span>
                </div>
                {dryRunResult.warnings.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {dryRunResult.warnings.map((w, i) => (
                      <p key={i} className="text-[11px] text-amber-600 dark:text-amber-400 flex items-start gap-1">
                        <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                        {w.message}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Price history */}
          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
            <h3 className="text-[11px] text-muted-foreground uppercase tracking-wide mb-3">Istoric Preț</h3>
            {loadingHistory ? (
              <div className="flex items-center gap-2 py-3">
                <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" />
                <span className="text-[11px] text-muted-foreground">Se încarcă...</span>
              </div>
            ) : priceHistory.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {priceHistory.slice(0, 10).map((entry, i) => (
                  <div key={entry.id || i} className="flex items-center justify-between text-[11px] border-b border-wo-border-strong pb-1.5 last:border-0">
                    <div>
                      <span className="text-muted-foreground">{fmtCost(entry.new_unit_cost ?? entry.unit_cost, entry.new_currency ?? entry.currency)}</span>
                      {entry.old_unit_cost != null && (
                        <span className="text-muted-foreground ml-2">← {fmtCost(entry.old_unit_cost, entry.old_currency)}</span>
                      )}
                    </div>
                    <span className="text-muted-foreground">{fmtDate(entry.changed_at ?? entry.created_at)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-muted-foreground">Nu există istoric disponibil.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENT: MaterialEditDrawer
// ══════════════════════════════════════════════════════════════════════════════

function materialToEditForm(mat: InventoryMaterialDTO): MaterialEditFormState {
  return {
    unit_cost: mat.unit_cost != null ? String(mat.unit_cost) : "",
    currency: mat.currency ?? "EUR",
    vat_percent: mat.vat_percent != null ? String(mat.vat_percent) : "",
    valid_from: mat.valid_from ? mat.valid_from.slice(0, 10) : "",
    status: mat.status ?? "active",
    source_review_status: mat.source_review_status ?? "",
    source_notes: mat.source_notes ?? "",
    change_reason: "",
  };
}

function MaterialEditDrawer({
  item,
  material,
  onClose,
  onSaved,
}: {
  item: PricingRegistryItem;
  material: InventoryMaterialDTO;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<MaterialEditFormState>(() => materialToEditForm(material));
  const [history, setHistory] = useState<PriceHistoryEntryDTO[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm(materialToEditForm(material));
    setLoadingHistory(true);
    inventoryMaterialsAdminApi
      .priceHistory(material.code, 10)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoadingHistory(false));
  }, [material]);

  const handleSave = async () => {
    const validationError = validateMaterialEditPayload(form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await inventoryMaterialsAdminApi.patch(
        material.code,
        buildMaterialPatchPayload(form) as InventoryMaterialPatchPayload
      );
      onSaved();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Eroare la salvare");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-xl bg-wo-surface-inset border-l border-border overflow-y-auto">
        <div className="sticky top-0 z-10 bg-wo-surface-inset border-b border-border px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-[16px] font-bold text-foreground">Editare preț material</h2>
            <p className="text-[12px] font-mono text-blue-600 dark:text-blue-400 mt-0.5">{material.code}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-muted transition-colors">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-3 text-[11px] text-amber-200 leading-relaxed">
            Registry intern de referință — Cost achiziție intern. Nu este tarif client.
            Oferta oficială = Snapshot V2. Inventory rămâne zona pentru recepții, furnizori, consum și stoc.
          </div>

          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4 space-y-3">
            <p className="text-[12px] text-foreground font-semibold">{material.name}</p>
            <p className="text-[10px] text-muted-foreground">
              Template-uri: {item.used_by_templates.join(", ") || "—"}
            </p>
            <p className="text-[10px] text-muted-foreground">
              Încredere curentă: {confidenceBadgeLabel(item.confidence)}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Cost achiziție — intern *</span>
              <input
                value={form.unit_cost}
                onChange={(e) => setForm((f) => ({ ...f, unit_cost: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              />
            </label>
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Monedă rând (override avansat)</span>
              <input
                value={form.currency}
                onChange={(e) => setForm((f) => ({ ...f, currency: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              />
            </label>
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">TVA %</span>
              <input
                value={form.vat_percent}
                onChange={(e) => setForm((f) => ({ ...f, vat_percent: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              />
            </label>
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Valid din</span>
              <input
                type="date"
                value={form.valid_from}
                onChange={(e) => setForm((f) => ({ ...f, valid_from: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              />
            </label>
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Status</span>
              <select
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[11px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              >
                {MATERIAL_STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{statusBadgeLabel(s)}</option>
                ))}
              </select>
            </label>
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Verificare sursă</span>
              <select
                value={form.source_review_status}
                onChange={(e) => setForm((f) => ({ ...f, source_review_status: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[11px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              >
                <option value="">— Neschimbat —</option>
                {SOURCE_REVIEW_STATUS_OPTIONS.filter(Boolean).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </label>
          </div>

          <label className="block space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase">Note sursă</span>
            <textarea
              value={form.source_notes}
              onChange={(e) => setForm((f) => ({ ...f, source_notes: e.target.value }))}
              rows={2}
              className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
            />
          </label>

          <label className="block space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase">Motiv modificare *</span>
            <textarea
              value={form.change_reason}
              onChange={(e) => setForm((f) => ({ ...f, change_reason: e.target.value }))}
              rows={2}
              placeholder="Ex: actualizare cost intern Q2"
              className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
            />
          </label>

          {error && (
            <p className="text-[11px] text-red-600 dark:text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              {error}
            </p>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-[12px] font-medium rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
              Salvează
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-[12px] rounded bg-slate-700 text-muted-foreground hover:bg-slate-600"
            >
              Anulează
            </button>
          </div>

          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
            <h3 className="text-[11px] text-muted-foreground uppercase tracking-wide mb-3">Istoric preț</h3>
            {loadingHistory ? (
              <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" />
            ) : history.length > 0 ? (
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {history.map((entry) => (
                  <div key={entry.id} className="text-[11px] border-b border-wo-border-strong pb-1.5">
                    <span className="text-muted-foreground">{fmtCost(entry.new_unit_cost ?? entry.unit_cost, entry.new_currency ?? entry.currency)}</span>
                    {entry.change_reason && (
                      <span className="text-muted-foreground ml-2">— {entry.change_reason}</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-muted-foreground">Nu există istoric.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENT: WorkcenterRateEditDrawer
// ══════════════════════════════════════════════════════════════════════════════

function rateToEditForm(rate: WorkcenterRateDTO): WorkcenterEditFormState {
  return {
    rate_per_hour: rate.rate_per_hour != null ? String(rate.rate_per_hour) : "",
    rate_per_linear_meter:
      rate.rate_per_linear_meter != null ? String(rate.rate_per_linear_meter) : "",
    rate_basis: rate.rate_basis ?? "per_hour",
    currency: rate.currency ?? "EUR",
    status: rate.status ?? "active",
    notes: "",
    change_reason: "",
  };
}

function WorkcenterRateEditDrawer({
  item,
  rate,
  onClose,
  onSaved,
}: {
  item: PricingRegistryItem;
  rate: WorkcenterRateDTO;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<WorkcenterEditFormState>(() => rateToEditForm(rate));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm(rateToEditForm(rate));
  }, [rate]);

  const handleSave = async () => {
    const validationError = validateWorkcenterEditPayload(form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await workcenterRatesAdminApi.patch(
        rate.code,
        buildWorkcenterPatchPayload(form, rate.notes)
      );
      onSaved();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Eroare la salvare");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-xl bg-wo-surface-inset border-l border-border overflow-y-auto">
        <div className="sticky top-0 z-10 bg-wo-surface-inset border-b border-border px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-[16px] font-bold text-foreground">Editare rată operație</h2>
            <p className="text-[12px] font-mono text-cyan-600 dark:text-cyan-300 mt-0.5">{rate.code}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-muted transition-colors">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-3 text-[11px] text-amber-200 leading-relaxed">
            Registry intern — Efort intern / capacitate. Nu este tarif client. Oferta oficială = Snapshot V2.
          </div>

          <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-4">
            <p className="text-[12px] text-foreground font-semibold">{rate.label}</p>
            <p className="text-[10px] text-muted-foreground mt-1">
              Template-uri: {item.used_by_templates.join(", ") || "—"}
            </p>
            <p className="text-[10px] text-muted-foreground">Bază rată: {rate.rate_basis}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Bază rată</span>
              <select
                value={form.rate_basis}
                onChange={(e) => setForm((f) => ({ ...f, rate_basis: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[11px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              >
                {RATE_BASIS_OPTIONS.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </label>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Monedă</span>
              <p className="px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-muted-foreground">
                {form.currency} (read-only)
              </p>
            </div>
            {form.rate_basis === "per_hour" ? (
              <label className="space-y-1 col-span-2">
                <span className="text-[10px] text-muted-foreground uppercase">Efort intern / oră (capacitate)</span>
                <input
                  value={form.rate_per_hour}
                  onChange={(e) => setForm((f) => ({ ...f, rate_per_hour: e.target.value }))}
                  className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
                />
              </label>
            ) : (
              <label className="space-y-1 col-span-2">
                <span className="text-[10px] text-muted-foreground uppercase">Rată / metru liniar</span>
                <input
                  value={form.rate_per_linear_meter}
                  onChange={(e) => setForm((f) => ({ ...f, rate_per_linear_meter: e.target.value }))}
                  className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
                />
              </label>
            )}
            <label className="space-y-1">
              <span className="text-[10px] text-muted-foreground uppercase">Status</span>
              <select
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                className="w-full px-2.5 py-1.5 text-[11px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
              >
                {WORKCENTER_STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>{statusBadgeLabel(s)}</option>
                ))}
              </select>
            </label>
          </div>

          {rate.notes && (
            <p className="text-[10px] text-muted-foreground italic">Note existente: {rate.notes}</p>
          )}

          <label className="block space-y-1">
            <span className="text-[10px] text-muted-foreground uppercase">Motiv modificare *</span>
            <textarea
              value={form.change_reason}
              onChange={(e) => setForm((f) => ({ ...f, change_reason: e.target.value }))}
              rows={2}
              className="w-full px-2.5 py-1.5 text-[12px] bg-wo-surface-raised border border-wo-border-strong rounded text-foreground"
            />
          </label>

          {error && (
            <p className="text-[11px] text-red-600 dark:text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              {error}
            </p>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-[12px] font-medium rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
              Salvează
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-[12px] rounded bg-slate-700 text-muted-foreground hover:bg-slate-600"
            >
              Anulează
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ══════════════════════════════════════════════════════════════════════════════

const DEFAULT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2";

export default function Pricing() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedTemplateFromQuery = useMemo(
    () => resolveTemplateCode(searchParams.get("template") ?? DEFAULT_TEMPLATE),
    [searchParams]
  );
  const [registry, setRegistry] = useState<PricingRegistryResponse | null>(null);
  const [policies, setPolicies] = useState<CommercialMarkupPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"db" | "loading" | "error">("loading");

  const [mainView, setMainView] = useState<PricingMainView>("coverage");
  const [selectedTemplate, setSelectedTemplate] = useState(selectedTemplateFromQuery);
  const [recentTemplates, setRecentTemplates] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem(RECENT_TEMPLATES_STORAGE_KEY);
      return raw ? (JSON.parse(raw) as string[]) : [];
    } catch {
      return [];
    }
  });
  const [favoriteTemplates, setFavoriteTemplates] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem(FAVORITE_TEMPLATES_STORAGE_KEY);
      return raw ? (JSON.parse(raw) as string[]) : [];
    } catch {
      return [];
    }
  });
  const [selectedItem, setSelectedItem] = useState<PricingRegistryItem | null>(null);
  const [stackSearch, setStackSearch] = useState(() =>
    String(searchParams.get("code") || searchParams.get("q") || "").trim(),
  );
  const [detailHistory, setDetailHistory] = useState<PriceHistoryEntryDTO[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const [markupDrawerOpen, setMarkupDrawerOpen] = useState(false);
  const [editMaterialCtx, setEditMaterialCtx] = useState<{
    item: PricingRegistryItem;
    mat: InventoryMaterialDTO;
  } | null>(null);
  const [editRateCtx, setEditRateCtx] = useState<{
    item: PricingRegistryItem;
    rate: WorkcenterRateDTO;
  } | null>(null);
  const [loadingRate, setLoadingRate] = useState(false);
  const [baseCurrency, setBaseCurrency] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [reg, pols, ceConfig] = await Promise.all([
        pricingRegistryApi.getRegistry(),
        commercialMarkupPoliciesAdminApi.list(),
        costEngineApi.getConfig().catch(() => null),
      ]);
      setRegistry(reg);
      setPolicies(pols);
      setBaseCurrency(ceConfig?.moneda_implicita ?? null);
      setSource("db");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Eroare necunoscută";
      setError(msg);
      setSource("error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!registry) return;
    const codes = registry.template_usage.map((t) => t.template_code);
    if (codes.length > 0 && !codes.includes(selectedTemplate)) {
      const nextTemplate = codes.find((c) => c === DEFAULT_TEMPLATE) ?? codes[0];
      setSelectedTemplate(nextTemplate);
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set("template", nextTemplate);
        return next;
      });
    }
  }, [registry, selectedTemplate, setSearchParams]);

  useEffect(() => {
    if (selectedTemplateFromQuery !== selectedTemplate) {
      setSelectedTemplate(selectedTemplateFromQuery);
    }
  }, [selectedTemplate, selectedTemplateFromQuery]);

  const loadItemHistory = useCallback(async (item: PricingRegistryItem) => {
    if (item.pricing_kind !== "material") {
      setDetailHistory([]);
      return;
    }
    setLoadingHistory(true);
    try {
      const history = await inventoryMaterialsAdminApi.priceHistory(item.pricing_code, 20);
      setDetailHistory(history);
    } catch {
      setDetailHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const handleSelectItem = useCallback(
    (item: PricingRegistryItem) => {
      setSelectedItem(item);
      void loadItemHistory(item);
    },
    [loadItemHistory]
  );

  const handleSelectTemplate = useCallback((code: string) => {
    setSelectedTemplate(code);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("template", code);
      return next;
    });
    setSelectedItem(null);
    setDetailHistory([]);
    setRecentTemplates((prev) => {
      const next = pushRecentTemplate(prev, code);
      try {
        localStorage.setItem(RECENT_TEMPLATES_STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, [setSearchParams]);

  const openMaterialEdit = useCallback(async (item: PricingRegistryItem) => {
    const mat = registryItemToMatDto(item);
    try {
      const fresh = await inventoryMaterialsAdminApi.get(mat.code);
      setEditMaterialCtx({ item, mat: fresh });
    } catch {
      setEditMaterialCtx({ item, mat });
    }
  }, []);

  const openRateEdit = useCallback(async (item: PricingRegistryItem) => {
    setLoadingRate(true);
    try {
      const rate = await workcenterRatesAdminApi.get(item.pricing_code);
      setEditRateCtx({ item, rate });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Nu s-a putut încărca rata");
    } finally {
      setLoadingRate(false);
    }
  }, []);

  const handleGoToProblem = useCallback(
    (item: PricingRegistryItem) => {
      setMainView("coverage");
      handleSelectItem(item);
    },
    [handleSelectItem]
  );

  const handleToggleFavoriteTemplate = useCallback((code: string) => {
    setFavoriteTemplates((prev) => {
      const next = toggleFavoriteTemplate(prev, code);
      try {
        localStorage.setItem(FAVORITE_TEMPLATES_STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  if (loading && !registry) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
          <p className="text-[12px] text-muted-foreground">Încărcare date prețuri...</p>
        </div>
      </div>
    );
  }

  if (!registry) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-[12px] text-muted-foreground">Nu s-au putut încărca datele registry.</p>
      </div>
    );
  }

  return (
    <>
      <PricingRegistrySpaciousView
        registry={registry}
        policies={policies}
        loading={loading}
        error={error}
        source={source}
        selectedTemplate={selectedTemplate}
        recentTemplates={recentTemplates}
        favoriteTemplates={favoriteTemplates}
        mainView={mainView}
        selectedItem={selectedItem}
        stackSearch={stackSearch}
        priceHistory={detailHistory}
        loadingHistory={loadingHistory}
        loadingRate={loadingRate}
        onRefresh={loadData}
        onSelectTemplate={handleSelectTemplate}
        onToggleFavoriteTemplate={handleToggleFavoriteTemplate}
        onMainViewChange={setMainView}
        onSelectItem={handleSelectItem}
        onStackSearchChange={setStackSearch}
        onEditMaterial={openMaterialEdit}
        onEditRate={openRateEdit}
        onOpenMarkupDrawer={() => setMarkupDrawerOpen(true)}
        onGoToProblem={handleGoToProblem}
        baseCurrency={baseCurrency}
      />

      <MarkupRulesDrawer
        open={markupDrawerOpen}
        onClose={() => setMarkupDrawerOpen(false)}
        policies={policies}
      />

      {editMaterialCtx && (
        <MaterialEditDrawer
          item={editMaterialCtx.item}
          material={editMaterialCtx.mat}
          onClose={() => setEditMaterialCtx(null)}
          onSaved={loadData}
        />
      )}

      {editRateCtx && (
        <WorkcenterRateEditDrawer
          item={editRateCtx.item}
          rate={editRateCtx.rate}
          onClose={() => setEditRateCtx(null)}
          onSaved={loadData}
        />
      )}
    </>
  );
}