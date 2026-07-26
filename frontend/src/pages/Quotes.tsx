import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  isTerminalClosedQuoteStatus,
  quoteDetailPath,
  resolveCreatedQuoteRouteId,
  terminalClosedQuoteMessage,
} from "@/lib/commercialSpineNavigation";
import {
  DEFAULT_QUOTE_CURRENCY,
  formatQuoteMoney,
  quoteCurrencyLabel,
} from "@/lib/quoteCurrency";
import { type Quote, type QuoteStatus, deliveryTypeLabels, type DeliveryType } from "@/lib/mockData";
import { getQuoteIntakeCommercialGuard } from "@/lib/quoteIntakeCommercialGuard";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import QuoteRevisionDialog from "@/components/workos/QuoteRevisionDialog";
import QuoteCommercialActionPanel from "@/components/workos/QuoteCommercialActionPanel";
import QuoteAcceptanceConversionPanel from "@/components/workos/QuoteAcceptanceConversionPanel";
import { isQuoteRevisionEligible } from "@/lib/quoteRevision";
import {
  parseOrderConversionError,
  QUOTE_CONVERT_BUTTON_LABEL,
  QUOTE_INTERNAL_ACCEPTANCE_BUTTON_LABEL,
} from "@/lib/quoteAcceptanceConversion";
import { useCompanyCommercialSettings } from "@/hooks/useCompanyCommercialSettings";
import { useBackendData } from "@/hooks/useBackendData";
import { useAuth } from "@/contexts/AuthContext";
import { SectionHeader } from "@/components/workos/SharedComponents";
import { SourceBadge, StatusBadge } from "@/components/workos/design-system";
import ComponentBreakdownTable from "@/components/workos/ComponentBreakdownTable";
import QuoteWizard from "@/components/workos/QuoteWizard";
import {
  shouldOpenWizardFromNav,
  shouldShowVolumetricQuoteWorkspace,
} from "@/lib/volumetricQuoteFlowState";
import { buildIntakeV6Path } from "@/lib/volumetricIntakeRoute";
import QuoteSendDialog from "@/components/workos/QuoteSendDialog";
import ReadinessWarningAcknowledgementModal from "@/components/workos/ReadinessWarningAcknowledgementModal";
import { VolumetricCommercialReadinessPanel } from "@/components/workos/VolumetricCommercialReadinessPanel";
import { VolumetricQuoteReadinessChip } from "@/components/workos/VolumetricQuoteReadinessChip";
import { updateQuoteStatus, createOrderFromQuote } from "@/lib/dataStore";
import type { QuoteCreatedPayload } from "@/api/quotes";
import {
  isVolumetricCommercialQuoteReadiness,
  summarizeVolumetricQuoteGate,
} from "@/lib/volumetricQuoteReady";
import FlowBreadcrumb, { quotesBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import NextStepPanel from "@/components/workos/NextStepPanel";
import QuoteCommercialDocument from "@/components/workos/QuoteCommercialDocument";
import QuotePdfPanel from "@/components/workos/QuotePdfPanel";
import QuoteOutputCompositionPreview from "@/components/workos/QuoteOutputCompositionPreview";
import QuoteOutputSnapshotsSection from "@/components/workos/QuoteOutputSnapshotsSection";
import QuoteDocumentGovernancePanel from "@/components/workos/QuoteDocumentGovernancePanel";
import FlatMaterialNestingSummary from "@/components/workos/FlatMaterialNestingSummary";
import IntakeV6QuoteCommercialSpinePanel from "@/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel";
import IntakeV6QuoteDetailExtras from "@/components/workos/intake-v6/IntakeV6QuoteDetailExtras";
import {
  formatV6QuoteTotalLabel,
  isIntakeV6Quote,
  isUnpricedIntakeV6Quote,
} from "@/lib/intakeV6/intakeV6QuoteDisplay";
import {
  readIntakeV6QuoteHumanSummary,
  shouldHideRawIntakeV6QuoteNotes,
} from "@/lib/intakeV6/intakeV6QuoteNotes";
import {
  FileText,
  DollarSign,
  Send,
  MessageSquare,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  Percent,
  ArrowRight,
  Package,
  Layers,
  Plus,
  AlertTriangle,
} from "lucide-react";

const statusConfig: Record<QuoteStatus, { label: string }> = {
  draft: { label: "Draft" },
  priced: { label: "Priced" },
  sent: { label: "Trimis" },
  viewed: { label: "Vizualizat" },
  negotiating: { label: "Negociere" },
  accepted: { label: "Acceptat" },
  rejected: { label: "Respins" },
  expired: { label: "Expirat" },
};

function QuoteStatusBadge({
  status,
  testId,
}: {
  status: QuoteStatus;
  testId?: string;
}) {
  const cfg = statusConfig[status] ?? { label: status || "Necunoscut" };
  const badge = (
    <StatusBadge
      domain="quote"
      status={status}
      label={cfg.label}
      className="text-[11px]"
    />
  );
  if (testId) {
    return <span data-testid={testId}>{badge}</span>;
  }
  return badge;
}

function formatAmount(val: number) {
  return val.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function deriveIntakeV6WorkspaceId(quote: Quote | null): string | null {
  if (!quote) return null;

  const intakeCode = quote.intakeId?.trim() ?? "";
  if (intakeCode.startsWith("IV6-")) {
    const workspaceId = intakeCode.slice(4).trim();
    return workspaceId || null;
  }

  const quoteCode = quote.id?.trim() ?? "";
  const match = /^Q-V6-IV6-([0-9a-fA-F-]{36})/i.exec(quoteCode);
  return match?.[1] ?? null;
}

function deriveIntakeV6IntakeCode(quote: Quote | null, workspaceId: string | null): string | null {
  const intakeCode = quote?.intakeId?.trim() ?? "";
  if (intakeCode) return intakeCode;
  if (!workspaceId) return null;
  return `IV6-${workspaceId}`;
}

type IntakeV6TechnicalWarning = {
  code: string;
  severity?: string;
  message: string;
  source?: string;
};

type IntakeV6TechnicalMaterialRow = {
  material_key: string;
  display_name: string;
  quantity: number;
  unit: string;
  estimated_cost?: number | null;
  currency?: string;
  warnings?: string[];
};

type IntakeV6TechnicalOperationRow = {
  key: string;
  display_name: string;
  quantity: number;
  unit: string;
  estimated_cost?: number | null;
  pricing_status?: string;
  warnings?: string[];
};

type IntakeV6TechnicalBreakdown = {
  material_rows: IntakeV6TechnicalMaterialRow[];
  consumable_rows: IntakeV6TechnicalMaterialRow[];
  operation_rows: IntakeV6TechnicalOperationRow[];
  edge_cant_operation_rows: IntakeV6TechnicalOperationRow[];
  totals?: {
    estimated_cost_total?: number;
    material_cost_total?: number;
    currency?: string;
    contains_estimates?: boolean;
    contains_missing_prices?: boolean;
  };
  warnings?: IntakeV6TechnicalWarning[];
};

function GuardedQuoteSourceBadges({ quote }: { quote: Quote }) {
  const guard = getQuoteIntakeCommercialGuard(quote);
  if (!guard.isGuardedQuote) return null;
  return (
    <span className="flex items-center gap-1 flex-wrap" data-testid={`quote-iv3-badges-${quote.id}`}>
      <span className="rounded border border-violet-700/50 bg-violet-950/40 px-1.5 py-0.5 text-[10px] text-violet-200">
        Intake V3
      </span>
      {quote.status === "draft" ? (
        <span className="rounded border border-slate-600 bg-slate-900 px-1.5 py-0.5 text-[10px] text-wo-text-secondary">
          Draft
        </span>
      ) : null}
      {guard.requiresPricingReview ? (
        <span className="rounded border border-amber-700/50 bg-amber-950/40 px-1.5 py-0.5 text-[10px] text-amber-200">
          Requires pricing review
        </span>
      ) : guard.pricingReviewCompleted ? (
        <span className="rounded border border-emerald-700/50 bg-emerald-950/40 px-1.5 py-0.5 text-[10px] text-emerald-200">
          Pricing reviewed
        </span>
      ) : null}
      {guard.pricedDraft && !guard.requiresPricingReview ? (
        <span className="rounded border border-blue-700/50 bg-blue-950/40 px-1.5 py-0.5 text-[10px] text-blue-200">
          Priced draft
        </span>
      ) : null}
      {guard.guardedAcceptCompleted ? (
        <span className="rounded border border-emerald-700/50 bg-emerald-950/40 px-1.5 py-0.5 text-[10px] text-emerald-200">
          Accepted
        </span>
      ) : guard.guardedAcceptReady ? (
        <span className="rounded border border-blue-700/50 bg-blue-950/40 px-1.5 py-0.5 text-[10px] text-blue-200">
          Accept ready
        </span>
      ) : guard.acceptBlocked ? (
        <span className="rounded border border-rose-700/50 bg-rose-950/40 px-1.5 py-0.5 text-[10px] text-rose-200">
          Accept blocked
        </span>
      ) : null}
      {guard.orderCreated ? (
        <>
          <span className="rounded border border-emerald-700/50 bg-emerald-950/40 px-1.5 py-0.5 text-[10px] text-emerald-200">
            Order created
          </span>
          <span className="rounded border border-blue-700/50 bg-blue-950/40 px-1.5 py-0.5 text-[10px] text-blue-200">
            Production readiness audit
          </span>
          <span className="rounded border border-slate-600 bg-slate-900 px-1.5 py-0.5 text-[10px] text-wo-text-secondary">
            Production not started
          </span>
        </>
      ) : guard.guardedConvertReady ? (
        <span className="rounded border border-blue-700/50 bg-blue-950/40 px-1.5 py-0.5 text-[10px] text-blue-200">
          Convert ready
        </span>
      ) : null}
      {!guard.orderCreated && guard.convertBlocked ? (
        <span className="rounded border border-rose-700/50 bg-rose-950/40 px-1.5 py-0.5 text-[10px] text-rose-200">
          Convert guarded
        </span>
      ) : null}
    </span>
  );
}

function QuoteCard({ quote, isSelected, onClick }: { quote: Quote; isSelected: boolean; onClick: () => void }) {
  const currency = quote.currency ?? DEFAULT_QUOTE_CURRENCY;
  return (
    <div
      onClick={onClick}
      className={`bg-wo-surface-raised border rounded-lg p-4 cursor-pointer transition-all ${
        isSelected ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-wo-border-subtle hover:border-slate-500"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[12px] font-mono text-blue-400">{quote.id}</span>
          <QuoteStatusBadge status={quote.status} />
          <GuardedQuoteSourceBadges quote={quote} />
          <VolumetricQuoteReadinessChip
            snapshot={quote.volumetricReadiness}
            testId={`quote-readiness-chip-${quote.id}`}
          />
          <span className="text-[10px] text-wo-text-muted">v{quote.version}</span>
        </div>
        <span
          className={`text-[16px] font-bold ${isUnpricedIntakeV6Quote(quote) ? "text-amber-300" : "text-wo-text-primary"}`}
          data-testid={isUnpricedIntakeV6Quote(quote) ? `quote-v6-unpriced-total-${quote.id}` : undefined}
        >
          {formatV6QuoteTotalLabel(quote, formatQuoteMoney(quote.grandTotal, currency))}
        </span>
      </div>
      <p className="text-[13px] font-semibold text-wo-text-primary">{quote.client}</p>
      {quote.intakeId ? (
        <p className="text-[10px] text-blue-400/80 font-mono mt-0.5">
          Cerere sursă: {quote.intakeId}
        </p>
      ) : null}
      <p className="text-[11px] text-wo-text-muted mt-0.5">{quote.contactPerson}</p>
      <div className="flex items-center gap-4 mt-2 text-[10px] text-wo-text-muted">
        <span>{quote.lineItems.length} linii</span>
        <span className="flex items-center gap-0.5">
          <Percent className="w-3 h-3" />{" "}
          {isIntakeV6Quote(quote) ? `Adaos ${quote.marginPct}%` : `Marjă ${quote.marginPct}%`}
        </span>
        {quote.discountPct > 0 && (
          <span className="text-amber-400">-{quote.discountPct}% discount</span>
        )}
        <span className="ml-auto">Valid: {quote.validUntil}</span>
      </div>
    </div>
  );
}

export default function Quotes() {
  const navigate = useNavigate();
  const location = useLocation();
  const { quoteId: quoteIdParam } = useParams<{ quoteId?: string }>();
  const wizardNavState = location.state as
    | {
        productSpec?: IntakeProductSpec;
        templateCode?: string;
        openWizard?: boolean;
        clientName?: string;
        intakeRequestId?: string;
        fromIntake?: boolean;
        confirmedTemplateCode?: string;
        deliveryType?: string;
        siteAudit?: import("@/lib/intakeSiteAudit").IntakeSiteAuditJson | null;
        intakeStatus?: string;
      }
    | null
    | undefined;
  const { quotes, loading, error, source, sourcesDetail, refresh } = useBackendData();
  const quotesSource = sourcesDetail?.quotes ?? source;
  const { eurToRonRate } = useCompanyCommercialSettings(quotesSource === "db");
  const { user } = useAuth();
  const quotesAccessDenied =
    quotesSource === "error" &&
    (user?.role === "employee_mobile" ||
      /403|forbidden|acces interzis|not authorized/i.test(error ?? ""));
  const canMutateQuotes = quotesSource === "db";
  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
  const [quoteNotFound, setQuoteNotFound] = useState(false);
  const [filterStatus, setFilterStatus] = useState<QuoteStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedLineItems, setExpandedLineItems] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(() =>
    shouldOpenWizardFromNav(wizardNavState)
  );
  const [sendDialogQuote, setSendDialogQuote] = useState<Quote | null>(null);
  const [revisionDialogQuote, setRevisionDialogQuote] = useState<Quote | null>(null);
  const [duplicateOrderCode, setDuplicateOrderCode] = useState<string | null>(null);

  useEffect(() => {
    if (shouldOpenWizardFromNav(wizardNavState)) {
      setWizardOpen(true);
    }
  }, [wizardNavState?.openWizard]);

  useEffect(() => {
    setDuplicateOrderCode(null);
  }, [selectedQuote?.id]);

  const selectQuote = useCallback(
    (quote: Quote | null, options?: { syncUrl?: boolean }) => {
      setSelectedQuote(quote);
      setQuoteNotFound(false);
      if (options?.syncUrl !== false) {
        if (quote) {
          navigate(quoteDetailPath(quote.id), {
            replace: true,
            state: location.state,
          });
        } else if (quoteIdParam) {
          navigate("/quotes", { replace: true, state: location.state });
        }
      }
    },
    [navigate, location.state, quoteIdParam]
  );

  useEffect(() => {
    if (!quoteIdParam || loading) return;
    const match = quotes.find(
      (q) => q.id.toLowerCase() === quoteIdParam.toLowerCase()
    );
    if (match) {
      setQuoteNotFound(false);
      setSelectedQuote((prev) => (prev?.id === match.id ? prev : match));
      return;
    }
    if (quotes.length > 0) {
      setQuoteNotFound(true);
      setSelectedQuote(null);
    }
  }, [quoteIdParam, quotes, loading]);
  
  // Warning acknowledgement modal state
  const [pendingWarningQuoteId, setPendingWarningQuoteId] = useState<string | null>(null);
  const [pendingReadinessWarnings, setPendingReadinessWarnings] = useState<unknown[]>([]);
  const [pendingReadinessResult, setPendingReadinessResult] = useState<Record<string, unknown> | undefined>();
  const [isSubmittingAcknowledgedConversion, setIsSubmittingAcknowledgedConversion] = useState(false);
  const [convertAckChecked, setConvertAckChecked] = useState(false);
  const [technicalBreakdown, setTechnicalBreakdown] = useState<IntakeV6TechnicalBreakdown | null>(null);
  const [technicalBreakdownLoading, setTechnicalBreakdownLoading] = useState(false);
  const [technicalBreakdownError, setTechnicalBreakdownError] = useState<string | null>(null);
  const [expandedTechnicalBreakdown, setExpandedTechnicalBreakdown] = useState(false);

  useEffect(() => {
    setConvertAckChecked(false);
  }, [selectedQuote?.id]);

  useEffect(() => {
    setExpandedTechnicalBreakdown(false);
  }, [selectedQuote?.id]);

  const volumetricGate = selectedQuote?.volumetricReadiness?.quoteGate;
  const volumetricReadinessSummary = useMemo(
    () => (volumetricGate ? summarizeVolumetricQuoteGate(volumetricGate) : null),
    [volumetricGate]
  );
  const showVolumetricReadinessPanel = isVolumetricCommercialQuoteReadiness(
    selectedQuote?.volumetricReadiness
  );
  const convertBlockedByGate = volumetricReadinessSummary
    ? !volumetricReadinessSummary.canCreate
    : false;
  const convertNeedsAck =
    volumetricReadinessSummary?.requiresAcknowledgement === true && !convertAckChecked;
  const convertDisabledByReadiness = convertBlockedByGate || convertNeedsAck;
  const intakeV6WorkspaceId = useMemo(
    () => deriveIntakeV6WorkspaceId(selectedQuote),
    [selectedQuote]
  );
  const intakeV6IntakeCode = useMemo(
    () => deriveIntakeV6IntakeCode(selectedQuote, intakeV6WorkspaceId),
    [selectedQuote, intakeV6WorkspaceId]
  );
  const showIntakeV6CommercialSpine = Boolean(
    selectedQuote?.dbId && intakeV6WorkspaceId && intakeV6IntakeCode
  );
  const intakeV6HumanNote = useMemo(
    () => readIntakeV6QuoteHumanSummary(selectedQuote?.notes),
    [selectedQuote?.notes],
  );
  const hideV6RawNotes = shouldHideRawIntakeV6QuoteNotes(selectedQuote?.notes);
  const showV6CompactTotals =
    showIntakeV6CommercialSpine && !isUnpricedIntakeV6Quote(selectedQuote);

  useEffect(() => {
    if (!intakeV6WorkspaceId) {
      setTechnicalBreakdown(null);
      setTechnicalBreakdownError(null);
      setTechnicalBreakdownLoading(false);
      return;
    }

    const controller = new AbortController();
    setTechnicalBreakdownLoading(true);
    setTechnicalBreakdownError(null);

    void fetch(`/api/v1/intake-v6/workspaces/${intakeV6WorkspaceId}/material-breakdown`, {
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return (await response.json()) as IntakeV6TechnicalBreakdown;
      })
      .then((payload) => {
        if (!controller.signal.aborted) {
          setTechnicalBreakdown(payload);
        }
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message = error instanceof Error ? error.message : "Nu am putut încărca breakdown-ul tehnic V6.";
        setTechnicalBreakdown(null);
        setTechnicalBreakdownError(message);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setTechnicalBreakdownLoading(false);
        }
      });

    return () => controller.abort();
  }, [intakeV6WorkspaceId, selectedQuote?.id]);

  const handleQuoteAction = async (
    action: "send" | "accept" | "reject" | "expire" | "convert"
  ) => {
    if (!canMutateQuotes) {
      alert("Acțiunile pe oferte sunt disponibile doar pe sursă backend live.");
      return;
    }
    if (!selectedQuote) return;
    setActionLoading(true);
    try {
      if (action === "send") {
        await updateQuoteStatus(selectedQuote.id, "sent");
      } else if (action === "accept") {
        await updateQuoteStatus(selectedQuote.id, "accepted");
        await refresh();
        setSelectedQuote((prev) => (prev ? { ...prev, status: "accepted" } : null));
        return;
      } else if (action === "reject") {
        await updateQuoteStatus(selectedQuote.id, "rejected");
      } else if (action === "expire") {
        await updateQuoteStatus(selectedQuote.id, "expired");
      } else if (action === "convert") {
        if (convertBlockedByGate) {
          alert(
            "Conversia este blocată de gate-ul comercial volumetric. Rezolvă blockers înainte de conversie."
          );
          return;
        }
        try {
          const convertOptions =
            volumetricReadinessSummary?.requiresAcknowledgement && convertAckChecked
              ? {
                  acknowledge_readiness_warnings: true,
                  readiness_warning_acknowledgement_reason:
                    "Confirmat în UI Quotes — avertismente comerciale verificate",
                }
              : undefined;
          const code = await createOrderFromQuote(selectedQuote.id, convertOptions);
          if (code) {
            await refresh();
            navigate(`/orders/${encodeURIComponent(code)}`);
            return;
          }
        } catch (err: unknown) {
          const errMessage = err instanceof Error ? err.message : String(err);
          try {
            const errDetail = JSON.parse(errMessage) as Record<string, unknown>;
            const detail =
              errDetail.detail && typeof errDetail.detail === "object"
                ? (errDetail.detail as Record<string, unknown>)
                : errDetail;
            const parsed = parseOrderConversionError(errMessage);
            if (parsed.error === "order_already_exists_for_quote" && parsed.existingOrderCode) {
              setDuplicateOrderCode(parsed.existingOrderCode);
              return;
            }
            if (detail.error === "readiness_blocked_prevents_order") {
              alert(
                `Conversia la comandă a fost blocată din cauza statusului de pregătire al produsului.\n\nBlockeri: ${(detail.blockers as string[] | undefined)?.join(", ") || "necunoscut"}\n\nVerificați statusul pregătirii produsului și încercați din nou.`
              );
              return;
            }
            if (detail.error === "readiness_warning_acknowledgement_required") {
              setPendingWarningQuoteId(selectedQuote.id);
              setPendingReadinessWarnings((detail.warnings as string[]) || []);
              setPendingReadinessResult(
                detail.readiness_result as Record<string, unknown> | undefined
              );
              return;
            }
            alert(`Eroare la conversia în comandă: ${String(detail.error || errMessage)}`);
            return;
          } catch {
            alert(`Eroare la conversia în comandă: ${errMessage}`);
            return;
          }
        }
      }
      await refresh();
      selectQuote(null);
    } catch (err) {
      console.error("[Quotes] action failed", err);
      alert("Acțiunea nu a putut fi finalizată. Verifică consola.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleWarningAcknowledgement = async (reason: string) => {
    if (!pendingWarningQuoteId) return;
    
    setIsSubmittingAcknowledgedConversion(true);
    try {
      const code = await createOrderFromQuote(pendingWarningQuoteId, {
        acknowledge_readiness_warnings: true,
        readiness_warning_acknowledgement_reason: reason,
      });
      
      if (code) {
        // Clear modal state
        setPendingWarningQuoteId(null);
        setPendingReadinessWarnings([]);
        setPendingReadinessResult(undefined);
        
        // Refresh and navigate
        await refresh();
        if (code) {
          navigate(`/orders/${encodeURIComponent(code)}`);
        } else {
          navigate("/orders");
        }
        return;
      }
    } catch (err: any) {
      // Parse and check for blocker error
      try {
        const errDetail = JSON.parse(err.message);
        if (errDetail.error === "readiness_blocked_prevents_order") {
          alert(
            `Conversia a fost blocată de blockers:\n\n${(errDetail.blockers || []).join(", ") || "necunoscut"}\n\nBlockers nu pot fi acknowledged. Contactați administratorul.`
          );
          // Close modal
          setPendingWarningQuoteId(null);
          setPendingReadinessWarnings([]);
          setPendingReadinessResult(undefined);
          return;
        }
      } catch {
        // Fall through to generic error
      }
      
      alert(`Eroare la conversia cu acknowledgement: ${err.message}`);
    } finally {
      setIsSubmittingAcknowledgedConversion(false);
    }
  };

  const handleWarningModalCancel = () => {
    // Clear modal state without converting
    setPendingWarningQuoteId(null);
    setPendingReadinessWarnings([]);
    setPendingReadinessResult(undefined);
  };

  const volumetricWorkspaceOpen = shouldShowVolumetricQuoteWorkspace(
    wizardOpen,
    wizardNavState
  );

  const closeWizard = () => {
    setWizardOpen(false);
    const target = selectedQuote
      ? quoteDetailPath(selectedQuote.id)
      : "/quotes";
    navigate(target, { replace: true, state: {} });
  };

  const handleQuoteCreated = useCallback(
    (_created: QuoteCreatedPayload) => {
      void refresh();
    },
    [refresh]
  );

  const handleOpenCreatedQuote = useCallback(
    (created: QuoteCreatedPayload) => {
      const routeId = resolveCreatedQuoteRouteId(created);
      setWizardOpen(false);
      void refresh().finally(() => {
        navigate(quoteDetailPath(routeId), { replace: true, state: {} });
      });
    },
    [navigate, refresh]
  );

  const openAdhocWizard = () => {
    navigate("/quotes", { replace: true, state: {} });
    setWizardOpen(true);
  };

  if (volumetricWorkspaceOpen) {
    return (
      <QuoteWizard
        open
        onClose={closeWizard}
        onCreated={handleQuoteCreated}
        onOpenCreatedQuote={handleOpenCreatedQuote}
        initialProductSpec={wizardNavState?.productSpec ?? null}
        preferredTemplateCode={wizardNavState?.templateCode}
        initialClientName={wizardNavState?.clientName}
        intakeRequestId={wizardNavState?.intakeRequestId}
        openedFromIntake={Boolean(wizardNavState?.fromIntake)}
        deliveryTypeLabel={
          wizardNavState?.deliveryType
            ? deliveryTypeLabels[wizardNavState.deliveryType as DeliveryType] ??
              wizardNavState.deliveryType
            : undefined
        }
        siteAuditJson={wizardNavState?.siteAudit}
        intakeStatus={wizardNavState?.intakeStatus}
      />
    );
  }

  if (quotesAccessDenied) {
    return (
      <div className="space-y-4" data-testid="quotes-access-denied">
        <FlowBreadcrumb items={quotesBreadcrumb()} />
        <div className="flex items-start gap-3 px-4 py-5 bg-amber-900/15 border border-amber-800/40 rounded-lg max-w-2xl">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h2 className="text-[14px] font-bold text-amber-200 mb-1">
              Nu ai acces la pagina Oferte.
            </h2>
            <p className="text-[12px] text-amber-200/80">
              Această secțiune este disponibilă în shell-ul admin/desktop. Dacă ești
              angajat operațional, folosește aplicația Employee Mobile.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (loading && quotes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p className="text-[12px] text-wo-text-muted">Încărcare oferte...</p>
        </div>
      </div>
    );
  }

  const filtered = quotes.filter((q) => {
    if (filterStatus !== "all" && q.status !== filterStatus) return false;
    const needle = searchQuery.trim().toLowerCase();
    if (!needle) return true;
    return (
      q.id.toLowerCase().includes(needle) ||
      q.client.toLowerCase().includes(needle) ||
      (q.intakeId?.toLowerCase().includes(needle) ?? false)
    );
  });

  const totalValue = quotes.reduce((sum, q) => sum + q.grandTotal, 0);
  const acceptedValue = quotes.filter((q) => q.status === "accepted").reduce((sum, q) => sum + q.grandTotal, 0);
  const pendingValue = quotes.filter((q) => ["draft", "priced", "sent", "viewed", "negotiating"].includes(q.status)).reduce((sum, q) => sum + q.grandTotal, 0);
  const kpiCurrency = quoteCurrencyLabel(quotes);
  const selectedCurrency = selectedQuote?.currency ?? DEFAULT_QUOTE_CURRENCY;
  const technicalBreakdownCurrency = technicalBreakdown?.totals?.currency ?? "EUR";
  const technicalBreakdownRowCount =
    (technicalBreakdown?.material_rows.length ?? 0) +
    (technicalBreakdown?.consumable_rows.length ?? 0) +
    (technicalBreakdown?.operation_rows.length ?? 0) +
    (technicalBreakdown?.edge_cant_operation_rows.length ?? 0);

  const statusCounts: { status: QuoteStatus; count: number }[] = [
    { status: "draft", count: quotes.filter((q) => q.status === "draft").length },
    { status: "priced", count: quotes.filter((q) => q.status === "priced").length },
    { status: "sent", count: quotes.filter((q) => q.status === "sent").length },
    { status: "negotiating", count: quotes.filter((q) => q.status === "negotiating").length },
    { status: "accepted", count: quotes.filter((q) => q.status === "accepted").length },
    { status: "rejected", count: quotes.filter((q) => q.status === "rejected").length },
  ];

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <FlowBreadcrumb items={quotesBreadcrumb()} />

      {/* Header */}
      <div className="flex items-center gap-2">
        <FileText className="w-5 h-5 text-amber-400" />
        <h1 className="text-[18px] font-bold text-wo-text-primary">Oferte</h1>
        <SourceBadge source={quotesSource} />
        <span className="text-[10px] text-wo-text-muted bg-slate-800 px-2 py-0.5 rounded-full ml-1">
          {quotes.length} oferte
        </span>
        <div className="ml-auto">
          <button
            onClick={openAdhocWizard}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold rounded bg-blue-600 text-white hover:bg-blue-500"
          >
            <Plus className="w-3.5 h-3.5" />
            Ofertă nouă
          </button>
        </div>
      </div>

      <QuoteWizard
        open={wizardOpen}
        onClose={closeWizard}
        onCreated={handleQuoteCreated}
        onOpenCreatedQuote={handleOpenCreatedQuote}
        initialProductSpec={wizardNavState?.productSpec ?? null}
        preferredTemplateCode={wizardNavState?.templateCode}
        initialClientName={wizardNavState?.clientName}
        intakeRequestId={wizardNavState?.intakeRequestId}
        openedFromIntake={Boolean(wizardNavState?.fromIntake)}
        deliveryTypeLabel={
          wizardNavState?.deliveryType
            ? deliveryTypeLabels[wizardNavState.deliveryType as DeliveryType] ??
              wizardNavState.deliveryType
            : undefined
        }
        siteAuditJson={wizardNavState?.siteAudit}
        intakeStatus={wizardNavState?.intakeStatus}
      />

      {error && source !== "mock" && (
        <div className="flex items-center gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-300">
            Datele ofertelor nu au putut fi încărcate din backend: {error}
          </p>
        </div>
      )}

      {quoteIdParam && quoteNotFound && !loading && (
        <div
          className="flex items-center gap-2 px-3 py-2 bg-amber-900/20 border border-amber-800/40 rounded-lg"
          data-testid="quote-not-found"
        >
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <p className="text-[12px] text-amber-300">
            Oferta <span className="font-mono">{quoteIdParam}</span> nu a fost
            găsită.{" "}
            <button
              type="button"
              onClick={() => navigate("/quotes", { replace: true })}
              className="underline hover:text-amber-200"
            >
              Înapoi la listă
            </button>
          </p>
        </div>
      )}

      {!showIntakeV6CommercialSpine && (
      <div className="flex items-start gap-2 px-3 py-2 bg-blue-900/15 border border-blue-800/30 rounded-lg">
        <AlertTriangle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <p className="text-[11px] text-blue-300/90">
          Quote readiness este decis canonic în backend (ProductSystem/CostEngine/Quotes policy). UI afișează rezultatul backend și nu inventează statusuri de readiness.
        </p>
      </div>
      )}

      {/* Summary KPIs */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-blue-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-wo-text-muted uppercase tracking-wide">Valoare Totală</p>
          <p className="text-[20px] font-bold text-wo-text-primary mt-1">{formatAmount(totalValue)}</p>
          <p className="text-[10px] text-wo-text-muted">{kpiCurrency.label}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-emerald-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-wo-text-muted uppercase tracking-wide">Acceptate</p>
          <p className="text-[20px] font-bold text-emerald-400 mt-1">{formatAmount(acceptedValue)}</p>
          <p className="text-[10px] text-wo-text-muted">{kpiCurrency.label}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-amber-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-wo-text-muted uppercase tracking-wide">În Pipeline</p>
          <p className="text-[20px] font-bold text-amber-400 mt-1">{formatAmount(pendingValue)}</p>
          <p className="text-[10px] text-wo-text-muted">{kpiCurrency.label}</p>
        </div>
      </div>

      {/* Search */}
      <div>
        <label htmlFor="quotes-search-input" className="sr-only">
          Caută oferte
        </label>
        <input
          id="quotes-search-input"
          data-testid="quotes-search-input"
          type="search"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Caută după cod ofertă, client sau cod cerere..."
          className="w-full max-w-md px-3 py-2 text-[12px] rounded-lg border border-wo-border-strong bg-wo-surface-raised text-wo-text-primary placeholder:text-wo-text-muted focus:outline-none focus:border-blue-500/50"
        />
      </div>

      {/* Status Filter */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <button
          onClick={() => setFilterStatus("all")}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all ${
            filterStatus === "all" ? "bg-blue-600/20 text-blue-400 border-blue-600/50" : "bg-transparent text-wo-text-muted border-wo-border-strong hover:border-slate-500"
          }`}
        >
          Toate ({quotes.length})
        </button>
        {statusCounts.filter((s) => s.count > 0).map((s) => (
          <button
            key={s.status}
            onClick={() => setFilterStatus(filterStatus === s.status ? "all" : s.status)}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all ${
              filterStatus === s.status ? "bg-blue-600/20 text-blue-400 border-blue-600/50" : "bg-transparent text-wo-text-muted border-wo-border-strong hover:border-slate-500"
            }`}
          >
            {statusConfig[s.status].label} ({s.count})
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Quote List */}
        <div className="lg:col-span-2 space-y-2">
          {filtered.map((q) => (
            <QuoteCard
              key={q.id}
              quote={q}
              isSelected={selectedQuote?.id === q.id}
              onClick={() => selectQuote(q)}
            />
          ))}
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selectedQuote ? (
            <>
              {/* Quote Header */}
              <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[12px] font-mono text-blue-400">{selectedQuote.id}</span>
                  <QuoteStatusBadge
                    status={selectedQuote.status}
                    testId="quote-readiness-state"
                  />
                </div>
                <h3 className="text-[16px] font-bold text-wo-text-primary">{selectedQuote.client}</h3>
                <p className="text-[12px] text-wo-text-muted mt-0.5">{selectedQuote.contactPerson}</p>
                {intakeV6WorkspaceId ? (
                  <p className="text-[11px] mt-1">
                    <Link
                      to={buildIntakeV6Path(intakeV6WorkspaceId)}
                      className="text-blue-400 hover:text-blue-300 font-mono"
                      data-testid="quote-detail-intake-link"
                    >
                      din cerere {intakeV6IntakeCode ?? selectedQuote.intakeId ?? intakeV6WorkspaceId}
                    </Link>
                  </p>
                ) : null}
                <div className="flex items-center gap-3 mt-2 text-[10px] text-wo-text-muted">
                  <span>Versiune {selectedQuote.version}</span>
                  <span>Creat: {new Date(selectedQuote.createdAt).toLocaleDateString("ro-RO")}</span>
                  <span>Valid: {selectedQuote.validUntil}</span>
                </div>
                {showIntakeV6CommercialSpine && intakeV6HumanNote ? (
                  <p
                    className="mt-3 text-[11px] leading-relaxed text-wo-text-muted border-t border-wo-border-subtle pt-3"
                    data-testid="quote-v6-human-note"
                  >
                    {intakeV6HumanNote}
                  </p>
                ) : null}

                {(selectedQuote.acceptedSnapshotV2Id || selectedQuote.snapshotV2Code) && (
                  <div
                    className="mt-4 bg-wo-surface-inset border border-cyan-800/30 rounded-lg p-3"
                    data-testid="quote-v2-snapshot-summary"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                      <p className="text-[12px] text-cyan-400 font-semibold">Frozen Snapshot V2</p>
                    </div>
                    <div className="space-y-2 text-[11px]">
                      <div className="flex items-center justify-between bg-[#121B2C] px-2 py-1.5 rounded">
                        <span className="text-wo-text-muted">Accepted snapshot</span>
                        <span className="text-wo-text-primary font-mono">
                          {selectedQuote.acceptedSnapshotV2Id != null
                            ? `#${selectedQuote.acceptedSnapshotV2Id}`
                            : "—"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between bg-[#121B2C] px-2 py-1.5 rounded">
                        <span className="text-wo-text-muted">Snapshot code</span>
                        <span className="text-wo-text-primary font-mono">
                          {selectedQuote.snapshotV2Code ?? "—"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between bg-[#121B2C] px-2 py-1.5 rounded">
                        <span className="text-wo-text-muted">Snapshot readiness</span>
                        <span className="text-wo-text-primary">
                          {selectedQuote.snapshotV2Readiness ?? "—"}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-[#121B2C] px-2 py-1.5 rounded">
                          <p className="text-wo-text-muted">Commercial frozen</p>
                          <p className="text-wo-text-primary font-semibold">
                            {selectedQuote.snapshotV2CommercialTotal != null
                              ? formatQuoteMoney(selectedQuote.snapshotV2CommercialTotal, selectedCurrency)
                              : "—"}
                          </p>
                        </div>
                        <div className="bg-[#121B2C] px-2 py-1.5 rounded">
                          <p className="text-wo-text-muted">Internal estimate</p>
                          <p className="text-wo-text-primary font-semibold">
                            {selectedQuote.snapshotV2InternalTotal != null
                              ? formatQuoteMoney(selectedQuote.snapshotV2InternalTotal, selectedCurrency)
                              : "—"}
                          </p>
                        </div>
                      </div>
                      <p className="text-[10px] text-wo-text-muted">
                        Read-only truth. This card reflects the frozen V2 snapshot used for acceptance/conversion, not legacy pricing shortcuts.
                      </p>
                    </div>
                  </div>
                )}

                {!showIntakeV6CommercialSpine && (
                <div
                  className="mt-4 rounded-lg border border-blue-800/30 bg-blue-950/10 px-3 py-3"
                  data-testid="quote-truth-boundary"
                >
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-blue-300 mt-0.5 shrink-0" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-[12px] font-semibold text-blue-200">Ofertă client înghețată</p>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-900/30 text-blue-300 border border-blue-700/30">
                          Ofertă client (Snapshot V2)
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-900/40 text-wo-text-secondary border border-slate-700/40">
                          Cost intern / registries upstream
                        </span>
                      </div>
                      <p className="text-[11px] text-blue-100/90 mt-1 leading-relaxed">
                        În Oferte vezi Oferta client (Snapshot V2) pentru acceptare și conversie. Pricing Registry,
                        Product System și Cost intern estimativ upstream nu pot înlocui acest snapshot după freeze.
                      </p>
                      <div className="flex items-center gap-3 flex-wrap mt-2 text-[11px]">
                        <Link to="/inventory/pricing" className="text-blue-300 hover:text-blue-200 underline underline-offset-2">
                          Pricing Registry (helper intern)
                        </Link>
                        <Link to="/orders" className="text-blue-300 hover:text-blue-200 underline underline-offset-2">
                          Vezi snapshot-to-plan în Comenzi
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
                )}
              </div>

              {showIntakeV6CommercialSpine ? (
                <IntakeV6QuoteCommercialSpinePanel
                  workspaceId={intakeV6WorkspaceId!}
                  quoteId={selectedQuote.dbId ?? null}
                  clientAnalysisHash={null}
                  intakeCode={intakeV6IntakeCode}
                  onSpineUpdated={() => {
                    void refresh();
                  }}
                />
              ) : null}

              {intakeV6WorkspaceId ? (
                <div className="bg-wo-surface-inset border border-cyan-900/40 rounded-lg p-3">
                  <p className="text-[11px] text-cyan-100 leading-relaxed">
                    Lista de mai jos este Oferta client persistată (Snapshot V2). Nu este Cost intern estimativ /
                    breakdown tehnic live din Intake V6 — e normal să fie mai agregată decât calculatorul intern.
                  </p>
                </div>
              ) : null}

              {intakeV6WorkspaceId ? (
                <div className="bg-wo-surface-raised border border-cyan-900/40 rounded-lg p-4">
                  <button
                    onClick={() => setExpandedTechnicalBreakdown((current) => !current)}
                    className="flex items-center justify-between w-full mb-3"
                    aria-expanded={expandedTechnicalBreakdown}
                  >
                    <SectionHeader
                      title="Cost intern estimativ — breakdown tehnic live"
                      count={technicalBreakdownRowCount || undefined}
                      icon={<Package className="w-4 h-4" />}
                    />
                    {expandedTechnicalBreakdown ? <ChevronUp className="w-4 h-4 text-wo-text-muted" /> : <ChevronDown className="w-4 h-4 text-wo-text-muted" />}
                  </button>
                  <p className="text-[10px] text-wo-text-muted mt-2 mb-3">
                    Canal Cost intern estimativ (live Intake V6) — separat de Oferta client înghețată. Nu modifica
                    Pricing Registry aici în fluxul de ofertare.
                  </p>
                  {technicalBreakdownLoading ? (
                    <p className="text-[12px] text-wo-text-muted">Încărcare breakdown tehnic V6...</p>
                  ) : technicalBreakdownError ? (
                    <p className="text-[12px] text-amber-300">{technicalBreakdownError}</p>
                  ) : technicalBreakdown ? (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                          <p className="text-[10px] uppercase tracking-wide text-wo-text-muted">Cost intern estimativ</p>
                          <p className="text-[14px] font-semibold text-wo-text-primary mt-1">
                            {formatQuoteMoney(technicalBreakdown.totals?.estimated_cost_total ?? 0, technicalBreakdownCurrency)}
                          </p>
                        </div>
                        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                          <p className="text-[10px] uppercase tracking-wide text-wo-text-muted">Rânduri tehnice</p>
                          <p className="text-[14px] font-semibold text-wo-text-primary mt-1">{technicalBreakdownRowCount}</p>
                        </div>
                        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                          <p className="text-[10px] uppercase tracking-wide text-wo-text-muted">Avertizări</p>
                          <p className="text-[14px] font-semibold text-wo-text-primary mt-1">{technicalBreakdown.warnings?.length ?? 0}</p>
                        </div>
                      </div>

                      {expandedTechnicalBreakdown ? (
                        <div className="space-y-4">
                          {technicalBreakdown.material_rows.length > 0 ? (
                            <div>
                              <p className="text-[11px] font-semibold text-wo-text-primary mb-2">Materiale</p>
                              <div className="space-y-2">
                                {technicalBreakdown.material_rows.map((row) => (
                                  <div key={row.material_key} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                                    <div className="flex items-start justify-between gap-3">
                                      <div>
                                        <p className="text-[12px] text-wo-text-primary font-medium">{row.display_name}</p>
                                        <p className="text-[10px] text-wo-text-muted mt-1">{row.quantity} {row.unit}</p>
                                      </div>
                                      <span className="text-[12px] font-semibold text-wo-text-primary">
                                        {formatQuoteMoney(row.estimated_cost ?? 0, row.currency ?? technicalBreakdownCurrency)}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : null}

                          {technicalBreakdown.consumable_rows.length > 0 ? (
                            <div>
                              <p className="text-[11px] font-semibold text-wo-text-primary mb-2">Consumabile</p>
                              <div className="space-y-2">
                                {technicalBreakdown.consumable_rows.map((row) => (
                                  <div key={row.material_key} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                                    <div className="flex items-start justify-between gap-3">
                                      <div>
                                        <p className="text-[12px] text-wo-text-primary font-medium">{row.display_name}</p>
                                        <p className="text-[10px] text-wo-text-muted mt-1">{row.quantity} {row.unit}</p>
                                      </div>
                                      <span className="text-[12px] font-semibold text-wo-text-primary">
                                        {formatQuoteMoney(row.estimated_cost ?? 0, row.currency ?? technicalBreakdownCurrency)}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : null}

                          {technicalBreakdown.operation_rows.length > 0 ? (
                            <div>
                              <p className="text-[11px] font-semibold text-wo-text-primary mb-2">Operațiuni</p>
                              <div className="space-y-2">
                                {technicalBreakdown.operation_rows.map((row) => (
                                  <div key={row.key} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                                    <div className="flex items-start justify-between gap-3">
                                      <div>
                                        <p className="text-[12px] text-wo-text-primary font-medium">{row.display_name}</p>
                                        <p className="text-[10px] text-wo-text-muted mt-1">{row.quantity} {row.unit}{row.pricing_status ? ` • ${row.pricing_status}` : ""}</p>
                                      </div>
                                      <span className="text-[12px] font-semibold text-wo-text-primary">
                                        {formatQuoteMoney(row.estimated_cost ?? 0, technicalBreakdownCurrency)}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : null}

                          {technicalBreakdown.edge_cant_operation_rows.length > 0 ? (
                            <div>
                              <p className="text-[11px] font-semibold text-wo-text-primary mb-2">Operațiuni muchii</p>
                              <div className="space-y-2">
                                {technicalBreakdown.edge_cant_operation_rows.map((row) => (
                                  <div key={row.key} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                                    <div className="flex items-start justify-between gap-3">
                                      <div>
                                        <p className="text-[12px] text-wo-text-primary font-medium">{row.display_name}</p>
                                        <p className="text-[10px] text-wo-text-muted mt-1">{row.quantity} {row.unit}{row.pricing_status ? ` • ${row.pricing_status}` : ""}</p>
                                      </div>
                                      <span className="text-[12px] font-semibold text-wo-text-primary">
                                        {formatQuoteMoney(row.estimated_cost ?? 0, technicalBreakdownCurrency)}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : null}

                          {technicalBreakdown.warnings && technicalBreakdown.warnings.length > 0 ? (
                            <div className="bg-amber-950/20 border border-amber-800/30 rounded-lg p-3">
                              <p className="text-[11px] font-semibold text-amber-200 mb-2">Avertizări backend</p>
                              <div className="space-y-1">
                                {technicalBreakdown.warnings.map((warning) => (
                                  <p key={`${warning.code}-${warning.source ?? "src"}`} className="text-[11px] text-amber-100/90">
                                    {warning.message}
                                  </p>
                                ))}
                              </div>
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                    </>
                  ) : (
                    <p className="text-[12px] text-wo-text-muted">Nu există încă breakdown tehnic V6 disponibil pentru această ofertă.</p>
                  )}
                </div>
              ) : null}

              {/*
                Sprint #18 — conditional rendering:
                  - If the backend persisted a component_breakdown (Sprint #17
                    CostEngine v2 output, wrapped inside line_items), render
                    the per-component breakdown table with expandable rows.
                  - Otherwise, fall back to the legacy flat line items UI —
                    byte-for-byte identical to pre-sprint behaviour.
                The UI ONLY reflects `selectedQuote.componentBreakdown`; it
                never recomputes cost.
              */}
              {selectedQuote.componentBreakdown && selectedQuote.componentBreakdown.length > 0 ? (
                <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                  <button
                    onClick={() => setExpandedLineItems(!expandedLineItems)}
                    className="flex items-center justify-between w-full mb-3"
                    aria-expanded={expandedLineItems}
                  >
                    <SectionHeader
                      title="Ofertă client — breakdown pe componente"
                      count={selectedQuote.componentBreakdown.length}
                      icon={<Layers className="w-4 h-4" />}
                    />
                    {expandedLineItems ? <ChevronUp className="w-4 h-4 text-wo-text-muted" /> : <ChevronDown className="w-4 h-4 text-wo-text-muted" />}
                  </button>
                  {expandedLineItems && (
                    <ComponentBreakdownTable components={selectedQuote.componentBreakdown} />
                  )}
                </div>
              ) : (
                <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                  <button
                    onClick={() => setExpandedLineItems(!expandedLineItems)}
                    className="flex items-center justify-between w-full mb-3"
                    aria-expanded={expandedLineItems}
                  >
                    <SectionHeader title="Linii comerciale ofertă" count={selectedQuote.lineItems.length} icon={<FileText className="w-4 h-4" />} />
                    {expandedLineItems ? <ChevronUp className="w-4 h-4 text-wo-text-muted" /> : <ChevronDown className="w-4 h-4 text-wo-text-muted" />}
                  </button>
                  {expandedLineItems && (
                    <div className="space-y-2">
                      {selectedQuote.lineItems.map((item, idx) => (
                        <div key={idx} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                          <p className="text-[12px] text-wo-text-primary font-medium">{item.description}</p>
                          <div className="flex items-center justify-between mt-1.5">
                            <span className="text-[10px] font-mono text-wo-text-muted">{item.productCode}</span>
                            <div className="flex items-center gap-3 text-[11px]">
                              <span className="text-wo-text-muted">
                                {item.quantity} × {formatQuoteMoney(item.unitPrice, selectedCurrency)}
                              </span>
                              <span className="text-wo-text-primary font-semibold">
                                {formatQuoteMoney(item.total, selectedCurrency)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {selectedQuote.flatMaterialNestingSummary ? (
                <FlatMaterialNestingSummary summary={selectedQuote.flatMaterialNestingSummary} />
              ) : null}

              {showVolumetricReadinessPanel && volumetricGate && (
                <VolumetricCommercialReadinessPanel
                  gate={volumetricGate}
                  testId="quote-volumetric-readiness"
                  showAcknowledgementControl={
                    selectedQuote.status === "accepted" ||
                    selectedQuote.status === "priced"
                  }
                  acknowledgementChecked={convertAckChecked}
                  onAcknowledgementChange={setConvertAckChecked}
                />
              )}

              {/* Pricing Summary */}
              {(!showIntakeV6CommercialSpine || showV6CompactTotals) && (
              <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                <SectionHeader title="Ofertă client — totaluri afișate" icon={<DollarSign className="w-4 h-4" />} />
                <p className="text-[10px] text-wo-text-muted mt-2 mb-3">
                  {isUnpricedIntakeV6Quote(selectedQuote)
                    ? "Draft V6 nepretuit: totalurile de mai jos sunt placeholder 0 RON până când bridge-ul V6 scrie totalurile backend oficiale."
                    : selectedQuote.acceptedSnapshotV2Id != null
                    ? "Frozen Snapshot V2 de mai sus rămâne sursa canonică pentru acceptare și conversie. Totalurile de aici sunt afișajul curent al ofertei selectate."
                    : "Până la freeze, aceste totaluri rămân afișajul curent al ofertei, nu un snapshot comercial înghețat."}
                </p>
                <div className="space-y-2 text-[12px]">
                  <div className="flex justify-between">
                    <span className="text-wo-text-muted">Subtotal</span>
                    <span className="text-wo-text-primary">
                      {isUnpricedIntakeV6Quote(selectedQuote)
                        ? "Nepretuit (draft V6)"
                        : formatQuoteMoney(selectedQuote.subtotal, selectedCurrency)}
                    </span>
                  </div>
                  {selectedQuote.discountPct > 0 && (
                    <div className="flex justify-between text-amber-400">
                      <span>Discount ({selectedQuote.discountPct}%)</span>
                      <span>-{formatQuoteMoney(selectedQuote.discount, selectedCurrency)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-wo-text-muted">Total fără TVA</span>
                    <span className="text-wo-text-primary">
                      {formatQuoteMoney(selectedQuote.totalBeforeVAT, selectedCurrency)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-wo-text-muted">
                      {selectedQuote.vatPct != null ? `TVA (${selectedQuote.vatPct}%)` : "TVA"}
                    </span>
                    <span className="text-wo-text-primary">
                      {formatQuoteMoney(selectedQuote.vat, selectedCurrency)}
                    </span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-wo-border-strong">
                    <span className="text-wo-text-primary font-bold">Total</span>
                    <span
                      className={`font-bold text-[14px] ${isUnpricedIntakeV6Quote(selectedQuote) ? "text-amber-300" : "text-wo-text-primary"}`}
                      data-testid={isUnpricedIntakeV6Quote(selectedQuote) ? "quote-v6-detail-unpriced-total" : undefined}
                    >
                      {isUnpricedIntakeV6Quote(selectedQuote)
                        ? "Nepretuit (draft V6)"
                        : formatQuoteMoney(selectedQuote.grandTotal, selectedCurrency)}
                    </span>
                  </div>
                  <div className="flex justify-between pt-1">
                    <span className="text-wo-text-muted flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />{" "}
                      {showIntakeV6CommercialSpine ? "Adaos comercial" : "Marjă"}
                    </span>
                    <span
                      className={`font-semibold ${selectedQuote.marginPct >= 35 ? "text-emerald-400" : "text-amber-400"}`}
                      data-testid={
                        showIntakeV6CommercialSpine ? "quote-v6-detail-adaos-percent" : undefined
                      }
                      title={
                        showIntakeV6CommercialSpine
                          ? "Adaos comercial % pe baza ofertei 7G (nu marjă pe cost: (preț−cost)/preț)."
                          : undefined
                      }
                    >
                      {selectedQuote.marginPct}%
                    </span>
                  </div>
                  {showIntakeV6CommercialSpine ? (
                    <p className="text-[10px] text-wo-text-muted pt-1" data-testid="quote-v6-adaos-vs-marja-hint">
                      Adaos = majorare pe baza comercială. Nu este marjă internă pe cost.
                    </p>
                  ) : null}
                </div>
              </div>
              )}

              {/* Notes */}
              {selectedQuote.notes && !hideV6RawNotes && (
                <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                  <SectionHeader title="Note" icon={<MessageSquare className="w-4 h-4" />} />
                  <p className="text-[12px] text-wo-text-secondary">{selectedQuote.notes}</p>
                </div>
              )}

              {showIntakeV6CommercialSpine ? (
                <IntakeV6QuoteDetailExtras>
                  <QuoteCommercialDocument
                    quoteDbId={selectedQuote.dbId ?? null}
                    quoteCode={selectedQuote.id}
                    visible={!!selectedQuote.dbId}
                  />
                  <QuoteDocumentGovernancePanel
                    quoteId={selectedQuote.dbId ?? null}
                    quoteCode={selectedQuote.id}
                    visible={!!selectedQuote.dbId}
                  />
                  <QuotePdfPanel
                    quoteDbId={selectedQuote.dbId ?? null}
                    quoteCode={selectedQuote.id}
                    visible={!!selectedQuote.dbId && source === "db"}
                  />
                  {selectedQuote.dbId && (
                    <QuoteOutputCompositionPreview
                      quoteId={selectedQuote.dbId}
                      quoteCode={selectedQuote.id}
                    />
                  )}
                  {selectedQuote.dbId && source === "db" && (
                    <QuoteOutputSnapshotsSection
                      quoteId={selectedQuote.dbId}
                      quoteCode={selectedQuote.id}
                    />
                  )}
                </IntakeV6QuoteDetailExtras>
              ) : (
                <>
              {/* Commercial Document Panel (BUILD 5) */}
              <QuoteCommercialDocument
                quoteDbId={selectedQuote.dbId ?? null}
                quoteCode={selectedQuote.id}
                visible={!!selectedQuote.dbId}
              />

              {/* Document Governance Surface (BUILD 26.40) */}
              <QuoteDocumentGovernancePanel
                quoteId={selectedQuote.dbId ?? null}
                quoteCode={selectedQuote.id}
                visible={!!selectedQuote.dbId}
              />

              {/* PDF Generation Panel (BUILD 15) */}
              <QuotePdfPanel
                quoteDbId={selectedQuote.dbId ?? null}
                quoteCode={selectedQuote.id}
                visible={!!selectedQuote.dbId && source === "db"}
              />

              {/* Output Composition Preview (BUILD 9) */}
              {selectedQuote.dbId && (
                <QuoteOutputCompositionPreview
                  quoteId={selectedQuote.dbId}
                  quoteCode={selectedQuote.id}
                />
              )}

              {/* Saved Output Snapshots (BUILD 10) */}
              {selectedQuote.dbId && source === "db" && (
                <QuoteOutputSnapshotsSection
                  quoteId={selectedQuote.dbId}
                  quoteCode={selectedQuote.id}
                />
              )}
                </>
              )}

              {!showIntakeV6CommercialSpine && (
                <>
                  <QuoteCommercialActionPanel
                    quote={selectedQuote}
                    onOpenRevision={() => setRevisionDialogQuote(selectedQuote)}
                  />

                  <QuoteAcceptanceConversionPanel
                    quote={selectedQuote}
                    duplicateOrderCode={duplicateOrderCode}
                    eurToRonRate={eurToRonRate}
                  />
                </>
              )}

              {isTerminalClosedQuoteStatus(selectedQuote.status) && (
                <div
                  className="bg-wo-surface-raised border border-red-900/40 rounded-lg p-4"
                  data-testid="quote-terminal-policy"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                    <p className="text-[12px] font-semibold text-red-300">
                      Ofertă terminală
                    </p>
                  </div>
                  <p className="text-[11px] text-wo-text-muted">
                    {terminalClosedQuoteMessage(selectedQuote.status)}
                  </p>
                </div>
              )}

              {/* Actions */}
              {!showIntakeV6CommercialSpine && (
                <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                  <SectionHeader title="Acțiuni" icon={<ArrowRight className="w-4 h-4" />} />
                  <div className="space-y-2">
                    {!isTerminalClosedQuoteStatus(selectedQuote.status) &&
                    (selectedQuote.status === "draft" || selectedQuote.status === "priced") && (
                      <button
                        data-testid="quote-assisted-send-action"
                        onClick={() => setSendDialogQuote(selectedQuote)}
                        disabled={actionLoading || !canMutateQuotes}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg text-[12px] font-semibold transition-colors"
                      >
                        <Send className="w-3.5 h-3.5" /> Trimite către Client
                      </button>
                    )}
                    {!isTerminalClosedQuoteStatus(selectedQuote.status) &&
                    ["sent", "viewed", "negotiating"].includes(selectedQuote.status) && (
                      <>
                        <button
                          data-testid="quote-accept-action"
                          onClick={() => handleQuoteAction("accept")}
                          disabled={actionLoading || !canMutateQuotes}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white rounded-lg text-[12px] font-semibold transition-colors"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> {QUOTE_INTERNAL_ACCEPTANCE_BUTTON_LABEL}
                        </button>
                        <button
                          data-testid="quote-reject-action"
                          onClick={() => handleQuoteAction("reject")}
                          disabled={actionLoading || !canMutateQuotes}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-60 text-wo-text-primary rounded-lg text-[12px] font-semibold transition-colors"
                        >
                          Respinge Oferta
                        </button>
                        <button
                          data-testid="quote-expire-action"
                          onClick={() => handleQuoteAction("expire")}
                          disabled={actionLoading || !canMutateQuotes}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-wo-text-secondary rounded-lg text-[12px] font-semibold transition-colors"
                        >
                          Marchează Expirată
                        </button>
                      </>
                    )}
                    {!isTerminalClosedQuoteStatus(selectedQuote.status) &&
                    (selectedQuote.status === "accepted" || selectedQuote.status === "priced") && (
                      <>
                        <button
                          data-testid="quote-convert-action"
                          onClick={() => handleQuoteAction("convert")}
                          disabled={
                            actionLoading || !canMutateQuotes || convertDisabledByReadiness
                          }
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-60 text-white rounded-lg text-[12px] font-bold transition-colors shadow-lg shadow-purple-900/20"
                        >
                          <Package className="w-3.5 h-3.5" /> {QUOTE_CONVERT_BUTTON_LABEL}
                        </button>
                        {convertBlockedByGate && (
                          <p
                            className="text-[10px] text-red-400 text-center"
                            data-testid="quote-convert-blocked-hint"
                          >
                            Conversie blocată — rezolvă blockers comerciale.
                          </p>
                        )}
                        {convertNeedsAck && (
                          <p
                            className="text-[10px] text-amber-400 text-center"
                            data-testid="quote-convert-ack-hint"
                          >
                            Confirmă avertismentele comerciale înainte de conversie.
                          </p>
                        )}
                      </>
                    )}
                    {!isTerminalClosedQuoteStatus(selectedQuote.status) &&
                    ["sent", "viewed", "negotiating", "accepted"].includes(selectedQuote.status) && (
                      <button
                        onClick={() => setSendDialogQuote(selectedQuote)}
                        disabled={!canMutateQuotes}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-wo-text-primary rounded-lg text-[12px] font-medium transition-colors"
                      >
                        <Send className="w-3.5 h-3.5" /> Retrimite / Descarcă PDF
                      </button>
                    )}
                    {isQuoteRevisionEligible(selectedQuote.status) && canMutateQuotes && (
                      <button
                        onClick={() => setRevisionDialogQuote(selectedQuote)}
                        disabled={actionLoading}
                        data-testid="quote-revision-action"
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-700 hover:bg-purple-600 disabled:opacity-60 text-white rounded-lg text-[12px] font-semibold transition-colors"
                      >
                        <Percent className="w-3.5 h-3.5" /> Creează revizie / ajustează discount
                      </button>
                    )}
                    {!canMutateQuotes && (
                      <p className="text-[10px] text-amber-400 text-center">
                        Acțiunile comerciale sunt blocate: necesită contract backend live.
                      </p>
                    )}
                    {actionLoading && (
                      <p className="text-[10px] text-wo-text-muted text-center">Se procesează...</p>
                    )}
                  </div>
                </div>
              )}

              {/* Next Step Guidance */}
              {!showIntakeV6CommercialSpine && selectedQuote.status === "draft" && (
                <NextStepPanel
                  title="Următorul pas: Calculează prețul"
                  description="Oferta este în stadiu draft. Adaugă componentele și calculează prețul pentru a o trimite clientului."
                  reason="Prețul trebuie calculat înainte de trimitere."
                />
              )}
              {!showIntakeV6CommercialSpine && selectedQuote.status === "priced" && (
                <NextStepPanel
                  title="Următorul pas: Trimite oferta"
                  description="Oferta este calculată. Poți trimite oferta către client sau o poți transforma în comandă din secțiunea Acțiuni."
                  primaryAction={{
                    label: "Trimite oferta",
                    onClick: () => setSendDialogQuote(selectedQuote),
                    disabled: !canMutateQuotes,
                    disabledReason: !canMutateQuotes ? "Necesită contract backend live" : undefined,
                  }}
                />
              )}
              {!showIntakeV6CommercialSpine &&
                (selectedQuote.status === "sent" || selectedQuote.status === "viewed" || selectedQuote.status === "negotiating") && (
                <NextStepPanel
                  title="Următorul pas: Marchează acceptarea internă"
                  description="Când operatorul confirmă acordul comercial, marchează oferta acceptată intern. Această acțiune nu trimite un link clientului și nu creează automat comanda."
                  reason="După acceptare, convertește oferta în comandă din secțiunea Acțiuni."
                />
              )}
              {isTerminalClosedQuoteStatus(selectedQuote.status) && (
                <NextStepPanel
                  title="Ofertă închisă"
                  description={terminalClosedQuoteMessage(selectedQuote.status)}
                  reason="Status terminal — fără acțiuni comerciale suplimentare."
                />
              )}
              {!showIntakeV6CommercialSpine && selectedQuote.status === "accepted" && (
                <NextStepPanel
                  title="Următorul pas: Convertește în comandă"
                  description="Oferta a fost marcată acceptată intern. Creează comanda din snapshot-ul ofertei active — totalurile ofertei nu se modifică la conversie."
                  primaryAction={{
                    label: QUOTE_CONVERT_BUTTON_LABEL,
                    onClick: () => handleQuoteAction("convert"),
                    disabled:
                      !canMutateQuotes || actionLoading || convertDisabledByReadiness,
                    disabledReason: convertBlockedByGate
                      ? "Gate comercial volumetric blocat"
                      : convertNeedsAck
                        ? "Confirmă avertismentele comerciale"
                        : !canMutateQuotes
                          ? "Necesită contract backend live"
                          : undefined,
                  }}
                  secondaryAction={{
                    label: "Vezi Comenzi",
                    to: "/orders",
                    variant: "ghost",
                  }}
                />
              )}
            </>
          ) : (
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-8 text-center">
              <FileText className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
              <p className="text-[13px] text-wo-text-muted">Selectează o ofertă pentru detalii</p>
              <p className="text-[11px] text-wo-text-dim mt-1">Alege o ofertă din lista din stânga pentru a vedea detaliile și acțiunile disponibile.</p>
            </div>
          )}
        </div>
      </div>

      {/* Send Dialog */}
      {sendDialogQuote && (
        <QuoteSendDialog
          quote={sendDialogQuote}
          open={!!sendDialogQuote}
          onClose={() => setSendDialogQuote(null)}
          onRegistered={async () => {
            await refresh();
          }}
        />
      )}

      {revisionDialogQuote && (
        <QuoteRevisionDialog
          quote={revisionDialogQuote}
          open={!!revisionDialogQuote}
          onClose={() => setRevisionDialogQuote(null)}
          onRevised={async () => {
            await refresh();
          }}
        />
      )}

      {/* Readiness Warning Acknowledgement Modal */}
      <ReadinessWarningAcknowledgementModal
        isOpen={pendingWarningQuoteId !== null}
        warnings={pendingReadinessWarnings}
        readinessResult={pendingReadinessResult}
        quoteId={pendingWarningQuoteId || ""}
        onConfirm={handleWarningAcknowledgement}
        onCancel={handleWarningModalCancel}
        isLoading={isSubmittingAcknowledgedConversion}
      />
    </div>
  );
}