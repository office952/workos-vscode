import {
  buildFaceBackPrepFormulaSummary,
  FACE_BACK_PREP_CNC_UNAVAILABLE_LABEL,
  FACE_BACK_PREP_IGNORED_RAW_CNC_LABEL,
  FACE_BACK_PREP_SHORT_VERIFICATION_ALERT,
  FACE_BACK_PREP_TOTAL_UNAVAILABLE_LABEL,
  FACE_BACK_PREP_VERIFICATION_REASON,
  formatFaceBackPrepMoney,
  formatFaceBackPrepPerimeterM,
  formatFaceBackPrepStatusLabel,
  needsFaceBackPrepPerimeterVerification,
  resolveFaceBackPrepCncPerimeterM,
  resolveFaceBackPrepDisplayCncCost,
  resolveFaceBackPrepDisplayMaterialCost,
  resolveFaceBackPrepDisplayTotalInternal,
  resolveFaceBackPrepIgnoredRawCncCost,
  resolveFaceBackPrepOperatorStatusLabel,
  INTAKE_V6_FACE_BACK_PREP_BOUNDARY_LINE,
  sortFaceBackPrepTaskDrafts,
} from "@/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay";
import {
  useIntakeV6FaceBackPrepCostDraft,
  type IntakeV6FaceBackPrepCostDraftViewModel,
} from "@/lib/intakeV6/useIntakeV6FaceBackPrepCostDraft";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6FaceBackPrepCostDraftPanel({
  workspaceId,
  analysisReady,
  viewModel,
}: {
  workspaceId: string | null;
  analysisReady: boolean;
  viewModel?: IntakeV6FaceBackPrepCostDraftViewModel;
}) {
  const internalViewModel = useIntakeV6FaceBackPrepCostDraft(workspaceId, analysisReady, !viewModel);
  const { shanfrenForex, setShanfrenForex, draft, loading, error } = viewModel ?? internalViewModel;
  const controlledExternally = Boolean(viewModel);

  const formulaLines = draft ? buildFaceBackPrepFormulaSummary(draft, shanfrenForex) : [];
  const needsVerification = draft ? needsFaceBackPrepPerimeterVerification(draft) : false;
  const perimeterM = draft ? resolveFaceBackPrepCncPerimeterM(draft) : null;
  const materialCost = draft ? resolveFaceBackPrepDisplayMaterialCost(draft) : null;
  const cncCost = draft ? resolveFaceBackPrepDisplayCncCost(draft) : null;
  const totalInternal = draft ? resolveFaceBackPrepDisplayTotalInternal(draft) : null;
  const ignoredRawCnc = draft ? resolveFaceBackPrepIgnoredRawCncCost(draft) : null;
  const statusLabel = draft ? resolveFaceBackPrepOperatorStatusLabel(draft) : null;
  const orderedTasks = draft ? sortFaceBackPrepTaskDrafts(draft.task_drafts) : [];

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-face-back-prep-cost-draft-panel">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-[12px] font-bold uppercase tracking-wide text-slate-200">
            CNC față/spate — detaliu draft
          </h3>
          <p className="mt-1 text-[10px] text-slate-500" data-testid="intake-v6-face-back-prep-subtitle">
            Read-only · Nu creează ofertă · Nu creează taskuri · Nu consumă stoc
          </p>
        </div>
        <AtomsBadge tone="muted">Preview intern</AtomsBadge>
      </div>

      {!analysisReady ? (
        <p className="text-[12px] text-amber-200" data-testid="intake-v6-face-back-prep-unavailable">
          Draft indisponibil: lipsesc date vectoriale.
        </p>
      ) : null}

      {analysisReady ? (
        <>
          <div
            className="mb-4 rounded border border-[#2A3548] bg-[#0A0F1A]/60 px-3 py-2 text-[11px] text-slate-400"
            data-testid="intake-v6-face-back-prep-template"
          >
            <div className={v6.mono + " text-slate-200"}>
              {draft?.template_key ?? "TPL-VOLUMETRIC-FACE-BACK-PREP"}
            </div>
            <div>version: {draft?.version ?? "v1-cnc-only"}</div>
          </div>

          {controlledExternally ? (
            <p className="mb-4 text-[11px] text-slate-400" data-testid="intake-v6-face-back-prep-shanfren-state">
              Șanfren Forex: {shanfrenForex ? "activ" : "inactiv"} — toggle în cardul compact Review
            </p>
          ) : (
            <label className="mb-4 flex items-center gap-2 text-[12px] text-slate-300">
              <input
                type="checkbox"
                checked={shanfrenForex}
                onChange={(event) => setShanfrenForex(event.target.checked)}
                data-testid="intake-v6-face-back-prep-shanfren-toggle"
              />
              <span>Șanfren Forex activ</span>
            </label>
          )}

          {loading ? (
            <p className="text-[12px] text-slate-400" data-testid="intake-v6-face-back-prep-loading">
              Se încarcă draftul CNC față/spate…
            </p>
          ) : null}

          {error ? (
            <p className="text-[12px] text-red-300" data-testid="intake-v6-face-back-prep-error">
              {error}
            </p>
          ) : null}

          {draft && !loading && !error ? (
            <>
              {needsVerification ? (
                <p
                  className="mb-4 rounded border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100"
                  data-testid="intake-v6-face-back-prep-vector-warning"
                >
                  {FACE_BACK_PREP_SHORT_VERIFICATION_ALERT}
                </p>
              ) : null}

              <div
                className="mb-4 rounded border border-[#2A3548] bg-[#0A0F1A]/40 px-3 py-2 text-[10px] text-slate-500"
                data-testid="intake-v6-face-back-prep-formulas"
              >
                {formulaLines.map((line) => (
                  <div key={line}>{line}</div>
                ))}
              </div>

              <div className="mb-4" data-testid="intake-v6-face-back-prep-materials">
                <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">
                  Materiale
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px]">
                    <thead>
                      <tr className="border-b border-[#2A3548] text-left text-slate-500">
                        <th className="py-2 pr-3">Material</th>
                        <th className="py-2 pr-3">Key</th>
                        <th className="py-2 pr-3">Cantitate</th>
                        <th className="py-2 pr-3">Preț unit.</th>
                        <th className="py-2 pr-3">Cost</th>
                        <th className="py-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {draft.materials.map((row) => (
                        <tr
                          key={`${row.component}-${row.material_key}`}
                          className="border-b border-[#2A3548]/60"
                          data-testid={`intake-v6-face-back-prep-material-${row.material_key}`}
                        >
                          <td className="py-2 pr-3 text-slate-200">{row.material_label}</td>
                          <td className={`py-2 pr-3 ${v6.mono} text-slate-500`}>{row.material_key}</td>
                          <td className="py-2 pr-3 text-slate-300">
                            {row.quantity.toFixed(4)} {row.unit}
                          </td>
                          <td className="py-2 pr-3 text-slate-300">
                            {row.unit_price != null
                              ? `${row.unit_price.toFixed(2)} ${row.currency}/${row.unit}`
                              : "—"}
                          </td>
                          <td className="py-2 pr-3 text-slate-200">
                            {formatFaceBackPrepMoney(row.cost, row.currency)}
                          </td>
                          <td className="py-2 text-slate-400">{formatFaceBackPrepStatusLabel(row.status)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mb-4" data-testid="intake-v6-face-back-prep-operations">
                <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">
                  Operații CNC
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px]">
                    <thead>
                      <tr className="border-b border-[#2A3548] text-left text-slate-500">
                        <th className="py-2 pr-3">Operație</th>
                        <th className="py-2 pr-3">Perimetru ml</th>
                        <th className="py-2 pr-3">Treceri</th>
                        <th className="py-2 pr-3">Tarif</th>
                        <th className="py-2 pr-3">Cost</th>
                        <th className="py-2 pr-3">Sursă perimetru</th>
                        <th className="py-2">Încredere</th>
                      </tr>
                    </thead>
                    <tbody>
                      {draft.operations.map((row) => (
                        <tr
                          key={row.operation_key}
                          className="border-b border-[#2A3548]/60"
                          data-testid={`intake-v6-face-back-prep-operation-${row.task_key}`}
                        >
                          <td className="py-2 pr-3 text-slate-200">
                            <div>{row.label}</div>
                            <div className={`${v6.mono} text-[10px] text-slate-500`}>{row.task_key}</div>
                          </td>
                          <td className="py-2 pr-3 text-slate-300">{row.quantity.toFixed(4)}</td>
                          <td
                            className="py-2 pr-3 text-slate-300"
                            data-testid={`intake-v6-face-back-prep-pass-count-${row.task_key}`}
                          >
                            {row.pass_count}
                          </td>
                          <td className="py-2 pr-3 text-slate-300">
                            {row.unit_price != null
                              ? `${row.unit_price.toFixed(2)} ${row.currency}/ml/trecere`
                              : "—"}
                          </td>
                          <td className="py-2 pr-3 text-slate-200">
                            {formatFaceBackPrepMoney(row.cost, row.currency)}
                          </td>
                          <td className={`py-2 pr-3 ${v6.mono} text-[10px] text-slate-500`}>
                            {row.perimeter_source ?? "—"}
                          </td>
                          <td className="py-2 text-slate-400">{row.perimeter_confidence ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div
                className="mb-4 rounded border border-[#2A3548] bg-[#0A0F1A]/40 px-3 py-2 text-[11px] text-slate-300"
                data-testid="intake-v6-face-back-prep-totals"
              >
                {statusLabel ? (
                  <div className="mb-2 text-slate-400" data-testid="intake-v6-face-back-prep-operator-status">
                    Status: <strong className="text-slate-200">{statusLabel}</strong>
                  </div>
                ) : null}
                {!needsVerification ? (
                  <div>
                    Perimetru CNC:{" "}
                    <strong data-testid="intake-v6-face-back-prep-perimeter">
                      {formatFaceBackPrepPerimeterM(perimeterM)}
                    </strong>
                  </div>
                ) : null}
                <div>
                  Materiale:{" "}
                  <strong>{formatFaceBackPrepMoney(materialCost, draft.currency)}</strong>
                </div>
                <div>
                  CNC:{" "}
                  <strong data-testid="intake-v6-face-back-prep-totals-cnc">
                    {cncCost != null
                      ? formatFaceBackPrepMoney(cncCost, draft.currency)
                      : FACE_BACK_PREP_CNC_UNAVAILABLE_LABEL}
                  </strong>
                </div>
                <div>
                  Total intern draft:{" "}
                  <strong data-testid="intake-v6-face-back-prep-totals-total">
                    {totalInternal != null
                      ? formatFaceBackPrepMoney(totalInternal, draft.currency)
                      : FACE_BACK_PREP_TOTAL_UNAVAILABLE_LABEL}
                  </strong>
                </div>
                {needsVerification ? (
                  <p className="mt-2 text-[10px] text-slate-500">
                    Motiv: {FACE_BACK_PREP_VERIFICATION_REASON}
                  </p>
                ) : null}
                {ignoredRawCnc != null ? (
                  <p
                    className="mt-2 text-[10px] text-slate-500"
                    data-testid="intake-v6-face-back-prep-ignored-raw-cnc"
                  >
                    {FACE_BACK_PREP_IGNORED_RAW_CNC_LABEL}:{" "}
                    {formatFaceBackPrepMoney(ignoredRawCnc, draft.currency)}
                  </p>
                ) : null}
              </div>

              {draft.warnings.length > 0 ? (
                <div className="mb-4" data-testid="intake-v6-face-back-prep-warnings">
                  <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">
                    Avertismente
                  </h4>
                  <ul className="space-y-2 text-[11px]">
                    {draft.warnings.map((warning) => (
                      <li
                        key={`${warning.code}-${warning.message}`}
                        className="rounded border border-[#2A3548]/60 px-3 py-2 text-slate-400"
                        data-testid={`intake-v6-face-back-prep-warning-${warning.code}`}
                      >
                        <span className={v6.mono + " text-slate-500"}>{warning.code}</span>
                        <div className="text-slate-300">{warning.message}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <div className="mb-3" data-testid="intake-v6-face-back-prep-task-drafts">
                <h4 className="mb-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">
                  Preview taskuri draft — nu sunt taskuri reale
                </h4>
                <p className={`${v6.mono} text-[10px] text-slate-500`}>
                  {orderedTasks.map((task) => task.task_key).join(" → ")}
                </p>
              </div>

              <p
                className="text-[10px] text-slate-600"
                data-testid="intake-v6-face-back-prep-boundaries"
              >
                {INTAKE_V6_FACE_BACK_PREP_BOUNDARY_LINE}
              </p>
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}



