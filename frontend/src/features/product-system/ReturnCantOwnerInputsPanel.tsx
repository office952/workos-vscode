import {
  buildReturnCantOwnerInputSummary,
  formatReturnCantOwnerInputDisplayValue,
  ownerConfirmedValueStatusLabel,
  RETURN_CANT_CONFIRMED_SO_FAR,
  RETURN_CANT_OWNER_INPUTS,
  RETURN_CANT_OWNER_QUESTIONS_PENDING,
  RETURN_CANT_STILL_MISSING_BEFORE_PRICING,
  RETURN_CANT_STILL_MISSING_BEFORE_PRODUCT_DEFINITION,
  type ReturnCantOwnerInput,
} from "./componentFirstReturnCantOwnerInputs";

function StatusChip({
  label,
  tone,
  testId,
}: {
  label: string;
  tone: "emerald" | "amber" | "rose" | "slate";
  testId?: string;
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-800/40 bg-emerald-950/25 text-emerald-200"
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

function inputTone(status: ReturnCantOwnerInput["status"]) {
  if (status === "owner_confirmed") return "emerald" as const;
  if (status === "owner_input_required") return "amber" as const;
  if (status === "blocked_until_owner_decision") return "rose" as const;
  return "slate" as const;
}

function OwnerInputRow({ input }: { input: ReturnCantOwnerInput }) {
  const displayValue = formatReturnCantOwnerInputDisplayValue(input);
  return (
    <tr data-testid={`product-system-return-cant-owner-input-row-${input.key}`}>
      <td className="px-2 py-2 align-top text-[10px] text-slate-300">{input.labelRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip
          label={ownerConfirmedValueStatusLabel(input.status)}
          tone={inputTone(input.status)}
        />
      </td>
      <td
        data-testid={`product-system-return-cant-owner-input-value-${input.key}`}
        className="px-2 py-2 align-top text-[10px] font-semibold text-slate-200"
      >
        {displayValue}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-500">{input.unit ?? "—"}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-500">
        {input.blockingArea.join(", ")}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">{input.ownerQuestionRo ?? "—"}</td>
    </tr>
  );
}

export function ReturnCantOwnerInputsPanel() {
  const summary = buildReturnCantOwnerInputSummary();

  return (
    <section
      data-testid="product-system-return-cant-owner-inputs"
      className="space-y-4 rounded-xl border border-purple-900/40 bg-purple-950/10 px-4 py-4"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-semibold text-purple-100">RETURN-CANT owner inputs</h4>
          <StatusChip
            label="OWNER INPUT REQUIRED"
            tone="amber"
            testId="product-system-return-cant-owner-inputs-global-status"
          />
        </div>
        <p className="mt-1 text-[10px] text-slate-500">Workshop only · nu este sursă runtime · nu scrie Product Truth live</p>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <article
          data-testid="product-system-return-cant-confirmed-so-far"
          className="rounded-lg border border-emerald-800/30 bg-emerald-950/10 px-3 py-2.5"
        >
          <p className="text-[10px] font-bold uppercase text-emerald-200/90">Confirmed so far</p>
          <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
            {RETURN_CANT_CONFIRMED_SO_FAR.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>

        <article
          data-testid="product-system-return-cant-missing-before-pricing"
          className="rounded-lg border border-amber-800/30 bg-amber-950/10 px-3 py-2.5"
        >
          <p className="text-[10px] font-bold uppercase text-amber-200/90">Still missing before pricing</p>
          <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
            {RETURN_CANT_STILL_MISSING_BEFORE_PRICING.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>

        <article
          data-testid="product-system-return-cant-missing-before-product-definition"
          className="rounded-lg border border-cyan-800/30 bg-cyan-950/10 px-3 py-2.5"
        >
          <p className="text-[10px] font-bold uppercase text-cyan-200/90">
            Still missing before ProductDefinition
          </p>
          <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
            {RETURN_CANT_STILL_MISSING_BEFORE_PRODUCT_DEFINITION.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
      </div>

      <div className="overflow-x-auto">
        <table
          data-testid="product-system-return-cant-owner-inputs-table"
          className="min-w-full border-collapse text-left"
        >
          <thead>
            <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wide text-slate-500">
              <th className="px-2 py-2">Owner input</th>
              <th className="px-2 py-2">Status</th>
              <th className="px-2 py-2">Current value</th>
              <th className="px-2 py-2">Unit</th>
              <th className="px-2 py-2">Blocking area</th>
              <th className="px-2 py-2">Question</th>
            </tr>
          </thead>
          <tbody>
            {RETURN_CANT_OWNER_INPUTS.map((input) => (
              <OwnerInputRow key={input.key} input={input} />
            ))}
          </tbody>
        </table>
      </div>

      <article
        data-testid="product-system-return-cant-owner-questions-pending"
        className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-slate-200">Întrebări owner — pending</p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
          {RETURN_CANT_OWNER_QUESTIONS_PENDING.map((q) => (
            <li key={q}>• {q}</li>
          ))}
        </ul>
      </article>

      <div
        data-testid="product-system-return-cant-owner-inputs-safety"
        className="rounded-lg border border-slate-800/80 bg-slate-950/50 px-3 py-2 text-[10px] text-slate-400"
      >
        <p>Workshop only</p>
        <p>No Product Truth live write</p>
        <p>No Pricing activation</p>
        <p>No Work Intake exposure</p>
        <p>No runtime replacement</p>
        <p className="mt-1 text-slate-500">
          Summary: {summary.confirmedCount} confirmed · {summary.pendingCount} pending ·{" "}
          {summary.blockedCount} blocked
        </p>
      </div>
    </section>
  );
}
