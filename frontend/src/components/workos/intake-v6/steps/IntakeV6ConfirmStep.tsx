import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import {
	createIntakeV6DraftQuote,
	getIntakeV6MaterialBreakdown,
	getIntakeV6NestingPreview,
	getIntakeV6PricedQuoteDryRun,
	getIntakeV6PricingInputPreview,
	getIntakeV6ProductSystemBinding,
	getIntakeV6QuoteHandoffPreview,
	handoffIntakeV6ToOffer,
	saveIntakeV6InternalDraftQuoteConfirmation,
	type IntakeV6CreateDraftQuoteResponse,
	type IntakeV6OfferHandoffResponse,
	type IntakeV6PricedQuoteDryRunResponse,
	type IntakeV6MaterialBreakdownResponse,
	type IntakeV6NestingPreviewResponse,
	type IntakeV6PricingInputPreviewResponse,
	type IntakeV6ProductSystemBindingResponse,
	type IntakeV6QuoteHandoffPreviewResponse,
	type IntakeV6FinishSetup,
} from "@/lib/intakeV6/intakeV6Api";
import { buildIntakeV6ConfirmSummary } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import {
	readIntakeV6OfferCommercialInputs,
	resolveIntakeV6OfferCommercialDefaults,
	serializeIntakeV6OfferCommercialInputs,
	type IntakeV6OfferCommercialInputs,
} from "@/lib/intakeV6/intakeV6OfferCalculator";
import {
	formatQuoteHandoffBlocker,
	hasArtworkNeedsDecisionWarning,
	hasFinishSetupIncompleteBlocker,
	resolveQuoteHandoffUiStatus,
	buildReviewHandoffSurfacing,
} from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";
import {
	resolveConfirmChecklistProgress,
	resolveConfirmSubmitDisabledReason,
} from "@/lib/intakeV6/intakeV6ConfirmSubmitReason";
import { buildIntakeV6ConfirmConsolidatedStatus } from "@/lib/intakeV6/intakeV6ConfirmConsolidatedStatus";
import { formatWorkspaceReadinessLabel } from "@/lib/intakeV6/intakeV6OperatorUiDisplay";
import {
	detectArtworkOnlyRequiresDecision,
	resolveArtworkOnlyFatalBlockers,
	resolveArtworkOnlyReviewWarnings,
} from "@/lib/intakeV6/intakeV6ArtworkOnlyGuard";
import { getPersistedFileHash } from "@/lib/intakeV6/intakeV6AnalysisIdentity";
import { v6 } from "../atoms/intakeV6Presentation";
import IntakeV6ConfirmOperationalSummary from "../IntakeV6ConfirmOperationalSummary";
import IntakeV6ConfirmDashboard from "../IntakeV6ConfirmDashboard";
import IntakeV6ConfirmKpiStrip from "../IntakeV6ConfirmKpiStrip";
import IntakeV6ConfirmHandoffPanel from "../IntakeV6ConfirmHandoffPanel";
import IntakeV6ConfirmConsolidatedStatusPanel from "../IntakeV6ConfirmConsolidatedStatusPanel";
import IntakeV6ModularFormAwarenessPanel from "../IntakeV6ModularFormAwarenessPanel";
import IntakeV6PricingInputPanel from "../IntakeV6PricingInputPanel";
import IntakeV6SvgPreviewCanvas from "../IntakeV6SvgPreviewCanvas";
import IntakeV6TechnicalDetailsAccordion from "../atoms/IntakeV6TechnicalDetailsAccordion";
import { useIntakeV6WorkspaceHeaderStatusOptional } from "../IntakeV6WorkspaceHeaderStatusContext";
import { useCompanyCommercialSettings } from "@/hooks/useCompanyCommercialSettings";
import { useModularFormContract } from "@/lib/intakeV6/useModularFormContract";
import { useModularFormAwareness } from "@/lib/intakeV6/useModularFormAwareness";
import { isAnalysisReadyForReview } from "@/lib/intakeV6/intakeV6AnalysisIdentity";

const EMPTY_REVIEW_WARNINGS: string[] = [];

export interface IntakeV6ConfirmStepProps {
	hook: IntakeV6WorkspaceHook;
}

export default function IntakeV6ConfirmStep({ hook }: IntakeV6ConfirmStepProps) {
	const navigate = useNavigate();
	const { state, isReadyForQuotePreview, firstBlocker, saveFinishSetup, trySetStep } = hook;
	const statusCtx = useIntakeV6WorkspaceHeaderStatusOptional();
	const ws = state.workspace;
	const { eurToRonRate } = useCompanyCommercialSettings(Boolean(ws?.id));
	const payload = ws?.payload;
	const resolveCommercialInputs = (
		persisted?: IntakeV6OfferCommercialInputs | null,
		preview?: IntakeV6PricingInputPreviewResponse | null,
	) =>
		resolveIntakeV6OfferCommercialDefaults(
			preview ?? null,
			persisted == null ? undefined : serializeIntakeV6OfferCommercialInputs(persisted),
		);
	const finishSetup = useMemo(() => {
		const raw = payload?.finish_setup;
		if (raw == null || typeof raw !== "object" || Array.isArray(raw)) {
			return null;
		}
		return raw as IntakeV6FinishSetup;
	}, [payload]);
	const persistedCommercialInputs = useMemo(
		() => readIntakeV6OfferCommercialInputs(finishSetup?.commercial_inputs),
		[finishSetup],
	);
	const persistedCommercialInputsKey = useMemo(
		() =>
			JSON.stringify(
				persistedCommercialInputs == null
					? null
					: serializeIntakeV6OfferCommercialInputs(persistedCommercialInputs),
			),
		[persistedCommercialInputs],
	);
	const [binding, setBinding] = useState<IntakeV6ProductSystemBindingResponse | null>(null);
	const [materialBreakdown, setMaterialBreakdown] = useState<IntakeV6MaterialBreakdownResponse | null>(null);
	const [nestingPreview, setNestingPreview] = useState<IntakeV6NestingPreviewResponse | null>(null);
	const [pricingPreview, setPricingPreview] = useState<IntakeV6PricingInputPreviewResponse | null>(null);
	const [pricedQuoteDryRun, setPricedQuoteDryRun] = useState<IntakeV6PricedQuoteDryRunResponse | null>(null);
	const [handoffPreview, setHandoffPreview] = useState<IntakeV6QuoteHandoffPreviewResponse | null>(null);
	const [confirmPreviewLoading, setConfirmPreviewLoading] = useState(true);
	const [confirmPreviewError, setConfirmPreviewError] = useState<string | null>(null);
	const [confirmDraftBoundary, setConfirmDraftBoundary] = useState(false);
	const [confirmInternalDraft, setConfirmInternalDraft] = useState(false);
	const [savingInternalConfirmation, setSavingInternalConfirmation] = useState(false);
	const [submitting, setSubmitting] = useState(false);
	const [submittingPricedQuote, setSubmittingPricedQuote] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [result, setResult] = useState<IntakeV6CreateDraftQuoteResponse | null>(null);
	const [pricedQuoteResult, setPricedQuoteResult] = useState<IntakeV6OfferHandoffResponse | null>(null);
	const [commercialInputs, setCommercialInputs] = useState<IntakeV6OfferCommercialInputs>(() =>
		resolveCommercialInputs(persistedCommercialInputs, null),
	);
	const commercialSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

	const clientAnalysisHash =
		state.localFileHash ?? getPersistedFileHash(payload as Record<string, unknown> | undefined);

	const templateCode =
		binding?.template_code ??
		(payload?.product_binding != null &&
		typeof payload.product_binding === "object" &&
		!Array.isArray(payload.product_binding)
			? String((payload.product_binding as Record<string, unknown>).template_code ?? "")
			: null);

	const modularFormContractHook = useModularFormContract(templateCode || null);
	const svgSourcePayload =
		payload?.svg_source != null &&
		typeof payload.svg_source === "object" &&
		!Array.isArray(payload.svg_source)
			? (payload.svg_source as Record<string, unknown>)
			: null;
	const quoteGeometryPayload =
		payload?.quote_geometry != null &&
		typeof payload.quote_geometry === "object" &&
		!Array.isArray(payload.quote_geometry)
			? (payload.quote_geometry as Record<string, unknown>)
			: null;
	const modularAwareness = useModularFormAwareness({
		contract: modularFormContractHook.contract,
		loading: modularFormContractHook.loading,
		error: modularFormContractHook.error,
		finishSetup: finishSetup as unknown as Record<string, unknown> | null,
		quoteGeometry: quoteGeometryPayload,
		svgSource: svgSourcePayload,
		analysisReady: isAnalysisReadyForReview(state),
	});

	useEffect(() => {
		if (!ws?.id) return;
		let cancelled = false;
		setConfirmPreviewLoading(true);
		setConfirmPreviewError(null);
		void Promise.all([
			getIntakeV6ProductSystemBinding(ws.id),
			getIntakeV6MaterialBreakdown(ws.id),
			getIntakeV6NestingPreview(ws.id),
			getIntakeV6PricingInputPreview(ws.id),
			getIntakeV6PricedQuoteDryRun(ws.id),
			getIntakeV6QuoteHandoffPreview(ws.id, clientAnalysisHash ?? undefined),
		])
			.then(([
				bindingResponse,
				breakdownResponse,
				nestingResponse,
				pricingResponse,
				pricedQuoteDryRunResponse,
				handoffResponse,
			]) => {
				if (cancelled) return;
				setBinding(bindingResponse);
				setMaterialBreakdown(breakdownResponse);
				setNestingPreview(nestingResponse);
				setPricingPreview(pricingResponse);
				setPricedQuoteDryRun(pricedQuoteDryRunResponse);
				setHandoffPreview(handoffResponse);
			})
			.catch((err) => {
				if (!cancelled) {
					setConfirmPreviewError(err instanceof Error ? err.message : "Failed to fetch");
					setBinding(null);
					setMaterialBreakdown(null);
					setNestingPreview(null);
					setPricingPreview(null);
					setPricedQuoteDryRun(null);
					setHandoffPreview(null);
				}
			})
			.finally(() => {
				if (!cancelled) setConfirmPreviewLoading(false);
			});
		return () => {
			cancelled = true;
		};
	}, [ws?.id, ws?.updated_at, clientAnalysisHash]);

	useEffect(() => {
		const nextCommercialInputs = resolveCommercialInputs(persistedCommercialInputs, pricingPreview);
		const nextSerialized = JSON.stringify(serializeIntakeV6OfferCommercialInputs(nextCommercialInputs));
		setCommercialInputs((current) => {
			const currentSerialized = JSON.stringify(serializeIntakeV6OfferCommercialInputs(current));
			return currentSerialized === nextSerialized ? current : nextCommercialInputs;
		});
	}, [ws?.id, pricingPreview?.workspace_id, persistedCommercialInputsKey]);

	useEffect(() => {
		return () => {
			if (commercialSaveTimerRef.current) {
				clearTimeout(commercialSaveTimerRef.current);
				commercialSaveTimerRef.current = null;
			}
		};
	}, []);

	function handleCommercialInputsChange(next: IntakeV6OfferCommercialInputs) {
		setCommercialInputs(next);
		if (!ws?.id || !finishSetup) {
			return;
		}
		if (commercialSaveTimerRef.current) {
			clearTimeout(commercialSaveTimerRef.current);
		}
		commercialSaveTimerRef.current = setTimeout(() => {
			commercialSaveTimerRef.current = null;
			void saveFinishSetup({
				...finishSetup,
				commercial_inputs: serializeIntakeV6OfferCommercialInputs(next),
			});
		}, 700);
	}

	const layerCount =
		state.layerChips.length ||
		(Array.isArray((payload?.layer_role_setup as { layers?: unknown[] } | undefined)?.layers)
			? (payload?.layer_role_setup as { layers: unknown[] }).layers.length
			: 0);

	const summary = useMemo(
		() =>
			buildIntakeV6ConfirmSummary({
				payload: payload as Record<string, unknown> | undefined,
				layerCount,
				materialBreakdown,
				nestingPreview,
				handoffBlockers: handoffPreview?.blockers,
			}),
		[payload, layerCount, materialBreakdown, nestingPreview, handoffPreview?.blockers],
	);

	const handoffPreviewOptions = useMemo(
		() => ({
			loading: confirmPreviewLoading,
			fetchError: confirmPreviewError,
		}),
		[confirmPreviewLoading, confirmPreviewError],
	);
	const handoffUi = resolveQuoteHandoffUiStatus(handoffPreview, handoffPreviewOptions);

	const handoffBlockers = handoffPreview?.blockers ?? [];
	const fatalBlockers = handoffPreview?.fatal_blockers ?? handoffBlockers;
	const reviewWarnings = useMemo(
		() =>
			resolveArtworkOnlyReviewWarnings(
				state.analyzerReport,
				state.layerRoleConfirmation,
				handoffPreview?.review_warnings ?? EMPTY_REVIEW_WARNINGS,
			),
		[state.analyzerReport, state.layerRoleConfirmation, handoffPreview?.review_warnings],
	);
	const bindingBlockers = binding?.blockers ?? [];
	const artworkOnlyBlocked = detectArtworkOnlyRequiresDecision(
		state.analyzerReport,
		state.layerRoleConfirmation,
	);
	const effectiveHandoffAllowed = handoffUi.handoffAllowed && !artworkOnlyBlocked;
	const allFatalBlockers = resolveArtworkOnlyFatalBlockers(
		state.analyzerReport,
		state.layerRoleConfirmation,
		[...new Set([...fatalBlockers, ...bindingBlockers])],
	);
	const finishSetupIncomplete = hasFinishSetupIncompleteBlocker(fatalBlockers, ws?.readiness_status);
	const artworkNeedsDecision =
		hasArtworkNeedsDecisionWarning(reviewWarnings) || artworkOnlyBlocked;
	const operatorConfirmationComplete = handoffPreview?.operator_confirmation_complete ?? false;
	const quoteGeometry = payload?.quote_geometry as
		| { width_mm?: number; height_mm?: number; letter_perimeter_m?: number }
		| undefined;

	const canShowHandoffSection = isReadyForQuotePreview || !finishSetupIncomplete;
	const canResolveInternalDraftConfirmation =
		canShowHandoffSection && bindingBlockers.length === 0 && !finishSetupIncomplete;
	const canShowBoundaryCheckboxes =
		canShowHandoffSection &&
		handoffUi.handoffAllowed &&
		bindingBlockers.length === 0 &&
		!finishSetupIncomplete;

	const canSubmit =
		Boolean(ws?.id) &&
		isReadyForQuotePreview &&
		effectiveHandoffAllowed &&
		bindingBlockers.length === 0 &&
		!artworkOnlyBlocked &&
		confirmDraftBoundary &&
		confirmInternalDraft &&
		operatorConfirmationComplete &&
		!submitting &&
		!result;

	const pricedQuoteDryRunReady = pricedQuoteDryRun?.pricing_status === "V6_PRICED_DRY_RUN_READY";
	const pricedQuoteDryRunTotal = pricedQuoteDryRun?.commercial_totals?.total_gross ?? null;
	const pricedQuoteDryRunBlockers = pricedQuoteDryRun?.blockers ?? [];
	const createPricedQuoteDisabledReason = useMemo(() => {
		if (pricedQuoteResult) return "Oferta pretuita a fost deja creata.";
		if (submitting || submittingPricedQuote) return "O actiune de ofertare este deja in curs.";
		if (!ws?.id) return "Workspace V6 indisponibil.";
		if (!clientAnalysisHash) return "Lipseste identitatea analizei SVG pentru handoff.";
		if (!isReadyForQuotePreview) return firstBlocker ?? "Workspace-ul nu este gata pentru ofertare.";
		if (!effectiveHandoffAllowed) return allFatalBlockers[0] ? formatQuoteHandoffBlocker(allFatalBlockers[0]) : "Handoff-ul V6 este blocat.";
		if (bindingBlockers.length > 0) return formatQuoteHandoffBlocker(bindingBlockers[0]);
		if (!operatorConfirmationComplete) return "Confirmarea operatorului nu este persistata.";
		if (!confirmInternalDraft) return "Confirma explicit draftul intern.";
		if (!confirmDraftBoundary) return "Confirma ca nu se creeaza comanda, executie sau miscari de stoc.";
		if (!pricedQuoteDryRunReady) return pricedQuoteDryRunBlockers[0]?.message ?? "Dry-run-ul backend de pretuire nu este pregatit.";
		if (pricedQuoteDryRunTotal == null) return "Totalul comercial V6 calculat pe server lipseste.";
		return null;
	}, [
		allFatalBlockers,
		bindingBlockers,
		clientAnalysisHash,
		confirmDraftBoundary,
		confirmInternalDraft,
		effectiveHandoffAllowed,
		firstBlocker,
		isReadyForQuotePreview,
		operatorConfirmationComplete,
		pricedQuoteDryRunBlockers,
		pricedQuoteDryRunReady,
		pricedQuoteDryRunTotal,
		pricedQuoteResult,
		submitting,
		submittingPricedQuote,
		ws?.id,
	]);
	const canCreatePricedQuote = createPricedQuoteDisabledReason == null;

	async function handleInternalDraftConfirmation(checked: boolean) {
		if (!ws?.id || finishSetupIncomplete) return;
		setConfirmInternalDraft(checked);
		if (!checked) {
			setSavingInternalConfirmation(true);
			try {
				await saveIntakeV6InternalDraftQuoteConfirmation(ws.id, { confirmed: false });
				const refreshed = await getIntakeV6QuoteHandoffPreview(ws.id, clientAnalysisHash ?? undefined);
				setHandoffPreview(refreshed);
			} catch (err) {
				setError(err instanceof Error ? err.message : "Salvare confirmare draft intern esuata.");
				setConfirmInternalDraft(false);
			} finally {
				setSavingInternalConfirmation(false);
			}
			return;
		}
		setSavingInternalConfirmation(true);
		setError(null);
		try {
			await saveIntakeV6InternalDraftQuoteConfirmation(ws.id, { confirmed: true });
			const refreshed = await getIntakeV6QuoteHandoffPreview(ws.id, clientAnalysisHash ?? undefined);
			setHandoffPreview(refreshed);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Salvare confirmare draft intern esuata.");
			setConfirmInternalDraft(false);
		} finally {
			setSavingInternalConfirmation(false);
		}
	}

	const showHandoffCheckboxes = canShowBoundaryCheckboxes;

	const confirmHandoffSurfacing = useMemo(
		() =>
			buildReviewHandoffSurfacing({
				handoff: handoffPreview,
				handoffOptions: handoffPreviewOptions,
				containsMissingPrices: materialBreakdown?.totals.contains_missing_prices === true,
				allArtworkFinishesConfirmed: !artworkNeedsDecision,
			}),
		[
			handoffPreview,
			handoffPreviewOptions,
			materialBreakdown?.totals.contains_missing_prices,
			artworkNeedsDecision,
		],
	);

	const submitDisabledReason = useMemo(
		() =>
			resolveConfirmSubmitDisabledReason({
				hasResult: Boolean(result),
				submitting,
				finishSetupIncomplete,
				bindingBlockers,
				handoffAllowed: effectiveHandoffAllowed,
				operatorConfirmationComplete,
				confirmInternalDraft,
				confirmDraftBoundary,
				showHandoffCheckboxes,
				isReadyForQuotePreview,
				firstBlocker,
				formatBlocker: formatQuoteHandoffBlocker,
			}),
		[
			result,
			submitting,
			finishSetupIncomplete,
			bindingBlockers,
			handoffUi.handoffAllowed,
			effectiveHandoffAllowed,
			operatorConfirmationComplete,
			confirmInternalDraft,
			confirmDraftBoundary,
			showHandoffCheckboxes,
			isReadyForQuotePreview,
			firstBlocker,
		],
	);

	const checklistProgress = useMemo(
		() =>
			resolveConfirmChecklistProgress({
				finishSetupComplete: !finishSetupIncomplete,
				operatorConfirmationComplete,
				confirmInternalDraft,
				draftBoundaryAcknowledged: confirmDraftBoundary,
				showDraftBoundaryItem: showHandoffCheckboxes,
			}),
		[
			finishSetupIncomplete,
			operatorConfirmationComplete,
			confirmInternalDraft,
			confirmDraftBoundary,
			showHandoffCheckboxes,
		],
	);

	const modularPendingCount = useMemo(() => {
		const view = modularAwareness.preview?.operatorView;
		if (!view) return 0;
		return [...view.productReady, ...view.mounting].filter((line) => line.state === "pending").length;
	}, [modularAwareness.preview]);

	const consolidatedStatus = useMemo(
		() =>
			buildIntakeV6ConfirmConsolidatedStatus({
				loading: confirmPreviewLoading && handoffPreview == null,
				fetchError: confirmPreviewError,
				finishSetupIncomplete,
				effectiveHandoffAllowed,
				bindingBlockers,
				allFatalBlockers,
				artworkNeedsDecision,
				reviewWarnings,
				containsMissingPrices: materialBreakdown?.totals.contains_missing_prices === true,
				operatorConfirmationComplete,
				confirmInternalDraft,
				confirmDraftBoundary,
				showHandoffCheckboxes,
				checklistProgress,
				modularPendingCount,
				formatBlocker: formatQuoteHandoffBlocker,
			}),
		[
			confirmPreviewLoading,
			handoffPreview,
			confirmPreviewError,
			finishSetupIncomplete,
			effectiveHandoffAllowed,
			bindingBlockers,
			allFatalBlockers,
			artworkNeedsDecision,
			reviewWarnings,
			materialBreakdown?.totals.contains_missing_prices,
			operatorConfirmationComplete,
			confirmInternalDraft,
			confirmDraftBoundary,
			showHandoffCheckboxes,
			checklistProgress,
			modularPendingCount,
		],
	);

	const setHeaderOverlay = statusCtx?.setOverlay;
	const setHeaderHandlers = statusCtx?.setHandlers;
	const setConfirmFooter = statusCtx?.setConfirmFooter;

	useEffect(() => {
		if (!setHeaderOverlay) return;
		setHeaderOverlay({
			loading: confirmPreviewLoading && handoffPreview == null,
			analysisReady: isReadyForQuotePreview,
			svgReady: Boolean(state.svg?.fileName),
			operatorConfirmationMissing: !operatorConfirmationComplete,
			reviewWarnings,
			containsMissingPrices: materialBreakdown?.totals.contains_missing_prices === true,
			surfacing: confirmHandoffSurfacing,
			pendingConfirmationCount:
				(!operatorConfirmationComplete ? 1 : 0) +
				(artworkNeedsDecision ? 1 : 0) +
				allFatalBlockers.length,
			widthMm: quoteGeometry?.width_mm ?? null,
			heightMm: quoteGeometry?.height_mm ?? null,
			perimeterM: quoteGeometry?.letter_perimeter_m ?? null,
		});
		return () => setHeaderOverlay({});
	}, [
		setHeaderOverlay,
		confirmPreviewLoading,
		handoffPreview,
		isReadyForQuotePreview,
		state.svg?.fileName,
		operatorConfirmationComplete,
		reviewWarnings,
		artworkNeedsDecision,
		allFatalBlockers.length,
		payload?.quote_geometry,
		materialBreakdown?.totals.contains_missing_prices,
		confirmHandoffSurfacing,
	]);

	useEffect(() => {
		if (!setHeaderHandlers) return;
		setHeaderHandlers({
			onJumpToPending: () => {
				document
					.querySelector('[data-testid="intake-v6-quote-handoff"]')
					?.scrollIntoView({ behavior: "smooth", block: "start" });
			},
		});
		return () => setHeaderHandlers({ onJumpToPending: undefined });
	}, [setHeaderHandlers]);

	const handleOpenQuoteWizardRef = useRef<() => void>(() => {});

	async function handleOpenQuoteWizard() {
		if (!ws?.id || !canSubmit) return;
		setSubmitting(true);
		setError(null);
		try {
			if (!clientAnalysisHash) {
				setError("Lipseste identitatea analizei SVG pentru handoff.");
				setSubmitting(false);
				return;
			}
			const response = await createIntakeV6DraftQuote(ws.id, {
				confirm_create_draft_only: true,
				confirm_no_order: true,
				confirm_no_execution: true,
				confirm_no_inventory: true,
				confirm_internal_draft_quote: true,
				decision_reason: "Operator approved draft quote from Intake V6 Confirm step.",
				client_analysis_hash: clientAnalysisHash,
			});
			setResult(response);
			setPricingPreview((current) =>
				current
					? {
						...current,
						quote_input_payload: response.quote_input_payload,
					}
					: current,
			);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Creare draft quote esuata.");
		} finally {
			setSubmitting(false);
		}
	}
	handleOpenQuoteWizardRef.current = handleOpenQuoteWizard;

	async function handleCreatePricedQuote() {
		if (!ws?.id || !canCreatePricedQuote || pricedQuoteDryRunTotal == null || !clientAnalysisHash) return;
		const confirmed = window.confirm(
			"Creez oferta pretuita folosind totalurile comerciale V6 calculate pe server. Aceasta actiune scrie preturile pe oferta, dar nu creeaza comanda, executie sau miscari de stoc.",
		);
		if (!confirmed) return;
		setSubmittingPricedQuote(true);
		setError(null);
		try {
			const response = await handoffIntakeV6ToOffer(ws.id, {
				client_analysis_hash: clientAnalysisHash,
				expected_total_gross: pricedQuoteDryRunTotal,
				expected_pricing_hash: pricedQuoteDryRun?.pricing_hash ?? undefined,
				operator_confirmation: true,
			});
			if (response.status !== "V6_PRICED_QUOTE_WRITTEN") {
				const blockerMessage = (response.blockers ?? [])
					.map((blocker) => blocker.message || blocker.code)
					.filter(Boolean)
					.join("; ");
				throw new Error(blockerMessage || "Crearea ofertei pretuita a fost blocata de backend.");
			}
			setPricedQuoteResult(response);
			if (response.next_route) {
				navigate(response.next_route);
			}
		} catch (err) {
			setError(err instanceof Error ? err.message : "Creare oferta pretuita esuata.");
		} finally {
			setSubmittingPricedQuote(false);
		}
	}

	const onConfirmFooterSubmit = useCallback(() => {
		void handleOpenQuoteWizardRef.current();
	}, []);

	useEffect(() => {
		if (!setConfirmFooter) return;
		setConfirmFooter({
			canSubmit,
			submitting: submitting || submittingPricedQuote,
			submitLabel: "Creează draft intern V6",
			submittingLabel: "Creez draft intern…",
			disabledReason: submitDisabledReason,
			checklistDone: checklistProgress.done,
			checklistTotal: checklistProgress.total,
			onSubmit: onConfirmFooterSubmit,
		});
		return () => setConfirmFooter(null);
	}, [
		setConfirmFooter,
		canSubmit,
		submitting,
		submittingPricedQuote,
		submitDisabledReason,
		checklistProgress.done,
		checklistProgress.total,
		onConfirmFooterSubmit,
	]);

	const fallbackBlockerMessage =
		!showHandoffCheckboxes
			? firstBlocker ??
				(finishSetupIncomplete
					? "Finalizează finisajele în Review."
					: handoffUi.label.includes("blocat")
						? "Handoff blocat — verifică verdictul."
						: "Completează pașii anteriori.")
			: null;

	return (
		<section data-testid="intake-v6-step-confirm">
			<div className="space-y-3" data-testid="intake-v6-confirm-dashboard">
				<div>
					<h2 className={v6.screenTitle}>Confirmare draft intern</h2>
					<p className={v6.sectionDesc}>Sumar logic înainte de crearea draftului de ofertare.</p>
				</div>

				<IntakeV6ConfirmConsolidatedStatusPanel status={consolidatedStatus} />

				{confirmPreviewError ? (
					<p className="text-[11px] text-rose-300" data-testid="intake-v6-confirm-preview-error">
						{confirmPreviewError}
					</p>
				) : null}

				<IntakeV6ModularFormAwarenessPanel
					loadStatus={modularAwareness.loadStatus}
					preview={modularAwareness.preview}
					triggerMismatchNote={modularAwareness.preview?.triggerMismatchNote}
					templateCode={templateCode || null}
					variant="confirm"
				/>

				<div className={v6.confirmStepGrid} data-testid="intake-v6-confirm-layout">
					<div className="min-w-0 space-y-3">
						<IntakeV6ConfirmKpiStrip
							internalCostEur={materialBreakdown?.totals.estimated_cost_total ?? null}
							internalCurrency={materialBreakdown?.totals.currency ?? "EUR"}
							widthMm={quoteGeometry?.width_mm ?? null}
							heightMm={quoteGeometry?.height_mm ?? null}
							layerCount={layerCount}
							loading={confirmPreviewLoading}
						/>

						<IntakeV6ConfirmDashboard
							workspaceCode={ws?.workspace_code}
							templateLabel={binding?.template_label ?? ws?.template_code}
							svgFileName={state.svg?.fileName}
							summary={summary}
							handoffPreview={handoffPreview}
							fatalBlockers={allFatalBlockers}
							reviewWarnings={reviewWarnings}
							nestingPreview={nestingPreview}
							loading={confirmPreviewLoading}
						/>

						<IntakeV6ConfirmHandoffPanel
							finishSetupIncomplete={finishSetupIncomplete}
							operatorConfirmationComplete={operatorConfirmationComplete}
							confirmInternalDraft={confirmInternalDraft}
							confirmDraftBoundary={confirmDraftBoundary}
							showHandoffCheckboxes={showHandoffCheckboxes}
							canResolveInternalDraftConfirmation={canResolveInternalDraftConfirmation}
							savingInternalConfirmation={savingInternalConfirmation}
							allFatalBlockers={allFatalBlockers}
							showBlockerList={allFatalBlockers.length > 0}
							resultMessage={
								pricedQuoteResult
									? `Oferta pretuita a fost creata: ${pricedQuoteResult.quote_code}. Totalurile comerciale V6 au fost scrise pe oferta. Nu a fost creata comanda.`
									: result ? `Draft ${result.quote_code} creat. Rămâi în V6.` : null
							}
							errorMessage={error}
							fallbackBlockerMessage={fallbackBlockerMessage}
							onInternalDraftChange={(checked) => void handleInternalDraftConfirmation(checked)}
							onDraftBoundaryChange={setConfirmDraftBoundary}
						/>

						<div className={`${v6.cardCompact} !p-3`} data-testid="intake-v6-priced-quote-cta-card">
							<div className="mb-2 flex flex-wrap items-start justify-between gap-2">
								<div>
									<h3 className={v6.sectionTitle}>Oferta pretuita</h3>
									<p className="mt-1 text-[11px] text-slate-400">
										Scrie totalurile comerciale V6 pe oferta. Nu creeaza comanda, executie sau miscari de stoc.
									</p>
								</div>
								<span className="text-[12px] font-semibold text-slate-100" data-testid="intake-v6-priced-quote-total">
									{pricedQuoteDryRunTotal == null
										? "Total indisponibil"
										: `${pricedQuoteDryRunTotal.toLocaleString("ro-RO", {
											minimumFractionDigits: 2,
											maximumFractionDigits: 2,
										})} ${pricedQuoteDryRun?.commercial_totals?.currency ?? "RON"}`}
								</span>
							</div>
							{createPricedQuoteDisabledReason ? (
								<p className="mb-2 text-[11px] text-amber-200" data-testid="intake-v6-priced-quote-disabled-reason">
									{createPricedQuoteDisabledReason}
								</p>
							) : null}
							<div className="flex flex-wrap items-center gap-2">
								<button
									type="button"
									className={v6.btnPrimary}
									disabled={!canCreatePricedQuote}
									data-testid="intake-v6-create-priced-quote"
									onClick={() => void handleCreatePricedQuote()}
								>
									{submittingPricedQuote ? "Creez oferta pretuita…" : "Creeaza oferta pretuita"}
								</button>
								{pricedQuoteResult?.next_route ? (
									<button
										type="button"
										className={v6.btnGhost}
										data-testid="intake-v6-priced-quote-open"
										onClick={() => navigate(pricedQuoteResult.next_route as string)}
									>
										Deschide oferta
									</button>
								) : null}
							</div>
						</div>

						<IntakeV6TechnicalDetailsAccordion
							title="Rezumat operator"
							testId="intake-v6-confirm-operator-summary"
						>
							<IntakeV6ConfirmOperationalSummary summary={summary} variant="operator" />
						</IntakeV6TechnicalDetailsAccordion>

						<IntakeV6TechnicalDetailsAccordion
							title="Detalii tehnice complete"
							testId="intake-v6-confirm-technical-details"
						>
							<div className={`${v6.card} mb-3`} data-testid="intake-v6-readiness-status">
								<ul className="space-y-1 text-[11px] text-slate-400">
									<li data-testid="intake-v6-readiness-preview">
										Preview: {handoffUi.handoffAllowed ? "gata" : "blocat"}
									</li>
									{ws?.readiness_status ? (
										<li>Workspace: {formatWorkspaceReadinessLabel(ws.readiness_status)}</li>
									) : null}
									{binding ? (
										<li data-testid="intake-v6-product-binding">
											ProductSystem: {binding.operation_count} operații ·{" "}
											{binding.template_active ? "activ" : "inactiv"}
										</li>
									) : null}
								</ul>
							</div>
							<IntakeV6ConfirmOperationalSummary summary={summary} variant="technical" />
						</IntakeV6TechnicalDetailsAccordion>
					</div>

					<div
						className="space-y-3 lg:sticky lg:top-3 lg:self-start"
						data-testid="intake-v6-confirm-pricing-sidebar"
					>
						<IntakeV6PricingInputPanel
							preview={pricingPreview}
							breakdown={materialBreakdown}
							officialPricing={pricedQuoteDryRun}
							loading={confirmPreviewLoading}
							commercialInputs={commercialInputs}
							onCommercialInputsChange={handleCommercialInputsChange}
							eurToRonRate={eurToRonRate}
							onEditCommercialInReview={() => trySetStep("review")}
							variant="confirmHero"
						/>
						{state.svg?.previewSource ? (
							<div className={`${v6.cardCompact} !p-3`} data-testid="intake-v6-confirm-svg-preview-panel">
								<h3 className={`mb-2 ${v6.sectionTitle}`}>Preview SVG</h3>
								<IntakeV6SvgPreviewCanvas
									source={state.svg.previewSource}
									variant="compact"
									testId="intake-v6-confirm-svg-preview"
								/>
							</div>
						) : null}
					</div>
				</div>
			</div>
		</section>
	);
}


