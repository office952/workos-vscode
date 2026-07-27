/**
 * Downstream channels — secondary links/mentions only.
 * Cost / Ofertă / Execution are NOT Product System spine steps and NOT calculators.
 */
import { Link } from "react-router-dom";
import {
  COST_INTERN_CHANNEL_HELP,
  COST_INTERN_CHANNEL_LABEL,
  DOWNSTREAM_CHANNELS_STRIP_HELP,
  DOWNSTREAM_CHANNELS_STRIP_LABEL,
  EXECUTION_CHANNEL_HELP,
  EXECUTION_CHANNEL_LABEL,
  EXECUTION_DOWNSTREAM_PATH,
  INTAKE_V6_OPERATOR_PATH,
  OFERTA_CLIENT_CHANNEL_HELP,
  OFERTA_CLIENT_CHANNEL_LABEL,
  QUOTES_DOWNSTREAM_PATH,
} from "./productTemplateModulesVocabulary";
import { PS_SURFACE_INSET, PS_SURFACE_PANEL } from "./productSystemSurfaces";

export function ProductSystemOfferCostChannels({
  testId = "product-system-offer-cost-channels",
}: {
  testId?: string;
}) {
  return (
    <section
      data-testid={testId}
      className={`${PS_SURFACE_PANEL} px-3 py-2.5`}
      aria-label={DOWNSTREAM_CHANNELS_STRIP_LABEL}
    >
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <p
          className="text-[10px] font-bold uppercase tracking-wide text-wo-text-muted"
          data-testid="product-system-downstream-strip-label"
        >
          {DOWNSTREAM_CHANNELS_STRIP_LABEL}
        </p>
        <p className="text-[10px] text-wo-text-dim">{DOWNSTREAM_CHANNELS_STRIP_HELP}</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        <div data-testid="product-system-channel-cost" className={`${PS_SURFACE_INSET} px-3 py-2`}>
          <p className="text-[10px] font-bold uppercase tracking-wide text-wo-warning">
            {COST_INTERN_CHANNEL_LABEL}
            <span className="ml-1.5 rounded border border-wo-warning/40 bg-wo-surface-raised px-1 py-0.5 text-[9px] font-semibold normal-case tracking-normal">
              INTERNAL ONLY
            </span>
          </p>
          <p className="mt-1 text-[11px] leading-relaxed text-wo-text-secondary">
            {COST_INTERN_CHANNEL_HELP}
          </p>
          <Link
            to={INTAKE_V6_OPERATOR_PATH}
            data-testid="product-system-channel-cost-link"
            className="mt-1.5 inline-block text-[11px] font-medium text-wo-info underline-offset-2 hover:underline"
          >
            Deschide Intake V6 (operator)
          </Link>
        </div>
        <div data-testid="product-system-channel-offer" className={`${PS_SURFACE_INSET} px-3 py-2`}>
          <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-700 dark:text-emerald-300/90">
            {OFERTA_CLIENT_CHANNEL_LABEL}
            <span className="ml-1.5 rounded border border-wo-border-strong bg-wo-surface-raised px-1 py-0.5 text-[9px] font-semibold normal-case tracking-normal text-wo-text-muted">
              NOT PRICE HERE
            </span>
          </p>
          <p className="mt-1 text-[11px] leading-relaxed text-wo-text-secondary">
            {OFERTA_CLIENT_CHANNEL_HELP}
          </p>
          <Link
            to={QUOTES_DOWNSTREAM_PATH}
            data-testid="product-system-channel-offer-link"
            className="mt-1.5 inline-block text-[11px] font-medium text-wo-info underline-offset-2 hover:underline"
          >
            Deschide Oferte
          </Link>
        </div>
        <div
          data-testid="product-system-channel-execution"
          className={`${PS_SURFACE_INSET} px-3 py-2`}
        >
          <p className="text-[10px] font-bold uppercase tracking-wide text-wo-text-secondary">
            {EXECUTION_CHANNEL_LABEL}
          </p>
          <p className="mt-1 text-[11px] leading-relaxed text-wo-text-secondary">
            {EXECUTION_CHANNEL_HELP}
          </p>
          <Link
            to={EXECUTION_DOWNSTREAM_PATH}
            data-testid="product-system-channel-execution-link"
            className="mt-1.5 inline-block text-[11px] font-medium text-wo-info underline-offset-2 hover:underline"
          >
            Deschide Execuție
          </Link>
        </div>
      </div>
    </section>
  );
}
