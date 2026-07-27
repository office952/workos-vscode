/**
 * Operator spine — Product System ownership only (blank workspace IA).
 * Product Template → Structură produs → Product Compiler → Pregătire.
 * Module produs model = MODULE_MODEL_DEFERRED (not a live spine step).
 * Ofertă / Cost / Execution are never spine steps.
 */
import { ChevronRight } from "lucide-react";
import {
  PRODUCT_SYSTEM_SPINE_STEPS,
  PRODUCT_SYSTEM_SPINE_TAGLINE,
  type ProductSystemSpineStep,
} from "./productTemplateModulesVocabulary";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

const STEP_TONE: Record<ProductSystemSpineStep["id"], string> = {
  template: "border-wo-info/40 bg-wo-info-muted text-wo-info",
  structure: "border-cyan-300 bg-cyan-50 text-cyan-800 dark:border-cyan-700/50 dark:bg-cyan-950/30 dark:text-cyan-100",
  compiler: "border-violet-300 bg-violet-50 text-violet-800 dark:border-violet-700/50 dark:bg-violet-950/30 dark:text-violet-100",
  readiness: "border-sky-300 bg-sky-50 text-sky-800 dark:border-sky-700/50 dark:bg-sky-950/30 dark:text-sky-100",
};

export function ProductSystemSpineBand({
  activeStepId,
  compact = false,
  testId = "product-system-spine-band",
}: {
  activeStepId?: ProductSystemSpineStep["id"];
  compact?: boolean;
  testId?: string;
}) {
  return (
    <section data-testid={testId} className={`${PS_SURFACE_PANEL} px-3 py-2.5`}>
      <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1.5">
        {PRODUCT_SYSTEM_SPINE_STEPS.map((step, i) => {
          const active = activeStepId === step.id;
          return (
            <div key={step.id} className="flex items-center gap-x-1.5">
              <div
                data-testid={`product-system-spine-step-${step.id}`}
                data-active={active ? "true" : "false"}
                className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                  active
                    ? STEP_TONE[step.id]
                    : "border-wo-border-strong bg-wo-surface-inset text-wo-text-secondary"
                }`}
                title={step.hint}
              >
                <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full border border-current/40 text-[9px] font-bold tabular-nums opacity-90">
                  {step.index}
                </span>
                <span>{step.label}</span>
              </div>
              {i < PRODUCT_SYSTEM_SPINE_STEPS.length - 1 ? (
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-wo-text-dim" aria-hidden />
              ) : null}
            </div>
          );
        })}
      </div>
      {!compact ? (
        <p className="mt-2 text-[11px] leading-relaxed text-wo-text-muted">
          {PRODUCT_SYSTEM_SPINE_TAGLINE}
        </p>
      ) : null}
    </section>
  );
}
