import ColorRegistrySelect from "@/components/workos/colorRegistry/ColorRegistrySelect";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import { resolveIntakeV6LetterGroupDisplayLabel } from "@/lib/intakeV6/intakeV6LayerDisplayLabel";
import { finishLetterCardStatusLabelRo } from "@/lib/intakeV6/intakeV6OperatorVocabulary";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import {
  faceFinishNeedsColorPicker,
  faceFinishNeedsRollWidth,
  faceFinishRollWidthOptions,
  normalizeFaceVinylRollWidthMm,
  oracalColorPaletteSeriesForFace,
  PRINT_LAMINATION_ROLL_WIDTHS_MM,
  PRINT_LAMINATION_SIDE_RETRACTION_MM,
  PRINT_LAMINATION_TOTAL_RETRACTION_MM,
} from "@/lib/intakeV6/intakeV6FaceFinishOptions";
import { resolveLetterGroupFaceFinishOptions } from "@/lib/intakeV6/intakeV6LetterGroupFaceFinishOptions";
import {
  letterGroupToReturnCant,
  patchLetterGroupFromReturnCant,
} from "@/lib/intakeV6/intakeV6ReturnCantBridge";
import { resolveIntakeV6ReturnFinishUiOption } from "@/lib/intakeV6/intakeV6ReturnFinishOptions";
import type { IntakeV6BackingMode } from "@/lib/intakeV6/intakeV6BackingMode";
import { resolveLayerBackingMode } from "@/lib/intakeV6/intakeV4BackingMode";
import { AlertTriangle, Box, CheckCircle2, Layers, PanelTop, Ruler } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import IntakeV6CardPagination, { INTAKE_V6_CARD_PAGE_SIZE } from "./IntakeV6CardPagination";
import IntakeV6LayerCardShell from "./IntakeV6LayerCardShell";
import IntakeV6ReviewBackingFinishRow from "./IntakeV6ReviewBackingFinishRow";
import IntakeV6ReturnCantFields from "./IntakeV6ReturnCantFields";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";
import { AtomsBadge, v6, v6Pilot } from "./atoms/intakeV6Presentation";
import {
  PILOT_REVIEW_FIELD_LABEL_CLASS,
  PILOT_REVIEW_SELECT_CLASS,
  REVIEW_COLOR_ROW_SHELL_CLASS,
  REVIEW_FIELD_BLOCK_CLASS,
} from "./reviewFieldLayout";
import {
  buildCantSummaryLine,
  buildFaceSummaryLine,
  buildSpateSummaryLine,
  layerAccentColor,
  resolveLayerCardStatus,
} from "./letterGroupCardPresentation";
import type { SoldScopeFieldVisibility } from "@/lib/intakeV6/intakeV6SoldScopeVisibility";
import { resolveSoldScopeFieldVisibility } from "@/lib/intakeV6/intakeV6SoldScopeVisibility";
import {
  copyFirstCantSettingsToAllGroups,
  patchLetterGroupFinishes,
} from "./letterGroupFinishSectionHelpers";
import type { LettersCanonicalFieldLabels } from "@/lib/intakeV6/lettersCanonicalFormContract";

function layerTestIdSuffix(key: string): string {
  return key.replace(/[^a-zA-Z0-9_-]+/g, "-");
}

function ZoneTitle({
  icon: Icon,
  title,
}: {
  icon: typeof PanelTop;
  title: string;
}) {
  return (
    <div className="mb-1.5 flex items-center gap-1.5">
      <Icon className="h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden />
      <span className={v6Pilot.zoneTitle}>{title}</span>
    </div>
  );
}

export default function IntakeV6ReviewLetterGroupsSection({
  groups,
  onChange,
  faceFinishOptions,
  allowedReturnDepthMm,
  globalBackingFallback,
  soldScopeVisibility,
  fieldLabels,
  analyzerReport = null,
}: {
  groups: IntakeV6LetterGroupFinish[];
  onChange: (groups: IntakeV6LetterGroupFinish[]) => void;
  faceFinishOptions?: readonly { value: string; label: string }[];
  allowedReturnDepthMm?: readonly number[];
  globalBackingFallback?: IntakeV6BackingMode;
  soldScopeVisibility?: SoldScopeFieldVisibility;
  fieldLabels?: Partial<LettersCanonicalFieldLabels> | null;
  /** Presentation-only — never mutates persisted layer_name */
  analyzerReport?: SvgAnalysisCoreReport | null;
}) {
  const visibility = soldScopeVisibility ?? resolveSoldScopeFieldVisibility(undefined);
  const effectiveFaceOptions = resolveLetterGroupFaceFinishOptions(faceFinishOptions);
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set());
  const [pageIndex, setPageIndex] = useState(0);
  const pageCount = Math.max(1, Math.ceil(groups.length / INTAKE_V6_CARD_PAGE_SIZE));
  const paginatedGroups = useMemo(() => {
    if (groups.length <= INTAKE_V6_CARD_PAGE_SIZE) return groups;
    const start = pageIndex * INTAKE_V6_CARD_PAGE_SIZE;
    return groups.slice(start, start + INTAKE_V6_CARD_PAGE_SIZE);
  }, [groups, pageIndex]);

  useEffect(() => {
    setPageIndex((current) => Math.min(current, pageCount - 1));
  }, [pageCount]);

  if (groups.length === 0) return null;

  function patchGroup(groupKey: string, patch: Partial<IntakeV6LetterGroupFinish>) {
    onChange(patchLetterGroupFinishes(groups, groupKey, patch));
  }

  function toggleExpanded(groupKey: string) {
    setExpandedKeys((current) => {
      const next = new Set(current);
      if (next.has(groupKey)) {
        next.delete(groupKey);
      } else {
        next.add(groupKey);
      }
      return next;
    });
  }

  return (
    <div className={`${v6.cardCompact} mb-3 !p-3`} data-testid="intake-v6-letter-group-face-finishes">
      <p className={`mb-1 ${v6Pilot.clusterTitle}`}>Litere volumetrice</p>
      <p className={`mb-2 ${v6Pilot.helper}`} data-testid="intake-v6-face-letters-helper">
        Anatomie: Față (finisaj vizibil) · Cant (lateral volum) · Spate (Forex corp).
      </p>
      <div
        className="mb-2.5 flex flex-wrap items-center gap-3 text-[12px] text-slate-500"
        data-testid="intake-v6-letter-anatomy-legend"
        aria-hidden
      >
        <span className="inline-flex items-center gap-1">
          <PanelTop className="h-3.5 w-3.5 text-slate-400" /> Față
        </span>
        <span className="inline-flex items-center gap-1">
          <Box className="h-3.5 w-3.5 text-slate-400" /> Cant
        </span>
        <span className="inline-flex items-center gap-1">
          <Layers className="h-3.5 w-3.5 text-slate-400" /> Spate
        </span>
      </div>

      <div data-testid="intake-v6-letter-group-cant-finishes">
        <p className="sr-only" data-testid="intake-v6-cant-letters-helper">
          Laterala literei / adâncimea volumului.
        </p>

        {visibility.returnCant && groups.length > 1 ? (
          <div
            className="mb-2 flex flex-wrap items-center justify-end gap-2"
            data-testid="intake-v6-cant-copy-zone"
          >
            <button
              type="button"
              className="rounded border border-[#2A3548] bg-[#1E293B]/80 px-2.5 py-1 text-[12px] font-semibold text-slate-300 hover:border-sky-500/30"
              onClick={() => onChange(copyFirstCantSettingsToAllGroups(groups))}
              data-testid="intake-v6-copy-cant-to-all"
              title="Copiază finisajul și adâncimea cantului la toate layerele"
            >
              Copiază cant la toate
            </button>
          </div>
        ) : null}

        <IntakeV6CardPagination
          pageIndex={pageIndex}
          pageCount={pageCount}
          totalItems={groups.length}
          onPageChange={setPageIndex}
          testId="intake-v6-review-letter-pagination"
        />

        <div className="space-y-1.5">
          {paginatedGroups.map((group) => {
            const groupIndex = Math.max(0, groups.findIndex((item) => item.group_key === group.group_key));
            const displayLayerName = resolveIntakeV6LetterGroupDisplayLabel(
              group,
              groupIndex,
              analyzerReport,
            );
            const showColor = faceFinishNeedsColorPicker(group.face_finish_type);
            const showRollWidth = faceFinishNeedsRollWidth(group.face_finish_type);
            const rollWidthOptions = faceFinishRollWidthOptions(group.face_finish_type);
            const accent = layerAccentColor(group.source_fill_color);
            const faceSummary = buildFaceSummaryLine(group, effectiveFaceOptions);
            const cantSummary = buildCantSummaryLine(group);
            const resolvedBacking = resolveLayerBackingMode(group.backing_mode, globalBackingFallback);
            const spateSummary = visibility.back ? buildSpateSummaryLine(resolvedBacking) : "—";
            const status = resolveLayerCardStatus(group);
            const expanded = expandedKeys.has(group.group_key);
            const returnCant = letterGroupToReturnCant(group);
            const cantUi = resolveIntakeV6ReturnFinishUiOption(returnCant.finishType);
            const showCantColor = cantUi === "oracal_wrapped" || cantUi === "ral_paint";
            const cantFieldProps = {
              layout: "review" as const,
              compact: true,
              idPrefix: `v6-${group.group_key}`,
              returnCant,
              onReturnChange: (cant: typeof returnCant) =>
                patchGroup(group.group_key, patchLetterGroupFromReturnCant(cant)),
              testIdPrefix: `intake-v6-letter-group-return-${group.group_key}`,
              allowedReturnDepthMm,
              finishLabel: fieldLabels?.return_finish_type,
              depthLabel: fieldLabels?.return_depth_mm,
            };

            return (
              <IntakeV6LayerCardShell
                key={group.group_key}
                cardTestId={`intake-v6-letter-group-${group.group_key}`}
                headerTestId={`intake-v6-letter-group-header-${group.group_key}`}
                expanded={expanded}
                onToggle={() => toggleExpanded(group.group_key)}
                accentColor={accent}
                layerIcon={Layers}
                layerName={displayLayerName}
                faceSummary={visibility.face ? faceSummary : "—"}
                cantSummary={visibility.returnCant ? cantSummary : "—"}
                spateSummary={spateSummary}
                faceSummaryTestId={`intake-v6-letter-group-face-summary-${group.group_key}`}
                cantSummaryTestId={`intake-v6-letter-group-cant-summary-${group.group_key}`}
                spateSummaryTestId={`intake-v6-letter-group-spate-summary-${group.group_key}`}
                swatchTestId={`intake-v6-letter-group-swatch-${group.group_key}`}
                statusAttr={status}
                status={
                  intakeV6ShowOperatorConfigStatusBadges() ? (
                    <>
                      {status === "ok" ? (
                        <AtomsBadge tone="ok">
                          <span className="inline-flex items-center gap-0.5">
                            <CheckCircle2 className="h-2.5 w-2.5" aria-hidden />
                            {finishLetterCardStatusLabelRo("ok")}
                          </span>
                        </AtomsBadge>
                      ) : null}
                      {status === "warning" ? (
                        <AtomsBadge tone="pending">
                          <span className="inline-flex items-center gap-0.5">
                            <AlertTriangle className="h-2.5 w-2.5" aria-hidden />
                            {finishLetterCardStatusLabelRo("warning")}
                          </span>
                        </AtomsBadge>
                      ) : null}
                    </>
                  ) : null
                }
                expandedChildren={
                  <>
                    {visibility.face ? (
                      <section
                        className={v6Pilot.anatomyZone}
                        data-testid={`intake-v6-face-letter-zone-${group.group_key}`}
                      >
                        <ZoneTitle icon={PanelTop} title="Față" />
                        <label className={REVIEW_FIELD_BLOCK_CLASS}>
                          <span className={PILOT_REVIEW_FIELD_LABEL_CLASS}>
                            {fieldLabels?.face_finish_type ?? "Finisaj față"}
                          </span>
                          <select
                            className={PILOT_REVIEW_SELECT_CLASS}
                            value={group.face_finish_type}
                            onChange={(event) =>
                              patchGroup(group.group_key, {
                                face_finish_type: event.target.value,
                                face_oracal_code: faceFinishNeedsColorPicker(event.target.value)
                                  ? group.face_oracal_code
                                  : null,
                                face_oracal_name: faceFinishNeedsColorPicker(event.target.value)
                                  ? group.face_oracal_name
                                  : null,
                                face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
                                  event.target.value,
                                  group.face_vinyl_roll_width_mm,
                                ),
                              })
                            }
                            data-testid={`intake-v6-face-type-${group.group_key}`}
                          >
                            {effectiveFaceOptions.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </label>
                        {showRollWidth ? (
                          <label
                            className={`${REVIEW_FIELD_BLOCK_CLASS} mt-2`}
                            data-testid={`intake-v6-face-settings-row-${group.group_key}`}
                          >
                            <span className={`${PILOT_REVIEW_FIELD_LABEL_CLASS} inline-flex items-center gap-1`}>
                              <Ruler className="h-3 w-3 shrink-0" aria-hidden />
                              Rolă (mm)
                            </span>
                            <select
                              className={PILOT_REVIEW_SELECT_CLASS}
                              value={
                                normalizeFaceVinylRollWidthMm(
                                  group.face_finish_type,
                                  group.face_vinyl_roll_width_mm,
                                ) ?? ""
                              }
                              onChange={(event) => {
                                const raw = event.target.value;
                                patchGroup(group.group_key, {
                                  face_vinyl_roll_width_mm: raw ? Number(raw) : null,
                                });
                              }}
                              data-testid={`intake-v6-face-roll-width-${group.group_key}`}
                            >
                              <option value="">—</option>
                              {rollWidthOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                            {group.face_finish_type === "print_laminate" ? (
                              <span
                                className={`${v6Pilot.helper} mt-1 block`}
                                data-testid={`intake-v6-face-roll-width-print-note-${group.group_key}`}
                              >
                                Rola print/laminare: {PRINT_LAMINATION_ROLL_WIDTHS_MM.join(" / ")} mm.
                                Util dupa retragere:{" "}
                                {PRINT_LAMINATION_ROLL_WIDTHS_MM.map(
                                  (width) => width - PRINT_LAMINATION_TOTAL_RETRACTION_MM,
                                ).join(" / ")}{" "}
                                mm ({PRINT_LAMINATION_SIDE_RETRACTION_MM} +{" "}
                                {PRINT_LAMINATION_SIDE_RETRACTION_MM} mm).
                              </span>
                            ) : null}
                          </label>
                        ) : null}
                        {showColor ? (
                          <div
                            className={`${REVIEW_COLOR_ROW_SHELL_CLASS} mt-2`}
                            data-testid={`intake-v6-face-color-row-${group.group_key}`}
                          >
                            <ColorRegistrySelect
                              reviewAlign
                              label="Culoare față"
                              valueCode={group.face_oracal_code ?? null}
                              filter={{
                                system: "ORACAL",
                                series: oracalColorPaletteSeriesForFace(group.face_finish_type),
                                usageScope: "face_vinyl",
                              }}
                              onChange={(item) =>
                                patchGroup(group.group_key, {
                                  face_oracal_code: item?.code,
                                  face_oracal_name: item?.name,
                                })
                              }
                              testId={`intake-v6-face-color-${group.group_key}`}
                            />
                          </div>
                        ) : null}
                      </section>
                    ) : null}

                    {visibility.returnCant ? (
                      <section
                        className={v6Pilot.anatomyZone}
                        data-testid={`intake-v6-cant-letter-zone-${group.group_key}`}
                      >
                        <ZoneTitle icon={Box} title="Cant" />
                        <IntakeV6ReturnCantFields {...cantFieldProps} reviewGridRow="finish" />
                        <div className="mt-2">
                          <IntakeV6ReturnCantFields
                            {...cantFieldProps}
                            reviewGridRow="depth"
                            cantSettingsRowTestId={`intake-v6-cant-settings-row-${group.group_key}`}
                          />
                        </div>
                        {showCantColor ? (
                          <div
                            className={`${REVIEW_COLOR_ROW_SHELL_CLASS} mt-2`}
                            data-testid={`intake-v6-letter-group-cant-finishes-${group.group_key}`}
                          >
                            <IntakeV6ReturnCantFields {...cantFieldProps} reviewGridRow="color" />
                          </div>
                        ) : null}
                      </section>
                    ) : null}

                    {visibility.back ? (
                      <section
                        className={v6Pilot.anatomyZone}
                        data-testid={`intake-v6-review-backing-finish-integration-${group.group_key}`}
                      >
                        <ZoneTitle icon={Layers} title="Spate" />
                        <IntakeV6ReviewBackingFinishRow
                          embedded
                          testIdSuffix={layerTestIdSuffix(group.group_key)}
                          backingMode={resolvedBacking}
                          backingLabel={fieldLabels?.backing_mode}
                          onBackingChange={(mode) =>
                            patchGroup(group.group_key, { backing_mode: mode, confirmed: false })
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
      </div>
    </div>
  );
}
