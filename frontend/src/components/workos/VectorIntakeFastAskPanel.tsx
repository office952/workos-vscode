/**
 * Legacy fast-ask panel (classic intake). Critical SVG/parsing fixes only.
 * New operator rules belong in WorkIntake V2. See VOLUMETRIC_WORKINTAKE_V2_MIGRATION_BOUNDARY.md
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, FileImage, Layers, Sparkles, Upload } from "lucide-react";
import InfoHint from "@/components/workos/templateIntakeWorkspace/InfoHint";
import {
  emptyVectorFastAskAnswers,
  type VolumetricVectorFastAskAnswers,
} from "@/lib/volumetricVectorFastAskMapping";
import {
  VECTOR_FILE_INPUT_ACCEPT,
  formatVectorFileSize,
  validateVectorFileSelection,
  type VectorFileSelectionMetadata,
} from "@/lib/vectorFileSelection";
import {
  analyzeSvgVectorFile,
  layerRoleLabel,
  type SvgVectorAnalysis,
  type SvgVectorDetectedLayer,
  VECTOR_LAYER_ROLE_OPTIONS,
} from "@/lib/svgVectorAnalysis";
import { isSafeRoleSuggestion } from "@/lib/svgLayerRoleSuggestion";
import type { GeometrySuggestionApplyKind } from "@/lib/mapSvgGeometryToSpec";
import {
  PERIMETER_AREA_UNSUPPORTED_MSG,
  parseSvgGeometryFromFile,
  parseSvgGeometryFromText,
  type SvgGeometryParseResult,
} from "@/lib/svgGeometryParser";
import {
  applySuggestedLayerRoles,
  confirmPrimaryLettersLayer,
  deriveSvgParseUiStatus,
  filterVectorReviewWarningsForLocalParse,
  isFilenameOnlyWithoutSvgParse,
  parseStatusLabel,
  primaryLettersLayerFromSpec,
  suggestPrimaryLettersLayer,
  type LettersLayerSuggestionConfidence,
} from "@/lib/svgIntakeFlow";

function fieldClass() {
  return "w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-slate-200 outline-none focus:border-blue-500/50";
}

function labelClass() {
  return "text-[11px] text-slate-400 font-semibold mb-1 block";
}

function sectionHeading(
  icon: React.ReactNode,
  title: string,
  hint?: { label: string; children: React.ReactNode }
) {
  return (
    <div className="flex items-center gap-1">
      {icon}
      <span className="text-[11px] font-semibold text-slate-300">{title}</span>
      {hint ? <InfoHint label={hint.label}>{hint.children}</InfoHint> : null}
    </div>
  );
}

export interface VectorIntakeReviewSummary {
  analysisStatusLabel?: string;
  layerMappingConfirmed?: boolean;
  layerMappingStatusLabel?: string;
  savedMappingsCount?: number;
  savedMappingsList?: string[];
  warnings?: string[];
}

export interface VectorIntakeFastAskPanelProps {
  initialAnswers?: Partial<VolumetricVectorFastAskAnswers>;
  readOnly?: boolean;
  onApply: (answers: VolumetricVectorFastAskAnswers) => void;
  /** Called when operator picks a file — sync metadata to spec before Apply/Save. */
  onFileAttach?: (
    metadata: VectorFileSelectionMetadata,
    analysis?: SvgVectorAnalysis | null
  ) => void;
  /** Live review fields synced to product_spec_json (not only on Apply). */
  manualReviewApproved?: boolean;
  manualReviewNotes?: string;
  onManualReviewChange?: (patch: {
    manualReviewApproved?: boolean;
    manualReviewNotes?: string;
    analysisStatus?: string;
  }) => void;
  reviewSummary?: VectorIntakeReviewSummary;
  /** Persisted or live geometry suggestions from parser MVP. */
  geometrySuggestions?: SvgGeometryParseResult | null;
  onGeometryParsed?: (result: SvgGeometryParseResult) => void;
  onApplyGeometrySuggestion?: (kind: GeometrySuggestionApplyKind) => void;
  /** Persist primary letters layer mapping to product_spec_json. */
  onConfirmLettersLayer?: (
    layers: SvgVectorDetectedLayer[],
    primaryLayerId: string,
    confidence: LettersLayerSuggestionConfidence
  ) => void;
  mappingConfirmed?: boolean;
  primaryLettersLayerId?: string | null;
  /** Background auto-save error from parent editor. */
  saveError?: string | null;
}

function fileMetaFromAnswers(
  answers: Partial<VolumetricVectorFastAskAnswers>
): VectorFileSelectionMetadata | null {
  const name = answers.vectorFileName?.trim();
  if (!name) return null;
  return {
    fileName: name,
    extension: answers.vectorFileExtension ?? name.split(".").pop() ?? "",
    mime: answers.vectorFileMime ?? "",
    sizeBytes: answers.vectorFileSizeBytes ?? 0,
    fileType: "svg",
    selectedAt: answers.vectorFileSelectedAt ?? "",
  };
}

export default function VectorIntakeFastAskPanel({
  initialAnswers,
  readOnly = false,
  onApply,
  onFileAttach,
  manualReviewApproved = false,
  manualReviewNotes = "",
  onManualReviewChange,
  reviewSummary,
  geometrySuggestions: persistedGeometry,
  onGeometryParsed,
  onApplyGeometrySuggestion,
  onConfirmLettersLayer,
  mappingConfirmed = false,
  primaryLettersLayerId: primaryLettersLayerIdProp = null,
  saveError = null,
}: VectorIntakeFastAskPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const localFilePickAtRef = useRef<string | null>(null);
  const latestLocalParseRef = useRef<{ at: string; layerCount: number } | null>(null);
  const lastSvgFileRef = useRef<File | null>(null);
  const lastSvgTextRef = useRef<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [cachedSvgFileName, setCachedSvgFileName] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [svgAnalysis, setSvgAnalysis] = useState<SvgVectorAnalysis | null>(
    initialAnswers?.svgAnalysis ?? null
  );
  const [detectedLayers, setDetectedLayers] = useState<SvgVectorDetectedLayer[]>(
    initialAnswers?.detectedLayers ?? []
  );
  const [selectedFileMeta, setSelectedFileMeta] = useState<VectorFileSelectionMetadata | null>(
    () => fileMetaFromAnswers(initialAnswers ?? {})
  );
  const [geometryResult, setGeometryResult] = useState<SvgGeometryParseResult | null>(
    persistedGeometry ?? null
  );
  const [primaryLettersLayerId, setPrimaryLettersLayerId] = useState<string | null>(
    primaryLettersLayerIdProp
  );

  const lettersLayerSuggestion = useMemo(
    () => suggestPrimaryLettersLayer(detectedLayers),
    [detectedLayers]
  );

  useEffect(() => {
    if (primaryLettersLayerIdProp) {
      setPrimaryLettersLayerId(primaryLettersLayerIdProp);
    }
  }, [primaryLettersLayerIdProp]);

  useEffect(() => {
    if (detectedLayers.length === 0) return;
    const fromSpec = primaryLettersLayerFromSpec(
      { vector_primary_letters_layer_id: primaryLettersLayerIdProp ?? undefined },
      detectedLayers
    );
    if (fromSpec) {
      setPrimaryLettersLayerId(fromSpec);
      return;
    }
    if (!primaryLettersLayerId && lettersLayerSuggestion) {
      setPrimaryLettersLayerId(lettersLayerSuggestion.layerId);
    }
  }, [
    detectedLayers,
    lettersLayerSuggestion,
    primaryLettersLayerId,
    primaryLettersLayerIdProp,
  ]);

  const [answers, setAnswers] = useState<VolumetricVectorFastAskAnswers>(() => {
    const defaults = emptyVectorFastAskAnswers();
    if (!initialAnswers) return defaults;
    const merged = { ...defaults };
    for (const key of Object.keys(initialAnswers) as (keyof VolumetricVectorFastAskAnswers)[]) {
      const value = initialAnswers[key];
      if (value !== undefined) {
        (merged as Record<keyof VolumetricVectorFastAskAnswers, VolumetricVectorFastAskAnswers[keyof VolumetricVectorFastAskAnswers]>)[key] = value;
      }
    }
    return merged;
  });

  const parseUiStatus = deriveSvgParseUiStatus({
    fileName: selectedFileMeta?.fileName ?? answers.vectorFileName,
    analyzing,
    parseOk: svgAnalysis?.parse_ok,
    parseError: analysisError ?? svgAnalysis?.parse_error,
    warningCount:
      (svgAnalysis?.warnings.length ?? 0) +
      (geometryResult?.warnings.length ?? 0),
  });

  const initialFileKey = JSON.stringify({
    name: initialAnswers?.vectorFileName ?? "",
    at: initialAnswers?.vectorFileSelectedAt ?? "",
    size: initialAnswers?.vectorFileSizeBytes ?? 0,
    layerIds: (initialAnswers?.detectedLayers ?? []).map((l) => l.id).join("|"),
    parseOk: initialAnswers?.svgAnalysis?.parse_ok ?? false,
  });

  useEffect(() => {
    const externalAt = initialAnswers?.vectorFileSelectedAt ?? "";
    const localParse = latestLocalParseRef.current;
    // Do not let parent initialSpec (often stale until refresh) clobber local file parse.
    if (localFilePickAtRef.current) {
      if (!externalAt || externalAt <= localFilePickAtRef.current) {
        return;
      }
    }
    if (
      localParse &&
      localParse.layerCount > 0 &&
      (initialAnswers?.detectedLayers?.length ?? 0) < localParse.layerCount
    ) {
      return;
    }
    if (
      latestLocalParseRef.current &&
      latestLocalParseRef.current.layerCount > 0 &&
      !initialAnswers?.detectedLayers?.length
    ) {
      return;
    }
    if (!initialAnswers?.vectorFileName?.trim()) return;

    const meta = fileMetaFromAnswers(initialAnswers);
    if (meta) {
      setSelectedFileMeta(meta);
      setAnswers((prev) => ({
        ...prev,
        vectorFileName: meta.fileName,
        vectorFileMime: meta.mime || undefined,
        vectorFileSizeBytes: meta.sizeBytes > 0 ? meta.sizeBytes : undefined,
        vectorFileExtension: meta.extension,
        vectorFileSelectedAt: meta.selectedAt || prev.vectorFileSelectedAt,
      }));
    }
    if (initialAnswers.detectedLayers?.length) {
      setDetectedLayers(initialAnswers.detectedLayers);
    }
    if (initialAnswers.svgAnalysis) {
      setSvgAnalysis(initialAnswers.svgAnalysis);
    }
  }, [initialFileKey]);

  useEffect(() => {
    if (persistedGeometry?.parseOk) {
      setGeometryResult(persistedGeometry);
    }
  }, [persistedGeometry]);

  const layersMappedForGeometry = useMemo(
    () =>
      detectedLayers.length > 0 &&
      detectedLayers.some((l) => l.confirmed_role !== "unknown"),
    [detectedLayers]
  );

  const runGeometryParse = async (layers: SvgVectorDetectedLayer[]) => {
    let layersForGeo = layers;
    if (!layers.some((l) => l.confirmed_role !== "unknown")) {
      const suggestion = suggestPrimaryLettersLayer(layers);
      if (!suggestion) return;
      layersForGeo = confirmPrimaryLettersLayer(layers, suggestion.layerId);
    }
    let result: SvgGeometryParseResult | null = null;
    if (lastSvgFileRef.current) {
      result = await parseSvgGeometryFromFile(lastSvgFileRef.current, layersForGeo);
    } else if (lastSvgTextRef.current) {
      result = parseSvgGeometryFromText(lastSvgTextRef.current, layersForGeo);
    }
    if (result) {
      setGeometryResult(result);
      onGeometryParsed?.(result);
    }
  };

  const canApply = useMemo(
    () => answers.vectorFileName.trim().length > 0,
    [answers.vectorFileName]
  );

  const set = <K extends keyof VolumetricVectorFastAskAnswers>(
    key: K,
    value: VolumetricVectorFastAskAnswers[K]
  ) => setAnswers((prev) => ({ ...prev, [key]: value }));

  const applyFileMetadata = (
    metadata: VectorFileSelectionMetadata,
    analysis?: SvgVectorAnalysis | null
  ) => {
    localFilePickAtRef.current = metadata.selectedAt;
    setFileError(null);
    setSelectedFileMeta(metadata);
    set("vectorFileName", metadata.fileName);
    set("vectorFileMime", metadata.mime || undefined);
    set("vectorFileSizeBytes", metadata.sizeBytes > 0 ? metadata.sizeBytes : undefined);
    set("vectorFileExtension", metadata.extension);
    set("vectorFileSelectedAt", metadata.selectedAt);
    const analysisForState =
      analysis?.parse_ok && analysis.layers.length > 0
        ? { ...analysis, layers: applySuggestedLayerRoles(analysis.layers) }
        : analysis;
    if (analysisForState?.parse_ok) {
      setSvgAnalysis(analysisForState);
      setDetectedLayers(analysisForState.layers);
      latestLocalParseRef.current = {
        at: metadata.selectedAt,
        layerCount: analysisForState.layers.length,
      };
    } else {
      setSvgAnalysis(analysisForState?.parse_ok ? analysisForState : null);
      setDetectedLayers([]);
      latestLocalParseRef.current = null;
    }
    onFileAttach?.(metadata, analysisForState ?? null);
  };

  const analysisForPersist = (
    analysis: SvgVectorAnalysis | null
  ): SvgVectorAnalysis | null => {
    if (!analysis?.parse_ok || analysis.layers.length === 0) return analysis;
    return { ...analysis, layers: applySuggestedLayerRoles(analysis.layers) };
  };

  const handleFilePick = async (file: File | null) => {
    if (!file) return;
    const result = validateVectorFileSelection(file);
    if (result.ok === false) {
      setFileError(result.error);
      return;
    }

    setAnalyzing(true);
    setAnalysisError(null);
    try {
      let analysis: SvgVectorAnalysis | null = null;
      if (result.metadata.extension === "svg") {
        lastSvgFileRef.current = file;
        lastSvgTextRef.current = await file.text();
        setCachedSvgFileName(file.name);
        analysis = await analyzeSvgVectorFile(file);
        if (!analysis.parse_ok) {
          setAnalysisError(
            analysis.parse_error ?? "Analiza SVG nu a reușit — poți continua manual."
          );
        } else {
          setAnalysisError(null);
        }
      } else {
        lastSvgFileRef.current = null;
        lastSvgTextRef.current = null;
        setCachedSvgFileName(null);
        setGeometryResult(null);
      }
      applyFileMetadata(result.metadata, analysisForPersist(analysis));
      if (analysis?.parse_ok && analysis.layers.length > 0) {
        const withRoles = applySuggestedLayerRoles(analysis.layers);
        await runGeometryParse(withRoles);
      }
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : "Analiza fișierului a eșuat.");
      applyFileMetadata(result.metadata, null);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    void handleFilePick(e.target.files?.[0] ?? null);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (readOnly || analyzing) return;
    void handleFilePick(e.dataTransfer.files?.[0] ?? null);
  };

  const handleReanalyzeCachedFile = () => {
    if (lastSvgFileRef.current) {
      void handleFilePick(lastSvgFileRef.current);
    }
  };

  const updateLayerRole = (layerId: string, role: SvgVectorDetectedLayer["confirmed_role"]) => {
    setDetectedLayers((prev) => {
      const next = prev.map((l) => (l.id === layerId ? { ...l, confirmed_role: role } : l));
      void runGeometryParse(next);
      return next;
    });
  };

  const handleConfirmLettersLayer = () => {
    if (!primaryLettersLayerId || readOnly) return;
    const confirmed = confirmPrimaryLettersLayer(detectedLayers, primaryLettersLayerId);
    setDetectedLayers(confirmed);
    void runGeometryParse(confirmed);
    onConfirmLettersLayer?.(
      confirmed,
      primaryLettersLayerId,
      lettersLayerSuggestion?.confidence ?? "medium"
    );
  };

  const handleApply = () => {
    const layerMappingConfirmed =
      detectedLayers.length > 0 &&
      detectedLayers.every((l) => l.confirmed_role !== "unknown");
    onApply({
      ...answers,
      layerNotes: manualReviewNotes || answers.layerNotes,
      svgAnalysis,
      detectedLayers,
      layerMappingConfirmed,
    });
  };

  const unclearLayers = detectedLayers.some(
    (l) => l.suggested_role === "unknown" && l.confirmed_role === "unknown"
  );

  const showAnalysisSection =
    parseUiStatus !== "not_selected" ||
    svgAnalysis?.parse_ok ||
    detectedLayers.length > 0 ||
    Boolean(reviewSummary?.analysisStatusLabel);

  const filenameOnlyWithoutParse = isFilenameOnlyWithoutSvgParse({
    fileName: answers.vectorFileName,
    hasFilePickMetadata: Boolean(selectedFileMeta?.selectedAt),
    parseOk: svgAnalysis?.parse_ok,
  });

  const reviewWarnings = useMemo(
    () =>
      filterVectorReviewWarningsForLocalParse(reviewSummary?.warnings ?? [], {
        detectedLayers,
        primaryLettersLayerId,
        geometryParseOk: geometryResult?.parseOk,
        mappingConfirmed,
      }),
    [
      reviewSummary?.warnings,
      detectedLayers,
      primaryLettersLayerId,
      geometryResult?.parseOk,
      mappingConfirmed,
    ]
  );

  const reviewNotesValue = manualReviewNotes || answers.layerNotes || "";

  return (
    <div
      className="rounded-lg border border-emerald-900/40 bg-emerald-900/10 p-4 space-y-5"
      data-testid="vector-intake-fast-ask"
      data-surface="vector-intake-review"
    >
      <div
        className="flex items-start gap-2"
        data-testid="vector-intake-review-surface"
      >
        <Sparkles className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-[13px] font-bold text-slate-100">Fișier vector și layere</h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Selectează fișierul, confirmă layerele și răspunde la întrebările rapide — tot
            într-un singur loc. Valorile se aplică în formularul de mai jos.
          </p>
        </div>
      </div>

      {(selectedFileMeta || answers.vectorFileName.trim()) && (
        <div
          className="rounded-lg border border-slate-700/50 bg-slate-900/40 px-3 py-2 space-y-1"
          data-testid="vector-parse-status-banner"
        >
          <p className="text-[11px] font-semibold text-slate-200">
            Status analiză:{" "}
            <span
              data-testid="vector-parse-status-label"
              className={
                parseUiStatus === "parsed"
                  ? "text-emerald-300"
                  : parseUiStatus === "failed"
                    ? "text-red-300"
                    : parseUiStatus === "parsed_with_warnings"
                      ? "text-amber-300"
                      : "text-slate-300"
              }
            >
              {parseStatusLabel(parseUiStatus)}
            </span>
          </p>
          {selectedFileMeta && (
            <p className="text-[10px] text-slate-400" data-testid="vector-parse-file-facts">
              Fișier: {selectedFileMeta.fileName}
              {svgAnalysis?.view_box ? ` · viewBox: ${svgAnalysis.view_box}` : ""}
              {detectedLayers.length > 0
                ? ` · ${detectedLayers.length} layere · ${detectedLayers.reduce((n, l) => n + l.element_count, 0)} elemente`
                : ""}
            </p>
          )}
        </div>
      )}

      {/* 1 — Fișier vector */}
      <div className="space-y-2" data-testid="vector-surface-file-section">
        {sectionHeading(
          <FileImage className="w-3.5 h-3.5 text-slate-500" />,
          "Fișier vector",
          {
            label: "Fișier vector",
            children:
              "Selectează SVG, DXF, DWG, EPS, AI sau PDF. Doar metadatele fișierului sunt salvate — conținutul binar nu este încărcat în stocare până la endpoint dedicat.",
          }
        )}

        <div
          className={`flex flex-wrap items-center gap-2 rounded-lg border border-dashed px-3 py-2 transition-colors ${
            dragOver
              ? "border-emerald-500/60 bg-emerald-900/20"
              : "border-wo-border-strong bg-wo-surface-inset/40"
          }`}
          data-testid="vector-file-drop-zone"
          onDragOver={(e) => {
            e.preventDefault();
            if (!readOnly && !analyzing) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            id="vector-fast-ask-file-input"
            type="file"
            accept={VECTOR_FILE_INPUT_ACCEPT}
            disabled={readOnly || analyzing}
            className="sr-only"
            data-testid="vector-fast-ask-file-input"
            onChange={handleFileInputChange}
          />
          <label
            htmlFor="vector-fast-ask-file-input"
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] font-semibold bg-wo-hover hover:bg-wo-hover border border-wo-border-strong text-slate-200 ${
              readOnly || analyzing ? "opacity-40 pointer-events-none" : "cursor-pointer"
            }`}
            data-testid="vector-fast-ask-file-button"
          >
            <Upload className="w-3.5 h-3.5" />
            {analyzing ? "Se analizează…" : "Selectează fișier vector"}
          </label>
          {cachedSvgFileName && !analyzing && (
            <button
              type="button"
              disabled={readOnly}
              onClick={handleReanalyzeCachedFile}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 disabled:opacity-40"
              data-testid="vector-reanalyze-file"
            >
              Reanalizează fișierul
            </button>
          )}
          {selectedFileMeta && (
            <span
              className="text-[11px] text-emerald-300/90"
              data-testid="vector-fast-ask-selected-file"
            >
              {selectedFileMeta.fileName}
              {selectedFileMeta.sizeBytes > 0
                ? ` · ${formatVectorFileSize(selectedFileMeta.sizeBytes)}`
                : ""}
              {selectedFileMeta.mime ? ` · ${selectedFileMeta.mime}` : ""}
            </span>
          )}
        </div>
        <p className="text-[10px] text-slate-500">
          Trage fișierul SVG aici sau apasă butonul — nu e suficient să scrii doar numele în câmpul
          de mai jos.
        </p>

        {saveError && (
          <p
            className="text-[11px] text-red-400 bg-red-900/15 border border-red-800/40 rounded px-2 py-1.5"
            data-testid="vector-fast-ask-save-error"
            role="alert"
          >
            Salvare automată eșuată: {saveError}. Analiza locală rămâne vizibilă — apasă „Salvează
            specificația”.
          </p>
        )}

        {fileError && (
          <p
            className="text-[11px] text-red-400"
            data-testid="vector-fast-ask-file-error"
            role="alert"
          >
            {fileError}
          </p>
        )}
        {analysisError && (
          <p
            className="text-[11px] text-amber-400"
            data-testid="vector-fast-ask-analysis-error"
            role="alert"
          >
            {analysisError}
          </p>
        )}
        {filenameOnlyWithoutParse && (
          <p
            className="text-[11px] text-amber-300/90 bg-amber-900/10 border border-amber-800/30 rounded px-2 py-1.5"
            data-testid="vector-filename-only-hint"
            role="status"
          >
            Ai introdus doar numele fișierului — analiza SVG nu rulează până nu apeși
            „Selectează fișier vector” și alegi fișierul de pe Desktop.
          </p>
        )}

        <div>
          <label className={labelClass()}>Nume fișier</label>
          <input
            className={fieldClass()}
            value={answers.vectorFileName}
            onChange={(e) => {
              setFileError(null);
              const value = e.target.value;
              set("vectorFileName", value);
              if (!value.trim()) {
                setSelectedFileMeta(null);
                setSvgAnalysis(null);
                setDetectedLayers([]);
                setCachedSvgFileName(null);
              } else if (selectedFileMeta) {
                setSelectedFileMeta({ ...selectedFileMeta, fileName: value });
              }
            }}
            readOnly={readOnly || !selectedFileMeta?.selectedAt}
            placeholder="ex. litere_fata.svg"
            data-testid="vector-fast-ask-filename"
          />
        </div>
        <div>
          <label className={labelClass()}>Note calitate fișier (opțional)</label>
          <input
            className={fieldClass()}
            value={answers.fileQualityNotes ?? ""}
            onChange={(e) => set("fileQualityNotes", e.target.value)}
            readOnly={readOnly}
            placeholder="ex. export Corel, layere separate"
            data-testid="vector-fast-ask-quality-notes"
          />
        </div>
      </div>

      {/* 2 — Analiză SVG */}
      {showAnalysisSection && (
        <div
          className="space-y-2 rounded-lg border border-slate-700/50 bg-slate-900/30 p-3"
          data-testid="vector-surface-analysis-section"
        >
          {sectionHeading(
            <Layers className="w-3.5 h-3.5 text-emerald-400" />,
            "Analiză SVG",
            {
              label: "Analiză SVG",
              children:
                "Rezumat client-side al fișierului SVG. Nu se calculează geometrie pentru ofertă.",
            }
          )}
          {reviewSummary?.analysisStatusLabel && (
            <p className="text-[11px] text-slate-400" data-testid="vector-surface-analysis-status">
              Status: <span className="text-slate-200">{reviewSummary.analysisStatusLabel}</span>
            </p>
          )}
          {detectedLayers.length > 0 && (
            <p className="text-[11px] text-emerald-300/90" data-testid="vector-fast-ask-layer-count">
              {detectedLayers.length}{" "}
              {detectedLayers.length === 1 ? "layer detectat" : "layere detectate"}
            </p>
          )}
          {svgAnalysis?.view_box && (
            <p className="text-[10px] text-slate-500" data-testid="vector-surface-viewbox">
              viewBox: {svgAnalysis.view_box}
              {svgAnalysis.width ? ` · width: ${svgAnalysis.width}` : ""}
              {svgAnalysis.height ? ` · height: ${svgAnalysis.height}` : ""}
            </p>
          )}
          {svgAnalysis?.warnings.map((w) => (
            <p key={w} className="text-[10px] text-amber-400/80" data-testid="vector-surface-warning">
              {w}
            </p>
          ))}
          {reviewWarnings.map((w) => (
            <p key={w} className="text-[10px] text-amber-400/80" data-testid="vector-surface-review-warning">
              {w}
            </p>
          ))}
          {svgAnalysis?.parse_ok && detectedLayers.length === 0 && (
            <p
              className="text-[11px] text-amber-300/90"
              data-testid="vector-fast-ask-no-layers"
            >
              Nu au fost detectate layere SVG. Poți continua manual sau verifica fișierul.
            </p>
          )}
        </div>
      )}

      {/* 3 — Mapare layere */}
      {detectedLayers.length > 0 && (
        <div
          className="space-y-3 rounded-lg border border-slate-700/50 bg-slate-900/30 p-3"
          data-testid="vector-surface-layer-mapping-section"
        >
          {sectionHeading(
            <Layers className="w-3.5 h-3.5 text-emerald-400" />,
            "Mapare layere",
            {
              label: "Layere SVG",
              children:
                "Rolurile sugerate se bazează doar pe numele layerului. Confirmă manual ce reprezintă fiecare layer înainte de salvare.",
            }
          )}
          {unclearLayers && (
            <p className="text-[10px] text-amber-300/90 flex items-start gap-1">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              Nu pot interpreta sigur rolul unor layere. Alege manual ce reprezintă fiecare.
            </p>
          )}
          <div
            className="space-y-2"
            data-testid="vector-fast-ask-detected-layers"
          >
            {detectedLayers.map((layer) => {
              const geoLayer = geometryResult?.layers.find((g) => g.layerId === layer.id);
              return (
              <div
                key={layer.id}
                className="grid gap-2 sm:grid-cols-[1fr_auto] items-center border border-slate-700/40 rounded px-2 py-2"
                data-testid={`vector-fast-ask-layer-row-${layer.id}`}
              >
                <div>
                  <p className="text-[11px] font-semibold text-slate-200">{layer.label}</p>
                  <p className="text-[10px] text-slate-500">
                    {layer.element_count} elemente
                    {layer.id !== layer.label ? ` · id: ${layer.id}` : ""}
                  </p>
                  {geoLayer?.bboxMm && (
                    <p className="text-[10px] text-blue-300/80" data-testid={`vector-layer-bbox-${layer.id}`}>
                      bbox ~{" "}
                      {Math.round(geoLayer.bboxMm.maxX - geoLayer.bboxMm.minX)} ├ù{" "}
                      {Math.round(geoLayer.bboxMm.maxY - geoLayer.bboxMm.minY)} mm
                    </p>
                  )}
                  {isSafeRoleSuggestion(layer.suggested_role) && (
                    <p className="text-[10px] text-slate-400">
                      Sugestie: {layerRoleLabel(layer.suggested_role)}
                    </p>
                  )}
                </div>
                <select
                  className={fieldClass()}
                  value={layer.confirmed_role}
                  disabled={readOnly}
                  onChange={(e) =>
                    updateLayerRole(
                      layer.id,
                      e.target.value as SvgVectorDetectedLayer["confirmed_role"]
                    )
                  }
                  data-testid={`vector-fast-ask-layer-role-${layer.id}`}
                >
                  {VECTOR_LAYER_ROLE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            );
            })}
          </div>

          {detectedLayers.length > 0 && (
            <div
              className="space-y-2 rounded border border-emerald-900/40 bg-emerald-900/10 p-3"
              data-testid="vector-primary-letters-layer-section"
            >
              <p className="text-[11px] font-semibold text-emerald-200">
                Layer principal litere
              </p>
              {lettersLayerSuggestion && (
                <p className="text-[10px] text-slate-400" data-testid="vector-letters-suggestion-reason">
                  Sugestie ({lettersLayerSuggestion.confidence}): {lettersLayerSuggestion.layerLabel} —{" "}
                  {lettersLayerSuggestion.reason}
                </p>
              )}
              <select
                className={fieldClass()}
                value={primaryLettersLayerId ?? ""}
                disabled={readOnly}
                onChange={(e) => setPrimaryLettersLayerId(e.target.value || null)}
                data-testid="vector-primary-letters-layer-select"
              >
                <option value="">Alege layer litere…</option>
                {detectedLayers.map((layer) => (
                  <option key={layer.id} value={layer.id}>
                    {layer.label} ({layer.element_count} elem.)
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={readOnly || !primaryLettersLayerId || mappingConfirmed}
                onClick={handleConfirmLettersLayer}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] font-semibold bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40 text-white"
                data-testid="vector-confirm-letters-layer"
              >
                Confirmă layer litere
              </button>
              {mappingConfirmed && (
                <p className="text-[10px] text-emerald-300" data-testid="vector-letters-layer-confirmed">
                  Layer principal litere confirmat și salvat.
                </p>
              )}
            </div>
          )}
          {(reviewSummary?.savedMappingsCount ?? 0) > 0 &&
            detectedLayers.length === 0 && (
              <div className="space-y-1" data-testid="vector-surface-saved-mappings">
                <p className="text-[10px] text-slate-500 font-semibold">Mapări salvate</p>
                {reviewSummary?.savedMappingsList?.map((line) => (
                  <p key={line} className="text-[10px] text-slate-400">
                    {line}
                  </p>
                ))}
              </div>
            )}
        </div>
      )}

      {/* 3b — Geometrie detectată (sugestii) */}
      {layersMappedForGeometry && geometryResult?.parseOk && (
        <div
          className="space-y-3 rounded-lg border border-blue-900/40 bg-blue-900/10 p-3"
          data-testid="vector-surface-geometry-suggestions"
        >
          {sectionHeading(
            <Layers className="w-3.5 h-3.5 text-blue-400" />,
            "Geometrie detectată din SVG — necesită confirmare",
            {
              label: "Sugestii geometrice",
              children:
                "Dimensiunile provin din bounding-box. Perimetrul și aria se calculează din contururile path din layerul litere când fișierul are unități fizice (mm/cm).",
            }
          )}
          <p className="text-[11px] text-slate-400" data-testid="vector-geometry-confidence">
            Încredere:{" "}
            <span className="text-slate-200 capitalize">{geometryResult.confidence}</span>
          </p>
          {geometryResult.suggestions.assemblyWidthMm != null && (
            <p className="text-[11px] text-slate-300">
              Ansamblu sugerat: {geometryResult.suggestions.assemblyWidthMm} ├ù{" "}
              {geometryResult.suggestions.assemblyHeightMm} mm
            </p>
          )}
          {geometryResult.suggestions.letterLayerWidthMm != null && (
            <p className="text-[11px] text-slate-300">
              Layer litere: {geometryResult.suggestions.letterLayerWidthMm} ├ù{" "}
              {geometryResult.suggestions.letterLayerHeightMm} mm
            </p>
          )}
          {geometryResult.suggestions.supportWidthMm != null && (
            <p className="text-[11px] text-slate-300">
              Suport: {geometryResult.suggestions.supportWidthMm} ├ù{" "}
              {geometryResult.suggestions.supportHeightMm} mm
              {geometryResult.suggestions.supportAreaM2 != null
                ? ` · ~${geometryResult.suggestions.supportAreaM2} m² (bbox)`
                : ""}
            </p>
          )}
          {geometryResult.suggestions.frameWidthMm != null && (
            <p className="text-[11px] text-slate-300">
              Cadru: {geometryResult.suggestions.frameWidthMm} ├ù{" "}
              {geometryResult.suggestions.frameHeightMm} mm
            </p>
          )}
          {geometryResult.suggestions.letterElementCount != null && (
            <p className="text-[11px] text-slate-300">
              Elemente path layer litere: {geometryResult.suggestions.letterElementCount}
            </p>
          )}
          {geometryResult.suggestions.letterPerimeterM != null && (
            <p className="text-[11px] text-emerald-300" data-testid="vector-geometry-perimeter">
              Perimetru litere (extras): {geometryResult.suggestions.letterPerimeterM} m
            </p>
          )}
          {geometryResult.suggestions.letterFaceAreaM2 != null && (
            <p className="text-[11px] text-emerald-300" data-testid="vector-geometry-area">
              Arie față litere (extrasă): {geometryResult.suggestions.letterFaceAreaM2} m²
            </p>
          )}
          {geometryResult.suggestions.letterCount != null && (
            <p className="text-[11px] text-emerald-300" data-testid="vector-geometry-letter-count">
              Litere estimate (contururi): {geometryResult.suggestions.letterCount}
            </p>
          )}
          {!geometryResult.suggestions.letterPerimeterM &&
            !geometryResult.suggestions.letterFaceAreaM2 && (
              <p className="text-[10px] text-amber-300/90">{PERIMETER_AREA_UNSUPPORTED_MSG}</p>
            )}
          {geometryResult.warnings
            .filter((w) => w !== PERIMETER_AREA_UNSUPPORTED_MSG)
            .map((w) => (
              <p key={w} className="text-[10px] text-amber-400/80">
                {w}
              </p>
            ))}
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              type="button"
              disabled={
                readOnly ||
                geometryResult.confidence === "low" ||
                (geometryResult.suggestions.assemblyWidthMm == null &&
                  geometryResult.suggestions.letterLayerWidthMm == null)
              }
              onClick={() => onApplyGeometrySuggestion?.("dimensions")}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white"
              data-testid="vector-geometry-apply-dimensions"
            >
              Aplică dimensiunile sugerate
            </button>
            {geometryResult.suggestions.supportAreaM2 != null && (
              <button
                type="button"
                disabled={readOnly || geometryResult.confidence === "low"}
                onClick={() => onApplyGeometrySuggestion?.("support_area")}
                className="px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200"
                data-testid="vector-geometry-apply-support"
              >
                Aplică aria suportului sugerată
              </button>
            )}
            {geometryResult.suggestions.letterPerimeterM != null &&
              geometryResult.suggestions.letterFaceAreaM2 != null && (
                <button
                  type="button"
                  disabled={readOnly || geometryResult.confidence === "low"}
                  onClick={() => onApplyGeometrySuggestion?.("quote_metrics")}
                  className="px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white"
                  data-testid="vector-geometry-apply-quote-metrics"
                >
                  Aplică geometrie ofertare (perimetru + arie + litere)
                </button>
              )}
            <button
              type="button"
              disabled={readOnly}
              onClick={() => onApplyGeometrySuggestion?.("ignore")}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold border border-slate-600 text-slate-400 hover:text-slate-200"
              data-testid="vector-geometry-ignore"
            >
              Ignoră sugestiile
            </button>
          </div>
          {geometryResult.confidence === "low" && (
            <p className="text-[10px] text-slate-500">
              Încredere redusă — confirmă manual sau reanalizează fișierul cu dimensiuni fizice clare.
            </p>
          )}
        </div>
      )}

      {/* 4 — Întrebări rapide */}
      <div className="space-y-3" data-testid="vector-surface-quick-questions-section">
        {sectionHeading(
          <Sparkles className="w-3.5 h-3.5 text-slate-500" />,
          "Întrebări rapide"
        )}

        <div className="space-y-2">
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-semibold text-slate-300">
              Layerele sunt aliniate corect?
            </span>
            <InfoHint label="Aliniere layere">
              Confirmă dacă fișierul are layere separate pentru litere, suport și alte elemente.
            </InfoHint>
          </div>
          <select
            className={fieldClass()}
            value={answers.layerAlignment}
            onChange={(e) =>
              set("layerAlignment", e.target.value as VolumetricVectorFastAskAnswers["layerAlignment"])
            }
            disabled={readOnly}
            data-testid="vector-fast-ask-layer-alignment"
          >
            <option value="aligned">Da, fișierul este pregătit corect</option>
            <option value="needs_review">Nu / trebuie verificat</option>
            <option value="unknown">Nu știu</option>
          </select>
        </div>

        <div>
          <label className={labelClass()}>Se colantează fața literelor?</label>
          <select
            className={fieldClass()}
            value={answers.faceWrap}
            onChange={(e) => {
              const wrap = e.target.value as VolumetricVectorFastAskAnswers["faceWrap"];
              set("faceWrap", wrap);
              if (wrap === "no") {
                set("faceColantareType", "unknown");
              }
            }}
            disabled={readOnly}
            data-testid="vector-fast-ask-face-wrap"
          >
            <option value="no">Nu — plexiglas vizibil / culoare material</option>
            <option value="yes">Da — autocolant pe față</option>
            <option value="unknown">Nu știu încă</option>
          </select>
        </div>

        {answers.faceWrap === "yes" && (
          <div>
            <label className={labelClass()}>Tip colantare față</label>
            <select
              className={fieldClass()}
              value={answers.faceColantareType}
              onChange={(e) =>
                set(
                  "faceColantareType",
                  e.target.value as VolumetricVectorFastAskAnswers["faceColantareType"]
                )
              }
              disabled={readOnly}
              data-testid="vector-fast-ask-face-colantare-type"
            >
              <option value="oracal_colored">Autocolant colorat Oracal</option>
              <option value="print_laminated">Printat / Laminat</option>
              <option value="unknown">Nu știu încă</option>
            </select>
          </div>
        )}

        <div>
          <label className={labelClass()}>Cant / lateral aluminiu</label>
          <select
            className={fieldClass()}
            value={answers.returnEdgeColor}
            onChange={(e) =>
              set(
                "returnEdgeColor",
                e.target.value as VolumetricVectorFastAskAnswers["returnEdgeColor"]
              )
            }
            disabled={readOnly}
            data-testid="vector-fast-ask-return-edge"
          >
            <option value="white">Alb (stoc)</option>
            <option value="black">Negru (stoc)</option>
            <option value="unknown">Nu știu încă</option>
          </select>
        </div>

        <div>
          <label className={labelClass()}>Adâncime litere</label>
          <select
            className={fieldClass()}
            value={String(answers.letterDepth)}
            onChange={(e) => {
              const v = e.target.value;
              if (v === "custom") {
                set("letterDepth", "custom");
              } else {
                set("letterDepth", Number(v) as 30 | 60 | 80 | 100);
              }
            }}
            disabled={readOnly}
            data-testid="vector-fast-ask-depth"
          >
            <option value="30">30 mm</option>
            <option value="60">60 mm</option>
            <option value="80">80 mm</option>
            <option value="100">100 mm</option>
            <option value="custom">Valoare custom</option>
          </select>
          {answers.letterDepth === "custom" && (
            <input
              type="number"
              min={1}
              className={`${fieldClass()} mt-2`}
              value={answers.customDepthMm ?? ""}
              onChange={(e) =>
                set("customDepthMm", e.target.value ? Number(e.target.value) : undefined)
              }
              readOnly={readOnly}
              placeholder="mm"
              data-testid="vector-fast-ask-depth-custom"
            />
          )}
        </div>

        <div>
          <label className={labelClass()}>Sistem iluminare (față)</label>
          <select
            className={fieldClass()}
            value={answers.lightingSystemType}
            onChange={(e) =>
              set(
                "lightingSystemType",
                e.target.value as VolumetricVectorFastAskAnswers["lightingSystemType"]
              )
            }
            disabled={readOnly}
            data-testid="vector-fast-ask-lighting-system"
          >
            <option value="led_modules">Module LED</option>
            <option value="led_strip">Bandă LED</option>
            <option value="unknown">Nu știu încă</option>
          </select>
        </div>

        {answers.lightingSystemType === "led_modules" && (
          <div>
            <label className={labelClass()}>Putere modul LED</label>
            <select
              className={fieldClass()}
              value={String(answers.ledModulePowerW)}
              onChange={(e) =>
                set(
                  "ledModulePowerW",
                  Number(e.target.value) as VolumetricVectorFastAskAnswers["ledModulePowerW"]
                )
              }
              disabled={readOnly}
              data-testid="vector-fast-ask-led-module-w"
            >
              <option value="0.72">0,72 W</option>
              <option value="1">1 W</option>
              <option value="1.44">1,44 W</option>
              <option value="unknown">Nu știu încă</option>
            </select>
          </div>
        )}

        {answers.lightingSystemType === "led_strip" && (
          <div>
            <label className={labelClass()}>Bandă LED</label>
            <select
              className={fieldClass()}
              value={answers.ledStripDensity}
              onChange={(e) =>
                set(
                  "ledStripDensity",
                  e.target.value as VolumetricVectorFastAskAnswers["ledStripDensity"]
                )
              }
              disabled={readOnly}
              data-testid="vector-fast-ask-led-strip"
            >
              <option value="60_led_per_m">60 LED / m — 5 W/ml</option>
              <option value="120_led_per_m">120 LED / m — 10 W/ml</option>
              <option value="unknown">Nu știu încă</option>
            </select>
          </div>
        )}

        <div>
          <label className={labelClass()}>Temperatură culoare LED</label>
          <select
            className={fieldClass()}
            value={answers.lightColor}
            onChange={(e) =>
              set(
                "lightColor",
                e.target.value as VolumetricVectorFastAskAnswers["lightColor"]
              )
            }
            disabled={readOnly}
            data-testid="vector-fast-ask-led-temp"
          >
            <option value="warm">Lumină caldă</option>
            <option value="cold">Lumină rece</option>
            <option value="unknown">Nu știu încă</option>
          </select>
        </div>
      </div>

      {/* 5 — Aplicare în specificație */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 pt-1">
        <button
          type="button"
          disabled={readOnly || !canApply}
          onClick={handleApply}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-[12px] font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white"
          data-testid="vector-fast-ask-apply"
        >
          Aplică și salvează
        </button>
        <p className="text-[10px] text-slate-500">
          Salvează răspunsurile rapide în specificație (inclusiv pentru simulare).
        </p>
      </div>

      {/* 6 — Review status */}
      <div
        className="space-y-3 rounded-lg border border-wo-border-subtle bg-wo-surface-inset/60 p-3"
        data-testid="vector-surface-review-section"
      >
        {sectionHeading(
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
          "Review status"
        )}

        <div className="flex flex-wrap gap-2 text-[10px]">
          {reviewSummary?.layerMappingConfirmed === true && (
            <span
              className="px-2 py-0.5 rounded bg-emerald-900/30 text-emerald-300 border border-emerald-800/40"
              data-testid="vector-surface-mapping-confirmed"
            >
              Mapare layere confirmată
            </span>
          )}
          {reviewSummary?.layerMappingStatusLabel && (
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {reviewSummary.layerMappingStatusLabel}
            </span>
          )}
          {manualReviewApproved && (
            <span
              className="px-2 py-0.5 rounded bg-emerald-900/30 text-emerald-300 border border-emerald-800/40"
              data-testid="vector-surface-review-approved-badge"
            >
              Review manual confirmat
            </span>
          )}
        </div>

        <label className="flex items-center gap-2 text-[12px] text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={manualReviewApproved === true}
            onChange={(e) => {
              const approved = e.target.checked;
              onManualReviewChange?.({
                manualReviewApproved: approved,
                analysisStatus: approved
                  ? "manual_review_approved"
                  : answers.vectorFileName.trim()
                    ? "attached_unanalyzed"
                    : "not_provided",
              });
            }}
            disabled={readOnly}
            className="rounded border-slate-600"
            data-testid="vector-surface-manual-review-checkbox"
          />
          Confirmare manuală vector (DWG/DXF sau analiză fără metrici)
        </label>
        <p className="text-[10px] text-slate-500">
          Bifează doar după verificarea manuală a fișierului. Nu inventează arie, perimetru sau
          număr de litere.
        </p>

        <div>
          <label className={labelClass()}>Note verificare vector</label>
          <textarea
            className={`${fieldClass()} min-h-[56px] resize-y`}
            value={reviewNotesValue}
            onChange={(e) => {
              const notes = e.target.value;
              set("layerNotes", notes);
              onManualReviewChange?.({ manualReviewNotes: notes });
            }}
            readOnly={readOnly}
            placeholder="Conversie DXF→SVG, verificare contur, reviewer..."
            data-testid="vector-surface-review-notes"
          />
        </div>

        {(reviewSummary?.savedMappingsCount ?? 0) > 0 && (
          <div className="space-y-1" data-testid="vector-surface-persisted-mappings">
            <p className="text-[10px] text-slate-500 font-semibold">
              Mapări salvate ({reviewSummary?.savedMappingsCount})
            </p>
            {reviewSummary?.savedMappingsList?.map((line) => (
              <p key={line} className="text-[10px] text-slate-400 font-mono">
                {line}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
