/**
 * Canonical ACP geometry card — same card model as layer/group cards.
 * Closed-contour detection stays in analyzer SoT; UI shows only the primary outer proposal.
 */

import { useEffect, useMemo, useState } from "react";
import type { SvgBindableComponent } from "@/lib/api";
import type { ClosedContourCandidate, SvgAnalysisReport } from "@/lib/svgAnalyzer";
import {
  buildAcmMountingSolutionFromSelection,
  confirmAlucobondSelection,
  emptySvgSupportSelection,
  readSvgSupportSelection,
  reconcileSelectionAfterReanalysis,
} from "@/lib/svgAnalyzer";
import {
  bindingFromSupportSelection,
  ownerFacingComponentProductLabel,
  ownerGeometryLabel,
  readSvgComponentBindings,
  upsertBinding,
  type SvgComponentBinding,
} from "@/lib/intakeV6/svgComponentBindings";
import IntakeV6LayerStatusIcon from "./IntakeV6LayerStatusIcon";

export function resolvePrimaryClosedContourCandidate(
  candidates: ClosedContourCandidate[] | undefined | null,
): ClosedContourCandidate | null {
  if (!candidates?.length) return null;
  return candidates.find((c) => c.is_outer_candidate) ?? candidates[0] ?? null;
}

type Props = {
  supportComp: SvgBindableComponent;
  report: SvgAnalysisReport;
  finishSetup: Record<string, unknown> | null | undefined;
  svgSourceHash: string | null | undefined;
  disabled?: boolean;
  focused?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
  onSelectedContourIdChange?: (contourId: string | null) => void;
  onPersist: (patch: {
    svg_support_selection?: Record<string, unknown> | null;
    svg_component_bindings?: SvgComponentBinding[];
    mounting_solution?: Record<string, unknown> | null;
    power_supply_service_corner?: string | null;
  }) => Promise<void> | void;
};

export default function IntakeV6SupportContourGeometryCard({
  supportComp,
  report,
  finishSetup,
  svgSourceHash,
  disabled = false,
  focused = false,
  onFocus,
  onBlur,
  onSelectedContourIdChange,
  onPersist,
}: Props) {
  const cc = report.closedContourCandidates;
  const candidates = cc?.candidates ?? [];
  const primary = useMemo(() => resolvePrimaryClosedContourCandidate(candidates), [candidates]);

  const existing = useMemo(() => {
    const raw = readSvgSupportSelection(finishSetup ?? undefined);
    return reconcileSelectionAfterReanalysis({
      previous: raw,
      current_svg_source_hash: svgSourceHash ?? "",
      candidates,
    });
  }, [finishSetup, svgSourceHash, candidates]);

  const [activeContourId, setActiveContourId] = useState<string | null>(
    existing.contour_id ?? primary?.contour_id ?? null,
  );
  const [pickerOpen, setPickerOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (existing.contour_id) {
      setActiveContourId(existing.contour_id);
      return;
    }
    if (primary?.contour_id) {
      setActiveContourId(primary.contour_id);
    }
  }, [existing.contour_id, primary?.contour_id]);

  const activeCandidate =
    candidates.find((c) => c.contour_id === activeContourId) ?? primary;

  useEffect(() => {
    if (focused && activeCandidate) {
      onSelectedContourIdChange?.(activeCandidate.contour_id);
    }
  }, [focused, activeCandidate, onSelectedContourIdChange]);

  if (!cc || cc.candidate_count === 0 || !primary) return null;

  const bindings = readSvgComponentBindings(finishSetup);
  const supportBinding = bindings.find(
    (b) => b.component_template_code === supportComp.component_template_code,
  );
  const associated =
    (existing.status === "confirmed" || existing.status === "draft") &&
    existing.role === "ALUCOBOND_CASED_PANEL";
  const statusLabel =
    existing.status === "reconfirm_required"
      ? "Necesită reconfirmare"
      : associated && supportBinding?.status === "CONFIRMED"
        ? "Confirmat"
        : associated
          ? "Selectat"
          : "Opțional · disponibil";

  const associate = async (candidate?: ClosedContourCandidate | null) => {
    const target = candidate ?? activeCandidate;
    if (!target || disabled || busy) return;
    setError(null);
    setBusy(true);
    try {
      const result = confirmAlucobondSelection({
        candidate: target,
        svg_source_hash: svgSourceHash ?? "",
        fold_count: existing.casing_profile?.fold_count ?? 2,
        l1_mm: existing.casing_profile?.l1_mm ?? 60,
        l2_mm: existing.casing_profile?.fold_count === 1 ? null : (existing.casing_profile?.l2_mm ?? 25),
        service_corner: existing.service_corner ?? null,
        internal_frame_enabled: Boolean(existing.internal_frame_enabled),
        unit_ambiguity: Boolean(cc.unit_ambiguity),
      });
      if (result.blockers.length) {
        setError(result.blockers.join(" "));
        return;
      }
      const supportBindingNext = bindingFromSupportSelection(result.selection);
      const prevBindings = readSvgComponentBindings(finishSetup);
      await onPersist({
        svg_support_selection: result.selection,
        svg_component_bindings: supportBindingNext
          ? upsertBinding(prevBindings, supportBindingNext)
          : prevBindings,
        mounting_solution: buildAcmMountingSolutionFromSelection(result.selection),
        power_supply_service_corner: result.selection.service_corner,
      });
      setActiveContourId(target.contour_id);
      onSelectedContourIdChange?.(target.contour_id);
    } finally {
      setBusy(false);
    }
  };

  const clearAssociation = async () => {
    if (disabled || busy) return;
    setBusy(true);
    setError(null);
    try {
      const prevBindings = readSvgComponentBindings(finishSetup);
      await onPersist({
        svg_support_selection: emptySvgSupportSelection(),
        svg_component_bindings: prevBindings.filter(
          (b) => b.component_template_code !== supportComp.component_template_code,
        ),
        mounting_solution: null,
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <article
      className={`rounded-md border px-3 py-3 transition outline-none focus-visible:ring-1 focus-visible:ring-cyan-400/50 ${
        focused
          ? "border-cyan-400/40 bg-cyan-400/5"
          : associated
            ? "border-emerald-500/30 bg-emerald-500/5"
            : "border-[#2A3548]/80 bg-[#0A0F1A]/40"
      }`}
      data-testid="intake-v6-support-contour-card"
      data-acp-card="canonical"
      tabIndex={0}
      onMouseEnter={onFocus}
      onMouseLeave={onBlur}
      onFocus={onFocus}
      onBlur={onBlur}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-[12px] font-semibold text-slate-100">
            Panou ACP — contur exterior
          </p>
          <p className="text-[11px] text-slate-500">Grup detectat: contur principal închis</p>
        </div>
        {associated ? (
          <IntakeV6LayerStatusIcon state="confirmed" testId="intake-v6-support-contour-status-icon" />
        ) : (
          <span
            className="shrink-0 rounded border border-slate-600/60 px-1.5 py-0.5 text-[10px] text-slate-400"
            data-testid="intake-v6-support-contour-status"
          >
            {statusLabel}
          </span>
        )}
      </div>

      <label className="block">
        <span className="mb-1 block text-[11px] text-slate-400">Rol geometrie</span>
        <select
          className="w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[12px] text-slate-200"
          value={associated || existing.role === "ALUCOBOND_CASED_PANEL" ? "SUPPORT_CONTOUR" : "NONE"}
          disabled={disabled || busy}
          data-testid="intake-v6-support-geometry-role"
          onChange={(e) => {
            if (e.target.value === "SUPPORT_CONTOUR") {
              void associate();
            } else {
              void clearAssociation();
            }
          }}
        >
          <option value="NONE">— neasociat —</option>
          <option value="SUPPORT_CONTOUR">{ownerGeometryLabel("SUPPORT_CONTOUR")}</option>
        </select>
      </label>

      <div
        className="mt-2 rounded border border-[#2A3548]/80 bg-[#0A0F1A]/70 px-2 py-1.5"
        data-testid="intake-v6-support-contour-component"
      >
        <p className="text-[10px] uppercase tracking-wide text-slate-500">Componentă produs</p>
        <p className="text-[12px] font-medium text-slate-100">
          {ownerFacingComponentProductLabel(supportComp)}
        </p>
        <p className="mt-0.5 text-[10px] text-slate-400">
          {supportComp.required ? "Obligatoriu" : "Opțional"}
          {associated ? " · asociat" : " · disponibil"}
        </p>
      </div>

      {error ? (
        <p className="mt-2 text-[11px] text-red-300" data-testid="intake-v6-support-contour-error">
          {error}
        </p>
      ) : null}

      <details className="mt-2">
        <summary className="cursor-pointer text-[10px] text-slate-500">Detalii tehnice</summary>
        <div className="mt-1 space-y-1 text-[10px] text-slate-500">
          <p className="font-mono">{supportComp.component_template_code}</p>
          {activeCandidate ? (
            <>
              <p>
                {activeCandidate.width_mm.toFixed(1)} × {activeCandidate.height_mm.toFixed(1)} mm ·
                conf. {(activeCandidate.confidence * 100).toFixed(0)}%
              </p>
              <p className="font-mono break-all">id: {activeCandidate.contour_id}</p>
              <p className="font-mono break-all">hash: {activeCandidate.geometry_hash}</p>
            </>
          ) : null}
          {candidates.length > 1 ? (
            <div className="pt-1">
              <button
                type="button"
                className="text-[10px] text-cyan-300/90 underline-offset-2 hover:underline"
                data-testid="intake-v6-support-change-geometry"
                disabled={disabled || busy}
                onClick={(e) => {
                  e.preventDefault();
                  setPickerOpen((v) => !v);
                }}
              >
                {pickerOpen ? "Închide schimbarea geometriei" : "Schimbă geometria"}
              </button>
              {pickerOpen ? (
                <ul
                  className="mt-1 max-h-36 space-y-1 overflow-auto"
                  data-testid="intake-v6-support-geometry-picker"
                >
                  {candidates.slice(0, 12).map((c) => (
                    <li key={c.contour_id}>
                      <button
                        type="button"
                        className={`w-full rounded border px-1.5 py-1 text-left ${
                          c.contour_id === activeContourId
                            ? "border-cyan-500/60 bg-cyan-950/40 text-cyan-100"
                            : "border-[#2A3548] text-slate-400"
                        }`}
                        onClick={() => {
                          setActiveContourId(c.contour_id);
                          onSelectedContourIdChange?.(c.contour_id);
                          if (associated) void associate(c);
                        }}
                      >
                        {c.is_outer_candidate ? "Contur exterior" : "Contur"} ·{" "}
                        {c.width_mm.toFixed(0)}×{c.height_mm.toFixed(0)} mm
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
          <p className="pt-1 text-slate-600">
            Configurația casetării (L1/L2, colț service) se face la Pasul 2 — Configurare.
          </p>
        </div>
      </details>
    </article>
  );
}
