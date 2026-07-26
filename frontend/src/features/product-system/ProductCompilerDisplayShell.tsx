/**
 * Display-only Product Compiler chrome — no API / compiler behavior changes.
 */
import {
  PRODUCT_COMPILER_DEFINITION_STAGE_LABEL,
  PRODUCT_COMPILER_GRAPH_STAGE_LABEL,
  PRODUCT_COMPILER_LABEL,
  PRODUCT_COMPILER_NO_PRICE_HELP,
  PRODUCT_COMPILER_RELATION_HELP,
  PRODUCT_MODULES_SEMANTIC_LABEL,
} from "./productTemplateModulesVocabulary";

export type ProductCompilerDisplayStage = "definition" | "graph" | "both";

export function ProductCompilerDisplayShell({
  stage = "both",
  compact = false,
}: {
  stage?: ProductCompilerDisplayStage;
  compact?: boolean;
}) {
  const stageLabel =
    stage === "definition"
      ? PRODUCT_COMPILER_DEFINITION_STAGE_LABEL
      : stage === "graph"
        ? PRODUCT_COMPILER_GRAPH_STAGE_LABEL
        : PRODUCT_COMPILER_LABEL;

  return (
    <div
      className={
        compact
          ? "rounded-lg border border-cyan-900/40 bg-cyan-950/20 px-3 py-2"
          : "rounded-xl border border-cyan-900/40 bg-cyan-950/20 px-4 py-3"
      }
      data-testid="product-compiler-display-shell"
      data-compiler-stage={stage}
    >
      <p className="text-[10px] font-bold uppercase tracking-wide text-cyan-300/90">{stageLabel}</p>
      <p className={`text-slate-200 ${compact ? "mt-0.5 text-[11px]" : "mt-1 text-[12px] font-semibold"}`}>
        {PRODUCT_MODULES_SEMANTIC_LABEL}
      </p>
      <p className={`text-slate-400 ${compact ? "mt-0.5 text-[10px]" : "mt-1 text-[11px]"}`}>
        {PRODUCT_COMPILER_RELATION_HELP}
      </p>
      {!compact ? (
        <p className="mt-1 text-[10px] text-slate-500">{PRODUCT_COMPILER_NO_PRICE_HELP}</p>
      ) : null}
      {stage === "both" ? (
        <div className="mt-2 flex flex-wrap gap-1.5" data-testid="product-compiler-stage-chips">
          <span className="rounded border border-cyan-800/50 bg-cyan-950/40 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-cyan-200/90">
            {PRODUCT_COMPILER_DEFINITION_STAGE_LABEL}
          </span>
          <span className="rounded border border-violet-800/50 bg-violet-950/40 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-violet-200/90">
            {PRODUCT_COMPILER_GRAPH_STAGE_LABEL}
          </span>
        </div>
      ) : null}
    </div>
  );
}
