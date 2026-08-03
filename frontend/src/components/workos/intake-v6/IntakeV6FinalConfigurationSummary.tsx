import { useMemo } from "react";
import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import { useIntakeV6FinalHandoff } from "@/lib/intakeV6/useIntakeV6FinalHandoff";
import { formatWorkspaceReadinessLabel } from "@/lib/intakeV6/intakeV6OperatorUiDisplay";
import { isAcmPanelOnlyComposition } from "@/lib/intakeV6/acmPanel/acmPanelOnlyComposition";
import type {
	OfferProductRow,
	OfferTotalState,
} from "@/lib/intakeV6/intakeV6OfferProductSummary";
import {
	OFFER_TOTAL_AVAILABLE_LABEL,
	OFFER_TOTAL_GENERIC_UNAVAILABLE_MESSAGE,
	OFFER_TOTAL_PARTIAL_LABEL,
	OFFER_TOTAL_PARTIAL_MESSAGE,
	OFFER_TOTAL_UNAVAILABLE_LABEL,
	buildOfferProductSummary,
	formatOfferMoney,
	offerSubtotalLabel,
	offerTaxNote,
} from "@/lib/intakeV6/intakeV6OfferProductSummary";
import { v6 } from "./atoms/intakeV6Presentation";
import IntakeV6ConfirmDashboard from "./IntakeV6ConfirmDashboard";
import IntakeV6ConfirmHandoffPanel from "./IntakeV6ConfirmHandoffPanel";
import IntakeV6ConfirmOperationalSummary from "./IntakeV6ConfirmOperationalSummary";
import IntakeV6ModularFormAwarenessPanel from "./IntakeV6ModularFormAwarenessPanel";
import IntakeV6LiveCalculationSummary from "./IntakeV6LiveCalculationSummary";
import IntakeV6OfferScopeReviewSummary from "./IntakeV6OfferScopeReviewSummary";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";

export interface IntakeV6FinalConfigurationSummaryProps {
	hook: IntakeV6WorkspaceHook;
	defaultExpanded?: boolean;
	variant?: "embedded" | "legacyPage";
}

function ConsolidatedBlockersList({
	headline,
	observations,
	tier,
}: {
	headline: string;
	observations: string[];
	tier: string;
}) {
	if (observations.length === 0 && !headline) return null;
	const blocked = tier === "blocked" || tier === "blocker";
	return (
		<div
			className={
				blocked
					? "rounded-md border border-rose-500/30 bg-rose-950/30 px-3 py-2.5"
					: "rounded-md border border-wo-border-strong/70 bg-wo-surface-raised/40 px-3 py-2.5"
			}
			data-testid="intake-v6-final-config-status"
			data-status-tier={tier}
		>
			<p
				className={`text-[13px] font-semibold leading-snug ${blocked ? "text-rose-100" : "text-slate-200"}`}
				data-testid="intake-v6-final-config-headline"
			>
				{headline}
			</p>
			{observations.length > 0 ? (
				<ul className="mt-2 space-y-1" data-testid="intake-v6-confirm-consolidated-observations">
					{observations.map((observation) => (
						<li key={observation} className="text-[12px] leading-relaxed text-slate-300">
							{observation}
						</li>
					))}
				</ul>
			) : null}
		</div>
	);
}

interface OfferCardModel {
	products: OfferProductRow[];
	total: OfferTotalState;
	taxNote: string;
	net: { amount: number; currency: string } | null;
	vat: { amount: number; currency: string; ratePercent: number } | null;
	adaosPercent: number | null;
}

function normalizeReportedCurrency(raw: unknown): string | null {
	if (typeof raw !== "string") return null;
	const value = raw.trim().toUpperCase();
	return value.length > 0 ? value : null;
}

function OfferProductBreakdownList({ products }: { products: OfferProductRow[] }) {
	if (products.length === 0) return null;
	return (
		<ul className="mb-2 space-y-1.5" data-testid="intake-v6-offer-product-breakdown">
			{products.map((product) => (
				<li
					key={product.productKey}
					className="rounded border border-wo-border-strong/60 bg-wo-surface-input/40 px-2.5 py-2"
					data-testid={`intake-v6-offer-product-row-${product.productKey}`}
					data-blocked={product.blocked ? "true" : "false"}
				>
					<div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
						<span className="text-[12px] font-medium text-wo-text-secondary">{product.label}</span>
						<span className="text-[11px] text-wo-text-muted">
							{offerSubtotalLabel(product.productKey, product.label)}
						</span>
					</div>
					{product.amounts.length > 0 ? (
						<ul className="mt-1 space-y-0.5">
							{product.amounts.map((amount) => (
								<li
									key={`${product.productKey}-${amount.currency}`}
									className="flex items-baseline justify-between gap-2 text-[12px]"
								>
									<span className="text-wo-text-dim">{amount.currency}</span>
									<span className="tabular-nums text-wo-text-primary">
										{formatOfferMoney(amount.subtotal, amount.currency)}
									</span>
								</li>
							))}
						</ul>
					) : (
						<p className="mt-1 text-[11px] text-wo-text-muted">Subtotal indisponibil</p>
					)}
					{product.blocked ? (
						<p className="mt-1 text-[11px] leading-relaxed text-rose-200">
							Blocat comercial
							{product.blockerCodes.length > 0 ? `: ${product.blockerCodes.join(", ")}` : ""}
						</p>
					) : null}
				</li>
			))}
		</ul>
	);
}

function OfferTotalBlock({ total }: { total: OfferTotalState }) {
	if (total.kind === "available") {
		return (
			<div data-testid="intake-v6-offer-total-block" data-partial={total.partial ? "true" : "false"}>
				<div className="flex flex-wrap items-baseline justify-between gap-2">
					<span className="text-[12px] font-semibold text-wo-text-secondary">
						{total.partial ? OFFER_TOTAL_PARTIAL_LABEL : OFFER_TOTAL_AVAILABLE_LABEL}
					</span>
					<span
						className={`text-[20px] font-bold tabular-nums ${total.partial ? "text-amber-200" : "text-emerald-200"}`}
						data-testid="intake-v6-offer-total"
					>
						{formatOfferMoney(total.amount, total.currency)}
					</span>
				</div>
				{total.partial ? (
					<p
						className="mt-1 text-[11px] leading-relaxed text-amber-100/85"
						data-testid="intake-v6-offer-total-partial-note"
					>
						{OFFER_TOTAL_PARTIAL_MESSAGE}
						{total.pendingLineCodes.length > 0 ? ` (${total.pendingLineCodes.join(", ")})` : ""}
					</p>
				) : null}
			</div>
		);
	}
	return (
		<div
			className="rounded-md border border-amber-500/30 bg-amber-500/5 px-2.5 py-2"
			data-testid="intake-v6-offer-total-unavailable"
			data-reason-code={total.reasonCode ?? ""}
		>
			<p className="text-[12px] font-semibold text-amber-100">{OFFER_TOTAL_UNAVAILABLE_LABEL}</p>
			<p className="mt-1 text-[11px] leading-relaxed text-amber-100/85">{total.message}</p>
		</div>
	);
}

export default function IntakeV6FinalConfigurationSummary({
	hook,
	defaultExpanded = true,
	variant = "embedded",
}: IntakeV6FinalConfigurationSummaryProps) {
	const handoff = useIntakeV6FinalHandoff(hook);
	const acmPanelOnly = useMemo(
		() =>
			isAcmPanelOnlyComposition(
				handoff.ws?.payload as Record<string, unknown> | null | undefined,
			),
		[handoff.ws?.payload],
	);

	const offerCard = useMemo<OfferCardModel | null>(() => {
		const dryRun = handoff.pricedQuoteDryRun;
		if (!dryRun) return null;
		const breakdown = dryRun.commercial_product_breakdown ?? null;
		const summary = buildOfferProductSummary(breakdown);
		const totals = dryRun.commercial_totals ?? null;
		const reportedCurrency = normalizeReportedCurrency(totals?.currency);
		// Canonical breakdown owns VAT truth; legacy responses fall back to dry-run totals.
		const vatRatePercent =
			summary != null
				? summary.vatRatePercent
				: typeof totals?.vat_rate === "number" && Number.isFinite(totals.vat_rate)
					? totals.vat_rate
					: null;
		const netAmount = totals?.subtotal_net;
		const vatAmount = totals?.vat_amount;
		const grossAmount = handoff.pricedQuoteDryRunTotal;
		const fallbackTotal: OfferTotalState =
			reportedCurrency != null && grossAmount != null && Number.isFinite(grossAmount)
				? {
						kind: "available",
						amount: grossAmount,
						currency: reportedCurrency,
						partial: false,
						pendingLineCodes: [],
					}
				: {
						kind: "unavailable",
						reasonCode: null,
						message: OFFER_TOTAL_GENERIC_UNAVAILABLE_MESSAGE,
					};
		return {
			products: summary?.products ?? [],
			total: summary?.total ?? fallbackTotal,
			taxNote: summary != null ? summary.taxNote : offerTaxNote(vatRatePercent),
			net:
				reportedCurrency != null && typeof netAmount === "number" && Number.isFinite(netAmount)
					? { amount: netAmount, currency: reportedCurrency }
					: null,
			vat:
				reportedCurrency != null &&
				typeof vatAmount === "number" &&
				Number.isFinite(vatAmount) &&
				vatRatePercent != null
					? { amount: vatAmount, currency: reportedCurrency, ratePercent: vatRatePercent }
					: null,
			adaosPercent:
				typeof totals?.commercial_adjustment_trace?.markup_percent === "number"
					? totals.commercial_adjustment_trace.markup_percent
					: null,
		};
	}, [handoff.pricedQuoteDryRun, handoff.pricedQuoteDryRunTotal]);

	// Confirmare first paint always exposes the checklist / handoff purpose.
	const showHandoffPanel =
		variant === "legacyPage" ||
		handoff.canShowHandoffSection ||
		handoff.finishSetupIncomplete ||
		handoff.allFatalBlockers.length > 0;

	return (
		<section
			data-testid={variant === "legacyPage" ? "intake-v6-step-confirm" : "intake-v6-final-configuration-summary-root"}
			className={variant === "embedded" ? "mt-4" : undefined}
		>
			{variant === "legacyPage" ? (
				<div className="mb-3">
					<h2 className={v6.screenTitle}>Confirmare finală</h2>
					<p className={v6.sectionDesc}>
						Verifică starea, checklist-ul și confirmă pentru continuare.
					</p>
				</div>
			) : null}

			<div className="mb-3">
				<IntakeV6OfferScopeReviewSummary
					payload={handoff.ws?.payload as Record<string, unknown> | null | undefined}
				/>
			</div>

			{/* D7: status + checklist on first paint — not behind technical disclosure */}
			<div className="mb-3 space-y-3" data-testid="intake-v6-confirm-first-paint">
				{handoff.confirmPreviewError ? (
					<p className="text-[12px] text-rose-300" data-testid="intake-v6-confirm-preview-error">
						{handoff.confirmPreviewError}
					</p>
				) : null}

				{/* One readiness summary — checklist owns the action; do not re-list every observation. */}
				<ConsolidatedBlockersList
					headline={handoff.consolidatedStatus.headline}
					observations={
						showHandoffPanel
							? handoff.consolidatedStatus.observations.slice(0, 1)
							: handoff.consolidatedStatus.observations
					}
					tier={handoff.consolidatedStatus.tier}
				/>

				{showHandoffPanel ? (
					<IntakeV6ConfirmHandoffPanel
						compositionConfirmed={handoff.compositionConfirmed}
						finishSetupIncomplete={handoff.finishSetupIncomplete}
						operatorConfirmationComplete={handoff.operatorConfirmationComplete}
						confirmInternalDraft={handoff.confirmInternalDraft}
						confirmDraftBoundary={handoff.confirmDraftBoundary}
						showHandoffCheckboxes={handoff.showHandoffCheckboxes}
						canResolveInternalDraftConfirmation={handoff.canResolveInternalDraftConfirmation}
						savingInternalConfirmation={handoff.savingInternalConfirmation}
						confirmationHydrationPending={handoff.confirmationHydrationPending}
						confirmationLoadError={handoff.confirmPreviewError}
						allFatalBlockers={handoff.allFatalBlockers}
						showBlockerList={handoff.allFatalBlockers.length > 0}
						resultMessage={
							handoff.pricedQuoteResult
								? `Oferta pretuita a fost creata: ${handoff.pricedQuoteResult.quote_code}. Totalurile comerciale V6 au fost scrise pe oferta. Nu a fost creata comanda.`
								: handoff.result ? `Draft ${handoff.result.quote_code} creat. Rămâi în V6.` : null
						}
						errorMessage={handoff.error}
						fallbackBlockerMessage={handoff.fallbackBlockerMessage}
						onInternalDraftChange={(checked) => void handoff.handleInternalDraftConfirmation(checked)}
						onDraftBoundaryChange={handoff.setConfirmDraftBoundary}
					/>
				) : null}

				{offerCard != null && (handoff.pricedQuoteDryRunTotal != null || offerCard.products.length > 0) ? (
					<div className={`${v6.cardCompact} !p-3`} data-testid="intake-v6-priced-quote-cta-card">
						<div className="mb-2">
							<div className="mb-2">
								<h3 className={v6.sectionTitle}>Ofertă client</h3>
								<p className="mt-1 text-[11px] text-slate-400">
									Subtotaluri pe produs și total comercial din backend — fără comandă sau stoc.
								</p>
							</div>

							<OfferProductBreakdownList products={offerCard.products} />

							<div className="mb-2">
								<OfferTotalBlock total={offerCard.total} />
							</div>

							<p className="mb-2 text-[11px] text-slate-400" data-testid="intake-v6-offer-tax-note">
								{offerCard.taxNote}
							</p>

							{offerCard.net || offerCard.vat || offerCard.adaosPercent != null ? (
								<dl
									className="grid grid-cols-2 gap-x-3 gap-y-1 rounded border border-wo-border-strong/60 bg-wo-surface-input/50 px-2.5 py-2 text-[11px]"
									data-testid="intake-v6-confirm-offer-totals-breakdown"
								>
									{offerCard.net ? (
										<div className="flex justify-between gap-2 text-slate-400">
											<dt>Net</dt>
											<dd className="tabular-nums text-slate-200">
												{formatOfferMoney(offerCard.net.amount, offerCard.net.currency)}
											</dd>
										</div>
									) : null}
									{offerCard.vat ? (
										<div className="flex justify-between gap-2 text-slate-400">
											<dt>
												{`TVA (${offerCard.vat.ratePercent.toLocaleString("ro-RO", {
													maximumFractionDigits: 2,
												})}%)`}
											</dt>
											<dd className="tabular-nums text-slate-200">
												{formatOfferMoney(offerCard.vat.amount, offerCard.vat.currency)}
											</dd>
										</div>
									) : null}
									{offerCard.adaosPercent != null ? (
										<div className="col-span-2 flex justify-between gap-2 text-slate-400">
											<dt>Adaos comercial</dt>
											<dd className="tabular-nums text-slate-200">
												{offerCard.adaosPercent.toLocaleString("ro-RO", { maximumFractionDigits: 2 })}%
											</dd>
										</div>
									) : null}
								</dl>
							) : null}
						</div>
						{handoff.createPricedQuoteDisabledReason &&
						!handoff.canCreatePricedQuote &&
						!/finisaj|draft intern|confirm/i.test(handoff.createPricedQuoteDisabledReason) ? (
							<p className="mb-2 text-[11px] text-slate-400" data-testid="intake-v6-priced-quote-disabled-reason">
								{handoff.createPricedQuoteDisabledReason}
							</p>
						) : null}
						<div className="flex flex-wrap items-center gap-2">
							<button
								type="button"
								className={v6.btnPrimary}
								disabled={!handoff.canCreatePricedQuote}
								data-testid="intake-v6-create-priced-quote"
								onClick={() => void handoff.handleCreatePricedQuote()}
							>
								{handoff.submittingPricedQuote ? "Creez oferta pretuita…" : "Creeaza oferta pretuita"}
							</button>
							{handoff.pricedQuoteResult?.next_route ? (
								<button
									type="button"
									className={v6.btnGhost}
									data-testid="intake-v6-priced-quote-open"
									onClick={() => handoff.navigate(handoff.pricedQuoteResult!.next_route as string)}
								>
									Deschide oferta
								</button>
							) : null}
						</div>
					</div>
				) : (
					<IntakeV6LiveCalculationSummary
						breakdown={handoff.materialBreakdown}
						faceBackDraft={null}
						loading={handoff.confirmPreviewLoading}
						layout="bar"
						pricingPreview={handoff.pricingPreview}
						officialPricing={handoff.pricedQuoteDryRun}
						commercialInputs={handoff.commercialInputs}
						eurToRonRate={handoff.eurToRonRate}
						suppressLetterCantChrome={acmPanelOnly}
						hideAcmPanelProvisional
					/>
				)}
			</div>

			<IntakeV6TechnicalDetailsAccordion
				title="Recapitulare și diagnostic tehnic"
				hint={handoff.compactStatusHint}
				defaultOpen={false}
				testId="intake-v6-final-configuration-summary"
				className="mb-4"
			>
				<div className="space-y-3" data-testid="intake-v6-confirm-dashboard">
					<IntakeV6ConfirmDashboard
						workspaceCode={handoff.ws?.workspace_code}
						templateLabel={handoff.binding?.template_label ?? handoff.ws?.template_code}
						svgFileName={handoff.state.svg?.fileName}
						summary={handoff.summary}
						handoffPreview={handoff.handoffPreview}
						fatalBlockers={handoff.allFatalBlockers}
						reviewWarnings={handoff.reviewWarnings}
						nestingPreview={handoff.nestingPreview}
						loading={handoff.confirmPreviewLoading}
					/>

					<IntakeV6TechnicalDetailsAccordion
						title="Detalii tehnice"
						testId="intake-v6-final-configuration-technical-details"
						defaultOpen={defaultExpanded === true ? false : false}
					>
						<IntakeV6ModularFormAwarenessPanel
							loadStatus={handoff.modularAwareness.loadStatus}
							preview={handoff.modularAwareness.preview}
							triggerMismatchNote={handoff.modularAwareness.preview?.triggerMismatchNote}
							templateCode={handoff.templateCode || null}
							variant="confirm"
						/>

						<div className={`${v6.card} mb-3`} data-testid="intake-v6-readiness-status">
							<ul className="space-y-1 text-[11px] text-slate-400">
								<li data-testid="intake-v6-readiness-preview">
									Preview: {handoff.handoffUi.handoffAllowed ? "gata" : "blocat"}
								</li>
								{handoff.ws?.readiness_status ? (
									<li>Workspace: {formatWorkspaceReadinessLabel(handoff.ws.readiness_status)}</li>
								) : null}
								{handoff.binding ? (
									<li data-testid="intake-v6-product-binding">
										ProductSystem: {handoff.binding.operation_count} operații ·{" "}
										{handoff.binding.template_active ? "activ" : "inactiv"}
									</li>
								) : null}
							</ul>
						</div>

						<IntakeV6ConfirmOperationalSummary
							summary={handoff.summary}
							variant="technical"
							acmPanelOnly={acmPanelOnly}
						/>
					</IntakeV6TechnicalDetailsAccordion>
				</div>
			</IntakeV6TechnicalDetailsAccordion>
		</section>
	);
}
