import type { ReactNode } from "react";

/**
 * Tabs + active panel as one visual form unit.
 * Workbench mode: horizontal domain nav along the top, panel below.
 * Legacy mode: horizontal tab chrome on top.
 */
export default function IntakeV6ReviewFormRegion({
  tabNav,
  attention,
  children,
  layout = "horizontal",
}: {
  tabNav: ReactNode;
  attention?: ReactNode;
  children: ReactNode;
  layout?: "horizontal" | "workbench";
}) {
  if (layout === "workbench") {
    return (
      <div
        className="rounded-lg border border-wo-border-strong/90 bg-wo-surface-input/55"
        data-testid="intake-v6-review-form-region"
        data-form-leads="true"
        data-workbench="true"
      >
        <div
          className="flex min-h-[18rem] flex-col gap-0"
          data-testid="intake-v6-review-form-chrome"
          data-domain-nav-placement="top"
        >
          <aside
            className="border-b border-wo-border-strong/80 bg-wo-surface-inset/40"
            data-testid="intake-v6-review-domain-nav-shell"
            data-domain-nav-placement="top"
          >
            {tabNav}
          </aside>
          <div
            className="min-w-0 flex-1 px-2.5 py-2.5 sm:px-3 sm:py-3"
            data-testid="intake-v6-review-form-body"
          >
            {attention ? (
              <div className="mb-2 flex justify-end" data-testid="intake-v6-review-attention-slot">
                {attention}
              </div>
            ) : null}
            {children}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border border-wo-border-strong/90 bg-wo-surface-input/55"
      data-testid="intake-v6-review-form-region"
      data-form-leads="true"
    >
      <div
        className="relative flex items-end justify-between gap-2 border-b border-wo-border-strong/80 px-2 pt-1.5 sm:px-3"
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
