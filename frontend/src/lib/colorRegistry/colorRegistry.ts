import { ORACAL_651_REGISTRY } from "./oracal651";
import { ORACAL_8500_REGISTRY } from "./oracal8500";
import { RAL_COLOR_REGISTRY } from "./ralColors";
import type {
  ColorRegistryItem,
  ColorRegistrySystem,
  ColorUsageScope,
  OracalSeries,
} from "./colorRegistryTypes";

export const ALL_COLOR_REGISTRY_ITEMS: ColorRegistryItem[] = [
  ...RAL_COLOR_REGISTRY,
  ...ORACAL_651_REGISTRY,
  ...ORACAL_8500_REGISTRY,
];

export type ColorRegistryFilter = {
  system?: ColorRegistrySystem;
  series?: OracalSeries;
  usageScope?: ColorUsageScope;
  activeOnly?: boolean;
};

export function filterColorRegistry(
  items: ColorRegistryItem[],
  filter: ColorRegistryFilter
): ColorRegistryItem[] {
  const activeOnly = filter.activeOnly !== false;
  return items.filter((item) => {
    if (activeOnly && !item.active) return false;
    if (filter.system && item.system !== filter.system) return false;
    if (filter.series && item.series !== filter.series) return false;
    if (filter.usageScope && !item.usageScope.includes(filter.usageScope)) return false;
    return true;
  });
}

export function searchColorRegistry(
  items: ColorRegistryItem[],
  query: string
): ColorRegistryItem[] {
  const q = query.trim().toLowerCase();
  if (!q) return items;
  return items.filter((item) => {
    const haystack = [
      item.code,
      item.name,
      item.romanianName,
      item.system,
      item.series,
      item.brand,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystack.includes(q) || `ral ${item.code}`.includes(q) || `651-${item.code}`.includes(q);
  });
}

export function normalizeColorRegistryCode(
  system: ColorRegistrySystem,
  code: string,
  series?: OracalSeries
): string {
  let normalized = code.trim();
  if (!normalized) return normalized;

  if (system === "RAL") {
    normalized = normalized.replace(/^ral[\s-]*/i, "").replace(/\s+/g, "");
    return normalized;
  }

  normalized = normalized.replace(/^oracal[\s-]*/i, "");
  if (series) {
    normalized = normalized.replace(new RegExp(`^${series}[\\s-]*`, "i"), "");
  } else {
    normalized = normalized.replace(/^(651|8500)[\s-]*/i, "");
  }
  return normalized;
}

export function findColorRegistryItem(
  system: ColorRegistrySystem,
  code: string,
  series?: OracalSeries
): ColorRegistryItem | undefined {
  const normalizedCode = normalizeColorRegistryCode(system, code, series);
  return ALL_COLOR_REGISTRY_ITEMS.find(
    (item) =>
      item.system === system &&
      item.code === normalizedCode &&
      (series == null || item.series === series)
  );
}

export type ColorRegistryLookupResult =
  | { status: "found"; item: ColorRegistryItem }
  | { status: "unknown"; normalizedCode: string; system: ColorRegistrySystem; series?: OracalSeries };

export function lookupColorRegistryItem(
  system: ColorRegistrySystem,
  code: string,
  series?: OracalSeries
): ColorRegistryLookupResult {
  const normalizedCode = normalizeColorRegistryCode(system, code, series);
  const item = findColorRegistryItem(system, normalizedCode, series);
  if (item) {
    return { status: "found", item };
  }
  return { status: "unknown", normalizedCode, system, series };
}

export function formatColorRegistryLabel(item: ColorRegistryItem): string {
  if (item.system === "RAL") {
    return `RAL ${item.code} — ${item.name}${item.romanianName ? ` / ${item.romanianName}` : ""}`;
  }
  return `Oracal ${item.series}-${item.code} — ${item.name}${item.translucent ? " (translucent)" : ""}`;
}
