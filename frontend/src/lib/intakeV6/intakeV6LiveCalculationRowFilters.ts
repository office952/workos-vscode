import type { IntakeV6LiveMaterialUsedRow } from "./intakeV6LiveMaterialsUsedDisplay";



export type LiveCalcFilterId =

  | "all"

  | "materials"

  | "services_operations"

  | "labor"

  | "missing_rates";



export const LIVE_CALC_BASE_FILTER_OPTIONS: ReadonlyArray<{ id: LiveCalcFilterId; label: string }> = [

  { id: "all", label: "Toate" },

  { id: "materials", label: "Materiale" },

  { id: "services_operations", label: "Servicii / Operații" },

  { id: "labor", label: "Manoperă" },

];



export const LIVE_CALC_MISSING_RATES_FILTER = {

  id: "missing_rates" as const,

  label: "Fără tarif",

};



/** @deprecated use resolveLiveCalcFilterOptions */

export const LIVE_CALC_FILTER_OPTIONS = [

  ...LIVE_CALC_BASE_FILTER_OPTIONS,

  LIVE_CALC_MISSING_RATES_FILTER,

] as const;



const OPERATION_KEYS = new Set([

  "cnc_face",

  "cnc_face_bevel",

  "cnc_backing",

  "print_service",

  "lamination_service",

  "application_service",

  "edge_oracal_application",

  "service.cnc_face",

  "service.cnc_face_bevel",

  "service.cnc_back",

  "service.print",

  "service.lamination",

  "service.application",

]);



const LABOR_KEYS = new Set([

  "edge_bond",

  "labor.cant_glue",

]);



const MATERIAL_KEYS = new Set([

  "plexi",

  "plexi_letters",

  "plexi_emblems",

  "forex",

  "oracal_641",

  "oracal_651",

  "oracal_8500",

  "oracal_cant_651",

  "ral_paint_spray",

  "print_vinyl",

  "lamination_material",

  "cant_letters",

  "cant_emblems",

  "led_modules",

  "led_psu",

  "adhesive_return_to_face",

  "adhesive_led_modules",

  "wire_letters_myyup_2x075",

  "wire_supply_myyup_2x15",

  "mounting_accessories_percent",

  "material.plexiglas_face",

  "material.logo_plexiglas_face",

  "material.forex_backing",

  "material.face_oracal",

  "material.print",

  "material.lamination",

  "material.return_profile",

  "material.led_modules",

  "material.led_psu",

  "material.adhesive_cant",

  "material.adhesive_led",

  "material.wire_letters",

  "material.wire_supply",

  "material.mounting_accessories",

]);



function isMaterialRow(groupKey: string): boolean {

  return MATERIAL_KEYS.has(groupKey);

}



export function rowHasMissingRate(row: IntakeV6LiveMaterialUsedRow): boolean {

  return row.muted === true || row.costText === "tarif lipsă";

}



export function resolveLiveCalcFilterOptions(

  rows: IntakeV6LiveMaterialUsedRow[],

): ReadonlyArray<{ id: LiveCalcFilterId; label: string }> {

  const hasMissingRates = rows.some(rowHasMissingRate);

  if (!hasMissingRates) return LIVE_CALC_BASE_FILTER_OPTIONS;

  return [...LIVE_CALC_BASE_FILTER_OPTIONS, LIVE_CALC_MISSING_RATES_FILTER];

}



/** Parse numeric cost from display text like "32.00 EUR". Returns null for missing rates. */

export function parseLiveCalcRowCost(costText: string): number | null {

  if (costText === "tarif lipsă" || !costText.trim()) return null;

  const match = costText.match(/^([\d.,]+)/);

  if (!match) return null;

  const normalized = match[1].replace(",", ".");

  const parsed = Number(normalized);

  return Number.isFinite(parsed) ? parsed : null;

}



export function sumFilteredLiveCalcRows(

  rows: IntakeV6LiveMaterialUsedRow[],

): { subtotal: number; pricedLineCount: number; lineCount: number } {

  let subtotal = 0;

  let pricedLineCount = 0;

  for (const row of rows) {

    const cost = parseLiveCalcRowCost(row.costText);

    if (cost != null) {

      subtotal += cost;

      pricedLineCount += 1;

    }

  }

  return { subtotal, pricedLineCount, lineCount: rows.length };

}



export function liveCalcRowMatchesFilter(

  row: IntakeV6LiveMaterialUsedRow,

  filter: LiveCalcFilterId,

): boolean {

  if (filter === "all") return true;

  const key = row.groupKey;

  if (filter === "missing_rates") return rowHasMissingRate(row);

  if (filter === "services_operations") return OPERATION_KEYS.has(key);

  if (filter === "labor") return LABOR_KEYS.has(key);

  if (filter === "materials") return isMaterialRow(key);

  return true;

}



export function filterLiveCalcRows(

  rows: IntakeV6LiveMaterialUsedRow[],

  activeFilter: LiveCalcFilterId,

): IntakeV6LiveMaterialUsedRow[] {

  if (activeFilter === "all") return rows;

  return rows.filter((row) => liveCalcRowMatchesFilter(row, activeFilter));

}

