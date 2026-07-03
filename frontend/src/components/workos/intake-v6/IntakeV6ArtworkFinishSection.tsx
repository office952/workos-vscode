import { useEffect, useMemo, useRef, useState } from "react";
import type { IntakeV6ArtworkFinish } from "@/lib/intakeV6/intakeV6ArtworkFinish";
import { artworkToReturnCant, patchArtworkFromReturnCant } from "@/lib/intakeV6/intakeV6ReturnCantBridge";
import { AlertTriangle, Box, CheckCircle2, ImageIcon, Palette } from "lucide-react";
import IntakeV6CardPagination, { INTAKE_V6_CARD_PAGE_SIZE } from "./IntakeV6CardPagination";
import IntakeV6LayerCardCollapsedHeader from "./IntakeV6LayerCardCollapsedHeader";
import IntakeV6LayerCardColumnHeader from "./IntakeV6LayerCardColumnHeader";
import IntakeV6ReturnCantFields from "./IntakeV6ReturnCantFields";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";
import {
  REVIEW_CANT_COLUMN_CLASS,
  REVIEW_FACE_COLUMN_CLASS,
  REVIEW_FIELD_BLOCK_CLASS,
  REVIEW_FIELD_LABEL_CLASS,
  REVIEW_LAYER_CARD_GRID_CLASS,
} from "./reviewFieldLayout";
import {
  buildArtworkCantSummaryLine,
  buildArtworkFaceSummaryLine,
  INTAKE_V6_ARTWORK_LAYER_ACCENT,
  artworkExecutionLabel,
} from "./artworkCardPresentation";

export const INTAKE_V6_ARTWORK_VERIFY_INSTRUCTION =
  "Confirmă fiecare vector atipic / logo înainte de a continua.";

function patchRows(
  rows: IntakeV6ArtworkFinish[],
  layerKey: string,
  patch: Partial<IntakeV6ArtworkFinish>,
): IntakeV6ArtworkFinish[] {
  return rows.map((row) => (row.layer_key === layerKey ? { ...row, ...patch } : row));
}

function ArtworkAlerts({
  showDecisionAlert,
  showResidualVectorNotice,
  onVerifyArtwork,
}: {
  showDecisionAlert?: boolean;
  showResidualVectorNotice?: boolean;
  onVerifyArtwork?: () => void;
}) {
  if (!showDecisionAlert && !showResidualVectorNotice) return null;
  return (
    <div className="mb-2 space-y-2">
      {showDecisionAlert ? (
        <div
          className="rounded border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100"
          data-testid="intake-v6-artwork-verify-instruction"
        >
          <p>{INTAKE_V6_ARTWORK_VERIFY_INSTRUCTION}</p>
          {onVerifyArtwork ? (
            <button
              type="button"
              className="mt-2 rounded border border-amber-400/60 px-2 py-1 text-[10px] font-semibold text-amber-50 hover:bg-amber-500/20"
              onClick={onVerifyArtwork}
              data-testid="intake-v6-artwork-verify-cta"
            >
              Verifică artwork
            </button>
          ) : null}
        </div>
      ) : null}
      {showResidualVectorNotice ? (
        <div
          className="rounded border border-slate-600/60 bg-slate-800/40 px-3 py-2 text-[11px] text-slate-300"
          data-testid="intake-v6-artwork-residual-vector-notice"
        >
          Există vector rezidual neclasificat — verifică stratul înainte de confirmare.
        </div>
      ) : null}
    </div>
  );
}

function ZoneTitle({
  icon: Icon,
  title,
}: {
  icon: typeof Palette;
  title: string;
}) {
  return (
    <div className="mb-1 flex items-center gap-1">
      <Icon className="h-3 w-3 shrink-0 text-slate-500" aria-hidden />
      <span className={v6.zoneTitle}>{title}</span>
    </div>
  );
}

export default function IntakeV6ArtworkFinishSection({
  rows,
  onChange,
  allowedReturnDepthMm,
  showDecisionAlert,
  showResidualVectorNotice,
  onVerifyArtwork,
  embedded = false,
  rasterLayerKeys: _rasterLayerKeys,
  decisionMessages: _decisionMessages,
  highlightUnconfirmed = false,
}: {
  rows: IntakeV6ArtworkFinish[];
  onChange: (rows: IntakeV6ArtworkFinish[]) => void;
  allowedReturnDepthMm?: readonly number[];
  showDecisionAlert?: boolean;
  showResidualVectorNotice?: boolean;
  onVerifyArtwork?: () => void;
  embedded?: boolean;
  rasterLayerKeys?: Set<string>;
  decisionMessages?: string[];
  highlightUnconfirmed?: boolean;
}) {
  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => a.layer_name.localeCompare(b.layer_name, "ro")),
    [rows],
  );
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set());
  const highlightAppliedRef = useRef(false);
  const [pageIndex, setPageIndex] = useState(0);
  const pageCount = Math.max(1, Math.ceil(sortedRows.length / INTAKE_V6_CARD_PAGE_SIZE));
  const paginatedRows = useMemo(() => {
    if (sortedRows.length <= INTAKE_V6_CARD_PAGE_SIZE) return sortedRows;
    const start = pageIndex * INTAKE_V6_CARD_PAGE_SIZE;
    return sortedRows.slice(start, start + INTAKE_V6_CARD_PAGE_SIZE);
  }, [sortedRows, pageIndex]);

  useEffect(() => {
    setPageIndex((current) => Math.min(current, pageCount - 1));
  }, [pageCount]);

  useEffect(() => {
    if (!highlightUnconfirmed) {
      highlightAppliedRef.current = false;
      return;
    }
    if (highlightAppliedRef.current) return;
    const pendingKeys = sortedRows.filter((row) => !row.confirmed).map((row) => row.layer_key);
    if (pendingKeys.length === 0) return;
    highlightAppliedRef.current = true;
    setExpandedKeys(new Set(pendingKeys));
  }, [highlightUnconfirmed, sortedRows]);

  if (sortedRows.length === 0) return null;

  function toggleExpanded(layerKey: string) {
    setExpandedKeys((current) => {
      const next = new Set(current);
      if (next.has(layerKey)) {
        next.delete(layerKey);
      } else {
        next.add(layerKey);
      }
      return next;
    });
  }

  const cards = (
    <>
      <ArtworkAlerts
        showDecisionAlert={showDecisionAlert}
        showResidualVectorNotice={showResidualVectorNotice}
        onVerifyArtwork={onVerifyArtwork}
      />
      <div className="space-y-1.5" data-testid="intake-v6-artwork-layer-cards">
        <IntakeV6CardPagination
          pageIndex={pageIndex}
          pageCount={pageCount}
          totalItems={sortedRows.length}
          onPageChange={setPageIndex}
          testId="intake-v6-review-artwork-pagination"
        />
        <IntakeV6LayerCardColumnHeader faceLabel="Vector Atipic" />
        {paginatedRows.map((row) => {
          const faceSummary = buildArtworkFaceSummaryLine(row);
          const cantSummary = buildArtworkCantSummaryLine(row);
          const expanded = expandedKeys.has(row.layer_key);

          return (
            <div
              key={row.layer_key}
              className="overflow-hidden rounded-md border border-[#2A3548] bg-[#0A0F1A]/55"
              style={{ borderLeftWidth: 3, borderLeftColor: INTAKE_V6_ARTWORK_LAYER_ACCENT }}
              data-testid={`intake-v6-artwork-${row.layer_key}`}
              data-layer-card-expanded={expanded ? "true" : "false"}
            >
              <button
                type="button"
                className="min-h-[40px] w-full min-w-0 text-left transition hover:bg-[#111827]/40"
                onClick={() => toggleExpanded(row.layer_key)}
                data-testid={`intake-v6-artwork-header-${row.layer_key}`}
                aria-expanded={expanded}
              >
                <IntakeV6LayerCardCollapsedHeader
                  layerIcon={ImageIcon}
                  layerIconClassName="text-cyan-400/80"
                  accentColor={INTAKE_V6_ARTWORK_LAYER_ACCENT}
                  layerName={row.layer_name}
                  faceSummary={faceSummary}
                  cantSummary={cantSummary}
                  faceSummaryTestId={`intake-v6-artwork-face-summary-${row.layer_key}`}
                  cantSummaryTestId={`intake-v6-artwork-cant-summary-${row.layer_key}`}
                  expanded={expanded}
                  status={
                    row.confirmed ? (
                      <span data-testid={`intake-v6-artwork-confirmed-${row.layer_key}`}>
                        <AtomsBadge tone="ok">
                          <span className="inline-flex items-center gap-0.5">
                            <CheckCircle2 className="h-2.5 w-2.5" aria-hidden />
                            OK
                          </span>
                        </AtomsBadge>
                      </span>
                    ) : (
                      <AtomsBadge tone="pending">
                        <span className="inline-flex items-center gap-0.5">
                          <AlertTriangle className="h-2.5 w-2.5" aria-hidden />
                          Lipsă
                        </span>
                      </AtomsBadge>
                    )
                  }
                />
              </button>

              {expanded ? (
                <div className={REVIEW_LAYER_CARD_GRID_CLASS}>
                  <div className={REVIEW_FACE_COLUMN_CLASS}>
                    <ZoneTitle icon={Palette} title="Vector Atipic / față" />
                  </div>
                  <div className={REVIEW_CANT_COLUMN_CLASS}>
                    <ZoneTitle icon={Box} title="Cant" />
                  </div>

                  <div
                    className={REVIEW_FACE_COLUMN_CLASS}
                    data-testid={`intake-v6-artwork-face-zone-${row.layer_key}`}
                  >
                    <div className={`${REVIEW_FIELD_BLOCK_CLASS} space-y-2 text-[11px]`}>
                      <div>
                        <span className={REVIEW_FIELD_LABEL_CLASS}>Execuție</span>
                        <p
                          className="font-medium text-slate-200"
                          data-testid={`intake-v6-artwork-execution-${row.layer_key}`}
                        >
                          {artworkExecutionLabel(row)}
                        </p>
                      </div>
                      <div>
                        <span className={REVIEW_FIELD_LABEL_CLASS}>Policromie</span>
                        <p
                          className="font-medium text-slate-200"
                          data-testid={`intake-v6-artwork-color-mode-${row.layer_key}`}
                        >
                          {row.color_mode === "polychrome" ? "Da" : "Nu"}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <label className="flex items-center gap-1.5 text-slate-300">
                          <input
                            type="checkbox"
                            className="rounded border-slate-600"
                            checked={row.print_transparency === "translucent"}
                            onChange={(event) => {
                              onChange(
                                patchRows(rows, row.layer_key, {
                                  print_transparency: event.target.checked ? "translucent" : "standard",
                                  confirmed: row.confirmed ? row.confirmed : false,
                                }),
                              );
                            }}
                            data-testid={`intake-v6-artwork-translucent-${row.layer_key}`}
                          />
                          Translucid
                        </label>
                        <label className="flex items-center gap-1.5 text-slate-300">
                          <input
                            type="checkbox"
                            className="rounded border-slate-600"
                            checked={row.print_transparency === "transparent"}
                            onChange={(event) => {
                              onChange(
                                patchRows(rows, row.layer_key, {
                                  print_transparency: event.target.checked ? "transparent" : "standard",
                                  confirmed: row.confirmed ? row.confirmed : false,
                                }),
                              );
                            }}
                            data-testid={`intake-v6-artwork-transparent-${row.layer_key}`}
                          />
                          Transparent
                        </label>
                      </div>
                      <button
                        type="button"
                        className={`inline-flex h-8 items-center gap-1.5 rounded border px-2.5 text-[10px] font-semibold ${
                          row.confirmed
                            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
                            : "border-sky-500/40 bg-sky-500/15 text-sky-100 hover:bg-sky-500/25"
                        }`}
                        onClick={() => {
                          if (!row.confirmed) {
                            onChange(patchRows(rows, row.layer_key, { confirmed: true }));
                          }
                        }}
                        disabled={row.confirmed}
                        data-testid={`intake-v6-artwork-confirm-${row.layer_key}`}
                      >
                        {row.confirmed ? (
                          <>
                            <CheckCircle2 className="h-3 w-3" aria-hidden />
                            Vector Atipic confirmat
                          </>
                        ) : (
                          "Confirm vector atipic"
                        )}
                      </button>
                    </div>
                  </div>

                  <div
                    className={REVIEW_CANT_COLUMN_CLASS}
                    data-testid={`intake-v6-artwork-cant-${row.layer_key}`}
                  >
                    <IntakeV6ReturnCantFields
                      layout="review"
                      compact
                      idPrefix={`v6-artwork-${row.layer_key}`}
                      returnCant={artworkToReturnCant(row)}
                      onReturnChange={(cant) => {
                        const cantPatch = patchArtworkFromReturnCant(cant);
                        onChange(
                          patchRows(rows, row.layer_key, {
                            ...cantPatch,
                            confirmed: row.confirmed,
                          }),
                        );
                      }}
                      testIdPrefix={`intake-v6-artwork-return-${row.layer_key}`}
                      allowedReturnDepthMm={allowedReturnDepthMm}
                    />
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </>
  );

  if (embedded) {
    return (
      <div className={`${v6.cardCompact} mt-2 !p-3`} data-testid="intake-v6-artwork-finishes">
        <p className="mb-2 text-[10px] font-semibold text-slate-400">Vector Atipic / logo</p>
        {cards}
      </div>
    );
  }

  return (
    <div className={`${v6.cardCompact} mb-3 !p-3`} data-testid="intake-v6-artwork-finishes">
      <p className="mb-2 text-[10px] font-semibold text-slate-400">Vector Atipic / logo</p>
      {cards}
    </div>
  );
}
