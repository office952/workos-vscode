import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import {
  COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES,
  normalizeComponentFirstTemplateCode,
} from "./componentFirstReadonlyCompleteness";
import { buildComponentFirstReadonlySetModel } from "./componentFirstReadonlySetModel";
import type { UnifiedCatalogEntry } from "./productSystemUnifiedCatalogTypes";

const CANDIDATE_SET_ENTRY_ID = "candidate-set:component-first-letters";

function normalizeCode(code: string): string {
  return code.trim().toUpperCase();
}

function isComponentFirstCatalogCode(code: string): boolean {
  return COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES.some(
    (expected) => normalizeComponentFirstTemplateCode(expected) === normalizeComponentFirstTemplateCode(code),
  );
}

function fallbackAvailability(template: ProductTemplateEntity): ProductTemplateAvailabilityItem {
  return {
    template_id: template.id,
    template_code: template.template_code,
    family_id: template.family_id ?? null,
    family_name: template.family_name ?? null,
    description: template.description ?? null,
    db_active: template.active !== false,
    quote_offerable: false,
    runtime_module: false,
    is_parent: false,
    has_modules: false,
    parent_codes: [],
    module_codes: [],
    status: "not_offerable",
    status_reason: "availability_unavailable",
    product_system_role: "archived_experimental",
    display_group: "archived_experimental",
    importance_rank: 50,
    owner_decision_required: false,
    readiness_reason: "",
    ui_label: "Unknown",
    ui_description: "",
    parent_product_codes: [],
    child_module_codes: [],
    shared_with_product_codes: [],
    composition_modules: [],
    shared_component_contracts: [],
  };
}

function entityTypeLabel(availability: ProductTemplateAvailabilityItem): string {
  switch (availability.product_system_role) {
    case "offerable_product":
      return "Product";
    case "candidate_product":
      return "Product candidate";
    case "internal_module":
      return "Component module";
    case "shared_component":
      return "Shared component";
    default:
      return "Template";
  }
}

function lifecycleLabel(availability: ProductTemplateAvailabilityItem, template: ProductTemplateEntity): string {
  if (availability.display_group === "archived_experimental") {
    return "Archived";
  }
  if (availability.quote_offerable) {
    return "Active root · Offerable";
  }
  if (availability.product_system_role === "candidate_product") {
    return "Candidate product";
  }
  if (template.active === false) {
    return "Inactive";
  }
  return availability.ui_label || "Catalog entry";
}

function templateEntry(
  template: ProductTemplateEntity,
  availability: ProductTemplateAvailabilityItem,
): UnifiedCatalogEntry {
  const isProduct =
    availability.product_system_role === "offerable_product" ||
    availability.product_system_role === "candidate_product";
  const isComponent =
    availability.product_system_role === "internal_module" ||
    availability.product_system_role === "shared_component";
  const isArchived = availability.display_group === "archived_experimental";
  const isActiveRoot =
    availability.quote_offerable || availability.display_group === "active_products";
  const isBlocked = Boolean(availability.owner_decision_required);

  return {
    id: `template:${template.id}`,
    kind: "template",
    name: template.family_name || template.template_code,
    templateCode: template.template_code,
    entityType: entityTypeLabel(availability),
    lifecycleLabel: lifecycleLabel(availability, template),
    metadata: availability.ui_description || availability.readiness_reason || "",
    importanceRank: availability.importance_rank ?? 50,
    isProduct,
    isComponent,
    isCandidateReadonly: false,
    isActiveRoot,
    isArchived,
    isBlocked,
    isReadonly: false,
    template,
    availability,
  };
}

function candidateSetEntry(): UnifiedCatalogEntry {
  return {
    id: CANDIDATE_SET_ENTRY_ID,
    kind: "candidate-set",
    name: "Component-first Letters Candidate",
    templateCode: COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
    entityType: "Candidate set",
    lifecycleLabel: "Candidate readonly · NOT OFFERABLE",
    metadata: "1 Product Composer + 6 Component Templates · inactive · no Work Intake",
    importanceRank: 15,
    isProduct: false,
    isComponent: false,
    isCandidateReadonly: true,
    isActiveRoot: false,
    isArchived: false,
    isBlocked: true,
    isReadonly: true,
  };
}

export function buildUnifiedCatalogEntries({
  templates,
  availabilityItems,
}: {
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
}): UnifiedCatalogEntry[] {
  const availabilityByCode = new Map(
    availabilityItems.map((item) => [normalizeCode(item.template_code), item]),
  );
  const hasCandidateModel = buildComponentFirstReadonlySetModel(
    templates,
    availabilityItems,
    COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  );

  const templateEntries = templates
    .filter((template) => !hasCandidateModel || !isComponentFirstCatalogCode(template.template_code))
    .map((template) => {
      const availability =
        availabilityByCode.get(normalizeCode(template.template_code)) ?? fallbackAvailability(template);
      return templateEntry(template, availability);
    });

  const entries: UnifiedCatalogEntry[] = [...templateEntries];
  if (hasCandidateModel) {
    entries.push(candidateSetEntry());
  }

  return entries.sort((a, b) => {
    const rank = a.importanceRank - b.importanceRank;
    if (rank !== 0) return rank;
    return a.templateCode.localeCompare(b.templateCode);
  });
}

export function filterUnifiedCatalogEntries({
  entries,
  filter,
  search,
}: {
  entries: UnifiedCatalogEntry[];
  filter: import("./productSystemUnifiedCatalogTypes").UnifiedCatalogFilter;
  search: string;
}): UnifiedCatalogEntry[] {
  const q = search.trim().toLowerCase();
  return entries.filter((entry) => {
    if (filter === "products" && !entry.isProduct) return false;
    if (filter === "components" && !entry.isComponent) return false;
    if (filter === "candidate-sets" && entry.kind !== "candidate-set") return false;
    if (filter === "active-roots" && !entry.isActiveRoot) return false;
    if (filter === "readonly" && !entry.isReadonly && !entry.isCandidateReadonly) return false;
    if (filter === "blocked" && !entry.isBlocked) return false;
    if (filter === "archived" && !entry.isArchived) return false;

    if (!q) return true;
    const haystack = [
      entry.name,
      entry.templateCode,
      entry.entityType,
      entry.lifecycleLabel,
      entry.metadata,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
}

export { CANDIDATE_SET_ENTRY_ID };
