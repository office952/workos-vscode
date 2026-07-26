/**
 * Admin/quote panel for flat material nesting summary (sheet + roll).
 * Displays backend truth only — never recomputes nesting.
 */

import { AlertTriangle, Layers } from "lucide-react";

export interface FlatMaterialSheetSummaryEntry {
  role: string;
  label: string;
  enabled?: boolean;
  reason?: string;
  sheets_used?: number;
  allocated_sheet_area_m2?: number;
  used_piece_bbox_area_m2?: number;
  remaining_area_m2?: number;
  remaining_percent?: number;
  profile_source_label?: string;
  is_default_fallback?: boolean;
  sheet_width_mm?: number;
  sheet_height_mm?: number;
  pieces_count?: number;
  nesting_method?: string;
  is_fallback?: boolean;
  geometry_assumption?: string;
  real_offcut_measurement_required?: boolean;
}

export interface FlatMaterialRollSummaryEntry {
  role: string;
  label: string;
  recommended_roll_length_m?: number;
  quantity_m2?: number;
  pieces_count?: number;
  method?: string;
}

export interface FlatMaterialNestingSummaryData {
  sheet_materials?: FlatMaterialSheetSummaryEntry[];
  roll_materials?: FlatMaterialRollSummaryEntry[];
  real_offcut_measurement_required?: boolean;
}

interface Props {
  summary: FlatMaterialNestingSummaryData | null | undefined;
}

function formatM2(value?: number): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} mp`;
}

function formatMmPair(w?: number, h?: number): string {
  if (w == null || h == null) return "—";
  return `${Math.round(w)} × ${Math.round(h)} mm`;
}

function methodLabel(entry: FlatMaterialSheetSummaryEntry): string {
  if (entry.geometry_assumption === "same_as_letter_face_bbox") {
    return "aceeași geometrie ca fețele literelor";
  }
  if (entry.is_fallback) {
    return "estimare pe dimensiunea ansamblului";
  }
  if (entry.nesting_method === "sheet_rectangular") {
    return "calculat pe piesele literelor";
  }
  return entry.nesting_method ?? "—";
}

export default function FlatMaterialNestingSummary({ summary }: Props) {
  if (!summary) return null;

  const sheets = summary.sheet_materials ?? [];
  const rolls = summary.roll_materials ?? [];
  const hasContent =
    sheets.some((s) => s.enabled || s.reason) || rolls.length > 0;
  if (!hasContent) return null;

  return (
    <div
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4"
      data-testid="flat-material-nesting-summary"
    >
      <div className="flex items-center gap-2 mb-3">
        <Layers className="w-4 h-4 text-slate-400" />
        <h4 className="text-[13px] font-semibold text-slate-200">Nesting materiale plane</h4>
      </div>

      <div className="space-y-4">
        {sheets.map((entry) => (
          <div
            key={entry.role}
            className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3"
            data-testid={`flat-nesting-sheet-${entry.role}`}
          >
            <p className="text-[12px] font-medium text-slate-200">{entry.label}</p>
            {!entry.enabled ? (
              <p className="text-[11px] text-slate-500 mt-1">
                Nesting indisponibil — {entry.reason === "missing_geometry" ? "lipsesc piese geometrice" : entry.reason ?? "date insuficiente"}
              </p>
            ) : (
              <ul className="mt-2 space-y-1 text-[11px] text-slate-400">
                <li>Profil placă: {formatMmPair(entry.sheet_width_mm, entry.sheet_height_mm)}</li>
                <li>
                  Sursă profil: {entry.profile_source_label ?? "—"}
                  {entry.is_default_fallback ? (
                    <span className="text-amber-400/90 ml-1">(fallback intern)</span>
                  ) : null}
                </li>
                <li>Piese: {entry.pieces_count ?? "—"}</li>
                <li>Plăci alocate: {entry.sheets_used ?? "—"}</li>
                <li>Suprafață plăci alocată: {formatM2(entry.allocated_sheet_area_m2)}</li>
                <li>Suprafață piese: {formatM2(entry.used_piece_bbox_area_m2)}</li>
                <li>
                  Rest placă estimat: {formatM2(entry.remaining_area_m2)}
                  {entry.remaining_percent != null ? ` (${entry.remaining_percent}%)` : ""}
                </li>
                <li>Metodă: {methodLabel(entry)}</li>
              </ul>
            )}
          </div>
        ))}

        {rolls.map((entry) => (
          <div
            key={entry.role}
            className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3"
            data-testid={`flat-nesting-roll-${entry.role}`}
          >
            <p className="text-[12px] font-medium text-slate-200">{entry.label}</p>
            <ul className="mt-2 space-y-1 text-[11px] text-slate-400">
              <li>
                Rolă recomandată:{" "}
                {entry.recommended_roll_length_m != null
                  ? `${entry.recommended_roll_length_m.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ml`
                  : "—"}
              </li>
              <li>Suprafață: {formatM2(entry.quantity_m2)}</li>
            </ul>
          </div>
        ))}
      </div>

      {summary.real_offcut_measurement_required ? (
        <div className="mt-3 flex items-start gap-2 text-[11px] text-slate-500">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
          <span>
            Restul real se măsoară în producție și se poate introduce în stoc.
          </span>
        </div>
      ) : null}
    </div>
  );
}
