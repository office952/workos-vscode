/**
 * Operator-facing labels, units, and warning grouping for Intake V4 — display only.
 */

import type { IntakeV4CncOperationRow, IntakeV4MaterialBreakdownResponse } from "./intakeV4Api";

const PRINT_OPERATION_TYPES = new Set(["print_vinyl", "lamination", "vinyl_application"]);

const ADHESIVE_MATERIAL_KEY_HINTS = ["adhesive", "adeziv"];

const POSITIONAL_LOGO_PATTERN = /logo(?:\s|_|-)*(?:stanga|dreapta|centru|center|middle|left|right|sus|jos|top|bottom)/i;

type OperatorLayerIdentity = {
  id?: string | null;
  name?: string | null;
  layerKey?: string | null;
  layerName?: string | null;
};

function normalizeOperatorLayerToken(value: string | null | undefined): string {
  return String(value ?? "").trim().toLowerCase().replace(/[_-]+/g, " ");
}

function setLogoLabelToken(
  target: Map<string, string>,
  value: string | null | undefined,
  label: string,
): void {
  const normalized = normalizeOperatorLayerToken(value);
  if (!normalized) return;
  target.set(normalized, label);
}

export function isPositionalLogoLayer(
  layerId: string | null | undefined,
  layerName?: string | null,
): boolean {
  const id = normalizeOperatorLayerToken(layerId);
  const name = normalizeOperatorLayerToken(layerName);
  return POSITIONAL_LOGO_PATTERN.test(id) || POSITIONAL_LOGO_PATTERN.test(name);
}

export function buildOperatorLogoLabelMap(
  layers: OperatorLayerIdentity[],
): Map<string, string> {
  const labelMap = new Map<string, string>();
  let logoIndex = 0;

  for (const layer of layers) {
    if (!isPositionalLogoLayer(layer.id ?? layer.layerKey, layer.name ?? layer.layerName)) {
      continue;
    }
    logoIndex += 1;
    const label = `Logo ${logoIndex}`;
    setLogoLabelToken(labelMap, layer.id, label);
    setLogoLabelToken(labelMap, layer.name, label);
    setLogoLabelToken(labelMap, layer.layerKey, label);
    setLogoLabelToken(labelMap, layer.layerName, label);
  }

  return labelMap;
}

export function isInternalCorelLayerId(value: string | null | undefined): boolean {
  const token = String(value ?? "").trim();
  return /^_\d+$/.test(token) || /^_220\d+/.test(token);
}

export function getOperatorLayerLabel(
  layerId: string,
  layerName?: string | null,
  options?: { logoLabelMap?: ReadonlyMap<string, string> },
): string {
  const id = layerId.trim().toLowerCase();
  const name = String(layerName ?? "").trim().toLowerCase();
  const explicitLogoLabel =
    options?.logoLabelMap?.get(normalizeOperatorLayerToken(layerId)) ??
    options?.logoLabelMap?.get(normalizeOperatorLayerToken(layerName));

  if (explicitLogoLabel) {
    return explicitLogoLabel;
  }

  if (isPositionalLogoLayer(layerId, layerName)) {
    return "Logo";
  }
  if (name && !isInternalCorelLayerId(name)) {
    return layerName!.trim();
  }
  if (!isInternalCorelLayerId(layerId) && layerId.trim()) {
    return layerId.trim();
  }
  if (/logo|emblem|artwork|policromie/.test(name)) {
    return name.replace(/_/g, " ");
  }
  return "artwork layer";
}

export function sanitizeOperatorDisplayText(text: string): string {
  return text.replace(/_\d{10,}/g, (match) => getOperatorLayerLabel(match, match));
}

export function formatOperatorOperationDisplayName(displayName: string): string {
  return sanitizeOperatorDisplayText(displayName);
}

export type IntakeV4LinearQuantityContext =
  | "cnc"
  | "cant"
  | "cable"
  | "adhesive"
  | "machine_pass"
  | "generic";

export function isAdhesiveQuantityUnit(materialKey?: string | null, displayName?: string | null): boolean {
  const haystack = `${materialKey ?? ""} ${displayName ?? ""}`.toLowerCase();
  return ADHESIVE_MATERIAL_KEY_HINTS.some((hint) => haystack.includes(hint));
}

/** Backend sometimes sends linear meters as unit `ml`; operator UI must not confuse with milliliters. */
export function formatIntakeV4LinearQuantityDisplay(
  value: number,
  unit: string,
  context: IntakeV4LinearQuantityContext,
  options?: { materialKey?: string | null; displayName?: string | null },
): string {
  const rounded = Number.isFinite(value) ? value : 0;
  const token = unit.trim().toLowerCase();

  if (context === "machine_pass") {
    return `${rounded.toFixed(2)} m-pass`;
  }

  if (
    context === "adhesive" ||
    (token === "ml" && isAdhesiveQuantityUnit(options?.materialKey, options?.displayName))
  ) {
    return `${rounded.toFixed(2)} ml`;
  }

  if (token === "m2") {
    return `${rounded.toFixed(3)} m²`;
  }

  if (token === "m" || token === "linear_meter" || token === "ml") {
    if (context === "cnc" || context === "cant" || context === "cable" || token === "ml") {
      return `${rounded.toFixed(2)} m`;
    }
  }

  if (token === "w") {
    return `${rounded.toFixed(2)} W`;
  }

  if (token === "buc" || token === "pcs") {
    return `${Math.round(rounded)} buc`;
  }

  return `${rounded.toFixed(2)} ${unit}`;
}

export function isPrintLaminationOperationRow(row: IntakeV4CncOperationRow): boolean {
  if (PRINT_OPERATION_TYPES.has(row.operation_type)) return true;
  if (/print|lamin|autocolant|vinyl_application|apply_printed/i.test(row.key)) return true;
  if (/imprimare|laminare|aplicare autocolant/i.test(row.display_name)) return true;
  return false;
}

export function splitMaterialBreakdownOperationRows(
  rows: IntakeV4CncOperationRow[] | undefined,
): { cncRows: IntakeV4CncOperationRow[]; printRows: IntakeV4CncOperationRow[] } {
  const cncRows: IntakeV4CncOperationRow[] = [];
  const printRows: IntakeV4CncOperationRow[] = [];
  for (const row of rows ?? []) {
    if (isPrintLaminationOperationRow(row)) {
      printRows.push(row);
    } else {
      cncRows.push(row);
    }
  }
  return { cncRows, printRows };
}

export function formatOperationPricingMissingLabel(operationType: string): string {
  if (PRINT_OPERATION_TYPES.has(operationType)) {
    return "Preț neconfigurat / necesită tarif operație print/laminare/colantare";
  }
  return "Preț operație neconfigurat";
}

export function adaptBackingAbsentOperationLabel(
  displayName: string,
  backingMode: string | null | undefined,
): string {
  const backingAbsent = !backingMode || backingMode === "none";
  if (!backingAbsent) return sanitizeOperatorDisplayText(displayName);
  let label = displayName;
  label = label.replace(/\s*și spate Forex\b/gi, "");
  label = label.replace(/\s*\+\s*spate Forex\b/gi, "");
  label = label.replace(/Debitare față plexiglas și spate Forex/gi, "Debitare față plexiglas");
  label = label.replace(/spate Forex la CNC/gi, "față plexiglas la CNC");
  return sanitizeOperatorDisplayText(label);
}

export type IntakeV4WarningGroup = "operator" | "quoting" | "technical";

export interface IntakeV4GroupedWarning {
  group: IntakeV4WarningGroup;
  message: string;
  count: number;
}

const TECHNICAL_WARNING_CODES = new Set([
  "mapping_gap",
  "missing_pricing_registry_row",
  "missing_client_analysis_hash",
  "dryrun_task_key",
  "dossier_priced_operation_split",
  "production_handoff_operation_groups",
]);

function classifyWarningMessage(message: string, code?: string): IntakeV4WarningGroup {
  const haystack = `${code ?? ""} ${message}`.toLowerCase();
  if (TECHNICAL_WARNING_CODES.has(code ?? "") || /mapping_gap|dryrun_task_key|missing_client_analysis_hash|dossier_priced|operation_groups/.test(haystack)) {
    return "technical";
  }
  if (/preț|pricing|registry|nesting|fallback|estimare|neconfigurat|missing_rate/.test(haystack)) {
    return "quoting";
  }
  if (/logo|artwork|raster|extern|embedded|decizie|execuție/.test(haystack)) {
    return "operator";
  }
  return "quoting";
}

export function groupIntakeV4Warnings(
  items: Array<{ message: string; code?: string }>,
): IntakeV4GroupedWarning[] {
  const buckets = new Map<string, IntakeV4GroupedWarning>();
  for (const item of items) {
    const group = classifyWarningMessage(item.message, item.code);
    const normalized = item.message.trim();
    const key = `${group}::${normalized}`;
    const existing = buckets.get(key);
    if (existing) {
      existing.count += 1;
    } else {
      buckets.set(key, { group, message: normalized, count: 1 });
    }
  }
  return Array.from(buckets.values());
}

export function formatGroupedWarningLine(warning: IntakeV4GroupedWarning): string {
  if (warning.count > 1) {
    return `${warning.message} (${warning.count}×)`;
  }
  return warning.message;
}

export function dedupeExternalRasterWarnings(messages: string[]): string[] {
  const rasterPatterns = [
    /external raster image reference detected/i,
    /external image asset must be provided/i,
    /logo\/artwork raster extern/i,
  ];
  let rasterSeen = false;
  const result: string[] = [];
  for (const message of messages) {
    if (rasterPatterns.some((pattern) => pattern.test(message))) {
      if (rasterSeen) continue;
      rasterSeen = true;
      result.push("2 logo-uri au asset extern lipsă — atașează folderul *_Images sau exportă SVG embedded.");
      continue;
    }
    result.push(message);
  }
  return result;
}

export function formatWorkspaceReadinessLabel(status: string | null | undefined): string {
  if (status === "ready_for_quote_preview") {
    return "Pregătit pentru previzualizare ofertă";
  }
  if (status === "finish_setup_incomplete") {
    return "Finisaje incomplete";
  }
  if (status === "logo_only_candidate_not_offerable") {
    return "Logo candidate read-only — neofertabil comercial";
  }
  return status?.replace(/_/g, " ") ?? "—";
}

export function formatQuoteHandoffOperatorLabels(args: {
  workspaceReadiness?: string | null;
  handoffAllowed: boolean;
  handoffLabel: string;
}): {
  previewLabel: string;
  handoffLabel: string;
  taskGenerationLabel: string;
} {
  const previewReady = args.workspaceReadiness === "ready_for_quote_preview";
  return {
    previewLabel: previewReady ? "Preview ofertare: pregătit" : "Preview ofertare: incomplet",
    handoffLabel: args.handoffAllowed
      ? "Handoff către ofertă reală: permis (draft intern)"
      : "Handoff către ofertă reală: blocat",
    taskGenerationLabel: "Generare task reală: blocată (doar previzualizare)",
  };
}

export function formatHandoffBlockerForOperator(code: string): string {
  if (code === "missing_client_analysis_hash") {
    return "Analiza SVG nu este sincronizată complet cu workspace-ul. Salvează/confirmă din nou analiza sau reîncarcă fișierul.";
  }
  if (code.startsWith("artwork_execution_undecided:")) {
    const layerKey = code.split(":")[1] ?? "artwork";
    return `Metoda de execuție pentru ${getOperatorLayerLabel(layerKey, layerKey)} nu este decisă.`;
  }
  return sanitizeOperatorDisplayText(code.replace(/_/g, " "));
}

export function formatTaskDryRunMaterialBreakdownStatus(
  available: boolean | undefined,
): string {
  if (available) {
    return "Material breakdown preview available; not bound to real task generation.";
  }
  return "Material breakdown not available for real task generation yet.";
}

export function assessArtworkAreaEstimateUnsafe(
  areaM2: number | null | undefined,
  options?: { hasExternalRaster?: boolean; peerAreas?: number[] },
): boolean {
  if (areaM2 == null || areaM2 <= 0) return false;
  if (options?.hasExternalRaster) return true;
  const peers = (options?.peerAreas ?? []).filter((value) => value > 0);
  if (peers.length >= 2) {
    const max = Math.max(...peers);
    const min = Math.min(...peers);
    if (max > 0 && min / max < 0.05) return true;
  }
  if (areaM2 < 0.005 && peers.some((peer) => peer > 0.1)) return true;
  return false;
}

export function formatArtworkAreaDisplay(
  areaM2: number | null | undefined,
  unsafe: boolean,
): string {
  if (unsafe) {
    return "Suprafață artwork: estimare nesigură — raster extern/clipPath/transform.";
  }
  if (areaM2 == null || areaM2 <= 0) return "—";
  return `${areaM2.toFixed(4)} m²`;
}

export const INTAKE_V4_MATERIAL_ESTIMATE_DISCLAIMER =
  "Nu este preț final ofertă. Prețul final se calculează în QuoteWizard / CostEngine.";

export const INTAKE_V4_PREVIEW_ONLY_BANNER =
  "Doar previzualizare — nu creează taskuri reale, nu consumă stoc, nu pornește producția.";

export const INTAKE_V4_TASK_PREVIEW_BOUNDARY_LINE =
  "Task preview temporar — va fi derivat din ProductSystem după integrarea registry-ului de operații.";

export function collectMaterialBreakdownWarningsForGrouping(
  breakdown: IntakeV4MaterialBreakdownResponse,
): Array<{ message: string; code?: string }> {
  return breakdown.warnings.map((warning) => ({
    message: warning.message,
    code: warning.code,
  }));
}
