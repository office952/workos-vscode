import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import { useIntakeV6FinalHandoff } from "@/lib/intakeV6/useIntakeV6FinalHandoff";
import { formatWorkspaceReadinessLabel } from "@/lib/intakeV6/intakeV6OperatorUiDisplay";
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
					: "rounded-md border border-[#243044]/70 bg-[#101827]/40 px-3 py-2.5"
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

export default function IntakeV6FinalConfigurationSummary({
	hook,
	defaultExpanded = true,
	variant = "embedded",
}: IntakeV6FinalConfigurationSummaryProps) {
	const handoff = useIntakeV6FinalHandoff(hook);

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

				{handoff.pricedQuoteDryRunTotal != null ? (
					<div className={`${v6.cardCompact} !p-3`} data-testid="intake-v6-priced-quote-cta-card">
						<div className="mb-2 flex flex-wrap items-start justify-between gap-2">
							<div>
								<h3 className={v6.sectionTitle}>Oferta pretuita</h3>
								<p className="mt-1 text-[11px] text-slate-400">
									Total comercial pe ofertă — fără comandă sau stoc.
								</p>
							</div>
							<span className="text-[12px] font-semibold text-slate-100" data-testid="intake-v6-priced-quote-total">
								{`${handoff.pricedQuoteDryRunTotal.toLocaleString("ro-RO", {
									minimumFractionDigits: 2,
									maximumFractionDigits: 2,
								})} ${handoff.pricedQuoteDryRun?.commercial_totals?.currency ?? "RON"}`}
							</span>
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

						<IntakeV6ConfirmOperationalSummary summary={handoff.summary} variant="technical" />
					</IntakeV6TechnicalDetailsAccordion>
				</div>
			</IntakeV6TechnicalDetailsAccordion>
		</section>
	);
}
