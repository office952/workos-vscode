/**
 * Pricing Registry UI helpers — category mapping, badges, filtering.
 */

import type { PricingRegistryItem } from "@/api/pricingRegistry";

export const PRICING_REGISTRY_CATEGORIES = [
  "Plăci",
  "Role / materiale flexibile",
  "Profile / canturi",
  "LED / electrice",
  "Consumabile",
  "Operații / Rate",
  "Adaos comercial",
  "Verificare",
] as const;

export const TEMPLATE_FILTER_OPTIONS = [
  { value: "all", label: "Toate template-urile active" },
  { value: "Product 001", label: "Product 001" },
  { value: "TPL-VOLUMETRIC-LETTERS", label: "TPL-VOLUMETRIC-LETTERS" },
] as const;

export type PricingSectionTab =
  | "materials"
  | "rates"
  | "markup"
  | "verification";

/** Normalize currency code for comparison (EUR, RON, etc.). */
export function normalizeCurrencyCode(currency: string | null | undefined): string {
  return String(currency ?? "")
    .trim()
    .toUpperCase();
}

/** True when row currency differs from Settings base currency. */
export function rowCurrencyDiffersFromBase(
  item: PricingRegistryItem,
  baseCurrency: string | null | undefined
): boolean {
  const base = normalizeCurrencyCode(baseCurrency);
  const row = normalizeCurrencyCode(item.currency);
  if (!base || !row) return false;
  return row !== base;
}

export const CURRENCY_MISMATCH_WARNING =
  "Monedă diferită de moneda de bază — calcul blocat până la normalizare/conversie.";

export function confidenceBadgeLabel(confidence: string): string {
  switch (confidence) {
    case "owner_confirmed":
      return "Owner-confirmed";
    case "estimated":
      return "Estimat";
    case "missing":
      return "Lipsă preț";
    case "needs_review":
      return "Needs review";
    case "supplier_average":
      return "Medie furnizor";
    case "imported_from_inventory":
      return "Sursă tehnică";
    default:
      return confidence;
  }
}

export function confidenceBadgeClass(confidence: string): string {
  switch (confidence) {
    case "owner_confirmed":
      return "bg-emerald-900/30 text-emerald-300 border-emerald-700/50";
    case "estimated":
      return "bg-amber-900/30 text-amber-300 border-amber-700/50";
    case "missing":
      return "bg-red-900/30 text-red-300 border-red-700/50";
    default:
      return "bg-slate-800 text-slate-400 border-slate-600";
  }
}

export function statusBadgeLabel(status: string): string {
  switch (status) {
    case "active":
      return "Activ";
    case "missing_price":
      return "Lipsă preț";
    case "needs_review":
      return "Needs review";
    case "archived":
      return "Arhivat";
    default:
      return status;
  }
}

export function filterRegistryItems(
  items: PricingRegistryItem[],
  opts: {
    search?: string;
    category?: string;
    templateCode?: string;
    section?: PricingSectionTab;
    verificationOnly?: boolean;
  }
): PricingRegistryItem[] {
  let out = items;

  if (opts.section === "materials") {
    out = out.filter((i) => i.pricing_kind === "material");
  } else if (opts.section === "rates") {
    out = out.filter((i) =>
      ["operation_rate", "workcenter_rate", "service"].includes(i.pricing_kind)
    );
  } else if (opts.section === "verification") {
    out = out.filter(
      (i) =>
        i.status === "missing_price" ||
        i.status === "needs_review" ||
        i.confidence === "estimated" ||
        i.confidence === "missing"
    );
  }

  if (opts.category && opts.category !== "all") {
    out = out.filter((i) => i.registry_category === opts.category);
  }

  if (opts.templateCode && opts.templateCode !== "all") {
    const aliases = templateCodeAliases(opts.templateCode);
    out = out.filter((i) => i.used_by_templates.some((used) => aliases.includes(used)));
  }

  if (opts.search?.trim()) {
    const q = opts.search.trim().toLowerCase();
    out = out.filter(
      (i) =>
        i.pricing_code.toLowerCase().includes(q) ||
        i.display_name.toLowerCase().includes(q) ||
        i.registry_category.toLowerCase().includes(q)
    );
  }

  return out;
}

export const MATERIAL_STATUS_OPTIONS = [
  "active",
  "missing_price",
  "needs_owner_input",
  "archived",
] as const;

export const SOURCE_REVIEW_STATUS_OPTIONS = [
  "",
  "missing",
  "needs_review",
  "reviewed",
  "stale",
  "accepted_override",
] as const;

export const WORKCENTER_STATUS_OPTIONS = [
  "active",
  "missing_price",
  "needs_owner_input",
  "archived",
] as const;

export const RATE_BASIS_OPTIONS = ["per_hour", "per_linear_meter"] as const;

export interface MaterialEditFormState {
  unit_cost: string;
  currency: string;
  vat_percent: string;
  valid_from: string;
  status: string;
  source_review_status: string;
  source_notes: string;
  change_reason: string;
}

export interface WorkcenterEditFormState {
  rate_per_hour: string;
  rate_per_linear_meter: string;
  rate_basis: string;
  currency: string;
  status: string;
  notes: string;
  change_reason: string;
}

export function validateMaterialEditPayload(
  form: MaterialEditFormState
): string | null {
  if (!form.change_reason.trim()) {
    return "Motivul modificării este obligatoriu.";
  }
  const costProvided = form.unit_cost.trim().length > 0;
  if (costProvided) {
    const cost = Number(form.unit_cost);
    if (Number.isNaN(cost) || cost <= 0) {
      return "Costul unitar trebuie să fie un număr pozitiv.";
    }
  }
  if (form.status === "active" && !costProvided) {
    return "Statusul activ necesită un cost unitar pozitiv.";
  }
  if (form.vat_percent.trim()) {
    const vat = Number(form.vat_percent);
    if (Number.isNaN(vat) || vat < 0) {
      return "TVA trebuie să fie un număr valid (>= 0).";
    }
  }
  if (
    form.source_review_status === "accepted_override" &&
    !form.source_notes.trim()
  ) {
    return "Owner-confirmed (accepted_override) necesită note sursă.";
  }
  return null;
}

export function buildMaterialPatchPayload(
  form: MaterialEditFormState
): Record<string, string | number | null> {
  const payload: Record<string, string | number | null> = {
    change_reason: form.change_reason.trim(),
    snapshot_source: "pricing_registry_edit",
  };
  if (form.unit_cost.trim()) {
    payload.unit_cost = Number(form.unit_cost);
  }
  if (form.currency.trim()) {
    payload.currency = form.currency.trim();
  }
  if (form.vat_percent.trim()) {
    payload.vat_percent = Number(form.vat_percent);
  }
  if (form.valid_from.trim()) {
    payload.valid_from = form.valid_from.trim();
  }
  if (form.status.trim()) {
    payload.status = form.status.trim();
  }
  if (form.source_review_status.trim()) {
    payload.source_review_status = form.source_review_status.trim();
  }
  if (form.source_notes.trim()) {
    payload.source_notes = form.source_notes.trim();
  }
  return payload;
}

export function validateWorkcenterEditPayload(
  form: WorkcenterEditFormState
): string | null {
  if (!form.change_reason.trim()) {
    return "Motivul modificării este obligatoriu.";
  }
  if (form.rate_basis === "per_hour" && form.rate_per_hour.trim()) {
    const rate = Number(form.rate_per_hour);
    if (Number.isNaN(rate) || rate <= 0) {
      return "Rata pe oră trebuie să fie un număr pozitiv.";
    }
  }
  if (form.rate_basis === "per_linear_meter" && form.rate_per_linear_meter.trim()) {
    const rate = Number(form.rate_per_linear_meter);
    if (Number.isNaN(rate) || rate <= 0) {
      return "Rata pe metru liniar trebuie să fie un număr pozitiv.";
    }
  }
  if (form.status === "active") {
    if (form.rate_basis === "per_hour" && !form.rate_per_hour.trim()) {
      return "Statusul activ necesită o rată pe oră pozitivă.";
    }
    if (form.rate_basis === "per_linear_meter" && !form.rate_per_linear_meter.trim()) {
      return "Statusul activ necesită o rată pe metru liniar pozitivă.";
    }
  }
  return null;
}

export function buildWorkcenterPatchPayload(
  form: WorkcenterEditFormState,
  existingNotes?: string | null
): Record<string, string | number | boolean | null> {
  const auditNote = `[Pricing] ${form.change_reason.trim()}`;
  const mergedNotes = form.notes.trim()
    ? `${auditNote}\n${form.notes.trim()}`
    : existingNotes?.trim()
      ? `${auditNote}\n${existingNotes.trim()}`
      : auditNote;

  const payload: Record<string, string | number | boolean | null> = {
    notes: mergedNotes,
  };
  if (form.rate_basis.trim()) {
    payload.rate_basis = form.rate_basis.trim();
  }
  if (form.status.trim()) {
    payload.status = form.status.trim();
    payload.is_active = form.status.trim() === "active";
  }
  if (form.rate_per_hour.trim()) {
    payload.rate_per_hour = Number(form.rate_per_hour);
  }
  if (form.rate_per_linear_meter.trim()) {
    payload.rate_per_linear_meter = Number(form.rate_per_linear_meter);
  }
  return payload;
}

export function product001ExpectedCodes(): string[] {
  return [
    "MAT-ACP-FATA-LITERE",
    "MAT-SPATE-PVC-LITERE",
    "MAT-LED-MODULE",
    "MAT-SABLON-MONTAJ",
    "MAT-PROFIL-LATERAL-LITERE-30MM",
    "MAT-PROFIL-LATERAL-LITERE-60MM",
    "MAT-PROFIL-LATERAL-LITERE-80MM",
    "MAT-PROFIL-LATERAL-LITERE-100MM",
    "MAT-LED-PSU-12V-60W",
    "MAT-LED-PSU-12V-100W",
    "MAT-LED-PSU-12V-160W",
    "MAT-LED-PSU-12V-200W",
    "MAT-VOPSEA-RAL",
    "MAT-CONSUMABILE-MONTAJ",
    "RETURN_PROFILE_MACHINE_FORMING",
    "RETURN_PROFILE_FACE_BONDING",
  ];
}

// ── V2 spacious layout helpers ─────────────────────────────────────────────

export type PricingMainView = "coverage" | "all" | "verify" | "markup" | "audit";

export type StatusSeverity = "ok" | "warn" | "bad";

export interface StatusDisplay {
  text: string;
  severity: StatusSeverity;
}

export interface TemplateListEntry {
  template_code: string;
  label: string;
  family: string;
  materialCount: number;
  workcenterCount: number;
}

export interface TemplateStats {
  ownerConfirmed: number;
  estimated: number;
  needsReview: number;
  missingPrice: number;
  total: number;
  readiness: "available" | "partial" | "blocked";
  readinessLabel: string;
}

export interface ProblemQueueEntry {
  item: PricingRegistryItem;
  severity: "bad" | "warn";
  label: string;
}

export interface StackSubgroup {
  label: string;
  items: PricingRegistryItem[];
}

export interface StackSection {
  key: "materials" | "services" | "markup" | "verification";
  title: string;
  subgroups: StackSubgroup[];
}

const TEMPLATE_HUMAN_LABELS: Record<string, string> = {
  "TPL-VOLUMETRIC-LETTERS": "Litere volumetrice (Product 001)",
  "TPL-VOLUMETRIC-LETTERS_v2": "Litere volumetrice (Product 001)",
  "TPL-ACM-CASSETTED-PANEL": "Panou ACM casetat",
  "TPL-CUT-ACM-LETTERS": "Litere ACM tăiate",
};

const MATERIAL_SUBGROUP_ORDER = [
  "Plăci",
  "Role / materiale flexibile",
  "Profile / canturi",
  "LED / electrice",
  "Consumabile",
] as const;

const SERVICE_SUBGROUP_RULES: Array<{ label: string; test: (code: string) => boolean }> = [
  { label: "Formare cant", test: (c) => /FORMING|MACHINE_FORM/i.test(c) },
  { label: "Lipire cant", test: (c) => /BONDING|BOND/i.test(c) && !/MAT-/i.test(c) },
  { label: "CNC / router / laser", test: (c) => /CNC|ROUTER|LASER|CUT/i.test(c) },
  { label: "Vopsire / QC / ambalare", test: (c) => /PAINT|QC|PACK|VOPSE/i.test(c) },
];

export function resolveTemplateCode(code: string): string {
  const trimmed = code.trim();
  const upper = trimmed.toUpperCase();
  if (
    trimmed === "Product 001" ||
    upper === "TPL-VOLUMETRIC-LETTERS" ||
    upper === "TPL-VOLUMETRIC-LETTERS_V2"
  ) {
    return "TPL-VOLUMETRIC-LETTERS_v2";
  }
  return trimmed;
}

function templateCodeAliases(code: string): string[] {
  const resolved = resolveTemplateCode(code);
  if (resolved === "TPL-VOLUMETRIC-LETTERS_v2") {
    return ["TPL-VOLUMETRIC-LETTERS_v2", "TPL-VOLUMETRIC-LETTERS"];
  }
  return [resolved];
}

export function templateHumanLabel(templateCode: string): string {
  return TEMPLATE_HUMAN_LABELS[templateCode] ?? templateCode.replace(/^TPL-/, "").replace(/-/g, " ");
}

export function templateFamily(templateCode: string): string {
  const c = templateCode.toUpperCase();
  if (c.includes("VOLUMETRIC") || (c.includes("LETTER") && !c.includes("ACM"))) return "Litere";
  if (c.includes("ACM")) return "ACM";
  if (c.includes("CUT")) return "Tăiere";
  return "Altele";
}

export function buildTemplateList(
  usage: Array<{
    template_code: string;
    material_codes: string[];
    workcenter_codes: string[];
  }>
): TemplateListEntry[] {
  return usage
    .map((u) => ({
      template_code: u.template_code,
      label: templateHumanLabel(u.template_code),
      family: templateFamily(u.template_code),
      materialCount: u.material_codes.length,
      workcenterCount: u.workcenter_codes.length,
    }))
    .sort((a, b) => a.template_code.localeCompare(b.template_code));
}

export function filterTemplatesForPicker(
  templates: TemplateListEntry[],
  opts: { search?: string; family?: string }
): TemplateListEntry[] {
  let out = templates;
  if (opts.family && opts.family !== "all") {
    out = out.filter((t) => t.family === opts.family);
  }
  if (opts.search?.trim()) {
    const q = opts.search.trim().toLowerCase();
    out = out.filter(
      (t) =>
        t.template_code.toLowerCase().includes(q) ||
        t.label.toLowerCase().includes(q) ||
        t.family.toLowerCase().includes(q)
    );
  }
  return out;
}

export function itemsForTemplate(
  items: PricingRegistryItem[],
  templateCode: string
): PricingRegistryItem[] {
  const aliases = templateCodeAliases(templateCode);
  return items.filter((i) => i.used_by_templates.some((used) => aliases.includes(used)));
}

export function computeTemplateStats(items: PricingRegistryItem[]): TemplateStats {
  const ownerConfirmed = items.filter((i) => i.confidence === "owner_confirmed").length;
  const estimated = items.filter((i) => i.confidence === "estimated").length;
  const needsReview = items.filter((i) => i.status === "needs_review").length;
  const missingPrice = items.filter(
    (i) => i.status === "missing_price" || i.confidence === "missing"
  ).length;
  const total = items.length;

  let readiness: TemplateStats["readiness"] = "available";
  let readinessLabel = "Calcul preliminar disponibil";

  if (missingPrice > 0) {
    readiness = "blocked";
    readinessLabel = "Calcul preliminar blocat — preț/rată lipsă";
  } else if (needsReview > 0 || estimated > 0) {
    readiness = "partial";
    readinessLabel = "Calcul preliminar parțial — confirmări de review";
  }

  return {
    ownerConfirmed,
    estimated,
    needsReview,
    missingPrice,
    total,
    readiness,
    readinessLabel,
  };
}

export function statusDisplayText(item: PricingRegistryItem): StatusDisplay {
  if (item.status === "missing_price" || item.confidence === "missing") {
    return { text: "Rată lipsă", severity: "bad" };
  }
  if (item.status === "needs_review") {
    return { text: "Needs review", severity: "warn" };
  }
  if (item.confidence === "estimated") {
    return { text: "Estimat", severity: "warn" };
  }
  if (item.confidence === "owner_confirmed") {
    return { text: "Owner-confirmed", severity: "ok" };
  }
  return { text: confidenceBadgeLabel(item.confidence), severity: "warn" };
}

export function quoteImpactLabel(item: PricingRegistryItem): string {
  if (item.status === "missing_price" || item.confidence === "missing") {
    return "Blochează calcul complet";
  }
  if (
    item.status === "needs_review" ||
    item.confidence === "estimated" ||
    item.confidence === "needs_review"
  ) {
    return "Preliminar — review";
  }
  return "În calcul ofertă";
}

export function isProblemItem(item: PricingRegistryItem): boolean {
  return (
    item.status === "missing_price" ||
    item.status === "needs_review" ||
    item.confidence === "estimated" ||
    item.confidence === "missing"
  );
}

export function buildProblemQueue(items: PricingRegistryItem[]): ProblemQueueEntry[] {
  const problems = items.filter(isProblemItem);
  return problems.map((item) => {
    const status = statusDisplayText(item);
    const severity: "bad" | "warn" = status.severity === "bad" ? "bad" : "warn";
    return {
      item,
      severity,
      label: status.text,
    };
  });
}

export function formatProblemBanner(queue: ProblemQueueEntry[]): string | null {
  if (queue.length === 0) return null;
  const missing = queue.filter((q) => q.severity === "bad").length;
  const review = queue.filter((q) => q.severity === "warn").length;
  const parts: string[] = [];
  if (missing > 0) {
    parts.push(`${missing} ${missing === 1 ? "rată/preț lipsă" : "rate/prețuri lipsă"}`);
  }
  if (review > 0) {
    parts.push(`${review} ${review === 1 ? "estimare de confirmat" : "estimări de confirmat"}`);
  }
  return parts.join(" și ");
}

function subgroupForRate(code: string): string {
  for (const rule of SERVICE_SUBGROUP_RULES) {
    if (rule.test(code)) return rule.label;
  }
  return "Alte operații";
}

export interface DetailPanelModel {
  name: string;
  code: string;
  typeLabel: string;
  category: string;
  value: string;
  unit: string;
  status: StatusDisplay;
  impact: string;
  technicalSource: string;
  templates: string[];
  sourceNotes: string | null;
  isMaterial: boolean;
  isRate: boolean;
  isMarkup: boolean;
  editable: boolean;
  costEngineRate: number | null;
  costEngineRateMatch: boolean | null;
  currencyMismatchWarning: string | null;
}

export function buildDetailPanelModel(
  item: PricingRegistryItem | null | undefined,
  opts?: { baseCurrency?: string | null }
): DetailPanelModel | null {
  if (!item?.pricing_code) return null;

  const isMaterial = item.pricing_kind === "material";
  const isRate = ["operation_rate", "workcenter_rate", "service"].includes(
    item.pricing_kind ?? ""
  );
  const isMarkup = item.pricing_kind === "markup_rule";

  let typeLabel = "Material";
  if (isRate) typeLabel = "Rată operație / workcenter";
  if (isMarkup) typeLabel = "Regulă adaos comercial";

  const value =
    item.base_cost != null && !Number.isNaN(item.base_cost)
      ? String(item.base_cost)
      : "Lipsă";

  return {
    name: item.display_name || item.pricing_code,
    code: item.pricing_code,
    typeLabel,
    category: item.registry_category || "—",
    value,
    unit: item.unit || "—",
    status: statusDisplayText(item),
    impact: quoteImpactLabel(item),
    technicalSource: item.technical_source || "—",
    templates: Array.isArray(item.used_by_templates) ? item.used_by_templates : [],
    sourceNotes: item.source_notes ?? null,
    isMaterial,
    isRate,
    isMarkup,
    editable: item.editable !== false,
    costEngineRate: item.cost_engine_rate ?? null,
    costEngineRateMatch: item.cost_engine_rate_match ?? null,
    currencyMismatchWarning: rowCurrencyDiffersFromBase(
      item,
      opts?.baseCurrency
    )
      ? CURRENCY_MISMATCH_WARNING
      : null,
  };
}

export function groupItemsForCoverageStack(
  items: PricingRegistryItem[],
  markupPolicies: PricingRegistryItem[],
  opts?: { includeVerification?: boolean }
): StackSection[] {
  const materials = items.filter((i) => i.pricing_kind === "material");
  const rates = items.filter((i) =>
    ["operation_rate", "workcenter_rate", "service"].includes(i.pricing_kind)
  );

  const materialSubgroups: StackSubgroup[] = [];
  for (const cat of MATERIAL_SUBGROUP_ORDER) {
    const catItems = materials.filter((i) => i.registry_category === cat);
    if (catItems.length > 0) {
      materialSubgroups.push({
        label: cat,
        items: catItems.sort((a, b) => a.pricing_code.localeCompare(b.pricing_code)),
      });
    }
  }
  const otherMaterials = materials.filter(
    (i) => !MATERIAL_SUBGROUP_ORDER.includes(i.registry_category as (typeof MATERIAL_SUBGROUP_ORDER)[number])
  );
  if (otherMaterials.length > 0) {
    materialSubgroups.push({
      label: "Alte materiale",
      items: otherMaterials.sort((a, b) => a.pricing_code.localeCompare(b.pricing_code)),
    });
  }

  const serviceBuckets = new Map<string, PricingRegistryItem[]>();
  for (const rate of rates) {
    const label = subgroupForRate(rate.pricing_code);
    const bucket = serviceBuckets.get(label) ?? [];
    bucket.push(rate);
    serviceBuckets.set(label, bucket);
  }
  const serviceSubgroups: StackSubgroup[] = Array.from(serviceBuckets.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, bucketItems]) => ({
      label,
      items: bucketItems.sort((a, b) => a.pricing_code.localeCompare(b.pricing_code)),
    }));

  const sections: StackSection[] = [];
  if (materialSubgroups.length > 0) {
    sections.push({ key: "materials", title: "Materiale", subgroups: materialSubgroups });
  }
  if (serviceSubgroups.length > 0) {
    sections.push({ key: "services", title: "Servicii / operații", subgroups: serviceSubgroups });
  }
  if (markupPolicies.length > 0) {
    sections.push({
      key: "markup",
      title: "Adaos comercial",
      subgroups: [{ label: "Reguli active", items: markupPolicies }],
    });
  }

  if (opts?.includeVerification) {
    const verifyItems = items.filter(isProblemItem);
    if (verifyItems.length > 0) {
      sections.push({
        key: "verification",
        title: "Verificare",
        subgroups: [{ label: "Probleme deschise", items: verifyItems }],
      });
    }
  }

  return sections;
}

export const RECENT_TEMPLATES_STORAGE_KEY = "pricing-registry-recent-templates";

export function pushRecentTemplate(codes: string[], code: string, max = 3): string[] {
  const resolved = resolveTemplateCode(code);
  const next = [resolved, ...codes.filter((c) => c !== resolved)].slice(0, max);
  return next;
}
