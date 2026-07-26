/**
 * Decizii operaționale AI — configurable defaults (AI_OPERATIONAL_DEFAULTS_V1).
 */

import { useState } from "react";
import {
  templatePricingRecipeApi,
  type AiOperationalDecisionItem,
} from "@/api/templatePricingRecipe";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

function confidenceChip(c: AiOperationalDecisionItem["confidence"]): string {
  switch (c) {
    case "HIGH":
      return "border-emerald-800/40 text-emerald-200";
    case "MEDIUM":
      return "border-sky-800/40 text-sky-200";
    case "LOW":
      return "border-amber-800/40 text-amber-200";
    default: {
      const _exhaustive: never = c;
      return _exhaustive;
    }
  }
}

export function AiOperationalDefaultsSection({
  items,
  ownershipNote,
  onChanged,
}: {
  items: AiOperationalDecisionItem[];
  ownershipNote?: string;
  onChanged: () => void;
}) {
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!items.length) {
    return (
      <section
        data-testid="template-ai-defaults-section"
        className={`${PS_SURFACE_PANEL} px-4 py-3`}
      >
        <p className="text-[12px] text-slate-500">
          Nicio decizie AI aplicabilă acestui template.
        </p>
      </section>
    );
  }

  return (
    <section
      data-testid="template-ai-defaults-section"
      className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Decizii operaționale AI
          </p>
          <p className="mt-1 max-w-2xl text-[12px] text-slate-400">
            {ownershipNote ||
              "Default-uri configurabile. Precedență: măsurat > owner > catalog > AI. Timpul nu e baza primară."}
          </p>
        </div>
        <span className="rounded border border-sky-900/40 px-2 py-0.5 text-[10px] text-sky-200">
          AI activ · {items.length}
        </span>
      </div>

      {error ? (
        <p className="text-[11px] text-rose-300" data-testid="template-ai-defaults-error">
          {error}
        </p>
      ) : null}

      <div className="overflow-hidden rounded-lg border border-slate-800/70">
        <div className="grid grid-cols-[minmax(0,1.2fr)_minmax(0,0.9fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/70 bg-slate-950/40 px-3 py-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
          <span>Operație</span>
          <span>Formulă / valoare</span>
          <span>Sursă</span>
          <span>Config</span>
        </div>
        {items.map((row) => {
          const draft = drafts[row.decision_id] ?? String(row.resolved_value);
          const saveTarget =
            row.decision_id === "AI_PACK_PRODUCT_BAND" ? "AI_PACK_MEDIUM" : row.decision_id;
          return (
            <div
              key={row.decision_id}
              data-testid={`template-ai-default-row-${row.decision_id}`}
              className="grid grid-cols-[minmax(0,1.2fr)_minmax(0,0.9fr)_minmax(0,0.7fr)_auto] gap-2 border-b border-slate-800/50 px-3 py-2.5 text-[12px] text-slate-200 last:border-b-0"
            >
              <div className="min-w-0">
                <p className="truncate font-medium text-slate-100">{row.display_name_ro}</p>
                <p className="mt-0.5 font-mono text-[10px] text-slate-500">
                  {row.domain} · {row.target_code}
                </p>
                <p className="mt-1 text-[10px] text-slate-500">{row.rationale_ro}</p>
              </div>
              <div>
                <p className="font-mono text-[10px] text-slate-400">{row.formula}</p>
                <p className="mt-0.5 text-[11px] text-slate-200">
                  {row.resolved_value} {row.unit}
                </p>
                {row.quantity_key ? (
                  <p className="mt-0.5 font-mono text-[10px] text-slate-500">
                    qty: {row.quantity_key}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1">
                <span className="rounded border border-sky-900/40 px-1.5 py-0.5 text-[10px] text-sky-200">
                  AI activ
                </span>
                <span
                  className={`ml-1 rounded border px-1.5 py-0.5 text-[10px] ${confidenceChip(row.confidence)}`}
                >
                  {row.confidence}
                </span>
                <p className="text-[10px] text-slate-500">{row.resolved_from}</p>
                {row.has_override ? (
                  <p className="text-[10px] text-amber-200/80">override activ</p>
                ) : null}
              </div>
              <div className="flex min-w-[140px] flex-col gap-1">
                <label className="sr-only" htmlFor={`ai-default-${row.decision_id}`}>
                  Valoare {row.display_name_ro}
                </label>
                <input
                  id={`ai-default-${row.decision_id}`}
                  data-testid={`template-ai-default-input-${row.decision_id}`}
                  type="number"
                  step="any"
                  min={row.minimum}
                  max={row.maximum ?? undefined}
                  value={draft}
                  disabled={!row.configurable || busyId === row.decision_id}
                  onChange={(e) =>
                    setDrafts((prev) => ({ ...prev, [row.decision_id]: e.target.value }))
                  }
                  className="w-full rounded border border-slate-700 bg-slate-950/60 px-2 py-1 text-[11px] text-slate-100"
                />
                <div className="flex gap-1">
                  <button
                    type="button"
                    data-testid={`template-ai-default-save-${row.decision_id}`}
                    disabled={busyId === row.decision_id}
                    className="rounded border border-slate-600 px-2 py-0.5 text-[10px] text-slate-200 hover:bg-slate-800/60"
                    onClick={async () => {
                      setError(null);
                      setBusyId(row.decision_id);
                      try {
                        await templatePricingRecipeApi.putAiDefault(
                          saveTarget,
                          Number(draft),
                        );
                        onChanged();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Salvare eșuată");
                      } finally {
                        setBusyId(null);
                      }
                    }}
                  >
                    Salvează
                  </button>
                  <button
                    type="button"
                    data-testid={`template-ai-default-reset-${row.decision_id}`}
                    disabled={busyId === row.decision_id || !row.has_override}
                    className="rounded border border-slate-700 px-2 py-0.5 text-[10px] text-slate-400 hover:bg-slate-900/50 disabled:opacity-40"
                    onClick={async () => {
                      setError(null);
                      setBusyId(row.decision_id);
                      try {
                        await templatePricingRecipeApi.deleteAiDefault(saveTarget);
                        onChanged();
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Reset eșuat");
                      } finally {
                        setBusyId(null);
                      }
                    }}
                  >
                    Reset
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
