/**
 * Product System — connection price sheet Litere ↔ Alucobond.
 * Teaching / decision display. Not CostEngine write.
 */
import { Link, Navigate, useParams } from "react-router-dom";
import { ArrowLeft, BadgeCheck, ExternalLink } from "lucide-react";
import {
  buildProductSystemProductDetailPath,
  parseProductSystemTemplateRouteParam,
} from "@/features/product-system/productSystemRouteSync";
import { isAcmBoxedMountingTemplate } from "@/features/product-system/acmBoxedTemplateIdentity";
import { isVolumetricLettersTemplate } from "@/features/product-system/componentTypeDisplay";
import {
  countOwnerLockedConnectionPrices,
  countOwnerVerifiedConnectionPrices,
  decisionBadgeRo,
  formatLettersAcmConnectionPriceRo,
  LETTERS_ACM_CONNECTION_PRICE_SHEET,
  LETTERS_ACM_CONNECTION_PRICES_HELPER_RO,
  LETTERS_ACM_CONNECTION_PRICES_PAGE_TITLE_RO,
} from "@/features/product-system/lettersAcmCompositionConnectionPrices";
import { LETTERS_ACM_COMPOSITION_TASK_CHAIN } from "@/features/product-system/lettersAcmCompositionTaskOrder";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

export default function LettersAcmCompositionConnectionPricesPage() {
  const { templateCode: rawCode } = useParams<{ templateCode: string }>();
  const pathTemplateCode = parseProductSystemTemplateRouteParam(rawCode ?? null);
  const templateCode = pathTemplateCode ?? rawCode ?? null;

  const allowed =
    !!templateCode &&
    (isAcmBoxedMountingTemplate(templateCode) || isVolumetricLettersTemplate(templateCode));

  if (!templateCode || !allowed) {
    return <Navigate to="/product-system/products" replace />;
  }

  const backPath = buildProductSystemProductDetailPath(templateCode);
  const ownerLocked = countOwnerLockedConnectionPrices();
  const ownerVerified = countOwnerVerifiedConnectionPrices();

  return (
    <div
      className="w-full space-y-6 pb-12"
      data-testid="letters-acm-connection-prices-page"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={backPath}
          className="inline-flex items-center gap-1.5 rounded-md border border-wo-border-strong bg-wo-surface-raised px-3 py-2 text-[12px] font-medium text-wo-text-secondary transition-colors hover:border-emerald-500/40 hover:text-emerald-100"
          data-testid="letters-acm-connection-prices-back"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Structură
        </Link>
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-wo-text-muted">
          Conexiune · prețuri
        </span>
      </header>

      <section className={`${PS_SURFACE_PANEL} border-emerald-500/30 px-5 py-5`}>
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-300/80">
          Contract Litere ↔ Alucobond
        </p>
        <h1 className="mt-1 text-[1.45rem] font-semibold text-wo-text-primary">
          {LETTERS_ACM_CONNECTION_PRICES_PAGE_TITLE_RO}
        </h1>
        <p className="mt-2 max-w-3xl text-[13px] leading-relaxed text-wo-text-muted">
          {LETTERS_ACM_CONNECTION_PRICES_HELPER_RO}
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
          <span className="inline-flex items-center gap-1 rounded border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-emerald-100">
            <BadgeCheck className="h-3.5 w-3.5" aria-hidden />
            {ownerLocked} owner blocat
          </span>
          <span className="inline-flex items-center gap-1 rounded border border-sky-500/40 bg-sky-500/10 px-2 py-1 text-sky-100">
            <BadgeCheck className="h-3.5 w-3.5" aria-hidden />
            {ownerVerified} owner verificat (coerent)
          </span>
        </div>
      </section>

      <section className="space-y-2" data-testid="letters-acm-connection-price-rows">
        {LETTERS_ACM_CONNECTION_PRICE_SHEET.map((line) => {
          const isLocked = line.decision === "OWNER_LOCKED";
          return (
            <article
              key={line.id}
              className={`rounded-xl border px-4 py-3 ${
                isLocked
                  ? "border-emerald-500/35 bg-emerald-950/20"
                  : "border-sky-500/30 bg-sky-950/15"
              }`}
              data-testid={`letters-acm-connection-price-${line.id}`}
              data-decision={line.decision}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[11px] text-wo-text-muted">{line.order}.</span>
                    <h2 className="text-[14px] font-semibold text-wo-text-primary">{line.labelRo}</h2>
                    <span
                      className={`rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                        isLocked
                          ? "border-emerald-400/40 bg-emerald-500/15 text-emerald-50"
                          : "border-sky-400/40 bg-sky-500/15 text-sky-50"
                      }`}
                    >
                      {decisionBadgeRo(line.decision)}
                    </span>
                  </div>
                  <p className="mt-1 text-[12px] text-wo-text-muted">
                    Bază qty: {line.qtyBasisRo}
                  </p>
                  <p className="mt-1 text-[12px] leading-relaxed text-wo-text-muted">{line.rationaleRo}</p>
                </div>
                <p
                  className={`shrink-0 font-mono text-[15px] font-semibold ${
                    isLocked ? "text-emerald-200" : "text-sky-200"
                  }`}
                  data-testid={`letters-acm-connection-price-value-${line.id}`}
                >
                  {formatLettersAcmConnectionPriceRo(line)}
                </p>
              </div>
            </article>
          );
        })}
      </section>

      <section className={`${PS_SURFACE_PANEL} px-4 py-4`}>
        <h3 className="text-[12px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
          Ordine atelier (spine comun)
        </h3>
        <ol className="mt-2 space-y-1 text-[12px] text-wo-text-muted">
          {LETTERS_ACM_COMPOSITION_TASK_CHAIN.map((task) => (
            <li key={task.id}>
              <span className="font-mono text-wo-text-muted">{task.order}.</span> {task.labelRo}
              {task.costNoteRo ? (
                <span className="ml-2 font-mono text-emerald-300/80">{task.costNoteRo}</span>
              ) : null}
            </li>
          ))}
        </ol>
        <p className="mt-3 text-[11px] text-wo-text-muted">
          Nucleu ACM (1.5 EUR/ml debitare · 3.0 EUR/ml V-groove · 15 EUR/mp asamblare casetă) și
          materiale Litere/LED/PSU rămân pe template-urile lor — nu pe această foaie.
        </p>
        <div className="mt-3 flex flex-wrap gap-3 text-[11px]">
          <Link
            to={`${backPath}/structure/composer-litere-acm`}
            className="text-violet-300/90 hover:text-violet-200"
          >
            Composer mock →
          </Link>
          <a
            href="/inventory/pricing"
            className="inline-flex items-center gap-1 text-wo-text-muted hover:text-wo-text-primary"
          >
            Pricing Registry
            <ExternalLink className="h-3 w-3" aria-hidden />
          </a>
        </div>
      </section>
    </div>
  );
}
