import type { IntakeV6SheetQuoteMaterialCandidates } from "@/lib/intakeV6/intakeV6Api";
import type { IntakeV6SheetFootprintOverride } from "@/lib/intakeV6/intakeV6SheetFootprintOverride";
import {
  buildMaterialQuoteReviewSnapshot,
  formatMaterialQuoteReviewSnapshotText,
} from "@/lib/intakeV6/intakeV6MaterialQuoteReviewSnapshot";
import {
  formatActiveManualReviewReasons,
  formatSheetQuoteSourceLabel,
  formatSqmDisplay,
  isFreshSvgSnapshotAfterReanalysis,
  isStaleSvgSnapshotReview,
  resolveSheetQuoteReviewStatus,
  SHEET_QUOTE_FRESH_SNAPSHOT_OWNER_NOTE,
  SHEET_QUOTE_MANUAL_REVIEW_CTA_STEPS,
  SHEET_QUOTE_REVIEW_STATUS_LABELS,
} from "@/lib/intakeV6/intakeV6SheetQuoteReviewDisplay";
import IntakeV6SheetFootprintOverridePanel from "./IntakeV6SheetFootprintOverridePanel";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";

const STATUS_STYLES = {
  ok_auto: "border-emerald-500/40 bg-emerald-500/10 text-emerald-100",
  review_recommended: "border-amber-500/40 bg-amber-500/10 text-amber-100",
  review_required: "border-red-500/40 bg-red-500/10 text-red-100",
} as const;

export default function IntakeV6SheetQuoteReviewPanel({
  candidates,
  workspaceId,
  workspaceTitle,
  templateCode,
  sheetQuoteOverride,
  onSheetFootprintOverrideSaved,
}: {
  candidates: IntakeV6SheetQuoteMaterialCandidates;
  workspaceId?: string;
  workspaceTitle?: string | null;
  templateCode?: string | null;
  sheetQuoteOverride?: IntakeV6SheetFootprintOverride | null;
  onSheetFootprintOverrideSaved?: () => void;
}) {
  const status = resolveSheetQuoteReviewStatus(candidates);
  const reviewReasons = formatActiveManualReviewReasons(candidates.manual_review_reason, candidates);
  const appliedToQuote = candidates.selection?.is_applied_to_quote === true;
  const staleSnapshot = isStaleSvgSnapshotReview(candidates);
  const freshSnapshot = isFreshSvgSnapshotAfterReanalysis(candidates);

  async function handleCopyMaterialReviewSummary() {
    if (!workspaceId) return;
    const snapshot = buildMaterialQuoteReviewSnapshot({
      intakeId: workspaceId,
      template: templateCode,
      candidates,
      sheetQuoteOverride,
    });
    const text = formatMaterialQuoteReviewSnapshotText(snapshot, workspaceTitle);
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard may be unavailable in test/HTTP contexts — ignore silently.
    }
  }

  return (
    <div className="mt-4 space-y-3 border-t border-wo-border-strong pt-4" data-testid="intake-v6-sheet-quote-review">
      <div>
        <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-400">
          Material quote review — estimare internă (nu preț final)
        </h4>
        <p className="mt-1 text-[10px] text-slate-500">
          Candidați de arie pentru review intern. Nu consumă stoc, nu trimite în CostEngine, nu
          schimbă oferta comercială finală.
        </p>
      </div>

      <div
        className={`rounded border px-3 py-2 text-[11px] ${STATUS_STYLES[status]}`}
        data-testid="intake-v6-sheet-quote-status"
      >
        <strong>Status review material placă: {SHEET_QUOTE_REVIEW_STATUS_LABELS[status]}</strong>
        {reviewReasons.length > 0 ? (
          <ul className="mt-1 space-y-0.5 text-[10px] opacity-90">
            {reviewReasons.map((reason) => (
              <li key={reason}>• {reason}</li>
            ))}
          </ul>
        ) : null}
      </div>

      {staleSnapshot ? (
        <div
          className="rounded border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-[10px] text-amber-100"
          data-testid="intake-v6-stale-snapshot-warning"
        >
          <p className="font-semibold text-amber-200">Snapshot SVG vechi detectat</p>
          <p className="mt-1 text-slate-300">
            Re-analiza poate elimina geometrie defs/clipPath veche. Această acțiune trebuie
            confirmată de owner — nu se execută automat din această pagină.
          </p>
        </div>
      ) : null}

      {freshSnapshot && candidates.requires_manual_review ? (
        <div
          className="rounded border border-emerald-500/30 bg-emerald-500/5 px-3 py-2 text-[10px] text-emerald-100"
          data-testid="intake-v6-fresh-snapshot-note"
        >
          <p className="font-semibold text-emerald-200">Snapshot SVG actualizat</p>
          <p className="mt-1 text-slate-300">{SHEET_QUOTE_FRESH_SNAPSHOT_OWNER_NOTE}</p>
        </div>
      ) : null}

      {candidates.requires_manual_review ? (
        <div
          className="rounded border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-[10px] text-amber-100"
          data-testid="intake-v6-sheet-quote-manual-review-cta"
        >
          <p className="font-semibold uppercase tracking-wide text-amber-200">Pas recomandat</p>
          <ol className="mt-1 list-decimal space-y-0.5 pl-4 text-slate-300">
            {SHEET_QUOTE_MANUAL_REVIEW_CTA_STEPS.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      ) : null}

      <p
        className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2 text-[11px] text-slate-300"
        data-testid="intake-v6-sheet-quote-applied-readable"
      >
        Aplicat în ofertă finală: {appliedToQuote ? "Da" : "Nu"}
      </p>

      <IntakeV6TechnicalDetailsAccordion
        title="Detalii tehnice — candidați material"
        testId="intake-v6-sheet-quote-technical"
      >
        <div
          className="mb-3 rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2 text-[11px] text-slate-300"
          data-testid="intake-v6-sheet-quote-main-summary"
        >
          <p className="font-semibold uppercase tracking-wide text-slate-400">Material review intern</p>
          <p className="mt-1" data-testid="intake-v6-sheet-quote-selected-area-readable">
            Arie selectată pentru review:{" "}
            {formatSqmDisplay(
              candidates.selection?.final_area_sqm ?? candidates.selected_quote_sheet_area_sqm,
            )}
          </p>
          <p data-testid="intake-v6-sheet-quote-source-readable">
            Sursă calcul:{" "}
            {formatSheetQuoteSourceLabel(
              candidates.selection?.selected_source ?? candidates.selected_quote_sheet_area_source,
            )}
          </p>
        </div>
        <div
          className="space-y-1 text-[10px] text-slate-400"
          data-testid="intake-v6-sheet-quote-policy-table"
        >
          <p className="font-semibold uppercase tracking-wide text-slate-500">
            Candidați material placă
          </p>
          <ul className="space-y-0.5">
            <li>Aria pieselor eligibile: {formatSqmDisplay(candidates.eligible_face_area_sqm)}</li>
            <li>
              Sumă dreptunghiuri piese plasate (placement bbox):{" "}
              {formatSqmDisplay(candidates.placement_footprint_face_sqm)} — diagnostic, nu preț final
            </li>
            <li>Child part bbox sum: {formatSqmDisplay(candidates.child_part_bbox_sum_sqm)}</li>
            <li>
              Recommended auto (
              {candidates.recommended_auto_candidate?.confidence ?? "—"}, buffer{" "}
              {candidates.recommended_auto_candidate?.buffer_percent ?? 5}%):{" "}
              {formatSqmDisplay(candidates.recommended_auto_candidate?.area_sqm)}
            </li>
            <li>Design-space union bbox: {formatSqmDisplay(candidates.design_space_union_bbox_sqm)}</li>
            <li>Face union bbox (shelf): {formatSqmDisplay(candidates.face_union_bbox_sqm)}</li>
            <li>
              Auto shelf occupied:{" "}
              {formatSqmDisplay(
                candidates.nesting_shelf_occupied_sqm ?? candidates.layout_occupied_area_sqm,
              )}{" "}
              — diagnostic shelf, nu consum ofertat automat
            </li>
            <li>
              Aria plăcii disponibile: {formatSqmDisplay(candidates.full_sheet_allocation_sqm)} — nu
              este consum ofertat automat
            </li>
            {candidates.orphan_defs_split_placement_sqm != null ? (
              <li className="text-amber-200">
                Orphan defs/clipPath (exclus din face):{" "}
                {formatSqmDisplay(candidates.orphan_defs_split_placement_sqm)} — semnal snapshot stale
              </li>
            ) : null}
            <li data-testid="intake-v6-sheet-quote-selected-current">
              Arie selectată pentru review (detaliu tehnic):{" "}
              {formatSheetQuoteSourceLabel(
                candidates.selection?.selected_source ?? candidates.selected_quote_sheet_area_source,
              )}{" "}
              ({formatSqmDisplay(
                candidates.selection?.final_area_sqm ?? candidates.selected_quote_sheet_area_sqm,
              )}
              )
            </li>
          </ul>
        </div>

        {workspaceId ? (
          <div className="mt-4" data-testid="intake-v6-sheet-quote-operator-decision">
            <IntakeV6SheetFootprintOverridePanel
              workspaceId={workspaceId}
              candidates={candidates}
              initialOverride={sheetQuoteOverride}
              onSaved={onSheetFootprintOverrideSaved}
            />
          </div>
        ) : null}
      </IntakeV6TechnicalDetailsAccordion>

      {workspaceId ? (
        <button
          type="button"
          className="rounded border border-wo-border-strong bg-wo-surface-inset/60 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-slate-300 hover:bg-wo-surface-raised"
          data-testid="intake-v6-copy-material-review-summary"
          onClick={() => void handleCopyMaterialReviewSummary()}
        >
          Copiază rezumat material review
        </button>
      ) : null}
    </div>
  );
}



