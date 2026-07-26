import type { IntakeV6RuntimeCaptureReadModelResponse } from "@/lib/intakeV6/intakeV6Api";

function Badge({
  children,
  tone = "muted",
}: {
  children: React.ReactNode;
  tone?: "ok" | "warn" | "bad" | "muted";
}) {
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

function toneForState(state: string): "ok" | "warn" | "bad" | "muted" {
  if (state === "confirmed") return "ok";
  if (state === "blocked") return "bad";
  if (state === "pending" || state === "suggested" || state === "fallback") return "warn";
  return "muted";
}

export default function FormSystemRuntimeCaptureReadModelPanel({
  model,
  loading,
  error,
}: {
  model: IntakeV6RuntimeCaptureReadModelResponse | null;
  loading: boolean;
  error: string | null;
}) {
  const fields = model?.fields ?? [];
  const blockedCount = fields.filter((field) => field.blockers.length > 0).length;
  const summary = model
    ? `${model.workspace_code} · ${fields.length} fields · ${blockedCount} blocked · ${model.read_only ? "read-only" : "unexpected write mode"}`
    : loading
      ? "Loading runtime capture read model..."
      : error
        ? "Runtime capture read model unavailable"
        : "No runtime capture read model available.";

  return (
    <section
      className="mb-4 rounded-lg border border-slate-800 bg-slate-950/35 text-[11px] text-slate-300"
      data-testid="runtime-capture-read-model-panel"
      data-read-only="true"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 p-3">
        <div>
          <h3 className="text-[13px] font-bold text-wo-text-primary">Runtime Capture Read Model</h3>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Read-only mirror of persisted runtime capture state for Product Truth readiness review.
          </p>
          <p className="mt-1 font-mono text-[10px] text-slate-300" data-testid="runtime-capture-read-model-summary">
            {summary}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={model?.read_only !== false ? "ok" : "bad"}>
            {model?.read_only !== false ? "read only" : "unexpected write mode"}
          </Badge>
          <Badge tone={blockedCount > 0 ? "warn" : "ok"}>blockers {blockedCount}</Badge>
        </div>
      </div>

      {error ? (
        <div className="border-t border-slate-800 px-3 py-2" data-testid="runtime-capture-read-model-error">
          <p className="rounded border border-amber-700/30 bg-amber-950/15 px-3 py-2 text-amber-100">
            Runtime capture read model indisponibil momentan. Review flow ramane read-only si neintrerupt. {error}
          </p>
        </div>
      ) : null}

      <div className="border-t border-slate-800 p-3">
        {loading && fields.length === 0 ? (
          <p className="text-slate-400" data-testid="runtime-capture-read-model-loading">
            Se incarca diagnosticul runtime capture...
          </p>
        ) : fields.length === 0 ? (
          <p className="text-slate-400" data-testid="runtime-capture-read-model-empty">
            Niciun camp runtime capture disponibil inca.
          </p>
        ) : (
          <div className="space-y-2" data-testid="runtime-capture-read-model-fields">
            {fields.map((field) => (
              <div key={field.field_key} className="rounded border border-slate-800 bg-slate-900/40 px-3 py-2">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="font-mono text-[10px] font-bold text-wo-text-primary">{field.field_key}</span>
                  <Badge tone={toneForState(field.state)}>{field.state}</Badge>
                  <Badge tone={field.ready_for_product_truth ? "ok" : "warn"}>
                    {field.ready_for_product_truth ? "ready for product truth" : "not ready"}
                  </Badge>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-400">
                  <span>blockers:</span>
                  {field.blockers.length > 0 ? (
                    field.blockers.map((blocker) => (
                      <Badge key={`${field.field_key}-${blocker}`} tone="bad">
                        {blocker}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-emerald-200">none</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}