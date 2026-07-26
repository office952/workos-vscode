import type {
  IntakeV4ArtworkFinish,
  IntakeV4CncOperationRow,
  IntakeV4LetterGroupFinish,
  IntakeV4MaterialBreakdownResponse,
  IntakeV4MaterialQuantityRow,
} from "./intakeV4Api";
import { formatIntakeV4Quantity } from "./intakeV4QuantityDisplay";
import { sanitizeOperatorDisplayText } from "./intakeV4OperatorUiDisplay";

export type IntakeV4LiveMaterialGroupKey = string;

export interface IntakeV4LiveMaterialUsedRow {
  groupKey: IntakeV4LiveMaterialGroupKey;
  label: string;
  quantityText: string;
  costText: string;
  muted?: boolean;
  technicalDetails?: string[];
}

function positive(value: unknown): number | null {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  return parsed;
}

function readRowQuantity(row: IntakeV4MaterialQuantityRow): number | null {
  return positive(row.base_quantity ?? row.quantity);
}

function readRowPricedQuantity(row: IntakeV4MaterialQuantityRow): number | null {
  return positive(row.priced_quantity ?? row.quantity_with_waste ?? row.quantity ?? row.base_quantity);
}

function resolveMaterialRowCost(row: IntakeV4MaterialQuantityRow): number | null {
  if (row.estimated_cost != null && Number.isFinite(row.estimated_cost)) {
    return row.estimated_cost;
  }
  if (row.material_cost != null && Number.isFinite(row.material_cost)) {
    return row.material_cost;
  }
  const pricedQuantity = readRowPricedQuantity(row);
  if (row.unit_price != null && Number.isFinite(row.unit_price) && row.unit_price > 0 && pricedQuantity != null) {
    return row.unit_price * pricedQuantity;
  }
  return null;
}

function formatMoney(value: number | null | undefined, currency: string): string {
  if (value == null || !Number.isFinite(value)) return "tarif lipsă";
  return `${value.toFixed(2)} ${currency}`;
}

function formatQuantity(
  value: number | null,
  unit: string,
  row: Pick<IntakeV4MaterialQuantityRow, "material_key" | "display_name">,
): string {
  if (value == null || value <= 0) return "cantitate lipsă";
  return formatIntakeV4Quantity(value, unit, {
    materialKey: row.material_key,
    displayName: row.display_name,
  });
}

function dedupeStrings(values: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const trimmed = value?.trim();
    if (!trimmed || seen.has(trimmed)) continue;
    seen.add(trimmed);
    result.push(trimmed);
  }
  return result;
}

function buildTechnicalDetailsFromMaterialRows(rows: IntakeV4MaterialQuantityRow[]): string[] {
  const details = dedupeStrings(
    rows.flatMap((row) => {
      const parts: Array<string | null> = [];
      const sourceLabel = sanitizeOperatorDisplayText(row.display_name);
      if (sourceLabel) parts.push(`Sursă: ${sourceLabel}`);
      if (row.registry_code ?? row.material_code) parts.push(`Cod: ${row.registry_code ?? row.material_code}`);
      if (row.quantity_basis) parts.push(`Bază: ${row.quantity_basis}`);
      return parts;
    }),
  );
  return details;
}

function buildTechnicalDetailsFromOperationRows(rows: IntakeV4CncOperationRow[]): string[] {
  const details = dedupeStrings(
    rows.flatMap((row) => {
      const parts: Array<string | null> = [];
      const sourceLabel = sanitizeOperatorDisplayText(row.display_name);
      if (sourceLabel) parts.push(`Sursă: ${sourceLabel}`);
      if (row.pricing_rate_key) parts.push(`Tarif: ${row.pricing_rate_key}`);
      return parts;
    }),
  );
  return details;
}

function splitRowsByIdentity(rows: IntakeV4MaterialQuantityRow[]): IntakeV4MaterialQuantityRow[][] {
  const groups = new Map<string, IntakeV4MaterialQuantityRow[]>();
  for (const row of rows) {
    const fallbackIdentityCode =
      row.material_key === "return_material" || row.material_key.startsWith("artwork_return_")
        ? "RETURN_PROFILE_SHARED"
        : row.material_key;
    const identityKey = [
      row.registry_code ?? row.material_code ?? fallbackIdentityCode,
      row.unit,
      row.price_source,
      row.unit_price != null ? String(row.unit_price) : "missing",
    ].join("|");
    const existing = groups.get(identityKey) ?? [];
    existing.push(row);
    groups.set(identityKey, existing);
  }
  return Array.from(groups.values());
}

function isPlexiglasFaceRow(row: IntakeV4MaterialQuantityRow): boolean {
  const code = row.registry_code ?? row.material_code ?? "";
  return row.material_key === "plexiglas_face" || code === "MAT-ACP-FATA-LITERE";
}

function sumCost(rows: IntakeV4MaterialQuantityRow[]): number | null {
  let total = 0;
  let hasCost = false;
  for (const row of rows) {
    const cost = resolveMaterialRowCost(row);
    if (cost != null && cost > 0) {
      total += cost;
      hasCost = true;
    }
  }
  return hasCost ? total : null;
}

function sumOperationCost(rows: IntakeV4CncOperationRow[]): number | null {
  let total = 0;
  let hasCost = false;
  for (const row of rows) {
    if (row.estimated_cost != null && Number.isFinite(row.estimated_cost) && row.estimated_cost > 0) {
      total += row.estimated_cost;
      hasCost = true;
    }
  }
  return hasCost ? total : null;
}

function sumQuantity(rows: IntakeV4MaterialQuantityRow[], priced = true): number | null {
  let total = 0;
  let hasQuantity = false;
  for (const row of rows) {
    const qty = priced ? readRowPricedQuantity(row) : readRowQuantity(row);
    if (qty != null) {
      total += qty;
      hasQuantity = true;
    }
  }
  return hasQuantity ? total : null;
}

function addMaterialGroup(
  result: IntakeV4LiveMaterialUsedRow[],
  args: {
    groupKey: string;
    label: string;
    rows: IntakeV4MaterialQuantityRow[];
    currency: string;
    quantity?: number | null;
    unit?: string;
    pricedQuantity?: boolean;
    suffix?: string;
    technicalDetails?: string[];
  },
): void {
  const first = args.rows[0];
  if (!first) return;
  const quantity = args.quantity ?? sumQuantity(args.rows, args.pricedQuantity ?? true);
  const unit = args.unit ?? first.unit;
  const cost = sumCost(args.rows);
  result.push({
    groupKey: args.groupKey,
    label: args.label,
    quantityText: `${formatQuantity(quantity, unit, first)}${args.suffix ?? ""}`,
    costText: formatMoney(cost, args.currency),
    muted: cost == null || args.rows.some((row) => row.price_source === "missing"),
    technicalDetails: args.technicalDetails ?? buildTechnicalDetailsFromMaterialRows(args.rows),
  });
}

function addOperationGroup(
  result: IntakeV4LiveMaterialUsedRow[],
  args: {
    groupKey: string;
    label: string;
    rows: IntakeV4CncOperationRow[];
    currency: string;
  },
): void {
  if (args.rows.length === 0) return;
  const first = args.rows[0]!;
  const quantity = args.rows.reduce((sum, row) => sum + (positive(row.operation_equivalent_quantity) ?? positive(row.quantity) ?? 0), 0);
  const unit = first.operation_equivalent_unit ?? first.unit;
  const cost = sumOperationCost(args.rows);
  result.push({
    groupKey: args.groupKey,
    label: args.label,
    quantityText: quantity > 0 ? formatIntakeV4Quantity(quantity, unit, {
      materialKey: first.material_key ?? first.key,
      displayName: first.display_name,
    }) : "cantitate lipsă",
    costText: cost != null ? formatMoney(cost, args.currency) : "tarif lipsă",
    muted: cost == null || args.rows.some((row) => row.pricing_status === "missing_rate"),
    technicalDetails: buildTechnicalDetailsFromOperationRows(args.rows),
  });
}

function groupRowsByPredicate(
  rows: IntakeV4MaterialQuantityRow[],
  predicate: (row: IntakeV4MaterialQuantityRow) => boolean,
): IntakeV4MaterialQuantityRow[] {
  return rows.filter(predicate);
}

export function buildIntakeV4LiveMaterialsUsedRows(args: {
  breakdown: IntakeV4MaterialBreakdownResponse | null;
  operatorCantPerimeterM?: number | null;
  letterGroups?: IntakeV4LetterGroupFinish[];
  artworkFinishes?: IntakeV4ArtworkFinish[];
  currency?: string;
}): IntakeV4LiveMaterialUsedRow[] {
  const breakdown = args.breakdown;
  if (!breakdown) return [];

  const currency = args.currency ?? breakdown.totals.currency ?? "EUR";
  const materialRows = breakdown.material_rows.filter((row) => !row.material_key.startsWith("nesting_"));
  const consumableRows = breakdown.consumable_rows.filter((row) => row.price_source !== "informational_only");
  const result: IntakeV4LiveMaterialUsedRow[] = [];

  for (const [index, rows] of splitRowsByIdentity(groupRowsByPredicate(materialRows, isPlexiglasFaceRow)).entries()) {
    addMaterialGroup(result, {
      groupKey: index === 0 ? "plexi" : `plexi_${index + 1}`,
      label: "plexiglas 3mm PMMA - opal",
      rows,
      currency,
    });
  }

  addMaterialGroup(result, {
    groupKey: "forex",
    label: "Forex 10 mm",
    rows: groupRowsByPredicate(materialRows, (row) => row.material_key === "forex_backing"),
    currency,
  });

  for (const series of ["641", "651", "8500"]) {
    addMaterialGroup(result, {
      groupKey: `oracal_${series}`,
      label: `Oracal ${series}`,
      rows: groupRowsByPredicate(materialRows, (row) => row.material_key === `face_vinyl_${series}`),
      currency,
    });
  }

  addMaterialGroup(result, {
    groupKey: "oracal_cant_651",
    label: "Oracal 651 / cant volum",
    rows: groupRowsByPredicate(materialRows, (row) => row.material_key === "edge_cant_oracal_651"),
    currency,
  });

  addMaterialGroup(result, {
    groupKey: "ral_paint_spray",
    label: "Vopsea RAL spray / cant volum",
    rows: groupRowsByPredicate(materialRows, (row) => row.material_key === "ral_paint_spray"),
    currency,
  });

  addMaterialGroup(result, {
    groupKey: "print_vinyl",
    label: "Material print Orafol",
    rows: groupRowsByPredicate(materialRows, (row) => row.material_key.endsWith("_print_vinyl")),
    currency,
    pricedQuantity: false,
    suffix: " acoperire",
  });

  addMaterialGroup(result, {
    groupKey: "lamination_material",
    label: "Material laminare Orafol",
    rows: groupRowsByPredicate(materialRows, (row) => row.material_key.endsWith("_laminated_vinyl")),
    currency,
    pricedQuantity: false,
    suffix: " acoperire",
  });

  for (const [index, rows] of splitRowsByIdentity(groupRowsByPredicate(
    materialRows,
    (row) => row.material_key === "return_material" || row.material_key.startsWith("artwork_return_"),
  )).entries()) {
    addMaterialGroup(result, {
      groupKey: index === 0 ? "cant_profile" : `cant_profile_${index + 1}`,
      label: "Cant / volum",
      rows,
      currency,
      pricedQuantity: false,
    });
  }

  addMaterialGroup(result, {
    groupKey: "led_modules",
    label: "Module LED",
    rows: groupRowsByPredicate(consumableRows, (row) => row.material_key === "led_modules"),
    currency,
    pricedQuantity: false,
  });

  addMaterialGroup(result, {
    groupKey: "led_psu",
    label: sanitizeOperatorDisplayText(
      groupRowsByPredicate(consumableRows, (row) => row.material_key === "led_psu")[0]?.display_name ?? "Sursă LED 12V",
    ),
    rows: groupRowsByPredicate(consumableRows, (row) => row.material_key === "led_psu"),
    currency,
    pricedQuantity: false,
  });

  for (const key of [
    "adhesive_return_to_face",
    "adhesive_led_modules",
    "wire_letters_myyup_2x075",
    "wire_supply_myyup_2x15",
    "mounting_accessories_percent",
  ]) {
    const rows = groupRowsByPredicate(consumableRows, (row) => row.material_key === key);
    const first = rows[0];
    addMaterialGroup(result, {
      groupKey: key,
      label: first ? sanitizeOperatorDisplayText(first.display_name) : key,
      rows,
      currency,
      pricedQuantity: false,
    });
  }

  const operationRows = breakdown.operation_rows ?? [];
  addOperationGroup(result, {
    groupKey: "cnc_face",
    label: "Debitare CNC față plexiglas 3mm PMMA - opal",
    rows: operationRows.filter((row) => row.key === "cnc_face_cutting_plexiglas_3mm"),
    currency,
  });
  addOperationGroup(result, {
    groupKey: "cnc_face_bevel",
    label: "Șanfren CNC față plexiglas 3mm PMMA - opal",
    rows: operationRows.filter((row) => row.key === "cnc_face_bevel_plexiglas_3mm"),
    currency,
  });
  addOperationGroup(result, {
    groupKey: "cnc_backing",
    label: "Debitare CNC spate Forex",
    rows: operationRows.filter((row) => row.key === "cnc_backing_cutting_forex_10mm"),
    currency,
  });
  addOperationGroup(result, {
    groupKey: "cnc_backing_bevel",
    label: "CNC sanfren spate Forex",
    rows: operationRows.filter((row) => row.key === "cnc_backing_bevel_forex_10mm"),
    currency,
  });
  addOperationGroup(result, {
    groupKey: "print_service",
    label: "Serviciu print",
    rows: operationRows.filter((row) => row.operation_type === "print_vinyl"),
    currency,
  });
  addOperationGroup(result, {
    groupKey: "lamination_service",
    label: "Serviciu laminare X-PRO",
    rows: operationRows.filter((row) => row.operation_type === "lamination"),
    currency,
  });
  addOperationGroup(result, {
    groupKey: "application_service",
    label: "Serviciu aplicare",
    rows: operationRows.filter(
      (row) => row.operation_type === "vinyl_application" && (row.operation_equivalent_unit ?? row.unit) === "m2",
    ),
    currency,
  });

  const edgeOperationRows = breakdown.edge_cant_operation_rows ?? [];
  addOperationGroup(result, {
    groupKey: "edge_oracal_application",
    label: "Aplicare Oracal cant",
    rows: edgeOperationRows.filter((row) => row.key === "edge_cant_oracal_wrap"),
    currency,
  });
  addOperationGroup(result, {
    groupKey: "edge_bond",
    label: "Lipire cant / volum",
    rows: edgeOperationRows.filter((row) => row.key === "edge_cant_bond_to_face"),
    currency,
  });

  return result.filter((row) => row.quantityText !== "cantitate lipsă" || row.costText !== "tarif lipsă");
}
