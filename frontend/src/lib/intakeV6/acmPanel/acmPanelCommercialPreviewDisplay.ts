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
};

export function humanizeAcmPanelPreviewWarning(code: string): string {
  const key = code.replace(/^acm_panel:/, "");
  return WARNING_LABELS[key] || key;
}

export function acmPanelPreviewIsVisible(
  preview: AcmPanelCommercialPreview | null | undefined,
): boolean {
  if (!preview) return false;
  if (preview.status === "unavailable") return false;
  return (preview.lines?.length ?? 0) > 0 || preview.estimated_total != null;
}
