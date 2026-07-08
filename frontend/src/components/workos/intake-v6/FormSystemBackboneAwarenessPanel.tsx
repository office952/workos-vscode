import { useState, type ReactNode } from "react";

import { buildFormSystemBackboneAwarenessModel } from "@/lib/intakeV6/formSystemBackboneAwareness";
import type { FormSystemBackboneContract } from "@/lib/intakeV6/intakeV6ModularFormContractTypes";
import type { FormSystemRuntimeStateOverlayInput } from "@/lib/intakeV6/formSystemBackboneRuntimeStateOverlay";

function Badge({ children, tone = "muted" }: { children: ReactNode; tone?: "ok" | "warn" | "bad" | "muted" }) {
  const toneClass =
    tone === "ok"
      ? "border-emerald-600/40 bg-emerald-950/30 text-emerald-200"
      : tone === "warn"
        ? "border-amber-600/40 bg-amber-950/30 text-amber-200"
        : tone === "bad"
          ? "border-red-600/40 bg-red-950/30 text-red-200"
          : "border-slate-700 bg-slate-900/70 text-slate-300";
  return <span className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${toneClass}`}>{children}</span>;
}

function coverageTone(coverage: string): "ok" | "warn" | "bad" | "muted" {
  if (coverage === "covered") return "ok";
  if (coverage === "partial" || coverage === "future") return "warn";
  if (coverage === "missing" || coverage === "not_found") return "bad";
  return "muted";
}

export default function FormSystemBackboneAwarenessPanel({
  backbone,
  runtimeState,
}: {
  backbone?: FormSystemBackboneContract | null;
  runtimeState?: FormSystemRuntimeStateOverlayInput | null;
}) {
  const model = buildFormSystemBackboneAwarenessModel(backbone, runtimeState ?? null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const summaryText = model.available
    ? `${model.root.canonicalCode} · ${model.fields.length} fields · ${model.blockers.length} blockers · ${model.downstreamWriteSafe ? "downstream safe" : "write-intent warning"}`
    : "diagnostic unavailable · Review flow unchanged";

  return (
    <section
      className="mb-4 rounded-lg border border-slate-800 bg-slate-950/35 text-[11px] text-slate-300"
      data-testid="form-system-backbone-awareness-panel"
      data-read-only="true"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 p-3">
        <div>
          <h3 className="text-[13px] font-bold text-slate-100">Form System Backbone</h3>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Read-only diagnostic: component ownership, source/state and Product Truth readiness.
          </p>
          <p className="mt-1 font-mono text-[10px] text-slate-300" data-testid="form-system-backbone-summary">
            {summaryText}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={model.downstreamWriteSafe ? "ok" : "bad"}>
            {model.downstreamWriteSafe ? "downstream write intent: safe" : "downstream write intent: warning"}
          </Badge>
          <button
            type="button"
            className="rounded border border-slate-700 bg-slate-900/80 px-2.5 py-1 text-[10px] font-semibold text-slate-200 hover:border-sky-700 hover:text-sky-100"
            aria-expanded={detailsOpen}
            data-testid="form-system-backbone-toggle"
            onClick={() => setDetailsOpen((value) => !value)}
          >
            {detailsOpen ? "Ascunde detalii" : "Arată detalii"}
          </button>
        </div>
      </div>

      {detailsOpen ? (
        <div className="space-y-3 border-t border-slate-800 p-3" data-testid="form-system-backbone-details">
          {!model.available ? (
            <p className="rounded border border-slate-800 bg-slate-900/50 px-3 py-2 text-slate-400">
              Form System Backbone diagnostic unavailable. Review flow remains unchanged.
            </p>
          ) : (
            <>
          <div className="grid gap-2 md:grid-cols-4" data-testid="form-system-backbone-root-summary">
            <div>
              <p className="text-slate-500">Root</p>
              <p className="font-mono text-[10px] text-slate-100">{model.root.canonicalCode}</p>
            </div>
            <div>
              <p className="text-slate-500">Type</p>
              <p>{model.root.rootType}</p>
            </div>
            <div>
              <p className="text-slate-500">Quote mode</p>
              <p>{model.root.quoteMode}</p>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              <Badge tone={model.root.allowed && !model.root.blocked ? "ok" : "bad"}>
                {model.root.allowed && !model.root.blocked ? "allowed" : "blocked"}
              </Badge>
              {model.root.aliasNormalized ? <Badge tone="warn">alias normalized</Badge> : null}
            </div>
          </div>

          <div data-testid="form-system-backbone-component-coverage">
            <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">Components</p>
            <div className="mb-2 flex flex-wrap gap-1.5">
              <Badge tone="ok">covered {model.coverage.covered}</Badge>
              <Badge tone="warn">partial {model.coverage.partial}</Badge>
              <Badge tone={model.coverage.missing ? "bad" : "muted"}>missing {model.coverage.missing}</Badge>
              <Badge tone="warn">future {model.coverage.future}</Badge>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {model.components.slice(0, 9).map((component) => (
                <Badge key={component.key} tone={coverageTone(component.coverage)}>
                  {component.label}: {component.coverage}
                </Badge>
              ))}
            </div>
          </div>

          <div data-testid="form-system-backbone-fields">
            <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">Fields</p>
            <div className="space-y-1.5">
              {model.fields.slice(0, 6).map((field) => (
                <div key={field.fieldKey} className="rounded border border-slate-800 bg-slate-900/40 px-2.5 py-2">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="font-mono text-[10px] font-bold text-slate-100">{field.fieldKey}</span>
                    <Badge>{field.owningComponent}</Badge>
                    <Badge tone={field.state === "suggested" || field.state === "fallback" || field.state === "hydrated" ? "warn" : field.state === "blocked" || field.state === "missing" ? "bad" : "muted"}>
                      {field.sourceType} / {field.state}
                    </Badge>
                    {field.blockerCode ? <Badge tone="bad">{field.blockerCode}</Badge> : null}
                  </div>
                  <p className="mt-1 font-mono text-[10px] text-slate-500">{field.targetPath}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-2 md:grid-cols-2">
            <div className="rounded border border-amber-700/30 bg-amber-950/15 px-3 py-2" data-testid="form-system-backbone-state-warnings">
              <p className="mb-1 font-semibold text-amber-100">Source/state safety</p>
              <ul className="space-y-1 text-amber-100/90">
                {model.stateWarnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
            <div className="rounded border border-slate-800 bg-slate-900/40 px-3 py-2" data-testid="form-system-backbone-blockers">
              <p className="mb-1 font-semibold text-slate-100">Readiness / blockers ({model.blockers.length})</p>
              {model.blockers.length > 0 ? (
                <ul className="space-y-1 text-slate-300">
                  {model.blockers.slice(0, 4).map((blocker) => (
                    <li key={`${blocker.code}-${blocker.component}`}>
                      <span className="font-mono text-[10px] text-amber-200">{blocker.code}</span>
                      <span className="text-slate-500"> · {blocker.component}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400">No blockers reported by the read-only contract.</p>
              )}
            </div>
          </div>

          <p className="rounded border border-cyan-900/50 bg-cyan-950/15 px-3 py-2 text-cyan-100" data-testid="form-system-backbone-read-only-safety">
            This panel is read-only. It does not price, create quote/order, write Product Truth, start execution, or materialize tasks.
          </p>
            </>
          )}
        </div>
      ) : null}
    </section>
  );
}