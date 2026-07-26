/**
 * TPL-VOLUMETRIC-LETTERS — integrated quote workspace (method-first).
 * Replaces generic QuoteWizard UX for this template only.
 *
 * Legacy compatibility path (embedded + standalone QuoteWizard).
 * Do not add new TPL-VOLUMETRIC-LETTERS business logic here; use Intake V6
 * and canonical product_spec_json unless fixing a critical regression.
 * See docs/architecture/VOLUMETRIC_WORKSPACE_MIGRATION_BOUNDARY.md
 */
import { useEffect, useMemo, useState } from "react";
import { useCompanyVatPct } from "@/hooks/useCompanyVatPct";
import {
  X,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Layers,
  Calculator,
  MapPin,
} from "lucide-react";
import { Link } from "react-router-dom";
import type { ProductTemplateEntity } from "@/lib/api";
import { intakesApi, productTemplatesApi } from "@/lib/api";
import {
  priceQuote,
  QuotePricingError,
  type QuoteCreatedPayload,
  type QuotePricingInput,
  type QuotePriceResponse,
} from "@/api/quotes";
import { LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO } from "@/lib/legacyQuotePriceRetirement";
import { LegacyQuotePriceRetiredBanner } from "@/components/workos/LegacyQuotePriceRetiredBanner";
import {
  costSimulationApi,
  type CostSimulationResponse,
} from "@/api/costSimulation";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { parsePreliminaryCostBreakdown } from "@/lib/preliminaryCostBreakdown";
import { computeCommercialPreviewBreakdown } from "@/lib/volumetricCommercialPreview";
import { humanizeQuoteBlocker, type VolumetricQuoteGate } from "@/lib/volumetricQuoteReady";
import { VolumetricCommercialReadinessPanel } from "@/components/workos/VolumetricCommercialReadinessPanel";
import {
  TPL_VOLUMETRIC_LETTERS,
  isCantRalPaintEnabled,
  VOLUMETRIC_FACE_FINISH_OPTIONS,
  VOLUMETRIC_MOUNTING_SYSTEM_OPTIONS,
  VOLUMETRIC_PSU_WATTAGE_OPTIONS,
} from "@/lib/volumetricQuoteInput";
import { evaluateSimulationReadiness } from "@/lib/intakeReadinessStages";
import {
  buildClientMaterialFiles,
  buildInitialVolumetricQuoteFlowState,
  buildSimulateQuoteInputPayload,
  countTerrainChecks,
  hasExtractedVectorGeometry,
  isVolumetricWorkIntakeHandoffCommercialMode,
  summarizeClientMaterials,
  switchCalculationMethod,
  updateFlowDimension,
  updateFlowQuoteInputField,
  updateFlowText,
  type TerrainReadinessChecks,
  type VolumetricCalculationMethod,
  type VolumetricQuoteFlowState,
} from "@/lib/volumetricQuoteFlowState";
import {
  filterActiveTemplatesForQuote,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
} from "@/lib/activeTemplateScope";
import FlowBreadcrumb from "@/components/workos/FlowBreadcrumb";
import {
  parseSiteAuditJson,
  terrainSummaryLabel,
  type IntakeSiteAuditJson,
} from "@/lib/intakeSiteAudit";
import {
  derivePathwayFromSpec,
  PATHWAY_OPTIONS,
  pathwayToCalculationMethod,
} from "@/lib/volumetricIntakePathway";
import { buildIntakeV6Path } from "@/lib/volumetricIntakeRoute";
import VolumetricFinishDisplayPanel from "@/components/workos/VolumetricFinishDisplayPanel";
import VolumetricWorkIntakeHandoffPanel from "@/components/workos/VolumetricWorkIntakeHandoffPanel";

export interface VolumetricLettersQuoteFlowProps {
  onClose: () => void;
  onCreated?: (created: QuoteCreatedPayload) => void;
  /** Navigate/open the quote after operator clicks „Deschide oferta”. */
  onOpenCreatedQuote?: (created: QuoteCreatedPayload) => void;
  initialProductSpec?: IntakeProductSpec | null;
  preferredTemplateCode?: string;
  initialClientName?: string;
  intakeRequestId?: string;
  intakeDbId?: number;
  openedFromIntake?: boolean;
  /** Optional intake description for client materials context. */
  intakeDescription?: string;
  deliveryTypeLabel?: string;
  deadlineLabel?: string;
  siteAuditJson?: IntakeSiteAuditJson | null;
  intakeStatus?: string;
  /** When true, hides duplicate breadcrumb/context — parent workspace owns navigation. */
  embedded?: boolean;
}

const METHOD_OPTIONS: {
  id: VolumetricCalculationMethod;
  title: string;
  subtitle: string;
}[] = [
  {
    id: "vector_first",
    title: "Pornesc de la vector",
    subtitle: "Vector mapat, review manual, geometrie doar dacă e extrasă valid",
  },
  {
    id: "manual_geometry",
    title: "Am geometria",
    subtitle: "Dimensiuni și metrici litere introduse explicit",
  },
  {
    id: "quick_estimate",
    title: "Estimare rapidă",
    subtitle: "Câmpuri minime — nu este ofertă comercială finală",
  },
];

function formatMoney(val: number, currency: string) {
  return `${val.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

function numericCostField(
  source: Record<string, unknown> | undefined,
  key: string
): number | null {
  const value = Number(source?.[key] ?? NaN);
  return Number.isFinite(value) ? value : null;
}

function volumetricQuoteBreadcrumb(intakeId?: string) {
  return [
    { label: "Cereri", to: "/intake" },
    ...(intakeId
      ? [{ label: `Cerere ${intakeId}`, to: buildIntakeV6Path(intakeId) }]
      : []),
    { label: "Ofertare litere volumetrice", active: true },
  ];
}

export default function VolumetricLettersQuoteFlow({
  onClose,
  onCreated,
  onOpenCreatedQuote,
  initialProductSpec = null,
  preferredTemplateCode = OWNER_VALID_ACTIVE_TEMPLATE_CODE,
  initialClientName = "",
  intakeRequestId,
  intakeDbId: intakeDbIdProp,
  openedFromIntake = false,
  intakeDescription = "",
  deliveryTypeLabel,
  deadlineLabel,
  siteAuditJson = null,
  intakeStatus,
  embedded = false,
}: VolumetricLettersQuoteFlowProps) {
  const siteAudit = useMemo(
    () => parseSiteAuditJson(siteAuditJson),
    [siteAuditJson]
  );

  const [flowState, setFlowState] = useState<VolumetricQuoteFlowState>(() =>
    buildInitialVolumetricQuoteFlowState(initialProductSpec, siteAuditJson)
  );
  const [clientName, setClientName] = useState(initialClientName.trim());
  const [templates, setTemplates] = useState<ProductTemplateEntity[]>([]);
  const [templateId, setTemplateId] = useState<number | null>(null);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  const [intakeDbId, setIntakeDbId] = useState<number | undefined>(intakeDbIdProp);
  const [showFullRequestText, setShowFullRequestText] = useState(false);

  const [marginPct, setMarginPct] = useState(25);
  const { vatPct } = useCompanyVatPct();
  const [discountPct, setDiscountPct] = useState(0);

  const [simulating, setSimulating] = useState(false);
  const [simulateError, setSimulateError] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] =
    useState<CostSimulationResponse | null>(null);
  const [commercialSubmitting, setCommercialSubmitting] = useState(false);
  const [commercialError, setCommercialError] = useState<string | null>(null);
  const [commercialResult, setCommercialResult] =
    useState<QuotePriceResponse | null>(null);
  const [blockedReasons, setBlockedReasons] = useState<string[]>([]);
  const [technicalOverrideEnabled, setTechnicalOverrideEnabled] = useState(false);
  const [technicalOverrideReason, setTechnicalOverrideReason] = useState("");

  const commercialHandoffMode = useMemo(
    () =>
      isVolumetricWorkIntakeHandoffCommercialMode({
        openedFromIntake,
        embedded,
        templateCode: preferredTemplateCode,
        productSpec: initialProductSpec,
      }),
    [openedFromIntake, embedded, preferredTemplateCode, initialProductSpec]
  );
  const technicalFieldsEditable =
    !commercialHandoffMode ||
    (technicalOverrideEnabled && technicalOverrideReason.trim().length > 0);

  const selectedTemplate =
    templates.find((t) => t.id === templateId) ?? null;

  const materialFiles = useMemo(
    () =>
      buildClientMaterialFiles(initialProductSpec, intakeDescription),
    [initialProductSpec, intakeDescription]
  );
  const materialSummary = summarizeClientMaterials(materialFiles);
  const terrainProgress = countTerrainChecks(flowState.terrainChecks);
  const geometryExtracted = hasExtractedVectorGeometry(initialProductSpec);
  const cantRalPaintEnabled = isCantRalPaintEnabled(initialProductSpec);
  const simulationReadiness = useMemo(
    () =>
      evaluateSimulationReadiness({
        showVolumetricForm: true,
        confirmedTemplateCode: preferredTemplateCode ?? TPL_VOLUMETRIC_LETTERS,
        productSpec: initialProductSpec,
        flowState,
      }),
    [initialProductSpec, preferredTemplateCode, flowState]
  );
  const simulateReady = simulationReadiness.ready;
  const simulationBlockers = simulationReadiness.missing;

  const costBreakdown = simulationResult
    ? parsePreliminaryCostBreakdown(simulationResult)
    : null;
  const linkedModuleResults = simulationResult?.linked_module_results ?? [];
  const quoteGate = simulationResult?.readiness?.quote_gate as
    | VolumetricQuoteGate
    | undefined;
  const canCreateCommercialQuote =
    quoteGate?.can_create_commercial_quote === true;
  const missingCount =
    (quoteGate?.blockers?.length ?? 0) +
    (simulateReady ? 0 : 1);

  useEffect(() => {
    let alive = true;
    setLoadingTemplates(true);
    productTemplatesApi
      .list({}, { sort: "template_code", limit: 500 })
      .then((rows) => {
        if (!alive) return;
        const active = filterActiveTemplatesForQuote(rows);
        setTemplates(active);
        const preferredCodes = [
          preferredTemplateCode,
          OWNER_VALID_ACTIVE_TEMPLATE_CODE,
          TPL_VOLUMETRIC_LETTERS,
        ].filter(Boolean);
        const preferred = preferredCodes
          .map((code) => active.find((t) => t.template_code === code))
          .find(Boolean);
        setTemplateId(preferred?.id ?? null);
      })
      .catch((err: unknown) => {
        if (!alive) return;
        setTemplatesError(
          err instanceof Error ? err.message : "Eroare la încărcarea șabloanelor."
        );
      })
      .finally(() => {
        if (alive) setLoadingTemplates(false);
      });
    return () => {
      alive = false;
    };
  }, [preferredTemplateCode]);

  useEffect(() => {
    if (intakeDbIdProp != null) {
      setIntakeDbId(intakeDbIdProp);
      return;
    }
    if (!openedFromIntake || !intakeRequestId) {
      setIntakeDbId(undefined);
      return;
    }
    let alive = true;
    intakesApi
      .list({ code: intakeRequestId }, { limit: 1 })
      .then((rows) => {
        if (!alive) return;
        setIntakeDbId(rows[0]?.id);
      })
      .catch(() => {
        if (!alive) return;
        setIntakeDbId(undefined);
      });
    return () => {
      alive = false;
    };
  }, [openedFromIntake, intakeRequestId, intakeDbIdProp]);

  useEffect(() => {
    if (initialClientName?.trim()) {
      setClientName(initialClientName.trim());
    }
  }, [initialClientName]);

  useEffect(() => {
    if (!embedded) return;
    setFlowState(
      buildInitialVolumetricQuoteFlowState(initialProductSpec, siteAuditJson)
    );
  }, [embedded, initialProductSpec, siteAuditJson]);

  async function handleSimulate() {
    if (!selectedTemplate) return;
    setSimulating(true);
    setSimulateError(null);
    setBlockedReasons([]);
    setSimulationResult(null);
    setCommercialResult(null);

    const quote_input = buildSimulateQuoteInputPayload(flowState, initialProductSpec);
    try {
      const sim = await costSimulationApi.simulate({
        template_id: selectedTemplate.id,
        quantity: 1,
        intake_id: intakeDbId,
        quote_input,
        pricing: { margin_pct: marginPct, vat_pct: vatPct, discount_pct: discountPct },
        simulation_context: {
          source: "volumetric_quote_flow",
          reason: "Product 001 preliminary volumetric costing",
        },
      });
      setSimulationResult(sim);
      if (sim.blocked_reasons?.length) {
        setBlockedReasons(sim.blocked_reasons.map(String));
      }
      if (sim.status === "error") {
        setSimulateError("Eroare simulare preliminară.");
      }
    } catch (err) {
      setSimulateError(
        err instanceof Error ? err.message : "Eroare simulare preliminară."
      );
    } finally {
      setSimulating(false);
    }
  }

  async function handleCommercialQuote() {
    setCommercialError(LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO);
    setBlockedReasons(["legacy_quote_price_retired"]);
  }

  const requestExcerpt =
    intakeDescription?.trim() ||
    initialProductSpec?.notes?.trim() ||
    flowState.text ||
    "—";

  return (
    <div className="space-y-3" data-testid={embedded ? "volumetric-quote-embedded" : undefined}>
      {!embedded && (
        <div className="flex items-center justify-between gap-3">
          <FlowBreadcrumb items={volumetricQuoteBreadcrumb(intakeRequestId)} />
          <button
            onClick={onClose}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] rounded border border-[#2A3548] text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          >
            <X className="w-3.5 h-3.5" />
            Închide
          </button>
        </div>
      )}
      {embedded && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] rounded border border-[#2A3548] text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            data-testid="volumetric-quote-back-to-spec"
          >
            <X className="w-3.5 h-3.5" />
            Înapoi la specificație
          </button>
        </div>
      )}

      <LegacyQuotePriceRetiredBanner testId="volumetric-legacy-quote-price-retired" />

      {commercialHandoffMode && (
        <div
          className="flex items-start gap-2 px-3 py-2.5 bg-emerald-900/15 border border-emerald-800/35 rounded-lg text-[11px] text-emerald-200/95"
          data-testid="volumetric-handoff-commercial-banner"
        >
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
          Date tehnice preluate din WorkIntake V2. Oferta comercială se calculează în
          Intake V6 (nu prin acest flux legacy).
        </div>
      )}

      {openedFromIntake && intakeStatus && intakeStatus !== "ready_for_quote" && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg text-[11px] text-amber-300/90">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          Poți calcula preliminar, dar cererea nu este marcată Gata pt. Ofertă.
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-4 items-start">
        <div className="min-w-0 space-y-3">
          {!embedded && (
            <>
              {/* Context strip */}
              <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-4 py-3">
                <div className="flex flex-wrap gap-x-6 gap-y-2 text-[12px]">
                  <div>
                    <p className="text-[9px] uppercase tracking-wide text-slate-500">Client</p>
                    <p className="font-medium text-slate-100">{clientName || "—"}</p>
                  </div>
                  <div>
                    <p className="text-[9px] uppercase tracking-wide text-slate-500">Cerere</p>
                    <p className="font-medium text-slate-100">{intakeRequestId ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-[9px] uppercase tracking-wide text-slate-500">Șablon</p>
                    <p className="font-mono text-blue-300">
                      {selectedTemplate?.template_code ?? OWNER_VALID_ACTIVE_TEMPLATE_CODE}
                    </p>
                  </div>
                  {deliveryTypeLabel && (
                    <div>
                      <p className="text-[9px] uppercase tracking-wide text-slate-500">Tip</p>
                      <p className="font-medium text-slate-100">{deliveryTypeLabel}</p>
                    </div>
                  )}
                  {deadlineLabel && (
                    <div>
                      <p className="text-[9px] uppercase tracking-wide text-slate-500">Termen</p>
                      <p className="font-medium text-amber-300">{deadlineLabel}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-[9px] uppercase tracking-wide text-slate-500">Sursă</p>
                    <p className="font-medium text-slate-100">
                      {openedFromIntake ? "Work Intake" : "Ofertă nouă"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Client info */}
              <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
                <p className="text-[11px] font-semibold text-slate-300 mb-2">
                  Informații primite de la client
                </p>
                <p className="text-[12px] text-slate-400 line-clamp-2">
                  {showFullRequestText ? requestExcerpt : requestExcerpt.slice(0, 160)}
                  {!showFullRequestText && requestExcerpt.length > 160 ? "…" : ""}
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  {flowState.text && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-[#2A3548] text-slate-500">
                      text cerere
                    </span>
                  )}
                  {deliveryTypeLabel?.toLowerCase().includes("montaj") && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-amber-800/50 text-amber-400">
                      montaj exterior
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowFullRequestText((v) => !v)}
                    className="text-[11px] text-blue-400 hover:text-blue-300"
                  >
                    {showFullRequestText ? "Ascunde text" : "Vezi text complet"}
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Materials — collapsed by default */}
          <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-[12px] text-slate-300">{materialSummary}</p>
              <button
                type="button"
                onClick={() =>
                  setFlowState((s) => ({
                    ...s,
                    materialsExpanded: !s.materialsExpanded,
                  }))
                }
                className="text-[11px] text-blue-400 hover:text-blue-300"
              >
                {flowState.materialsExpanded ? "Ascunde materiale" : "Vezi materiale"}
              </button>
            </div>
            {flowState.materialsExpanded && (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                {materialFiles.length === 0 ? (
                  <p className="text-[11px] text-slate-500 col-span-2">
                    Niciun fișier clasificat în specificația intake.
                  </p>
                ) : (
                  materialFiles.map((file) => (
                    <div
                      key={file.id}
                      className="border border-[#2A3548] rounded-md px-3 py-2 bg-[#0f1524]"
                    >
                      <p className="text-[12px] text-slate-200 truncate">{file.name}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {file.category.replace("_", " ")} · {file.status}
                        {file.contextOnly ? " · context" : ""}
                      </p>
                    </div>
                  ))
                )}
              </div>
            )}
            <p className="text-[10px] text-slate-600 mt-2">
              Pozele sunt context — nu alimentează CostEngine și nu deduc dimensiuni sau preț.
            </p>
          </div>

          {!embedded && !commercialHandoffMode && (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
              <h2 className="text-[15px] font-semibold text-slate-100 mb-3">
                Cum vrei să calculezi?
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                {METHOD_OPTIONS.map((opt) => {
                  const active = flowState.method === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() =>
                        setFlowState((s) => switchCalculationMethod(s, opt.id))
                      }
                      className={`text-left rounded-lg border p-3 transition-colors ${
                        active
                          ? "border-blue-500/60 bg-blue-950/30 ring-1 ring-blue-500/30"
                          : "border-[#2A3548] hover:border-slate-500 bg-[#0f1524]"
                      }`}
                    >
                      <p className="text-[13px] font-semibold text-slate-100">{opt.title}</p>
                      <p className="text-[10px] text-slate-500 mt-1">{opt.subtitle}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {commercialHandoffMode && initialProductSpec && (
            <VolumetricWorkIntakeHandoffPanel
              spec={initialProductSpec}
              intakeRequestId={intakeRequestId}
              templateCode={preferredTemplateCode}
              textLabel={flowState.text}
            />
          )}

          {/* Active method content — legacy / override */}
          {initialProductSpec && !commercialHandoffMode && (
            <VolumetricFinishDisplayPanel spec={initialProductSpec} />
          )}

          <div
            className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-4"
            data-testid={embedded ? "volumetric-quote-embedded-summary" : undefined}
          >
            {embedded ? (
              <>
                <EmbeddedIntakeSpecSummary
                  spec={initialProductSpec}
                  geometryExtracted={geometryExtracted}
                />
                <p className="text-[10px] text-slate-500 border-t border-[#1E293B] pt-3">
                  Datele provin din tab-ul <span className="text-blue-400">Specificație</span>.
                  Modifică acolo, apoi recalculează.
                </p>
              </>
            ) : commercialHandoffMode ? (
              <>
                <details
                  className="rounded-md border border-[#2A3548] bg-[#0A0F1A]/30"
                  data-testid="volumetric-advanced-technical-override"
                >
                  <summary className="cursor-pointer px-3 py-2.5 text-[12px] font-medium text-slate-400 hover:text-slate-200">
                    Advanced technical override
                  </summary>
                  <div className="px-3 pb-3 space-y-3 border-t border-[#1E293B]/80 pt-3">
                    <label className="flex items-start gap-2 text-[11px] text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={technicalOverrideEnabled}
                        onChange={(e) => {
                          setTechnicalOverrideEnabled(e.target.checked);
                          if (!e.target.checked) setTechnicalOverrideReason("");
                        }}
                        className="rounded border-slate-600 mt-0.5"
                        data-testid="volumetric-technical-override-toggle"
                      />
                      <span>Activează override tehnic pentru ofertă</span>
                    </label>
                    {technicalOverrideEnabled && (
                      <>
                        <label className="block text-[11px]">
                          <span className="text-slate-400">Motiv override *</span>
                          <input
                            type="text"
                            value={technicalOverrideReason}
                            onChange={(e) => setTechnicalOverrideReason(e.target.value)}
                            placeholder="ex: ajustare perimetru pentru variantă comercială"
                            className="mt-1 w-full bg-[#0f1524] border border-[#2A3548] rounded px-2 py-1.5 text-[12px] text-slate-100"
                            data-testid="volumetric-technical-override-reason"
                          />
                        </label>
                        {technicalFieldsEditable && (
                          <p
                            className="text-[10px] text-amber-300/90 bg-amber-950/20 border border-amber-800/40 rounded px-2.5 py-2"
                            data-testid="volumetric-technical-override-warning"
                          >
                            Atenție: modificările de aici afectează oferta, nu actualizează automat
                            WorkIntake V2.
                          </p>
                        )}
                        {technicalFieldsEditable && (
                          <div className="space-y-3">
                            <GeometryFields
                              state={flowState}
                              readOnly={false}
                              onTextChange={(text) =>
                                setFlowState((s) => updateFlowText(s, text))
                              }
                              onDimensionChange={(field, value, key) =>
                                setFlowState((s) =>
                                  updateFlowDimension(s, field, value, key)
                                )
                              }
                              onQuoteInputChange={(key, value) =>
                                setFlowState((s) =>
                                  updateFlowQuoteInputField(s, key, value)
                                )
                              }
                              compact={false}
                            />
                            <CostOptionsPanel
                              quoteInput={flowState.quoteInput}
                              suggestedKeys={flowState.suggestedKeys}
                              cantRalPaintEnabled={cantRalPaintEnabled}
                              hidePsuWhenMultiUnit={false}
                              onChange={(key, value) =>
                                setFlowState((s) =>
                                  updateFlowQuoteInputField(s, key, value)
                                )
                              }
                            />
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </details>
              </>
            ) : (
              <>
                {flowState.method === "vector_first" && (
                  <VectorMethodPanel
                    spec={initialProductSpec}
                    geometryExtracted={geometryExtracted}
                  />
                )}
                {flowState.method === "quick_estimate" && (
                  <p className="text-[11px] text-amber-400/90 bg-amber-950/20 border border-amber-800/40 rounded px-3 py-2">
                    Estimarea rapidă nu este ofertă comercială finală.
                  </p>
                )}

                <GeometryFields
                  state={flowState}
                  readOnly={!technicalFieldsEditable}
                  onTextChange={(text) => setFlowState((s) => updateFlowText(s, text))}
                  onDimensionChange={(field, value, key) =>
                    setFlowState((s) => updateFlowDimension(s, field, value, key))
                  }
                  onQuoteInputChange={(key, value) =>
                    setFlowState((s) => updateFlowQuoteInputField(s, key, value))
                  }
                  compact={flowState.method === "quick_estimate"}
                />
              </>
            )}

            {!commercialHandoffMode && (
              <details className="group">
                <summary className="cursor-pointer list-none flex items-center justify-between text-[12px] font-medium text-slate-300 py-1">
                  <span>Opțiuni cost — necesare simulare</span>
                  <ChevronDown className="w-4 h-4 text-slate-500 group-open:hidden" />
                  <ChevronUp className="w-4 h-4 text-slate-500 hidden group-open:block" />
                </summary>
                <CostOptionsPanel
                  quoteInput={flowState.quoteInput}
                  suggestedKeys={flowState.suggestedKeys}
                  cantRalPaintEnabled={cantRalPaintEnabled}
                  hidePsuWhenMultiUnit={false}
                  onChange={(key, value) =>
                    setFlowState((s) => updateFlowQuoteInputField(s, key, value))
                  }
                />
              </details>
            )}

            <details className="group">
              <summary className="cursor-pointer list-none flex items-center justify-between text-[12px] font-medium text-slate-300 py-1">
                <span>
                  Cerere &amp; teren · Teren: {terrainProgress.done}/{terrainProgress.total}{" "}
                  verificări · recomandat pentru montaj
                </span>
                <ChevronDown className="w-4 h-4 text-slate-500 group-open:hidden" />
                <ChevronUp className="w-4 h-4 text-slate-500 hidden group-open:block" />
              </summary>
              <TerrainReadOnlySummary
                checks={flowState.terrainChecks}
                siteAudit={siteAudit}
              />
            </details>
          </div>

          {/* Simulation panel */}
          {simulationResult && costBreakdown && (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
              <p className="text-[12px] font-semibold text-slate-200 mb-3 flex items-center gap-2">
                <Calculator className="w-4 h-4 text-blue-400" />
                Rezultat simulare preliminară
              </p>
              <div className="grid grid-cols-3 gap-3 text-[12px]">
                <div>
                  <p className="text-slate-500">Materiale</p>
                  <p className="font-semibold text-slate-100">
                    {formatMoney(costBreakdown.materials, costBreakdown.currency)}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Operații</p>
                  <p className="font-semibold text-slate-100">
                    {formatMoney(costBreakdown.includedOperations, costBreakdown.currency)}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Total</p>
                  <p className="font-semibold text-emerald-300">
                    {formatMoney(costBreakdown.partialTotal, costBreakdown.currency)}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-3 mt-3 text-[10px] text-slate-500">
                <span>persisted=false</span>
                <span>
                  simulate_ready=
                  {String(simulationResult.readiness?.simulate_ready ?? quoteGate?.simulate_ready ?? false)}
                </span>
                <span>
                  can_create_commercial_quote=
                  {String(canCreateCommercialQuote)}
                </span>
              </div>
              {linkedModuleResults.length > 0 && (
                <div
                  className="mt-4 border-t border-[#1E293B] pt-3 space-y-2"
                  data-testid="volumetric-linked-modules-preview"
                >
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
                    <div className="bg-[#0A0F1A] border border-[#1E293B] rounded px-3 py-2">
                      <p className="text-slate-500">Litere volumetrice</p>
                      <p className="font-semibold text-slate-100">
                        {formatMoney(
                          numericCostField(simulationResult.cost_result, "parent_total_cost") ??
                            costBreakdown.partialTotal,
                          costBreakdown.currency
                        )}
                      </p>
                    </div>
                    <div className="bg-[#0A0F1A] border border-[#1E293B] rounded px-3 py-2">
                      <p className="text-slate-500">Module atașate</p>
                      <p className="font-semibold text-blue-300">
                        {formatMoney(
                          numericCostField(simulationResult.cost_result, "linked_modules_total_cost") ?? 0,
                          costBreakdown.currency
                        )}
                      </p>
                    </div>
                    <div className="bg-[#0A0F1A] border border-[#1E293B] rounded px-3 py-2">
                      <p className="text-slate-500">Total compus</p>
                      <p className="font-semibold text-emerald-300">
                        {formatMoney(
                          numericCostField(simulationResult.cost_result, "composite_total_cost") ??
                            costBreakdown.partialTotal,
                          costBreakdown.currency
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {linkedModuleResults.map((module, index) => {
                      const input = module.input_payload ?? {};
                      const total = numericCostField(module.cost_result, "total_cost") ?? 0;
                      return (
                        <div
                          key={`${module.template_code}-${index}`}
                          className="border border-[#2A3548] rounded-md bg-[#0f1524] px-3 py-2"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="text-[12px] font-semibold text-slate-200">
                              Structură metalică premontaj
                            </p>
                            <span className="text-[10px] font-mono text-blue-300">
                              {module.template_code}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2 text-[10px] text-slate-400">
                            <span>material: {String(input.bar_material ?? "—")}</span>
                            <span>profil: {String(input.mounting_bar_profile ?? "—")}</span>
                            <span>lungime: {String(input.premount_bar_length_ml ?? "—")} ml</span>
                            <span className="text-emerald-300">cost: {formatMoney(total, costBreakdown.currency)}</span>
                          </div>
                          <p className="mt-1 text-[10px] text-slate-500">
                            {module.pricing_mode ?? "separate_quote_line"} · {module.execution_mode ?? "linked_child_work"}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {(simulateError || commercialError || blockedReasons.length > 0) && (
            <div className="bg-red-950/20 border border-red-800/40 rounded-lg p-3 text-[11px] text-red-300">
              {simulateError && <p>{simulateError}</p>}
              {commercialError && <p>{commercialError}</p>}
              {blockedReasons.map((r) => (
                <p key={r}>{humanizeQuoteBlocker(r)}</p>
              ))}
            </div>
          )}
        </div>

        {/* Right rail */}
        <aside className="xl:sticky xl:top-4 bg-[#0a0f1a] border border-[#1E293B] rounded-lg p-4 space-y-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Stare ofertare
          </p>
          <RailRow
            label="Date pentru simulare"
            value={simulateReady ? "OK" : "lipsă"}
            ok={simulateReady}
          />
          <RailRow
            label="Ofertă finală"
            value={canCreateCommercialQuote ? "pregătită" : "blocată"}
            ok={canCreateCommercialQuote}
          />
          <div className="text-[11px] text-slate-400 space-y-1">
            <p>Fișiere: {materialSummary.replace("Materiale client: ", "")}</p>
            <p>Ce lipsește: {missingCount}</p>
          </div>
          {commercialHandoffMode && (
            <CommercialPricingPanel
              marginPct={marginPct}
              vatPct={vatPct}
              discountPct={discountPct}
              onMarginChange={setMarginPct}
              onDiscountChange={setDiscountPct}
            />
          )}
          <div className="border-t border-[#1E293B] pt-3 space-y-2">
            <div data-testid="volumetric-production-cost-summary">
              <p className="text-[10px] text-slate-500">Cost estimat producție</p>
              <p className="text-[22px] font-bold text-slate-100">
                {costBreakdown
                  ? formatMoney(costBreakdown.partialTotal, costBreakdown.currency)
                  : "—"}
              </p>
            </div>
            {commercialHandoffMode && costBreakdown && (
              <CommercialPricingPreviewBreakdown
                productionCost={costBreakdown.partialTotal}
                currency={costBreakdown.currency}
                marginPct={marginPct}
                vatPct={vatPct}
                discountPct={discountPct}
              />
            )}
          </div>
          {simulationBlockers.length > 0 && (
            <div
              className="text-[10px] text-amber-300/90 space-y-0.5"
              data-testid="simulation-blockers"
            >
              <p>Pentru simulare lipsesc:</p>
              <ul className="list-disc pl-4">
                {simulationBlockers.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            </div>
          )}
          <button
            type="button"
            onClick={handleSimulate}
            disabled={
              simulating ||
              !selectedTemplate ||
              loadingTemplates ||
              !simulateReady
            }
            data-testid="action-calculate-preliminary"
            className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded bg-blue-600 text-white text-[12px] font-semibold hover:bg-blue-500 disabled:opacity-50"
          >
            {simulating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Calculator className="w-4 h-4" />
            )}
            Calculează preliminar
          </button>
          <button
            type="button"
            onClick={handleCommercialQuote}
            disabled
            title={LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO}
            data-testid="action-create-commercial-quote-retired"
            className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded border border-slate-700 text-slate-500 text-[12px] font-semibold cursor-not-allowed opacity-50"
          >
            <FileText className="w-4 h-4" />
            Ofertă comercială retrasă — folosește Intake V6
          </button>

          {quoteGate && (
            <VolumetricCommercialReadinessPanel
              gate={quoteGate}
              testId="volumetric-flow-readiness"
              compact
            />
          )}

          {templatesError && (
            <p className="text-[10px] text-red-400">{templatesError}</p>
          )}
          {commercialResult && (
            <div className="space-y-2" data-testid="volumetric-commercial-created">
              <p className="text-[10px] text-emerald-400">
                Ofertă{" "}
                <span className="font-mono font-semibold">
                  {commercialResult.quote_code ?? `#${commercialResult.quote_id}`}
                </span>{" "}
                creată.
              </p>
              <button
                type="button"
                data-testid="volumetric-open-created-quote"
                onClick={() => {
                  if (!commercialResult) return;
                  const payload: QuoteCreatedPayload = {
                    quoteId: commercialResult.quote_id,
                    quoteCode: commercialResult.quote_code,
                  };
                  if (onOpenCreatedQuote) {
                    onOpenCreatedQuote(payload);
                    return;
                  }
                  onCreated?.(payload);
                }}
                className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded border border-emerald-700/50 text-emerald-300 text-[12px] font-semibold hover:bg-emerald-950/30"
              >
                <FileText className="w-4 h-4" />
                Deschide oferta
              </button>
            </div>
          )}
          {intakeRequestId && (
            <Link
              to={buildIntakeV6Path(intakeRequestId)}
              className="block text-center text-[11px] text-blue-400 hover:text-blue-300"
            >
              Înapoi la cerere
            </Link>
          )}
        </aside>
      </div>
    </div>
  );
}

function RailRow({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between text-[12px]">
      <span className="text-slate-400">{label}</span>
      <span
        className={`font-medium ${ok ? "text-emerald-400" : "text-amber-400"}`}
      >
        {value}
      </span>
    </div>
  );
}

function EmbeddedIntakeSpecSummary({
  spec,
  geometryExtracted,
}: {
  spec: IntakeProductSpec | null;
  geometryExtracted: boolean;
}) {
  const pathway = derivePathwayFromSpec(spec);
  const pathwayLabel =
    PATHWAY_OPTIONS.find((o) => o.id === pathway)?.title ?? pathway;
  const methodLabel =
    METHOD_OPTIONS.find((o) => o.id === pathwayToCalculationMethod(pathway))?.title ??
    "—";

  const fmt = (v: number | string | undefined | null, suffix = "") =>
    v != null && v !== "" ? `${v}${suffix}` : "—";

  return (
    <div className="space-y-3 text-[11px]">
      <p className="text-[12px] font-semibold text-slate-200">
        Date din specificație salvată
      </p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-2">
        <SummaryRow label="Cale intake" value={pathwayLabel} />
        <SummaryRow label="Metodă simulare" value={methodLabel} />
        <SummaryRow label="Text / denumire" value={spec?.text?.trim() || "—"} />
        <SummaryRow label="Lățime (mm)" value={fmt(spec?.width_mm)} />
        <SummaryRow
          label="Înălțime (mm)"
          value={fmt(spec?.height_mm ?? spec?.letter_height_mm)}
        />
        <SummaryRow
          label="Adâncime (mm)"
          value={fmt(spec?.depth_mm ?? spec?.return_depth_mm)}
        />
        {pathway !== "quick_estimate" && (
          <>
            <SummaryRow
              label="Arie față (m²)"
              value={fmt(spec?.letter_face_area_m2)}
            />
            <SummaryRow
              label="Perimetru (m)"
              value={fmt(spec?.letter_perimeter_m)}
            />
            <SummaryRow label="Nr. litere" value={fmt(spec?.letter_count)} />
          </>
        )}
        {pathway === "vector" && (
          <>
            <SummaryRow
              label="Fișier vector"
              value={spec?.vector_file_name?.trim() || "—"}
            />
            <SummaryRow
              label="Geometrie extrasă"
              value={geometryExtracted ? "da" : "nu"}
            />
          </>
        )}
      </div>
      {pathway === "quick_estimate" && (
        <p className="text-amber-400/90 bg-amber-950/20 border border-amber-800/40 rounded px-3 py-2">
          Estimare rapidă — nu este ofertă comercială finală.
        </p>
      )}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[9px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="font-medium text-slate-200 truncate">{value}</p>
    </div>
  );
}

function VectorMethodPanel({
  spec,
  geometryExtracted,
}: {
  spec: IntakeProductSpec | null;
  geometryExtracted: boolean;
}) {
  const mapped =
    spec?.vector_layer_mapping_status === "mapped" ||
    Boolean(spec?.svg_layer_mappings && Object.keys(spec.svg_layer_mappings).length);
  return (
    <div className="rounded-md border border-[#2A3548] bg-[#0f1524] p-3 space-y-2 text-[11px]">
      <p className="text-slate-300 font-medium flex items-center gap-2">
        <Layers className="w-4 h-4 text-blue-400" />
        Vector &amp; review
      </p>
      <p className="text-slate-400">
        Fișier: {spec?.vector_file_name ?? "—"} · Status:{" "}
        {spec?.vector_analysis_status ?? "necunoscut"}
      </p>
      <p className="text-slate-400">
        Layer mapat: {mapped ? "da" : "nu"} · Review manual:{" "}
        {spec?.vector_manual_review_approved ? "aprobat" : "neconfirmat"}
      </p>
      <p className="text-slate-400">
        Geometrie extrasă valid: {geometryExtracted ? "da" : "nu"}
      </p>
      {!geometryExtracted && (
        <p className="text-amber-400/90">
          Fără geometrie extrasă valid — completați manual câmpurile de mai jos.
        </p>
      )}
      {spec?.vector_file_name && (
        <p className="text-slate-500">
          Vector Studio rămâne în{" "}
          <span className="text-blue-400">Work Intake</span> — fără duplicare aici.
        </p>
      )}
    </div>
  );
}

function GeometryFields({
  state,
  onTextChange,
  onDimensionChange,
  onQuoteInputChange,
  compact,
  readOnly = false,
}: {
  state: VolumetricQuoteFlowState;
  onTextChange: (text: string) => void;
  onDimensionChange: (
    field: "widthMm" | "heightMm" | "depthMm",
    value: number,
    key: "width_mm" | "height_mm" | "depth_mm"
  ) => void;
  onQuoteInputChange: (key: string, value: string) => void;
  compact: boolean;
  readOnly?: boolean;
}) {
  const qi = state.quoteInput;
  return (
    <div
      className="grid grid-cols-2 md:grid-cols-3 gap-3"
      data-testid={readOnly ? "volumetric-geometry-fields-readonly" : "volumetric-geometry-fields"}
    >
      <Field
        label="Denumire / text"
        value={state.text}
        onChange={(v) => onTextChange(v)}
        type="text"
        readOnly={readOnly}
      />
      <Field
        label="Lățime (mm)"
        value={String(state.widthMm)}
        onChange={(v) => onDimensionChange("widthMm", Number(v), "width_mm")}
        readOnly={readOnly}
      />
      <Field
        label="Înălțime (mm)"
        value={String(state.heightMm)}
        onChange={(v) => onDimensionChange("heightMm", Number(v), "height_mm")}
        readOnly={readOnly}
      />
      {!compact && (
        <>
          <Field
            label="Adâncime cant / retur volumetric (mm)"
            value={qi.return_depth_mm ?? String(state.depthMm)}
            onChange={(v) => onQuoteInputChange("return_depth_mm", v)}
            readOnly={readOnly}
          />
          <Field
            label="Arie față litere (m²)"
            value={qi.letter_face_area_m2 ?? ""}
            onChange={(v) => onQuoteInputChange("letter_face_area_m2", v)}
            readOnly={readOnly}
          />
          <Field
            label="Perimetru litere (m)"
            value={qi.letter_perimeter_m ?? ""}
            onChange={(v) => onQuoteInputChange("letter_perimeter_m", v)}
            readOnly={readOnly}
          />
          <Field
            label="Număr litere"
            value={qi.letter_count ?? ""}
            onChange={(v) => onQuoteInputChange("letter_count", v)}
            readOnly={readOnly}
          />
        </>
      )}
    </div>
  );
}

function CostOptionsPanel({
  quoteInput,
  suggestedKeys,
  cantRalPaintEnabled,
  onChange,
  hidePsuWhenMultiUnit = false,
}: {
  quoteInput: Record<string, string>;
  suggestedKeys: string[];
  cantRalPaintEnabled: boolean;
  onChange: (key: string, value: string) => void;
  hidePsuWhenMultiUnit?: boolean;
}) {
  return (
    <div
      className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-3"
      data-testid="volumetric-cost-options-panel"
    >
      {cantRalPaintEnabled && (
        <>
          <Field
            label="RAL"
            value={quoteInput.paint_ral_code ?? ""}
            onChange={(v) => onChange("paint_ral_code", v)}
            type="text"
            hint={suggestedKeys.includes("paint_ral_code") ? "sugerat" : undefined}
          />
          <Field
            label="Tuburi vopsea"
            value={quoteInput.paint_tube_count ?? ""}
            onChange={(v) => onChange("paint_tube_count", v)}
          />
        </>
      )}
      {!hidePsuWhenMultiUnit && (
        <label className="block text-[11px]" data-testid="volumetric-psu-select-field">
          <span className="text-slate-400">PSU (W)</span>
          <select
            value={quoteInput.selected_psu_watts ?? ""}
            onChange={(e) => onChange("selected_psu_watts", e.target.value)}
            className="mt-1 w-full bg-[#0f1524] border border-[#2A3548] rounded px-2 py-1.5 text-[12px] text-slate-100"
          >
            <option value="">—</option>
            {VOLUMETRIC_PSU_WATTAGE_OPTIONS.map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </select>
        </label>
      )}
      <label className="block text-[11px]">
        <span className="text-slate-400">Montaj</span>
        <select
          value={quoteInput.mounting_system ?? ""}
          onChange={(e) => onChange("mounting_system", e.target.value)}
          className="mt-1 w-full bg-[#0f1524] border border-[#2A3548] rounded px-2 py-1.5 text-[12px] text-slate-100"
        >
          {VOLUMETRIC_MOUNTING_SYSTEM_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-[11px] col-span-2">
        <span className="inline-flex items-center gap-2 text-slate-400">
          <input
            type="checkbox"
            checked={quoteInput.mounting_template_enabled !== "false"}
            onChange={(e) =>
              onChange("mounting_template_enabled", e.target.checked ? "true" : "false")
            }
          />
          Șablon Forex
        </span>
      </label>
      <Field
        label="Arie șablon (m²)"
        value={quoteInput.mounting_template_area_m2 ?? ""}
        onChange={(v) => onChange("mounting_template_area_m2", v)}
        hint={
          suggestedKeys.includes("mounting_template_area_m2")
            ? "sugerat din arie față"
            : undefined
        }
      />
      <label className="block text-[11px]">
        <span className="text-slate-400">Finisaj față</span>
        <select
          value={quoteInput.face_finish_type ?? "none"}
          onChange={(e) => onChange("face_finish_type", e.target.value)}
          className="mt-1 w-full bg-[#0f1524] border border-[#2A3548] rounded px-2 py-1.5 text-[12px] text-slate-100"
        >
          {VOLUMETRIC_FACE_FINISH_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

function CommercialPricingPreviewBreakdown({
  productionCost,
  currency,
  marginPct,
  vatPct,
  discountPct,
}: {
  productionCost: number;
  currency: string;
  marginPct: number;
  vatPct: number;
  discountPct: number;
}) {
  const preview = computeCommercialPreviewBreakdown({
    productionCost,
    marginPct,
    discountPct,
    vatPct,
  });
  if (!preview) {
    return null;
  }

  const showDiscount = discountPct > 0;

  return (
    <div
      className="space-y-1 text-[10px] text-slate-400"
      data-testid="volumetric-commercial-preview-breakdown"
    >
      <PreviewBreakdownRow
        label={`Adaos comercial ${marginPct}%`}
        value={`+${formatMoney(preview.markupValue, currency)}`}
        testId="volumetric-preview-markup"
      />
      <PreviewBreakdownRow
        label="Preț ofertă fără TVA"
        value={formatMoney(preview.priceBeforeVat, currency)}
        testId="volumetric-preview-price-before-vat"
      />
      {showDiscount && (
        <>
          <PreviewBreakdownRow
            label={`Discount ${discountPct}%`}
            value={`-${formatMoney(preview.discountValue, currency)}`}
            testId="volumetric-preview-discount"
          />
          <PreviewBreakdownRow
            label="Subtotal fără TVA după discount"
            value={formatMoney(preview.subtotalBeforeVat, currency)}
            testId="volumetric-preview-subtotal"
          />
        </>
      )}
      <PreviewBreakdownRow
        label={`TVA ${vatPct}%`}
        value={`+${formatMoney(preview.vatValue, currency)}`}
        testId="volumetric-preview-vat"
      />
      <PreviewBreakdownRow
        label="Total estimat cu TVA"
        value={formatMoney(preview.totalWithVat, currency)}
        testId="volumetric-preview-total-with-vat"
        emphasized
      />
      <p className="text-[9px] text-slate-500 pt-1">
        Estimare internă (nu este preț client). Oferta comercială se calculează în Intake V6.
      </p>
    </div>
  );
}

function PreviewBreakdownRow({
  label,
  value,
  testId,
  emphasized = false,
}: {
  label: string;
  value: string;
  testId: string;
  emphasized?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-2" data-testid={testId}>
      <span className={emphasized ? "text-slate-300 font-medium" : undefined}>{label}</span>
      <span className={emphasized ? "text-slate-100 font-semibold" : "text-slate-300"}>
        {value}
      </span>
    </div>
  );
}

function CommercialPricingPanel({
  marginPct,
  vatPct,
  discountPct,
  onMarginChange,
  onDiscountChange,
}: {
  marginPct: number;
  vatPct: number;
  discountPct: number;
  onMarginChange: (v: number) => void;
  onDiscountChange: (v: number) => void;
}) {
  return (
    <div
      className="border-t border-[#1E293B] pt-3 space-y-2"
      data-testid="volumetric-commercial-pricing"
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Parametri comerciali
      </p>
      <div className="grid grid-cols-3 gap-2">
        <Field
          label="Adaos comercial %"
          value={String(marginPct)}
          onChange={(v) => onMarginChange(Number(v) || 0)}
          readOnly={false}
        />
        <div data-testid="volumetric-settings-vat-readonly">
          <Field
            label="TVA % (Settings)"
            value={String(vatPct)}
            onChange={() => undefined}
            readOnly={true}
          />
        </div>
        <Field
          label="Discount %"
          value={String(discountPct)}
          onChange={(v) => onDiscountChange(Number(v) || 0)}
          readOnly={false}
        />
      </div>
    </div>
  );
}

function TerrainReadOnlySummary({
  checks,
  siteAudit,
}: {
  checks: TerrainReadinessChecks;
  siteAudit: ReturnType<typeof parseSiteAuditJson>;
}) {
  const items: { key: keyof TerrainReadinessChecks; label: string }[] = [
    { key: "locationVerified", label: "Locație montaj verificată" },
    { key: "photosVerified", label: "Poze locație verificate" },
    { key: "powerVerified", label: "Alimentare electrică verificată" },
    { key: "accessVerified", label: "Acces montaj verificat" },
  ];
  return (
    <div className="mt-3 space-y-2">
      <p className="text-[10px] text-slate-500">{terrainSummaryLabel(siteAudit)}</p>
      {siteAudit.mounting_address && (
        <p className="text-[11px] text-slate-400">
          Adresă: {siteAudit.mounting_address}
        </p>
      )}
      {items.map((item) => (
        <div
          key={item.key}
          className="flex items-center gap-2 text-[11px] text-slate-300"
        >
          {checks[item.key] ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-3.5 h-3.5 text-slate-500" />
          )}
          {item.label}
        </div>
      ))}
      <p className="text-[10px] text-slate-600">
        Date din Work Intake — nu sunt intrări CostEngine. Editează în cerere.
      </p>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "number",
  hint,
  readOnly = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "number";
  hint?: string;
  readOnly?: boolean;
}) {
  return (
    <label className="block text-[11px]">
      <span className="text-slate-400">
        {label}
        {hint ? ` (${hint})` : ""}
      </span>
      <input
        type={type}
        value={value}
        readOnly={readOnly}
        disabled={readOnly}
        onChange={(e) => onChange(e.target.value)}
        className={`mt-1 w-full border border-[#2A3548] rounded px-2 py-1.5 text-[12px] ${
          readOnly
            ? "bg-[#0A0F1A]/60 text-slate-400 cursor-default"
            : "bg-[#0f1524] text-slate-100"
        }`}
      />
    </label>
  );
}
