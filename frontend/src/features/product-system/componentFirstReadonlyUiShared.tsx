import type { ReactNode } from "react";
import type { ComponentFirstTemplateCode } from "./componentFirstReadonlyCompleteness";
import { COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE } from "./componentFirstReadonlyCompleteness";

export const COMPONENT_FIRST_SEMANTIC_LABEL = "1 Product Composer + 6 Component Templates";

export const COMPONENT_FIRST_DISPLAY_LABEL: Partial<Record<ComponentFirstTemplateCode, string>> = {
  "TPL-COMP-LETTER-FACE_v1": "Face",
  "TPL-COMP-LETTER-BACK_v1": "Back",
  "TPL-COMP-LETTER-RETURN-CANT_v1": "Return/Cant",
  "TPL-COMP-LETTER-LED_v1": "LED",
  "TPL-COMP-LETTER-FINISH_v1": "Finish",
  "TPL-COMP-LETTER-MOUNTING_v1": "Mounting",
};

export function componentFirstDisplayName(templateCode: string): string {
  return (
    COMPONENT_FIRST_DISPLAY_LABEL[templateCode as ComponentFirstTemplateCode] ??
    templateCode.replace(/^TPL-COMP-LETTER-/, "").replace(/_v1$/, "")
  );
}

export function isComponentFirstComposer(templateCode: string): boolean {
  return templateCode === COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE;
}

export function truthOwnerLabel(owner: "product_composer" | "component_owned_truth"): string {
  return owner === "product_composer" ? "Product composer orchestration" : "Component-owned truth";
}

export function ComponentFirstStatusStrip({
  showWorkIntake = true,
  testIdPrefix = "product-system-component-first",
}: {
  showWorkIntake?: boolean;
  testIdPrefix?: string;
}) {
  return (
    <div
      data-testid={`${testIdPrefix}-status-strip`}
      className="sticky top-0 z-10 flex flex-wrap gap-1.5 rounded-lg border border-cyan-900/50 bg-[#0A0F1A]/95 px-2.5 py-2 text-[10px] font-bold backdrop-blur-sm"
    >
      <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">INACTIVE</span>
      <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">CANDIDATE</span>
      <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">READONLY</span>
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

export function ComponentFirstSemanticLabel({ testId = "product-system-component-first-semantic-label" }: { testId?: string }) {
  return (
    <p data-testid={testId} className="text-[10px] font-bold text-cyan-200/90">
      {COMPONENT_FIRST_SEMANTIC_LABEL}
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

export function ReadonlyCardShell({
  testId,
  children,
  className = "",
  onClick,
}: {
  testId: string;
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <article
      data-testid={testId}
      className={`rounded-lg border border-[#1E293B] bg-[#111827] p-3 transition-colors ${className}`}
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
