import type { ReactNode } from "react";
import type { CandidateModuleProdusTemplateCode } from "./candidateModuleProdusReadonlyCompleteness";
import { CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE } from "./candidateModuleProdusReadonlyCompleteness";
import {
  MODULE_PRODUS_LABEL,
  PRODUCT_MODULES_SEMANTIC_LABEL,
} from "./productTemplateModulesVocabulary";

/** @deprecated Prefer PRODUCT_MODULES_SEMANTIC_LABEL — kept as alias for imports. */
export const CANDIDATE_MODULE_SEMANTIC_LABEL = PRODUCT_MODULES_SEMANTIC_LABEL;

export const CANDIDATE_MODULE_DISPLAY_LABEL: Partial<Record<CandidateModuleProdusTemplateCode, string>> = {
  "TPL-COMP-LETTER-FACE_v1": "Față",
  "TPL-COMP-LETTER-BACK_v1": "Spate",
  "TPL-COMP-LETTER-RETURN-CANT_v1": "Cant / volum",
  "TPL-COMP-LETTER-LED_v1": "Iluminare",
  "TPL-COMP-LETTER-FINISH_v1": "Finisaj",
  "TPL-COMP-LETTER-MOUNTING_v1": "Montaj",
};

export function candidateModuleProdusDisplayName(templateCode: string): string {
  return (
    CANDIDATE_MODULE_DISPLAY_LABEL[templateCode as CandidateModuleProdusTemplateCode] ??
    templateCode.replace(/^TPL-COMP-LETTER-/, "").replace(/_v1$/, "")
  );
}

export function isCandidateModuleProdusComposer(templateCode: string): boolean {
  return templateCode === CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE;
}

export function truthOwnerLabel(owner: "product_composer" | "component_owned_truth"): string {
  return owner === "product_composer"
    ? "Product Template orchestration"
    : `${MODULE_PRODUS_LABEL} — owned truth`;
}

export function CandidateModuleProdusStatusStrip({
  showWorkIntake = true,
  testIdPrefix = "product-system-candidate-module",
}: {
  showWorkIntake?: boolean;
  testIdPrefix?: string;
}) {
  return (
    <div
      data-testid={`${testIdPrefix}-status-strip`}
      className="sticky top-0 z-10 flex flex-wrap gap-2 rounded-xl border border-cyan-900/50 bg-[#0A0F1A]/95 px-3 py-2.5 text-xs font-semibold backdrop-blur-sm"
    >
      <span className="rounded-md border border-cyan-700/40 bg-cyan-950/40 px-2.5 py-1 text-cyan-200">INACTIVE</span>
      <span className="rounded-md border border-cyan-700/40 bg-cyan-950/40 px-2.5 py-1 text-cyan-200">CANDIDATE</span>
      <span className="rounded-md border border-cyan-700/40 bg-cyan-950/40 px-2.5 py-1 text-cyan-200">READONLY</span>
      <span
        data-testid={`${testIdPrefix}-not-offerable`}
        className="rounded border border-rose-700/40 bg-rose-900/20 px-2 py-0.5 text-rose-200"
      >
        NOT OFFERABLE
      </span>
      {showWorkIntake ? (
        <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-slate-300">
          Not exposed in Work Intake
        </span>
      ) : null}
    </div>
  );
}

export function CandidateModuleProdusSemanticLabel({ testId = "product-system-candidate-module-semantic-label" }: { testId?: string }) {
  return (
    <p data-testid={testId} className="text-[10px] font-bold text-cyan-200/90">
      {CANDIDATE_MODULE_SEMANTIC_LABEL}
    </p>
  );
}

export function ReadonlyLinkButton({
  label,
  testId,
  onClick,
}: {
  label: string;
  testId: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      className="rounded-md border border-slate-700 bg-slate-900/80 px-2 py-1 text-[10px] font-bold text-cyan-200 transition-colors hover:border-cyan-600/40 hover:bg-cyan-950/40"
    >
      {label}
    </button>
  );
}

export function ReadonlyDrawerBanner({
  testId = "product-system-candidate-module-readonly-drawer-banner",
}: {
  testId?: string;
}) {
  return (
    <div
      data-testid={testId}
      className="rounded-md border border-amber-700/50 bg-amber-950/40 px-2.5 py-1.5 text-[10px] font-bold tracking-wide text-amber-100"
    >
      READONLY · NO SAVE · NO WRITE
    </div>
  );
}

export function ReadonlyStatusChip({
  label,
  tone = "neutral",
}: {
  label: string;
  tone?: "neutral" | "cyan" | "rose" | "purple" | "slate";
}) {
  const toneClass =
    tone === "cyan"
      ? "border-cyan-700/40 bg-cyan-950/40 text-cyan-200"
      : tone === "rose"
        ? "border-rose-700/40 bg-rose-900/20 text-rose-200"
        : tone === "purple"
          ? "border-purple-700/40 bg-purple-950/30 text-purple-200"
          : tone === "slate"
            ? "border-slate-700 bg-slate-900 text-slate-300"
            : "border-slate-700 bg-slate-900 text-slate-300";

  return (
    <span className={`rounded border px-1.5 py-0.5 text-[9px] font-bold ${toneClass}`}>{label}</span>
  );
}

export function ReadonlyCardFooter({ children }: { children: ReactNode }) {
  return (
    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/80 pt-2.5">
      {children}
    </div>
  );
}

export function blockedExposureLabel(isBlocked: boolean): "blocked" | "exposed" {
  return isBlocked ? "blocked" : "exposed";
}

export function CandidateModuleProdusInertGuardLabels({
  noWorkIntakeExposure,
  noPricingActivation,
  noProductDefinitionActivation,
  noProductAggregateRuntimeWiring,
  noExecutableOperations,
  noExecutableBom,
  composerCatalogStatus,
}: {
  noWorkIntakeExposure: boolean;
  noPricingActivation: boolean;
  noProductDefinitionActivation: boolean;
  noProductAggregateRuntimeWiring: boolean;
  noExecutableOperations: boolean;
  noExecutableBom: boolean;
  composerCatalogStatus: string;
}) {
  return (
    <div
      data-testid="product-system-candidate-module-inert-guard-labels"
      className="grid gap-2 md:grid-cols-3 text-[10px] text-slate-200"
    >
      <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2 space-y-1">
        <p>
          <span className="text-slate-500">Work Intake exposure:</span>{" "}
          {blockedExposureLabel(noWorkIntakeExposure)}
        </p>
        <p>
          <span className="text-slate-500">Pricing activation:</span> {blockedExposureLabel(noPricingActivation)}
        </p>
        <p>
          <span className="text-slate-500">ProductDefinition runtime:</span>{" "}
          {blockedExposureLabel(noProductDefinitionActivation)}
        </p>
      </div>
      <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2 space-y-1">
        <p>
          <span className="text-slate-500">ProductAggregate runtime:</span>{" "}
          {blockedExposureLabel(noProductAggregateRuntimeWiring)}
        </p>
        <p>
          <span className="text-slate-500">Executable operations:</span> {blockedExposureLabel(noExecutableOperations)}
        </p>
        <p>
          <span className="text-slate-500">Quote/Order/Execution:</span> blocked
        </p>
      </div>
      <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/90 px-3 py-2 space-y-1">
        <p>
          <span className="text-slate-500">Executable BOM:</span> {blockedExposureLabel(noExecutableBom)}
        </p>
        <p>
          <span className="text-slate-500">Catalog status:</span> {composerCatalogStatus}
        </p>
      </div>
    </div>
  );
}

export function ReadonlyCardShell({
  testId,
  children,
  className = "",
  onClick,
  focused = false,
}: {
  testId: string;
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  focused?: boolean;
}) {
  return (
    <article
      data-testid={testId}
      data-focused={focused ? "true" : "false"}
      className={`group rounded-xl border border-[#1E293B] bg-[#111827] p-4 transition-colors hover:border-slate-600/50 ${focused ? "border-cyan-500/50 ring-1 ring-cyan-500/30" : ""} ${className}`}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </article>
  );
}
