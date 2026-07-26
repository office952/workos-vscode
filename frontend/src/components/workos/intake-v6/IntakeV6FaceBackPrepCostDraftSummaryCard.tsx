import {
  INTAKE_V6_FACE_BACK_PREP_BOUNDARY_LINE,
  FACE_BACK_PREP_CNC_UNAVAILABLE_LABEL,
  FACE_BACK_PREP_IGNORED_RAW_CNC_LABEL,
  FACE_BACK_PREP_SHORT_VERIFICATION_ALERT,
  FACE_BACK_PREP_TOTAL_UNAVAILABLE_LABEL,
  FACE_BACK_PREP_VERIFICATION_REASON,
  formatFaceBackPrepMoney,
  formatFaceBackPrepPerimeterM,
  needsFaceBackPrepPerimeterVerification,
  resolveFaceBackPrepCncPerimeterM,
  resolveFaceBackPrepDisplayCncCost,
  resolveFaceBackPrepDisplayMaterialCost,
  resolveFaceBackPrepDisplayTotalInternal,
  resolveFaceBackPrepIgnoredRawCncCost,
  resolveFaceBackPrepOperatorStatusLabel,
} from "@/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay";
import type { IntakeV6FaceBackPrepCostDraftViewModel } from "@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";

function unavailableCostLabel(): string {
  return FACE_BACK_PREP_CNC_UNAVAILABLE_LABEL;
}

export default function IntakeV6FaceBackPrepCostDraftSummaryCard({
  analysisReady,
  viewModel,
}: {
  analysisReady: boolean;
  viewModel: IntakeV6FaceBackPrepCostDraftViewModel;
}) {
  const { shanfrenForex, setShanfrenForex, draft, loading, error } = viewModel;
  const needsVerification = draft ? needsFaceBackPrepPerimeterVerification(draft) : false;
  const perimeterM = draft ? resolveFaceBackPrepCncPerimeterM(draft) : null;
  const materialCost = draft ? resolveFaceBackPrepDisplayMaterialCost(draft) : null;
  const cncCost = draft ? resolveFaceBackPrepDisplayCncCost(draft) : null;
  const totalInternal = draft ? resolveFaceBackPrepDisplayTotalInternal(draft) : null;
  const ignoredRawCnc = draft ? resolveFaceBackPrepIgnoredRawCncCost(draft) : null;
  const statusLabel = draft ? resolveFaceBackPrepOperatorStatusLabel(draft) : null;

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-face-back-prep-summary-card">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-[12px] font-bold uppercase tracking-wide text-slate-200">
          CNC față/spate — draft intern
        </h3>
        {statusLabel ? (
          <span data-testid="intake-v6-face-back-prep-summary-status-badge">
            <AtomsBadge tone={needsVerification ? "pending" : "ok"}>{statusLabel}</AtomsBadge>
          </span>
        ) : (
          <AtomsBadge tone="muted">Preview intern</AtomsBadge>
        )}
      </div>

      {!analysisReady ? (
        <p className="text-[12px] text-amber-200" data-testid="intake-v6-face-back-prep-summary-unavailable">
          Draft indisponibil: lipsesc date vectoriale.
        </p>
      ) : null}

      {analysisReady ? (
        <>
          <label className="mb-4 flex items-center gap-2 text-[12px] text-slate-300">
            <input
              type="checkbox"
              checked={shanfrenForex}
              onChange={(event) => setShanfrenForex(event.target.checked)}
              data-testid="intake-v6-face-back-prep-summary-shanfren-toggle"
            />
            <span>Șanfren Forex activ</span>
          </label>

          {loading ? (
            <p className="text-[12px] text-slate-400" data-testid="intake-v6-face-back-prep-summary-loading">
              Se încarcă…
            </p>
          ) : null}

          {error ? (
            <p className="text-[12px] text-red-300" data-testid="intake-v6-face-back-prep-summary-error">
              {error}
            </p>
          ) : null}

          {draft && !loading && !error ? (
            <>
              {needsVerification ? (
                <p
                  className="mb-3 rounded border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100"
                  data-testid="intake-v6-face-back-prep-summary-verification-alert"
                >
                  {FACE_BACK_PREP_SHORT_VERIFICATION_ALERT}
                </p>
              ) : null}

              <dl
                className="grid grid-cols-1 gap-2 text-[11px] sm:grid-cols-2"
                data-testid="intake-v6-face-back-prep-summary-totals"
              >
                {!needsVerification ? (
                  <div>
                    <dt className="text-slate-500">Perimetru CNC</dt>
                    <dd className="font-semibold text-wo-text-primary" data-testid="intake-v6-face-back-prep-summary-perimeter">
                      {formatFaceBackPrepPerimeterM(perimeterM)}
                    </dd>
                  </div>
                ) : null}
                <div>
                  <dt className="text-slate-500">Materiale estimate</dt>
                  <dd className="font-semibold text-slate-200" data-testid="intake-v6-face-back-prep-summary-materials">
                    {formatFaceBackPrepMoney(materialCost, draft.currency)}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">CNC</dt>
                  <dd
                    className="font-semibold text-slate-200"
                    data-testid="intake-v6-face-back-prep-summary-cnc"
                  >
                    {cncCost != null
                      ? formatFaceBackPrepMoney(cncCost, draft.currency)
                      : unavailableCostLabel()}
                  </dd>
                </div>
                <div className={needsVerification ? "sm:col-span-2" : undefined}>
                  <dt className="text-slate-500">Total intern draft</dt>
                  <dd
                    className="font-semibold text-slate-200"
                    data-testid="intake-v6-face-back-prep-summary-total-internal"
                  >
                    {totalInternal != null
                      ? formatFaceBackPrepMoney(totalInternal, draft.currency)
                      : FACE_BACK_PREP_TOTAL_UNAVAILABLE_LABEL}
                  </dd>
                </div>
              </dl>

              {needsVerification ? (
                <p className="mt-2 text-[10px] text-slate-500" data-testid="intake-v6-face-back-prep-summary-reason">
                  Motiv: {FACE_BACK_PREP_VERIFICATION_REASON}
                </p>
              ) : null}

              <IntakeV6TechnicalDetailsAccordion
                title="Detalii tehnice CNC draft"
                testId="intake-v6-face-back-prep-summary-technical"
              >
                <p className="text-[10px] text-slate-600" data-testid="intake-v6-face-back-prep-summary-boundaries">
                  {INTAKE_V6_FACE_BACK_PREP_BOUNDARY_LINE}
                </p>
                {ignoredRawCnc != null ? (
                  <p
                    className="mt-2 text-[10px] text-slate-500"
                    data-testid="intake-v6-face-back-prep-summary-ignored-raw-cnc"
                  >
                    {FACE_BACK_PREP_IGNORED_RAW_CNC_LABEL}:{" "}
                    {formatFaceBackPrepMoney(ignoredRawCnc, draft.currency)}
                  </p>
                ) : null}
              </IntakeV6TechnicalDetailsAccordion>
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}



