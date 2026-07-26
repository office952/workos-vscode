/**
 * Display helpers for AcmPanel provisional commercial preview (Slice C).
 * Read-only projection — no pricing ownership.
 */

import type { AcmPanelCommercialPreview } from "@/lib/intakeV6/intakeV6PricedQuoteTypes";

export function formatAcmPanelMmPair(
  width: number | null | undefined,
  height: number | null | undefined,
): string | null {
  if (width == null || height == null) return null;
  if (!Number.isFinite(width) || !Number.isFinite(height)) return null;
  const w = Number.isInteger(width) ? String(width) : String(Math.round(width * 10) / 10);
  const h = Number.isInteger(height) ? String(height) : String(Math.round(height * 10) / 10);
  return `${w} × ${h} mm`;
}

export function formatAcmPanelMoney(
  value: number | null | undefined,
  currency: string | null | undefined,
): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const cur = (currency || "EUR").toUpperCase();
  try {
    return new Intl.NumberFormat("ro-RO", {
      style: "currency",
      currency: cur === "RON" || cur === "EUR" ? cur : "EUR",
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `${value.toFixed(2)} ${cur}`;
  }
}

export function formatAcmPanelQty(
  value: number | null | undefined,
  unit: string | null | undefined,
): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const u = unit || "";
  const n = Number.isInteger(value) ? String(value) : String(Math.round(value * 1000) / 1000);
  return u ? `${n} ${u}` : n;
}

/** Honest panel count for UI — never show "0 panouri" when assembly is priced. */
export function formatAcmPanelPanelCountLabel(
  panelCount: number | null | undefined,
  assemblyWidthMm: number | null | undefined,
  assemblyHeightMm: number | null | undefined,
): string | null {
  const hasAssembly =
    assemblyWidthMm != null &&
    assemblyHeightMm != null &&
    Number.isFinite(assemblyWidthMm) &&
    Number.isFinite(assemblyHeightMm) &&
    assemblyWidthMm > 0 &&
    assemblyHeightMm > 0;
  const n =
    panelCount != null && Number.isFinite(panelCount) && panelCount > 0
      ? Math.floor(panelCount)
      : hasAssembly
        ? 1
        : null;
  if (n == null) return null;
  return n === 1 ? "1 panou" : `${n} panouri`;
}

const WARNING_LABELS: Record<string, string> = {
  technical_configuration_unconfirmed: "Configurație tehnică neconfirmată",
  construction_catalog_defaults: "Valori construction din catalog",
  segmentation_proposed: "Segmentare PROPOSED — neconfirmată",
  composition_inconsistent_or_unconfirmed: "Compoziție inconsistentă / neconfirmată",
  segmentation_joints_no_commercial_rate: "Rosturi fără rată comercială (gap)",
  envelope_not_used_for_commercial_face_area: "Envelope ignorat pentru aria comercială",
  final_price_unavailable: "Preț final indisponibil",
  offer_ferm_unavailable: "Ofertă fermă indisponibilă",
  execution_blocked: "Execution blocat",
  quantity_unavailable: "Cantități CUT/V indisponibile pentru configurația curentă",
  "cut_v_quantity_source=proxy_rectangular": "CUT/V din proxy rectangular (estimare, nu măsurare DXF)",
  "cut_v_quantity_source=commercial_deduction": "CUT/V din deducere comercială (estimare ofertă)",
  "quantity_source=commercial_deduction": "CUT/V din deducere comercială (estimare ofertă)",
  "quantity_source=proxy_rectangular": "CUT/V din proxy rectangular (estimare)",
  missing_panel_list_assembly_face_only:
    "Lista panouri goală — cantități din dimensiunea ansamblului (1 panou logic)",
  double_fold_proxy_forbidden: "Double-fold: proxy rectangular interzis",
  l2_active_proxy_forbidden: "L2 activ: proxy rectangular interzis",
  production_geometry_stale: "Geometrie producție stale — reîncarcă DXF sau folosește deducerea comercială",
  measured_with_warnings: "Măsurare cu avertismente (ACI necunoscut exclus)",
  semantic_mapping_required: "Mapping ACI necesar — cantități incomplete",
  missing_panel_attachment: "Lipsește DXF pentru un panou",
  fold_sides_not_supported_for_commercial_deduction:
    "fold_sides nesuportat pentru deducere comercială (doar toate laturile)",
  hourly_commercial_line_detected: "Linie comercială orară detectată (neobișnuit pentru AcmPanel)",
};

/** Warnings already covered by the path-source line — do not repeat as raw keys. */
const PATH_SOURCE_REDUNDANT_WARNINGS = new Set([
  "quantity_source=commercial_deduction",
  "cut_v_quantity_source=commercial_deduction",
  "quantity_source=proxy_rectangular",
  "cut_v_quantity_source=proxy_rectangular",
]);

export function formatAcmPanelPathSource(
  status: string | null | undefined,
  source: string | null | undefined,
): string | null {
  const s = (status || source || "").trim();
  if (!s) return null;
  if (s === "measured" || source === "imported_dxf") return "Sursa cantități: măsurat (DXF)";
  if (
    s === "commercial_deduced" ||
    s === "commercial_deduced_with_assumptions" ||
    source === "commercial_deduced" ||
    source === "commercial_deduced_after_stale"
  ) {
    return "Sursa cantități: Deducere comercială";
  }
  if (s === "proxy_rectangular" || source === "proxy_rectangular") {
    return "Sursa cantități: proxy rectangular (estimare)";
  }
  if (s === "unavailable" || source === "unavailable") {
    return "Sursa cantități: indisponibil";
  }
  if (s === "stale" || source === "stale") return "Sursa cantități: stale (config schimbată)";
  if (s === "measured_with_warnings") return "Sursa cantități: măsurat cu avertismente";
  return `Sursa cantități: ${s}`;
}

export function formatAcmPanelMultiPanelDeductionNote(
  panelCount: number | null | undefined,
  status: string | null | undefined,
  source: string | null | undefined,
): string | null {
  if (panelCount == null || panelCount < 2) return null;
  const s = (status || source || "").trim();
  const commercial =
    s === "commercial_deduced" ||
    s === "commercial_deduced_with_assumptions" ||
    source === "commercial_deduced" ||
    source === "commercial_deduced_after_stale";
  if (!commercial) return null;
  return `Calculat separat pentru ${panelCount} panouri`;
}

export function humanizeAcmPanelPreviewWarning(code: string): string {
  const key = code.replace(/^acm_panel:/, "");
  return WARNING_LABELS[key] || key;
}

/** Humanize + drop duplicates already shown via path-source line. */
export function prepareAcmPanelPreviewWarnings(
  warnings: string[] | null | undefined,
  pathSourceShown: boolean,
): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of warnings || []) {
    const key = String(raw || "").replace(/^acm_panel:/, "").trim();
    if (!key) continue;
    if (pathSourceShown && PATH_SOURCE_REDUNDANT_WARNINGS.has(key)) continue;
    const label = humanizeAcmPanelPreviewWarning(key);
    if (seen.has(label)) continue;
    seen.add(label);
    out.push(label);
  }
  return out;
}

export function acmPanelPreviewIsVisible(
  preview: AcmPanelCommercialPreview | null | undefined,
): boolean {
  if (!preview) return false;
  if (preview.status === "unavailable") return false;
  return (preview.lines?.length ?? 0) > 0 || preview.estimated_total != null;
}
