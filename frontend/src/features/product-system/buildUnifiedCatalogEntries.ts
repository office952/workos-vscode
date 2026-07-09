import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import {
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
} from "@/lib/productTemplateScopePresentation";
import {
  COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES,
  assessComponentFirstContractDrift,
  normalizeComponentFirstTemplateCode,
} from "./componentFirstReadonlyCompleteness";
import { buildComponentFirstReadonlySetModel } from "./componentFirstReadonlySetModel";
import {
  UNIFIED_CATALOG_BUCKETS,
  type UnifiedCatalogBucketGroup,
  type UnifiedCatalogBucketId,
  type UnifiedCatalogEntry,
} from "./productSystemUnifiedCatalogTypes";

const CANDIDATE_SET_ENTRY_ID = "candidate-set:component-first-letters";

function normalizeCode(code: string): string {
  return code.trim().toUpperCase();
}

function isComponentFirstCatalogCode(code: string): boolean {
  return COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES.some(
    (expected) => normalizeComponentFirstTemplateCode(expected) === normalizeComponentFirstTemplateCode(code),
  );
}

function isLegacyModuleTemplateCode(code: string): boolean {
  const normalized = normalizeCode(code);
  if (normalized === normalizeCode(LETTERS_TEMPLATE_CODE)) return false;
  if (normalized === normalizeCode(LOGO_TEMPLATE_CODE)) return false;
  return /^(TPL-VOLUMETRIC-|TPL-VOLUM-|TPL-METAL-)/.test(normalized);
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

function assignCatalogBucket(
  kind: UnifiedCatalogEntry["kind"],
  templateCode: string,
  availability: ProductTemplateAvailabilityItem,
): UnifiedCatalogBucketId {
  if (kind === "candidate-set") {
    return "component-first-sets";
  }

  const code = normalizeCode(templateCode);

  if (availability.display_group === "archived_experimental") {
    return "archived";
  }

  if (
    code === normalizeCode(LETTERS_TEMPLATE_CODE) ||
    (availability.quote_offerable && availability.product_system_role === "offerable_product") ||
    (availability.quote_offerable && availability.display_group === "active_products")
  ) {
    return "current-products";
  }

  if (
    code === normalizeCode(LOGO_TEMPLATE_CODE) ||
    availability.product_system_role === "candidate_product" ||
    availability.display_group === "candidate_products"
  ) {
    return "candidate-products";
  }

  if (
    availability.product_system_role === "internal_module" ||
    availability.product_system_role === "shared_component" ||
    availability.display_group === "internal_modules" ||
    availability.display_group === "shared_components" ||
    isLegacyModuleTemplateCode(code)
  ) {
    return "legacy-shared-modules";
  }

  if (availability.quote_offerable) {
    return "current-products";
  }

  return "legacy-shared-modules";
}

function enrichEntryPresentation(
  entry: UnifiedCatalogEntry,
  availability: ProductTemplateAvailabilityItem,
): UnifiedCatalogEntry {
  const code = normalizeCode(entry.templateCode);

  if (entry.kind === "candidate-set") {
    return {
      ...entry,
      entityType: "Component-first candidate set",
      lifecycleLabel: "Product Composer · Readonly · NOT OFFERABLE",
      metadata:
        "Product Composer + 6 Component Templates · readonly contract · no Work Intake / Pricing / Quote",
    };
  }

  if (code === normalizeCode(LETTERS_TEMPLATE_CODE)) {
    return {
      ...entry,
      entityType: "Current active root",
      lifecycleLabel: "Used today · Offerable · Work Intake: yes",
      metadata:
        availability.ui_description ||
        "Current production root for volumetric letters. Separate from component-first candidate set.",
    };
  }

  if (code === normalizeCode(LOGO_TEMPLATE_CODE)) {
    return {
      ...entry,
      entityType: "Candidate product",
      lifecycleLabel: "Not Work Intake · Requires owner GO · Linked/analyzer only",
      metadata:
        availability.ui_description ||
        "Logo volumetric candidate — linked/analyzer composition only. No direct root / no Logo activation.",
    };
  }

  if (entry.bucket === "legacy-shared-modules") {
    const parents =
      availability.parent_product_codes.length > 0
        ? availability.parent_product_codes.join(", ")
        : availability.parent_codes.join(", ") || "parent product";
    return {
      ...entry,
      entityType: "Legacy internal module",
      lifecycleLabel: "Used by parent product",
      metadata: `Legacy shared module contract · Used by ${parents} · Not component-first TPL-COMP-*`,
    };
  }

  if (entry.bucket === "archived") {
    return {
      ...entry,
      entityType: "Archived template",
      lifecycleLabel: "Archived / experimental",
      metadata: availability.ui_description || availability.readiness_reason || "",
    };
  }

  return entry;
}

function templateEntry(
  template: ProductTemplateEntity,
  availability: ProductTemplateAvailabilityItem,
): UnifiedCatalogEntry {
  const bucket = assignCatalogBucket("template", template.template_code, availability);
  const isProduct =
    bucket === "current-products" || bucket === "candidate-products";
  const isComponent = bucket === "legacy-shared-modules";
  const isArchived = bucket === "archived";
  const isActiveRoot = bucket === "current-products";
  const isBlocked = Boolean(availability.owner_decision_required);

  const base: UnifiedCatalogEntry = {
    id: `template:${template.id}`,
    kind: "template",
    bucket,
    name: template.family_name || template.template_code,
    templateCode: template.template_code,
    entityType: "",
    lifecycleLabel: "",
    metadata: "",
    importanceRank: availability.importance_rank ?? 50,
    isProduct,
    isComponent,
    isCandidateReadonly: false,
    isActiveRoot,
    isArchived,
    isBlocked,
    isReadonly: bucket === "legacy-shared-modules",
    template,
    availability,
  };

  return enrichEntryPresentation(base, availability);
}

function candidateSetEntry(liveRowCount: number, expectedRowCount: number): UnifiedCatalogEntry {
  const base: UnifiedCatalogEntry = {
    id: CANDIDATE_SET_ENTRY_ID,
    kind: "candidate-set",
    bucket: "component-first-sets",
    name: "Component-first Letters Candidate",
    templateCode: COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
    entityType: "Component-first candidate set",
    lifecycleLabel: "Product Composer · Readonly · NOT OFFERABLE",
    metadata: `Product Composer + 6 Component Templates · ${liveRowCount}/${expectedRowCount} live rows · no Work Intake`,
    importanceRank: 15,
    isProduct: false,
    isComponent: false,
    isCandidateReadonly: true,
    isActiveRoot: false,
    isArchived: false,
    isBlocked: true,
    isReadonly: true,
  };

  return enrichEntryPresentation(
    base,
    fallbackAvailability({
      id: 0,
      template_code: COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
      active: false,
      components_json: "[]",
      operations_json: "[]",
      required_materials_json: "[]",
    }),
  );
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
  const candidateModel = buildComponentFirstReadonlySetModel(
    templates,
    availabilityItems,
    COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  );

  const templateEntries = templates
    .filter((template) => !candidateModel || !isComponentFirstCatalogCode(template.template_code))
    .map((template) => {
      const availability =
        availabilityByCode.get(normalizeCode(template.template_code)) ?? fallbackAvailability(template);
      return templateEntry(template, availability);
    });

  const entries: UnifiedCatalogEntry[] = [...templateEntries];
  if (candidateModel) {
    const drift = assessComponentFirstContractDrift(templates);
    entries.push(
      candidateSetEntry(drift.completeness.foundRowCount, drift.completeness.expectedRowCount),
    );
  }

  return entries.sort((a, b) => {
    const bucketOrder =
      UNIFIED_CATALOG_BUCKETS.find((bucket) => bucket.id === a.bucket)!.order -
      UNIFIED_CATALOG_BUCKETS.find((bucket) => bucket.id === b.bucket)!.order;
    if (bucketOrder !== 0) return bucketOrder;
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
    if (filter === "current-products" && entry.bucket !== "current-products") return false;
    if (filter === "candidate-products" && entry.bucket !== "candidate-products") return false;
    if (filter === "component-first-sets" && entry.bucket !== "component-first-sets") return false;
    if (filter === "legacy-modules" && entry.bucket !== "legacy-shared-modules") return false;
    if (filter === "archived" && entry.bucket !== "archived") return false;
    if (filter === "blocked" && !entry.isBlocked) return false;

    if (!q) return true;
    const haystack = [
      entry.name,
      entry.templateCode,
      entry.entityType,
      entry.lifecycleLabel,
      entry.metadata,
      entry.bucket,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
}

export function groupUnifiedCatalogEntriesByBucket(
  entries: UnifiedCatalogEntry[],
): UnifiedCatalogBucketGroup[] {
  return UNIFIED_CATALOG_BUCKETS.map((bucket) => ({
    bucket,
    entries: entries.filter((entry) => entry.bucket === bucket.id),
  })).filter((group) => group.entries.length > 0);
}

export { CANDIDATE_SET_ENTRY_ID };
