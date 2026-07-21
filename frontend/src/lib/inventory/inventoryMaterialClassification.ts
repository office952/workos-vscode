/**
 * Live inventory classification — category/unit based (no mock IDs).
 */

export type InventoryUiTabCategory = "placi" | "role" | "cerneala" | "altele";

export type InventoryStockStatus =
  | "ok"
  | "low"
  | "critical"
  | "out_of_stock"
  | "untracked";

const PLATE_CATEGORIES = new Set([
  "panou_compozit",
  "plexiglas",
  "forex",
  "placi",
  "plăci",
  "placa",
  "placă",
]);

const ROLL_CATEGORIES = new Set([
  "vinyl",
  "banner",
  "mesh",
  "laminare",
  "consumabile_print",
  "rola",
  "rolă",
  "role",
]);

const INK_CATEGORIES = new Set(["cerneala", "cerneală", "ink"]);

/** Normalize raw inventory category for tab membership. */
export function normalizeInventoryCategoryKey(category: string | null | undefined): string {
  return String(category ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "");
}

/**
 * Classify a live material into Inventory UI tabs using category (+ light unit hints).
 * Unknown → altele. Never uses mock MAT-00x IDs.
 */
export function classifyInventoryUiTab(args: {
  category: string | null | undefined;
  unit?: string | null | undefined;
  code?: string | null | undefined;
}): InventoryUiTabCategory {
  const cat = normalizeInventoryCategoryKey(args.category);
  const unit = String(args.unit ?? "")
    .trim()
    .toLowerCase();
  const code = String(args.code ?? "")
    .trim()
    .toUpperCase();

  if (INK_CATEGORIES.has(cat) || (cat.includes("consumabile") && unit === "litru")) {
    return "cerneala";
  }
  if (code.startsWith("MAT-INK") || code.includes("-INK-")) {
    return "cerneala";
  }
  if (PLATE_CATEGORIES.has(cat) || cat.includes("panou") || cat.includes("plexiglas") || cat.includes("forex")) {
    return "placi";
  }
  if (
    ROLL_CATEGORIES.has(cat) ||
    cat.includes("vinyl") ||
    cat.includes("banner") ||
    cat.includes("mesh") ||
    cat.includes("lamin")
  ) {
    return "role";
  }
  return "altele";
}

export function computeInventoryStockStatus(args: {
  stockCurrent: number | null | undefined;
  stockMin: number | null | undefined;
}): InventoryStockStatus {
  if (args.stockCurrent === null || args.stockCurrent === undefined) {
    return "untracked";
  }
  const current = Number(args.stockCurrent);
  const min = Number(args.stockMin ?? 0);
  if (!Number.isFinite(current) || current <= 0) return "out_of_stock";
  if (Number.isFinite(min) && min > 0) {
    if (current <= min * 0.5) return "critical";
    if (current <= min) return "low";
  }
  return "ok";
}

export function stockStatusLabelRo(status: InventoryStockStatus): string {
  switch (status) {
    case "ok":
      return "În stoc";
    case "low":
      return "Scăzut";
    case "critical":
      return "Critic";
    case "out_of_stock":
      return "Epuizat";
    case "untracked":
      return "Stoc neurmărit";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

export function formatStockQuantity(
  stockCurrent: number | null | undefined,
  unit: string
): string {
  if (stockCurrent === null || stockCurrent === undefined) {
    return `— ${unit}`.trim();
  }
  return `${stockCurrent} ${unit}`.trim();
}
