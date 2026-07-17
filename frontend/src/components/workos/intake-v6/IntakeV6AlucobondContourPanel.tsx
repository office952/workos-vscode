import { useEffect, useMemo, useState } from "react";
import type { SvgAnalysisReport } from "@/lib/svgAnalyzer";
import {
  blankPreviewMm,
  buildAcmMountingSolutionFromSelection,
  confirmAlucobondSelection,
  emptySvgSupportSelection,
  readSvgSupportSelection,
  reconcileSelectionAfterReanalysis,
  type ContourRoleOption,
  type SvgSupportSelectionState,
} from "@/lib/svgAnalyzer";
import {
  bindingFromSupportSelection,
  readSvgComponentBindings,
  upsertBinding,
  type SvgComponentBinding,
} from "@/lib/intakeV6/svgComponentBindings";
import { v6 } from "./atoms/intakeV6Presentation";

type Props = {
  report: SvgAnalysisReport;
  finishSetup: Record<string, unknown> | null | undefined;
  svgSourceHash: string | null | undefined;
  disabled?: boolean;
  onSelectedContourIdChange?: (contourId: string | null) => void;
  onPersist: (patch: {
    svg_support_selection: SvgSupportSelectionState;
    svg_component_bindings?: SvgComponentBinding[];
    mounting_solution?: Record<string, unknown> | null;
    power_supply_service_corner?: string | null;
  }) => Promise<void> | void;
};

const ROLE_OPTIONS: Array<{ value: ContourRoleOption; label: string }> = [
  { value: "ALUCOBOND_CASED_PANEL", label: "Panou Alucobond casetat" },
  { value: "FLAT_BACKGROUND", label: "Fundal plat" },
  { value: "DECORATIVE_CONTOUR", label: "Contur decorativ" },
  { value: "GRAPHIC_ELEMENT", label: "Element grafic" },
  { value: "IGNORE", label: "Ignoră" },
];

export default function IntakeV6AlucobondContourPanel({
  report,
  finishSetup,
  svgSourceHash,
  disabled = false,
  onSelectedContourIdChange,
  onPersist,
}: Props) {
  const cc = report.closedContourCandidates;
  const existing = useMemo(() => {
    const raw = readSvgSupportSelection(finishSetup ?? undefined);
    return reconcileSelectionAfterReanalysis({
      previous: raw,
      current_svg_source_hash: svgSourceHash ?? "",
      candidates: cc?.candidates ?? [],
    });
  }, [finishSetup, svgSourceHash, cc]);

  const [selectedId, setSelectedId] = useState<string | null>(existing.contour_id);
  const [role, setRole] = useState<ContourRoleOption | "">((existing.role as ContourRoleOption) ?? "");
  const [foldCount, setFoldCount] = useState<1 | 2>(existing.casing_profile?.fold_count ?? 2);
  const [l1, setL1] = useState<number>(existing.casing_profile?.l1_mm ?? 60);
  const [l2, setL2] = useState<number>(existing.casing_profile?.l2_mm ?? 25);
  const [corner, setCorner] = useState<SvgSupportSelectionState["service_corner"]>(
    existing.service_corner,
  );
  const [frame, setFrame] = useState(Boolean(existing.internal_frame_enabled));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    onSelectedContourIdChange?.(selectedId);
  }, [selectedId, onSelectedContourIdChange]);

  const selected = cc?.candidates.find((c) => c.contour_id === selectedId) ?? null;
  const blank =
    selected && role === "ALUCOBOND_CASED_PANEL"
      ? blankPreviewMm({
          width_mm: selected.width_mm,
          height_mm: selected.height_mm,
          fold_count: foldCount,
          l1_mm: l1,
          l2_mm: foldCount === 2 ? l2 : null,
        })
      : null;

  if (!cc || cc.candidate_count === 0) {
    return null;
  }

  const onConfirm = async () => {
    setError(null);
    if (!selected || !role) {
      setError("Selectează un contur și confirmă rolul.");
      return;
    }
    const prevBindings = readSvgComponentBindings(finishSetup ?? undefined);
    if (role !== "ALUCOBOND_CASED_PANEL") {
      const cleared = emptySvgSupportSelection();
      const selection: SvgSupportSelectionState = {
        ...cleared,
        status: "confirmed",
        role,
        contour_id: selected.contour_id,
        svg_support_element_id: selected.element_id,
        geometry_hash: selected.geometry_hash,
        svg_source_hash: svgSourceHash ?? null,
        candidate_explanation: selected.reasons,
        confirmed_at: new Date().toISOString(),
      };
      setBusy(true);
      try {
        await onPersist({
          svg_support_selection: selection,
          svg_component_bindings: prevBindings.filter(
            (b) => b.component_template_code !== "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
          ),
          mounting_solution: null,
        });
      } finally {
        setBusy(false);
      }
      return;
    }
    const result = confirmAlucobondSelection({
      candidate: selected,
      svg_source_hash: svgSourceHash ?? "",
      fold_count: foldCount,
      l1_mm: l1,
      l2_mm: foldCount === 2 ? l2 : null,
      service_corner: corner,
      internal_frame_enabled: frame,
      unit_ambiguity: cc.unit_ambiguity,
    });
    if (result.blockers.length) {
      setError(result.blockers.join(" "));
      return;
    }
    const mounting = buildAcmMountingSolutionFromSelection(result.selection);
    const supportBinding = bindingFromSupportSelection(result.selection);
    setBusy(true);
    try {
      await onPersist({
        svg_support_selection: result.selection,
        svg_component_bindings: supportBinding
          ? upsertBinding(prevBindings, supportBinding)
          : prevBindings,
        mounting_solution: mounting,
        power_supply_service_corner: corner,
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      className={`${v6.cardCompact} space-y-3`}
      data-testid="intake-v6-alucobond-contour-panel"
    >
      <div>
        <h3 className={v6.sectionTitle}>Candidat de fundal / panou</h3>
        <p className={v6.helper}>
          Analyzerul detectează contururi închise și propune. Operatorul selectează și confirmă rolul.
        </p>
      </div>

      {existing.status === "reconfirm_required" ? (
        <p
          className="rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1.5 text-[11px] text-amber-100"
          data-testid="intake-v6-alucobond-reconfirm"
        >
          Necesită reconfirmare — SVG-ul sau geometria selectată s-a schimbat.
        </p>
      ) : null}

      {cc.unit_ambiguity ? (
        <p className="text-[11px] text-amber-200/90" data-testid="intake-v6-alucobond-unit-guard">
          Unități ambigue (guard): dimensiunile panoului folosesc corecție viewBox-as-mm.
        </p>
      ) : null}

      <ul className="max-h-48 space-y-1 overflow-auto text-[11px]" data-testid="intake-v6-contour-candidates">
        {cc.candidates.slice(0, 12).map((c) => {
          const active = c.contour_id === selectedId;
          return (
            <li key={c.contour_id}>
              <button
                type="button"
                disabled={disabled || busy}
                onClick={() => setSelectedId(active ? null : c.contour_id)}
                className={`w-full rounded border px-2 py-1.5 text-left ${
                  active
                    ? "border-cyan-500/70 bg-cyan-950/40 text-cyan-100"
                    : "border-[#2A3548] bg-[#0A0F1A]/60 text-slate-300 hover:border-slate-500"
                }`}
                data-testid={`intake-v6-contour-candidate-${c.contour_id}`}
              >
                <div className="font-medium">
                  {c.is_outer_candidate ? "Candidat panou" : "Contur detectat"} · {c.source_element_type}
                </div>
                <div className="text-slate-400">
                  {c.width_mm.toFixed(1)} × {c.height_mm.toFixed(1)} mm · arie{" "}
                  {(c.area_mm2 / 1_000_000).toFixed(3)} m² · conf. {(c.confidence * 100).toFixed(0)}%
                </div>
                <div className="text-[10px] text-slate-500">{c.reasons.slice(0, 3).join(" · ")}</div>
              </button>
            </li>
          );
        })}
      </ul>

      {selected ? (
        <div className="space-y-2 rounded border border-[#2A3548] p-2" data-testid="intake-v6-contour-selected">
          <label className="block text-[11px] text-slate-300">
            Confirmă rolul
            <select
              className="mt-1 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1"
              value={role}
              disabled={disabled || busy}
              onChange={(e) => setRole(e.target.value as ContourRoleOption)}
              data-testid="intake-v6-contour-role"
            >
              <option value="">— selectează —</option>
              {ROLE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          {role === "ALUCOBOND_CASED_PANEL" ? (
            <div className="grid gap-2 sm:grid-cols-2" data-testid="intake-v6-alucobond-casing-fields">
              <label className="text-[11px] text-slate-300">
                Număr de întoarceri
                <select
                  className="mt-1 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1"
                  value={foldCount}
                  onChange={(e) => setFoldCount(Number(e.target.value) as 1 | 2)}
                >
                  <option value={1}>1 întoarcere</option>
                  <option value={2}>2 întoarceri</option>
                </select>
              </label>
              <label className="text-[11px] text-slate-300">
                Prima întoarcere (mm)
                <input
                  type="number"
                  min={1}
                  className="mt-1 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1"
                  value={l1}
                  onChange={(e) => setL1(Number(e.target.value))}
                />
              </label>
              {foldCount === 2 ? (
                <label className="text-[11px] text-slate-300">
                  A doua întoarcere (mm)
                  <input
                    type="number"
                    min={1}
                    className="mt-1 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1"
                    value={l2}
                    onChange={(e) => setL2(Number(e.target.value))}
                  />
                </label>
              ) : null}
              <label className="text-[11px] text-slate-300">
                Adâncime casetă (mm)
                <input
                  type="number"
                  className="mt-1 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1 text-slate-400"
                  value={l1}
                  readOnly
                  title="Authority: finished_depth_mm = L1"
                />
              </label>
              <label className="text-[11px] text-slate-300">
                Colț de service
                <select
                  className="mt-1 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1"
                  value={corner ?? ""}
                  onChange={(e) =>
                    setCorner(
                      (e.target.value || null) as SvgSupportSelectionState["service_corner"],
                    )
                  }
                >
                  <option value="">neconfirmat</option>
                  <option value="TOP_LEFT">sus stânga</option>
                  <option value="TOP_RIGHT">sus dreapta</option>
                  <option value="BOTTOM_LEFT">jos stânga</option>
                  <option value="BOTTOM_RIGHT">jos dreapta</option>
                </select>
              </label>
              <label className="flex items-center gap-2 text-[11px] text-slate-300">
                <input type="checkbox" checked={frame} onChange={(e) => setFrame(e.target.checked)} />
                Cadru interior activ
              </label>
            </div>
          ) : null}

          {blank ? (
            <div
              className="rounded border border-emerald-800/40 bg-emerald-950/20 p-2 text-[11px] text-emerald-100"
              data-testid="intake-v6-alucobond-blank-preview"
            >
              <div className="font-semibold">Preview tehnic (read-only)</div>
              <div>
                Dimensiune finală: {selected.width_mm.toFixed(1)} × {selected.height_mm.toFixed(1)} mm
              </div>
              <div>
                Dimensiune semifabricat: {blank.blank_width_mm.toFixed(1)} × {blank.blank_height_mm.toFixed(1)}{" "}
                mm
              </div>
              <div className="text-[10px] text-slate-400">
                ID element: {selected.element_id} · hash: {selected.geometry_hash}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      {error ? (
        <p className="text-[11px] text-red-300" data-testid="intake-v6-alucobond-error">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        disabled={disabled || busy || !selected || !role}
        onClick={() => void onConfirm()}
        className="rounded border border-cyan-700/60 bg-cyan-950/40 px-3 py-1.5 text-[11px] text-cyan-100 disabled:opacity-40"
        data-testid="intake-v6-alucobond-confirm"
      >
        {busy ? "Se salvează…" : "Confirmă selecția"}
      </button>

      {existing.status === "confirmed" && existing.role === "ALUCOBOND_CASED_PANEL" ? (
        <p className="text-[11px] text-emerald-300" data-testid="intake-v6-alucobond-confirmed-badge">
          Confirmat · Panou Alucobond casetat
        </p>
      ) : null}
    </section>
  );
}
