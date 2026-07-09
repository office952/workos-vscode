import type { ReactNode } from "react";
import type {
  IntakeV6ProductTruthPromotionPlannerEntry,
  IntakeV6ProductTruthPromotionPlannerResponse,
} from "@/lib/intakeV6/intakeV6Api";
import { v6 } from "./atoms/intakeV6Presentation";

function Badge({
  children,
  tone = "muted",
}: {
  children: ReactNode;
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

function formatValue(value: string | null | undefined): string {
  return typeof value === "string" && value.trim().length > 0 ? value : "lipsa";
}

function summarizeWriteIntent(intent: Record<string, boolean> | undefined): {
  total: number;
  falseCount: number;
  enabledKeys: string[];
  entries: Array<[string, boolean]>;
} {
  const entries = Object.entries(intent ?? {});
  const falseCount = entries.filter(([, value]) => value === false).length;
  const enabledKeys = entries.filter(([, value]) => value !== false).map(([key]) => key);
  return {
    total: entries.length,
    falseCount,
    enabledKeys,
    entries,
  };
}

function EntryList({
  entries,
  emptyText,
  blocked = false,
  testId,
}: {
  entries: IntakeV6ProductTruthPromotionPlannerEntry[];
  emptyText: string;
  blocked?: boolean;
  testId: string;
}) {
  if (entries.length === 0) {
    return <p className="text-[11px] text-slate-400" data-testid={`${testId}-empty`}>{emptyText}</p>;
  }

  return (
    <div className="space-y-2" data-testid={testId}>
      {entries.map((entry) => (
        <div
          key={entry.entry_key}
          className={`rounded border px-3 py-2 ${blocked ? "border-red-900/40 bg-red-950/10" : "border-slate-800 bg-slate-950/35"}`}
        >
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-mono text-[10px] font-bold text-slate-100">{entry.field_key}</span>
            {entry.identity_key ? <Badge>{entry.identity_key}</Badge> : null}
            <Badge tone={entry.promotion_allowed ? "ok" : blocked ? "bad" : "warn"}>{entry.state}</Badge>
            <Badge tone={entry.promotion_allowed ? "ok" : "warn"}>{entry.value_status}</Badge>
          </div>
          <p className="mt-1 font-mono text-[10px] text-slate-500">{entry.product_truth_path}</p>
          <p className="mt-1 text-[11px] text-slate-300">{entry.reason}</p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-400">
            <span>blockers:</span>
            {entry.blockers.length > 0 ? (
              entry.blockers.map((blocker) => (
                <Badge key={`${entry.entry_key}-${blocker}`} tone="bad">
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
  );
}

export default function ProductTruthPromotionPlannerPanel({
  model,
  loading,
  error,
}: {
  model: IntakeV6ProductTruthPromotionPlannerResponse | null;
  loading: boolean;
  error: string | null;
}) {
  const eligibleEntries = model?.eligible_entries ?? [];
  const blockedEntries = model?.blocked_entries ?? [];
  const plannerBlockers = model?.blockers ?? [];
  const writeIntent = summarizeWriteIntent(model?.downstream_write_intent);
  const summary = model
    ? `${model.workspace_code} · ${eligibleEntries.length} eligible · ${blockedEntries.length} blocked · ${model.read_only ? "read-only" : "unexpected write mode"}`
    : loading
      ? "Loading product truth promotion planner..."
      : error
        ? "Product truth promotion planner unavailable"
        : "No product truth promotion planner available.";

  return (
    <section
      className={`${v6.cardCompact} mb-4 border-slate-800 bg-slate-950/35 text-[11px] text-slate-300`}
      data-testid="product-truth-promotion-planner-panel"
      data-read-only="true"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-[13px] font-bold text-slate-100">Product Truth Promotion Planner</h3>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Read-only diagnostic for what can move from runtime capture into Product Truth later, without writing anything now.
          </p>
          <p className="mt-1 font-mono text-[10px] text-slate-300" data-testid="product-truth-promotion-planner-summary">
            {summary}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={model?.read_only !== false ? "ok" : "bad"}>
            {model?.read_only !== false ? "read only" : "unexpected write mode"}
          </Badge>
          <Badge tone={eligibleEntries.length > 0 ? "ok" : "muted"}>eligible {eligibleEntries.length}</Badge>
          <Badge tone={blockedEntries.length > 0 ? "warn" : "ok"}>blocked {blockedEntries.length}</Badge>
        </div>
      </div>

      {error ? (
        <div className="mt-3 rounded border border-amber-700/30 bg-amber-950/15 px-3 py-2 text-amber-100" data-testid="product-truth-promotion-planner-error">
          Product Truth promotion planner indisponibil momentan. Review flow ramane read-only si neintrerupt. {error}
        </div>
      ) : null}

      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <div className="rounded border border-slate-800 bg-slate-950/40 p-3" data-testid="product-truth-promotion-planner-metadata">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Planner metadata</p>
          <dl className="grid gap-2 text-[11px] sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">planner_version</dt>
              <dd className="font-mono text-slate-100" data-testid="product-truth-promotion-planner-version">
                {model?.planner_version ?? "lipsa"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">read_only</dt>
              <dd className="text-slate-100" data-testid="product-truth-promotion-planner-read-only">
                {model?.read_only !== false ? "true" : "false"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">root_template_code</dt>
              <dd className="font-mono text-slate-100" data-testid="product-truth-promotion-planner-root-template">
                {formatValue(model?.root_template_code)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">product_binding_template_code</dt>
              <dd className="font-mono text-slate-100" data-testid="product-truth-promotion-planner-binding-template">
                {formatValue(model?.product_binding_template_code)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">eligible_entries</dt>
              <dd className="text-slate-100" data-testid="product-truth-promotion-planner-eligible-count">
                {eligibleEntries.length}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">blocked_entries</dt>
              <dd className="text-slate-100" data-testid="product-truth-promotion-planner-blocked-count">
                {blockedEntries.length}
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded border border-slate-800 bg-slate-950/40 p-3" data-testid="product-truth-promotion-planner-write-intent">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Downstream write intent</p>
          <p className="text-[11px] text-slate-300" data-testid="product-truth-promotion-planner-write-intent-summary">
            {writeIntent.total > 0
              ? `${writeIntent.falseCount}/${writeIntent.total} write flags sunt false.`
              : "Niciun flag downstream raportat."}
          </p>
          {writeIntent.enabledKeys.length > 0 ? (
            <p className="mt-2 text-[11px] text-red-200" data-testid="product-truth-promotion-planner-write-intent-alert">
              Unexpected write intent: {writeIntent.enabledKeys.join(", ")}
            </p>
          ) : (
            <p className="mt-2 text-[11px] text-emerald-200" data-testid="product-truth-promotion-planner-write-intent-safe">
              All downstream write flags are false.
            </p>
          )}
          <div className="mt-2 flex flex-wrap gap-1.5" data-testid="product-truth-promotion-planner-write-intent-flags">
            {writeIntent.entries.map(([key, value]) => (
              <Badge key={key} tone={value ? "bad" : "ok"}>
                {key}: {String(value)}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-2">
        <div className="rounded border border-slate-800 bg-slate-950/40 p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Eligible entries</p>
          <EntryList
            entries={eligibleEntries}
            emptyText="0 eligible entries"
            testId="product-truth-promotion-planner-eligible-list"
          />
        </div>

        <div className="rounded border border-slate-800 bg-slate-950/40 p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Blocked entries</p>
          <EntryList
            entries={blockedEntries}
            emptyText="0 blocked entries"
            blocked
            testId="product-truth-promotion-planner-blocked-list"
          />
        </div>
      </div>

      <div className="mt-3 rounded border border-slate-800 bg-slate-950/30 p-3" data-testid="product-truth-promotion-planner-blockers">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Blockers summary</p>
        {plannerBlockers.length > 0 ? (
          <ul className="space-y-1.5 text-[11px] text-slate-200">
            {plannerBlockers.map((blocker, index) => (
              <li key={`${blocker.field_key}-${blocker.identity_key ?? index}`}>
                <span className="font-mono text-red-200">{blocker.field_key}</span>
                {blocker.identity_key ? <span className="font-mono text-slate-400"> · {blocker.identity_key}</span> : null}
                <span className="text-slate-400"> · {blocker.state}</span>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {blocker.blockers.map((code) => (
                    <Badge key={`${blocker.field_key}-${code}`} tone="bad">
                      {code}
                    </Badge>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[11px] text-slate-400" data-testid="product-truth-promotion-planner-blockers-empty">
            No blockers reported by the planner.
          </p>
        )}
      </div>

      <p className="mt-3 rounded border border-cyan-900/50 bg-cyan-950/15 px-3 py-2 text-[10px] text-cyan-100" data-testid="product-truth-promotion-planner-read-only-note">
        Read-only only: nu scrie Product Truth, nu promoveaza, nu confirma, nu porneste downstream write si nu modifica payload-ul workspace-ului.
      </p>
    </section>
  );
}