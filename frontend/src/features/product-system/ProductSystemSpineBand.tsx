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
  template: "border-purple-700/50 bg-purple-950/30 text-purple-100",
  structure: "border-cyan-700/50 bg-cyan-950/30 text-cyan-100",
  compiler: "border-violet-700/50 bg-violet-950/30 text-violet-100",
  readiness: "border-sky-700/50 bg-sky-950/30 text-sky-100",
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
                    : "border-slate-800 bg-slate-900/50 text-slate-400"
                }`}
                title={step.hint}
              >
                <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full border border-current/40 text-[9px] font-bold tabular-nums opacity-90">
                  {step.index}
                </span>
                <span>{step.label}</span>
              </div>
              {i < PRODUCT_SYSTEM_SPINE_STEPS.length - 1 ? (
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-600" aria-hidden />
              ) : null}
            </div>
          );
        })}
      </div>
      {!compact ? (
        <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
          {PRODUCT_SYSTEM_SPINE_TAGLINE}
        </p>
      ) : null}
    </section>
  );
}
