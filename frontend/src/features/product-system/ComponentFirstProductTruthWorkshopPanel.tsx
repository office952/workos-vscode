import { useMemo, useState } from "react";
import { ReturnCantOwnerInputsPanel } from "./ReturnCantOwnerInputsPanel";
import {
  buildWorkshopSummary,
  COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS,
  exportOwnerQuestions,
  getWorkshopByShortLabel,
  groupOwnerQuestionsBySeverity,
  ownerInputStatusLabel,
  pathSourceLabel,
  type ComponentTruthField,
  type ComponentTruthWorkshop,
} from "./componentFirstLettersProductTruthWorkshop";

function StatusChip({
  label,
  tone,
  testId,
}: {
  label: string;
  tone: "emerald" | "amber" | "rose" | "slate" | "cyan";
  testId?: string;
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-800/40 bg-emerald-950/25 text-emerald-200"
      : tone === "amber"
        ? "border-amber-800/40 bg-amber-950/25 text-amber-200"
        : tone === "rose"
          ? "border-rose-800/40 bg-rose-950/25 text-rose-200"
          : tone === "cyan"
            ? "border-cyan-800/40 bg-cyan-950/25 text-cyan-200"
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

function statusTone(status: ComponentTruthField["status"]) {
  if (status === "confirmed") return "emerald" as const;
  if (status === "owner_input_required") return "amber" as const;
  if (status === "blocked_until_owner_decision") return "rose" as const;
  return "slate" as const;
}

function FieldRow({ field }: { field: ComponentTruthField }) {
  return (
    <tr data-testid={`product-system-truth-workshop-field-${field.fieldKey}`}>
      <td className="px-2 py-2 align-top font-mono text-[10px] text-slate-200">{field.fieldKey}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-300">{field.labelRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip label={ownerInputStatusLabel(field.status)} tone={statusTone(field.status)} />
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-500">
        {field.audience.join(", ")}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-500">
        {field.requirement.join(", ")}
      </td>
      <td className="px-2 py-2 align-top font-mono text-[9px] text-cyan-200/80">
        {field.truthPath}
        <span className="mt-0.5 block text-slate-500">({pathSourceLabel(field.pathSource)})</span>
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">
        {field.ownerQuestionRo ?? "—"}
        {field.mustNotInvent ? (
          <span
            data-testid={`product-system-truth-workshop-must-not-invent-${field.fieldKey}`}
            className="mt-1 block font-semibold text-amber-200/90"
          >
            Must not invent
          </span>
        ) : null}
      </td>
    </tr>
  );
}

function ComponentWorkshopDetail({ workshop }: { workshop: ComponentTruthWorkshop }) {
  if (workshop.fields.length === 0) {
    return (
      <div
        data-testid={`product-system-truth-workshop-skeleton-${workshop.componentShortLabel}`}
        className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
      >
        <p className="text-[11px] font-bold text-slate-200">{workshop.componentLabelRo}</p>
        <p className="mt-1 text-[10px] text-slate-400">{workshop.role}</p>
        <p className="mt-2 text-[10px] font-semibold uppercase text-slate-500">Întrebări skeleton</p>
        <ul className="mt-1 space-y-1 text-[10px] text-slate-300">
          {workshop.ownerQuestions.map((q) => (
            <li key={q}>• {q}</li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div data-testid={`product-system-truth-workshop-detail-${workshop.componentShortLabel}`}>
      <p className="text-[11px] font-bold text-slate-200">{workshop.componentLabelRo}</p>
      <p className="mt-1 text-[10px] text-slate-400">{workshop.role}</p>
      {workshop.componentShortLabel === "RETURN-CANT" ? (
        <>
          <p
            data-testid="product-system-truth-workshop-return-cant-finish-options"
            className="mt-2 text-[10px] text-slate-300"
          >
            Variante finisaj confirmate: Culoare Stock · Oracal · Vopsit RAL
          </p>
          <div className="mt-4">
            <ReturnCantOwnerInputsPanel />
          </div>
        </>
      ) : null}
      <div className="mt-3 overflow-x-auto">
        <table
          data-testid={`product-system-truth-workshop-fields-table-${workshop.componentShortLabel}`}
          className="min-w-full border-collapse text-left"
        >
          <thead>
            <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wide text-slate-500">
              <th className="px-2 py-2">Field</th>
              <th className="px-2 py-2">Label</th>
              <th className="px-2 py-2">Status</th>
              <th className="px-2 py-2">Audience</th>
              <th className="px-2 py-2">Required for</th>
              <th className="px-2 py-2">Truth path</th>
              <th className="px-2 py-2">Owner question</th>
            </tr>
          </thead>
          <tbody>
            {workshop.fields.map((field) => (
              <FieldRow key={field.fieldKey} field={field} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ComponentFirstProductTruthWorkshopPanel() {
  const [selectedLabel, setSelectedLabel] = useState("RETURN-CANT");
  const summary = useMemo(() => buildWorkshopSummary(), []);
  const selectedWorkshop = useMemo(
    () => getWorkshopByShortLabel(selectedLabel) ?? COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS[0],
    [selectedLabel],
  );
  const questionsBySeverity = useMemo(() => groupOwnerQuestionsBySeverity(), []);
  const allQuestions = useMemo(() => exportOwnerQuestions(), []);

  return (
    <section
      data-testid="product-system-truth-owner-workshop"
      className="space-y-4 rounded-xl border border-amber-900/40 bg-amber-950/10 px-4 py-4"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold text-amber-100">Product Truth owner workshop</h3>
          <StatusChip
            label="OWNER INPUT REQUIRED"
            tone="amber"
            testId="product-system-truth-workshop-global-status"
          />
        </div>
        <p
          data-testid="product-system-truth-workshop-disclaimer"
          className="mt-2 text-xs leading-relaxed text-slate-400"
        >
          Acesta nu este Product Truth live. Este contract de lucru pentru completarea template-urilor
          component-first.
        </p>
      </div>

      <div
        data-testid="product-system-truth-workshop-safety-copy"
        className="rounded-lg border border-slate-800/80 bg-slate-950/50 px-3 py-2 text-[10px] text-slate-400"
      >
        <p>No Product Truth write</p>
        <p>No Pricing activation</p>
        <p>No Work Intake exposure</p>
        <p>No runtime replacement</p>
        <p>No seed / live rows</p>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-md border border-emerald-800/30 bg-emerald-950/10 px-2 py-1.5">
          <p className="text-[10px] font-semibold uppercase text-slate-500">Confirmed</p>
          <p
            data-testid="product-system-truth-workshop-summary-confirmed"
            className="text-base font-bold tabular-nums text-emerald-200"
          >
            {summary.confirmedFields}
          </p>
        </div>
        <div className="rounded-md border border-amber-800/30 bg-amber-950/10 px-2 py-1.5">
          <p className="text-[10px] font-semibold uppercase text-slate-500">Owner input</p>
          <p
            data-testid="product-system-truth-workshop-summary-owner-input"
            className="text-base font-bold tabular-nums text-amber-200"
          >
            {summary.ownerInputRequiredFields}
          </p>
        </div>
        <div className="rounded-md border border-rose-800/30 bg-rose-950/10 px-2 py-1.5">
          <p className="text-[10px] font-semibold uppercase text-slate-500">Blocked</p>
          <p className="text-base font-bold tabular-nums text-rose-200">{summary.blockedFields}</p>
        </div>
        <div className="rounded-md border border-slate-800 bg-slate-950/40 px-2 py-1.5">
          <p className="text-[10px] font-semibold uppercase text-slate-500">Before pricing</p>
          <p className="text-base font-bold tabular-nums text-slate-200">
            {summary.requiredBeforePricing}
          </p>
        </div>
        <div className="rounded-md border border-slate-800 bg-slate-950/40 px-2 py-1.5">
          <p className="text-[10px] font-semibold uppercase text-slate-500">Before ProductDef</p>
          <p className="text-base font-bold tabular-nums text-slate-200">
            {summary.requiredBeforeProductDefinition}
          </p>
        </div>
        <div className="rounded-md border border-slate-800 bg-slate-950/40 px-2 py-1.5">
          <p className="text-[10px] font-semibold uppercase text-slate-500">Before execution</p>
          <p className="text-base font-bold tabular-nums text-slate-200">
            {summary.requiredBeforeExecution}
          </p>
        </div>
      </div>

      <div
        data-testid="product-system-truth-workshop-component-selector"
        className="flex flex-wrap gap-1.5"
        role="tablist"
        aria-label="Component workshop selector"
      >
        {COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS.map((workshop) => {
          const active = selectedLabel === workshop.componentShortLabel;
          return (
            <button
              key={workshop.componentCode}
              type="button"
              role="tab"
              aria-selected={active}
              data-testid={`product-system-truth-workshop-tab-${workshop.componentShortLabel}`}
              onClick={() => setSelectedLabel(workshop.componentShortLabel)}
              className={`rounded-full px-3 py-1 text-[10px] font-bold uppercase transition-colors ${
                active
                  ? "bg-amber-950/40 text-amber-100 ring-1 ring-amber-700/40"
                  : "text-slate-500 hover:bg-slate-900/60 hover:text-slate-300"
              }`}
            >
              {workshop.componentShortLabel}
            </button>
          );
        })}
      </div>

      {selectedWorkshop ? <ComponentWorkshopDetail workshop={selectedWorkshop} /> : null}

      <article
        data-testid="product-system-truth-workshop-owner-questions"
        className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase tracking-wide text-slate-200">
          Întrebări pentru owner
        </p>

        <div className="mt-3 space-y-3">
          <div data-testid="product-system-truth-workshop-questions-return-cant">
            <p className="text-[10px] font-bold text-amber-200/90">RETURN-CANT — prioritate</p>
            <ul className="mt-1 space-y-1 text-[10px] text-slate-300">
              {allQuestions
                .filter((q) => q.componentShortLabel === "RETURN-CANT")
                .map((q) => (
                  <li key={`${q.fieldKey ?? "skeleton"}-${q.questionRo}`}>
                    <span className="text-slate-500">[{q.severity.replace(/_/g, " ")}]</span> {q.questionRo}
                  </li>
                ))}
            </ul>
          </div>

          {(["required_before_pricing", "required_before_product_definition"] as const).map((severity) => {
            const items = questionsBySeverity[severity];
            if (items.length === 0) return null;
            return (
              <div key={severity} data-testid={`product-system-truth-workshop-questions-${severity}`}>
                <p className="text-[10px] font-bold text-slate-400">{severity.replace(/_/g, " ")}</p>
                <ul className="mt-1 space-y-1 text-[10px] text-slate-300">
                  {items.map((q) => (
                    <li key={`${q.componentShortLabel}-${q.questionRo}`}>
                      <span className="font-mono text-slate-500">{q.componentShortLabel}:</span> {q.questionRo}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}

          <div data-testid="product-system-truth-workshop-questions-skeleton">
            <p className="text-[10px] font-bold text-slate-400">FACE / BACK / LED / FINISH / MOUNTING — skeleton</p>
            <ul className="mt-1 space-y-1 text-[10px] text-slate-300">
              {COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS.filter(
                (w) => w.componentShortLabel !== "RETURN-CANT",
              ).flatMap((w) =>
                w.ownerQuestions.map((q) => (
                  <li key={`${w.componentShortLabel}-${q}`}>
                    <span className="font-mono text-slate-500">{w.componentShortLabel}:</span> {q}
                  </li>
                )),
              )}
            </ul>
          </div>
        </div>
      </article>
    </section>
  );
}
