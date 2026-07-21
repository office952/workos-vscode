/**
 * Frontend mirror of backend typed pricing catalog contract.
 * Prefer API `typed_catalog` when present; fall back to deterministic code maps.
 */

import type { PricingRegistryItem } from "@/api/pricingRegistry";

export type TypedCatalog =
  | "material"
  | "machine_operation"
  | "labor"
  | "service"
  | "unknown"
  | "markup_rule";

export type TypedCatalogView = "all" | "material" | "machine_operation" | "labor_service";

export const RATE_BASIS_MISMATCH_FLAG = "rate_basis_column_mismatch";

export const RATE_BASIS_MISMATCH_MESSAGE_RO =
  "Valoarea ratei necesită verificare: unitatea declarată nu corespunde câmpului completat.";

const MACHINE_OPERATION_CODES = new Set([
  "CNC_ROUTER",
  "ACM_PANEL_CUTTING",
  "ACM_V_GROOVE",
  "LASER_CUTTING",
  "CONTOUR_CUTTING",
  "PANEL_CUTTING",
  "WC_METAL_FAB",
  "METAL_FAB",
  "RETURN_PROFILE_MACHINE_FORMING",
  "WELDING_BANNER",
]);

const LABOR_CODES = new Set([
  "ACM_BOXED_ASSEMBLY",
  "ASSEMBLY",
  "CAPSARE",
  "ELECTRICAL_WIRING",
  "FACE_VINYL_APPLICATION_LABOR",
  "FINISHING",
  "INSTALL_PREP",
  "LED_ASSEMBLY",
  "PACKAGING",
  "PREPRESS",
  "QC_INSPECTION",
  "RETURN_CANT_RAL_PAINT_LABOR",
  "RETURN_CANT_VINYL_APPLICATION_LABOR",
  "RETURN_PROFILE_FACE_BONDING",
]);

const SERVICE_CODES = new Set([
  "EXTERNAL_SUBCONTRACT",
  "LAMINATION",
  "LARGE_FORMAT_PRINT",
  "PAINTING",
  "SITE_INSTALLATION_STANDARD",
  "VINYL_APPLICATION",
]);

export function classifyWorkcenterTypedCatalog(code: string): TypedCatalog {
  const c = String(code || "").trim().toUpperCase();
  if (!c) return "unknown";
  if (MACHINE_OPERATION_CODES.has(c)) return "machine_operation";
  if (LABOR_CODES.has(c)) return "labor";
  if (SERVICE_CODES.has(c)) return "service";
  if (c.endsWith("_LABOR") || c.includes("LABOR")) return "labor";
  return "unknown";
}

export function resolveTypedCatalog(item: PricingRegistryItem): TypedCatalog {
  if (item.typed_catalog) return item.typed_catalog;
  if (item.pricing_kind === "material") return "material";
  if (item.pricing_kind === "markup_rule") return "markup_rule";
  return classifyWorkcenterTypedCatalog(item.pricing_code);
}

export function resolveMachineFamily(
  item: PricingRegistryItem
): "cnc_mechanical" | "cnc_laser" | "other_machine" | null {
  if (item.machine_family) return item.machine_family;
  const c = item.pricing_code.toUpperCase();
  if (c.includes("LASER") || c === "LASER_CUTTING") return "cnc_laser";
  if (resolveTypedCatalog(item) !== "machine_operation") return null;
  if (
    c.includes("CNC") ||
    c.includes("CUT") ||
    c.includes("GROOVE") ||
    c.includes("ROUTER") ||
    c === "PANEL_CUTTING" ||
    c === "CONTOUR_CUTTING"
  ) {
    return "cnc_mechanical";
  }
  return "other_machine";
}

export function hasRateBasisMismatch(item: PricingRegistryItem): boolean {
  return (item.data_quality_flags ?? []).includes(RATE_BASIS_MISMATCH_FLAG);
}

export function filterByTypedCatalogView(
  items: PricingRegistryItem[],
  view: TypedCatalogView
): PricingRegistryItem[] {
  if (view === "all") return items;
  if (view === "material") {
    return items.filter((i) => resolveTypedCatalog(i) === "material");
  }
  if (view === "machine_operation") {
    return items.filter((i) => resolveTypedCatalog(i) === "machine_operation");
  }
  return items.filter((i) => {
    const t = resolveTypedCatalog(i);
    return t === "labor" || t === "service" || t === "unknown";
  });
}

export function typedCatalogLabelRo(catalog: TypedCatalog): string {
  switch (catalog) {
    case "material":
      return "Material";
    case "machine_operation":
      return "Operație utilaj";
    case "labor":
      return "Manoperă";
    case "service":
      return "Serviciu";
    case "markup_rule":
      return "Adaos";
    case "unknown":
      return "Necesită clasificare";
    default: {
      const _exhaustive: never = catalog;
      return _exhaustive;
    }
  }
}

export function machineFamilyLabelRo(
  family: "cnc_mechanical" | "cnc_laser" | "other_machine" | null
): string | null {
  switch (family) {
    case "cnc_mechanical":
      return "CNC mecanic";
    case "cnc_laser":
      return "CNC laser";
    case "other_machine":
      return "Alt utilaj";
    case null:
      return null;
    default: {
      const _exhaustive: never = family;
      return _exhaustive;
    }
  }
}
