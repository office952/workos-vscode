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
import {
	confirmJobProductTruth,
	getJobProductTruthStatus,
} from "@/lib/intakeV6/productTruthJobConfirm";
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
import {
	buildIntakeV6ConfirmConsolidatedStatus,
	type IntakeV6ConfirmConsolidatedStatusDisplay,
} from "@/lib/intakeV6/intakeV6ConfirmConsolidatedStatus";
import {
	detectArtworkOnlyRequiresDecision,
	resolveArtworkOnlyFatalBlockers,
	resolveArtworkOnlyReviewWarnings,
} from "@/lib/intakeV6/intakeV6ArtworkOnlyGuard";
import { getPersistedFileHash } from "@/lib/intakeV6/intakeV6AnalysisIdentity";
import { useIntakeV6WorkspaceHeaderStatusOptional } from "@/components/workos/intake-v6/IntakeV6WorkspaceHeaderStatusContext";
import { useCompanyCommercialSettings } from "@/hooks/useCompanyCommercialSettings";
import { useModularFormContract } from "@/lib/intakeV6/useModularFormContract";
import { useModularFormAwareness } from "@/lib/intakeV6/useModularFormAwareness";
import { isAnalysisReadyForReview } from "@/lib/intakeV6/intakeV6AnalysisIdentity";
import { isProductCompositionConfirmed } from "@/lib/intakeV6/intakeV6Readiness";
import type { IntakeV6ConfirmSummaryViewModel } from "@/lib/intakeV6/intakeV6ConfirmSummary";
import {
	reconcileLocalConfirmationWithPersisted,
	resolveInternalDraftConfirmationHydration,
	restoreConfirmationAfterFailedPut,
	shouldApplyConfirmationSnapshot,
} from "@/lib/intakeV6/intakeV6InternalDraftConfirmationHydration";
import { readPersistedOfferScope } from "@/lib/intakeV6/intakeV6OfferScopeState";
import {
	describeOfferScopeSummary,
	resolveActiveOfferScopePreset,
	OFFER_SCOPE_PRESETS,
} from "@/lib/intakeV6/intakeV6OfferScopePresets";
import { resolveSoldScopeFieldVisibility } from "@/lib/intakeV6/intakeV6SoldScopeVisibility";

const EMPTY_REVIEW_WARNINGS: string[] = [];

export function useIntakeV6FinalHandoff(hook: IntakeV6WorkspaceHook) {
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
	const confirmationFetchGenRef = useRef(0);
	const savingInternalConfirmationRef = useRef(false);
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
		savingInternalConfirmationRef.current = savingInternalConfirmation;
	}, [savingInternalConfirmation]);

	useEffect(() => {
		if (!ws?.id) return;
		let cancelled = false;
		const fetchGeneration = ++confirmationFetchGenRef.current;
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
				if (fetchGeneration !== confirmationFetchGenRef.current) return;
				setBinding(bindingResponse);
				setMaterialBreakdown(breakdownResponse);
				setNestingPreview(nestingResponse);
				setPricingPreview(pricingResponse);
				setPricedQuoteDryRun(pricedQuoteDryRunResponse);
				setHandoffPreview(handoffResponse);
				if (
					shouldApplyConfirmationSnapshot({
						saving: savingInternalConfirmationRef.current,
						responseGeneration: fetchGeneration,
						latestGeneration: confirmationFetchGenRef.current,
					})
				) {
					setConfirmInternalDraft(handoffResponse.operator_confirmation_complete === true);
				}
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

	const confirmationHydration = useMemo(
		() =>
			resolveInternalDraftConfirmationHydration({
				hasFinishSetup: finishSetup != null,
				finishSetupConfirmed: finishSetup?.internal_draft_quote_confirmed,
				hasHandoffPreview: handoffPreview != null,
				handoffOperatorComplete: handoffPreview?.operator_confirmation_complete,
				previewLoading: confirmPreviewLoading,
				saving: savingInternalConfirmation,
			}),
		[
			finishSetup,
			finishSetup?.internal_draft_quote_confirmed,
			handoffPreview,
			handoffPreview?.operator_confirmation_complete,
			confirmPreviewLoading,
			savingInternalConfirmation,
		],
	);

	// Reconcile local checkbox with persisted truth after load/remount/upstream reset.
	useEffect(() => {
		if (!confirmationHydration.resolved) return;
		setConfirmInternalDraft((local) =>
			reconcileLocalConfirmationWithPersisted({
				saving: savingInternalConfirmation,
				localConfirmed: local,
				persistedConfirmed: confirmationHydration.confirmed,
				hydrationResolved: confirmationHydration.resolved,
			}),
		);
	}, [
		confirmationHydration.resolved,
		confirmationHydration.confirmed,
		savingInternalConfirmation,
		ws?.updated_at,
	]);

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
		(): IntakeV6ConfirmSummaryViewModel =>
			buildIntakeV6ConfirmSummary({
				payload: payload as Record<string, unknown> | undefined,
				layerCount,
				materialBreakdown,
				nestingPreview,
				handoffBlockers: handoffPreview?.blockers,
				analyzerReport: state.analyzerReport,
			}),
		[
			payload,
			layerCount,
			materialBreakdown,
			nestingPreview,
			handoffPreview?.blockers,
			state.analyzerReport,
		],
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
	// Prefer hydrated persisted truth so finish_setup confirmation is visible before handoff preview lands.
	// While saving, keep optimistic local checked state (handoff may still be pre-PUT until refresh).
	const operatorConfirmationComplete = savingInternalConfirmation
		? confirmInternalDraft
		: confirmationHydration.resolved
			? confirmationHydration.confirmed
			: false;
	const confirmationHydrationPending = !confirmationHydration.resolved;
	const quoteGeometry = payload?.quote_geometry as
		| { width_mm?: number; height_mm?: number; letter_perimeter_m?: number }
		| undefined;

	const canShowHandoffSection = isReadyForQuotePreview || !finishSetupIncomplete;
	const canResolveInternalDraftConfirmation =
		canShowHandoffSection &&
		bindingBlockers.length === 0 &&
		!finishSetupIncomplete &&
		confirmationHydration.resolved &&
		!confirmationHydration.disableInteraction;
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
		if (!ws?.id || finishSetupIncomplete || confirmationHydrationPending) return;
		const previousPersisted = restoreConfirmationAfterFailedPut({
			hasHandoffPreview: handoffPreview != null,
			handoffOperatorComplete: handoffPreview?.operator_confirmation_complete,
			hasFinishSetup: finishSetup != null,
			finishSetupConfirmed: finishSetup?.internal_draft_quote_confirmed,
		});
		setConfirmInternalDraft(checked);
		setSavingInternalConfirmation(true);
		savingInternalConfirmationRef.current = true;
		setError(null);
		try {
			if (checked) {
				// ConfirmJobProductTruth — pin typed bags + revision before commercial freeze.
				const status = await getJobProductTruthStatus(ws.id);
				const expectedRevision = status.has_job_revision
					? Number(status.metadata?.revision ?? 0)
					: 0;
				await confirmJobProductTruth(ws.id, {
					expected_revision: expectedRevision,
					expected_draft_hash: status.draft_hash,
					root_template_code: ws.template_code ?? undefined,
				});
			}
			await saveIntakeV6InternalDraftQuoteConfirmation(ws.id, { confirmed: checked });
			const refreshed = await getIntakeV6QuoteHandoffPreview(ws.id, clientAnalysisHash ?? undefined);
			setHandoffPreview(refreshed);
			setConfirmInternalDraft(refreshed.operator_confirmation_complete === true);
		} catch (err) {
			const detail =
				err && typeof err === "object" && "detail" in err
					? JSON.stringify((err as { detail: unknown }).detail)
					: null;
			setError(
				err instanceof Error
					? `${err.message}${detail ? ` — ${detail}` : ""}`
					: "Salvare confirmare draft intern esuata.",
			);
			setConfirmInternalDraft(previousPersisted);
		} finally {
			savingInternalConfirmationRef.current = false;
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
				allArtworkProductConfigured: !artworkNeedsDecision,
				currentStep: "confirm",
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
			effectiveHandoffAllowed,
			operatorConfirmationComplete,
			confirmInternalDraft,
			confirmDraftBoundary,
			showHandoffCheckboxes,
			isReadyForQuotePreview,
			firstBlocker,
		],
	);

	const compositionConfirmed = isProductCompositionConfirmed(
		payload as Record<string, unknown> | undefined,
	);

	const checklistProgress = useMemo(
		() =>
			resolveConfirmChecklistProgress({
				compositionConfirmed,
				finishSetupComplete: !finishSetupIncomplete,
				operatorConfirmationComplete,
				confirmInternalDraft,
				draftBoundaryAcknowledged: confirmDraftBoundary,
				showDraftBoundaryItem: showHandoffCheckboxes,
			}),
		[
			compositionConfirmed,
			finishSetupIncomplete,
			operatorConfirmationComplete,
			confirmInternalDraft,
			confirmDraftBoundary,
			showHandoffCheckboxes,
		],
	);

	const soldScopeVisibility = useMemo(
		() => resolveSoldScopeFieldVisibility(payload as Record<string, unknown> | undefined),
		[payload],
	);

	const modularPendingCount = useMemo(() => {
		const view = modularAwareness.preview?.operatorView;
		if (!view) return 0;
		const lines = [...view.productReady, ...view.mounting];
		return lines.filter((line) => {
			if (line.state !== "pending") return false;
			if (soldScopeVisibility.mode === "full_product") return true;
			if (line.key === "debitare_fata") return soldScopeVisibility.face;
			if (line.key === "modelare_cant") return soldScopeVisibility.returnCant;
			if (line.key === "debitare_spate") return soldScopeVisibility.back;
			if (line.key === "sistem_led") return soldScopeVisibility.lighting || soldScopeVisibility.electrical;
			if (line.key === "finisaje") {
				return soldScopeVisibility.face || soldScopeVisibility.returnCant;
			}
			// Mounting / packaging responsibilities stay silent on Slice-1 subsets.
			return false;
		}).length;
	}, [modularAwareness.preview, soldScopeVisibility]);

	const consolidatedStatus = useMemo(
		(): IntakeV6ConfirmConsolidatedStatusDisplay =>
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

	const missingDecisionCount =
		modularPendingCount +
		(artworkNeedsDecision ? 1 : 0) +
		(!operatorConfirmationComplete ? 1 : 0);

	const offerScopeSummary = useMemo(() => {
		const persisted = readPersistedOfferScope(payload as Record<string, unknown> | undefined);
		return describeOfferScopeSummary(persisted.mode, persisted.soldModules);
	}, [payload]);

	const compactStatusHint = useMemo(() => {
		const persisted = readPersistedOfferScope(payload as Record<string, unknown> | undefined);
		const presetId = resolveActiveOfferScopePreset(persisted.mode, persisted.soldModules);
		const presetLabel =
			OFFER_SCOPE_PRESETS.find((preset) => preset.id === presetId)?.labelRo ??
			offerScopeSummary.requestModeLabelRo;
		const scopeLabel =
			persisted.mode === "full_product"
				? `Configurație: ${presetLabel}`
				: `Configurație: ${presetLabel}`;
		const activeCount = offerScopeSummary.activeLabelsRo.length;
		const componentLabel =
			persisted.mode === "full_product"
				? `${binding?.component_count ?? layerCount} componente`
				: `${activeCount} componente active`;
		const decisionsLabel =
			missingDecisionCount === 0
				? "fără decizii lipsă"
				: `${missingDecisionCount} decizii lipsă`;
		return `${scopeLabel} · ${componentLabel} · ${decisionsLabel}`;
	}, [
		payload,
		offerScopeSummary,
		binding?.component_count,
		layerCount,
		missingDecisionCount,
	]);

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
					.querySelector('[data-testid="intake-v6-final-configuration-summary"]')
					?.scrollIntoView({ behavior: "smooth", block: "start" });
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
			submitLabel: "Continuă către ofertă",
			submittingLabel: "Continuă…",
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

	return {
		state,
		ws,
		trySetStep,
		binding,
		materialBreakdown,
		nestingPreview,
		pricingPreview,
		pricedQuoteDryRun,
		handoffPreview,
		confirmPreviewLoading,
		confirmPreviewError,
		confirmDraftBoundary,
		setConfirmDraftBoundary,
		confirmInternalDraft,
		savingInternalConfirmation,
		submitting,
		submittingPricedQuote,
		error,
		result,
		pricedQuoteResult,
		commercialInputs,
		handleCommercialInputsChange,
		eurToRonRate,
		layerCount,
		summary,
		handoffUi,
		allFatalBlockers,
		reviewWarnings,
		finishSetupIncomplete,
		compositionConfirmed,
		operatorConfirmationComplete,
		confirmationHydrationPending,
		quoteGeometry,
		canShowHandoffSection,
		canResolveInternalDraftConfirmation,
		showHandoffCheckboxes,
		canCreatePricedQuote,
		createPricedQuoteDisabledReason,
		pricedQuoteDryRunTotal,
		pricedQuoteDryRunReady,
		consolidatedStatus,
		compactStatusHint,
		modularAwareness,
		modularFormContractHook,
		templateCode,
		fallbackBlockerMessage,
		handleInternalDraftConfirmation,
		handleCreatePricedQuote,
		navigate,
	};
}

export type IntakeV6FinalHandoffHook = ReturnType<typeof useIntakeV6FinalHandoff>;
