/**
 * Legacy compatibility intake spec editor for TPL-VOLUMETRIC-LETTERS.
 * Do not add new business rules here; use WorkIntake V2 / product_spec_json.
 * See docs/architecture/VOLUMETRIC_WORKINTAKE_V2_MIGRATION_BOUNDARY.md
 */
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  Loader2,
  Save,
  Layers,
  Calculator,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { VectorStudioPanel } from "@/components/workos/VectorStudioPanel";
import IntakePathwaySelector from "@/components/workos/IntakePathwaySelector";
import VectorIntakeFastAskPanel from "@/components/workos/VectorIntakeFastAskPanel";
import InfoHint from "@/components/workos/templateIntakeWorkspace/InfoHint";
import { vectorAssetsApi } from "@/api/vectorAssets";
import {
  type IntakeProductSpec,
  type IndoorOutdoor,
  emptyIntakeProductSpec,
  normalizeIntakeProductSpecForSave,
} from "@/lib/intakeProductSpec";
import {
  INTAKE_FACE_FINISH_OPTIONS,
  INTAKE_MOUNTING_SYSTEM_OPTIONS,
  INTAKE_PSU_OPTIONS,
  INTAKE_ROLL_WIDTH_OPTIONS,
  deriveVectorMetadataFromFilename,
  resolveIntakeMountingSystem,
} from "@/lib/intakeVolumetricSpec";
import {
  buildVolumetricQuotePrepSummary,
  FIELD_TAG_LABELS,
  type FieldTagKind,
} from "@/lib/volumetricIntakeFormPrep";
import {
  getFaceOracalApplicationTiming,
  isFaceOracalFinish,
} from "@/features/product-system/volumetricLettersProduction";
import {
  applyFrontlitConstructionDefaults,
  computeLedLoadWatts,
  computePsuSizing,
  isFaceVinylEnabled,
  LED_MODULE_POWER_OPTIONS,
  LED_STRIP_DENSITY_OPTIONS,
  LIGHT_COLOR_OPTIONS,
  LIGHTING_SYSTEM_OPTIONS,
  PSU_HEADROOM_RATIO,
  RETURN_COLOR_OPTIONS,
} from "@/lib/volumetricFrontlitIntake";
import { updateSvgLayerMapping } from "@/lib/intakeVectorLayerMapping";
import {
  buildVectorStudioInfo,
  humanizeVectorAnalysisStatus,
  syncVectorAnalysisSummaryToSpec,
} from "@/lib/vectorStudioPreview";
import type { SvgLayerAnalysisResult } from "@/lib/svgLayerAnalysis";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import {
  applyIlluminationMode,
  applyMountingTemplateMode,
  ILLUMINATION_MODE_OPTIONS,
  isIntakeIlluminationDisabled,
  MOUNTING_TEMPLATE_MODE_OPTIONS,
  mountingTemplateModeRequiresArea,
  resolveIlluminationMode,
  resolveMountingTemplateMode,
} from "@/lib/volumetricIntakeSelectors";
import {
  defaultSectionOpen,
  derivePathwayFromSpec,
  INTAKE_INPUT_PATHWAY_VECTOR,
  isIntakeSectionVisible,
  type VolumetricIntakePathway,
} from "@/lib/volumetricIntakePathway";
import {
  mergeLocalVectorSpecFields,
  shouldKeepLocalVectorSpec,
} from "@/lib/vectorIntakeSpecMerge";
import {
  deriveFastAskFromSpec,
  isVectorFastAskComplete,
  mapVectorFastAskToProductSpec,
  type VolumetricVectorFastAskAnswers,
} from "@/lib/volumetricVectorFastAskMapping";
import {
  mapVectorFilePickToProductSpec,
  type VectorFileSelectionMetadata,
} from "@/lib/vectorFileSelection";
import { mapSvgVectorAnalysisToProductSpec } from "@/lib/mapSvgVectorAnalysisToSpec";
import {
  applySvgGeometrySuggestionsToSpec,
  mapSvgGeometrySuggestionsToSpec,
  rehydrateGeometryFromSpec,
  type GeometrySuggestionApplyKind,
} from "@/lib/mapSvgGeometryToSpec";
import type { SvgGeometryParseResult } from "@/lib/svgGeometryParser";
import type { SvgVectorAnalysis, SvgVectorDetectedLayer } from "@/lib/svgVectorAnalysis";
import type { LettersLayerSuggestionConfidence } from "@/lib/svgIntakeFlow";

const TEMPLATE_DISPLAY_NAME = "Litere volumetrice luminoase";

/** Seed local pathway lock when UI opens on derived vector (not only after explicit click). */
function seedLocalPathwayChoice(
  spec: IntakeProductSpec | null | undefined
): VolumetricIntakePathway | null {
  return derivePathwayFromSpec(spec) === INTAKE_INPUT_PATHWAY_VECTOR
    ? INTAKE_INPUT_PATHWAY_VECTOR
    : null;
}

const INDOOR_OUTDOOR_OPTIONS: { value: IndoorOutdoor; label: string }[] = [
  { value: "indoor", label: "Interior" },
  { value: "outdoor", label: "Exterior" },
];

const PAINT_FINISH_OPTIONS = [
  { value: "matte", label: "Mat" },
  { value: "gloss", label: "Lucios" },
  { value: "satin", label: "Satinat" },
  { value: "not_specified", label: "Nespecificat" },
] as const;

const VINYL_FINISH_OPTIONS = [
  { value: "gloss", label: "Lucios (651)" },
  { value: "matte", label: "Mat (651)" },
  { value: "translucent_matte", label: "Translucid mat (8500)" },
  { value: "satin", label: "Satin (8500)" },
] as const;

function fieldClass() {
  return "w-full bg-[#0A0F1A] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 outline-none focus:border-blue-500/50";
}

function labelClass() {
  return "text-[11px] text-slate-400 font-semibold mb-1 block";
}

function fieldTagHint(tags?: FieldTagKind[]): string | null {
  if (!tags?.length) return null;
  return tags.map((t) => FIELD_TAG_LABELS[t]).join(" · ");
}

function FieldLabel({
  children,
  tags,
  hint,
}: {
  children: ReactNode;
  tags?: FieldTagKind[];
  hint?: string;
}) {
  const tooltip = hint ?? fieldTagHint(tags);
  return (
    <div className="flex items-center gap-1 mb-1">
      <span className="text-[11px] text-slate-400 font-semibold">{children}</span>
      {tooltip && <InfoHint label={`Info: ${children}`}>{tooltip}</InfoHint>}
    </div>
  );
}

function VectorPathwayDetailGuidance({
  fileName,
  layerCount,
}: {
  fileName?: string | null;
  layerCount?: number | null;
}) {
  const hasFile = Boolean(fileName?.trim());
  const hasLayers = layerCount != null && layerCount > 0;

  return (
    <div
      className="rounded-lg border border-blue-800/40 bg-blue-950/25 px-3 py-3 space-y-1"
      data-testid="vector-pathway-active-status"
    >
      <p className="text-[12px] font-semibold text-blue-200">
        Flux activ: Din fișier vector
      </p>
      <p className="text-[11px] text-slate-300 leading-relaxed">
        Secțiunile de mai jos sunt pentru verificare și completare.
      </p>
      {(hasFile || hasLayers) && (
        <p className="text-[10px] text-slate-400 font-mono">
          {hasFile && <span>Fișier: {fileName}</span>}
          {hasFile && hasLayers && <span> · </span>}
          {hasLayers && <span>Layere detectate: {layerCount}</span>}
        </p>
      )}
    </div>
  );
}

function FormSection({
  number,
  title,
  purpose,
  children,
  defaultOpen = true,
  accent = "purple",
  highlighted = false,
}: {
  number: number;
  title: string;
  purpose: string;
  children: ReactNode;
  defaultOpen?: boolean;
  accent?: "purple" | "blue" | "amber" | "emerald";
  highlighted?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const borderAccent =
    accent === "blue"
      ? "border-blue-900/40"
      : accent === "amber"
        ? "border-amber-900/40"
        : accent === "emerald"
          ? "border-emerald-900/40"
          : "border-purple-900/30";
  const highlightRing = highlighted ? "ring-1 ring-emerald-500/40" : "";

  return (
    <div
      className={`rounded-lg border ${borderAccent} ${highlightRing} bg-[#0A0F1A]/40 overflow-hidden`}
      data-highlighted={highlighted ? "true" : undefined}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-[#0D1321]/60 transition-colors"
      >
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#1E293B] text-[11px] font-bold text-slate-300">
          {number}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-[12px] font-bold text-slate-200">{title}</h4>
            <InfoHint label={`Despre: ${title}`}>{purpose}</InfoHint>
            {open ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            )}
          </div>
        </div>
      </button>
      {open && <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div>}
    </div>
  );
}

export interface Product001IntakeSpecEditorProps {
  initialSpec: IntakeProductSpec | null;
  onSave: (
    spec: IntakeProductSpec | null,
    options?: { skipRefresh?: boolean }
  ) => Promise<void>;
  readOnly?: boolean;
  /** When set, Section 10 shows continue button (IntakeDetail). */
  onContinueToQuoteWizard?: () => void;
  showQuotePrepPanel?: boolean;
  /** Live spec updates for workspace quote tab / readiness. */
  onSpecChange?: (spec: IntakeProductSpec) => void;
}

export default function Product001IntakeSpecEditor({
  initialSpec,
  onSave,
  readOnly = false,
  onContinueToQuoteWizard,
  showQuotePrepPanel = false,
  onSpecChange,
}: Product001IntakeSpecEditorProps) {
  const [spec, setSpec] = useState<IntakeProductSpec>(() =>
    applyFrontlitConstructionDefaults({
      ...emptyIntakeProductSpec(),
      ...(initialSpec ?? {}),
    })
  );
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [svgPasteText, setSvgPasteText] = useState("");
  const [layerAnalysis, setLayerAnalysis] = useState<SvgLayerAnalysisResult | null>(null);
  const [layerAnalyzing, setLayerAnalyzing] = useState(false);
  const [layerAnalysisError, setLayerAnalysisError] = useState<string | null>(null);
  const [pathway, setPathway] = useState<VolumetricIntakePathway>(() =>
    derivePathwayFromSpec(initialSpec)
  );
  const [pathwayChangeWarning, setPathwayChangeWarning] = useState(false);
  const [fastAskApplied, setFastAskApplied] = useState(() =>
    isVectorFastAskComplete(initialSpec)
  );
  const [prefilledSections, setPrefilledSections] = useState<number[]>([]);
  const [fastAskApplyMessage, setFastAskApplyMessage] = useState<string | null>(null);
  /** Local pathway choice wins until parent catches up after save/refresh. */
  const localPathwayChoiceRef = useRef<VolumetricIntakePathway | null>(
    seedLocalPathwayChoice(initialSpec)
  );
  const localVectorFileAtRef = useRef<string | null>(
    initialSpec?.vector_file_selected_at ?? null
  );
  const specRef = useRef(spec);
  const persistQueueRef = useRef(Promise.resolve());

  useEffect(() => {
    specRef.current = spec;
    onSpecChange?.(spec);
  }, [spec, onSpecChange]);

  const initialSpecKey = JSON.stringify(initialSpec ?? {});

  useEffect(() => {
    const synced = JSON.parse(initialSpecKey) as IntakeProductSpec;

    let keepLocalVector = false;

    setSpec((prev) => {
      const base = { ...emptyIntakeProductSpec(), ...synced };
      const localFileAt = localVectorFileAtRef.current;
      keepLocalVector = shouldKeepLocalVectorSpec({
        localFileAt,
        localPathwayIsVector: localPathwayChoiceRef.current === INTAKE_INPUT_PATHWAY_VECTOR,
        syncedFileAt: synced.vector_file_selected_at,
      });

      if (!keepLocalVector) {
        if (localPathwayChoiceRef.current === INTAKE_INPUT_PATHWAY_VECTOR) {
          return { ...base, intake_input_pathway: INTAKE_INPUT_PATHWAY_VECTOR };
        }
        return base;
      }

      return mergeLocalVectorSpecFields(prev, base);
    });

    setPathway(() => {
      if (localPathwayChoiceRef.current) {
        return localPathwayChoiceRef.current;
      }
      return derivePathwayFromSpec(synced);
    });
    if (keepLocalVector) {
      setFastAskApplied((prev) => prev || isVectorFastAskComplete(synced));
    } else {
      setFastAskApplied(isVectorFastAskComplete(synced));
    }
    if (!keepLocalVector) {
      setPrefilledSections([]);
      setFastAskApplyMessage(null);
    }
    setPathwayChangeWarning(false);
    // Content key avoids resetting local edits when parent passes a new object reference.
  }, [initialSpecKey]);

  const buildPersistPayload = (specInput: IntakeProductSpec): IntakeProductSpec | null =>
    normalizeIntakeProductSpecForSave({
      ...emptyIntakeProductSpec(),
      ...specRef.current,
      ...specInput,
    });

  const persistSpec = (
    specInput: IntakeProductSpec,
    options?: { keepPathwayLocks?: boolean; skipRefresh?: boolean }
  ) => {
    persistQueueRef.current = persistQueueRef.current
      .catch(() => undefined)
      .then(async () => {
        setSaving(true);
        setSaveError(null);
        try {
          const payload = buildPersistPayload({
            ...specRef.current,
            ...specInput,
          });
          if (options?.skipRefresh) {
            await onSave(payload, { skipRefresh: true });
          } else {
            await onSave(payload);
          }
          if (!options?.keepPathwayLocks) {
            localPathwayChoiceRef.current = null;
            localVectorFileAtRef.current = null;
          }
          setSavedAt(Date.now());
        } catch (e) {
          setSaveError(e instanceof Error ? e.message : "Salvare eșuată");
        } finally {
          setSaving(false);
        }
      });
    return persistQueueRef.current;
  };

  const handlePathwayChange = (next: VolumetricIntakePathway) => {
    localPathwayChoiceRef.current = next;
    if (next !== INTAKE_INPUT_PATHWAY_VECTOR) {
      localVectorFileAtRef.current = null;
    }
    if (next === pathway) {
      return;
    }
    setPathwayChangeWarning(true);
    setPathway(next);
    setSpec((prev) => {
      const updated = { ...prev, intake_input_pathway: next };
      if (!readOnly) {
        void persistSpec(updated, { keepPathwayLocks: true, skipRefresh: true });
      }
      return updated;
    });
    if (next !== "vector") {
      setFastAskApplied(true);
    } else {
      setFastAskApplied(isVectorFastAskComplete({ ...spec, intake_input_pathway: next }));
    }
  };

  const vectorFastAskGateOpen =
    pathway !== "vector" || fastAskApplied;

  const showSection = (section: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9) =>
    vectorFastAskGateOpen && isIntakeSectionVisible(pathway, section, spec);

  const sectionHighlighted = (section: number) => prefilledSections.includes(section);

  const handleVectorFileAttach = (
    metadata: VectorFileSelectionMetadata,
    analysis?: SvgVectorAnalysis | null
  ) => {
    localPathwayChoiceRef.current = INTAKE_INPUT_PATHWAY_VECTOR;
    localVectorFileAtRef.current = metadata.selectedAt;
    setPathway(INTAKE_INPUT_PATHWAY_VECTOR);
    setSpec((prev) => {
      let next = mapVectorFilePickToProductSpec(prev, metadata);
      if (analysis?.parse_ok) {
        next = mapSvgVectorAnalysisToProductSpec(next, analysis);
      }
      if (!readOnly) {
        void persistSpec(next, { keepPathwayLocks: true, skipRefresh: true })
          .then(() => {
            if ((next.vector_detected_layers?.length ?? 0) > 0) {
              setFastAskApplyMessage(
                `Fișier analizat — ${next.vector_detected_layers!.length} layere detectate și salvate.`
              );
            } else if (analysis && !analysis.parse_ok) {
              setFastAskApplyMessage(
                analysis.parse_error ?? "Fișier atașat, dar analiza SVG a eșuat."
              );
            }
            setSavedAt(Date.now());
          })
          .catch(() => {
            setFastAskApplyMessage(
              "Analiza locală OK, dar salvarea automată a eșuat — apasă „Salvează specificația”."
            );
          });
      }
      return next;
    });
  };

  const handleVectorFastAskApply = (answers: VolumetricVectorFastAskAnswers) => {
    localPathwayChoiceRef.current = INTAKE_INPUT_PATHWAY_VECTOR;
    const result = mapVectorFastAskToProductSpec(spec, answers);
    setSpec(result.spec);
    setPathway(INTAKE_INPUT_PATHWAY_VECTOR);
    setPrefilledSections(result.prefilledSectionNumbers);
    setFastAskApplied(true);
    const appliedMsg =
      result.messages.length > 0
        ? result.messages.join(" ")
        : "Răspunsuri vector aplicate.";
    if (!readOnly) {
      void persistSpec(result.spec, { keepPathwayLocks: true, skipRefresh: true })
        .then(() => {
          setFastAskApplyMessage(`Salvat. ${appliedMsg}`);
          setSavedAt(Date.now());
        })
        .catch(() => {
          setFastAskApplyMessage(
            `${appliedMsg} Salvare eșuată — apasă „Salvează specificația”.`
          );
        });
    } else {
      setFastAskApplyMessage(`${appliedMsg} Verifică și salvează specificația.`);
      setSavedAt(null);
    }
  };

  const handleConfirmLettersLayerMapping = (
    layers: SvgVectorDetectedLayer[],
    primaryLayerId: string,
    confidence: LettersLayerSuggestionConfidence
  ) => {
    localPathwayChoiceRef.current = INTAKE_INPUT_PATHWAY_VECTOR;
    const analysisForSpec: SvgVectorAnalysis = {
      file_name: spec.vector_file_name ?? "",
      parse_ok: true,
      layers,
      warnings: spec.vector_layer_analysis_warnings ?? [],
      has_embedded_raster: false,
      vector_svg_analyzed: true,
      width: spec.vector_svg_width,
      height: spec.vector_svg_height,
      view_box: spec.vector_svg_viewbox,
    };
    setSpec((prev) => {
      const next = mapSvgVectorAnalysisToProductSpec(prev, analysisForSpec, {
        layerMappingConfirmed: true,
        primaryLettersLayerId: primaryLayerId,
        lettersLayerConfidence: confidence,
      });
      if (!readOnly) {
        void persistSpec(next, { keepPathwayLocks: true, skipRefresh: true }).then(() => {
          setFastAskApplyMessage("Layer principal litere confirmat și salvat.");
          setSavedAt(Date.now());
        });
      }
      return next;
    });
  };

  const vectorReviewSummary = useMemo(() => {
    const info = buildVectorStudioInfo(spec, layerAnalysis);
    return {
      analysisStatusLabel: humanizeVectorAnalysisStatus(spec.vector_analysis_status),
      layerMappingConfirmed: spec.vector_layer_mapping_confirmed === true,
      layerMappingStatusLabel: spec.vector_layer_mapping_status
        ? `Mapare: ${spec.vector_layer_mapping_status}`
        : undefined,
      savedMappingsCount: info.savedMappingsCount,
      savedMappingsList: info.savedMappingsList,
      warnings: info.warnings,
    };
  }, [spec, layerAnalysis]);

  const handleGeometryParsed = (result: SvgGeometryParseResult) => {
    setSpec((prev) => {
      let next = mapSvgGeometrySuggestionsToSpec(prev, result);
      const canAutoApplyQuoteMetrics =
        result.confidence === "high" &&
        (result.suggestions.letterPerimeterM ?? 0) > 0 &&
        (result.suggestions.letterFaceAreaM2 ?? 0) > 0 &&
        (result.suggestions.letterCount ?? 0) >= 1;
      if (canAutoApplyQuoteMetrics) {
        next = applySvgGeometrySuggestionsToSpec(next, "quote_metrics");
        setFastAskApplyMessage(
          `Geometrie ofertare extrasă din SVG: ${result.suggestions.letterPerimeterM} m perimetru, ${result.suggestions.letterFaceAreaM2} m² arie, ${result.suggestions.letterCount} litere.`
        );
      }
      if (!readOnly) {
        void persistSpec(next, { keepPathwayLocks: true, skipRefresh: true });
      }
      return next;
    });
  };

  const handleApplyGeometrySuggestion = (kind: GeometrySuggestionApplyKind) => {
    setSpec((prev) => {
      const next = applySvgGeometrySuggestionsToSpec(prev, kind);
      if (!readOnly) {
        void persistSpec(next, { keepPathwayLocks: true, skipRefresh: true });
      }
      return next;
    });
  };

  const handleVectorManualReviewChange = (patch: {
    manualReviewApproved?: boolean;
    manualReviewNotes?: string;
    analysisStatus?: string;
  }) => {
    setSpec((prev) => {
      const next = { ...prev };
      if (patch.manualReviewApproved !== undefined) {
        next.vector_manual_review_approved = patch.manualReviewApproved;
      }
      if (patch.analysisStatus !== undefined) {
        next.vector_analysis_status = patch.analysisStatus as IntakeProductSpec["vector_analysis_status"];
      }
      if (patch.manualReviewNotes !== undefined) {
        next.vector_manual_review_notes = patch.manualReviewNotes;
      }
      if (!readOnly) {
        void persistSpec(next, { keepPathwayLocks: true, skipRefresh: true });
      }
      return next;
    });
  };

  const quotePrep = useMemo(() => buildVolumetricQuotePrepSummary(spec), [spec]);
  const hasSvgQuoteMetrics =
    (spec.letter_perimeter_m ?? 0) > 0 &&
    (spec.letter_face_area_m2 ?? 0) > 0 &&
    (spec.letter_count ?? 0) >= 1 &&
    spec.vector_metrics_source === "svg_analysis";

  const handleAnalyzeSvgLayers = async () => {
    const text = svgPasteText.trim();
    if (!text) {
      setLayerAnalysisError("Lipește conținutul SVG pentru analiză layer.");
      return;
    }
    setLayerAnalyzing(true);
    setLayerAnalysisError(null);
    try {
      const result = await vectorAssetsApi.analyzeLayers(text, {
        sourceFileName: spec.vector_file_name,
        manualLayerMappings: spec.svg_layer_mappings,
      });
      setLayerAnalysis(result);
      setSpec((prev) => syncVectorAnalysisSummaryToSpec(prev, result));
    } catch (err) {
      setLayerAnalysisError(err instanceof Error ? err.message : "Analiza layer a eșuat.");
      setLayerAnalysis(null);
    } finally {
      setLayerAnalyzing(false);
    }
  };

  const handleLayerMappingChange = async (layerName: string, target: string) => {
    const next = updateSvgLayerMapping(spec, layerName, target || undefined);
    setSpec(next);
    if (!svgPasteText.trim()) return;
    try {
      const result = await vectorAssetsApi.analyzeLayers(svgPasteText.trim(), {
        sourceFileName: next.vector_file_name,
        manualLayerMappings: next.svg_layer_mappings,
      });
      setLayerAnalysis(result);
      setSpec((prev) => syncVectorAnalysisSummaryToSpec(prev, result));
    } catch {
      // Mapping is persisted in spec; analysis refresh is best-effort.
    }
  };

  const update = <K extends keyof IntakeProductSpec>(key: K, value: IntakeProductSpec[K]) => {
    setSpec((prev) => applyFrontlitConstructionDefaults({ ...prev, [key]: value }));
    setSavedAt(null);
  };

  const patchSpec = (patch: Partial<IntakeProductSpec>) => {
    setSpec((prev) => applyFrontlitConstructionDefaults({ ...prev, ...patch }));
    setSavedAt(null);
  };

  const updateGeometryManual = () => {
    update("vector_metrics_source", "manual");
  };

  const handleSave = async () => {
    await persistSpec(spec, {
      keepPathwayLocks: pathway === INTAKE_INPUT_PATHWAY_VECTOR,
    });
  };

  const faceType = spec.face_finish_type ?? "none";
  const mountingSystem = resolveIntakeMountingSystem(spec) ?? "";
  const faceWrapOn = isFaceVinylEnabled(spec);
  const showOracalMeta =
    faceWrapOn &&
    (faceType === "oracal_651" ||
      faceType === "oracal_8500" ||
      faceType === "printed_vinyl" ||
      faceType === "printed_laminated_vinyl");
  const ledLoadWatts = spec.total_led_watts ?? computeLedLoadWatts(spec);
  const psuSizing = computePsuSizing(spec);
  const illuminationMode = resolveIlluminationMode(spec);
  const nonIlluminated = isIntakeIlluminationDisabled(spec);
  const mountingTemplateMode = resolveMountingTemplateMode(spec);
  const showBars =
    mountingSystem === "steel_bars" || mountingSystem === "aluminum_bars";

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg overflow-hidden">
      {/* Header — template identity */}
      <div className="px-4 py-4 border-b border-[#1E293B] bg-gradient-to-r from-purple-900/20 to-[#111827]">
        <div className="flex items-start gap-3">
          <Layers className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="text-[14px] font-bold text-slate-100">
              {TEMPLATE_DISPLAY_NAME}
            </h3>
            <p className="text-[10px] font-mono text-purple-300/80">{TPL_VOLUMETRIC_LETTERS}</p>
            <p className="text-[11px] text-slate-400 max-w-2xl leading-relaxed">
              Formular specific template-ului pentru litere volumetrice luminoase. Alte produse
              vor avea formulare diferite. Câmpurile de mai jos descriu produsul și pregătesc
              oferta — calculul final se validează separat în QuoteWizard.
            </p>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3">
        <IntakePathwaySelector
          value={pathway}
          onChange={handlePathwayChange}
          readOnly={readOnly}
        />

        {pathway === "quick_estimate" && (
          <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/40 rounded-lg text-[11px] text-amber-300/90">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            Estimarea rapidă folosește câmpuri minime. Pentru ofertă comercială
            finală, comută pe manual sau vector.
          </div>
        )}

        {pathwayChangeWarning && (
          <div className="flex items-start gap-2 px-3 py-2 bg-slate-800/40 border border-slate-600/40 rounded-lg text-[11px] text-slate-300">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
            Schimbarea metodei nu șterge datele introduse, dar poate necesita verificare.
          </div>
        )}

        {pathway === "vector" && (
          <VectorIntakeFastAskPanel
            initialAnswers={deriveFastAskFromSpec(spec)}
            readOnly={readOnly}
            onFileAttach={handleVectorFileAttach}
            onApply={handleVectorFastAskApply}
            onConfirmLettersLayer={handleConfirmLettersLayerMapping}
            mappingConfirmed={spec.vector_layer_mapping_confirmed === true}
            primaryLettersLayerId={spec.vector_primary_letters_layer_id ?? null}
            manualReviewApproved={spec.vector_manual_review_approved === true}
            manualReviewNotes={spec.vector_manual_review_notes ?? ""}
            onManualReviewChange={handleVectorManualReviewChange}
            reviewSummary={vectorReviewSummary}
            geometrySuggestions={rehydrateGeometryFromSpec(spec)}
            onGeometryParsed={handleGeometryParsed}
            onApplyGeometrySuggestion={handleApplyGeometrySuggestion}
            saveError={saveError}
          />
        )}

        {fastAskApplyMessage && (
          <p
            className="text-[11px] text-emerald-300/90 bg-emerald-900/10 border border-emerald-800/30 rounded px-3 py-2"
            data-testid="vector-fast-ask-applied-message"
          >
            {fastAskApplyMessage}
          </p>
        )}

        {pathway === "vector" && !vectorFastAskGateOpen && (
          <p className="text-[11px] text-slate-500">
            Completează pașii de mai sus și apasă „Aplică și salvează” pentru a deschide
            secțiunile de verificare.
          </p>
        )}

        {pathway === "vector" && fastAskApplied && vectorFastAskGateOpen && (
          <div className="space-y-2" data-testid="vector-spec-detail-sections">
            <VectorPathwayDetailGuidance
              fileName={spec.vector_file_name}
              layerCount={
                spec.vector_detected_layer_count ??
                spec.vector_detected_layers?.length ??
                null
              }
            />
            <p className="text-[11px] font-semibold text-slate-300 px-0.5">
              Verificare specificație
            </p>
          </div>
        )}

        {pathway === "manual" && vectorFastAskGateOpen && (
          <p
            className="text-[11px] font-semibold text-slate-300 px-0.5"
            data-testid="manual-spec-detail-sections-label"
          >
            Detalii specificație
          </p>
        )}

        {/* 1 — Ce trebuie produs */}
        {showSection(1) && (
        <FormSection
          number={1}
          title="Ce trebuie produs"
          purpose="Identitate vizuală, colantare față și descriere pentru client și producție."
          defaultOpen={defaultSectionOpen(pathway, 1)}
        >
          <div className="md:col-span-2 rounded-lg border border-purple-900/40 bg-purple-950/20 px-3 py-3 space-y-3">
            <label className="flex items-start gap-2 text-[12px] text-slate-200 cursor-pointer">
              <input
                type="checkbox"
                checked={faceWrapOn}
                onChange={(e) => {
                  const enabled = e.target.checked;
                  if (enabled) {
                    patchSpec({ face_vinyl_enabled: true, face_wrap_enabled: true });
                  } else {
                    patchSpec({
                      face_vinyl_enabled: false,
                      face_wrap_enabled: false,
                      face_finish_type: "none",
                      face_vinyl_color_code: undefined,
                      face_vinyl_color_name: undefined,
                      face_vinyl_roll_width_mm: undefined,
                      face_vinyl_finish: undefined,
                      face_vinyl_notes: undefined,
                    });
                  }
                }}
                disabled={readOnly}
                className="rounded border-slate-600 mt-0.5"
                data-testid="intake-face-wrap-enabled"
              />
              <span className="inline-flex items-center gap-1 font-semibold">
                Se colantează fața?
                <InfoHint label="Colantare față">
                  Dacă da, secțiunea Finisaj față / colantare devine disponibilă mai jos.
                  Dacă nu, rămâne vizibil plexiglasul / culoarea materialului.
                </InfoHint>
              </span>
            </label>
            {faceWrapOn && (
              <div>
                <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Tip colantare față</FieldLabel>
                <select
                  className={fieldClass()}
                  value={
                    faceType === "printed_laminated_vinyl"
                      ? "printed_laminated_vinyl"
                      : faceType === "oracal_8500"
                        ? "oracal_8500"
                        : faceType === "oracal_651"
                          ? "oracal_651"
                          : ""
                  }
                  onChange={(e) =>
                    update(
                      "face_finish_type",
                      (e.target.value || undefined) as IntakeProductSpec["face_finish_type"]
                    )
                  }
                  disabled={readOnly}
                  data-testid="intake-face-wrap-type"
                >
                  <option value="">— selectează —</option>
                  <option value="oracal_651">Autocolant colorat Oracal 651</option>
                  <option value="oracal_8500">Oracal 8500 translucent</option>
                  <option value="printed_laminated_vinyl">Print + laminare</option>
                </select>
              </div>
            )}
          </div>
          <div className="md:col-span-2">
            <FieldLabel tags={["production_only"]}>Text / logo / denumire lucrare</FieldLabel>
            <input
              className={fieldClass()}
              value={spec.text ?? ""}
              onChange={(e) => update("text", e.target.value)}
              readOnly={readOnly}
              placeholder="ex: DEDEMAN"
            />
          </div>
          <div>
            <FieldLabel tags={["production_only", "optional"]}>Font / stil grafic</FieldLabel>
            <input
              className={fieldClass()}
              value={spec.font ?? ""}
              onChange={(e) => update("font", e.target.value)}
              readOnly={readOnly}
              placeholder="ex: Helvetica Bold sau „din fișier vector”"
            />
          </div>
          <div className="md:col-span-2">
            <FieldLabel tags={["production_only", "optional"]}>
              Observații client / cerințe vizuale
            </FieldLabel>
            <textarea
              className={`${fieldClass()} min-h-[56px] resize-y`}
              value={spec.notes ?? ""}
              onChange={(e) => update("notes", e.target.value)}
              readOnly={readOnly}
              placeholder="Detalii suplimentare, referințe, constrângeri montaj..."
            />
          </div>
        </FormSection>
        )}

        {/* 2 — Dimensiuni generale */}
        {showSection(2) && (
        <FormSection
          number={2}
          title="Dimensiuni generale"
          purpose="Envelope fizic al ansamblului — nu înlocuiesc perimetrul sau aria literelor pentru calcul."
          accent="blue"
          highlighted={sectionHighlighted(2)}
          defaultOpen={defaultSectionOpen(pathway, 2)}
        >
          <div>
            <FieldLabel tags={["prefill_wizard", "optional"]}>Lățime totală ansamblu (mm)</FieldLabel>
            <input
              type="number"
              min={1}
              className={fieldClass()}
              value={spec.width_mm ?? ""}
              onChange={(e) =>
                update("width_mm", e.target.value ? Number(e.target.value) : undefined)
              }
              readOnly={readOnly}
            />
          </div>
          <div>
            <FieldLabel tags={["prefill_wizard", "optional"]}>
              Înălțime totală ansamblu (mm)
            </FieldLabel>
            <input
              type="number"
              min={1}
              className={fieldClass()}
              value={spec.height_mm ?? spec.letter_height_mm ?? ""}
              onChange={(e) => {
                const v = e.target.value ? Number(e.target.value) : undefined;
                update("height_mm", v);
                update("letter_height_mm", v);
              }}
              readOnly={readOnly}
            />
          </div>
          <div>
            <FieldLabel tags={["prefill_wizard", "affects_cost"]}>
              Adâncime cant / retur profil (mm)
            </FieldLabel>
            <input
              type="number"
              min={1}
              className={fieldClass()}
              value={spec.return_depth_mm ?? spec.depth_mm ?? ""}
              onChange={(e) => {
                const v = e.target.value ? Number(e.target.value) : undefined;
                update("return_depth_mm", v);
                update("depth_mm", v);
              }}
              readOnly={readOnly}
              placeholder="30 / 60 / 80 / 100"
            />
            <p className="text-[10px] text-slate-500 mt-1">
              Variantă profil lateral — precomplează QuoteWizard dacă este 30 / 60 / 80 / 100.
            </p>
          </div>
          {pathway !== "quick_estimate" && (
            <div>
              <FieldLabel tags={["production_only", "optional"]}>Montaj interior / exterior</FieldLabel>
              <select
                className={fieldClass()}
                value={spec.indoor_outdoor ?? ""}
                onChange={(e) =>
                  update("indoor_outdoor", (e.target.value || undefined) as IndoorOutdoor | undefined)
                }
                disabled={readOnly}
              >
                <option value="">—</option>
                {INDOOR_OUTDOOR_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          )}
          {pathway !== "quick_estimate" && (
            <p className="md:col-span-2 text-[10px] text-slate-500 border-t border-[#1E293B] pt-2">
              Dimensiunile generale descriu ansamblul montat. Nu calculează singure perimetrul
              sau aria față a literelor.
            </p>
          )}
        </FormSection>
        )}

        {/* 3 — Geometrie pentru ofertare */}
        {showSection(3) && (
        <FormSection
          number={3}
          title="Geometrie pentru ofertare"
          purpose="Metrici folosite în calculul de cost — completați manual sau după extragere validă din vector."
          accent="amber"
          defaultOpen={defaultSectionOpen(pathway, 3)}
        >
          {pathway === "vector" && !hasSvgQuoteMetrics && (
            <p className="md:col-span-2 text-[11px] text-amber-300/90 bg-amber-900/10 border border-amber-800/30 rounded px-2 py-1.5">
              Analiza vector nu a furnizat metrici validate — reîncarcă SVG-ul sau aplică
              geometria ofertare din panoul vector, apoi completează manual dacă lipsește ceva.
            </p>
          )}
          {pathway === "vector" && hasSvgQuoteMetrics && (
            <p className="md:col-span-2 text-[11px] text-emerald-300/90 bg-emerald-900/10 border border-emerald-800/30 rounded px-2 py-1.5">
              Perimetru, arie și număr litere preluate din analiza SVG — verifică valorile înainte
              de simulare.
            </p>
          )}
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Arie față litere (m²)</FieldLabel>
            <input
              type="number"
              min={0}
              step="0.01"
              className={fieldClass()}
              value={spec.letter_face_area_m2 ?? ""}
              onChange={(e) => {
                updateGeometryManual();
                update(
                  "letter_face_area_m2",
                  e.target.value ? Number(e.target.value) : undefined
                );
              }}
              readOnly={readOnly}
              placeholder="ex: 2.88"
            />
          </div>
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Perimetru litere (ml)</FieldLabel>
            <input
              type="number"
              min={0}
              step="0.1"
              className={fieldClass()}
              value={spec.letter_perimeter_m ?? ""}
              onChange={(e) => {
                updateGeometryManual();
                update(
                  "letter_perimeter_m",
                  e.target.value ? Number(e.target.value) : undefined
                );
              }}
              readOnly={readOnly}
              placeholder="ex: 18"
            />
          </div>
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>
              Număr litere / elemente (buc)
            </FieldLabel>
            <input
              type="number"
              min={1}
              className={fieldClass()}
              value={spec.letter_count ?? ""}
              onChange={(e) => {
                updateGeometryManual();
                update("letter_count", e.target.value ? Number(e.target.value) : undefined);
              }}
              readOnly={readOnly}
              placeholder="ex: 9"
            />
          </div>
          <div className="md:col-span-2 rounded-md border border-[#1E293B] bg-[#05080f] px-3 py-2">
            <p className="text-[10px] text-slate-500">Sursă geometrie (informativ)</p>
            <p className="text-[11px] text-slate-300">{quotePrep.geometrySource}</p>
            {quotePrep.ledModuleCountEstimate != null && (
              <p className="text-[10px] text-blue-300/90 mt-1">
                Estimare module LED din perimetru:{" "}
                <span className="font-semibold">{quotePrep.ledModuleCountEstimate}</span> buc
                (se recalculează în QuoteWizard)
              </p>
            )}
          </div>
          {!hasSvgQuoteMetrics && (
            <p className="md:col-span-2 text-[10px] text-amber-300/80 bg-amber-900/10 border border-amber-800/30 rounded px-2 py-1.5">
              Aceste valori intră în calcul. Se completează automat doar când analiza SVG extrage
              perimetru și arie din contururile layerului litere.
            </p>
          )}
        </FormSection>
        )}

        {/* 4 — Construcție litere */}
        {showSection(4) && (
        <FormSection
          number={4}
          title="Construcție litere"
          purpose="Alegeri de fabricație CNC și volum aluminiu."
          defaultOpen={defaultSectionOpen(pathway, 4)}
          highlighted={sectionHighlighted(4)}
        >
          <div className="md:col-span-2 flex flex-col gap-3">
            <label className="flex items-start gap-2 text-[12px] text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={spec.back_bevel_enabled === true || spec.backing_chamfer === true}
                onChange={(e) => {
                  update("back_bevel_enabled", e.target.checked);
                  update("backing_chamfer", e.target.checked);
                }}
                disabled={readOnly}
                className="rounded border-slate-600 mt-0.5"
              />
              <span className="inline-flex items-center gap-1 font-semibold">
                Șanfren spate litere
                <InfoHint label="Șanfren spate">
                  Opțional — treceri CNC suplimentare pe spatele Forex. Afectează calculul.
                </InfoHint>
              </span>
            </label>
            <label className="flex items-start gap-2 text-[12px] text-slate-300">
              <input
                type="checkbox"
                checked
                disabled
                readOnly
                className="rounded border-slate-600 mt-0.5 opacity-70"
                data-testid="intake-face-miter-locked"
              />
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-300/90">
                Șanfren vizual față (miter) — inclus obligatoriu
                <InfoHint label="Șanfren față">
                  Standard pe litere volumetrice luminoase față — necesar pentru lipirea
                  volumului aluminiu pe față.
                </InfoHint>
              </span>
            </label>
          </div>
          <div>
            <FieldLabel tags={["production_only"]}>Cant / lateral aluminiu</FieldLabel>
            <select
              className={fieldClass()}
              value={spec.return_color ?? spec.return_edge_color ?? "white"}
              onChange={(e) => {
                const color = e.target.value as IntakeProductSpec["return_color"];
                patchSpec({ return_color: color, return_edge_color: color });
              }}
              disabled={readOnly}
              data-testid="intake-return-edge-color"
            >
              {RETURN_COLOR_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-500 mt-1.5 leading-relaxed">
              Cant alb sau negru din stoc — fără vopsire RAL pe lateral.
            </p>
          </div>
        </FormSection>
        )}

        {/* 5 — Finisaj față */}
        {showSection(5) && faceWrapOn && (
        <FormSection
          number={5}
          title="Finisaj față / colantare"
          purpose="Aspect vizual al feței literelor — date pentru producție și ofertă finală."
          defaultOpen={defaultSectionOpen(pathway, 5)}
          highlighted={sectionHighlighted(5)}
        >
          <div className="md:col-span-2">
            <FieldLabel tags={["affects_cost", "prefill_wizard", "final_quote"]}>
              Finisaj față litere
            </FieldLabel>
            <select
              className={fieldClass()}
              value={spec.face_finish_type ?? ""}
              onChange={(e) =>
                update(
                  "face_finish_type",
                  (e.target.value || undefined) as IntakeProductSpec["face_finish_type"]
                )
              }
              disabled={readOnly}
            >
              <option value="">—</option>
              {INTAKE_FACE_FINISH_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            {isFaceOracalFinish(spec.face_finish) && (
              <p className="text-[10px] text-blue-300/90 mt-1.5 leading-relaxed">
                {getFaceOracalApplicationTiming(spec)}
              </p>
            )}
          </div>
          {showOracalMeta && (
            <>
              <div>
                <FieldLabel tags={["production_only", "final_quote"]}>
                  Cod culoare folie
                </FieldLabel>
                <input
                  className={fieldClass()}
                  value={spec.face_vinyl_color_code ?? ""}
                  onChange={(e) => update("face_vinyl_color_code", e.target.value)}
                  readOnly={readOnly}
                  placeholder="ex: 070 black"
                />
              </div>
              <div>
                <FieldLabel tags={["production_only", "optional"]}>Denumire culoare</FieldLabel>
                <input
                  className={fieldClass()}
                  value={spec.face_vinyl_color_name ?? ""}
                  onChange={(e) => update("face_vinyl_color_name", e.target.value)}
                  readOnly={readOnly}
                />
              </div>
              <div>
                <FieldLabel tags={["production_only", "final_quote"]}>
                  Lățime rolă folie (mm)
                </FieldLabel>
                <select
                  className={fieldClass()}
                  value={spec.face_vinyl_roll_width_mm ?? ""}
                  onChange={(e) =>
                    update(
                      "face_vinyl_roll_width_mm",
                      e.target.value
                        ? (Number(e.target.value) as 1000 | 1260)
                        : undefined
                    )
                  }
                  disabled={readOnly}
                >
                  <option value="">—</option>
                  {INTAKE_ROLL_WIDTH_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <FieldLabel tags={["production_only", "optional"]}>Finisaj folie</FieldLabel>
                <select
                  className={fieldClass()}
                  value={spec.face_vinyl_finish ?? ""}
                  onChange={(e) =>
                    update(
                      "face_vinyl_finish",
                      (e.target.value || undefined) as IntakeProductSpec["face_vinyl_finish"]
                    )
                  }
                  disabled={readOnly}
                >
                  <option value="">—</option>
                  {VINYL_FINISH_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <FieldLabel tags={["production_only", "optional"]}>Note colantare</FieldLabel>
                <input
                  className={fieldClass()}
                  value={spec.face_vinyl_notes ?? ""}
                  onChange={(e) => update("face_vinyl_notes", e.target.value)}
                  readOnly={readOnly}
                />
              </div>
            </>
          )}
          <p className="md:col-span-2 text-[10px] text-slate-500">
            Datele de colantare ajută producția și pot bloca oferta comercială finală dacă lipsesc
            (cod culoare, lățime rolă pentru Oracal).
          </p>
        </FormSection>
        )}

        {/* 6 — Vopsire RAL */}
        {showSection(6) && (
        <FormSection
          number={6}
          title="Vopsire / RAL"
          purpose="Metadata vopsea și estimare tuburi — tuburile se rotunjesc la calcul."
          defaultOpen={defaultSectionOpen(pathway, 6)}
        >
          <div>
            <FieldLabel tags={["production_only", "final_quote"]}>Cod RAL vopsea</FieldLabel>
            <input
              className={fieldClass()}
              value={spec.paint_ral_code ?? spec.ral_color ?? ""}
              onChange={(e) => {
                update("paint_ral_code", e.target.value);
                update("ral_color", e.target.value);
              }}
              readOnly={readOnly}
              placeholder="ex: RAL 9005"
            />
          </div>
          <div>
            <FieldLabel tags={["production_only", "optional"]}>Denumire RAL</FieldLabel>
            <input
              className={fieldClass()}
              value={spec.paint_ral_name ?? ""}
              onChange={(e) => update("paint_ral_name", e.target.value)}
              readOnly={readOnly}
            />
          </div>
          <div>
            <FieldLabel tags={["production_only", "optional"]}>Finisaj vopsea</FieldLabel>
            <select
              className={fieldClass()}
              value={spec.paint_finish ?? ""}
              onChange={(e) =>
                update("paint_finish", (e.target.value || undefined) as IntakeProductSpec["paint_finish"])
              }
              disabled={readOnly}
            >
              <option value="">—</option>
              {PAINT_FINISH_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>
              Număr tuburi spray estimate
            </FieldLabel>
            <input
              type="number"
              min={1}
              className={fieldClass()}
              value={spec.paint_tube_count ?? ""}
              onChange={(e) =>
                update("paint_tube_count", e.target.value ? Number(e.target.value) : undefined)
              }
              readOnly={readOnly}
            />
            <p className="text-[10px] text-slate-500 mt-1">
              Tuburile se rotunjesc în sus la calcul. Codul RAL este necesar pentru producție
              când există tuburi estimate.
            </p>
          </div>
        </FormSection>
        )}

        {/* 7 — Iluminare față */}
        {showSection(7) && (
        <FormSection
          number={7}
          title="Iluminare"
          purpose="Neluminat sau iluminare frontală — module LED sau bandă LED, cu sursă dimensionată automat (+15% rezervă)."
          defaultOpen={defaultSectionOpen(pathway, 7)}
          highlighted={sectionHighlighted(7)}
        >
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Iluminare</FieldLabel>
            <select
              className={fieldClass()}
              value={illuminationMode}
              onChange={(e) =>
                patchSpec(
                  applyIlluminationMode(spec, e.target.value as typeof illuminationMode)
                )
              }
              disabled={readOnly}
              data-testid="intake-illumination-mode"
            >
              {ILLUMINATION_MODE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            {nonIlluminated && (
              <p className="text-[10px] text-slate-500 mt-1" data-testid="intake-non-illuminated-hint">
                Fără cost LED, surse sau cablaj — literele rămân neiluminate.
              </p>
            )}
          </div>
          {!nonIlluminated && (
            <>
          <p className="md:col-span-2 text-[11px] text-blue-300/90 bg-blue-950/25 border border-blue-900/40 rounded px-2 py-1.5">
            Acest template este doar pentru iluminare față. Halo / spate vor avea template
            separat.
          </p>
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Tip sistem</FieldLabel>
            <select
              className={fieldClass()}
              value={spec.lighting_system_type === "led_strip" ? "led_strip" : "led_modules"}
              onChange={(e) =>
                patchSpec(
                  applyIlluminationMode(
                    spec,
                    e.target.value === "led_strip" ? "led_strip" : "led_modules"
                  )
                )
              }
              disabled={readOnly}
              data-testid="intake-lighting-system-type"
            >
              {LIGHTING_SYSTEM_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <FieldLabel tags={["production_only"]}>Temperatură culoare</FieldLabel>
            <select
              className={fieldClass()}
              value={spec.light_color ?? (spec.led_color_temperature === "cool" ? "cold" : spec.led_color_temperature) ?? "warm"}
              onChange={(e) => {
                const color = e.target.value as IntakeProductSpec["light_color"];
                update("light_color", color);
                update("led_color_temperature", color === "cold" ? "cool" : "warm");
              }}
              disabled={readOnly}
              data-testid="intake-led-color-temp"
            >
              {LIGHT_COLOR_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-500 mt-1">
              Cald / rece — același cost la calcul; diferență doar la comandă material.
            </p>
          </div>
          {(spec.lighting_system_type === "led_modules" ||
            spec.lighting_system_type === "led_module" ||
            spec.lighting_system_type == null) ? (
            <div className="md:col-span-2">
              <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Putere modul LED</FieldLabel>
              <select
                className={fieldClass()}
                value={spec.led_module_power_w ?? spec.led_module_wattage ?? 1.44}
                onChange={(e) => {
                  const w = Number(e.target.value) as IntakeProductSpec["led_module_power_w"];
                  patchSpec({ led_module_power_w: w, led_module_wattage: w });
                }}
                disabled={readOnly}
                data-testid="intake-led-module-wattage"
              >
                {LED_MODULE_POWER_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="md:col-span-2">
              <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Densitate bandă LED</FieldLabel>
              <select
                className={fieldClass()}
                value={
                  spec.led_strip_density === "60_5w"
                    ? "60_led_per_m"
                    : spec.led_strip_density === "120_10w"
                      ? "120_led_per_m"
                      : (spec.led_strip_density ?? "60_led_per_m")
                }
                onChange={(e) =>
                  update(
                    "led_strip_density",
                    e.target.value as IntakeProductSpec["led_strip_density"]
                  )
                }
                disabled={readOnly}
                data-testid="intake-led-strip-density"
              >
                {LED_STRIP_DENSITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Putere sursă LED (W)</FieldLabel>
            <select
              className={fieldClass()}
              value={spec.selected_psu_watts ?? ""}
              onChange={(e) =>
                update(
                  "selected_psu_watts",
                  e.target.value ? (Number(e.target.value) as 60 | 100 | 160 | 200) : undefined
                )
              }
              disabled={readOnly}
              data-testid="intake-selected-psu"
            >
              <option value="">—</option>
              {INTAKE_PSU_OPTIONS.map((w) => (
                <option key={w} value={w}>
                  {w} W
                </option>
              ))}
            </select>
            {ledLoadWatts > 0 && psuSizing.status === "ok" && psuSizing.selectedPsuWatts != null && (
              <p className="text-[10px] text-emerald-300/90 mt-1">
                Consum estimat LED: {ledLoadWatts.toFixed(1)} W · necesar ≥{" "}
                {psuSizing.requiredPsuWatts} W (+{Math.round(PSU_HEADROOM_RATIO * 100)}%) · sursă:{" "}
                {psuSizing.selectedPsuWatts} W
              </p>
            )}
            {psuSizing.status === "pending_geometry" && (
              <p className="text-[10px] text-amber-300/90 mt-1">{psuSizing.warning}</p>
            )}
            {psuSizing.status === "insufficient_capacity" && (
              <p className="text-[10px] text-red-300/90 mt-1" data-testid="intake-psu-insufficient">
                {psuSizing.warning}
              </p>
            )}
          </div>
          <input type="hidden" value="frontlit" readOnly />
          <div className="md:col-span-2">
            <FieldLabel tags={["production_only", "optional"]}>Observații electrice</FieldLabel>
            <input
              className={fieldClass()}
              value={spec.lighting_notes ?? ""}
              onChange={(e) => update("lighting_notes", e.target.value)}
              readOnly={readOnly}
            />
          </div>
          {quotePrep.ledModuleCountEstimate != null &&
            (spec.lighting_system_type === "led_modules" ||
              spec.lighting_system_type === "led_module" ||
              spec.lighting_system_type == null) && (
            <div className="md:col-span-2 rounded-md border border-blue-900/40 bg-blue-900/10 px-3 py-2">
              <p className="text-[10px] text-slate-500">Module LED estimate (doar informativ)</p>
              <p className="text-[12px] text-blue-200 font-semibold">
                {quotePrep.ledModuleCountEstimate} buc — derivat din perimetru în QuoteWizard
              </p>
            </div>
          )}
            </>
          )}
        </FormSection>
        )}

        {/* 8 — Montaj */}
        {showSection(8) && (
        <FormSection
          number={8}
          title="Montaj / suport"
          purpose="Sistem de prindere și șablon montaj — independente între ele."
          defaultOpen={defaultSectionOpen(pathway, 8)}
        >
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Sistem montaj</FieldLabel>
            <select
              className={fieldClass()}
              value={spec.mounting_system ?? ""}
              onChange={(e) =>
                update(
                  "mounting_system",
                  (e.target.value || undefined) as IntakeProductSpec["mounting_system"]
                )
              }
              disabled={readOnly}
            >
              <option value="">—</option>
              {INTAKE_MOUNTING_SYSTEM_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <FieldLabel tags={["affects_cost", "prefill_wizard"]}>Șablon de montaj</FieldLabel>
            <select
              className={fieldClass()}
              value={mountingTemplateMode}
              onChange={(e) =>
                patchSpec(
                  applyMountingTemplateMode(
                    spec,
                    e.target.value as typeof mountingTemplateMode
                  )
                )
              }
              disabled={readOnly}
              data-testid="intake-mounting-template-mode"
            >
              {MOUNTING_TEMPLATE_MODE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-500 mt-1" data-testid="intake-mounting-template-mode-hint">
              {MOUNTING_TEMPLATE_MODE_OPTIONS.find((o) => o.value === mountingTemplateMode)?.helper}
            </p>
          </div>
          {mountingTemplateModeRequiresArea(mountingTemplateMode) && (
            <div>
              <FieldLabel tags={["affects_cost", "prefill_wizard", "optional"]}>
                Arie șablon montaj (m²)
              </FieldLabel>
              <input
                type="number"
                min={0}
                step="0.01"
                className={fieldClass()}
                value={spec.mounting_template_area_m2 ?? ""}
                onChange={(e) =>
                  update(
                    "mounting_template_area_m2",
                    e.target.value ? Number(e.target.value) : undefined
                  )
                }
                readOnly={readOnly}
              />
            </div>
          )}
          {showBars && (
            <>
              <div>
                <FieldLabel tags={["affects_cost", "prefill_wizard"]}>
                  Profil bare premontaj
                </FieldLabel>
                <input
                  className={fieldClass()}
                  value={spec.mounting_bar_profile ?? "30x30x1.5"}
                  onChange={(e) => update("mounting_bar_profile", e.target.value)}
                  readOnly={readOnly}
                />
              </div>
              <div>
                <FieldLabel tags={["affects_cost", "prefill_wizard", "optional"]}>
                  Număr bare premontaj
                </FieldLabel>
                <input
                  type="number"
                  min={1}
                  className={fieldClass()}
                  value={spec.mounting_bar_count ?? 2}
                  onChange={(e) =>
                    update("mounting_bar_count", e.target.value ? Number(e.target.value) : undefined)
                  }
                  readOnly={readOnly}
                />
              </div>
              <div>
                <FieldLabel tags={["affects_cost", "prefill_wizard", "optional"]}>
                  Lungime totală bare — override (ml)
                </FieldLabel>
                <input
                  type="number"
                  min={0}
                  step="0.1"
                  className={fieldClass()}
                  value={spec.mounting_bar_length_m ?? ""}
                  onChange={(e) =>
                    update(
                      "mounting_bar_length_m",
                      e.target.value ? Number(e.target.value) : undefined
                    )
                  }
                  readOnly={readOnly}
                />
              </div>
            </>
          )}
          <div className="md:col-span-2">
            <FieldLabel tags={["production_only", "optional"]}>Note montaj</FieldLabel>
            <input
              className={fieldClass()}
              value={spec.mounting_notes ?? ""}
              onChange={(e) => update("mounting_notes", e.target.value)}
              readOnly={readOnly}
            />
          </div>
          <p className="md:col-span-2 text-[10px] text-slate-500">
            Panoul ACM casetat se ofertează prin template separat — nu folosi dimensiunile
            literelor pentru ACM.
          </p>
        </FormSection>
        )}

        {/* 9 — Vector Studio */}
        {showSection(9) && (
        <FormSection
          number={9}
          title="Vector Studio — fișier și readiness"
          purpose="Pregătire fișier vector pentru producție și gate-uri ofertă — fără calcul automat din preview."
          accent="emerald"
          defaultOpen={defaultSectionOpen(pathway, 9)}
          highlighted={sectionHighlighted(9)}
        >
          <div className="md:col-span-2">
            <VectorStudioPanel
              spec={spec}
              readOnly={readOnly}
              svgPasteText={svgPasteText}
              onSvgPasteTextChange={setSvgPasteText}
              layerAnalysis={layerAnalysis}
              layerAnalyzing={layerAnalyzing}
              layerAnalysisError={layerAnalysisError}
              onAnalyze={() => void handleAnalyzeSvgLayers()}
              onLayerMappingChange={(layerName, target) =>
                void handleLayerMappingChange(layerName, target)
              }
              onSpecUpdate={update}
              onFilenameChange={(filename) =>
                setSpec((prev) => deriveVectorMetadataFromFilename(prev, filename))
              }
              onFileTypeChange={(fileType) => update("vector_file_type", fileType)}
            />
          </div>
        </FormSection>
        )}

        {/* 10 — Pregătire ofertă */}
        {showQuotePrepPanel && (
          <div className="rounded-lg border border-blue-900/40 bg-blue-900/10 p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-blue-400" />
              <h4 className="text-[13px] font-bold text-slate-100">Pregătire ofertă</h4>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Rezumat pentru simulare preliminară și ofertă comercială. Valorile salvate aici
              pot precompleta QuoteWizard, dar oferta finală are propriul gate de validare.
              Nu se creează ofertă sau comandă din acest ecran.
            </p>

            {quotePrep.prefill.prefilledFields.length > 0 && (
              <div>
                <p className="text-[10px] text-slate-500 font-semibold mb-1">
                  Câmpuri care vor precompleta QuoteWizard
                </p>
                <ul className="text-[10px] text-purple-300/90 space-y-0.5">
                  {quotePrep.prefill.prefilledFields.slice(0, 8).map((f) => (
                    <li key={f.key}>
                      {f.label}: <span className="text-slate-300">{f.value}</span>
                    </li>
                  ))}
                  {quotePrep.prefill.prefilledFields.length > 8 && (
                    <li className="text-slate-500">
                      +{quotePrep.prefill.prefilledFields.length - 8} altele
                    </li>
                  )}
                </ul>
              </div>
            )}

            <div className="grid gap-3 md:grid-cols-2">
              <PrepList
                title="Lipsește pentru simulare preliminară"
                items={quotePrep.missingForSimulate}
                emptyLabel="Date suficiente pentru simulare (în QuoteWizard)"
                tone="amber"
              />
              <PrepList
                title="Posibile blocaje ofertă comercială"
                items={quotePrep.missingForFinalQuote}
                emptyLabel="Niciun indiciu evident — gate-ul final se validează în QuoteWizard"
                tone="red"
              />
            </div>

            {quotePrep.prefill.warnings.length > 0 && (
              <ul className="text-[11px] text-amber-300/90 list-disc pl-4 space-y-0.5">
                {quotePrep.prefill.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            )}

            {onContinueToQuoteWizard && (
              <div className="flex justify-end pt-1">
                <button
                  type="button"
                  onClick={onContinueToQuoteWizard}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-[12px] font-semibold bg-blue-600 hover:bg-blue-500 text-white"
                >
                  <Calculator className="w-4 h-4" />
                  Deschide ofertare preliminară
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {!readOnly && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-[#1E293B] bg-[#0D1321]/50">
          <div className="text-[10px] text-slate-500 max-w-lg">
            Salvează specificația produsului în cerere. Geometria pentru calcul poate fi
            completată aici sau în QuoteWizard — nu se inventează din vector fără extragere
            validă.
          </div>
          <div className="flex items-center gap-2">
            {saveError && (
              <span className="text-[11px] text-red-400 max-w-[200px] truncate">{saveError}</span>
            )}
            {savedAt != null && !saveError && (
              <span className="text-[11px] text-emerald-400">Salvat</span>
            )}
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-[12px] font-semibold"
            >
              {saving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              Salvează specificația
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PrepList({
  title,
  items,
  emptyLabel,
  tone,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
  tone: "amber" | "red";
}) {
  const Icon = items.length === 0 ? CheckCircle2 : AlertTriangle;
  const iconCls =
    items.length === 0
      ? "text-emerald-400"
      : tone === "amber"
        ? "text-amber-400"
        : "text-red-400";

  return (
    <div className="rounded-md border border-[#1E293B] bg-[#05080f] p-3">
      <div className="flex items-center gap-1.5 mb-2">
        <Icon className={`w-3.5 h-3.5 ${iconCls}`} />
        <p className="text-[10px] text-slate-400 font-semibold">{title}</p>
      </div>
      {items.length === 0 ? (
        <p className="text-[10px] text-emerald-400/90">{emptyLabel}</p>
      ) : (
        <ul className="text-[10px] text-slate-300 space-y-0.5 list-disc pl-4">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
