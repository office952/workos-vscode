import type { IntakeV6QuoteHandoffPreviewResponse } from "./intakeV6Api";
import type { IntakeV6OperatorStateBadge } from "./intakeV6OperatorStateBadges";

export type QuoteHandoffUiTone = "ok" | "pending" | "warn";

export type QuoteHandoffUiOptions = {
	loading?: boolean;
	fetchError?: string | null;
};

function formatHandoffUiOperatorLabel(code: string): string {
	switch (code) {
		case "HANDOFF_PREVIEW_UNAVAILABLE":
			return "Previzualizare handoff indisponibilă";
		case "LOADING_HANDOFF":
			return "Se încarcă previzualizarea handoff…";
		case "READY_FOR_INTERNAL_DRAFT_REVIEW":
			return "Draft intern: pregătit pentru review";
		case "HANDOFF_ALLOWED":
			return "Handoff permis (draft intern)";
		case "ACTION_NEEDED":
			return "Acțiune necesară înainte de handoff";
		case "QUOTE_HANDOFF_BLOCKED":
			return "Handoff către ofertă reală: blocat";
		case "WORKSPACE_READY":
			return "Pregătit pentru previzualizare ofertă";
		default:
			return code.replace(/_/g, " ");
	}
}

export function formatQuoteHandoffBlocker(code: string): string {
	if (code.startsWith("canonical_missing_required_field:")) {
		const field = code.split(":")[1] ?? "unknown";
		return `Lipsește câmpul canonic necesar pentru ofertare: ${field}.`;
	}
	if (code.startsWith("canonical_invalid_combination:")) {
		const detail = code.slice("canonical_invalid_combination:".length).trim();
		if (detail === "MOUNTING_SCOPE_INACTIVE") {
			return "Montajul comercial nu este activ — suportul de produs rămâne valid. Verifică doar opțiunile comerciale dacă oferta le include.";
		}
		return `Combinație invalidă în configurație: ${detail || "necunoscută"}.`;
	}
	if (code.startsWith("canonical_unresolved_warning:")) {
		const detail = code.slice("canonical_unresolved_warning:".length).trim();
		return `Avertizare canonică de aliniere: ${detail || "neprecizată"}.`;
	}
	if (code === "product_definition_preview_unavailable") {
		return "ProductDefinition preview nu a putut fi construit pentru acest workspace.";
	}
	if (code.startsWith("artwork_execution_undecided:")) {
		const layerKey = code.split(":")[1] ?? "vector-logo";
		return `Vector Logo — execuție nedecisă pe ${layerKey}.`;
	}
	if (code === "unclassified_vector_artwork_requires_decision") {
		return "Perimetru vector nealocat — verifică Vector Logo în Finisaje.";
	}
	if (code === "artwork_only_requires_decision") {
		return "Nu există straturi de litere volumetrice confirmate. Vector Logo/policromie necesită decizie operator. Template-ul curent este Litere volumetrice; fișierul încărcat pare doar Vector Logo.";
	}
	if (code === "operator_confirmation_missing") {
		return "Operatorul trebuie să confirme finisajele și datele de ofertare pentru draft intern.";
	}
	if (code === "missing_client_analysis_hash") {
		return "Analiza SVG nu este sincronizată complet cu workspace-ul. Salvează/confirmă din nou analiza sau reîncarcă fișierul.";
	}
	if (code === "analysis_hash_mismatch") {
		return "SVG analysis hash does not match persisted workspace identity.";
	}
	if (code === "missing_svg_source_hash") {
		return "Persisted SVG source hash is missing.";
	}
	if (code.startsWith("readiness_not_ready:")) {
		const readiness = code.split(":")[1] ?? "unknown";
		if (readiness === "layer_roles_incomplete") {
			return "Confirmă rolul pentru toate straturile înainte de ofertare.";
		}
		if (readiness === "product_composition_not_confirmed") {
			return "Confirmă compoziția produsului în Configurare.";
		}
		if (readiness === "finish_setup_incomplete") {
			return "Finalizează finisajele în Configurare înainte de draft.";
		}
		if (readiness === "offer_scope_not_confirmed") {
			return "Confirmă ce producem (produs complet sau componente selectate).";
		}
		return "Configurarea nu este gata pentru confirmare finală.";
	}
	if (code === "product_composition_not_confirmed") {
		return "Confirmă compoziția produsului în Configurare.";
	}
	if (code === "finish_setup_not_confirmed") {
		return "Finalizează și confirmă finisajele în Review înainte de draft quote.";
	}
	if (code === "layer_roles_incomplete") {
		return "Product Truth incomplet: rolurile layerelor/grupurilor trebuie confirmate de operator.";
	}
	if (code === "missing_svg_analysis") {
		return "SVG analysis bundle is missing.";
	}
	if (code === "missing_quote_geometry") {
		return "Quote geometry is missing.";
	}
	if (code === "QUOTE_NOT_PRICED") {
		return "Quote-ul nu are totaluri comerciale oficiale. Rulează dry-run V6 și scrie totalurile backend înainte de pricing review.";
	}
	if (code === "V6_PRICED_DRY_RUN_BLOCKED") {
		return "Dry-run V6 blocat: propunerea comercială backend nu este încă pregătită.";
	}
	if (code === "V6_PRICED_DRY_RUN_ZERO_TOTAL") {
		return "Dry-run V6 a returnat total zero — nu poate deveni ofertă oficială.";
	}
	if (code === "V6_PRICED_DRY_RUN_COMMERCIAL_REVIEW_NOT_READY") {
		return "Propunerea comercială backend nu este în status ready.";
	}
	if (code === "V6_PRICED_QUOTE_WRITE_DRY_RUN_BLOCKED") {
		return "Scrierea totalurilor V6 este blocată: dry-run backend nu este READY.";
	}
	if (code === "V6_PRICED_QUOTE_WRITE_ZERO_TOTAL") {
		return "Totalurile dry-run lipsesc sau sunt zero — nu pot fi scrise pe quote.";
	}
	if (code === "V6_PRICED_QUOTE_WRITE_ALREADY_PRICED") {
		return "Quote-ul are deja totaluri comerciale pozitive.";
	}
	if (code === "V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH") {
		return "Totalul așteptat nu corespunde recomputării serverului V6.";
	}
	if (code === "V6_SNAPSHOT_QUOTE_NOT_PRICED") {
		return "Quote Snapshot V2 necesită quote prețuit oficial prin bridge-ul V6.";
	}
	if (code === "V6_PRICED_QUOTE_WRITE_OPERATOR_CONFIRMATION_REQUIRED") {
		return "Confirmarea operatorului este necesară înainte de scrierea totalurilor V6.";
	}
	if (code.startsWith("COMMERCIAL_BASIS_UNKNOWN")) {
		return "Baza comercială necunoscută pentru un modul — decizie owner necesară.";
	}
	if (code.startsWith("DEBITARE_SPATE_BASIS_ML_VS_M2")) {
		return "Decizie owner: baza comercială debitare spate ml vs m².";
	}
	if (code.startsWith("SABLON_FOREX_COMMERCIAL_PRICE")) {
		return "Preț comercial Forex sablon necesită aprobare owner.";
	}
	if (code.startsWith("AMBALARE_COMMERCIAL_RULE")) {
		return "Regula comercială ambalare nu este definită de owner (deferred — nonblocking).";
	}
	if (code.startsWith("MONTAJ_COMMERCIAL_RULE")) {
		return "Lipsește tariful comercial pentru montaj șantier (obligatoriu când instalarea este inclusă).";
	}
	if (code === "LOGO_PRINT_COMMERCIAL_RULE") {
		return "Lipsește tariful comercial pentru print logo volumetric (fail-closed până la configurare owner).";
	}
	if (code === "LOGO_LAMINATE_COMMERCIAL_RULE") {
		return "Lipsește tariful comercial pentru laminare logo volumetric (fail-closed până la configurare owner).";
	}
	if (code === "LOGO_APPLICATION_COMMERCIAL_RULE") {
		return "Lipsește tariful comercial pentru aplicare folie logo (fail-closed până la configurare owner).";
	}
	if (code === "V6_PRICED_DRY_RUN_COMMERCIAL_REVIEW_NOT_READY") {
		return "CommercialPriceProposal este parțial — completează tarifele comerciale lipsă înainte de Confirmare.";
	}
	if (code === "PRICING_REVIEW_INCOMPLETE" || code === "PRICING_REVIEW_REQUIRED") {
		return "Review preț necesar înainte de aprobare owner sau conversie.";
	}
	if (code === "OWNER_APPROVAL_MISSING" || code === "OWNER_APPROVAL_REQUIRED") {
		return "Aprobare owner necesară pentru quote-ul V6.";
	}
	if (code === "QUOTE_NOT_ACCEPTED") {
		return "Quote-ul trebuie acceptat înainte de conversia în order.";
	}
	if (code.startsWith("missing_face_oracal_color:")) {
		return "Lipsește culoarea Oracal pentru față.";
	}
	if (code.startsWith("missing_ral_color:")) {
		return "Lipsește culoarea RAL.";
	}
	return code.replace(/_/g, " ");
}

export function hasFinishSetupIncompleteBlocker(
	fatalBlockers: string[] | null | undefined,
	readinessStatus?: string | null,
): boolean {
	const blockers = fatalBlockers ?? [];
	return (
		readinessStatus === "finish_setup_incomplete" ||
		blockers.includes("finish_setup_not_confirmed") ||
		blockers.some((code) => code === "readiness_not_ready:finish_setup_incomplete")
	);
}

export function hasArtworkNeedsDecisionWarning(
	reviewWarnings: string[] | null | undefined,
): boolean {
	return (reviewWarnings ?? []).some(
		(code) =>
			code.startsWith("artwork_execution_undecided:") ||
			code === "unclassified_vector_artwork_requires_decision" ||
			code === "artwork_only_requires_decision",
	);
}

export function hasUnclassifiedVectorArtworkWarning(
	reviewWarnings: string[] | null | undefined,
): boolean {
	return (reviewWarnings ?? []).includes("unclassified_vector_artwork_requires_decision");
}

export function hasUnconfirmedArtworkFinishes(
	rows: Array<{ confirmed?: boolean }> | null | undefined,
): boolean {
	return (rows ?? []).some((row) => row.confirmed !== true);
}

export function resolveQuoteHandoffUiStatus(
	handoff: IntakeV6QuoteHandoffPreviewResponse | null | undefined,
	options?: QuoteHandoffUiOptions,
): { label: string; tone: QuoteHandoffUiTone; handoffAllowed: boolean; debugLabel: string } {
	if (options?.fetchError) {
		return {
			label: formatHandoffUiOperatorLabel("HANDOFF_PREVIEW_UNAVAILABLE"),
			debugLabel: "HANDOFF_PREVIEW_UNAVAILABLE",
			tone: "warn",
			handoffAllowed: false,
		};
	}
	if (!handoff) {
		if (options?.loading) {
			return {
				label: formatHandoffUiOperatorLabel("LOADING_HANDOFF"),
				debugLabel: "LOADING_HANDOFF",
				tone: "pending",
				handoffAllowed: false,
			};
		}
		return {
			label: formatHandoffUiOperatorLabel("HANDOFF_PREVIEW_UNAVAILABLE"),
			debugLabel: "HANDOFF_PREVIEW_UNAVAILABLE",
			tone: "warn",
			handoffAllowed: false,
		};
	}

	const canCreate = handoff.can_create_internal_draft_quote ?? handoff.handoff_allowed;

	if (handoff.status_label === "READY_FOR_INTERNAL_DRAFT_REVIEW" && canCreate) {
		return {
			label: formatHandoffUiOperatorLabel("READY_FOR_INTERNAL_DRAFT_REVIEW"),
			debugLabel: "READY_FOR_INTERNAL_DRAFT_REVIEW",
			tone: "warn",
			handoffAllowed: true,
		};
	}
	if (canCreate) {
		return {
			label: formatHandoffUiOperatorLabel("HANDOFF_ALLOWED"),
			debugLabel: "HANDOFF_ALLOWED",
			tone: "ok",
			handoffAllowed: true,
		};
	}
	if (handoff.status_label === "ACTION_NEEDED") {
		return {
			label: formatHandoffUiOperatorLabel("ACTION_NEEDED"),
			debugLabel: "ACTION_NEEDED",
			tone: "warn",
			handoffAllowed: false,
		};
	}
	return {
		label: formatHandoffUiOperatorLabel("QUOTE_HANDOFF_BLOCKED"),
		debugLabel: "QUOTE_HANDOFF_BLOCKED",
		tone: "warn",
		handoffAllowed: false,
	};
}

export function resolveWorkspaceSummaryBadgeLabel(
	workspaceReadiness: string | null | undefined,
	handoff: IntakeV6QuoteHandoffPreviewResponse | null | undefined,
	options?: QuoteHandoffUiOptions,
): { label: string; tone: QuoteHandoffUiTone } {
	const handoffUi = resolveQuoteHandoffUiStatus(handoff, options);
	if (!handoffUi.handoffAllowed) {
		return { label: handoffUi.label, tone: handoffUi.tone };
	}
	if (handoff?.status_label === "READY_FOR_INTERNAL_DRAFT_REVIEW") {
		return {
			label: formatHandoffUiOperatorLabel("READY_FOR_INTERNAL_DRAFT_REVIEW"),
			tone: "warn",
		};
	}
	if (workspaceReadiness === "ready_for_quote_preview") {
		return { label: formatHandoffUiOperatorLabel("WORKSPACE_READY"), tone: "ok" };
	}
	return {
		label: formatWorkspaceReadinessLabel(workspaceReadiness),
		tone: "pending",
	};
}

function formatWorkspaceReadinessLabel(status: string | null | undefined): string {
	if (status === "ready_for_quote_preview") {
		return "Pregătit pentru previzualizare ofertă";
	}
	if (status === "finish_setup_incomplete") {
		return "Finisaje incomplete";
	}
	return status?.replace(/_/g, " ") ?? "—";
}

export function collectArtworkUndecidedWarnings(
	blockers: string[] | null | undefined,
): string[] {
	return (blockers ?? [])
		.filter(
			(code) =>
				code.startsWith("artwork_execution_undecided:") ||
				code === "unclassified_vector_artwork_requires_decision",
		)
		.map(formatQuoteHandoffBlocker);
}

export function collectFatalHandoffBlockers(handoff: IntakeV6QuoteHandoffPreviewResponse | null): string[] {
	if (!handoff) return [];
	if (handoff.fatal_blockers?.length) return handoff.fatal_blockers;
	return (handoff.blockers ?? []).filter(
		(code) =>
			!code.startsWith("artwork_execution_undecided:") &&
			code !== "unclassified_vector_artwork_requires_decision",
	);
}

export type ReviewHandoffSurfacing = {
	showBanner: boolean;
	reasons: string[];
	actions: string[];
	badges?: IntakeV6OperatorStateBadge[];
	/** Neutral next-step guidance (not a red/primary blocker). */
	nextStepGuidance?: string | null;
};

function isProductTruthBlocker(code: string): boolean {
	return (
		code === "layer_roles_incomplete" ||
		code === "readiness_not_ready:layer_roles_incomplete" ||
		code.startsWith("canonical_missing_required_field:") ||
		code.startsWith("canonical_invalid_combination:") ||
		code.startsWith("artwork_execution_undecided:") ||
		code === "artwork_only_requires_decision" ||
		code === "unclassified_vector_artwork_requires_decision" ||
		code === "finish_setup_not_confirmed"
	);
}

/** Fatals that remain actionable on the current operator step. */
export function filterStepScopedFatalBlockers(
	fatalBlockers: string[],
	currentStep: "layers" | "review" | "confirm" | undefined,
): string[] {
	const step = currentStep ?? "review";
	if (step === "confirm") return fatalBlockers;
	return fatalBlockers.filter((code) => code !== "operator_confirmation_missing");
}

export function isOnlyOperatorConfirmationBlocking(args: {
	handoffAllowed: boolean;
	fatalBlockers: string[];
}): boolean {
	if (args.handoffAllowed) return false;
	const hasOperator = args.fatalBlockers.includes("operator_confirmation_missing");
	if (!hasOperator) return false;
	return args.fatalBlockers.every((code) => code === "operator_confirmation_missing");
}

export function buildReviewHandoffSurfacing(args: {
	handoff: IntakeV6QuoteHandoffPreviewResponse | null | undefined;
	handoffOptions?: QuoteHandoffUiOptions;
	containsMissingPrices?: boolean;
	allArtworkFinishesConfirmed?: boolean;
	allArtworkProductConfigured?: boolean;
	/** When 0, residual Vector Logo chrome is noise (no logo rows to decide). */
	artworkFinishRowCount?: number;
	currentStep?: "layers" | "review" | "confirm";
}): ReviewHandoffSurfacing {
	const handoffUi = resolveQuoteHandoffUiStatus(args.handoff, args.handoffOptions);
	const reviewWarnings = args.handoff?.review_warnings ?? [];
	const fatalBlockers = args.handoff?.fatal_blockers ?? args.handoff?.blockers ?? [];
	const step = args.currentStep ?? "review";
	const artworkFinishRowCount = args.artworkFinishRowCount;
	const suppressArtworkVectorFatals = artworkFinishRowCount === 0;
	const stepScopedFatals = filterStepScopedFatalBlockers(fatalBlockers, step).filter((code) => {
		if (!suppressArtworkVectorFatals) return true;
		return !(
			code === "unclassified_vector_artwork_requires_decision" ||
			code.startsWith("artwork_execution_undecided:") ||
			code === "artwork_only_requires_decision"
		);
	});
	const reviewWarningsEffective = suppressArtworkVectorFatals
		? reviewWarnings.filter(
				(code) =>
					code !== "unclassified_vector_artwork_requires_decision" &&
					!code.startsWith("artwork_execution_undecided:") &&
					code !== "artwork_only_requires_decision",
			)
		: reviewWarnings;
	const artworkNeedsDecision = hasArtworkNeedsDecisionWarning(reviewWarningsEffective);
	const vectorResidualWarning = hasUnclassifiedVectorArtworkWarning(reviewWarningsEffective);
	const artworkConfigured =
		args.allArtworkProductConfigured ??
		(args.allArtworkFinishesConfirmed !== false && args.allArtworkFinishesConfirmed !== undefined
			? args.allArtworkFinishesConfirmed
			: true);
	const artworkUnconfigured = args.allArtworkProductConfigured === false;
	const surfaceResidualVector =
		vectorResidualWarning &&
		artworkConfigured &&
		!artworkUnconfigured &&
		(artworkFinishRowCount == null || artworkFinishRowCount > 0);
	const operatorConfirmationMissing = fatalBlockers.includes("operator_confirmation_missing");
	const onlyOperatorConfirmationPending = isOnlyOperatorConfirmationBlocking({
		handoffAllowed: handoffUi.handoffAllowed,
		fatalBlockers,
	});
	const showOperatorConfirmationOnStep = step === "confirm" && operatorConfirmationMissing;
	const containsMissingPrices = args.containsMissingPrices === true;
	const layerRolesBlocked = stepScopedFatals.some(
		(code) =>
			code === "layer_roles_incomplete" || code === "readiness_not_ready:layer_roles_incomplete",
	);
	const productTruthBlocked = stepScopedFatals.some(isProductTruthBlocker);
	// Suppress only the loading flash (null handoff + loading) — permanent fetch failure still banners.
	const suppressLoadingHandoffBanner =
		Boolean(args.handoffOptions?.loading) && !args.handoff;
	const handoffBlockedOnThisStep =
		!suppressLoadingHandoffBanner &&
		!handoffUi.handoffAllowed &&
		!(onlyOperatorConfirmationPending && step !== "confirm");

	const showBanner =
		handoffBlockedOnThisStep ||
		artworkUnconfigured ||
		surfaceResidualVector ||
		(artworkNeedsDecision && !vectorResidualWarning) ||
		containsMissingPrices ||
		showOperatorConfirmationOnStep;

	const nextStepGuidance =
		!showBanner && onlyOperatorConfirmationPending && step !== "confirm"
			? "Confirmarea finală se efectuează în Pasul 3."
			: null;

	// Paired reason/action — never prepend a generic Product Truth action onto an unrelated reason.
	const pairs: Array<{ reason: string; action: string }> = [];
	if (layerRolesBlocked) {
		pairs.push({
			reason:
				"Oferta rămâne blocată: rolurile layerelor/grupurilor trebuie confirmate de operator. Pricing Registry este pregătit; lipsește Product Truth confirmat.",
			action:
				"Confirmă rolurile layerelor/grupurilor și deciziile de componentă înainte de ofertă/preview/handoff.",
		});
	}
	if (artworkUnconfigured) {
		pairs.push({
			reason: "Vector Logo necesită decizie de execuție sau date obligatorii lipsă.",
			action: "Deschide Finisaje și completează execuția Vector Logo.",
		});
	} else if (surfaceResidualVector) {
		pairs.push({
			reason: "Perimetru vector nealocat — verifică Vector Logo în Finisaje.",
			action: "Deschide Finisaje și confirmă execuția Vector Logo (sau ignore).",
		});
	} else if (artworkNeedsDecision && !vectorResidualWarning) {
		pairs.push({
			reason: "Vector Logo neconfirmat sau fără decizie de execuție.",
			action: "Deschide Finisaje și rezolvă deciziile Vector Logo.",
		});
	}
	if (showOperatorConfirmationOnStep) {
		pairs.push({
			reason:
				"Confirmă finisajele și datele de ofertare pentru draft intern (checkbox-ul din Confirmare finală).",
			action: "Bifează checkbox-ul de confirmare draft intern din Confirmare finală.",
		});
	}
	if (containsMissingPrices) {
		pairs.push({
			reason: "Calculul live conține linii fără tarif configurat.",
			action: "Verifică liniile cu tarif lipsă în Calcul live.",
		});
	}
	if (handoffBlockedOnThisStep && pairs.length === 0) {
		pairs.push({
			reason: "Handoff-ul către ofertă reală este blocat.",
			action: productTruthBlocked
				? "Confirmă rolurile layerelor/grupurilor și deciziile de componentă înainte de ofertă/preview/handoff."
				: "Rezolvă blocajele din diagnosticul tehnic.",
		});
	}

	const reasons = pairs.map((pair) => pair.reason);
	const actions = pairs.map((pair) => pair.action);

	const badges: IntakeV6OperatorStateBadge[] = showBanner
		? layerRolesBlocked || artworkUnconfigured || showOperatorConfirmationOnStep
			? ["BLOCKED", "NEEDS_CONFIRMATION"]
			: containsMissingPrices
				? ["WARNING", "NEEDS_FORM_INPUT"]
				: ["WARNING"]
		: onlyOperatorConfirmationPending && step !== "confirm"
			? ["NEEDS_CONFIRMATION"]
			: ["READY"];

	return { showBanner, reasons, actions, badges, nextStepGuidance };
}

export function resolveReviewReadinessDisplay(
	workspaceReadiness: string | null | undefined,
	handoff: IntakeV6QuoteHandoffPreviewResponse | null | undefined,
	options?: QuoteHandoffUiOptions,
): { primary: string; secondary: string | null } {
	const handoffUi = resolveQuoteHandoffUiStatus(handoff, options);
	const workspaceReady = workspaceReadiness === "ready_for_quote_preview";
	const fatalBlockers = handoff?.fatal_blockers ?? handoff?.blockers ?? [];
	const onlyOperatorConfirmationPending = isOnlyOperatorConfirmationBlocking({
		handoffAllowed: handoffUi.handoffAllowed,
		fatalBlockers,
	});

	if (workspaceReady && onlyOperatorConfirmationPending) {
		return {
			primary: "Date tehnice pregătite pentru preview",
			secondary: "Confirmarea finală se efectuează în Pasul 3.",
		};
	}

	if (workspaceReady && !handoffUi.handoffAllowed) {
		return {
			primary: "Date tehnice pregătite pentru preview",
			secondary:
				"Handoff ofertă necesită Product Truth confirmat. Dacă blockerul este layer_roles_incomplete, confirmă rolurile layerelor/grupurilor; nu este o problemă de Pricing Registry.",
		};
	}

	if (workspaceReady && hasArtworkNeedsDecisionWarning(handoff?.review_warnings)) {
		return {
			primary: "Date tehnice pregătite pentru preview",
			secondary: "Există atenționări Vector Logo de rezolvat înainte de draft final.",
		};
	}

	return {
		primary: formatWorkspaceReadinessLabel(workspaceReadiness),
		secondary: null,
	};
}
