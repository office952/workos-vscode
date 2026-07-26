import { useEffect, useMemo, useRef, useState } from "react";
import ColorRegistrySelect from "@/components/workos/colorRegistry/ColorRegistrySelect";
import type { IntakeV6ArtworkFinish } from "@/lib/intakeV6/intakeV6ArtworkFinish";
import {
  faceFinishDefaultRollWidthMm,
  faceFinishNeedsV6ColorPicker,
  faceFinishNeedsRollWidth,
  faceFinishRollWidthOptions,
  oracalColorPaletteSeriesForV6Face,
  PRINT_LAMINATION_ROLL_WIDTHS_MM,
  PRINT_LAMINATION_SIDE_RETRACTION_MM,
  PRINT_LAMINATION_TOTAL_RETRACTION_MM,
} from "@/lib/intakeV6/intakeV6FaceFinishOptions";
import { artworkToReturnCant, patchArtworkFromReturnCant } from "@/lib/intakeV6/intakeV6ReturnCantBridge";
import { INTAKE_V6_OWNER_ROLE_LABEL_LOGO } from "@/lib/intakeV6/intakeV6LayerRoleOptions";
import { artworkFinishStatusLabelRo } from "@/lib/intakeV6/intakeV6OperatorVocabulary";
import { AlertTriangle, Box, CheckCircle2, ImageIcon, Layers, Palette } from "lucide-react";
import type { IntakeV6BackingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import { resolveLayerBackingMode } from "@/lib/intakeV6/intakeV4BackingMode";
import IntakeV6CardPagination, { INTAKE_V6_CARD_PAGE_SIZE } from "./IntakeV6CardPagination";
import IntakeV6ReviewBackingFinishRow from "./IntakeV6ReviewBackingFinishRow";
import IntakeV6LayerCardShell from "./IntakeV6LayerCardShell";
import IntakeV6LayerCardColumnHeader from "./IntakeV6LayerCardColumnHeader";
import IntakeV6ReturnCantFields from "./IntakeV6ReturnCantFields";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";
import { AtomsBadge, v6, v6Pilot } from "./atoms/intakeV6Presentation";
import {
  PILOT_REVIEW_FIELD_LABEL_CLASS,
  PILOT_REVIEW_SELECT_CLASS,
  REVIEW_FIELD_BLOCK_CLASS,
} from "./reviewFieldLayout";
import {
  buildArtworkCantSummaryLine,
  buildArtworkFaceSummaryLine,
  buildSpateSummaryLine,
  INTAKE_V6_ARTWORK_LAYER_ACCENT,
  artworkExecutionLabel,
} from "./artworkCardPresentation";
import type { SoldScopeFieldVisibility } from "@/lib/intakeV6/intakeV6SoldScopeVisibility";
import { resolveSoldScopeFieldVisibility } from "@/lib/intakeV6/intakeV6SoldScopeVisibility";

export const INTAKE_V6_ARTWORK_VERIFY_INSTRUCTION =
  "Confirmă fiecare Vector Logo înainte de a continua.";

function layerTestIdSuffix(key: string): string {
  return key.replace(/[^a-zA-Z0-9_-]+/g, "-");
}

function patchRows(
  rows: IntakeV6ArtworkFinish[],
  layerKey: string,
  patch: Partial<IntakeV6ArtworkFinish>,
): IntakeV6ArtworkFinish[] {
  return rows.map((row) => (row.layer_key === layerKey ? { ...row, ...patch } : row));
}

const ARTWORK_FACE_METHOD_OPTIONS = [
  { value: "none", label: "Fără finisaj — plexiglas brut" },
  { value: "oracal_641", label: "Oracal 641" },
  { value: "oracal_651", label: "Oracal 651" },
  { value: "oracal_8500", label: "Oracal 8500" },
  { value: "print_laminate", label: "Printat / Laminat" },
] as const;

type ArtworkFaceMethod = (typeof ARTWORK_FACE_METHOD_OPTIONS)[number]["value"];

function resolveArtworkFaceMethod(row: IntakeV6ArtworkFinish): ArtworkFaceMethod {
  if (row.face_personalization_method === "print_laminate") return "print_laminate";
  if (row.face_personalization_method === "oracal") {
    if (row.material_code === "ORACAL_641") return "oracal_641";
    if (row.material_code === "ORACAL_8500") return "oracal_8500";
    return "oracal_651";
  }
  if (row.face_personalization_method === "none_raw_plexi") return "none";
  if (row.execution_type === "print_laminate") return "print_laminate";
  if (row.material_code === "ORACAL_641") return "oracal_641";
  if (row.material_code === "ORACAL_8500") return "oracal_8500";
  if (row.execution_type === "cut_vinyl" || row.material_code === "ORACAL_651") return "oracal_651";
  return "none";
}

function artworkFaceMethodToFinishType(method: ArtworkFaceMethod): string {
  if (method === "oracal_641" || method === "oracal_651" || method === "oracal_8500" || method === "print_laminate") {
    return method;
  }
  return "none";
}

function artworkFaceMaterialLabel(row: IntakeV6ArtworkFinish, method: ArtworkFaceMethod): string {
  if (method === "print_laminate") return "Plexiglas + print + laminare";
  if (method === "oracal_8500") return "Plexiglas + Oracal 8500";
  if (method === "oracal_641") return "Plexiglas + Oracal 641";
  if (method === "oracal_651") return "Plexiglas + Oracal 651";
  if (row.material_code === "PLEXIGLAS_3MM_CLEAR") return "Plexiglas clar 3 mm";
  return "Plexiglas opal 3 mm";
}

function patchArtworkFaceMethod(method: ArtworkFaceMethod): Partial<IntakeV6ArtworkFinish> {
  if (method === "print_laminate") {
    return {
      execution_type: "print_laminate",
      color_mode: "polychrome",
      print_transparency: "standard",
      material_code: "ORAFOL_PRINT_LAMINATION",
      face_personalization_method: "print_laminate",
      face_roll_width_mm: faceFinishDefaultRollWidthMm("print_laminate"),
      print_roll_width_mm: faceFinishDefaultRollWidthMm("print_laminate"),
      lamination_roll_width_mm: faceFinishDefaultRollWidthMm("print_laminate"),
      roll_side_retraction_mm: PRINT_LAMINATION_SIDE_RETRACTION_MM,
      roll_total_retraction_mm: PRINT_LAMINATION_TOTAL_RETRACTION_MM,
      face_oracal_code: null,
      face_oracal_name: null,
      print_material_code: "ORAFOL_PRINT",
      lamination_material_code: "ORAFOL_LAMINATION",
      confirmed: false,
    };
  }
  if (method === "oracal_8500") {
    return {
      execution_type: "translucent_vinyl",
      color_mode: "monochrome",
      print_transparency: "standard",
      material_code: "ORACAL_8500",
      face_personalization_method: "oracal",
      face_roll_width_mm: faceFinishDefaultRollWidthMm("oracal_8500"),
      print_roll_width_mm: null,
      lamination_roll_width_mm: null,
      roll_side_retraction_mm: null,
      roll_total_retraction_mm: null,
      print_material_code: null,
      lamination_material_code: null,
      confirmed: false,
    };
  }
  if (method === "oracal_641" || method === "oracal_651") {
    return {
      execution_type: "cut_vinyl",
      color_mode: "monochrome",
      print_transparency: "standard",
      material_code: method === "oracal_641" ? "ORACAL_641" : "ORACAL_651",
      face_personalization_method: "oracal",
      face_roll_width_mm: faceFinishDefaultRollWidthMm(method),
      print_roll_width_mm: null,
      lamination_roll_width_mm: null,
      roll_side_retraction_mm: null,
      roll_total_retraction_mm: null,
      print_material_code: null,
      lamination_material_code: null,
      confirmed: false,
    };
  }
  return {
    execution_type: "none_raw_plexi",
    color_mode: "none",
    print_transparency: "standard",
    material_code: null,
    face_personalization_method: "none_raw_plexi",
    face_roll_width_mm: null,
    print_roll_width_mm: null,
    lamination_roll_width_mm: null,
    roll_side_retraction_mm: null,
    roll_total_retraction_mm: null,
    face_oracal_code: null,
    face_oracal_name: null,
    print_material_code: null,
    lamination_material_code: null,
    confirmed: false,
  };
}

function inferPositionHint(row: IntakeV6ArtworkFinish): string | null {
  const text = `${row.position_hint ?? ""} ${row.source_layer_name ?? ""} ${row.original_detected_label ?? ""} ${row.layer_name ?? ""} ${row.layer_key}`.toLowerCase();
  if (/stanga|left/.test(text)) return "stanga";
  if (/dreapta|right/.test(text)) return "dreapta";
  if (/centru|center|middle/.test(text)) return "centru";
  if (/sus|top/.test(text)) return "sus";
  if (/jos|bottom/.test(text)) return "jos";
  return row.position_hint ?? null;
}

function genericArtworkDisplayName(row: IntakeV6ArtworkFinish, index: number): string {
  if (row.display_name?.trim()) return row.display_name.trim();
  return `Vector Logo ${index + 1}`;
}

function artworkTooltip(row: IntakeV6ArtworkFinish, displayName: string, stepOneConfirmed: boolean): string {
  const details = [
    displayName,
    `source: ${row.source_layer_name ?? row.layer_key}`,
    `group_key: ${row.layer_key}`,
  ];
  const position = inferPositionHint(row);
  if (position) details.push(`position: ${position}`);
  if (typeof row.element_count === "number") details.push(`elemente: ${row.element_count}`);
  details.push(stepOneConfirmed ? "status: confirmat in Pasul 1" : "status: necesita decizie");
  return details.join("\n");
}

function artworkMetadataLine(row: IntakeV6ArtworkFinish, stepOneConfirmed: boolean): string {
  const parts = [`sursa SVG: ${row.source_layer_name ?? row.layer_key}`];
  const position = inferPositionHint(row);
  if (position) parts.push(`pozitie: ${position}`);
  if (typeof row.element_count === "number") parts.push(`elemente: ${row.element_count}`);
  parts.push(stepOneConfirmed ? "confirmat in Pasul 1" : "necesita decizie");
  return parts.join(" · ");
}

function ArtworkAlerts({
  showDecisionAlert,
  showResidualVectorNotice,
  onVerifyArtwork,
}: {
  showDecisionAlert?: boolean;
  showResidualVectorNotice?: boolean;
  onVerifyArtwork?: () => void;
  stepOneConfirmedLayerKeys?: Set<string>;
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
              className="mt-2 rounded border border-amber-400/60 px-2 py-1 text-[12px] font-semibold text-amber-50 hover:bg-amber-500/20"
              onClick={onVerifyArtwork}
              data-testid="intake-v6-artwork-verify-cta"
            >
              Verifică Vector Logo
            </button>
          ) : null}
        </div>
      ) : null}
      {showResidualVectorNotice ? (
        <div
          className="rounded border border-slate-600/60 bg-slate-800/40 px-3 py-2 text-[11px] text-slate-300"
          data-testid="intake-v6-artwork-residual-vector-notice"
        >
          Există Vector Logo neconfirmat (diferență de perimetru) — confirmă finisajele înainte de Confirmare.
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
    <div className="mb-1.5 flex items-center gap-1.5">
      <Icon className="h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden />
      <span className={v6Pilot.zoneTitle}>{title}</span>
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
  stepOneConfirmedLayerKeys,
  embedded = false,
  rasterLayerKeys: _rasterLayerKeys,
  decisionMessages: _decisionMessages,
  highlightUnconfirmed = false,
  globalBackingFallback,
  soldScopeVisibility,
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
  /** Legacy global fallback when layer row has no explicit backing_mode yet. */
  globalBackingFallback?: IntakeV6BackingMode;
  soldScopeVisibility?: SoldScopeFieldVisibility;
}) {
  const visibility = soldScopeVisibility ?? resolveSoldScopeFieldVisibility(undefined);
  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => a.layer_name.localeCompare(b.layer_name, "ro")),
    [rows],
  );
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set());
  const [localRollWidths, setLocalRollWidths] = useState<Record<string, number | null>>({});
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
        <IntakeV6LayerCardColumnHeader showFace={visibility.face} showCant={visibility.returnCant} />
        {paginatedRows.map((row, rowIndex) => {
          const faceMethod = resolveArtworkFaceMethod(row);
          const faceFinishType = artworkFaceMethodToFinishType(faceMethod);
          const showFaceColor = faceFinishNeedsV6ColorPicker(faceFinishType);
          const showRollWidth = faceFinishNeedsRollWidth(faceFinishType);
          const rollWidthOptions = faceFinishRollWidthOptions(faceFinishType);
          const selectedRollWidth =
            localRollWidths[row.layer_key] ?? faceFinishDefaultRollWidthMm(faceFinishType) ?? null;
          const stepOneConfirmed = stepOneConfirmedLayerKeys?.has(row.layer_key) === true;
          const displayName = genericArtworkDisplayName(row, pageIndex * INTAKE_V6_CARD_PAGE_SIZE + rowIndex);
          const tooltip = artworkTooltip(row, displayName, stepOneConfirmed);
          const faceSummary = buildArtworkFaceSummaryLine(row);
          const cantSummary = buildArtworkCantSummaryLine(row);
          const resolvedBacking = resolveLayerBackingMode(row.backing_mode, globalBackingFallback);
          const spateSummary = visibility.back ? buildSpateSummaryLine(resolvedBacking) : "—";
          const expanded = expandedKeys.has(row.layer_key);

          return (
            <IntakeV6LayerCardShell
              key={row.layer_key}
              cardTestId={`intake-v6-artwork-${row.layer_key}`}
              headerTestId={`intake-v6-artwork-header-${row.layer_key}`}
              expanded={expanded}
              onToggle={() => toggleExpanded(row.layer_key)}
              accentColor={INTAKE_V6_ARTWORK_LAYER_ACCENT}
              layerIcon={ImageIcon}
              layerIconClassName="text-cyan-400/80"
              layerName={displayName}
              faceSummary={visibility.face ? faceSummary : "—"}
              cantSummary={visibility.returnCant ? cantSummary : "—"}
              spateSummary={spateSummary}
              faceSummaryTestId={`intake-v6-artwork-face-summary-${row.layer_key}`}
              cantSummaryTestId={`intake-v6-artwork-cant-summary-${row.layer_key}`}
              spateSummaryTestId={`intake-v6-artwork-spate-summary-${row.layer_key}`}
              cardTitle={tooltip}
              status={(() => {
                if (!intakeV6ShowOperatorConfigStatusBadges()) return null;
                const finishStatus = artworkFinishStatusLabelRo({
                  confirmed: row.confirmed,
                  stepOneConfirmed,
                });
                if (row.confirmed) {
                  return (
                    <span data-testid={`intake-v6-artwork-confirmed-${row.layer_key}`}>
                      <AtomsBadge tone="ok">
                        <span className="inline-flex items-center gap-0.5">
                          <CheckCircle2 className="h-2.5 w-2.5" aria-hidden />
                          {finishStatus.label}
                        </span>
                      </AtomsBadge>
                    </span>
                  );
                }
                if (stepOneConfirmed) {
                  return (
                    <span data-testid={`intake-v6-artwork-step1-badge-${row.layer_key}`}>
                      <AtomsBadge tone="pending">
                        <span className="inline-flex items-center gap-0.5">
                          <AlertTriangle className="h-2.5 w-2.5" aria-hidden />
                          {finishStatus.label}
                        </span>
                      </AtomsBadge>
                    </span>
                  );
                }
                return (
                  <AtomsBadge tone="pending">
                    <span className="inline-flex items-center gap-0.5">
                      <AlertTriangle className="h-2.5 w-2.5" aria-hidden />
                      {finishStatus.label}
                    </span>
                  </AtomsBadge>
                );
              })()}
              expandedChildren={
                <>
                  {visibility.face ? (
                    <section
                      className={v6Pilot.anatomyZone}
                      data-testid={`intake-v6-artwork-face-zone-${row.layer_key}`}
                    >
                      <ZoneTitle icon={Palette} title="Față" />
                      <div className={`${REVIEW_FIELD_BLOCK_CLASS} space-y-2`}>
                        <label className={REVIEW_FIELD_BLOCK_CLASS}>
                          <span className={PILOT_REVIEW_FIELD_LABEL_CLASS}>Metodă personalizare față</span>
                          <select
                            className={PILOT_REVIEW_SELECT_CLASS}
                            value={resolveArtworkFaceMethod(row)}
                            onChange={(event) => {
                              const nextMethod = event.target.value as ArtworkFaceMethod;
                              const nextFinishType = artworkFaceMethodToFinishType(nextMethod);
                              const defaultRollWidth = faceFinishDefaultRollWidthMm(nextFinishType);
                              setLocalRollWidths((current) => ({
                                ...current,
                                [row.layer_key]: defaultRollWidth,
                              }));
                              onChange(
                                patchRows(
                                  rows,
                                  row.layer_key,
                                  patchArtworkFaceMethod(nextMethod),
                                ),
                              );
                            }}
                            data-testid={`intake-v6-artwork-face-method-${row.layer_key}`}
                          >
                            {ARTWORK_FACE_METHOD_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </label>
                        <p
                          className={v6Pilot.helper}
                          data-testid={`intake-v6-artwork-face-material-${row.layer_key}`}
                        >
                          Material față: {artworkFaceMaterialLabel(row, faceMethod)}
                        </p>
                        <p
                          className={v6Pilot.helper}
                          data-testid={`intake-v6-artwork-symbolic-color-note-${row.layer_key}`}
                        >
                          Pata de culoare este un indicator simbolic, nu randare print/logo.
                        </p>
                        <IntakeV6TechnicalDetailsAccordion
                          title="Detalii tehnice"
                          defaultOpen={false}
                          testId={`intake-v6-artwork-source-metadata-${row.layer_key}`}
                          className="mt-1"
                        >
                          <p className={v6Pilot.technical}>{artworkMetadataLine(row, stepOneConfirmed)}</p>
                          <p className={`mt-1 font-mono ${v6Pilot.technical}`}>
                            group_key: {row.layer_key}
                          </p>
                        </IntakeV6TechnicalDetailsAccordion>
                        {showRollWidth ? (
                          <label className={REVIEW_FIELD_BLOCK_CLASS}>
                            <span className={PILOT_REVIEW_FIELD_LABEL_CLASS}>Rolă (mm)</span>
                            <select
                              className={PILOT_REVIEW_SELECT_CLASS}
                              value={selectedRollWidth ?? ""}
                              onChange={(event) => {
                                const raw = event.target.value;
                                const value = raw ? Number(raw) : null;
                                setLocalRollWidths((current) => ({
                                  ...current,
                                  [row.layer_key]: value,
                                }));
                                if (faceMethod === "print_laminate") {
                                  onChange(
                                    patchRows(rows, row.layer_key, {
                                      face_roll_width_mm: value,
                                      print_roll_width_mm: value,
                                      lamination_roll_width_mm: value,
                                      roll_side_retraction_mm: PRINT_LAMINATION_SIDE_RETRACTION_MM,
                                      roll_total_retraction_mm: PRINT_LAMINATION_TOTAL_RETRACTION_MM,
                                      confirmed: false,
                                    }),
                                  );
                                } else if (faceMethod !== "none") {
                                  onChange(
                                    patchRows(rows, row.layer_key, {
                                      face_roll_width_mm: value,
                                      confirmed: false,
                                    }),
                                  );
                                }
                              }}
                              data-testid={`intake-v6-artwork-roll-width-${row.layer_key}`}
                            >
                              <option value="">—</option>
                              {rollWidthOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                            {faceMethod === "print_laminate" ? (
                              <span
                                className={`${v6Pilot.helper} mt-1 block`}
                                data-testid={`intake-v6-artwork-roll-retraction-${row.layer_key}`}
                              >
                                Rola print/laminare: {PRINT_LAMINATION_ROLL_WIDTHS_MM.join(" / ")} mm. Util dupa
                                retragere:{" "}
                                {PRINT_LAMINATION_ROLL_WIDTHS_MM.map(
                                  (width) => width - PRINT_LAMINATION_TOTAL_RETRACTION_MM,
                                ).join(" / ")}{" "}
                                mm ({PRINT_LAMINATION_SIDE_RETRACTION_MM} + {PRINT_LAMINATION_SIDE_RETRACTION_MM}{" "}
                                mm).
                              </span>
                            ) : null}
                          </label>
                        ) : null}
                        {showFaceColor ? (
                          <ColorRegistrySelect
                            reviewAlign
                            label="Culoare Oracal față"
                            valueCode={row.face_oracal_code ?? null}
                            filter={{
                              system: "ORACAL",
                              series: oracalColorPaletteSeriesForV6Face(faceFinishType),
                              usageScope: "face_vinyl",
                            }}
                            onChange={(item) =>
                              onChange(
                                patchRows(rows, row.layer_key, {
                                  face_oracal_code: item?.code ?? null,
                                  face_oracal_name: item?.name ?? null,
                                  confirmed: false,
                                }),
                              )
                            }
                            testId={`intake-v6-artwork-face-color-${row.layer_key}`}
                          />
                        ) : null}
                        <p
                          className="sr-only"
                          data-testid={`intake-v6-artwork-execution-${row.layer_key}`}
                        >
                          {artworkExecutionLabel(row)}
                        </p>
                        {stepOneConfirmed && !row.confirmed ? (
                          <p
                            className="inline-flex h-8 items-center rounded border border-emerald-500/30 bg-emerald-500/10 px-2.5 text-[12px] font-semibold text-emerald-200"
                            data-testid={`intake-v6-artwork-step1-confirmed-${row.layer_key}`}
                          >
                            Vector Logo confirmat in Pasul 1
                          </p>
                        ) : (
                          <button
                            type="button"
                            className={`inline-flex h-8 items-center gap-1.5 rounded border px-2.5 text-[12px] font-semibold ${
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
                                {INTAKE_V6_OWNER_ROLE_LABEL_LOGO} confirmat
                              </>
                            ) : (
                              `Confirm ${INTAKE_V6_OWNER_ROLE_LABEL_LOGO.toLowerCase()}`
                            )}
                          </button>
                        )}
                      </div>
                    </section>
                  ) : null}

                  {visibility.returnCant ? (
                    <section
                      className={v6Pilot.anatomyZone}
                      data-testid={`intake-v6-artwork-cant-${row.layer_key}`}
                    >
                      <ZoneTitle icon={Box} title="Cant" />
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
                    </section>
                  ) : null}

                  {visibility.back ? (
                    <section
                      className={v6Pilot.anatomyZone}
                      data-testid={`intake-v6-review-backing-finish-integration-${row.layer_key}`}
                    >
                      <ZoneTitle icon={Layers} title="Spate" />
                      <IntakeV6ReviewBackingFinishRow
                        embedded
                        testIdSuffix={layerTestIdSuffix(row.layer_key)}
                        backingMode={resolvedBacking}
                        onBackingChange={(mode) =>
                          onChange(
                            patchRows(rows, row.layer_key, {
                              backing_mode: mode,
                              confirmed: row.confirmed,
                            }),
                          )
                        }
                      />
                    </section>
                  ) : null}
                </>
              }
            />
          );
        })}
      </div>
    </>
  );

  if (embedded) {
    return (
      <div className={`${v6.cardCompact} mt-2 !p-3`} data-testid="intake-v6-artwork-finishes">
        <p className={`mb-2 ${v6Pilot.clusterTitle}`}>{INTAKE_V6_OWNER_ROLE_LABEL_LOGO}</p>
        {cards}
      </div>
    );
  }

  return (
    <div className={`${v6.cardCompact} mb-3 !p-3`} data-testid="intake-v6-artwork-finishes">
      <p className={`mb-2 ${v6Pilot.clusterTitle}`}>{INTAKE_V6_OWNER_ROLE_LABEL_LOGO}</p>
      {cards}
    </div>
  );
}
