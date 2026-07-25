import type { ReactNode } from "react";

/**
 * Variant B shell: optional product strip + workbench (top horizontal domain nav + panel) + sticky offer.
 * Configurare omits the identity strip so domain nav / form lead; presentation only.
 * Domain nav is a compact horizontal strip at the top of the Configurare form card.
 */
export default function IntakeV6ReviewWorkbenchLayout({
  productStrip = null,
  domainNav,
  attention,
  formBody,
  formFooter,
  offerRail,
  mobileOfferBar,
}: {
  productStrip?: ReactNode;
  domainNav: ReactNode;
  attention?: ReactNode;
  formBody: ReactNode;
  formFooter?: ReactNode;
  offerRail: ReactNode;
  mobileOfferBar?: ReactNode;
}) {
  const showTopStrip = Boolean(productStrip) || Boolean(attention);

  return (
    <div data-testid="intake-v6-review-workbench" data-workbench-variant="b">
      {showTopStrip ? (
        <div
          className="mb-2 flex flex-wrap items-center gap-2"
          data-testid="intake-v6-review-product-strip"
        >
          {productStrip ? <div className="min-w-0 flex-1">{productStrip}</div> : null}
          {attention ? (
            <div className="shrink-0" data-testid="intake-v6-review-attention-slot">
              {attention}
            </div>
          ) : null}
        </div>
      ) : null}

      {mobileOfferBar ? (
        <div className="mb-2 lg:hidden" data-testid="intake-v6-review-price-spine-mobile">
          {mobileOfferBar}
        </div>
      ) : null}

      <div
        className="grid items-start gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(280px,320px)] xl:grid-cols-[minmax(0,1fr)_minmax(300px,340px)]"
        data-testid="intake-v6-review-layout"
      >
        <div className="min-w-0 lg:flex lg:min-h-0 lg:flex-col">
          <div
            className="min-h-[12rem] overflow-hidden rounded-lg border border-[#2A3548]/90 bg-[#0B1220]/55"
            data-testid="intake-v6-review-form-region"
            data-form-leads="true"
            data-workbench="true"
          >
            <div
              className="flex min-h-0 flex-col"
              data-testid="intake-v6-review-form-chrome"
              data-domain-nav-placement="top"
            >
              <div
                className="border-b border-[#2A3548]/80 bg-[#0A0F1A]/40"
                data-testid="intake-v6-review-domain-nav-shell"
                data-domain-nav-placement="top"
              >
                {domainNav}
              </div>
              <div
                className="min-w-0 px-2.5 py-2.5 sm:px-3 sm:py-3"
                data-testid="intake-v6-review-form-body"
              >
                {formBody}
              </div>
            </div>
          </div>
          {formFooter}
        </div>

        <div
          className="hidden lg:block lg:sticky lg:top-4 lg:self-start"
          data-testid="intake-v6-live-calculation-sticky-shell"
        >
          {offerRail}
        </div>
      </div>
    </div>
  );
}
