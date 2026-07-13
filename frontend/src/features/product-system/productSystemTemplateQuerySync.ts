import type { ProductTemplateAvailabilityItem } from "@/lib/api";
import { normalizeTemplateCode } from "@/lib/activeTemplateScope";
import type { UnifiedCatalogEntry } from "./productSystemUnifiedCatalogTypes";

export const PRODUCT_SYSTEM_TEMPLATE_QUERY_PARAM = "template";

export const TEMPLATE_UNAVAILABLE_MESSAGE =
  "Template indisponibil sau inexistent";

export type TemplateQueryResolution =
  | { kind: "none" }
  | {
      kind: "matched";
      entryId: string;
      templateCode: string;
      bucket: UnifiedCatalogEntry["bucket"];
    }
  | {
      kind: "unavailable";
      templateCode: string;
      reason: "archived" | "inactive" | "not_in_catalog" | "unknown";
    };

export function parseRequestedTemplateCode(
  raw: string | null | undefined,
): string | null {
  const normalized = normalizeTemplateCode(raw);
  return normalized.length > 0 ? normalized : null;
}

export function findCatalogEntryByTemplateCode(
  entries: UnifiedCatalogEntry[],
  templateCode: string,
): UnifiedCatalogEntry | null {
  const normalized = normalizeTemplateCode(templateCode);
  return (
    entries.find(
      (entry) =>
        entry.kind === "template" &&
        normalizeTemplateCode(entry.templateCode) === normalized,
    ) ?? null
  );
}

function availabilityForCode(
  availabilityItems: ProductTemplateAvailabilityItem[],
  templateCode: string,
): ProductTemplateAvailabilityItem | undefined {
  const normalized = normalizeTemplateCode(templateCode);
  return availabilityItems.find(
    (item) => normalizeTemplateCode(item.template_code) === normalized,
  );
}

function isDeepLinkCatalogEntry(entry: UnifiedCatalogEntry): boolean {
  return entry.kind === "template";
}

export function resolveTemplateQuerySelection(
  requestedCode: string | null | undefined,
  entries: UnifiedCatalogEntry[],
  availabilityItems: ProductTemplateAvailabilityItem[],
): TemplateQueryResolution {
  const normalized = parseRequestedTemplateCode(requestedCode);
  if (!normalized) {
    return { kind: "none" };
  }

  const entry = findCatalogEntryByTemplateCode(entries, normalized);
  const availability = availabilityForCode(availabilityItems, normalized);

  if (entry && isDeepLinkCatalogEntry(entry)) {
    if (
      availability &&
      (availability.display_group === "archived_experimental" ||
        availability.status === "archived" ||
        availability.db_active === false)
    ) {
      return {
        kind: "unavailable",
        templateCode: availability.template_code,
        reason: availability.db_active === false ? "inactive" : "archived",
      };
    }

    return {
      kind: "matched",
      entryId: entry.id,
      templateCode: entry.templateCode,
      bucket: entry.bucket,
    };
  }

  if (availability) {
    if (
      availability.display_group === "archived_experimental" ||
      availability.status === "archived" ||
      availability.db_active === false
    ) {
      return {
        kind: "unavailable",
        templateCode: availability.template_code,
        reason: availability.db_active === false ? "inactive" : "archived",
      };
    }
  }

  return {
    kind: "unavailable",
    templateCode: normalized,
    reason: availability ? "not_in_catalog" : "unknown",
  };
}

export function buildProductSystemTemplateQuery(code: string): string {
  return `${PRODUCT_SYSTEM_TEMPLATE_QUERY_PARAM}=${encodeURIComponent(code)}`;
}

export function selectedTemplateCodeFromEntry(
  entry: UnifiedCatalogEntry | null,
): string | null {
  if (!entry || entry.kind !== "template") return null;
  return entry.templateCode;
}
