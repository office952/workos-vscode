/**
 * Capac spate — dedicated structure-step page (model = Vizual față / Volum).
 * Visual identity + explanatory directional documentation.
 * No calculation / Product Truth write.
 */
import { Link, Navigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BookOpen,
  BoxSelect,
  ExternalLink,
  Layers,
  Route,
  Scissors,
  ShieldAlert,
} from "lucide-react";
import {
  LETTERS_BACK_FOREX_10MM_DISPLAY_NAME,
  LETTERS_BACK_FOREX_10MM_REGISTRY_CODE,
  LETTERS_BACK_FOREX_PROCESS_STEPS,
  LETTERS_BACK_STRUCTURE_DISPLAY_NAME,
} from "@/lib/materials/lettersBackForexMaterialDisplay";
import {
  buildMaterialPriceVerifyHref,
  MATERIAL_PRICE_VERIFY_LABEL_RO,
} from "@/lib/pricing/materialPriceVerifyLink";
import { isVolumetricLettersTemplate } from "@/features/product-system/componentTypeDisplay";
import {
  buildProductSystemProductDetailPath,
  parseProductSystemTemplateRouteParam,
} from "@/features/product-system/productSystemRouteSync";
import {
  LETTERS_BACK_CALC_CARDS,
  LETTERS_BACK_DOC_ROLE_RO,
  LETTERS_BACK_DOC_SECTIONS,
  LETTERS_BACK_DOC_SOURCES,
  type LettersBackCalcCard,
} from "@/features/product-system/lettersBackForexStructureDocumentation";
import { LettersStructurePrincipalTaskOrderPanel } from "@/features/product-system/LettersStructurePrincipalTaskOrderPanel";
import { LETTERS_STRUCTURE_STEP_CAPAC_SPATE } from "@/features/product-system/lettersStructureDetailRoutes";
import { PS_SURFACE_PANEL, PS_SURFACE_INSET } from "./productSystemSurfaces";

function CalcCardIcon({ id }: { id: LettersBackCalcCard["id"] }) {
  if (id === "material_consumption") {
    return <BoxSelect className="h-7 w-7" aria-hidden />;
  }
  return <Route className="h-7 w-7" aria-hidden />;
}

function MaterialPriceVerifyLink({
  materialCode,
  testId,
  className = "",
}: {
  materialCode: string;
  testId?: string;
  className?: string;
}) {
  return (
    <Link
      to={buildMaterialPriceVerifyHref(materialCode)}
      className={`inline-flex items-center gap-1 text-[11px] font-medium text-cyan-300/90 underline-offset-2 transition-colors hover:text-cyan-200 hover:underline ${className}`}
      data-testid={testId}
    >
      {MATERIAL_PRICE_VERIFY_LABEL_RO}
      <ExternalLink className="h-3 w-3" aria-hidden />
    </Link>
  );
}

function PricingVerifyLink({
  href,
  label,
  testId,
}: {
  href: string;
  label: string;
  testId?: string;
}) {
  return (
    <Link
      to={href}
      className="inline-flex items-center gap-1 text-[11px] font-medium text-cyan-300/90 underline-offset-2 transition-colors hover:text-cyan-200 hover:underline"
      data-testid={testId}
    >
      {label}
      <ExternalLink className="h-3 w-3" aria-hidden />
    </Link>
  );
}

export default function LettersBackForexStructureDetailPage() {
  const { templateCode: rawCode } = useParams<{ templateCode: string }>();
  const templateCode = parseProductSystemTemplateRouteParam(rawCode);
  const pathTemplateCode = (() => {
    try {
      return rawCode ? decodeURIComponent(rawCode) : null;
    } catch {
      return rawCode ?? null;
    }
  })();

  if (!templateCode || !isVolumetricLettersTemplate(templateCode) || !pathTemplateCode) {
    return <Navigate to="/product-system/products" replace />;
  }

  const backPath = buildProductSystemProductDetailPath(pathTemplateCode);

  return (
    <div
      className="w-full space-y-6 pb-12"
      data-testid="letters-back-structure-detail"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={backPath}
          className="inline-flex items-center gap-1.5 rounded-md border border-wo-border-strong bg-wo-surface-raised px-3 py-2 text-[12px] font-medium text-wo-text-secondary transition-colors hover:border-amber-500/40 hover:text-amber-100"
          data-testid="letters-back-structure-detail-back"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Structură
        </Link>
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-wo-text-muted">
          Litere · pas 3 / 5
        </span>
      </header>

      <section
        className="relative overflow-hidden rounded-2xl border border-amber-500/35 bg-wo-surface-raised"
        data-testid="letters-back-structure-detail-hero"
      >
        <div
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_12%_0%,rgba(245,158,11,0.26),transparent_52%),radial-gradient(ellipse_at_88%_70%,rgba(251,191,36,0.10),transparent_48%)]"
          aria-hidden
        />
        <div className="relative grid gap-8 px-6 py-7 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:items-end lg:px-8 lg:py-8">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="font-mono text-[12px] font-bold tabular-nums tracking-[0.22em] text-amber-300/90">
                03
              </p>
              <h1 className="text-[12px] font-bold uppercase tracking-[0.22em] text-amber-300">
                Capac spate
              </h1>
              <span className="rounded-md border border-amber-500/40 bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-100">
                Forex
              </span>
            </div>
            <p
              className="mt-4 max-w-3xl text-[2rem] font-semibold leading-[1.15] tracking-tight text-slate-50 sm:text-[2.35rem]"
              data-testid="letters-back-structure-detail-material"
            >
              {LETTERS_BACK_STRUCTURE_DISPLAY_NAME}
            </p>
            <p className="mt-3 font-mono text-[12px] text-amber-200/55">
              {LETTERS_BACK_FOREX_10MM_REGISTRY_CODE}
            </p>
          </div>
          <p
            className="max-w-xl border-t border-amber-500/25 pt-4 text-[13px] leading-relaxed text-amber-100/80 lg:border-t-0 lg:border-l lg:pl-8 lg:pt-0"
            data-testid="letters-back-structure-detail-role"
          >
            {LETTERS_BACK_DOC_ROLE_RO}
          </p>
        </div>
      </section>

      <section
        className="grid gap-4 lg:grid-cols-3"
        data-testid="letters-back-structure-detail-identity"
      >
        <div
          className={`${PS_SURFACE_PANEL} flex flex-col px-5 py-5`}
          data-testid="letters-back-structure-detail-material-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/15 text-amber-300">
              <Layers className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-400/90">
              Material
            </p>
          </div>
          <p className="mt-4 text-[16px] font-semibold leading-snug text-wo-text-primary">
            {LETTERS_BACK_FOREX_10MM_DISPLAY_NAME}
          </p>
          <p className="mt-2 inline-flex w-fit rounded-md border border-amber-800/40 bg-amber-950/30 px-2 py-1 font-mono text-[10px] text-amber-200/70">
            {LETTERS_BACK_FOREX_10MM_REGISTRY_CODE}
          </p>
          <div className="mt-auto pt-4">
            <MaterialPriceVerifyLink
              materialCode={LETTERS_BACK_FOREX_10MM_REGISTRY_CODE}
              testId="letters-back-structure-detail-material-price-verify"
            />
          </div>
        </div>

        <div
          className={`${PS_SURFACE_PANEL} px-5 py-5`}
          data-testid="letters-back-structure-detail-cnc-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/15 text-amber-300">
              <Scissors className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-400/90">
              Procese CNC
            </p>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {LETTERS_BACK_FOREX_PROCESS_STEPS.map((step, index) => (
              <div
                key={step.id}
                className="rounded-xl border border-amber-500/25 bg-amber-500/[0.07] px-3.5 py-3.5"
                data-testid={`letters-back-structure-detail-cnc-step-${step.id}`}
              >
                <p className="font-mono text-[22px] font-bold tabular-nums text-amber-300/90">
                  {index + 1}
                </p>
                <p className="mt-1.5 text-[13px] font-semibold text-wo-text-primary">{step.labelRo}</p>
                <p className="mt-1 text-[10px] text-wo-text-muted">
                  {step.required ? "obligatoriu" : "opțional · default fără"}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div
          className={`${PS_SURFACE_PANEL} flex flex-col px-5 py-5`}
          data-testid="letters-back-structure-detail-boundary-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/15 text-amber-300">
              <ShieldAlert className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-400/90">
              Nu confunda
            </p>
          </div>
          <ul className="mt-4 space-y-2 text-[12px] leading-snug text-wo-text-secondary">
            <li className={`${PS_SURFACE_INSET} px-3 py-2`}>Nu panou ACM / Dibond</li>
            <li className={`${PS_SURFACE_INSET} px-3 py-2`}>Nu șablon montaj 3 mm</li>
            <li className={`${PS_SURFACE_INSET} px-3 py-2`}>
              Nu badge CNC processable pe Forex
            </li>
            <li className={`${PS_SURFACE_INSET} px-3 py-2`}>
              LED se montează pe acest spate — pasul 4
            </li>
          </ul>
        </div>
      </section>

      <LettersStructurePrincipalTaskOrderPanel
        stepId={LETTERS_STRUCTURE_STEP_CAPAC_SPATE}
        accent="amber"
        testIdPrefix="letters-back-structure-detail"
      />

      <section className="space-y-4" data-testid="letters-back-structure-detail-calc">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-[12px] font-bold uppercase tracking-[0.16em] text-amber-300/90">
            Cum calculăm
          </h2>
          <span className="text-[11px] text-wo-text-muted">metodă owner · fără preț duplicat</span>
        </div>
        <div className="grid gap-5 xl:grid-cols-2">
          {LETTERS_BACK_CALC_CARDS.map((card) => (
            <article
              key={card.id}
              className="relative overflow-hidden rounded-2xl border border-amber-500/40 bg-wo-surface-raised"
              data-testid={`letters-back-structure-detail-calc-${card.id}`}
              data-importance={card.importance}
            >
              <div
                className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_0%_0%,rgba(245,158,11,0.14),transparent_50%)]"
                aria-hidden
              />
              <div className="relative flex h-full flex-col px-6 py-6 lg:px-7 lg:py-7">
                <div className="flex items-start gap-4">
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-amber-400/35 bg-amber-500/20 text-amber-100">
                    <CalcCardIcon id={card.id} />
                  </span>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-400/90">
                      {card.subtitleRo}
                    </p>
                    <h3 className="mt-1.5 text-[1.45rem] font-semibold tracking-tight text-slate-50">
                      {card.titleRo}
                    </h3>
                  </div>
                </div>

                <p
                  className="mt-5 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3.5 font-mono text-[13px] leading-relaxed text-amber-100"
                  data-testid={`letters-back-structure-detail-calc-${card.id}-formula`}
                >
                  {card.formulaRo}
                </p>

                <ol className="mt-5 space-y-2.5">
                  {card.stepsRo.map((step, index) => (
                    <li key={step} className="flex gap-3 text-[13px] leading-relaxed text-wo-text-secondary">
                      <span className="font-mono text-[12px] font-bold tabular-nums text-amber-300/85">
                        {index + 1}.
                      </span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>

                <div className="mt-5 grid flex-1 gap-3 sm:grid-cols-2">
                  <div className={`${PS_SURFACE_INSET} px-3.5 py-3`}>
                    <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
                      Ieșiri
                    </p>
                    <ul className="mt-2 space-y-1.5">
                      {card.outputsRo.map((line) => (
                        <li key={line} className="text-[11px] leading-snug text-wo-text-muted">
                          {line}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className={`${PS_SURFACE_INSET} px-3.5 py-3`}>
                    <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
                      Nu așa
                    </p>
                    <ul className="mt-2 space-y-1.5">
                      {card.notThisRo.map((line) => (
                        <li key={line} className="text-[11px] leading-snug text-wo-text-muted">
                          {line}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-amber-500/20 pt-4">
                  <p className="max-w-md text-[12px] leading-relaxed text-wo-text-muted">
                    {card.priceNoteRo}
                  </p>
                  <PricingVerifyLink
                    href={card.verifyHref}
                    label={card.verifyLabelRo}
                    testId={`letters-back-structure-detail-calc-${card.id}-price-verify`}
                  />
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className={`${PS_SURFACE_PANEL} overflow-hidden`}
        data-testid="letters-back-structure-detail-document"
      >
        <div className="flex flex-wrap items-center gap-2 border-b border-wo-border-subtle px-6 py-4">
          <BookOpen className="h-4 w-4 text-amber-300" aria-hidden />
          <h2 className="text-[12px] font-bold uppercase tracking-[0.14em] text-wo-text-primary">
            Document componentă
          </h2>
          <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.12em] text-wo-text-muted">
            explicativ · direcțional
          </span>
        </div>

        <ol
          className="grid gap-4 p-4 sm:p-5 xl:grid-cols-2"
          data-testid="letters-back-structure-detail-doc-sections"
        >
          {LETTERS_BACK_DOC_SECTIONS.map((section, index) => (
            <li
              key={section.id}
              className="rounded-xl border border-wo-border-subtle bg-wo-surface-inset px-5 py-5"
              data-testid={`letters-back-structure-detail-doc-${section.id}`}
            >
              <div className="flex items-baseline gap-2.5">
                <span className="font-mono text-[12px] font-bold tabular-nums text-amber-400/80">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="text-[14px] font-semibold text-wo-text-primary">{section.titleRo}</h3>
              </div>
              <p className="mt-3 max-w-prose text-[13px] leading-relaxed text-wo-text-muted">
                {section.bodyRo}
              </p>
              {section.bulletsRo && section.bulletsRo.length > 0 ? (
                <ul className="mt-3.5 space-y-2">
                  {section.bulletsRo.map((bullet) => (
                    <li
                      key={bullet}
                      className={`${PS_SURFACE_INSET} px-3 py-2 text-[12px] leading-snug text-wo-text-secondary`}
                    >
                      {bullet}
                    </li>
                  ))}
                </ul>
              ) : null}
            </li>
          ))}
        </ol>

        <div
          className="border-t border-wo-border-subtle bg-wo-surface-inset px-6 py-4"
          data-testid="letters-back-structure-detail-doc-sources"
        >
          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
            Surse owner / lock
          </p>
          <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
            {LETTERS_BACK_DOC_SOURCES.map((source) => (
              <li key={source.path} className="text-[11px] leading-snug text-wo-text-muted">
                <span className="text-wo-text-muted">{source.labelRo}</span>
                <span className="mx-1.5 text-slate-700">·</span>
                <span className="font-mono text-[10px] text-wo-text-dim">{source.path}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
