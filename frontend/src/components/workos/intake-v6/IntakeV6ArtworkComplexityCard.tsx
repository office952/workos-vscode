import type { ArtworkComplexityAssessment } from "@/lib/svgAnalyzer/analyzer/artworkComplexityAssessment";
import {
  ARTWORK_APPLICATION_LABELS,
  type IntakeV6ArtworkComplexityDecision,
  formatArtworkSourceType,
} from "@/lib/intakeV6/intakeV6ArtworkComplexityDisplay";
import { formatArtworkComplexityWarning } from "@/lib/intakeV6/intakeV6ArtworkLogoDiagnostic";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

function formatAreaM2(value: number | null | undefined): string {
  if (value == null || value <= 0) return "—";
  return `${value.toFixed(4)} m²`;
}

export default function IntakeV6ArtworkComplexityCard({
  assessments,
  decisions,
  onDecisionChange,
}: {
  assessments: ArtworkComplexityAssessment[];
  decisions: IntakeV6ArtworkComplexityDecision[];
  onDecisionChange: (next: IntakeV6ArtworkComplexityDecision[]) => void;
}) {
  if (!assessments.length) return null;

  function patchDecision(
    artworkId: string,
    patch: Partial<IntakeV6ArtworkComplexityDecision>,
  ) {
    const next = decisions.map((row) =>
      row.artwork_id === artworkId ? { ...row, ...patch } : row,
    );
    onDecisionChange(next);
  }

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-artwork-complexity-card">
      <h2 className="mb-3 text-[13px] font-bold uppercase tracking-wide">
        Artwork / grafică față
      </h2>
      <p className="mb-4 text-[12px] text-slate-400">
        Clasificare artwork pentru fața literelor volumetrice — recomandare de aplicare, nu
        execuție automată.
      </p>

      <div className="space-y-4">
        {assessments.map((assessment) => {
          const decision = decisions.find((row) => row.artwork_id === assessment.artwork_id);
          const operatorApplication =
            decision?.operator_application ?? assessment.recommended_application;

          return (
            <div
              key={assessment.artwork_id}
              className="rounded border border-[#2A3548] bg-[#0A0F1A]/60 p-3"
              data-testid={`intake-v6-artwork-complexity-row-${assessment.artwork_id}`}
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="text-[12px] font-semibold text-slate-200">
                  {assessment.source_layer_name ?? assessment.artwork_id}
                </span>
                <AtomsBadge tone="muted">{formatArtworkSourceType(assessment.source_element_type)}</AtomsBadge>
                <AtomsBadge
                  tone={
                    assessment.recommended_application === "print_on_vinyl_laminated"
                      ? "pending"
                      : assessment.recommended_application === "vinyl_cut"
                        ? "ok"
                        : "muted"
                  }
                  data-testid="intake-v6-artwork-recommendation"
                >
                  {ARTWORK_APPLICATION_LABELS[assessment.recommended_application]}
                </AtomsBadge>
              </div>

              <dl className="grid gap-1 text-[11px] text-slate-400 sm:grid-cols-2">
                <div>
                  <dt className="text-slate-500">Culori dominante estimate</dt>
                  <dd className="text-slate-300">{assessment.dominant_color_count}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Suprafață estimată (vector acoperit)</dt>
                  <dd className="text-slate-300">{formatAreaM2(assessment.artwork_area_estimate_m2)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Gradient / raster / foto</dt>
                  <dd className="text-slate-300">
                    {[
                      assessment.has_gradient ? "gradient" : null,
                      assessment.has_raster_image ? "raster" : null,
                      assessment.has_external_image ? "extern" : null,
                    ]
                      .filter(Boolean)
                      .join(", ") || "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Motiv recomandare</dt>
                  <dd className="text-slate-300">{assessment.recommendation_reason}</dd>
                </div>
              </dl>

              {assessment.warnings.length > 0 ? (
                <ul className="mt-2 space-y-1 text-[11px] text-amber-300/90">
                  {assessment.warnings.map((warning) => (
                    <li key={warning} data-testid="intake-v6-artwork-warning">
                      {formatArtworkComplexityWarning(warning)}
                    </li>
                  ))}
                </ul>
              ) : null}

              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded border border-emerald-700/60 bg-emerald-950/40 px-3 py-1.5 text-[11px] text-emerald-200"
                  data-testid="intake-v6-accept-print-laminate"
                  onClick={() =>
                    patchDecision(assessment.artwork_id, {
                      operator_application: "print_on_vinyl_laminated",
                      accepted_system_recommendation: true,
                      override_manual_vinyl_cut: false,
                    })
                  }
                >
                  Accept recomandarea: print + laminare
                </button>
                <button
                  type="button"
                  className="rounded border border-[#334155] bg-[#0A0F1A] px-3 py-1.5 text-[11px] text-slate-300"
                  data-testid="intake-v6-override-vinyl-cut"
                  onClick={() =>
                    patchDecision(assessment.artwork_id, {
                      operator_application: "vinyl_cut",
                      accepted_system_recommendation: false,
                      override_manual_vinyl_cut: true,
                    })
                  }
                >
                  Override manual: colantare decupată
                </button>
              </div>

              {decision?.override_manual_vinyl_cut ? (
                <p
                  className="mt-2 text-[11px] text-amber-300/90"
                  data-testid="intake-v6-artwork-manual-review-state"
                >
                  Override operator documentat — colantare decupată în loc de recomandarea sistemului.
                </p>
              ) : null}

              {operatorApplication === "print_on_vinyl_laminated" ? (
                <p className="mt-2 text-[11px] text-slate-400" data-testid="intake-v6-print-laminate-visible">
                  Preview material: autocolant printabil + laminare protecție (rate lipsă = estimare
                  absentă).
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}



