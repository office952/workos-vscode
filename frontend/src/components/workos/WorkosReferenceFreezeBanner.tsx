import {
  WORKOS_BOUNDED_EXCEPTION_BODY_RO,
  WORKOS_REFERENCE_FREEZE_BODY_RO,
  WORKOS_REFERENCE_FREEZE_CODE,
  WORKOS_REFERENCE_FREEZE_LABEL_RO,
} from "@/lib/workosReferenceFreezePresentation";

type WorkosReferenceFreezeBannerProps = {
  testId?: string;
  showBoundedException?: boolean;
};

export function WorkosReferenceFreezeBanner({
  testId = "workos-reference-freeze-banner",
  showBoundedException = false,
}: WorkosReferenceFreezeBannerProps) {
  return (
    <div
      className="flex items-start gap-2 rounded-lg border border-wo-border-subtle bg-wo-surface-inset px-3 py-2.5"
      data-testid={testId}
    >
      <div className="space-y-1 text-[12px] leading-relaxed text-wo-text-secondary">
        <p className="flex flex-wrap items-center gap-2">
          <span
            className="rounded border border-wo-border-strong px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-wo-text-primary"
            data-testid="workos-reference-freeze-status"
          >
            {WORKOS_REFERENCE_FREEZE_LABEL_RO}
          </span>
          <span
            className="font-mono text-[10px] text-wo-text-muted"
            data-testid="workos-reference-freeze-code"
          >
            {WORKOS_REFERENCE_FREEZE_CODE}
          </span>
        </p>
        <p data-testid="workos-reference-freeze-body">{WORKOS_REFERENCE_FREEZE_BODY_RO}</p>
        {showBoundedException ? (
          <p data-testid="workos-bounded-exception-note">{WORKOS_BOUNDED_EXCEPTION_BODY_RO}</p>
        ) : null}
      </div>
    </div>
  );
}
