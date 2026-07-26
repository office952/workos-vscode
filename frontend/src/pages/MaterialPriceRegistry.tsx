/**
 * Material Price Registry — Admin UI page.
 *
 * Route: /inventory/material-price-registry
 *
 * Rules enforced by this UI:
 *   - unit_cost = acquisition / production cost. NOT commercial selling price.
 *   - Commercial markup is separate — never added to unit_cost here.
 *   - VAT is separate.
 *   - valid_from is separate.
 *   - Source metadata (source_name, source_url, etc.) is verification reference only.
 *     It does NOT constitute price truth and does NOT create price history by itself.
 *   - No prices are invented or hardcoded.
 *   - No prices are activated without explicit owner confirmation.
 *   - Price history is read-only.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { MaterialNamingHints } from "@/lib/materials/MaterialNamingHints";
import {
  Search,
  RefreshCw,
  Pencil,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Archive,
  X,
  Save,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Info,
  History,
  Loader2,
  PackageSearch,
  ShieldCheck,
} from "lucide-react";
import {
  inventoryMaterialsAdminApi,
  type InventoryMaterialDTO,
  type CategoryCleanupPreviewEntryDTO,
  type InventoryMaterialsPolicyDTO,
  type InventoryMaterialPatchPayload,
  type SourceReviewAuditEntryDTO,
  type PriceHistoryEntryDTO,
} from "@/api/inventoryMaterialsAdmin";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

// ── Status config ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  { label: string; textCls: string; dotCls: string; icon: React.FC<{ className?: string }> }
> = {
  active: { label: "Activ", textCls: "text-emerald-400", dotCls: "bg-emerald-500", icon: CheckCircle2 },
  missing_price: { label: "Preț lipsă", textCls: "text-amber-400", dotCls: "bg-amber-500", icon: AlertTriangle },
  needs_owner_input: { label: "Necesită input", textCls: "text-orange-400", dotCls: "bg-orange-500", icon: Clock },
  archived: { label: "Arhivat", textCls: "text-wo-text-muted", dotCls: "bg-slate-600", icon: Archive },
};

const STATUS_OPTIONS = [
  { value: "all", label: "Toate statusurile" },
  { value: "active", label: "Active" },
  { value: "missing_price", label: "Preț lipsă" },
  { value: "needs_owner_input", label: "Necesită input" },
  { value: "archived", label: "Arhivate" },
];

const QUICK_VIEW_OPTIONS = [
  { value: "all", label: "Toate materialele" },
  { value: "active", label: "Active" },
  { value: "active_incomplete", label: "Active incomplete" },
  { value: "needs_input", label: "Needs input" },
  { value: "needs_category_normalization", label: "Needs category normalization" },
  { value: "needs_source_review", label: "Needs source review" },
  { value: "source_stale", label: "Source stale" },
  { value: "ready", label: "Ready for pricing" },
  { value: "productsystem_ready", label: "ProductSystem ready" },
  { value: "archived", label: "Arhivate" },
];

const SOURCE_REVIEW_OPTIONS = [
  { value: "missing", label: "missing" },
  { value: "needs_review", label: "needs_review" },
  { value: "reviewed", label: "reviewed" },
  { value: "stale", label: "stale" },
  { value: "accepted_override", label: "accepted_override" },
];

const FALLBACK_POLICY: InventoryMaterialsPolicyDTO = {
  canonical_categories: ["Placi", "Profile metalice", "Parti electrice", "Folii", "Consumabile"],
  recommended_subcategories: {
    "Profile metalice": ["Volum aluminiu (litere)", "Otel / teava rectangulara", "Otel / teava rotunda", "Otel / cornier", "Otel / platbanda", "Aluminiu / profil litera volumetrica", "Aluminiu / profil caseta luminoasa", "Aluminiu / profil rama", "Aluminiu / profil sistem textil/banner"],
    Folii: ["Oracal 651", "Oracal 641", "Oracal 8500", "Printat / Laminat", "Printabil"],
    Placi: ["ACM / Alucobond / Dibond", "Plexiglas", "Forex", "HIPS / alte placi"],
    "Parti electrice": ["Module LED", "Surse LED 12V", "Cabluri / conectori"],
    Consumabile: ["adezivi", "suruburi / prinderi", "distantieri / kit montaj", "consumabile generale"],
  },
  required_pricing_fields: ["unit", "unit_cost", "currency", "vat_percent", "valid_from"],
  price_governed_fields: ["unit_cost", "currency", "vat_percent", "valid_from"],
  source_review_policy: { statuses: SOURCE_REVIEW_OPTIONS.map((s) => s.value), accepted_override_requires_notes: true },
  product_system_gate_rules: { requires_ready_for_pricing: true, requires_active_status: true, rejects_archived: true, requires_category_normalized: true, requires_unit: true, requires_source_review_ok: true, informational_only: true },
  stale_source_days: 90,
  warnings: ["Material Registry unit_cost remains acquisition/production cost.", "Commercial markup policy is separate from Material Registry.", "ProductSystem ready is informational and does not activate Product 001."],
  category_policy: {
    accepted: ["Placi", "Profile metalice", "Parti electrice", "Folii", "Consumabile"],
    recommended_subcategories: {
      "Profile metalice": ["Volum aluminiu (litere)", "Otel / teava rectangulara", "Otel / teava rotunda", "Otel / cornier", "Otel / platbanda", "Aluminiu / profil litera volumetrica", "Aluminiu / profil caseta luminoasa", "Aluminiu / profil rama", "Aluminiu / profil sistem textil/banner"],
      Folii: ["Oracal 651", "Oracal 641", "Oracal 8500", "Printat / Laminat", "Printabil"],
      Placi: ["ACM / Alucobond / Dibond", "Plexiglas", "Forex", "HIPS / alte placi"],
      "Parti electrice": ["Module LED", "Surse LED 12V", "Cabluri / conectori"],
      Consumabile: ["adezivi", "suruburi / prinderi", "distantieri / kit montaj", "servicii interne"],
    },
  },
  source_review: { stale_after_days: 90, override_token: "source_review:accepted" },
  productsystem_gate: { informational_only: true, activates_product_001: false, connects_cost_engine: false },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtCost(n: number | null | undefined, currency?: string | null): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "\u2014";
  const formatted = n.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  return currency ? `${formatted} ${currency}` : formatted;
}

function fmtVat(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "\u2014";
  return `${n}%`;
}

function fmtDate(s: string | null | undefined): string {
  if (!s) return "\u2014";
  try { return new Date(s).toLocaleDateString("ro-RO", { year: "numeric", month: "2-digit", day: "2-digit" }); } catch { return s; }
}

function fmtDateTime(s: string | null | undefined): string {
  if (!s) return "\u2014";
  try { return new Date(s).toLocaleString("ro-RO"); } catch { return s; }
}

function getMissingPricingFields(m: Pick<InventoryMaterialDTO, "unit" | "unit_cost" | "currency" | "vat_percent" | "valid_from">): string[] {
  const missing: string[] = [];
  if (!m.unit || !m.unit.trim()) missing.push("unit");
  if (m.unit_cost === null || m.unit_cost === undefined || m.unit_cost <= 0) missing.push("unit_cost");
  if (!m.currency || !m.currency.trim()) missing.push("currency");
  if (m.vat_percent === null || m.vat_percent === undefined) missing.push("vat_percent");
  if (!m.valid_from) missing.push("valid_from");
  return missing;
}

function isPriceComplete(m: InventoryMaterialDTO): boolean { return getMissingPricingFields(m).length === 0; }

function getReadinessState(m: InventoryMaterialDTO): "ready" | "active_incomplete" | "not_active" | "archived" {
  if (m.status === "archived") return "archived";
  if (m.status !== "active") return "not_active";
  return isPriceComplete(m) ? "ready" : "active_incomplete";
}

function isReadyForPricing(m: InventoryMaterialDTO): boolean { return getReadinessState(m) === "ready"; }
function isActiveIncomplete(m: InventoryMaterialDTO): boolean { return getReadinessState(m) === "active_incomplete"; }

function normalizeCategory(value: string | null | undefined): string {
  return (value ?? "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
}

function getCanonicalCategory(value: string | null | undefined, policy: InventoryMaterialsPolicyDTO): string | null {
  const raw = (value ?? "").trim();
  if (raw && policy.canonical_categories.includes(raw)) return raw;
  const n = normalizeCategory(value);
  if (!n) return null;
  if (n.includes("plac") || n.includes("acm") || n.includes("dibond") || n.includes("plexi") || n.includes("forex")) return "Placi";
  if (n.includes("profil") || n.includes("otel") || n.includes("aluminiu") || n.includes("teava") || n.includes("cornier")) return "Profile metalice";
  if (n.includes("electric") || n.includes("led") || n.includes("aliment") || n.includes("cablu") || n.includes("conector")) return "Parti electrice";
  if (n.includes("folie") || n.includes("oracal") || n.includes("laminare") || n.includes("print")) return "Folii";
  if (n.includes("consum") || n.includes("adeziv") || n.includes("surub") || n.includes("prinder") || n.includes("kit")) return "Consumabile";
  if (n.startsWith("dev_smoke_")) return "Consumabile";
  return null;
}

function inferRecommendedSubcategory(m: InventoryMaterialDTO, canonicalCategory: string | null): string | null {
  const hay = `${m.code} ${m.name} ${m.category ?? ""}`.toLowerCase();
  if (!canonicalCategory) return null;
  if (canonicalCategory === "Folii") {
    if (hay.includes("8500")) return "Oracal 8500";
    if (hay.includes("651")) return "Oracal 651";
    if (hay.includes("641")) return "Oracal 641";
    if (hay.includes("print") && hay.includes("lamin")) return "Printat / Laminat";
    if (hay.includes("lamin")) return "Laminare";
    if (hay.includes("print")) return "Printabil";
  }
  if (canonicalCategory === "Placi") {
    if (hay.includes("acm") || hay.includes("dibond") || hay.includes("alucobond")) return "ACM / Alucobond / Dibond";
    if (hay.includes("plexi")) return "Plexiglas";
    if (hay.includes("forex")) return "Forex";
    if (hay.includes("hips")) return "HIPS / alte placi";
  }
  if (canonicalCategory === "Profile metalice") {
    if (
      hay.includes("profil-lateral-litere") ||
      hay.includes("mat-profil-lateral-litere") ||
      (hay.includes("volum aluminiu") && !hay.includes("caseta"))
    ) {
      return "Volum aluminiu (litere)";
    }
    if (hay.includes("rectang")) return "Otel / teava rectangulara";
    if (hay.includes("rotund")) return "Otel / teava rotunda";
    if (hay.includes("cornier")) return "Otel / cornier";
    if (hay.includes("platband")) return "Otel / platbanda";
    if (hay.includes("caseta")) return "Aluminiu / profil caseta luminoasa";
    if (hay.includes("rama")) return "Aluminiu / profil rama";
    if (hay.includes("textil") || hay.includes("banner")) return "Aluminiu / profil sistem textil/banner";
    if (hay.includes("litera")) return "Aluminiu / profil litera volumetrica";
  }
  if (canonicalCategory === "Parti electrice") {
    if (hay.includes("psu") || hay.includes("sursa") || hay.includes("aliment")) {
      return "Surse LED 12V";
    }
    if (hay.includes("cablu") || hay.includes("conector")) return "Cabluri / conectori";
    if (hay.includes("led") || hay.includes("banda led") || hay.includes("modul led")) {
      return "Module LED";
    }
  }
  if (canonicalCategory === "Consumabile") {
    if (hay.includes("adeziv")) return "adezivi";
    if (hay.includes("surub") || hay.includes("prinder")) return "suruburi / prinderi";
    if (hay.includes("distanti") || hay.includes("kit")) return "distantieri / kit montaj";
  }
  return null;
}

function isCategoryPolicyValid(m: InventoryMaterialDTO, policy: InventoryMaterialsPolicyDTO): boolean { return !!getCanonicalCategory(m.category, policy); }

function getSourceMissingFields(m: Pick<InventoryMaterialDTO, "source_name" | "source_url" | "source_checked_at">): string[] {
  const missing: string[] = [];
  if (!m.source_name || !m.source_name.trim()) missing.push("source_name");
  if (!m.source_url || !m.source_url.trim()) missing.push("source_url");
  if (!m.source_checked_at) missing.push("source_checked_at");
  return missing;
}

function isSourceStale(checkedAt: string | null | undefined, staleAfterDays: number): boolean {
  if (!checkedAt) return true;
  const parsed = new Date(checkedAt);
  if (Number.isNaN(parsed.getTime())) return true;
  return Date.now() - parsed.getTime() > staleAfterDays * 86400000;
}

type SourceReviewState = "source_missing" | "source_needs_check" | "source_stale" | "source_recently_checked" | "source_reviewed" | "source_review_override";

function getSourceReviewState(m: InventoryMaterialDTO, policy: InventoryMaterialsPolicyDTO): SourceReviewState {
  const explicit = (m.source_review_status ?? "").trim().toLowerCase();
  if (explicit === "accepted_override") return "source_review_override";
  if (explicit === "reviewed") return "source_reviewed";
  if (explicit === "stale") return "source_stale";
  if (explicit === "needs_review") return "source_needs_check";
  if (explicit === "missing") return "source_missing";
  const overrideToken = policy.source_review?.override_token?.toLowerCase?.() ?? "";
  const notes = (m.source_notes ?? "").toLowerCase();
  if (overrideToken && notes.includes(overrideToken)) return "source_review_override";
  if (!m.source_url || !m.source_url.trim()) return "source_missing";
  if (!m.source_checked_at) return "source_needs_check";
  if (isSourceStale(m.source_checked_at, policy.stale_source_days ?? policy.source_review.stale_after_days)) return "source_stale";
  if (m.source_name && m.source_name.trim()) return "source_reviewed";
  return "source_recently_checked";
}

function isSourceReviewAccepted(m: InventoryMaterialDTO, policy: InventoryMaterialsPolicyDTO): boolean {
  const state = getSourceReviewState(m, policy);
  return state === "source_reviewed" || state === "source_review_override";
}

function needsSourceReview(m: InventoryMaterialDTO, policy: InventoryMaterialsPolicyDTO): boolean { return !isSourceReviewAccepted(m, policy); }
function isMarkedSourceStale(m: InventoryMaterialDTO, policy: InventoryMaterialsPolicyDTO): boolean { return getSourceReviewState(m, policy) === "source_stale"; }

function getProductSystemReadinessReasons(m: InventoryMaterialDTO, policy: InventoryMaterialsPolicyDTO): string[] {
  const reasons: string[] = [];
  if (m.status !== "active") reasons.push("material not active");
  if (m.status === "archived") reasons.push("material archived");
  if (isActiveIncomplete(m)) reasons.push("active incomplete pricing");
  const missingPrice = getMissingPricingFields(m);
  if (missingPrice.length > 0) reasons.push(`missing price fields: ${missingPrice.join(", ")}`);
  if (!m.unit || !m.unit.trim()) reasons.push("missing unit");
  if (!isCategoryPolicyValid(m, policy)) reasons.push("invalid category policy");
  if (!m.subcategory || !m.subcategory.trim()) reasons.push("missing subcategory");
  const canonicalCategory = getCanonicalCategory(m.category, policy);
  const recommendedSubcategory = inferRecommendedSubcategory(m, canonicalCategory);
  if (canonicalCategory && recommendedSubcategory && m.subcategory && m.subcategory !== recommendedSubcategory) reasons.push(`subcategory normalization recommended: ${recommendedSubcategory}`);
  if (!isSourceReviewAccepted(m, policy)) reasons.push("source review missing or stale");
  return reasons;
}

function isProductSystemReady(m: InventoryMaterialDTO, policy: InventoryMaterialsPolicyDTO): boolean { return getProductSystemReadinessReasons(m, policy).length === 0; }

// ── Badge components ──────────────────────────────────────────────────────────

function SourceReviewBadge({ material, policy }: { material: InventoryMaterialDTO; policy: InventoryMaterialsPolicyDTO }) {
  const state = getSourceReviewState(material, policy);
  const map: Record<SourceReviewState, { label: string; cls: string }> = {
    source_missing: { label: "Missing", cls: "border-red-800/40 bg-red-900/20 text-red-300" },
    source_needs_check: { label: "Needs check", cls: "border-amber-800/40 bg-amber-900/20 text-amber-300" },
    source_stale: { label: "Stale", cls: "border-orange-800/40 bg-orange-900/20 text-orange-300" },
    source_recently_checked: { label: "Checked", cls: "border-cyan-800/40 bg-cyan-900/20 text-cyan-300" },
    source_reviewed: { label: "Reviewed", cls: "border-emerald-800/40 bg-emerald-900/20 text-emerald-300" },
    source_review_override: { label: "Override", cls: "border-blue-800/40 bg-blue-900/20 text-blue-300" },
  };
  const cfg = map[state];
  return <Badge variant="outline" className={`px-1.5 py-0 text-[10px] font-medium ${cfg.cls}`}>{cfg.label}</Badge>;
}

function ProductSystemBadge({ ready }: { ready: boolean }) {
  return ready ? (
    <Badge variant="outline" className="px-1.5 py-0 text-[10px] font-medium border-emerald-800/40 bg-emerald-900/20 text-emerald-300">
      <ShieldCheck className="w-2.5 h-2.5 mr-0.5" />Ready
    </Badge>
  ) : (
    <Badge variant="outline" className="px-1.5 py-0 text-[10px] font-medium border-slate-700/50 bg-slate-800/30 text-wo-text-muted">Blocked</Badge>
  );
}

function StatusBadge({ status }: { status?: string | null }) {
  const cfg = STATUS_CONFIG[status ?? ""] ?? { label: status ?? "\u2014", textCls: "text-wo-text-muted", dotCls: "bg-slate-500", icon: Info };
  return (
    <Badge variant="outline" className={`inline-flex items-center gap-1 border-slate-700/50 bg-slate-800/30 px-1.5 py-0 text-[10px] font-semibold ${cfg.textCls}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dotCls}`} />
      {cfg.label}
    </Badge>
  );
}

function IncompleteBadge() {
  return (
    <Badge variant="destructive" className="inline-flex items-center gap-0.5 px-1.5 py-0 text-[9px] font-semibold">
      <AlertTriangle className="w-2.5 h-2.5" />Incomplet
    </Badge>
  );
}

function ReadyBadge({ ready }: { ready: boolean }) {
  return ready ? (
    <Badge variant="outline" className="inline-flex items-center gap-0.5 border-emerald-800/40 bg-emerald-900/20 px-1.5 py-0 text-[10px] text-emerald-300">
      <CheckCircle2 className="w-2.5 h-2.5" />Ready
    </Badge>
  ) : (
    <Badge variant="outline" className="inline-flex items-center gap-0.5 border-amber-800/40 bg-amber-900/20 px-1.5 py-0 text-[10px] text-amber-300">
      <Clock className="w-2.5 h-2.5" />Not ready
    </Badge>
  );
}

// ── Form components ───────────────────────────────────────────────────────────

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <label className="block text-[11px] font-semibold uppercase tracking-wide text-wo-text-muted mb-1">{children}</label>;
}

function FieldInput({ value, onChange, placeholder, type = "text", readOnly }: { value: string; onChange?: (v: string) => void; placeholder?: string; type?: string; readOnly?: boolean }) {
  return (
    <Input type={type} value={value} readOnly={readOnly} onChange={readOnly ? undefined : (e) => onChange?.(e.target.value)} placeholder={placeholder}
      className={`w-full bg-wo-surface-inset border-wo-border-strong text-[13px] text-wo-text-primary placeholder:text-wo-text-dim focus:border-blue-500 ${readOnly ? "opacity-60 cursor-default" : ""}`} />
  );
}

function FieldTextarea({ value, onChange, placeholder, rows = 2 }: { value: string; onChange: (v: string) => void; placeholder?: string; rows?: number }) {
  return <Textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={rows} className="w-full min-h-0 bg-wo-surface-inset border-wo-border-strong text-[13px] text-wo-text-primary placeholder:text-wo-text-dim focus:border-blue-500 resize-none" />;
}

function FieldSelect({ value, onChange, options }: { value: string; onChange: (value: string) => void; options: { value: string; label: string }[] }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-full bg-wo-surface-inset border-wo-border-strong text-[13px] text-wo-text-primary"><SelectValue /></SelectTrigger>
      <SelectContent>{options.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
    </Select>
  );
}

// ── Price history panel ───────────────────────────────────────────────────────

function PriceHistoryPanel({ code, refreshToken }: { code: string; refreshToken: number }) {
  const [entries, setEntries] = useState<PriceHistoryEntryDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { setLoading(true); setError(null); inventoryMaterialsAdminApi.priceHistory(code).then(setEntries).catch((err) => setError(err instanceof Error ? err.message : "Eroare")).finally(() => setLoading(false)); }, [code, refreshToken]);
  if (loading) return <div className="flex items-center gap-2 py-4 text-wo-text-muted text-[12px]"><Loader2 className="w-4 h-4 animate-spin" />Se \u00eencarc\u0103 istoricul...</div>;
  if (error) return <div className="flex items-center gap-2 py-3 text-red-400 text-[12px]"><AlertTriangle className="w-4 h-4" />{error}</div>;
  if (entries.length === 0) return <p className="text-[12px] text-wo-text-dim py-3 italic">Nu exist\u0103 intr\u0103ri \u00een istoricul de pre\u021buri.</p>;
  return (
    <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
      {entries.map((e) => (
        <Card key={e.id} className="border-wo-border-strong bg-wo-surface-inset">
          <CardContent className="px-3 py-2 text-[12px]">
            <div className="flex items-center justify-between mb-1">
              <span className="text-wo-text-muted text-[11px]">{fmtDateTime(e.changed_at ?? e.created_at)}</span>
              {e.changed_by && <span className="text-wo-text-dim text-[10px]">by {e.changed_by}</span>}
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
              {(e.old_unit_cost != null || e.new_unit_cost != null || e.unit_cost != null) && (<><span className="text-wo-text-muted">Cost:</span><span className="text-wo-text-secondary">{e.old_unit_cost != null || e.new_unit_cost != null ? `${fmtCost(e.old_unit_cost)} \u2192 ${fmtCost(e.new_unit_cost, e.new_currency ?? e.old_currency)}` : fmtCost(e.unit_cost, e.currency)}</span></>)}
              {(e.old_vat_percent != null || e.new_vat_percent != null || e.vat_percent != null) && (<><span className="text-wo-text-muted">TVA:</span><span className="text-wo-text-secondary">{e.old_vat_percent != null || e.new_vat_percent != null ? `${fmtVat(e.old_vat_percent)} \u2192 ${fmtVat(e.new_vat_percent)}` : fmtVat(e.vat_percent)}</span></>)}
              {(e.old_valid_from != null || e.new_valid_from != null || e.valid_from != null) && (<><span className="text-wo-text-muted">Valid from:</span><span className="text-wo-text-secondary">{e.old_valid_from != null || e.new_valid_from != null ? `${fmtDate(e.old_valid_from)} \u2192 ${fmtDate(e.new_valid_from)}` : fmtDate(e.valid_from)}</span></>)}
            </div>
            <p className="mt-1 text-wo-text-muted text-[11px] italic">Motiv: {e.change_reason && e.change_reason.trim() ? e.change_reason : "No reason recorded"}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function SourceReviewAuditPanel({ code, refreshToken }: { code: string; refreshToken: number }) {
  const [entries, setEntries] = useState<SourceReviewAuditEntryDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { setLoading(true); setError(null); inventoryMaterialsAdminApi.sourceReviewAudit(code).then(setEntries).catch((err) => setError(err instanceof Error ? err.message : "Eroare")).finally(() => setLoading(false)); }, [code, refreshToken]);
  if (loading) return <div className="flex items-center gap-2 py-4 text-wo-text-muted text-[12px]"><Loader2 className="w-4 h-4 animate-spin" />Se \u00eencarc\u0103 auditul...</div>;
  if (error) return <div className="flex items-center gap-2 py-3 text-red-400 text-[12px]"><AlertTriangle className="w-4 h-4" />{error}</div>;
  if (entries.length === 0) return <p className="text-[12px] text-wo-text-dim py-3 italic">No source review audit yet.</p>;
  return (
    <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
      {entries.map((entry) => (
        <Card key={entry.id} className="border-wo-border-strong bg-wo-surface-inset">
          <CardContent className="px-3 py-2 text-[12px]">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-wo-text-muted text-[11px]">{fmtDateTime(entry.created_at)}</span>
              <span className="text-wo-text-dim text-[10px]">by {entry.actor ?? "\u2014"}</span>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
              <span className="text-wo-text-muted">Status:</span>
              <span className="text-wo-text-secondary">{entry.old_status ?? "\u2014"} \u2192 {entry.new_status ?? "\u2014"}</span>
            </div>
            <p className="mt-1 text-wo-text-muted text-[11px] italic">Motiv: {entry.reason && entry.reason.trim() ? entry.reason : "No reason recorded"}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ── Edit form state ───────────────────────────────────────────────────────────

interface EditForm { name: string; subcategory: string; unit_cost: string; currency: string; vat_percent: string; valid_from: string; status: string; supplier: string; source_name: string; source_url: string; source_checked_at: string; source_notes: string; source_review_status: string; change_reason: string; }

function materialToForm(m: InventoryMaterialDTO): EditForm {
  return { name: m.name ?? "", subcategory: m.subcategory ?? "", unit_cost: m.unit_cost !== null && m.unit_cost !== undefined ? String(m.unit_cost) : "", currency: m.currency ?? "", vat_percent: m.vat_percent !== null && m.vat_percent !== undefined ? String(m.vat_percent) : "", valid_from: m.valid_from ? m.valid_from.slice(0, 10) : "", status: m.status ?? "missing_price", supplier: m.supplier ?? "", source_name: m.source_name ?? "", source_url: m.source_url ?? "", source_checked_at: m.source_checked_at ? m.source_checked_at.slice(0, 10) : "", source_notes: m.source_notes ?? "", source_review_status: (m.source_review_status ?? "needs_review").trim() || "needs_review", change_reason: "" };
}

function parseNum(s: string): number | null { if (!s.trim()) return null; const n = Number(s.replace(",", ".")); return Number.isFinite(n) ? n : null; }

function formToPayload(f: EditForm): InventoryMaterialPatchPayload {
  return { name: f.name.trim() || undefined, subcategory: f.subcategory.trim() || null, unit_cost: parseNum(f.unit_cost), currency: f.currency.trim() || null, vat_percent: parseNum(f.vat_percent), valid_from: f.valid_from.trim() ? `${f.valid_from}T00:00:00Z` : null, status: f.status || null, supplier: f.supplier.trim() || null, source_name: f.source_name.trim() || null, source_url: f.source_url.trim() || null, source_checked_at: f.source_checked_at.trim() ? `${f.source_checked_at}T00:00:00Z` : null, source_notes: f.source_notes.trim() || null, source_review_status: f.source_review_status.trim() || null, change_reason: f.change_reason.trim() || null, snapshot_source: "admin_patch" };
}

// ── Edit drawer ───────────────────────────────────────────────────────────────

function EditDrawer({ material, policy, open, onClose, onSaved }: { material: InventoryMaterialDTO; policy: InventoryMaterialsPolicyDTO; open: boolean; onClose: () => void; onSaved: (updated: InventoryMaterialDTO) => void }) {
  const [form, setForm] = useState<EditForm>(() => materialToForm(material));
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showSourceAudit, setShowSourceAudit] = useState(false);
  const [historyRefreshToken, setHistoryRefreshToken] = useState(0);

  useEffect(() => { setForm(materialToForm(material)); setSaveError(null); setSaveSuccess(null); }, [material]);
  const update = <K extends keyof EditForm>(key: K, value: EditForm[K]) => setForm((prev) => ({ ...prev, [key]: value }));

  const currentValidFrom = material.valid_from ? material.valid_from.slice(0, 10) : null;
  const nextUnitCost = parseNum(form.unit_cost);
  const nextCurrency = form.currency.trim() || null;
  const nextVatPercent = parseNum(form.vat_percent);
  const nextValidFrom = form.valid_from || null;
  const hasPriceGovernedChange = (nextUnitCost !== (material.unit_cost ?? null) || nextCurrency !== (material.currency ?? null) || nextVatPercent !== (material.vat_percent ?? null) || nextValidFrom !== currentValidFrom);
  const missingPriceFieldsDraft = getMissingPricingFields({ unit: material.unit, unit_cost: nextUnitCost, currency: nextCurrency, vat_percent: nextVatPercent, valid_from: nextValidFrom });
  const reasonMissingForPriceChange = hasPriceGovernedChange && !form.change_reason.trim();

  const handleSave = async () => {
    const payload = formToPayload(form);
    if (reasonMissingForPriceChange) { setSaveError("Motiv modificare este obligatoriu c\u00e2nd se schimb\u0103 cost/moned\u0103/TVA/valid_from."); return; }
    const statusAfter = payload.status ?? material.status;
    const draftAfter: InventoryMaterialDTO = { ...material, unit_cost: payload.unit_cost ?? null, currency: payload.currency ?? null, vat_percent: payload.vat_percent ?? null, valid_from: payload.valid_from ?? null, status: statusAfter };
    if (statusAfter === "active" && !isPriceComplete(draftAfter)) { setSaveError("Status active necesit\u0103 unit_cost, currency, vat_percent, valid_from \u0219i unit completate."); return; }
    setSaving(true); setSaveError(null); setSaveSuccess(null);
    try { const updated = await inventoryMaterialsAdminApi.patch(material.code, payload); onSaved(updated); setSaveSuccess("Salvat cu succes."); setHistoryRefreshToken((v) => v + 1); } catch (err) { setSaveError(err instanceof Error ? err.message : "Eroare la salvare"); } finally { setSaving(false); }
  };

  const draftForChecks: InventoryMaterialDTO = { ...material, subcategory: form.subcategory.trim() || null, unit_cost: parseNum(form.unit_cost), currency: form.currency.trim() || null, vat_percent: parseNum(form.vat_percent), valid_from: form.valid_from ? `${form.valid_from}T00:00:00Z` : null, status: form.status || material.status, source_name: form.source_name.trim() || null, source_url: form.source_url.trim() || null, source_checked_at: form.source_checked_at ? `${form.source_checked_at}T00:00:00Z` : null, source_notes: form.source_notes.trim() || null, source_review_status: form.source_review_status.trim() || null };
  const incomplete = isActiveIncomplete(draftForChecks);
  const sourceStatus = getSourceReviewState(draftForChecks, policy);
  const sourceMissing = getSourceMissingFields(draftForChecks);
  const categoryCanonical = getCanonicalCategory(draftForChecks.category, policy);
  const suggestedSubcategory = inferRecommendedSubcategory(draftForChecks, categoryCanonical);
  const productReasons = getProductSystemReadinessReasons(draftForChecks, policy);
  const disableSave = saving || reasonMissingForPriceChange;

  return (
    <Sheet open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <SheetContent side="right" className="w-[520px] max-w-full bg-wo-surface-inset border-l border-wo-border-subtle text-wo-text-primary overflow-y-auto p-0">
        <SheetHeader className="px-6 py-4 border-b border-wo-border-subtle">
          <SheetTitle className="text-[15px] font-semibold text-wo-text-primary flex items-center gap-2">
            <span>{material.code}</span><StatusBadge status={material.status} />{incomplete && <IncompleteBadge />}
          </SheetTitle>
          <p className="text-[12px] text-wo-text-muted mt-0.5 truncate">{material.name}</p>
          <SheetDescription className="text-[11px] text-wo-text-muted">Edit material pricing, source metadata and governance fields.</SheetDescription>
        </SheetHeader>
        <div className="px-6 py-4 space-y-5">
          {incomplete && (<div className="flex items-start gap-2 p-3 rounded-md bg-red-900/15 border border-red-800/40 text-[12px] text-red-300"><AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /><span>Material activ cu date de pre\u021bare incomplete.</span></div>)}
          <Card className="border-wo-border-strong bg-transparent"><CardHeader className="px-3 py-3"><CardTitle className="text-[11px] font-bold uppercase tracking-wide text-wo-text-muted">Identity</CardTitle></CardHeader><CardContent className="px-3 pb-3 space-y-3">
            <div className="grid grid-cols-2 gap-3"><div><FieldLabel>Cod</FieldLabel><FieldInput value={material.code} readOnly /></div><div><FieldLabel>Unitate</FieldLabel><FieldInput value={material.unit ?? "\u2014"} readOnly /></div></div>
            <div><FieldLabel>Categorie</FieldLabel><FieldInput value={material.category ?? "\u2014"} readOnly /></div>
            <div><FieldLabel>Subcategorie</FieldLabel><FieldInput value={form.subcategory} onChange={(v) => update("subcategory", v)} placeholder={suggestedSubcategory ?? "Subcategorie"} /></div>
            <div>
              <FieldLabel>Denumire</FieldLabel>
              <FieldInput value={form.name} onChange={(v) => update("name", v)} placeholder="Denumire material" />
              <div className="mt-2">
                <MaterialNamingHints name={form.name} />
              </div>
            </div>
          </CardContent></Card>

          <Card className="border-wo-border-strong bg-transparent"><CardHeader className="px-3 py-3"><CardTitle className="text-[11px] font-bold uppercase tracking-wide text-wo-text-muted">Pre\u021bare \u2014 cost achizi\u021bie / produc\u021bie</CardTitle></CardHeader><CardContent className="px-3 pb-3 space-y-3">
            <p className="text-[11px] text-wo-text-dim">unit_cost = cost achizi\u021bie/produc\u021bie. Adaosul comercial se configureaz\u0103 separat.</p>
            <div className="grid grid-cols-2 gap-3"><div><FieldLabel>Cost unitar (f\u0103r\u0103 TVA)</FieldLabel><FieldInput value={form.unit_cost} onChange={(v) => update("unit_cost", v)} placeholder="12.50" /></div><div><FieldLabel>Moned\u0103</FieldLabel><FieldInput value={form.currency} onChange={(v) => update("currency", v)} placeholder="RON" /></div></div>
            <div className="grid grid-cols-2 gap-3"><div><FieldLabel>TVA (%)</FieldLabel><FieldInput value={form.vat_percent} onChange={(v) => update("vat_percent", v)} placeholder="19" /></div><div><FieldLabel>Valabil de la</FieldLabel><FieldInput value={form.valid_from} onChange={(v) => update("valid_from", v)} type="date" /></div></div>
            <div><FieldLabel>Status</FieldLabel><FieldSelect value={form.status} onChange={(v) => update("status", v)} options={STATUS_OPTIONS.filter((o) => o.value !== "all")} /></div>
            <div><FieldLabel>Furnizor</FieldLabel><FieldInput value={form.supplier} onChange={(v) => update("supplier", v)} placeholder="Furnizor" /></div>
          </CardContent></Card>

          <Card className="border-wo-border-strong bg-transparent"><CardHeader className="px-3 py-3"><CardTitle className="text-[11px] font-bold uppercase tracking-wide text-wo-text-muted">Surs\u0103 de verificare</CardTitle></CardHeader><CardContent className="px-3 pb-3 space-y-3">
            <p className="text-[11px] text-wo-text-dim">Sursa este referin\u021b\u0103 de verificare, nu actualizeaz\u0103 automat pre\u021bul activ.</p>
            <div><FieldLabel>Surs\u0103 (denumire)</FieldLabel><FieldInput value={form.source_name} onChange={(v) => update("source_name", v)} placeholder="Baduc, Oracal" /></div>
            <div><FieldLabel>URL surs\u0103</FieldLabel><div className="flex items-center gap-2"><FieldInput value={form.source_url} onChange={(v) => update("source_url", v)} placeholder="https://..." />{form.source_url && <a href={form.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 shrink-0"><ExternalLink className="w-4 h-4" /></a>}</div></div>
            <div><FieldLabel>Verificat la</FieldLabel><FieldInput value={form.source_checked_at} onChange={(v) => update("source_checked_at", v)} type="date" /></div>
            <div><FieldLabel>Note surs\u0103</FieldLabel><FieldTextarea value={form.source_notes} onChange={(v) => update("source_notes", v)} placeholder="Observa\u021bii..." /></div>
            <div><FieldLabel>Source review status</FieldLabel><FieldSelect value={form.source_review_status} onChange={(v) => update("source_review_status", v)} options={SOURCE_REVIEW_OPTIONS} /></div>
          </CardContent></Card>

          <Card className="border-wo-border-strong bg-transparent"><CardHeader className="px-3 py-3"><CardTitle className="text-[11px] font-bold uppercase tracking-wide text-wo-text-muted">Governance</CardTitle></CardHeader><CardContent className="px-3 pb-3 space-y-3">
            <div className="flex items-center gap-2"><span className="text-[11px] text-wo-text-muted">Ready for pricing:</span><ReadyBadge ready={isReadyForPricing(draftForChecks)} /></div>
            <div className="flex items-center gap-2"><span className="text-[11px] text-wo-text-muted">Source review:</span><SourceReviewBadge material={draftForChecks} policy={policy} /></div>
            <div className="flex items-center gap-2"><span className="text-[11px] text-wo-text-muted">ProductSystem:</span><ProductSystemBadge ready={isProductSystemReady(draftForChecks, policy)} /></div>
            <div className="rounded-md border border-wo-border-strong bg-wo-surface-inset px-2.5 py-2 space-y-1">
              <p className="text-[11px] font-semibold text-wo-text-muted">Readiness</p>
              {missingPriceFieldsDraft.length === 0 ? <p className="text-[11px] text-emerald-300">Pricing fields complete.</p> : <p className="text-[11px] text-amber-300">Missing: {missingPriceFieldsDraft.join(", ")}</p>}
            </div>
            <div className="rounded-md border border-wo-border-strong bg-wo-surface-inset px-2.5 py-2 space-y-1">
              <p className="text-[11px] font-semibold text-wo-text-muted">Category</p>
              <p className="text-[11px] text-wo-text-secondary">Canonical: {categoryCanonical ?? "Missing"}</p>
              <p className="text-[11px] text-wo-text-muted">Suggested sub: {suggestedSubcategory ?? "No match"}</p>
            </div>
            <div className="rounded-md border border-wo-border-strong bg-wo-surface-inset px-2.5 py-2 space-y-1">
              <p className="text-[11px] font-semibold text-wo-text-muted">Source review</p>
              <p className="text-[11px] text-wo-text-secondary">Status: {sourceStatus.replace(/_/g, " ")}</p>
              <p className="text-[11px] text-wo-text-muted">Missing: {sourceMissing.length > 0 ? sourceMissing.join(", ") : "none"}</p>
            </div>
            <div className="rounded-md border border-wo-border-strong bg-wo-surface-inset px-2.5 py-2 space-y-1">
              <p className="text-[11px] font-semibold text-wo-text-muted">ProductSystem gate</p>
              {productReasons.length === 0 ? <p className="text-[11px] text-emerald-300">No blockers.</p> : <ul className="list-disc pl-4 text-[11px] text-amber-300 space-y-0.5">{productReasons.map((r) => <li key={r}>{r}</li>)}</ul>}
            </div>
            <div><FieldLabel>Motiv modificare *</FieldLabel><FieldTextarea value={form.change_reason} onChange={(v) => update("change_reason", v)} placeholder="Motiv (obligatoriu pt schimb\u0103ri de pre\u021b)" rows={2} />{reasonMissingForPriceChange && <p className="text-[11px] text-amber-300 mt-1">change_reason obligatoriu.</p>}</div>
          </CardContent></Card>

          {saveError && <div className="flex items-center gap-2 p-3 rounded-md bg-red-900/20 border border-red-800/40 text-[12px] text-red-300"><AlertTriangle className="w-4 h-4 shrink-0" />{saveError}</div>}
          {saveSuccess && <div className="flex items-center gap-2 p-3 rounded-md bg-emerald-900/20 border border-emerald-800/40 text-[12px] text-emerald-300"><CheckCircle2 className="w-4 h-4 shrink-0" />{saveSuccess}</div>}

          <div className="flex items-center gap-3 pt-1">
            <Button onClick={handleSave} disabled={disableSave} className="flex items-center gap-2">{saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}{saving ? "Se salveaz\u0103..." : "Salveaz\u0103"}</Button>
            <Button onClick={onClose} variant="outline" className="flex items-center gap-2 border-wo-border-strong bg-transparent text-wo-text-secondary hover:bg-slate-800/50"><X className="w-4 h-4" />Anuleaz\u0103</Button>
          </div>

          <div className="border-t border-wo-border-subtle pt-4">
            <Button onClick={() => setShowHistory((v) => !v)} variant="ghost" className="h-auto px-0 py-0 flex items-center gap-2 text-[12px] font-semibold text-wo-text-muted hover:text-wo-text-primary"><History className="w-4 h-4" />Istoric pre\u021buri{showHistory ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}</Button>
            {showHistory && <div className="mt-3"><PriceHistoryPanel code={material.code} refreshToken={historyRefreshToken} /></div>}
          </div>
          <div className="border-t border-wo-border-subtle pt-4">
            <Button onClick={() => setShowSourceAudit((v) => !v)} variant="ghost" className="h-auto px-0 py-0 flex items-center gap-2 text-[12px] font-semibold text-wo-text-muted hover:text-wo-text-primary"><History className="w-4 h-4" />Source review audit{showSourceAudit ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}</Button>
            {showSourceAudit && <div className="mt-3"><SourceReviewAuditPanel code={material.code} refreshToken={historyRefreshToken} /></div>}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

interface MaterialPriceRegistryProps { embedded?: boolean; }

export default function MaterialPriceRegistry({ embedded = false }: MaterialPriceRegistryProps) {
  const [items, setItems] = useState<InventoryMaterialDTO[]>([]);
  const [policy, setPolicy] = useState<InventoryMaterialsPolicyDTO>(FALLBACK_POLICY);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [quickView, setQuickView] = useState("all");
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const [showCleanupPreview, setShowCleanupPreview] = useState(false);
  const [cleanupPreview, setCleanupPreview] = useState<CategoryCleanupPreviewEntryDTO[]>([]);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [cleanupError, setCleanupError] = useState<string | null>(null);
  const [editMaterial, setEditMaterial] = useState<InventoryMaterialDTO | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setLoadError(null);
    try { const [data, policyData] = await Promise.all([inventoryMaterialsAdminApi.list(), inventoryMaterialsAdminApi.policy().catch(() => FALLBACK_POLICY)]); setItems(data); setPolicy(policyData); } catch (err) { setLoadError(err instanceof Error ? err.message : "Eroare la \u00eencarcare"); } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const loadCleanupPreview = useCallback(async () => {
    setCleanupLoading(true); setCleanupError(null);
    try { const data = await inventoryMaterialsAdminApi.categoryCleanupPreview(); setCleanupPreview(data); } catch (err) { setCleanupError(err instanceof Error ? err.message : "Eroare"); } finally { setCleanupLoading(false); }
  }, []);

  const categories = useMemo(() => { const cats = new Set<string>(); items.forEach((m) => { if (m.category) cats.add(m.category); }); return Array.from(cats).sort(); }, [items]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter((m) => {
      if (statusFilter !== "all" && m.status !== statusFilter) return false;
      if (categoryFilter !== "all" && m.category !== categoryFilter) return false;
      if (quickView === "active" && m.status !== "active") return false;
      if (quickView === "active_incomplete" && !isActiveIncomplete(m)) return false;
      if (quickView === "needs_input" && m.status !== "needs_owner_input") return false;
      if (quickView === "needs_category_normalization" && isCategoryPolicyValid(m, policy)) return false;
      if (quickView === "needs_source_review" && !needsSourceReview(m, policy)) return false;
      if (quickView === "source_stale" && !isMarkedSourceStale(m, policy)) return false;
      if (quickView === "ready" && !isReadyForPricing(m)) return false;
      if (quickView === "productsystem_ready" && !isProductSystemReady(m, policy)) return false;
      if (quickView === "archived" && m.status !== "archived") return false;
      if (q) { const hay = `${m.code} ${m.name} ${m.category ?? ""}`.toLowerCase(); if (!hay.includes(q)) return false; }
      return true;
    });
  }, [items, search, statusFilter, categoryFilter, quickView, policy]);

  const kpis = useMemo(() => {
    const total = items.length;
    const active = items.filter((m) => m.status === "active").length;
    const archived = items.filter((m) => m.status === "archived").length;
    const incomplete = items.filter(isActiveIncomplete).length;
    const ready = items.filter(isReadyForPricing).length;
    const needsCategory = items.filter((m) => !isCategoryPolicyValid(m, policy)).length;
    const needsSource = items.filter((m) => needsSourceReview(m, policy)).length;
    const sourceStale = items.filter((m) => isMarkedSourceStale(m, policy)).length;
    const productReady = items.filter((m) => isProductSystemReady(m, policy)).length;
    return { total, active, archived, incomplete, ready, needsCategory, needsSource, sourceStale, productReady };
  }, [items, policy]);

  const hasNonSearchFilters = statusFilter !== "all" || categoryFilter !== "all" || quickView !== "all";
  const hasActiveFilters = !!search.trim() || hasNonSearchFilters;

  const openEdit = (m: InventoryMaterialDTO) => { setEditMaterial(m); setDrawerOpen(true); };
  const handleSaved = (updated: InventoryMaterialDTO) => { setItems((prev) => prev.map((m) => (m.code === updated.code ? updated : m))); setEditMaterial(updated); setSaveNotice(`Material ${updated.code} actualizat.`); };

  return (
    <div className="w-full min-w-0 space-y-5">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {[
          { label: "Total materiale", value: kpis.total, cls: "text-wo-text-primary" },
          { label: "Active", value: kpis.active, cls: "text-emerald-400" },
          { label: "Incomplete", value: kpis.incomplete, cls: "text-red-400" },
          { label: "Ready for pricing", value: kpis.ready, cls: "text-cyan-400" },
          { label: "Needs review", value: kpis.needsSource, cls: "text-amber-400" },
        ].map((k) => (
          <Card key={k.label} className="border-slate-800/60 bg-slate-950/70 shadow-none">
            <CardContent className="px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-wo-text-dim">{k.label}</p>
              <p className={`text-[22px] font-bold mt-1 ${k.cls}`}>{k.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Secondary KPIs */}
      <div className="flex flex-wrap items-center gap-2 text-[11px]">
        {[
          { label: "Source stale", value: kpis.sourceStale, cls: "text-orange-300 border-orange-800/40" },
          { label: "ProductSystem ready", value: kpis.productReady, cls: "text-blue-300 border-blue-800/40" },
          { label: "Category norm.", value: kpis.needsCategory, cls: "text-yellow-300 border-yellow-800/40" },
          { label: "Archived", value: kpis.archived, cls: "text-wo-text-muted border-slate-700/50" },
        ].map((item) => (
          <Badge key={item.label} variant="outline" className={`bg-slate-900/50 px-2.5 py-1 ${item.cls}`}>{item.label}: {item.value}</Badge>
        ))}
        <Button onClick={() => void load()} disabled={loading} variant="ghost" className="ml-auto h-7 px-2.5 text-[11px] text-wo-text-muted hover:text-wo-text-primary">
          <RefreshCw className={`w-3 h-3 mr-1.5 ${loading ? "animate-spin" : ""}`} />Re\u00eencarc\u0103
        </Button>
      </div>

      {/* Filters */}
      <div className="grid gap-2 lg:grid-cols-[minmax(0,1.5fr)_180px_160px_160px_auto]">
        <div className="relative flex items-center">
          <Search className="absolute left-3 w-3.5 h-3.5 text-wo-text-dim" />
          <Input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Caut\u0103 cod, denumire, categorie..." className="pl-9 bg-slate-950/80 border-slate-800/60 text-[12px] text-wo-text-primary placeholder:text-wo-text-dim h-9" />
          {search && <Button onClick={() => setSearch("")} variant="ghost" size="icon" className="absolute right-0 h-8 w-8 text-wo-text-dim hover:text-wo-text-muted"><X className="w-3.5 h-3.5" /></Button>}
        </div>
        <Select value={quickView} onValueChange={setQuickView}><SelectTrigger className="bg-slate-950/80 border-slate-800/60 text-[12px] text-wo-text-secondary h-9"><SelectValue placeholder="Quick view" /></SelectTrigger><SelectContent>{QUICK_VIEW_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent></Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}><SelectTrigger className="bg-slate-950/80 border-slate-800/60 text-[12px] text-wo-text-secondary h-9"><SelectValue placeholder="Status" /></SelectTrigger><SelectContent>{STATUS_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent></Select>
        {categories.length > 0 && <Select value={categoryFilter} onValueChange={setCategoryFilter}><SelectTrigger className="bg-slate-950/80 border-slate-800/60 text-[12px] text-wo-text-secondary h-9"><SelectValue placeholder="Categorie" /></SelectTrigger><SelectContent><SelectItem value="all">Toate categoriile</SelectItem>{categories.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent></Select>}
        <div className="flex items-center justify-end gap-2">
          <span className="text-[11px] text-wo-text-dim whitespace-nowrap">{filtered.length}/{items.length}</span>
          {hasActiveFilters && <Button onClick={() => { setSearch(""); setStatusFilter("all"); setCategoryFilter("all"); setQuickView("all"); }} variant="outline" className="h-8 border-slate-800/60 bg-transparent px-2.5 text-[11px] text-wo-text-muted hover:bg-slate-900/80">Reset</Button>}
        </div>
      </div>

      {saveNotice && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-emerald-800/40 bg-emerald-900/15 px-4 py-2.5 text-[12px] text-emerald-300">
          <span>{saveNotice}</span>
          <Button variant="ghost" onClick={() => setSaveNotice(null)} className="h-6 px-2 text-[11px] text-emerald-200 hover:text-white">{"\u2715"}</Button>
        </div>
      )}

      {/* Category cleanup */}
      <Card className="border-slate-800/60 bg-slate-950/60 shadow-none">
        <CardHeader className="px-5 py-3 flex flex-row items-center justify-between gap-3">
          <div><CardTitle className="text-[12px] font-semibold text-wo-text-secondary">Category cleanup preview</CardTitle><p className="text-[10px] text-wo-text-dim">Preview only.</p></div>
          <Button onClick={() => { const next = !showCleanupPreview; setShowCleanupPreview(next); if (next && cleanupPreview.length === 0 && !cleanupLoading) void loadCleanupPreview(); }} variant="outline" className="border-slate-800/60 bg-transparent text-[11px] text-wo-text-muted hover:bg-slate-900/80 h-7 px-3">{showCleanupPreview ? "Hide" : "Show"}</Button>
        </CardHeader>
        {showCleanupPreview && (
          <CardContent className="px-5 pb-4 pt-0 space-y-3">
            {cleanupLoading && <div className="flex items-center gap-2 py-3 text-wo-text-muted text-[12px]"><Loader2 className="w-4 h-4 animate-spin" />Se \u00eencarc\u0103...</div>}
            {cleanupError && <div className="flex items-center gap-2 py-3 text-red-400 text-[12px]"><AlertTriangle className="w-4 h-4" />{cleanupError}</div>}
            {!cleanupLoading && !cleanupError && (cleanupPreview.length === 0 ? <p className="text-[12px] text-wo-text-muted italic">No issues detected.</p> : (
              <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">{cleanupPreview.map((item) => (
                <div key={item.material_id} className="rounded-lg border border-slate-800/50 bg-slate-900/30 px-3 py-2 text-[11px]">
                  <div className="flex items-center justify-between gap-2"><span className="text-wo-text-primary font-medium">{item.code}</span><Badge variant="outline" className="border-amber-800/40 bg-amber-900/20 text-amber-300 text-[9px] px-1.5">{item.issue_type ?? "issue"}</Badge></div>
                  <p className="text-wo-text-muted mt-0.5">{item.current_category ?? "\u2014"} \u2192 {item.suggested_category ?? "\u2014"}</p>
                </div>
              ))}</div>
            ))}
          </CardContent>
        )}
      </Card>

      {/* Table */}
      <Card className="border-slate-800/60 bg-slate-950/60 shadow-none overflow-hidden rounded-xl">
        {loading && <div className="flex items-center justify-center gap-3 py-16 text-wo-text-muted"><Loader2 className="w-5 h-5 animate-spin" /><span className="text-[13px]">Se \u00eencarc\u0103 materialele...</span></div>}
        {!loading && loadError && <div className="flex flex-col items-center gap-2 py-16 text-red-400"><AlertTriangle className="w-6 h-6" /><p className="text-[13px]">{loadError}</p><Button onClick={() => void load()} variant="outline" className="mt-2 border-red-800/40 bg-transparent text-[12px] hover:bg-red-900/20">Re\u00eencearc\u0103</Button></div>}
        {!loading && !loadError && filtered.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-16 text-wo-text-dim">
            <PackageSearch className="w-7 h-7" />
            <p className="text-[13px]">{items.length === 0 ? "Nu exist\u0103 materiale \u00een registru." : "Niciun material nu corespunde filtrelor."}</p>
            {hasActiveFilters && <Button onClick={() => { setSearch(""); setStatusFilter("all"); setCategoryFilter("all"); setQuickView("all"); }} variant="outline" className="border-slate-800/60 bg-transparent text-[12px] text-wo-text-muted hover:bg-slate-900/80">Reset filters</Button>}
          </div>
        )}
        {!loading && !loadError && filtered.length > 0 && (
          <Table className="min-w-0 text-[12px]">
            <TableHeader>
              <TableRow className="border-b border-slate-800/50 hover:bg-transparent">
                <TableHead className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-wo-text-dim">Material</TableHead>
                <TableHead className="px-3 py-3 text-[10px] font-bold uppercase tracking-wider text-wo-text-dim">Categorie</TableHead>
                <TableHead className="px-3 py-3 text-[10px] font-bold uppercase tracking-wider text-wo-text-dim w-[50px]">UM</TableHead>
                <TableHead className="px-3 py-3 text-right text-[10px] font-bold uppercase tracking-wider text-wo-text-dim">Cost</TableHead>
                <TableHead className="px-3 py-3 text-center text-[10px] font-bold uppercase tracking-wider text-wo-text-dim">Status</TableHead>
                <TableHead className="px-3 py-3 text-center text-[10px] font-bold uppercase tracking-wider text-wo-text-dim">Source</TableHead>
                <TableHead className="px-3 py-3 text-center text-[10px] font-bold uppercase tracking-wider text-wo-text-dim">Gate</TableHead>
                <TableHead className="px-3 py-3 text-right text-[10px] font-bold uppercase tracking-wider text-wo-text-dim w-[80px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((m) => {
                const mIncomplete = isActiveIncomplete(m);
                const psReady = isProductSystemReady(m, policy);
                return (
                  <TableRow key={m.code} className="border-b border-slate-800/40 hover:bg-slate-900/40 transition-colors cursor-pointer" onClick={() => openEdit(m)}>
                    <TableCell className="px-4 py-3 align-top">
                      <div className="space-y-0.5">
                        <p className="text-[12px] font-medium text-wo-text-primary truncate max-w-[200px]" title={m.name}>{m.name}</p>
                        <p className="text-[10px] font-mono text-wo-text-muted">{m.code}</p>
                        {mIncomplete && <IncompleteBadge />}
                      </div>
                    </TableCell>
                    <TableCell className="px-3 py-3 align-top">
                      <p className="text-[11px] text-wo-text-secondary truncate max-w-[140px]" title={m.category ?? undefined}>{m.category ?? "\u2014"}</p>
                    </TableCell>
                    <TableCell className="px-3 py-3 align-top text-[11px] text-wo-text-muted">{m.unit ?? "\u2014"}</TableCell>
                    <TableCell className="px-3 py-3 align-top text-right">
                      <span className="text-[13px] font-semibold text-wo-text-primary tabular-nums">{fmtCost(m.unit_cost, m.currency)}</span>
                    </TableCell>
                    <TableCell className="px-3 py-3 align-top text-center"><StatusBadge status={m.status} /></TableCell>
                    <TableCell className="px-3 py-3 align-top text-center"><SourceReviewBadge material={m} policy={policy} /></TableCell>
                    <TableCell className="px-3 py-3 align-top text-center"><ProductSystemBadge ready={psReady} /></TableCell>
                    <TableCell className="px-3 py-3 align-top text-right">
                      <Button onClick={(e) => { e.stopPropagation(); openEdit(m); }} variant="ghost" className="h-7 px-2 text-[11px] text-wo-text-muted hover:text-wo-text-primary">
                        <Pencil className="w-3 h-3 mr-1" />Edit
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>

      {editMaterial && <EditDrawer material={editMaterial} policy={policy} open={drawerOpen} onClose={() => { setDrawerOpen(false); setEditMaterial(null); }} onSaved={handleSaved} />}
    </div>
  );
}