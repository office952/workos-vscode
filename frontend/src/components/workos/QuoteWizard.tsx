/**
 * QuoteWizard — multi-step UI for pricing a hierarchical product template.
 *
 * Currently wired for TPL-ACP-LIGHT-ROUTED (Sprint #22). Steps:
 *   1. Select client + template (TPL-ACP-LIGHT-ROUTED preselected if present).
 *   2. Configure quantity + dimensions.
 *   3. Fill quote_input (the formula-based inputs required by the template).
 *   4. Choose pricing (margin/VAT/discount) and preview the priced snapshot.
 *
 * The wizard NEVER computes costs locally. Step 4 calls
 *   POST /api/v1/entities/quotes/price
 * and renders the backend-provided breakdown verbatim.
 *
 * On successful priced response, `onCreated(quoteId)` is invoked so the
 * parent page can refresh the quotes list and select the new quote.
 *
 * Validation block (HTTP 422) is surfaced via `QuotePricingError.blockedReasons`
 * so users immediately see WHICH quote_input keys are missing.
 */
import { useEffect, useMemo, useState } from "react";
import { useCompanyVatPct } from "@/hooks/useCompanyVatPct";
import {
  X,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  FileText,
  Ruler,
  Sliders,
  DollarSign,
} from "lucide-react";
import type { ProductTemplateEntity } from "@/lib/api";
import { intakesApi, productTemplatesApi } from "@/lib/api";
import {
  priceQuote,
  QuotePricingError,
  type QuoteCreatedPayload,
  type QuoteInputPayload,
  type QuotePricingInput,
  type QuotePriceResponse,
  type QuoteUserConfig,
} from "@/api/quotes";
import { LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO } from "@/lib/legacyQuotePriceRetirement";
import { LegacyQuotePriceRetiredBanner } from "@/components/workos/LegacyQuotePriceRetiredBanner";
import {
  costSimulationApi,
  type CostSimulationResponse,
} from "@/api/costSimulation";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { parsePreliminaryCostBreakdown } from "@/lib/preliminaryCostBreakdown";
import SvgLayerAnalysisPanel from "@/components/workos/SvgLayerAnalysisPanel";
import { humanizeQuoteBlocker, type VolumetricQuoteGate } from "@/lib/volumetricQuoteReady";
import { VolumetricCommercialReadinessPanel } from "@/components/workos/VolumetricCommercialReadinessPanel";
import {
  buildVolumetricQuoteInputPayload,
  describeVolumetricIntakePrefill,
  applyVolumetricQuoteInputDefaults,
  enrichVolumetricQuoteInputStrings,
  isVolumetricLettersTemplateCode,
  mapProductSpecToVolumetricQuotePrefill,
  TPL_VOLUMETRIC_LETTERS,
  VOLUMETRIC_QUOTE_INPUT_FIELDS,
  volumetricQuoteInputStepValid,
} from "@/lib/volumetricQuoteInput";
import {
  filterActiveTemplatesForQuote,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
} from "@/lib/activeTemplateScope";
import VolumetricLettersQuoteFlow from "@/components/workos/VolumetricLettersQuoteFlow";

// ------------------------------------------------------------
// Quote input schema — per template
// ------------------------------------------------------------
// For TPL-ACP-LIGHT-ROUTED, the seed script declares these requires_quote_input
// keys (see scripts/seed_tpl_acp_light_routed.py). We surface them here with
// human-readable labels and units. If the template changes in the future, the
// seed remains the source of truth; this table is a presentation layer only.
interface QuoteInputFieldSpec {
  key: keyof QuoteInputPayload & string;
  label: string;
  unit: string;
  placeholder: string;
  helper: string;
  min: number;
  computed?: boolean;
  boolean?: boolean;
  optional?: boolean;
  selectOptions?: readonly number[];
  enumOptions?: readonly { value: string; label: string }[];
  defaultEnum?: string;
}

const ACP_LIGHT_ROUTED_FIELDS: QuoteInputFieldSpec[] = [
  {
    key: "front_face_area_m2",
    label: "Aria fața panoului",
    unit: "m²",
    placeholder: "2.00",
    helper: "Aria totală a feței ACP (width × height în m²).",
    min: 0,
  },
  {
    key: "personalization_path_length_mm",
    label: "Lungime traseu personalizare ACP",
    unit: "mm",
    placeholder: "3000",
    helper: "Lungimea totală a traseului de frezare personalizare pe ACP.",
    min: 0,
  },
  {
    key: "personalization_bounding_area_m2",
    label: "Aria bounding personalizare (difuzor)",
    unit: "m²",
    placeholder: "0.60",
    helper: "Bounding-box-ul zonei personalizate — folosit pentru difuzor.",
    min: 0,
  },
  {
    key: "diffuser_cut_path_length_mm",
    label: "Lungime traseu debitare difuzor",
    unit: "mm",
    placeholder: "4000",
    helper: "Lungimea traseului de debitare pentru plexiglas opal 3mm.",
    min: 0,
  },
  {
    key: "led_count",
    label: "Număr module LED",
    unit: "buc",
    placeholder: "55",
    helper: "Numărul de module LED (poate fi estimat din aria feței).",
    min: 0,
  },
  {
    key: "relief_cut_path_length_mm",
    label: "Lungime traseu relief plexi 10mm",
    unit: "mm",
    placeholder: "4000",
    helper: "Lungimea traseului de frezare pentru relief plexi 10mm (4 treceri).",
    min: 0,
  },
];

function fieldsForTemplate(
  tpl: ProductTemplateEntity | null
): QuoteInputFieldSpec[] {
  if (!tpl) return [];
  if (tpl.template_code === "TPL-ACP-LIGHT-ROUTED") {
    return ACP_LIGHT_ROUTED_FIELDS;
  }
  if (isVolumetricLettersTemplateCode(tpl.template_code)) {
    return VOLUMETRIC_QUOTE_INPUT_FIELDS as QuoteInputFieldSpec[];
  }
  return [];
}

// ------------------------------------------------------------
// Component
// ------------------------------------------------------------
export interface QuoteWizardProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (created: QuoteCreatedPayload) => void;
  onOpenCreatedQuote?: (created: QuoteCreatedPayload) => void;
  /** Optional intake capture — prefill safe quote_input keys only (no invented geometry). */
  initialProductSpec?: IntakeProductSpec | null;
  preferredTemplateCode?: string;
  /** Prefill client name when opened from Work Intake. */
  initialClientName?: string;
  /** Intake request id for source banner (display only). */
  intakeRequestId?: string;
  /** DB intake id when known (vector readiness gate). */
  intakeDbId?: number;
  openedFromIntake?: boolean;
  deliveryTypeLabel?: string;
  siteAuditJson?: import("@/lib/intakeSiteAudit").IntakeSiteAuditJson | null;
  intakeStatus?: string;
}

type Step = 1 | 2 | 3 | 4;

const STEPS: { idx: Step; label: string; icon: React.ElementType }[] = [
  { idx: 1, label: "Client & șablon", icon: FileText },
  { idx: 2, label: "Cantitate & dimensiuni", icon: Ruler },
  { idx: 3, label: "Parametri formulă", icon: Sliders },
  { idx: 4, label: "Preț & preview", icon: DollarSign },
];

function formatRON(val: number) {
  return val.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function QuoteWizard({
  open,
  onClose,
  onCreated,
  onOpenCreatedQuote,
  initialProductSpec = null,
  preferredTemplateCode,
  initialClientName,
  intakeRequestId,
  intakeDbId: intakeDbIdProp,
  openedFromIntake = false,
  deliveryTypeLabel,
  siteAuditJson = null,
  intakeStatus,
}: QuoteWizardProps) {
  // ------------------------------------------------------------
  // State
  // ------------------------------------------------------------
  const [step, setStep] = useState<Step>(1);

  // Step 1 — client + template
  const [clientName, setClientName] = useState("");
  const [templates, setTemplates] = useState<ProductTemplateEntity[]>([]);
  const [templateId, setTemplateId] = useState<number | null>(null);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [templatesError, setTemplatesError] = useState<string | null>(null);

  // Step 2 — user_config
  const [quantity, setQuantity] = useState<number>(1);
  const [widthMm, setWidthMm] = useState<number>(1000);
  const [heightMm, setHeightMm] = useState<number>(2000);
  const [depthMm, setDepthMm] = useState<number>(80);

  // Step 3 — quote_input (keyed by field.key)
  const [quoteInput, setQuoteInput] = useState<Record<string, string>>({});

  // Step 4 — pricing
  const [marginPct, setMarginPct] = useState<number>(25);
  const { vatPct } = useCompanyVatPct(open);
  const [discountPct, setDiscountPct] = useState<number>(0);

  // Submission
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [blockedReasons, setBlockedReasons] = useState<string[]>([]);
  const [result, setResult] = useState<QuotePriceResponse | null>(null);
  const [simulationResult, setSimulationResult] =
    useState<CostSimulationResponse | null>(null);
  const [intakeDbId, setIntakeDbId] = useState<number | undefined>(intakeDbIdProp);
  const [commercialSubmitting, setCommercialSubmitting] = useState(false);
  const [commercialError, setCommercialError] = useState<string | null>(null);

  const selectedTemplate =
    templates.find((t) => t.id === templateId) ?? null;
  const isVolumetricPreliminary = isVolumetricLettersTemplateCode(
    selectedTemplate?.template_code
  );
  const intakePrefillSummary = useMemo(
    () =>
      openedFromIntake
        ? describeVolumetricIntakePrefill(initialProductSpec)
        : null,
    [openedFromIntake, initialProductSpec]
  );
  const quoteFields = useMemo(
    () => fieldsForTemplate(selectedTemplate),
    [selectedTemplate]
  );

  // ------------------------------------------------------------
  // Load templates when the wizard opens
  // ------------------------------------------------------------
  useEffect(() => {
    if (!open) return;
    let alive = true;
    setLoadingTemplates(true);
    setTemplatesError(null);
    productTemplatesApi
      .list({}, { sort: "template_code", limit: 500 })
      .then((rows) => {
        if (!alive) return;
        const active = filterActiveTemplatesForQuote(rows);
        setTemplates(active);
        const preferredCode =
          preferredTemplateCode ?? OWNER_VALID_ACTIVE_TEMPLATE_CODE;
        const preferred = active.find(
          (t) => t.template_code === preferredCode
        );
        setTemplateId(
          (preferred ?? active[0])?.id ?? null
        );
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
  }, [open, preferredTemplateCode, initialProductSpec]);

  useEffect(() => {
    if (!open || !initialClientName?.trim()) return;
    setClientName(initialClientName.trim());
  }, [open, initialClientName]);

  useEffect(() => {
    if (!open || !isVolumetricPreliminary) return;
    const prefill = mapProductSpecToVolumetricQuotePrefill(initialProductSpec);
    setQuoteInput((prev) =>
      applyVolumetricQuoteInputDefaults({ ...prefill, ...prev })
    );
    const depth = initialProductSpec?.return_depth_mm;
    if (depth != null && [30, 60, 80, 100].includes(depth)) {
      setDepthMm(depth);
    }
  }, [open, isVolumetricPreliminary, initialProductSpec]);

  useEffect(() => {
    if (!open) return;
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
  }, [open, openedFromIntake, intakeRequestId, intakeDbIdProp]);

  // Reset wizard state when closed
  useEffect(() => {
    if (open) return;
    setStep(1);
    setClientName("");
    setQuantity(1);
    setWidthMm(1000);
    setHeightMm(2000);
    setDepthMm(80);
    setQuoteInput({});
    setMarginPct(25);
    setDiscountPct(0);
    setSubmitting(false);
    setSubmitError(null);
    setBlockedReasons([]);
    setResult(null);
    setSimulationResult(null);
    setCommercialSubmitting(false);
    setCommercialError(null);
    setIntakeDbId(undefined);
  }, [open]);

  // ------------------------------------------------------------
  // Validation helpers
  // ------------------------------------------------------------
  const step1Valid = clientName.trim().length > 0 && templateId !== null;
  const step2Valid =
    quantity >= 1 && widthMm > 0 && heightMm > 0 && depthMm >= 0;
  const step3Valid = useMemo(() => {
    if (isVolumetricPreliminary) {
      return volumetricQuoteInputStepValid(quoteInput, { widthMm });
    }
    for (const f of quoteFields) {
      const raw = quoteInput[f.key];
      if (raw === undefined || raw === "") return false;
      const n = Number(raw);
      if (!Number.isFinite(n) || n < f.min) return false;
    }
    return true;
  }, [quoteFields, quoteInput, isVolumetricPreliminary, widthMm]);
  const step4Valid =
    marginPct >= 0 && vatPct >= 0 && discountPct >= 0 && discountPct <= 100;

  // ------------------------------------------------------------
  // Step navigation
  // ------------------------------------------------------------
  function goNext() {
    setSubmitError(null);
    setBlockedReasons([]);
    if (step === 1 && step1Valid) setStep(2);
    else if (step === 2 && step2Valid) setStep(3);
    else if (step === 3 && step3Valid) setStep(4);
  }
  function goBack() {
    setSubmitError(null);
    setBlockedReasons([]);
    if (step > 1) setStep(((step - 1) as Step));
  }

  // ------------------------------------------------------------
  // Submit — legacy /entities/quotes/price is RETIRED (use Intake V6 / 7G)
  // ------------------------------------------------------------
  async function handleSubmit() {
    if (!selectedTemplate) return;
    setSubmitting(true);
    setSubmitError(null);
    setBlockedReasons([]);
    setSimulationResult(null);
    setResult(null);

    const user_config: QuoteUserConfig = {
      quantity,
      dimensions: {
        width_mm: widthMm,
        height_mm: heightMm,
        depth_mm: depthMm,
      },
    };
    const pricing: QuotePricingInput = {
      margin_pct: marginPct,
      vat_pct: vatPct,
      discount_pct: discountPct,
    };

    if (!isVolumetricPreliminary) {
      setSubmitError(LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO);
      setBlockedReasons(["legacy_quote_price_retired"]);
      setSubmitting(false);
      return;
    }

    if (isVolumetricPreliminary) {
      const qi = buildVolumetricQuoteInputPayload(quoteInput);
      try {
        const sim = await costSimulationApi.simulate({
          template_id: selectedTemplate.id,
          quantity,
          intake_id: intakeDbId,
          quote_input: {
            ...qi,
            width_mm: widthMm,
            height_mm: heightMm,
            depth_mm: depthMm,
          },
          pricing: {
            margin_pct: marginPct,
            vat_pct: vatPct,
            discount_pct: discountPct,
          },
          simulation_context: {
            source: "quote_wizard",
            reason: "Product 001 preliminary volumetric costing",
          },
        });
        setSimulationResult(sim);
        if (sim.blocked_reasons?.length) {
          setBlockedReasons(sim.blocked_reasons.map(String));
        }
        if (sim.status === "error") {
          setSubmitError("Eroare simulare preliminară.");
        } else if (
          sim.status === "blocked" &&
          Number((sim.cost_result as { total_cost?: number })?.total_cost ?? 0) <= 0
        ) {
          setSubmitError(
            "Calcul preliminar blocat — verificați parametrii și registry."
          );
        }
      } catch (err) {
        setSubmitError(
          err instanceof Error ? err.message : "Eroare simulare preliminară."
        );
      } finally {
        setSubmitting(false);
      }
      return;
    }

    const qi: QuoteInputPayload = {};
    for (const f of quoteFields) {
      const raw = quoteInput[f.key];
      if (raw !== undefined && raw !== "") {
        qi[f.key] = Number(raw);
      }
    }

    try {
      const resp = await priceQuote({
        product_template: selectedTemplate,
        user_config,
        pricing,
        client_name: clientName.trim(),
        quote_input: Object.keys(qi).length > 0 ? qi : undefined,
      });
      setResult(resp);
      onCreated?.({ quoteId: resp.quote_id, quoteCode: resp.quote_code });
    } catch (err) {
      if (err instanceof QuotePricingError) {
        setSubmitError(err.message);
        setBlockedReasons(err.blockedReasons);
      } else {
        setSubmitError(
          err instanceof Error ? err.message : "Eroare necunoscută."
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCommercialQuote() {
    setCommercialError(LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO);
    setBlockedReasons(["legacy_quote_price_retired"]);
  }

  const volumetricQuoteGate = simulationResult?.readiness?.quote_gate as
    | VolumetricQuoteGate
    | undefined;
  const canCreateCommercialQuote =
    volumetricQuoteGate?.can_create_commercial_quote === true;

  if (!open) return null;

  if (isVolumetricLettersTemplateCode(preferredTemplateCode)) {
    return (
      <VolumetricLettersQuoteFlow
        onClose={onClose}
        onCreated={onCreated}
        onOpenCreatedQuote={onOpenCreatedQuote}
        initialProductSpec={initialProductSpec}
        preferredTemplateCode={preferredTemplateCode}
        initialClientName={initialClientName}
        intakeRequestId={intakeRequestId}
        intakeDbId={intakeDbIdProp}
        openedFromIntake={openedFromIntake}
        deliveryTypeLabel={deliveryTypeLabel}
        siteAuditJson={siteAuditJson}
        intakeStatus={intakeStatus}
      />
    );
  }

  // ------------------------------------------------------------
  // Render
  // ------------------------------------------------------------
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl max-h-[90vh] bg-wo-surface-inset border border-border rounded-xl shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" />
            <h2 className="text-[14px] font-semibold text-foreground">
              {isVolumetricPreliminary ? "Calcul preliminar" : "Ofertă nouă"}
            </h2>
            {selectedTemplate && (
              <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-mono bg-blue-900/30 text-blue-300 border border-blue-800/50">
                {selectedTemplate.template_code}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground"
            aria-label="Închide"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {openedFromIntake && (
          <IntakeSourceBanner
            intakeRequestId={intakeRequestId}
            prefillSummary={intakePrefillSummary}
          />
        )}

        <div className="px-5 pt-3">
          <LegacyQuotePriceRetiredBanner />
        </div>

        {/* Stepper */}
        <div className="px-5 py-3 border-b border-border bg-background">
          <div className="flex items-center gap-2">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const done = step > s.idx;
              const active = step === s.idx;
              return (
                <div key={s.idx} className="flex items-center gap-2">
                  <div
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] border ${
                      active
                        ? "bg-blue-600/20 text-blue-300 border-blue-600/50"
                        : done
                        ? "bg-emerald-900/30 text-emerald-300 border-emerald-800/50"
                        : "bg-transparent text-muted-foreground border-wo-border-strong"
                    }`}
                  >
                    {done ? (
                      <CheckCircle2 className="w-3 h-3" />
                    ) : (
                      <Icon className="w-3 h-3" />
                    )}
                    <span className="font-semibold">{s.idx}.</span>
                    <span>{s.label}</span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <ChevronRight className="w-3 h-3 text-wo-text-dim" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto p-5 space-y-4">
          {step === 1 && (
            <Step1
              clientName={clientName}
              setClientName={setClientName}
              templates={templates}
              templateId={templateId}
              setTemplateId={setTemplateId}
              loading={loadingTemplates}
              error={templatesError}
            />
          )}
          {step === 2 && (
            <Step2
              quantity={quantity}
              setQuantity={setQuantity}
              widthMm={widthMm}
              setWidthMm={setWidthMm}
              heightMm={heightMm}
              setHeightMm={setHeightMm}
              depthMm={depthMm}
              setDepthMm={setDepthMm}
            />
          )}
          {step === 3 && (
            <Step3
              fields={quoteFields}
              values={quoteInput}
              setValues={setQuoteInput}
              templateCode={selectedTemplate?.template_code}
              isVolumetricPreliminary={isVolumetricPreliminary}
              intakePrefillSummary={intakePrefillSummary}
              templates={templates}
              quantity={quantity}
              widthMm={widthMm}
              heightMm={heightMm}
              depthMm={depthMm}
              marginPct={marginPct}
              vatPct={vatPct}
              discountPct={discountPct}
            />
          )}
          {step === 4 && (
            <Step4
              marginPct={marginPct}
              setMarginPct={setMarginPct}
              vatPct={vatPct}
              discountPct={discountPct}
              setDiscountPct={setDiscountPct}
              result={result}
              simulationResult={simulationResult}
              submitting={submitting}
              submitError={submitError}
              blockedReasons={blockedReasons}
              commercialError={commercialError}
              isVolumetricPreliminary={isVolumetricPreliminary}
            />
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-border flex items-center justify-between bg-background">
          <button
            onClick={goBack}
            disabled={step === 1 || submitting}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded border border-wo-border-strong text-muted-foreground hover:border-slate-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Înapoi
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              disabled={submitting}
              className="px-3 py-1.5 text-[12px] rounded border border-wo-border-strong text-muted-foreground hover:text-foreground disabled:opacity-40"
            >
              Anulează
            </button>
            {step < 4 && (
              <button
                onClick={goNext}
                disabled={
                  (step === 1 && !step1Valid) ||
                  (step === 2 && !step2Valid) ||
                  (step === 3 && !step3Valid)
                }
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Continuă
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
            {step === 4 && !result && !simulationResult && isVolumetricPreliminary && (
              <button
                onClick={handleSubmit}
                disabled={!step4Valid || submitting}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Se calculează...
                  </>
                ) : (
                  <>
                    <DollarSign className="w-3.5 h-3.5" />
                    Simulare preliminară (intern)
                  </>
                )}
              </button>
            )}
            {step === 4 && !result && !simulationResult && !isVolumetricPreliminary && (
              <button
                type="button"
                disabled
                title={LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded bg-slate-700 text-muted-foreground cursor-not-allowed opacity-60"
              >
                <DollarSign className="w-3.5 h-3.5" />
                Flux comercial retras
              </button>
            )}
            {step === 4 &&
              isVolumetricPreliminary &&
              simulationResult &&
              !result && (
                <button
                  onClick={handleCommercialQuote}
                  disabled
                  title={LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded bg-slate-700 text-muted-foreground cursor-not-allowed opacity-60"
                >
                  <FileText className="w-3.5 h-3.5" />
                  Ofertă comercială retrasă — Intake V6
                </button>
              )}
            {step === 4 && (result || simulationResult) && (
              <button
                onClick={onClose}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] rounded bg-emerald-600 text-white hover:bg-emerald-500"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Închide
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Step 1 — Client + template
// ============================================================
function Step1(props: {
  clientName: string;
  setClientName: (v: string) => void;
  templates: ProductTemplateEntity[];
  templateId: number | null;
  setTemplateId: (id: number) => void;
  loading: boolean;
  error: string | null;
}) {
  const {
    clientName,
    setClientName,
    templates,
    templateId,
    setTemplateId,
    loading,
    error,
  } = props;
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
          Nume client *
        </label>
        <input
          type="text"
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
          placeholder="Ex: SC Exemplu SRL"
          className="w-full bg-card border border-wo-border-strong rounded px-3 py-2 text-[13px] text-foreground placeholder:text-wo-text-dim outline-none focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
          Șablon produs *
        </label>
        {loading && (
          <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Se încarcă șabloanele...
          </div>
        )}
        {error && (
          <div className="text-[12px] text-red-400 bg-red-900/20 border border-red-800/40 rounded px-2 py-1.5">
            {error}
          </div>
        )}
        {!loading && !error && templates.length === 0 && (
          <div className="text-[12px] text-muted-foreground">
            Nu există șabloane active. Adăugați unul din Product System.
          </div>
        )}
        {!loading && !error && templates.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {templates.map((t) => {
              const selected = t.id === templateId;
              return (
                <button
                  key={t.id}
                  onClick={() => setTemplateId(t.id)}
                  className={`text-left p-3 rounded border transition-all ${
                    selected
                      ? "border-blue-500/60 bg-blue-900/20"
                      : "border-wo-border-strong bg-card hover:border-slate-500"
                  }`}
                >
                  <div className="text-[12px] font-mono text-blue-400">
                    {t.template_code}
                  </div>
                  <div className="text-[13px] font-semibold text-foreground mt-0.5">
                    {t.family_name}
                  </div>
                  {t.family_id && (
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                      {t.family_id}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// Step 2 — Quantity + dimensions
// ============================================================
function Step2(props: {
  quantity: number;
  setQuantity: (n: number) => void;
  widthMm: number;
  setWidthMm: (n: number) => void;
  heightMm: number;
  setHeightMm: (n: number) => void;
  depthMm: number;
  setDepthMm: (n: number) => void;
}) {
  const {
    quantity,
    setQuantity,
    widthMm,
    setWidthMm,
    heightMm,
    setHeightMm,
    depthMm,
    setDepthMm,
  } = props;
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
          Cantitate (bucăți) *
        </label>
        <input
          type="number"
          min={1}
          value={quantity}
          onChange={(e) => setQuantity(Math.max(1, Number(e.target.value) || 1))}
          className="w-full bg-card border border-wo-border-strong rounded px-3 py-2 text-[13px] text-foreground outline-none focus:border-blue-500"
        />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <NumberField
          label="Lățime"
          unit="mm"
          value={widthMm}
          onChange={setWidthMm}
          min={1}
        />
        <NumberField
          label="Înălțime"
          unit="mm"
          value={heightMm}
          onChange={setHeightMm}
          min={1}
        />
        <NumberField
          label="Adâncime"
          unit="mm"
          value={depthMm}
          onChange={setDepthMm}
          min={0}
        />
      </div>
      <div className="text-[11px] text-muted-foreground bg-background border border-border rounded px-3 py-2">
        Dimensiunile definesc geometria casetei. Parametrii formulei (aria feței,
        lungimi trasee etc.) se completează la pasul următor.
      </div>
    </div>
  );
}

function NumberField(props: {
  label: string;
  unit: string;
  value: number;
  onChange: (n: number) => void;
  min?: number;
  step?: number;
}) {
  const { label, unit, value, onChange, min = 0, step } = props;
  return (
    <div>
      <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
        {label} ({unit})
      </label>
      <input
        type="number"
        min={min}
        step={step}
        value={Number.isFinite(value) ? value : ""}
        onChange={(e) => {
          const n = Number(e.target.value);
          onChange(Number.isFinite(n) ? n : 0);
        }}
        className="w-full bg-card border border-wo-border-strong rounded px-3 py-2 text-[13px] text-foreground outline-none focus:border-blue-500"
      />
    </div>
  );
}

function VolumetricPreliminaryBanner() {
  return (
    <div className="space-y-1 text-[11px] bg-amber-900/15 border border-amber-800/40 rounded px-3 py-2 text-amber-200/90">
      <p className="font-semibold text-amber-300">Calcul preliminar</p>
      <p>Estimări / necesită verificare owner — unele prețuri registry sunt marcate needs_review.</p>
      <p>
        Datele geometrice trebuie verificate/completate manual — nu se generează metrici
        din SVG.
      </p>
      <p>
        Simularea preliminară este permisă când modulul de cost intern poate calcula. Oferta comercială
        finală necesită gate separat (vector, geometrie, metadate, dossier).
      </p>
      <p>Nu se creează comandă automat. Butonul „Creează ofertă comercială” rămâne dezactivat până la readiness complet.</p>
    </div>
  );
}

function IntakeSourceBanner({
  intakeRequestId,
  prefillSummary,
}: {
  intakeRequestId?: string;
  prefillSummary: ReturnType<typeof describeVolumetricIntakePrefill> | null;
}) {
  return (
    <div className="mx-5 mt-3 text-[11px] bg-purple-900/15 border border-purple-800/40 rounded px-3 py-2 text-purple-200/90">
      <p className="font-semibold text-purple-300">Date preluate din Work Intake</p>
      {intakeRequestId && (
        <p className="font-mono text-[10px] text-purple-300/80 mt-0.5">
          Cerere: {intakeRequestId}
        </p>
      )}
      {prefillSummary && prefillSummary.prefilledFields.length > 0 && (
        <p className="mt-1">
          Prefill:{" "}
          {prefillSummary.prefilledFields
            .map((f) => `${f.label} = ${f.value}`)
            .join("; ")}
        </p>
      )}
      {prefillSummary && prefillSummary.warnings.length > 0 && (
        <ul className="mt-1 list-disc pl-4 text-amber-200/90">
          {prefillSummary.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ============================================================
// Step 3 — quote_input
// ============================================================
function Step3(props: {
  fields: QuoteInputFieldSpec[];
  values: Record<string, string>;
  setValues: (v: Record<string, string>) => void;
  templateCode?: string;
  isVolumetricPreliminary?: boolean;
  intakePrefillSummary?: ReturnType<typeof describeVolumetricIntakePrefill> | null;
  templates: ProductTemplateEntity[];
  quantity: number;
  widthMm: number;
  heightMm: number;
  depthMm: number;
  marginPct: number;
  vatPct: number;
  discountPct: number;
}) {
  const {
    fields,
    values,
    setValues,
    templateCode,
    isVolumetricPreliminary,
    intakePrefillSummary,
    templates,
    quantity,
    widthMm,
    heightMm,
    depthMm,
    marginPct,
    vatPct,
    discountPct,
  } = props;
  function set(key: string, v: string) {
    const next = { ...values, [key]: v };
    setValues(
      isVolumetricPreliminary
        ? enrichVolumetricQuoteInputStrings(next)
        : next
    );
  }
  if (fields.length === 0) {
    return (
      <div className="text-[12px] text-muted-foreground bg-background border border-border rounded px-3 py-4">
        Șablonul <span className="font-mono text-blue-400">{templateCode}</span>{" "}
        nu necesită parametri de formulă. Puteți trece la pasul următor.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {isVolumetricPreliminary && <VolumetricPreliminaryBanner />}
      {isVolumetricPreliminary && (
        <SvgLayerAnalysisPanel
          templates={templates}
          quantity={quantity}
          widthMm={widthMm}
          heightMm={heightMm}
          depthMm={depthMm}
          marginPct={marginPct}
          vatPct={vatPct}
          discountPct={discountPct}
          quoteInputValues={values}
          onApplyVolumetricSuggestions={(next) =>
            setValues(enrichVolumetricQuoteInputStrings(next))
          }
        />
      )}
      {isVolumetricPreliminary && intakePrefillSummary && (
        <div className="text-[11px] bg-background border border-border rounded px-3 py-2 text-muted-foreground">
          <p className="font-semibold text-muted-foreground mb-1">
            Parametri de completat manual (geometrie / cost)
          </p>
          <ul className="list-disc pl-4 space-y-0.5">
            {intakePrefillSummary.manualGeometryFields.map((f) => (
              <li key={f.key}>
                {f.label}{" "}
                <span className="font-mono text-amber-300/80">({f.key})</span>
              </li>
            ))}
            {intakePrefillSummary.manualOtherFields.map((f) => (
              <li key={f.key}>
                {f.label}{" "}
                <span className="font-mono text-muted-foreground">({f.key})</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-muted-foreground">
            Module LED rămân calculate automat din perimetru (readonly).
          </p>
        </div>
      )}
      <div className="text-[11px] text-muted-foreground bg-background border border-border rounded px-3 py-2">
        Acești parametri sunt folosiți de modulul de cost intern pentru calculele
        bazate pe formule (arii, perimetru, LED, profil, PSU). Toate câmpurile
        marcate cu <span className="text-amber-400">*</span> sunt obligatorii.
        {!isVolumetricPreliminary && (
          <>
            {" "}
            Nu se inventează metrici din SVG — completați valorile măsurate /
            estimate explicit.
          </>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {fields.map((f) => (
          <div key={f.key}>
            <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
              {f.label}{" "}
              {!f.computed && !f.optional && (
                <span className="text-amber-400">*</span>
              )}{" "}
              {f.unit ? (
                <span className="text-wo-text-dim">({f.unit})</span>
              ) : null}
            </label>
            {f.boolean ? (
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={values[f.key] === "true"}
                  onChange={(e) => set(f.key, e.target.checked ? "true" : "false")}
                  className="rounded border-slate-600"
                />
                <span className="text-[12px] text-muted-foreground">Activ</span>
              </label>
            ) : f.enumOptions ? (
              <select
                value={values[f.key] ?? f.defaultEnum ?? ""}
                onChange={(e) => set(f.key, e.target.value)}
                className="w-full bg-card border border-wo-border-strong rounded px-3 py-2 text-[13px] text-foreground outline-none focus:border-blue-500"
              >
                {f.enumOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            ) : f.selectOptions ? (
              <select
                value={values[f.key] ?? ""}
                onChange={(e) => set(f.key, e.target.value)}
                className="w-full bg-card border border-wo-border-strong rounded px-3 py-2 text-[13px] text-foreground outline-none focus:border-blue-500"
              >
                <option value="">Selectați…</option>
                {f.selectOptions.map((w) => (
                  <option key={w} value={String(w)}>
                    {w} W
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="number"
                min={f.min}
                step="any"
                readOnly={Boolean(f.computed)}
                value={values[f.key] ?? ""}
                onChange={(e) => set(f.key, e.target.value)}
                placeholder={f.placeholder}
                className={`w-full bg-card border border-wo-border-strong rounded px-3 py-2 text-[13px] text-foreground placeholder:text-wo-text-dim outline-none focus:border-blue-500 ${
                  f.computed ? "opacity-80 cursor-not-allowed" : ""
                }`}
              />
            )}
            <p className="text-[10px] text-muted-foreground mt-1">{f.helper}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// Step 4 — Pricing + preview
// ============================================================
function Step4(props: {
  marginPct: number;
  setMarginPct: (n: number) => void;
  vatPct: number;
  discountPct: number;
  setDiscountPct: (n: number) => void;
  result: QuotePriceResponse | null;
  simulationResult: CostSimulationResponse | null;
  submitting: boolean;
  submitError: string | null;
  blockedReasons: string[];
  commercialError?: string | null;
  isVolumetricPreliminary?: boolean;
}) {
  const {
    marginPct,
    setMarginPct,
    vatPct,
    discountPct,
    setDiscountPct,
    result,
    simulationResult,
    submitting,
    submitError,
    blockedReasons,
    commercialError,
    isVolumetricPreliminary,
  } = props;
  return (
    <div className="space-y-4">
      {isVolumetricPreliminary && <VolumetricPreliminaryBanner />}
      <div className="grid grid-cols-3 gap-3">
        <NumberField
          label="Margine"
          unit="%"
          value={marginPct}
          onChange={setMarginPct}
          min={0}
          step={0.5}
        />
        <div className="space-y-1">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide">TVA</p>
          <p
            className="text-[13px] text-foreground bg-background border border-border rounded px-3 py-2"
            data-testid="quote-wizard-settings-vat"
          >
            TVA aplicat din Settings: {vatPct}%
          </p>
        </div>
        <NumberField
          label="Discount"
          unit="%"
          value={discountPct}
          onChange={setDiscountPct}
          min={0}
          step={0.5}
        />
      </div>

      {submitting && (
        <div className="flex items-center gap-2 text-[12px] text-muted-foreground bg-background border border-border rounded px-3 py-2">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          Calcul cost intern (legacy)...
        </div>
      )}

      {submitError && (
        <div className="bg-red-900/20 border border-red-800/50 rounded px-3 py-2 space-y-2">
          <div className="flex items-center gap-2 text-[12px] text-red-300">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span className="font-semibold">
              Eroare: {submitError}
            </span>
          </div>
          {blockedReasons.length > 0 && (
            <ul className="list-disc pl-5 space-y-0.5 text-[11px] text-red-300/90">
              {blockedReasons.map((r, i) => (
                <li key={i} className="font-mono">
                  {r}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {commercialError && (
        <div className="bg-red-900/20 border border-red-800/50 rounded px-3 py-2 space-y-2">
          <div className="flex items-center gap-2 text-[12px] text-red-300">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span className="font-semibold">Ofertă comercială blocată: {commercialError}</span>
          </div>
          {blockedReasons.length > 0 && (
            <ul className="list-disc pl-5 space-y-0.5 text-[11px] text-red-300/90">
              {blockedReasons.map((r, i) => (
                <li key={i}>{humanizeQuoteBlocker(r)}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {result && <PricePreview result={result} />}

      {simulationResult && (
        <PreliminarySimulationPreview result={simulationResult} />
      )}

      {!submitting && !result && !simulationResult && !submitError && (
        <div className="text-[11px] text-muted-foreground bg-background border border-border rounded px-3 py-2">
          Apăsați{" "}
          <span className="text-muted-foreground">
            {isVolumetricPreliminary
              ? "Simulare preliminară"
              : "Calculează & salvează"}
          </span>{" "}
          {isVolumetricPreliminary
            ? "pentru simulare read-only (fără ofertă persistată). Breakdown-ul vine de la modulul de cost intern (legacy)."
            : "pentru a trimite oferta la backend. Breakdown-ul și prețul final sunt returnate de modulul de cost intern (nu se calculează în frontend)."}
        </div>
      )}
    </div>
  );
}

function PreliminarySimulationPreview({
  result,
}: {
  result: CostSimulationResponse;
}) {
  const breakdown = parsePreliminaryCostBreakdown(result);
  const readiness = result.readiness as {
    ready_for_quote?: boolean;
    simulate_ready?: boolean;
    can_create_commercial_quote?: boolean;
    quote_gate?: VolumetricQuoteGate;
    blockers?: string[];
    warnings?: string[];
  };
  const quoteGate = readiness.quote_gate;
  const headerTone = breakdown.isBlocked
    ? "bg-amber-900/20 border-amber-800/50 text-amber-200"
    : "bg-blue-900/20 border-blue-800/50 text-blue-200";
  const HeaderIcon = breakdown.isBlocked ? AlertTriangle : CheckCircle2;

  return (
    <div className="space-y-3">
      <div
        className={`flex items-center justify-between border rounded px-3 py-2 ${headerTone}`}
      >
        <div className="flex items-center gap-2 text-[12px]">
          <HeaderIcon className="w-4 h-4" />
          <span className="font-semibold">
            Simulare preliminară — {result.template_code} ({result.status})
          </span>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground">
          persisted={String(result.persisted)}
        </span>
      </div>

      {breakdown.isPartial && (
        <div className="bg-amber-900/20 border border-amber-800/50 rounded px-3 py-2 text-[11px] text-amber-200">
          <span className="font-semibold">Total parțial calculabil.</span>{" "}
          Sumele includ doar materialele și operațiile cu rată workcenter în
          registry. Operațiile blocate (
          {breakdown.excludedOperationLines.length > 0
            ? breakdown.excludedOperationLines.length
            : breakdown.blockedWorkcenterCount}
          ) nu sunt incluse în total — vezi blockers mai jos.
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <KPI label="Materiale" value={formatRON(breakdown.materials)} />
        <KPI
          label="Operații incluse"
          value={formatRON(breakdown.includedOperations)}
        />
        <KPI
          label="Operații neincluse"
          value={String(
            breakdown.excludedOperationLines.length > 0
              ? breakdown.excludedOperationLines.length
              : breakdown.blockedWorkcenterCount
          )}
        />
        <KPI
          label={breakdown.isPartial ? "Total parțial" : "Cost total"}
          value={`${formatRON(breakdown.partialTotal)} ${breakdown.currency}`}
          highlight
        />
      </div>

      <div className="text-[10px] text-muted-foreground bg-background border border-border rounded px-3 py-2">
        Modulul de cost intern raportează toate operațiile cu rată în{" "}
        <span className="font-mono text-muted-foreground">labour_cost</span> (
        <span className="font-mono text-muted-foreground">total_operation_cost</span>
        ). Câmpul <span className="font-mono text-muted-foreground">machine_cost</span>{" "}
        rămâne 0 — operațiile pe workcenters (CNC, vopsire etc.) apar aici când
        au rată; altfel sunt listate ca blockers, fără valoare.
      </div>

      {(breakdown.includedOperationLines.length > 0 ||
        breakdown.excludedOperationLines.length > 0) && (
        <div className="bg-card border border-border rounded">
          <div className="px-3 py-2 border-b border-border text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
            Detaliu operații (din component_breakdown)
          </div>
          <div className="max-h-48 overflow-auto">
            <table className="w-full text-[11px]">
              <thead className="bg-background text-[10px] uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="text-left px-3 py-1.5">Cod</th>
                  <th className="text-left px-3 py-1.5">Workcenter</th>
                  <th className="text-left px-3 py-1.5">Bază</th>
                  <th className="text-right px-3 py-1.5">Total</th>
                  <th className="text-right px-3 py-1.5">Status</th>
                </tr>
              </thead>
              <tbody>
                {breakdown.includedOperationLines.map((line, i) => (
                  <tr
                    key={`in-${i}`}
                    className="border-t border-border text-foreground"
                  >
                    <td className="px-3 py-1.5 font-mono">{line.code || "—"}</td>
                    <td className="px-3 py-1.5 font-mono">{line.workcenter}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">
                      {line.rateBasis ?? "—"}
                    </td>
                    <td className="px-3 py-1.5 text-right font-semibold">
                      {formatRON(line.lineTotal)}
                    </td>
                    <td className="px-3 py-1.5 text-right text-emerald-400">
                      inclus
                    </td>
                  </tr>
                ))}
                {breakdown.excludedOperationLines.map((line, i) => (
                  <tr
                    key={`ex-${i}`}
                    className="border-t border-border text-muted-foreground"
                  >
                    <td className="px-3 py-1.5 font-mono">{line.code || "—"}</td>
                    <td className="px-3 py-1.5 font-mono">{line.workcenter}</td>
                    <td className="px-3 py-1.5">{line.rateBasis ?? "—"}</td>
                    <td className="px-3 py-1.5 text-right">—</td>
                    <td className="px-3 py-1.5 text-right text-red-400">
                      rată lipsă
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <VolumetricCommercialReadinessPanel
        gate={quoteGate}
        testId="wizard-volumetric-readiness"
      />

      {(result.blocked_reasons?.length ?? 0) > 0 && (
        <div className="bg-red-900/20 border border-red-800/50 rounded px-3 py-2 text-[11px] text-red-300">
          <div className="font-semibold mb-1">Blockers cost intern / readiness:</div>
          <ul className="list-disc pl-5 font-mono">
            {result.blocked_reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {(result.warnings?.length ?? 0) > 0 && (
        <div className="bg-wo-surface-shell/40 border border-border rounded px-3 py-2 text-[11px] text-muted-foreground">
          <div className="font-semibold mb-1">Avertismente:</div>
          <ul className="list-disc pl-5 font-mono">
            {result.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PricePreview({ result }: { result: QuotePriceResponse }) {
  const snap = result.snapshot;
  const cost = snap.cost_result;
  const price = snap.price;
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between bg-emerald-900/20 border border-emerald-800/50 rounded px-3 py-2">
        <div className="flex items-center gap-2 text-[12px] text-emerald-300">
          <CheckCircle2 className="w-4 h-4" />
          <span className="font-semibold">
            Ofertă creată — ID {result.quote_id} ({snap.status})
          </span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2">
        <KPI label="Materiale" value={formatRON(cost.materials_cost)} />
        <KPI label="Manoperă" value={formatRON(cost.labour_cost)} />
        <KPI label="Cost total" value={formatRON(cost.total_cost)} highlight />
        <KPI
          label="Timp estimat"
          value={`${cost.estimated_time_minutes.toFixed(1)} min`}
        />
      </div>

      <div className="grid grid-cols-3 gap-2">
        <KPI label="Net" value={`${formatRON(price.net)} ${cost.currency}`} />
        <KPI label="Brut (cu TVA)" value={`${formatRON(price.gross)} ${cost.currency}`} />
        <KPI
          label="Final"
          value={`${formatRON(price.final)} ${cost.currency}`}
          highlight
        />
      </div>

      <div className="bg-card border border-border rounded">
        <div className="px-3 py-2 border-b border-border text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
          Breakdown ({cost.breakdown.length} linii)
        </div>
        <div className="max-h-64 overflow-auto">
          <table className="w-full text-[12px]">
            <thead className="bg-background text-[10px] uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="text-left px-3 py-1.5">Tip</th>
                <th className="text-left px-3 py-1.5">Nume</th>
                <th className="text-right px-3 py-1.5">Cant.</th>
                <th className="text-right px-3 py-1.5">Unit.</th>
                <th className="text-right px-3 py-1.5">Total</th>
              </tr>
            </thead>
            <tbody>
              {cost.breakdown.map((line, i) => (
                <tr
                  key={i}
                  className="border-t border-border hover:bg-background"
                >
                  <td className="px-3 py-1.5">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                        line.type === "material"
                          ? "bg-blue-900/40 text-blue-300"
                          : line.type === "labour"
                          ? "bg-amber-900/40 text-amber-300"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {line.type}
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-foreground">{line.name}</td>
                  <td className="px-3 py-1.5 text-right text-muted-foreground">
                    {line.quantity.toFixed(2)} {line.unit}
                  </td>
                  <td className="px-3 py-1.5 text-right text-muted-foreground">
                    {formatRON(line.unit_cost)}
                  </td>
                  <td className="px-3 py-1.5 text-right text-foreground font-semibold">
                    {formatRON(line.total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {snap.blocked_reasons.length > 0 && (
        <div className="bg-amber-900/20 border border-amber-800/50 rounded px-3 py-2 text-[11px] text-amber-300">
          <div className="font-semibold mb-1">Avertismente:</div>
          <ul className="list-disc pl-5">
            {snap.blocked_reasons.map((r, i) => (
              <li key={i} className="font-mono">
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function KPI({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`border rounded px-3 py-2 ${
        highlight
          ? "bg-blue-900/20 border-blue-600/40"
          : "bg-card border-border"
      }`}
    >
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div
        className={`text-[14px] font-bold mt-0.5 ${
          highlight ? "text-blue-300" : "text-foreground"
        }`}
      >
        {value}
      </div>
    </div>
  );
}