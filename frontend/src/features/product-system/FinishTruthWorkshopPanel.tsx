import {
  buildFinishReadinessSummary,
  FINISH_ARTWORK_DEPENDENCY_INPUTS,
  FINISH_BOUNDARY_REAFFIRMATION,
  FINISH_COMPONENT_TEMPLATE_CODE,
  FINISH_DOES_NOT_OWN,
  FINISH_DOES_NOT_OWN_CANT,
  FINISH_FACE_DEPENDENCY_INPUTS,
  FINISH_IDENTITY,
  FINISH_OWNER_DECISION_SOURCE,
  FINISH_OWNER_QUESTIONS_PENDING,
  FINISH_OWNS,
  FINISH_PRICING_EVIDENCE,
  FINISH_QUANTITY_BASIS_QUESTIONS,
  FINISH_READINESS_BLOCKERS,
  FINISH_VARIANT_ENTRIES,
  FINISH_WORKSHOP_STATUS,
  type FinishWorkshopFieldStatus,
  type FinishWorkshopVariantEntry,
} from "./componentFirstFinishTruthWorkshop";
import { FinishEstimatedPriceDraftPanel } from "./FinishEstimatedPriceDraftPanel";

function StatusChip({
  label,
  tone,
  testId,
}: {
  label: string;
  tone: "emerald" | "amber" | "rose" | "slate" | "cyan" | "violet";
  testId?: string;
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-800/40 bg-emerald-950/25 text-emerald-200"
      : tone === "cyan"
        ? "border-cyan-800/40 bg-cyan-950/25 text-cyan-200"
        : tone === "violet"
          ? "border-violet-800/40 bg-violet-950/25 text-violet-200"
          : tone === "amber"
            ? "border-amber-800/40 bg-amber-950/25 text-amber-200"
            : tone === "rose"
              ? "border-rose-800/40 bg-rose-950/25 text-rose-200"
              : "border-slate-700 bg-slate-900 text-slate-400";

  return (
    <span
      data-testid={testId}
      className={`rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase ${toneClass}`}
    >
      {label}
    </span>
  );
}

function fieldStatusLabel(status: FinishWorkshopFieldStatus) {
  return status.replace(/_/g, " ").toUpperCase();
}

function fieldStatusTone(status: FinishWorkshopFieldStatus) {
  if (status === "owner_confirmed" || status === "registry_authority") return "emerald" as const;
  if (status === "evidence_only" || status === "source_found") return "cyan" as const;
  if (status === "owner_input_required" || status === "draft_only") return "amber" as const;
  if (status === "blocked") return "rose" as const;
  return "slate" as const;
}

function VariantRow({ entry }: { entry: FinishWorkshopVariantEntry }) {
  return (
    <tr data-testid={`product-system-finish-truth-variant-row-${entry.id}`}>
      <td className="px-2 py-2 align-top text-[10px] text-slate-300">{entry.labelRo}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">{entry.surfaceTarget}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip label={fieldStatusLabel(entry.ownerStatus)} tone={fieldStatusTone(entry.ownerStatus)} />
      </td>
      <td className="px-2 py-2 align-top font-mono text-[9px] text-cyan-200/80">{entry.truthPathProposal}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">{entry.quantityBasis}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-500">{entry.notesRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip label="BLOCKED" tone="slate" testId={`product-system-finish-truth-variant-active-${entry.id}`} />
      </td>
    </tr>
  );
}

export function FinishTruthWorkshopPanel() {
  const summary = buildFinishReadinessSummary();

  return (
    <section
      data-testid="product-system-finish-truth-workshop"
      className="space-y-4 rounded-xl border border-fuchsia-900/40 bg-fuchsia-950/10 px-4 py-4"
    >
      <div data-testid="product-system-finish-truth-contract-summary">
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-semibold text-fuchsia-100">FINISH Component Truth Workshop</h4>
          <StatusChip
            label="READONLY WORKSHOP"
            tone="slate"
            testId="product-system-finish-truth-readonly-workshop-badge"
          />
          <StatusChip
            label="PARTIAL CONFIRMED"
            tone="cyan"
            testId="product-system-finish-truth-partial-confirmed-badge"
          />
          <StatusChip
            label="OWNER DECISIONS APPLIED"
            tone="emerald"
            testId="product-system-finish-truth-owner-decisions-applied-badge"
          />
        </div>
        <p className="mt-1 text-[10px] text-slate-500">
          {FINISH_COMPONENT_TEMPLATE_CODE} · role: FINISH · status: {FINISH_WORKSHOP_STATUS.replace(/_/g, " ")}
          · source: {FINISH_OWNER_DECISION_SOURCE}
        </p>
        <p className="mt-1 text-[10px] text-fuchsia-200/80">
          Face/artwork surface application — consumes FACE outputs; does not own substrate or cant finish.
        </p>
      </div>

      <div
        data-testid="product-system-finish-truth-guard-badges"
        className="flex flex-wrap gap-2"
      >
        <StatusChip
          label="PRICING ACTIVE: NO"
          tone="rose"
          testId="product-system-finish-truth-pricing-active-no"
        />
        <StatusChip
          label="PRODUCT TRUTH WRITE: NO"
          tone="rose"
          testId="product-system-finish-truth-product-truth-write-no"
        />
        <StatusChip
          label="WORK INTAKE: BLOCKED"
          tone="rose"
          testId="product-system-finish-truth-work-intake-blocked"
        />
        {FINISH_DOES_NOT_OWN_CANT ? (
          <StatusChip
            label="FINISH DOES NOT OWN CANT"
            tone="emerald"
            testId="product-system-finish-truth-does-not-own-cant"
          />
        ) : null}
      </div>

      <div
        data-testid="product-system-finish-truth-safety-copy"
        className="rounded-lg border border-slate-800/80 bg-slate-950/50 px-3 py-2 text-[10px] text-slate-400"
      >
        <p>No Product Truth live write</p>
        <p>No Pricing Registry write · no /inventory/pricing write</p>
        <p>No Pricing activation</p>
        <p>No Work Intake exposure</p>
        <p>No Save / Apply / Activate / Create Pricing Key / Generate Quote / Sync</p>
        <p data-testid="product-system-finish-truth-ready-for-pricing">Ready for pricing: NO</p>
        <p>Owner-confirmed variants: {summary.ownerConfirmedVariantCount}/{summary.variantCount}</p>
        <p data-testid="product-system-finish-truth-face-material-boundary">
          FACE 3 mm material (MAT-ACP-FATA-LITERE 16 EUR/mp) belongs to FACE — not FINISH
        </p>
        <p data-testid="product-system-finish-truth-ral-minimum-boundary">
          RAL cant minimum 100 lei belongs to RETURN-CANT — not FINISH
        </p>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <article
          data-testid="product-system-finish-truth-owns"
          className="rounded-lg border border-emerald-900/30 bg-emerald-950/10 px-3 py-3"
        >
          <p className="text-[11px] font-bold uppercase text-emerald-200">FINISH owns</p>
          <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
            {FINISH_OWNS.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>

        <article
          data-testid="product-system-finish-truth-does-not-own"
          className="rounded-lg border border-rose-900/30 bg-rose-950/10 px-3 py-3"
        >
          <p className="text-[11px] font-bold uppercase text-rose-200">FINISH does not own</p>
          <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
            {FINISH_DOES_NOT_OWN.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
      </div>

      <article
        data-testid="product-system-finish-truth-face-dependencies"
        className="rounded-lg border border-cyan-900/30 bg-cyan-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-cyan-200">Dependencies from FACE</p>
        <div className="mt-2 space-y-2">
          {FINISH_FACE_DEPENDENCY_INPUTS.map((input) => (
            <div
              key={input.inputKey}
              data-testid={`product-system-finish-truth-face-dep-${input.inputKey}`}
              className="rounded border border-slate-800/60 bg-slate-950/30 px-2.5 py-2 text-[10px]"
            >
              <p className="font-semibold text-slate-200">{input.labelRo}</p>
              <p className="mt-0.5 text-slate-400">Use: {input.consumerUse}</p>
              <p className="mt-0.5 text-slate-500">{input.notesRo}</p>
            </div>
          ))}
        </div>
        <p className="mt-2 text-[10px] text-slate-500">
          Artwork inputs ({summary.artworkDependencyCount}) — separate section; LOGO component split pending owner.
        </p>
        <div className="mt-2 space-y-2">
          {FINISH_ARTWORK_DEPENDENCY_INPUTS.map((input) => (
            <div
              key={input.inputKey}
              data-testid={`product-system-finish-truth-artwork-dep-${input.inputKey}`}
              className="rounded border border-slate-800/60 bg-slate-950/30 px-2.5 py-2 text-[10px]"
            >
              <p className="font-semibold text-slate-200">{input.labelRo}</p>
              <p className="mt-0.5 text-slate-500">{input.notesRo}</p>
            </div>
          ))}
        </div>
      </article>

      <article data-testid="product-system-finish-truth-variants-table">
        <p className="text-[11px] font-bold uppercase text-slate-200">Surface variants (readonly)</p>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-bold uppercase text-slate-500">
                <th className="px-2 py-2">Variant</th>
                <th className="px-2 py-2">Surface</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Truth path</th>
                <th className="px-2 py-2">Qty basis</th>
                <th className="px-2 py-2">Notes</th>
                <th className="px-2 py-2">Active</th>
              </tr>
            </thead>
            <tbody>
              {FINISH_VARIANT_ENTRIES.map((entry) => (
                <VariantRow key={entry.id} entry={entry} />
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article
        data-testid="product-system-finish-truth-quantity-basis"
        className="rounded-lg border border-amber-900/30 bg-amber-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-amber-200">Quantity basis questions</p>
        <ul className="mt-2 space-y-2 text-[10px] text-slate-300">
          {FINISH_QUANTITY_BASIS_QUESTIONS.map((q) => (
            <li
              key={q.questionKey}
              data-testid={`product-system-finish-truth-qty-question-${q.questionKey}`}
            >
              <span className="font-semibold text-slate-200">{q.labelRo}</span>
              <span className="mt-0.5 block text-amber-200/90">{q.ownerQuestionRo}</span>
              <span className="mt-0.5 block text-slate-500">Proposed: {q.proposedBasis}</span>
            </li>
          ))}
        </ul>
      </article>

      <article
        data-testid="product-system-finish-truth-owner-questions"
        className="rounded-lg border border-violet-900/30 bg-violet-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-violet-200">Owner decisions A–E — applied (readonly)</p>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-bold uppercase text-slate-500">
                <th className="px-2 py-2">ID</th>
                <th className="px-2 py-2">Topic</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Evidence</th>
                <th className="px-2 py-2">Owner must answer</th>
              </tr>
            </thead>
            <tbody>
              {FINISH_OWNER_QUESTIONS_PENDING.map((q) => (
                <tr key={q.questionId} data-testid={`product-system-finish-truth-owner-question-${q.questionId}`}>
                  <td className="px-2 py-2 align-top font-mono text-[10px] text-violet-200">{q.questionId}</td>
                  <td className="px-2 py-2 align-top text-[10px] text-slate-300">{q.topicRo}</td>
                  <td className="px-2 py-2 align-top">
                    <StatusChip
                      label={fieldStatusLabel(q.status)}
                      tone={fieldStatusTone(q.status)}
                    />
                  </td>
                  <td className="px-2 py-2 align-top text-[10px] text-slate-500">{q.currentEvidenceRo}</td>
                  <td className="px-2 py-2 align-top text-[10px] text-amber-200/90">{q.ownerMustAnswerRo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article
        data-testid="product-system-finish-truth-boundary-reaffirmation"
        className="rounded-lg border border-emerald-900/30 bg-emerald-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-emerald-200">Boundary D — reaffirmed (not FINISH)</p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
          {FINISH_BOUNDARY_REAFFIRMATION.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
        <p
          data-testid="product-system-finish-truth-logo-split-question"
          className="mt-2 text-[10px] text-amber-200/90"
        >
          Question E (owner-confirmed): artwork surface finish under FINISH now — future LOGO component may own geometry later.
        </p>
      </article>

      <article
        data-testid="product-system-finish-truth-pricing-evidence"
        className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-slate-200">Evidence cross-reference (readonly)</p>
        <ul className="mt-2 space-y-2 text-[10px] text-slate-300">
          {FINISH_PRICING_EVIDENCE.map((ref) => (
            <li
              key={ref.evidenceKey}
              data-testid={`product-system-finish-truth-evidence-${ref.evidenceKey}`}
            >
              <span className="font-semibold text-slate-200">{ref.labelRo}</span>
              {ref.materialKeys.length > 0 ? (
                <span className="mt-0.5 block font-mono text-cyan-200/80">{ref.materialKeys.join(" · ")}</span>
              ) : null}
              {ref.laborKeys.length > 0 ? (
                <span className="mt-0.5 block font-mono text-cyan-200/80">{ref.laborKeys.join(" · ")}</span>
              ) : null}
              <span className="mt-0.5 block text-slate-500">{ref.notesRo}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[10px] text-rose-200/90">Evidence only — not active pricing rows.</p>
      </article>

      <FinishEstimatedPriceDraftPanel />

      <article
        data-testid="product-system-finish-truth-blockers"
        className="rounded-lg border border-rose-900/30 bg-rose-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-rose-200">Blockers & guards</p>
        <p className="mt-1 text-[10px] text-slate-500">
          {summary.readinessBlockerCount} blockers · {summary.blockedVariantCount}/{summary.variantCount} variants
          blocked · offerable: {String(FINISH_IDENTITY.offerable)} · pricing active:{" "}
          {String(FINISH_IDENTITY.pricingActive)}
        </p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
          {FINISH_READINESS_BLOCKERS.map((blocker) => (
            <li key={blocker}>• {blocker}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}

