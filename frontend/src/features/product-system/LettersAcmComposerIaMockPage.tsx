/**
 * Composer IA mock — Litere ↔ Alucobond.
 * Teaching only: no CostEngine / Offer / DB writes.
 */
import { useMemo, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { ArrowLeft, BadgeCheck, Layers2, Link2 } from "lucide-react";
import {
  buildProductSystemProductDetailPath,
  parseProductSystemTemplateRouteParam,
} from "@/features/product-system/productSystemRouteSync";
import {
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
  ACM_BOXED_OWNER_LABEL_RO,
  isAcmBoxedMountingTemplate,
} from "@/features/product-system/acmBoxedTemplateIdentity";
import {
  isVolumetricLettersTemplate,
  VOLUMETRIC_LETTERS_TEMPLATE_CODES,
} from "@/features/product-system/componentTypeDisplay";
import { LETTERS_ACM_COMPOSITION_TASK_CHAIN } from "@/features/product-system/lettersAcmCompositionTaskOrder";
import {
  formatLettersAcmConnectionPriceRo,
  LETTERS_ACM_CONNECTION_PRICE_SHEET,
  LETTERS_ACM_CONNECTION_PRICES_PAGE_TITLE_RO,
} from "@/features/product-system/lettersAcmCompositionConnectionPrices";
import { buildLettersAcmConnectionPricesPath } from "@/features/product-system/lettersAcmCompositionConnectionPricesRoutes";
import { formatLettersAcmSablonProcessRateRo } from "@/features/product-system/lettersAcmCompositionSablonProcess";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

const LETTERS_V2_CODE =
  [...VOLUMETRIC_LETTERS_TEMPLATE_CODES].find((c) => c.includes("V2")) ??
  "TPL-VOLUMETRIC-LETTERS_V2";

type Peer = {
  code: string;
  labelRo: string;
};

export default function LettersAcmComposerIaMockPage() {
  const { templateCode: rawCode } = useParams<{ templateCode: string }>();
  const pathTemplateCode = parseProductSystemTemplateRouteParam(rawCode ?? null);
  const templateCode = pathTemplateCode ?? rawCode ?? null;

  const allowed =
    !!templateCode &&
    (isAcmBoxedMountingTemplate(templateCode) || isVolumetricLettersTemplate(templateCode));

  const rootIsLetters = !!templateCode && isVolumetricLettersTemplate(templateCode);
  const rootLabel = rootIsLetters ? "Litere volumetrice" : ACM_BOXED_OWNER_LABEL_RO;

  const peer: Peer = useMemo(
    () =>
      rootIsLetters
        ? { code: ACM_BOXED_MOUNTING_TEMPLATE_CODE, labelRo: ACM_BOXED_OWNER_LABEL_RO }
        : { code: LETTERS_V2_CODE, labelRo: "Litere volumetrice" },
    [rootIsLetters],
  );

  const [attached, setAttached] = useState(false);

  if (!templateCode || !allowed) {
    return <Navigate to="/product-system/products" replace />;
  }

  const backPath = buildProductSystemProductDetailPath(templateCode);
  const pricesPath = buildLettersAcmConnectionPricesPath(templateCode);

  return (
    <div className="w-full space-y-6 pb-12" data-testid="letters-acm-composer-ia-mock">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={backPath}
          className="inline-flex items-center gap-1.5 rounded-md border border-wo-border-strong bg-wo-surface-raised px-3 py-2 text-[12px] font-medium text-wo-text-secondary transition-colors hover:border-violet-500/40 hover:text-violet-800 dark:hover:text-violet-100"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Structură
        </Link>
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-wo-text-muted">
          Composer · mock
        </span>
      </header>

      <section className={`${PS_SURFACE_PANEL} border-violet-300 px-5 py-5 dark:border-violet-500/30`}>
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-violet-800 dark:text-violet-300/80">
          Compatibilitate Litere ↔ Alucobond
        </p>
        <h1 className="mt-1 text-[1.45rem] font-semibold text-wo-text-primary">
          Composer — mock IA
        </h1>
        <p className="mt-2 max-w-3xl text-[13px] leading-relaxed text-wo-text-muted">
          Alegi template-ul curent, vezi compatibilul v1, formezi un composit de studiu.
          Fără scriere CostEngine / Ofertă / Execution. Prețurile conexiunii sunt teaching
          readonly.
        </p>
        <p className="mt-2 inline-flex items-center gap-1 rounded border border-amber-400/50 bg-amber-50 px-2 py-1 text-[11px] text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-100">
          Mock — nu calc live
        </p>
      </section>

      <section className="grid gap-3 md:grid-cols-2">
        <div className={`${PS_SURFACE_PANEL} px-4 py-4`}>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
            1. Root (curent)
          </p>
          <p className="mt-2 text-[15px] font-semibold text-wo-text-primary">{rootLabel}</p>
          <p className="mt-1 font-mono text-[11px] text-wo-text-muted">{templateCode}</p>
        </div>
        <div className={`${PS_SURFACE_PANEL} px-4 py-4`}>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
            2. Compatibil v1
          </p>
          <p className="mt-2 text-[15px] font-semibold text-wo-text-primary">{peer.labelRo}</p>
          <p className="mt-1 font-mono text-[11px] text-wo-text-muted">{peer.code}</p>
          <button
            type="button"
            className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-violet-400/50 bg-violet-100/80 px-3 py-1.5 text-[12px] font-semibold text-violet-800 dark:border-violet-500/40 dark:bg-violet-500/15 dark:text-violet-100"
            onClick={() => setAttached(true)}
            data-testid="letters-acm-composer-attach"
          >
            <Link2 className="h-3.5 w-3.5" aria-hidden />
            Atașează → composit
          </button>
        </div>
      </section>

      {attached ? (
        <section
          className={`${PS_SURFACE_PANEL} border-emerald-300 px-5 py-5 dark:border-emerald-500/30`}
          data-testid="letters-acm-composer-composite"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Layers2 className="h-4 w-4 text-emerald-700 dark:text-emerald-300" aria-hidden />
            <h2 className="text-[1.1rem] font-semibold text-wo-text-primary">
              Composit: {rootLabel} + {peer.labelRo}
            </h2>
            <span className="inline-flex items-center gap-1 rounded border border-emerald-400/50 bg-emerald-50 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-800 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-100">
              <BadgeCheck className="h-3 w-3" aria-hidden />
              Contract v1
            </span>
          </div>
          <p className="mt-2 text-[12px] text-wo-text-muted">
            Spine montaj (delta Alucobond) · șablon {formatLettersAcmSablonProcessRateRo()} pe
            outbox layer
          </p>

          <ol className="mt-4 space-y-1.5 text-[12px] text-wo-text-secondary">
            {LETTERS_ACM_COMPOSITION_TASK_CHAIN.map((task) => (
              <li key={task.id}>
                <span className="font-mono text-wo-text-muted">{task.order}.</span> {task.labelRo}
                {task.costNoteRo ? (
                  <span className="ml-2 font-mono text-emerald-700 dark:text-emerald-300/80">
                    {task.costNoteRo}
                  </span>
                ) : null}
              </li>
            ))}
          </ol>

          <div className="mt-5 border-t border-wo-border-strong pt-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
              {LETTERS_ACM_CONNECTION_PRICES_PAGE_TITLE_RO}
            </p>
            <ul className="mt-2 space-y-1 text-[12px] text-wo-text-muted">
              {LETTERS_ACM_CONNECTION_PRICE_SHEET.map((line) => (
                <li key={line.id} className="flex justify-between gap-3">
                  <span>{line.labelRo}</span>
                  <span className="shrink-0 font-mono text-wo-text-primary">
                    {formatLettersAcmConnectionPriceRo(line)}
                  </span>
                </li>
              ))}
            </ul>
            <Link
              to={pricesPath}
              className="mt-3 inline-block text-[11px] text-emerald-700 hover:text-emerald-800 dark:text-emerald-300/90 dark:hover:text-emerald-200"
            >
              Deschide foaia de prețuri →
            </Link>
          </div>
        </section>
      ) : (
        <p className="text-[12px] text-wo-text-muted">
          Apasă „Atașează → composit” ca să vezi spine-ul și prețurile conexiunii.
        </p>
      )}
    </div>
  );
}
