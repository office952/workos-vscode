import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  acceptIntakeV6Quote,
  completeIntakeV6PricingReview,
  convertIntakeV6QuoteToOrder,
  createIntakeV6QuoteSnapshotV2,
  getIntakeV6CommercialSpineState,
  getIntakeV6PricedQuoteDryRun,
  handoffIntakeV6ToOffer,
  persistIntakeV6OwnerApproval,
  writeIntakeV6PricedQuote,
  type IntakeV6CommercialSpineStateResponse,
  type IntakeV6PricedQuoteDryRunResponse,
} from "@/lib/intakeV6/intakeV6Api";
import { formatQuoteHandoffBlocker } from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";
import { v6 } from "./atoms/intakeV6Presentation";

type Props = {
  workspaceId: string;
  quoteId: number | null;
  clientAnalysisHash: string | null;
  intakeCode: string | null;
  onSpineUpdated?: () => void;
};

type WorkflowStep = {
  id: string;
  label: string;
  done: boolean;
  active: boolean;
};

type SpineActionId = "write" | "snapshot" | "pricing" | "approval" | "accept" | "convert";

function resolvePrimarySpineAction(args: {
  quoteTotalsAvailable: boolean;
  snapshotExists: boolean;
  pricingDone: boolean;
  ownerValid: boolean;
  accepted: boolean;
  converted: boolean;
  dryRunReady: boolean;
}): SpineActionId | null {
  if (args.converted) return null;
  if (args.accepted) return "convert";
  if (args.ownerValid) return "accept";
  if (args.pricingDone) return "approval";
  if (args.quoteTotalsAvailable && !args.snapshotExists) return "snapshot";
  if (args.quoteTotalsAvailable) return "pricing";
  if (args.dryRunReady) return "write";
  return null;
}

function readBlockedReasons(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

function readBlockerCodes(dryRun: IntakeV6PricedQuoteDryRunResponse | null): string[] {
  return (dryRun?.blockers ?? []).map((blocker) => blocker.code).filter(Boolean);
}

function formatMoney(value: number | null | undefined, currency = "RON"): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
}

function dryRunStatusLabel(status: string | undefined, loading: boolean): string {
  if (loading) return "Se calculează…";
  if (status === "V6_PRICED_DRY_RUN_READY") return "Pregătit de scriere";
  if (status === "V6_PRICED_DRY_RUN_BLOCKED") return "Blocat";
  return "Indisponibil";
}

function buildWorkflowSteps(args: {
  quoteTotalsAvailable: boolean;
  snapshotExists: boolean;
  pricingDone: boolean;
  ownerValid: boolean;
  accepted: boolean;
  converted: boolean;
  dryRunReady: boolean;
}): WorkflowStep[] {
  const priced = args.quoteTotalsAvailable;
  return [
    {
      id: "price",
      label: "Prețuire",
      done: priced,
      active: !priced && args.dryRunReady,
    },
    {
      id: "snapshot",
      label: "Snapshot V2",
      done: args.snapshotExists,
      active: priced && !args.snapshotExists,
    },
    {
      id: "review",
      label: "Review",
      done: args.pricingDone,
      active: args.snapshotExists && !args.pricingDone,
    },
    {
      id: "owner",
      label: "Aprobare",
      done: args.ownerValid,
      active: args.pricingDone && !args.ownerValid,
    },
    {
      id: "accept",
      label: "Accept",
      done: args.accepted,
      active: args.ownerValid && !args.accepted,
    },
    {
      id: "order",
      label: "Comandă",
      done: args.converted,
      active: args.accepted && !args.converted,
    },
  ];
}

function WorkflowStepper({ steps }: { steps: WorkflowStep[] }) {
  return (
    <ol
      className="mb-4 grid grid-cols-3 gap-2 sm:grid-cols-6"
      data-testid="intake-v6-workflow-steps"
    >
      {steps.map((step) => (
        <li
          key={step.id}
          className={`rounded border px-2 py-1.5 text-center text-[10px] ${
            step.done
              ? "border-emerald-700/40 bg-emerald-950/20 text-emerald-200"
              : step.active
                ? "border-amber-600/40 bg-amber-950/20 text-amber-100"
                : "border-[#1E293B] bg-[#0B1220] text-slate-500"
          }`}
          data-testid={`intake-v6-workflow-step-${step.id}`}
        >
          {step.label}
        </li>
      ))}
    </ol>
  );
}

export default function IntakeV6QuoteCommercialSpinePanel({
  workspaceId,
  quoteId,
  clientAnalysisHash,
  intakeCode,
  onSpineUpdated,
}: Props) {
  const navigate = useNavigate();
  const [state, setState] = useState<IntakeV6CommercialSpineStateResponse | null>(null);
  const [dryRun, setDryRun] = useState<IntakeV6PricedQuoteDryRunResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [dryRunLoading, setDryRunLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [showTechnical, setShowTechnical] = useState(false);
  const [showSecondaryActions, setShowSecondaryActions] = useState(false);

  const refreshDryRun = useCallback(async () => {
    if (!workspaceId) return;
    setDryRunLoading(true);
    try {
      const next = await getIntakeV6PricedQuoteDryRun(workspaceId);
      setDryRun(next);
    } catch (err) {
      setDryRun(null);
      setActionError(err instanceof Error ? err.message : "Nu am putut încărca previzualizarea de preț.");
    } finally {
      setDryRunLoading(false);
    }
  }, [workspaceId]);

  const refresh = useCallback(async () => {
    if (!workspaceId) return;
    setLoading(true);
    setActionError(null);
    try {
      const next = await getIntakeV6CommercialSpineState(workspaceId);
      setState(next);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Nu am putut încărca starea comercială.");
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  const refreshAll = useCallback(async () => {
    await Promise.all([refresh(), refreshDryRun()]);
  }, [refresh, refreshDryRun]);

  useEffect(() => {
    if (quoteId) {
      void refreshAll();
    }
  }, [quoteId, refreshAll]);

  const runAction = async (label: string, fn: () => Promise<unknown>) => {
    setBusyAction(label);
    setActionError(null);
    try {
      await fn();
      await refreshAll();
      onSpineUpdated?.();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : `${label} a eșuat.`);
    } finally {
      setBusyAction(null);
    }
  };

  const dryRunReady = dryRun?.pricing_status === "V6_PRICED_DRY_RUN_READY";
  const dryRunTotals = dryRun?.commercial_totals;
  const expectedTotalGross = dryRunTotals?.total_gross ?? null;
  const dryRunBlockers = useMemo(() => readBlockerCodes(dryRun), [dryRun]);

  if (!intakeCode) {
    return (
      <div className={v6.card} data-testid="intake-v6-commercial-spine">
        <p className="text-[12px] text-slate-400">Workspace-ul V6 nu este încă legat de ofertare.</p>
      </div>
    );
  }

  const pricingDone = state?.pricing_review?.completed === true;
  const quoteTotalsAvailable = state?.quote_commercial_totals?.available === true;
  const quoteTotalsBlocker =
    typeof state?.quote_commercial_totals?.blocker === "string"
      ? state.quote_commercial_totals.blocker
      : null;
  const ownerValid = state?.owner_approval?.valid === true && state?.owner_approval?.stale !== true;
  const snapshotV2 = state?.snapshot_v2 ?? {};
  const snapshotExists = snapshotV2.exists === true;
  const snapshotAcceptAllowed = snapshotV2.accept_allowed === true;
  const accepted = state?.quote_accepted === true;
  const converted = state?.v6_order_conversion?.converted === true;
  const convertBlockers = readBlockedReasons(state?.v6_order_conversion?.blocked_reasons);

  const workflowSteps = buildWorkflowSteps({
    quoteTotalsAvailable,
    snapshotExists,
    pricingDone,
    ownerValid,
    accepted,
    converted,
    dryRunReady,
  });

  const heroTotal = quoteTotalsAvailable
    ? formatMoney(state?.quote_commercial_totals?.grand_total as number | null | undefined)
    : dryRunReady
      ? formatMoney(expectedTotalGross, dryRunTotals?.currency)
      : "Nepretuit";

  const heroHint = quoteTotalsAvailable
    ? "Total oficial pe quote. Continuă cu snapshot și review."
    : dryRunReady
      ? "Previzualizare backend pregătită. Scrie totalurile pe ofertă."
      : "Completează workspace-ul V6 sau rezolvă blockerele de mai jos.";

  const primaryAction = resolvePrimarySpineAction({
    quoteTotalsAvailable,
    snapshotExists,
    pricingDone,
    ownerValid,
    accepted,
    converted,
    dryRunReady,
  });

  const showAction = (actionId: SpineActionId) =>
    showSecondaryActions ||
    primaryAction === actionId ||
    (actionId === "write" && !quoteTotalsAvailable);

  const pricingSectionComplete = quoteTotalsAvailable;

  return (
    <div className={v6.card} data-testid="intake-v6-commercial-spine">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-[13px] font-bold text-slate-100">Flux comercial V6</h3>
          <p className="mt-1 text-[11px] text-slate-400">{heroHint}</p>
        </div>
        <div className="text-right" data-testid="intake-v6-hero-total">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Total estimat / oficial</p>
          <p
            className={`text-[18px] font-bold ${quoteTotalsAvailable || dryRunReady ? "text-slate-100" : "text-amber-300"}`}
          >
            {heroTotal}
          </p>
        </div>
      </div>

      <WorkflowStepper steps={workflowSteps} />

      {loading && !state ? (
        <p className="mb-3 text-[12px] text-slate-400">Încarc starea comercială…</p>
      ) : null}

      <section className="mb-4 rounded-lg border border-[#1E293B] bg-[#0B1220] p-3" data-testid="intake-v6-priced-quote-bridge">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h4 className="text-[12px] font-semibold text-slate-200">1. Prețuire oficială</h4>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
              pricingSectionComplete || dryRunReady
                ? "bg-emerald-950/40 text-emerald-200 border border-emerald-800/40"
                : "bg-amber-950/30 text-amber-200 border border-amber-800/30"
            }`}
            data-testid="intake-v6-dry-run-status-label"
          >
            {pricingSectionComplete
              ? "Prețuit"
              : dryRunStatusLabel(dryRun?.pricing_status, dryRunLoading)}
          </span>
        </div>

        {pricingSectionComplete && !showSecondaryActions && primaryAction !== "snapshot" ? (
          <p className="text-[11px] text-emerald-200/90" data-testid="intake-v6-pricing-complete-summary">
            Totalurile oficiale sunt pe ofertă.
          </p>
        ) : dryRunLoading && !dryRun ? (
          <p className="text-[11px] text-slate-400">Calculez previzualizarea backend…</p>
        ) : (
          <>
            {!quoteTotalsAvailable && dryRunReady ? (
              <p className="mb-3 text-[11px] text-slate-300">
                Total propus:{" "}
                <strong data-testid="intake-v6-dry-run-total">{formatMoney(expectedTotalGross, dryRunTotals?.currency)}</strong>
              </p>
            ) : null}

            {dryRunBlockers.length > 0 ? (
              <ul className="mb-3 space-y-1 text-[11px] text-amber-200" data-testid="intake-v6-dry-run-blockers">
                {dryRunBlockers.map((code) => (
                  <li key={code}>• {formatQuoteHandoffBlocker(code)}</li>
                ))}
              </ul>
            ) : null}

            {!quoteTotalsAvailable && !pricingDone ? (
              <p className="mb-3 text-[11px] text-amber-200/90" data-testid="intake-v6-spine-pricing-blocker">
                {quoteTotalsBlocker === "QUOTE_NOT_PRICED"
                  ? "Draft nepretuit — apasă «Scrie totaluri pe ofertă» când previzualizarea e pregătită."
                  : "Totalurile comerciale nu sunt încă disponibile."}
              </p>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className={v6.btnPrimary}
                disabled={
                  !!busyAction ||
                  !dryRunReady ||
                  expectedTotalGross == null ||
                  !clientAnalysisHash
                }
                data-testid="intake-v6-handoff-to-offer"
                onClick={() =>
                  void runAction("handoff", async () => {
                    const result = await handoffIntakeV6ToOffer(workspaceId, {
                      client_analysis_hash: clientAnalysisHash,
                      expected_total_gross: expectedTotalGross as number,
                      expected_pricing_hash: dryRun?.pricing_hash ?? undefined,
                      operator_confirmation: true,
                    });
                    if (result.status !== "V6_PRICED_QUOTE_WRITTEN") {
                      const blockerCodes = (result.blockers ?? []).map((item) => item.code).join(", ");
                      throw new Error(
                        blockerCodes
                          ? `Trimiterea în ofertare a fost blocată: ${blockerCodes}`
                          : "Trimiterea în ofertare a fost blocată.",
                      );
                    }
                    if (result.next_route) {
                      navigate(result.next_route);
                    }
                  })
                }
              >
                {busyAction === "handoff" ? "…" : "Trimite în ofertare"}
              </button>

              {showAction("write") ? (
              <button
                type="button"
                className={primaryAction === "write" ? v6.btnPrimary : v6.btnGhost}
                disabled={!!busyAction || !dryRunReady || quoteTotalsAvailable || expectedTotalGross == null}
                data-testid="intake-v6-write-priced-quote"
                onClick={() =>
                  void runAction("write", async () => {
                    const result = await writeIntakeV6PricedQuote(workspaceId, {
                      quote_id: quoteId,
                      expected_total_gross: expectedTotalGross as number,
                      expected_pricing_hash: dryRun?.pricing_hash ?? undefined,
                      operator_confirmation: true,
                    });
                    if (result.status !== "V6_PRICED_QUOTE_WRITTEN") {
                      const blockerCodes = (result.blockers ?? []).map((item) => item.code).join(", ");
                      throw new Error(
                        blockerCodes
                          ? `Scrierea totalurilor a fost blocată: ${blockerCodes}`
                          : "Scrierea totalurilor a fost blocată.",
                      );
                    }
                  })
                }
              >
                {busyAction === "write" ? "…" : "Scrie totaluri pe ofertă"}
              </button>
              ) : null}

              {showAction("snapshot") || showSecondaryActions ? (
              <>
              <button
                type="button"
                className={primaryAction === "snapshot" ? v6.btnPrimary : v6.btnGhost}
                disabled={!!busyAction || !quoteTotalsAvailable || snapshotExists}
                data-testid="intake-v6-create-snapshot-v2"
                onClick={() =>
                  void runAction("snapshot", async () => {
                    const result = await createIntakeV6QuoteSnapshotV2(workspaceId, quoteId, {
                      operator_confirmation: true,
                      expected_grand_total: state?.quote_commercial_totals?.grand_total ?? undefined,
                    });
                    if (result.status !== "V6_QUOTE_SNAPSHOT_V2_CREATED") {
                      const blockerCodes = (result.blockers ?? []).map((item) => item.code).join(", ");
                      throw new Error(blockerCodes ? `Snapshot blocat: ${blockerCodes}` : "Snapshot blocat.");
                    }
                  })
                }
              >
                {busyAction === "snapshot" ? "…" : "Snapshot V2"}
              </button>

              {!snapshotExists ? (
                <p className="basis-full text-[11px] text-amber-200" data-testid="intake-v6-snapshot-required-hint">
                  Creeaza Snapshot V2 inainte de Review si Accept.
                </p>
              ) : null}

              {showSecondaryActions ? (
              <button
                type="button"
                className={v6.btnGhost}
                disabled={!!busyAction || dryRunLoading}
                data-testid="intake-v6-refresh-dry-run"
                onClick={() => void refreshDryRun()}
              >
                Reîmprospătează
              </button>
              ) : null}
              </>
              ) : null}
            </div>
          </>
        )}
      </section>

      <section className="mb-3 rounded-lg border border-[#1E293B] bg-[#0B1220] p-3">
        <h4 className="mb-2 text-[12px] font-semibold text-slate-200">2. Aprobare & conversie</h4>
        {convertBlockers.length > 0 && !converted ? (
          <ul className="mb-3 space-y-1 text-[11px] text-amber-200" data-testid="intake-v6-spine-blockers">
            {convertBlockers.slice(0, 3).map((code) => (
              <li key={code}>• {formatQuoteHandoffBlocker(code)}</li>
            ))}
          </ul>
        ) : null}

        <div className="flex flex-wrap gap-2">
          {showAction("pricing") ? (
          <button
            type="button"
            className={primaryAction === "pricing" ? v6.btnPrimary : v6.btnGhost}
            disabled={!!busyAction || pricingDone || !quoteTotalsAvailable || !snapshotExists}
            data-testid="intake-v6-complete-pricing-review"
            onClick={() =>
              void runAction("pricing", () =>
                completeIntakeV6PricingReview(quoteId, {
                  expected_quote_id: quoteId,
                  expected_intake_code: intakeCode,
                  client_analysis_hash: clientAnalysisHash ?? undefined,
                  reviewer_confirmation: true,
                  confirm_quote_stays_draft: true,
                  confirm_no_order: true,
                  confirm_no_execution: true,
                  confirm_no_inventory: true,
                  pricing_review_reason: "Pricing review completed using official V6 backend quote totals.",
                }),
              )
            }
          >
            {busyAction === "pricing" ? "…" : "Review preț"}
          </button>
          ) : null}

          {showAction("approval") ? (
          <button
            type="button"
            className={primaryAction === "approval" ? v6.btnPrimary : v6.btnGhost}
            disabled={!!busyAction || !pricingDone || ownerValid}
            data-testid="intake-v6-owner-approval"
            onClick={() =>
              void runAction("approval", () =>
                persistIntakeV6OwnerApproval(quoteId, {
                  decision_reason: "Reviewed V6 quote and production handoff preview.",
                  acknowledged_no_execution_tasks: true,
                  acknowledged_no_stock_consumption: true,
                  client_analysis_hash: clientAnalysisHash ?? undefined,
                }),
              )
            }
          >
            {busyAction === "approval" ? "…" : "Aprobare owner"}
          </button>
          ) : null}

          {showAction("accept") ? (
          <button
            type="button"
            className={primaryAction === "accept" ? v6.btnPrimary : v6.btnGhost}
            disabled={!!busyAction || !pricingDone || !ownerValid || !snapshotAcceptAllowed || accepted}
            data-testid="intake-v6-accept-quote"
            onClick={() =>
              void runAction("accept", () =>
                acceptIntakeV6Quote(quoteId, {
                  expected_quote_id: quoteId,
                  expected_intake_code: intakeCode,
                  accept_reason: "Accept V6 priced draft after owner approval.",
                  reviewer_confirmation: true,
                  confirm_pricing_review_completed: true,
                  confirm_no_order: true,
                  confirm_no_execution: true,
                  confirm_no_inventory: true,
                  confirm_convert_separate: true,
                }),
              )
            }
          >
            {busyAction === "accept" ? "…" : "Acceptă oferta"}
          </button>
          ) : null}

          {showAction("convert") ? (
          <button
            type="button"
            className={primaryAction === "convert" ? v6.btnPrimary : v6.btnGhost}
            disabled={!!busyAction || !accepted || converted || convertBlockers.length > 0}
            data-testid="intake-v6-convert-order"
            onClick={() =>
              void runAction("convert", () =>
                convertIntakeV6QuoteToOrder(quoteId, {
                  expected_quote_id: quoteId,
                  expected_intake_code: intakeCode,
                  convert_reason: "Convert accepted V6 quote to locked order with frozen snapshot.",
                  reviewer_confirmation: true,
                  confirm_quote_accepted: true,
                  confirm_pricing_review_completed: true,
                  confirm_create_order_only: true,
                  confirm_no_execution_plan: true,
                  confirm_no_execution_tasks: true,
                  confirm_no_inventory: true,
                  confirm_production_separate: true,
                }),
              )
            }
          >
            {busyAction === "convert" ? "…" : "Conversie comandă"}
          </button>
          ) : null}
        </div>
      </section>

      {!converted ? (
        <button
          type="button"
          className="mb-3 text-[11px] text-slate-500 hover:text-slate-300"
          onClick={() => setShowSecondaryActions((value) => !value)}
          data-testid="intake-v6-toggle-secondary-actions"
        >
          {showSecondaryActions ? "Ascunde acțiuni secundare" : "Arată toate acțiunile"}
        </button>
      ) : null}

      {actionError ? (
        <p className="mb-3 text-[11px] text-red-300" data-testid="intake-v6-spine-error">
          {actionError}
        </p>
      ) : null}

      <button
        type="button"
        className="text-[11px] text-slate-500 hover:text-slate-300"
        onClick={() => setShowTechnical((value) => !value)}
        data-testid="intake-v6-toggle-technical"
      >
        {showTechnical ? "Ascunde detalii tehnice" : "Arată detalii tehnice"}
      </button>

      {showTechnical ? (
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            className={v6.btnGhost}
            disabled={!!busyAction}
            data-testid="intake-v6-spine-refresh"
            onClick={() => void refreshAll()}
          >
            Reîmprospătează starea
          </button>
        </div>
      ) : null}

      {showTechnical ? (
        <div
          className="mt-3 rounded border border-[#1E293B] bg-[#090f18] p-3 text-[10px] text-slate-500"
          data-testid="intake-v6-commercial-spine-truth-boundary"
        >
          <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div>
              <dt>Quote priced</dt>
              <dd data-testid="intake-v6-spine-quote-priced">{quoteTotalsAvailable ? "yes" : "no"}</dd>
            </div>
            <div>
              <dt>Snapshot V2</dt>
              <dd data-testid="intake-v6-spine-snapshot">{snapshotExists ? `#${snapshotV2.snapshot_id ?? "yes"}` : "missing"}</dd>
            </div>
            <div>
              <dt>Pricing review</dt>
              <dd data-testid="intake-v6-spine-pricing">{pricingDone ? "completed" : "pending"}</dd>
            </div>
            <div>
              <dt>Owner approval</dt>
              <dd data-testid="intake-v6-spine-owner">
                {ownerValid ? "valid" : state?.owner_approval?.exists ? "stale/missing" : "missing"}
              </dd>
            </div>
            <div>
              <dt>Order</dt>
              <dd data-testid="intake-v6-spine-order">
                {converted ? `#${state?.v6_order_conversion?.order_id}` : "not created"}
              </dd>
            </div>
          </dl>
          <p className="mt-2 leading-relaxed">
            Totalurile oficiale provin din backend V6, nu din preview Intake. Snapshot V2 îngheață oferta
            înainte de accept; conversia creează doar order snapshot, fără plan de execuție.
          </p>
          {dryRunTotals ? (
            <p className="mt-2" data-testid="intake-v6-dry-run-subtotal">
              Dry-run subtotal: {formatMoney(dryRunTotals.subtotal_net, dryRunTotals.currency)} · TVA:{" "}
              {formatMoney(dryRunTotals.vat_amount, dryRunTotals.currency)}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
