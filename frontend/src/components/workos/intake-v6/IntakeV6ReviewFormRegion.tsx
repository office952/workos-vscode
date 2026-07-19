import type { ReactNode } from "react";

/**
 * Tabs + active panel as one visual form unit.
 * Attention corner slots into the tab chrome (top-right).
 */
export default function IntakeV6ReviewFormRegion({
  tabNav,
  attention,
  children,
}: {
  tabNav: ReactNode;
  attention?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div
      className="rounded-lg border border-[#2A3548]/90 bg-[#0B1220]/55"
      data-testid="intake-v6-review-form-region"
      data-form-leads="true"
    >
      <div
        className="relative flex items-end justify-between gap-2 border-b border-[#2A3548]/80 px-2 pt-1.5 sm:px-3"
        data-testid="intake-v6-review-form-chrome"
      >
        <div className="min-w-0 flex-1 [&_[data-testid=intake-v6-review-tabs]]:mb-0 [&_[data-testid=intake-v6-review-tabs]]:border-b-0">
          {tabNav}
        </div>
        {attention ? (
          <div
            className="mb-1.5 shrink-0 self-center"
            data-testid="intake-v6-review-attention-slot"
          >
            {attention}
          </div>
        ) : null}
      </div>
      <div
        className="px-2.5 py-2.5 sm:px-3 sm:py-3"
        data-testid="intake-v6-review-form-body"
      >
        {children}
      </div>
    </div>
  );
}
