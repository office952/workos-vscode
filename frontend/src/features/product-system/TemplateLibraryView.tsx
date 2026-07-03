import { useEffect, useRef, useState } from "react";
import { Search, ChevronRight, Star, SquarePen, Eye, ChevronDown, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { StatusBadge } from "@/components/workos/design-system";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { isActiveTemplateForQuote } from "@/lib/activeTemplateScope";
import { getProductTemplateIconConfig } from "@/features/product-system/productTemplateIconRegistry";
import {
  formatTemplateListDate,
  type LibraryTab,
} from "@/features/product-system/productSystemNavigation";

type SharedFoundationModuleMapping = {
  componentKey: string;
  displayName: string;
  profileKey: string;
  confidence: string;
  ownerDecision: string;
};

export interface TemplateLibraryRowSummary {
  components: number;
  operations: number;
  materials: number;
  validationPassed: number;
  validationTotal: number;
  aggregateCounts?: { components: number; operations: number; materials: number } | null;
  showDualCounts?: boolean;
  parentDirectCounts?: { components: number; operations: number; materials: number };
}

export type CatalogDensity = "compact" | "detailed";

function ProductTemplateIcon({
  templateCode,
  productSystemRole,
  compact,
}: {
  templateCode: string;
  productSystemRole?: string | null;
  compact: boolean;
}) {
  const iconConfig = getProductTemplateIconConfig(templateCode, productSystemRole);
  const Icon = iconConfig.Icon;

  return (
    <div
      aria-label={iconConfig.label}
      data-testid={`product-system-template-icon-${templateCode}`}
      data-icon-source={iconConfig.source}
      data-icon-color={iconConfig.color}
      data-icon-size={compact ? "large" : "standard"}
      className={`${compact ? "h-16 w-16 xl:h-20 xl:w-20" : "h-9 w-9"} flex shrink-0 items-center justify-center rounded-xl border`}
      style={{
        color: iconConfig.color,
        backgroundColor: iconConfig.backgroundColor,
        borderColor: iconConfig.borderColor,
      }}
    >
      {iconConfig.iconUrl ? (
        <span
          aria-hidden="true"
          className={`${compact ? "h-11 w-11 xl:h-14 xl:w-14" : "h-5 w-5"} block`}
          style={{
            backgroundColor: "currentColor",
            mask: `url(${iconConfig.iconUrl}) center / contain no-repeat`,
            WebkitMask: `url(${iconConfig.iconUrl}) center / contain no-repeat`,
          }}
        />
      ) : Icon ? (
        <Icon aria-hidden="true" className={compact ? "h-10 w-10 xl:h-12 xl:w-12" : "h-5 w-5"} />
      ) : null}
    </div>
  );
}

function CompactMetadataPopover({
  templateCode,
  label,
  recommended,
  moduleCount,
  validationPassed,
  validationTotal,
  workIntakeVisible,
  ownerDecisionRequired,
  sharedProfileLabel,
  sharedContractCount,
}: {
  templateCode: string;
  label: string;
  recommended: boolean;
  moduleCount: number;
  validationPassed: number;
  validationTotal: number;
  workIntakeVisible: boolean;
  ownerDecisionRequired: boolean;
  sharedProfileLabel?: string | null;
  sharedContractCount?: number;
}) {
  const [open, setOpen] = useState(false);
  const metadata = [
    ["Status", label],
    ["Recomandat", recommended ? "Da" : "Nu"],
    ["Module", String(moduleCount)],
    ["Validare", `${validationPassed}/${validationTotal}`],
    ["Work Intake", workIntakeVisible ? "Da" : "Nu"],
    ["GO owner", ownerDecisionRequired ? "Da" : "Nu"],
    ...(sharedContractCount ? [["Shared foundation", `${sharedContractCount} contracte`], ["Profile", sharedProfileLabel ?? "—"]] : []),
  ];

  return (
    <div
      className="relative"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <button
        type="button"
        aria-label={`Detalii ${templateCode}`}
        aria-expanded={open}
        data-testid={`product-system-template-meta-trigger-${templateCode}`}
        onClick={(event) => {
          event.stopPropagation();
          setOpen(true);
        }}
        onKeyDown={(event) => event.stopPropagation()}
        className="flex h-7 w-7 items-center justify-center rounded-md border border-slate-700 bg-slate-900/70 text-slate-400 transition-colors hover:border-purple-500/40 hover:text-purple-200 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
      >
        <Info className="h-3.5 w-3.5" />
      </button>
      {open ? (
        <div
          role="tooltip"
          data-testid={`product-system-template-meta-popover-${templateCode}`}
          className="absolute right-0 top-8 z-30 w-56 rounded-lg border border-slate-700 bg-slate-950 p-3 text-[11px] shadow-xl shadow-black/40"
          onClick={(event) => event.stopPropagation()}
        >
          <p className="mb-2 font-mono text-[10px] font-bold text-slate-300">{templateCode}</p>
          <dl className="space-y-1.5">
            {metadata.map(([term, value]) => (
              <div key={term} className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">{term}</dt>
                <dd className="text-right font-bold text-slate-200">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}
    </div>
  );
}

function TemplateLibraryRow({
  template,
  availability,
  summary,
  recommended,
  density,
  onOpen,
}: {
  template: ProductTemplateEntity;
  availability: ProductTemplateAvailabilityItem | null;
  summary: TemplateLibraryRowSummary;
  recommended: boolean;
  density: CatalogDensity;
  onOpen: () => void;
}) {
  const [compositionOpen, setCompositionOpen] = useState(false);
  const detailed = density === "detailed";
  const quoteActive = isActiveTemplateForQuote(template);
  const updated = formatTemplateListDate(template.updated_at);
  const created = formatTemplateListDate(template.created_at);
  const label = availability?.ui_label ?? (quoteActive ? "Produs activ pentru ofertare" : "Arhivat / experimental");
  const parentCodes = availability?.parent_product_codes ?? [];
  const compositionModules = availability?.composition_modules ?? [];
  const canShowComposition =
    compositionModules.length > 0 &&
    (availability?.display_group === "active_products" || availability?.display_group === "candidate_products");
  const compositionLabel = availability?.display_group === "candidate_products" ? "Module produs candidat" : "Module produs";
  const moduleCount = compositionModules.length || availability?.child_module_codes.length || availability?.module_codes.length || 0;
  const sharedContracts = availability?.shared_component_contracts ?? [];
  const sharedProfileLabel = Array.from(new Set(sharedContracts.map((contract) => contract.profile_key))).join(" + ");
  const hasLightingAudit = sharedContracts.some((contract) => contract.component_key === "volumetric_lighting" && (contract.confidence === "PARTIAL" || contract.owner_decision === "NEEDS_MORE_AUDIT"));
  const compactStatusLabel = availability?.display_group === "candidate_products" ? "In pregatire" : availability?.display_group === "active_products" ? "Produs ofertabil" : label;
  const metricsLine = summary.showDualCounts && summary.aggregateCounts && summary.parentDirectCounts
    ? [
        label,
        `Parent direct: ${summary.parentDirectCounts.components}/${summary.parentDirectCounts.operations}/${summary.parentDirectCounts.materials}`,
        `Aggregate: ${summary.aggregateCounts.components}/${summary.aggregateCounts.operations}/${summary.aggregateCounts.materials}`,
        `Validare ${summary.validationPassed}/${summary.validationTotal}`,
      ].join(" · ")
    : [
        label,
        `${summary.components} componente`,
        `${summary.operations} operații`,
        `${summary.materials} materiale`,
        `Validare ${summary.validationPassed}/${summary.validationTotal}`,
      ].join(" · ");

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOpen();
        }
      }}
      data-testid={`product-system-template-${template.template_code}`}
      className={`bg-[#111827] border rounded-lg ${detailed ? "p-4" : "p-3"} cursor-pointer transition-all group ${
        availability?.display_group === "active_products"
          ? "border-[#1E293B] hover:border-purple-600/40 hover:bg-[#131B2E]"
          : "border-slate-800/80 hover:border-slate-600/50 hover:bg-[#131B2E]/80 opacity-90"
      } ${recommended ? "ring-1 ring-purple-500/30 border-purple-500/40" : ""}`}
    >
      <div className="flex min-h-[5rem] items-start gap-3">
          <ProductTemplateIcon
            templateCode={template.template_code}
            productSystemRole={availability?.product_system_role}
            compact={!detailed}
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`${detailed ? "text-[14px]" : "text-[12px]"} font-mono font-bold text-slate-100 truncate`}>
                {template.template_code}
              </span>
              {detailed && recommended ? (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-semibold rounded bg-purple-900/30 text-purple-300 border border-purple-700/40">
                  <Star className="w-2.5 h-2.5" />
                  Recomandat
                </span>
              ) : null}
              {detailed ? <StatusBadge
                domain="productSystem"
                status={availability?.display_group === "archived_experimental" ? "archived" : "active"}
                label={label}
                className="text-[9px] uppercase"
              /> : null}
            </div>
            <p className="text-[12px] text-slate-400 truncate mt-0.5">
              {template.family_name || "—"}
            </p>
            {detailed ? <p className="text-[11px] text-slate-500 mt-1">{metricsLine}</p> : <p className="mt-1 text-[11px] font-bold text-slate-300">{compactStatusLabel}</p>}
            {!detailed && sharedContracts.length > 0 ? (
              <div data-testid={`product-system-template-compact-foundation-${template.template_code}`} className="mt-1 flex flex-wrap gap-1 text-[9px] font-bold">
                <span className="rounded border border-cyan-700/40 bg-cyan-950/30 px-1.5 py-0.5 text-cyan-200">Foundation {sharedContracts.length}</span>
                <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-300">Profile {sharedProfileLabel}</span>
              </div>
            ) : null}
            {detailed ? (
              <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] font-bold">
                <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-300">Module {moduleCount}</span>
                <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-300">Validare {summary.validationPassed}/{summary.validationTotal}</span>
                <span className={`rounded border px-1.5 py-0.5 ${availability?.quote_offerable ? "border-emerald-700/40 bg-emerald-900/20 text-emerald-300" : "border-slate-700 bg-slate-900 text-slate-400"}`}>Work Intake: {availability?.quote_offerable ? "DA" : "NU"}</span>
                {availability?.owner_decision_required ? <span className="rounded border border-amber-700/40 bg-amber-900/20 px-1.5 py-0.5 text-amber-300">GO owner</span> : null}
              </div>
            ) : null}
            {detailed && sharedContracts.length > 0 ? (
              <div data-testid={`product-system-template-shared-foundation-${template.template_code}`} className="mt-2 flex flex-wrap gap-1.5 text-[10px] font-bold">
                <span className="rounded border border-cyan-700/40 bg-cyan-950/30 px-1.5 py-0.5 text-cyan-200">Shared foundation: {sharedContracts.length} contracte</span>
                <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-slate-300">Profile {sharedProfileLabel}</span>
                {hasLightingAudit ? <span className="rounded border border-amber-700/40 bg-amber-900/20 px-1.5 py-0.5 text-amber-300">Lighting PARTIAL</span> : null}
              </div>
            ) : null}
            {detailed && parentCodes.length > 0 ? (
              <p className="text-[10px] text-slate-500 mt-1">
                Folosit de: {parentCodes.join(", ")}
              </p>
            ) : null}
            {detailed && availability?.display_group === "active_products" ? (
              <p className="text-[10px] text-emerald-300/90 mt-1">Apare in Work Intake</p>
            ) : null}
            {detailed && availability?.runtime_module ? (
              <p className="text-[10px] text-slate-500 mt-1">Nu se alege direct in Work Intake</p>
            ) : null}
            {detailed && availability?.owner_decision_required ? (
              <p className="text-[10px] text-amber-300/90 mt-1">
                Nu apare in Work Intake. {" "}
                Necesita GO owner pentru ofertare.
              </p>
            ) : null}
            {detailed && (updated || created) && (
              <p className="text-[10px] text-slate-600 mt-1">
                {updated ? `Actualizat: ${updated}` : null}
                {updated && created ? " · " : null}
                {created ? `Creat: ${created}` : null}
              </p>
            )}
          </div>
      </div>

      <div className={`${detailed ? "mt-3" : "mt-2"} flex items-end justify-between gap-3`}>
        <div className="min-h-8">
          {canShowComposition ? (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                setCompositionOpen((value) => !value);
              }}
              onKeyDown={(event) => event.stopPropagation()}
              aria-expanded={compositionOpen}
              aria-label={`${compositionOpen ? "Ascunde" : "Afiseaza"} modulele produsului, ${compositionModules.length} module`}
              data-testid={`product-system-template-composition-trigger-${template.template_code}`}
              className={`inline-flex items-center justify-center rounded-md border border-slate-700 bg-slate-900/70 text-[10px] font-bold text-slate-200 hover:border-purple-500/40 hover:text-purple-200 focus:outline-none focus:ring-2 focus:ring-purple-500/40 ${
                detailed ? "gap-2 px-2 py-1" : "h-8 w-8 px-0 py-0"
              }`}
            >
              {detailed ? <span>{compositionLabel} ({compositionModules.length})</span> : null}
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${compositionOpen ? "rotate-180" : ""}`} />
            </button>
          ) : null}
        </div>

        <div data-testid={`product-system-template-bottom-actions-${template.template_code}`} className="flex shrink-0 items-center gap-2">
          {!detailed ? (
            <CompactMetadataPopover
              templateCode={template.template_code}
              label={label}
              recommended={recommended}
              moduleCount={moduleCount}
              validationPassed={summary.validationPassed}
              validationTotal={summary.validationTotal}
              workIntakeVisible={Boolean(availability?.quote_offerable)}
              ownerDecisionRequired={Boolean(availability?.owner_decision_required)}
              sharedProfileLabel={sharedProfileLabel || null}
              sharedContractCount={sharedContracts.length}
            />
          ) : null}
          <Tooltip>
            <TooltipTrigger asChild>
              <span
                aria-label={availability?.display_group === "archived_experimental" ? "Vezi template" : "Deschide editor"}
                className={`w-8 h-8 rounded-md flex items-center justify-center border transition-colors ${
                  availability?.display_group === "active_products"
                    ? "bg-purple-500/10 border-purple-500/25 text-purple-300 group-hover:bg-purple-500/20 group-hover:border-purple-500/40"
                    : "bg-slate-800/50 border-slate-700/60 text-slate-400 group-hover:bg-slate-800 group-hover:text-slate-300"
                }`}
              >
                {availability?.display_group !== "archived_experimental" ? (
                  <SquarePen className="w-3.5 h-3.5" />
                ) : (
                  <Eye className="w-3.5 h-3.5" />
                )}
              </span>
            </TooltipTrigger>
            <TooltipContent side="left" className="text-[11px]">
              {availability?.display_group === "archived_experimental" ? "Vezi template" : "Deschide editor"}
            </TooltipContent>
          </Tooltip>
          {detailed ? <ChevronRight
            className={`w-4 h-4 transition-transform group-hover:translate-x-0.5 ${
              quoteActive ? "text-purple-400" : "text-slate-600"
            }`}
          /> : null}
        </div>
      </div>
      {canShowComposition ? (
        <div className={`${detailed ? "mt-3 pt-3" : "mt-2 pt-2"} border-t border-slate-800/80`}>
          {compositionOpen ? (
            <div className="mt-2 overflow-hidden rounded-lg border border-slate-800 bg-slate-950/40">
              <div className="grid grid-cols-[minmax(0,1.2fr)_minmax(0,1.4fr)_auto] gap-2 border-b border-slate-800 px-2.5 py-1.5 text-[9px] font-bold uppercase text-slate-500">
                <span>Rol</span>
                <span>Template componenta</span>
                <span>Status</span>
              </div>
              <div className="divide-y divide-slate-800/80">
                {compositionModules.map((module) => (
                  <div
                    key={`${module.role_key}-${module.module_template_code}`}
                    className="grid grid-cols-[minmax(0,1.2fr)_minmax(0,1.4fr)_auto] gap-2 px-2.5 py-1.5 text-[11px]"
                  >
                    <div className="min-w-0">
                      <p className="font-bold text-slate-100">{module.role_label}</p>
                      {detailed && module.ui_hint ? <p className="mt-0.5 text-[10px] text-slate-500">{module.ui_hint}</p> : null}
                    </div>
                    <p className="min-w-0 truncate font-mono text-[10px] text-slate-400">{module.module_template_code}</p>
                    <span
                      className={`h-fit whitespace-nowrap rounded-full border px-2 py-0.5 text-[9px] font-bold ${
                        module.is_required
                          ? "border-emerald-700/40 bg-emerald-900/20 text-emerald-300"
                          : "border-amber-700/40 bg-amber-900/20 text-amber-300"
                      }`}
                    >
                      {module.status_label ?? (module.is_required ? "Modul intern activ" : "Optional / conditionat")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

const CATALOG_GROUPS = [
  {
    id: "active_products",
    title: "Produse active pentru ofertare",
    chip: "Produse ofertabile",
    description: "Produse care pot fi alese direct in Work Intake si pot porni un flow de ofertare.",
  },
  {
    id: "candidate_products",
    title: "Produse in pregatire",
    chip: "Produse in pregatire",
    description: "Produse structurale existente in Product System, dar care nu apar in Work Intake pana la GO owner.",
  },
  {
    id: "internal_modules",
    title: "Module interne active",
    chip: "Module interne",
    description: "Componente folosite de produse parinte. Nu se aleg direct in Work Intake.",
  },
  {
    id: "shared_components",
    title: "Componente comune",
    chip: "Componente comune",
    description: "Module confirmate sau reutilizabile intre mai multe produse.",
  },
  {
    id: "archived_experimental",
    title: "Arhivate / experimentale",
    chip: "Arhivate / experimentale",
    description: "Scoase din flow activ sau experimentale.",
  },
] as const;

type CatalogGroupId = (typeof CATALOG_GROUPS)[number]["id"];

export type ProductSystemCatalogView = "overview" | "products" | "components" | "composition" | "archived";

const CATALOG_VIEWS: Array<{
  id: ProductSystemCatalogView;
  label: string;
  description: string;
}> = [
  { id: "overview", label: "Overview", description: "Orientare rapida" },
  { id: "products", label: "Produse", description: "Produse ofertabile si candidate" },
  { id: "components", label: "Componente", description: "Module interne si shared" },
  { id: "composition", label: "Compozitii", description: "Produs -> rol -> componenta" },
  { id: "archived", label: "Arhivate", description: "Scoase din flow activ" },
];

type ProductFilter = "all" | "offerable" | "candidate" | "owner_go";
type ComponentFilter = "all" | "internal" | "shared";

function normalizeTemplateCode(code: string): string {
  return code.trim().toUpperCase();
}

function fallbackAvailability(template: ProductTemplateEntity): ProductTemplateAvailabilityItem {
  const quoteActive = isActiveTemplateForQuote(template);
  return {
    template_id: template.id,
    template_code: template.template_code,
    family_id: template.family_id ?? null,
    family_name: template.family_name ?? null,
    description: template.description ?? null,
    db_active: template.active !== false,
    quote_offerable: quoteActive,
    runtime_module: false,
    is_parent: false,
    has_modules: false,
    parent_codes: [],
    module_codes: [],
    status: quoteActive ? "offerable" : "not_offerable",
    status_reason: quoteActive ? "frontend_fallback_owner_valid" : "availability_unavailable",
    product_system_role: quoteActive ? "offerable_product" : "archived_experimental",
    display_group: quoteActive ? "active_products" : "archived_experimental",
    importance_rank: quoteActive ? 10 : 50,
    owner_decision_required: !quoteActive,
    readiness_reason: quoteActive
      ? "Produs valid pentru ofertare in Work Intake."
      : "Availability API indisponibil; clasificare defensiva.",
    ui_label: quoteActive ? "Produs activ pentru ofertare" : "Arhivat / experimental",
    ui_description: quoteActive
      ? "Poate fi ales ca produs initial in Work Intake."
      : "Scos din flow activ sau experimental.",
    parent_product_codes: [],
    child_module_codes: [],
    shared_with_product_codes: [],
    composition_modules: [],
    shared_component_contracts: [],
  };
}

function getRowSearchText({
  template,
  availability,
}: {
  template: ProductTemplateEntity;
  availability: ProductTemplateAvailabilityItem;
}): string {
  return [
    template.template_code,
    template.family_name,
    template.description,
    availability.ui_label,
    availability.ui_description,
    availability.readiness_reason,
    availability.parent_product_codes.join(" "),
    availability.shared_with_product_codes.join(" "),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function getCompositionSearchText({
  template,
  availability,
}: {
  template: ProductTemplateEntity;
  availability: ProductTemplateAvailabilityItem;
}): string {
  return [
    getRowSearchText({ template, availability }),
    ...availability.composition_modules.flatMap((module) => [
      module.role_label,
      module.role_key,
      module.module_template_code,
      module.status_label,
    ]),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function buildSharedFoundationModuleMap(
  availabilityItems: ProductTemplateAvailabilityItem[]
): Map<string, SharedFoundationModuleMapping> {
  const map = new Map<string, SharedFoundationModuleMapping>();
  for (const item of availabilityItems) {
    for (const contract of item.shared_component_contracts ?? []) {
      map.set(normalizeTemplateCode(contract.module_template_code), {
        componentKey: contract.component_key,
        displayName: contract.display_name,
        profileKey: contract.profile_key,
        confidence: contract.confidence,
        ownerDecision: contract.owner_decision,
      });
    }
  }
  return map;
}

export function TemplateLibraryView({
  templates,
  availabilityItems = [],
  tab,
  search,
  onSearchChange,
  catalogView,
  onCatalogViewChange,
  density,
  onDensityChange,
  summaries,
  recommendedTemplateId,
  loading,
  onOpenTemplate,
}: {
  templates: ProductTemplateEntity[];
  availabilityItems?: ProductTemplateAvailabilityItem[];
  tab: LibraryTab;
  onTabChange: (tab: LibraryTab) => void;
  search: string;
  onSearchChange: (value: string) => void;
  catalogView: ProductSystemCatalogView;
  onCatalogViewChange: (view: ProductSystemCatalogView) => void;
  density: CatalogDensity;
  onDensityChange: (density: CatalogDensity) => void;
  summaries: Map<number, TemplateLibraryRowSummary>;
  recommendedTemplateId: number | null;
  activeCount: number;
  archivedCount: number;
  loading: boolean;
  onOpenTemplate: (template: ProductTemplateEntity) => void;
}) {
  const headingRef = useRef<HTMLHeadingElement | null>(null);
  const [productFilter, setProductFilter] = useState<ProductFilter>("all");
  const [componentFilter, setComponentFilter] = useState<ComponentFilter>("all");
  const [parentFilter, setParentFilter] = useState("all");
  const availabilityByCode = new Map(
    availabilityItems.map((item) => [normalizeTemplateCode(item.template_code), item])
  );
  const sharedFoundationByModule = buildSharedFoundationModuleMap(availabilityItems);
  const q = search.trim().toLowerCase();
  const allCatalogRows = templates
    .map((template) => ({
      template,
      availability: availabilityByCode.get(normalizeTemplateCode(template.template_code)) ?? fallbackAvailability(template),
    }))
    .sort((a, b) => {
      const rank = a.availability.importance_rank - b.availability.importance_rank;
      if (rank !== 0) return rank;
      return a.template.template_code.localeCompare(b.template.template_code);
    });

  const grouped = CATALOG_GROUPS.reduce(
    (acc, group) => {
      acc[group.id] = allCatalogRows.filter((row) => row.availability.display_group === group.id);
      return acc;
    },
    {} as Record<CatalogGroupId, typeof allCatalogRows>
  );

  const productRows = allCatalogRows.filter((row) =>
    row.availability.product_system_role === "offerable_product" ||
    row.availability.product_system_role === "candidate_product"
  );
  const componentRows = allCatalogRows.filter((row) =>
    row.availability.product_system_role === "internal_module" ||
    row.availability.product_system_role === "shared_component"
  );
  const archivedRows = allCatalogRows.filter((row) => row.availability.display_group === "archived_experimental");
  const compositionRows = productRows.filter((row) => row.availability.composition_modules.length > 0);
  const parentOptions = Array.from(
    new Set(componentRows.flatMap((row) => row.availability.parent_product_codes.length > 0 ? row.availability.parent_product_codes : row.availability.parent_codes))
  ).sort();
  const searchedProductRows = productRows
    .filter((row) => !q || getRowSearchText(row).includes(q))
    .filter((row) => {
      if (productFilter === "offerable") return row.availability.quote_offerable;
      if (productFilter === "candidate") return row.availability.product_system_role === "candidate_product";
      if (productFilter === "owner_go") return row.availability.owner_decision_required;
      return true;
    });
  const searchedComponentRows = componentRows
    .filter((row) => !q || getRowSearchText(row).includes(q))
    .filter((row) => {
      if (componentFilter === "internal") return row.availability.product_system_role === "internal_module";
      if (componentFilter === "shared") return Boolean(sharedFoundationByModule.get(normalizeTemplateCode(row.template.template_code))) || row.availability.product_system_role === "shared_component";
      return true;
    })
    .filter((row) => {
      if (parentFilter === "all") return true;
      const parents = row.availability.parent_product_codes.length > 0 ? row.availability.parent_product_codes : row.availability.parent_codes;
      return parents.includes(parentFilter);
    });
  const searchedCompositionRows = productRows.filter((row) => !q || getCompositionSearchText(row).includes(q));
  const searchedArchivedRows = archivedRows.filter((row) => !q || getRowSearchText(row).includes(q));
  const currentView = CATALOG_VIEWS.find((view) => view.id === catalogView) ?? CATALOG_VIEWS[0];
  const detailed = density === "detailed";
  const sharedFoundationProductRows = productRows.filter((row) => row.availability.shared_component_contracts.length > 0);
  const sharedFoundationContractKeys = new Set(
    sharedFoundationProductRows.flatMap((row) => row.availability.shared_component_contracts.map((contract) => contract.component_key))
  );
  const sharedFoundationLightingPartial = sharedFoundationProductRows.some((row) =>
    row.availability.shared_component_contracts.some((contract) => contract.component_key === "volumetric_lighting" && contract.confidence === "PARTIAL")
  );
  const hasOfferableSharedFoundationProduct = sharedFoundationProductRows.some((row) => row.availability.quote_offerable);
  const hasCandidateSharedFoundationProduct = sharedFoundationProductRows.some((row) => row.availability.product_system_role === "candidate_product");

  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true });
  }, [catalogView]);

  const renderTemplateRow = ({ template, availability }: (typeof allCatalogRows)[number]) => {
    const summary = summaries.get(template.id) ?? {
      components: 0,
      operations: 0,
      materials: 0,
      validationPassed: 0,
      validationTotal: 6,
    };
    return (
      <TemplateLibraryRow
        key={template.id}
        template={template}
        availability={availability}
        summary={summary}
        recommended={recommendedTemplateId === template.id}
        density={density}
        onOpen={() => onOpenTemplate(template)}
      />
    );
  };

  return (
    <div className="space-y-3" data-testid="product-system-catalog-shell" data-density={density}>
      <div className="rounded-lg border border-[#1E293B] bg-[#0D1321] px-3 py-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-[14px] font-bold text-slate-100">Product System Catalog</p>
            {detailed ? <p className="mt-0.5 text-[11px] text-slate-500">Catalog scalabil pentru produse, componente si compozitii.</p> : null}
          </div>
          <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950/50 p-0.5" aria-label="Afisare catalog">
            {(["compact", "detailed"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                data-testid={`product-system-density-${mode}`}
                onClick={() => onDensityChange(mode)}
                className={`rounded-md px-2 py-1 text-[10px] font-bold ${density === mode ? "bg-purple-500/20 text-purple-100" : "text-slate-500 hover:text-slate-300"}`}
              >
                {mode === "compact" ? "Compact" : "Detaliat"}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5" role="tablist" aria-label="Product System catalog views">
          {CATALOG_VIEWS.map((view) => {
            const active = catalogView === view.id;
            const count = view.id === "products" ? productRows.length : view.id === "components" ? componentRows.length : view.id === "composition" ? compositionRows.length : view.id === "archived" ? archivedRows.length : allCatalogRows.length;
            return (
              <button
                key={view.id}
                type="button"
                role="tab"
                aria-selected={active}
                data-testid={`product-system-view-tab-${view.id}`}
                onClick={() => onCatalogViewChange(view.id)}
                className={`rounded-md border px-2.5 py-1 text-[10px] font-bold transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500/40 ${
                  active
                    ? "border-purple-500/50 bg-purple-500/10 text-purple-100"
                    : "border-slate-700 bg-slate-900/70 text-slate-300 hover:border-purple-500/30 hover:text-purple-200"
                }`}
              >
                {view.label}{view.id !== "overview" ? ` ${count}` : ""}
              </button>
            );
          })}
        </div>
      </div>

      <section className="rounded-lg border border-[#1E293B] bg-[#0B1120]/70 p-3" data-testid={`product-system-view-${catalogView}`}>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 ref={headingRef} tabIndex={-1} className="text-[14px] font-bold text-slate-100 focus:outline-none">
              {currentView.label}
            </h2>
            {detailed ? <p className="mt-0.5 text-[11px] text-slate-500">
              {catalogView === "overview" ? "Alege o zona pentru lucru. Overview-ul nu afiseaza toate componentele, ca sa ramana clar si rapid la volum mare." : currentView.description}
            </p> : null}
          </div>
          <span className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] font-bold text-slate-400">
            {allCatalogRows.length} total
          </span>
        </div>

        {loading ? (
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-2" />
            <p className="text-[12px] text-slate-500">Se încarcă șabloanele…</p>
          </div>
        ) : allCatalogRows.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-[13px]">Nu există șabloane în registru.</div>
        ) : catalogView === "overview" ? (
          <div className="space-y-3">
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
              {[
                { id: "products" as const, title: "Produse", count: productRows.length, detail: `${grouped.active_products.length} ofertabil, ${grouped.candidate_products.length} in pregatire`, action: "Vezi produse" },
                { id: "components" as const, title: "Componente / Module", count: componentRows.length, detail: `${grouped.internal_modules.length} module interne, ${sharedFoundationByModule.size} mapate la contract comun`, action: "Vezi componente" },
                { id: "composition" as const, title: "Compozitii", count: compositionRows.length, detail: "Produse cu compozitie expusa in API", action: "Vezi compozitii" },
                { id: "archived" as const, title: "Arhivate / experimentale", count: archivedRows.length, detail: "Template-uri scoase din flow activ", action: "Vezi arhivate" },
              ].map((card) => (
                <button key={card.id} type="button" onClick={() => onCatalogViewChange(card.id)} data-testid={`product-system-overview-card-${card.id}`} className="rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-left transition-colors hover:border-purple-500/40 hover:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-500/40">
                  <span className="flex items-center justify-between gap-2 text-[11px] font-bold text-slate-200"><span>{card.title}</span><span className="text-lg text-slate-100">{card.count}</span></span>
                  {detailed ? <span className="mt-1 block text-[10px] text-slate-500">{card.detail}</span> : null}
                  <span className="mt-1 inline-flex text-[10px] font-bold text-purple-300">{card.action}</span>
                </button>
              ))}
            </div>

            <div data-testid="product-system-overview-shared-foundation" className="rounded-lg border border-cyan-800/40 bg-cyan-950/10 px-3 py-2">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[12px] font-bold text-cyan-100">Shared Volumetric Foundation</p>
                  <p className="mt-0.5 text-[10px] text-cyan-300/70">Read-only Product System metadata. Nu activeaza pricing, executie sau Work Intake.</p>
                </div>
                <div className="flex flex-wrap gap-1.5 text-[10px] font-bold">
                  <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">{sharedFoundationProductRows.length} produse conectate</span>
                  <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">{sharedFoundationContractKeys.size} contracte comune</span>
                  {sharedFoundationLightingPartial ? <span className="rounded border border-amber-700/40 bg-amber-900/20 px-2 py-0.5 text-amber-300">Lighting PARTIAL / needs audit</span> : null}
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] font-bold">
                {hasOfferableSharedFoundationProduct ? <span className="rounded border border-emerald-700/40 bg-emerald-900/20 px-2 py-0.5 text-emerald-300">Letters: offerable</span> : null}
                {hasCandidateSharedFoundationProduct ? <span className="rounded border border-amber-700/40 bg-amber-900/20 px-2 py-0.5 text-amber-300">Logo: candidate / not Work Intake</span> : null}
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2">
              <p className="text-[12px] font-bold text-slate-200">Produse importante</p>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                {productRows.slice(0, 4).map(({ template, availability }) => (
                  <div key={template.id} className="rounded-md border border-slate-800 bg-slate-900/50 px-2.5 py-1.5">
                    <p className="font-mono text-[11px] font-bold text-slate-100">{template.template_code}</p>
                    {detailed ? <p className="mt-0.5 text-[10px] text-slate-500">{availability.ui_label}</p> : null}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center gap-2 bg-[#111827] rounded-md px-2.5 py-1.5 border border-[#1E293B] w-full max-w-md">
                <Search className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                <input type="text" placeholder="Caută cod șablon, familie…" value={search} onChange={(e) => onSearchChange(e.target.value)} className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full" />
              </div>

              {catalogView === "products" ? (
                <div className="flex flex-wrap gap-2">
                  {[["all", "Toate produsele"], ["offerable", "Ofertabile"], ["candidate", "In pregatire"], ["owner_go", "Necesita GO owner"]].map(([id, label]) => (
                    <button key={id} type="button" onClick={() => setProductFilter(id as ProductFilter)} className={`rounded-md border px-2.5 py-1 text-[10px] font-bold ${productFilter === id ? "border-purple-500/50 bg-purple-500/10 text-purple-200" : "border-slate-700 bg-slate-900 text-slate-400"}`}>{label}</button>
                  ))}
                </div>
              ) : null}

              {catalogView === "components" ? (
                <div className="flex flex-wrap gap-2">
                  {[["all", "Toate componentele"], ["internal", "Module interne"], ["shared", "Contract comun"]].map(([id, label]) => (
                    <button key={id} type="button" onClick={() => setComponentFilter(id as ComponentFilter)} className={`rounded-md border px-2.5 py-1 text-[10px] font-bold ${componentFilter === id ? "border-purple-500/50 bg-purple-500/10 text-purple-200" : "border-slate-700 bg-slate-900 text-slate-400"}`}>{label}</button>
                  ))}
                  <select aria-label="Filtru produs parinte" value={parentFilter} onChange={(event) => setParentFilter(event.target.value)} className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-[10px] font-bold text-slate-300 outline-none">
                    <option value="all">Toti parintii</option>
                    {parentOptions.map((code) => <option key={code} value={code}>{code}</option>)}
                  </select>
                </div>
              ) : null}
            </div>

            {catalogView === "products" ? (
              <div className="space-y-2">
                {detailed ? <p className="text-[11px] text-slate-500">Produse ofertabile si produse in pregatire. Modulele interne nu sunt afisate aici.</p> : null}
                {searchedProductRows.length === 0 ? <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 px-3 py-3 text-[11px] text-slate-500">Niciun produs pentru filtrele curente.</div> : <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4" data-testid="product-system-products-list">{searchedProductRows.map(renderTemplateRow)}</div>}
              </div>
            ) : null}

            {catalogView === "components" ? (
              <div className="space-y-2">
                {detailed ? <p className="text-[11px] text-slate-500">Componente interne si shared folosite de produse. Nu se aleg direct in Work Intake.</p> : null}
                {searchedComponentRows.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 px-3 py-3 text-[11px] text-slate-500">Nicio componenta pentru filtrele curente.</div>
                ) : (
                  <div className="overflow-hidden rounded-lg border border-slate-800" data-testid="product-system-components-list">
                    <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1.15fr)_minmax(0,0.9fr)_minmax(0,1.25fr)_auto] gap-2 border-b border-slate-800 bg-slate-950/40 px-2.5 py-1.5 text-[9px] font-bold uppercase text-slate-500"><span>Rol / label</span><span>Template code</span><span>Folosit de</span><span>Contract comun</span><span>Status</span></div>
                    <div className="divide-y divide-slate-800/80">
                      {searchedComponentRows.map(({ template, availability }) => {
                        const parents = availability.parent_product_codes.length > 0 ? availability.parent_product_codes : availability.parent_codes;
                        const foundation = sharedFoundationByModule.get(normalizeTemplateCode(template.template_code));
                        return (
                          <div key={template.id} data-testid={`product-system-component-row-${template.template_code}`} className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1.15fr)_minmax(0,0.9fr)_minmax(0,1.25fr)_auto] gap-2 px-2.5 py-1.5 text-[11px]">
                            <span className="min-w-0 font-bold text-slate-100">{availability.ui_label}</span>
                            <span className="min-w-0 truncate font-mono text-[10px] text-slate-400">{template.template_code}</span>
                            <span className="min-w-0 truncate text-[10px] text-slate-500">{parents.length > 0 ? parents.join(", ") : "Necunoscut"}</span>
                            {foundation ? (
                              <span data-testid={`product-system-component-foundation-${template.template_code}`} className="min-w-0 text-[10px] text-slate-300">
                                <span className="font-mono font-bold text-cyan-200">{foundation.componentKey}</span>
                                <span className="block text-slate-500">Profil: {foundation.profileKey}</span>
                              </span>
                            ) : (
                              <span className="text-[10px] text-slate-600">Fara contract comun</span>
                            )}
                            <span className="whitespace-nowrap rounded-full border border-slate-700 bg-slate-900 px-2 py-0.5 text-[9px] font-bold text-slate-300">{availability.ui_label}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            {catalogView === "composition" ? (
              <div className="space-y-2" data-testid="product-system-composition-list">
                {detailed ? <p className="text-[11px] text-slate-500">Relatia produs -&gt; roluri -&gt; componente/module.</p> : null}
                {searchedCompositionRows.length === 0 ? <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 px-3 py-3 text-[11px] text-slate-500">Nicio compozitie pentru cautarea curenta.</div> : searchedCompositionRows.map(({ template, availability }) => (
                  <div key={template.id} className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
                    <div className="flex flex-wrap items-center justify-between gap-2"><div><p className="font-mono text-[12px] font-bold text-slate-100">{template.template_code}</p><p className="mt-0.5 text-[10px] text-slate-500">{availability.ui_label}</p></div><span className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-[10px] font-bold text-slate-400">{availability.composition_modules.length} module</span></div>
                    {availability.composition_modules.length === 0 ? <div className="mt-3 rounded-lg border border-dashed border-slate-700 bg-slate-950/40 px-3 py-3 text-[11px] text-slate-500">Produsul nu are compozitie expusa in API.</div> : (
                      detailed ? <div className="mt-2 divide-y divide-slate-800 overflow-hidden rounded-lg border border-slate-800">
                        {availability.composition_modules.map((module) => <div key={`${template.template_code}-${module.role_key}-${module.module_template_code}`} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)_auto] gap-2 px-2.5 py-1.5 text-[11px]"><span className="font-bold text-slate-100">{module.role_label}</span><span className="truncate font-mono text-[10px] text-slate-400">{module.module_template_code}</span><span className="whitespace-nowrap rounded-full border border-slate-700 bg-slate-950 px-2 py-0.5 text-[9px] font-bold text-slate-300">{module.status_label ?? (module.is_required ? "Modul intern activ" : "Optional / conditionat")}</span></div>)}
                      </div> : <p className="mt-2 text-[11px] text-slate-300">{availability.composition_modules.map((module) => module.role_label).join(" | ")}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : null}

            {catalogView === "archived" ? (
              <div className="space-y-3" data-testid="product-system-archived-list">
                <p className="text-[11px] text-slate-500">Template-uri scoase din flow activ sau pastrate pentru analiza.</p>
                {searchedArchivedRows.length === 0 ? <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 px-3 py-3 text-[11px] text-slate-500">Nu exista template-uri arhivate sau experimentale in catalogul curent.</div> : <div className="space-y-2">{searchedArchivedRows.map(renderTemplateRow)}</div>}
              </div>
            ) : null}
          </div>
        )}
      </section>
    </div>
  );
}
