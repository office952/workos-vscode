/**
 * Sistem LED — dedicated structure-step page (model = Vizual față / Volum / Spate).
 * Visual identity + explanatory directional documentation.
 * No calculation / Product Truth write.
 */
import { Link, Navigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BookOpen,
  ExternalLink,
  Layers,
  Lightbulb,
  Zap,
  Wrench,
} from "lucide-react";
import {
  LETTERS_LED_FAMILY_LABEL_RO,
  LETTERS_LED_MODULE_CODE,
  LETTERS_LED_MODULE_DISPLAY_NAME,
  LETTERS_LED_MOUNT_NOTE_RO,
  LETTERS_LED_PROCESS_STEPS,
  LETTERS_LED_PSU_SELECTOR_CODE,
  LETTERS_LED_PSU_VARIANTS,
  LETTERS_LED_STRIP_CODE,
  LETTERS_LED_STRIP_DISPLAY_NAME,
  LETTERS_LED_STRUCTURE_DISPLAY_NAME,
} from "@/lib/materials/lettersLedMaterialDisplay";
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
  LETTERS_LED_CALC_CARDS,
  LETTERS_LED_DOC_ROLE_RO,
  LETTERS_LED_DOC_SECTIONS,
  LETTERS_LED_DOC_SOURCES,
  LETTERS_LED_PITCH_MM,
  type LettersLedCalcCard,
} from "@/features/product-system/lettersLedStructureDocumentation";
import { LettersStructurePrincipalTaskOrderPanel } from "@/features/product-system/LettersStructurePrincipalTaskOrderPanel";
import { LETTERS_STRUCTURE_STEP_SISTEM_LED } from "@/features/product-system/lettersStructureDetailRoutes";
import { PS_SURFACE_PANEL, PS_SURFACE_INSET } from "./productSystemSurfaces";

function CalcCardIcon({ id }: { id: LettersLedCalcCard["id"] }) {
  if (id === "module_count") {
    return <Lightbulb className="h-7 w-7" aria-hidden />;
  }
  return <Zap className="h-7 w-7" aria-hidden />;
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

export default function LettersLedStructureDetailPage() {
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
    <div className="w-full space-y-6 pb-12" data-testid="letters-led-structure-detail">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={backPath}
          className="inline-flex items-center gap-1.5 rounded-md border border-wo-border-strong bg-wo-surface-raised px-3 py-2 text-[12px] font-medium text-wo-text-secondary transition-colors hover:border-yellow-500/40 hover:text-yellow-100"
          data-testid="letters-led-structure-detail-back"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Structură
        </Link>
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-wo-text-muted">
          Litere · pas 4 / 5
        </span>
      </header>

      <section
        className="relative overflow-hidden rounded-2xl border border-yellow-500/35 bg-wo-surface-raised"
        data-testid="letters-led-structure-detail-hero"
      >
        <div
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_12%_0%,rgba(234,179,8,0.26),transparent_52%),radial-gradient(ellipse_at_88%_70%,rgba(250,204,21,0.10),transparent_48%)]"
          aria-hidden
        />
        <div className="relative grid gap-8 px-6 py-7 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:items-end lg:px-8 lg:py-8">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="font-mono text-[12px] font-bold tabular-nums tracking-[0.22em] text-yellow-300/90">
                04
              </p>
              <h1 className="text-[12px] font-bold uppercase tracking-[0.22em] text-yellow-300">
                {LETTERS_LED_FAMILY_LABEL_RO}
              </h1>
              <span className="rounded-md border border-yellow-500/40 bg-yellow-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-yellow-100">
                12V
              </span>
            </div>
            <p
              className="mt-4 max-w-3xl text-[2rem] font-semibold leading-[1.15] tracking-tight text-wo-text-primary sm:text-[2.35rem]"
              data-testid="letters-led-structure-detail-material"
            >
              {LETTERS_LED_STRUCTURE_DISPLAY_NAME}
            </p>
            <p className="mt-3 font-mono text-[12px] text-yellow-200/55">
              {LETTERS_LED_MODULE_CODE} · pitch {LETTERS_LED_PITCH_MM} mm
            </p>
          </div>
          <p
            className="max-w-xl border-t border-yellow-500/25 pt-4 text-[13px] leading-relaxed text-yellow-100/80 lg:border-t-0 lg:border-l lg:pl-8 lg:pt-0"
            data-testid="letters-led-structure-detail-role"
          >
            {LETTERS_LED_DOC_ROLE_RO}
          </p>
        </div>
      </section>

      <section
        className="grid gap-4 lg:grid-cols-3"
        data-testid="letters-led-structure-detail-identity"
      >
        <div
          className={`${PS_SURFACE_PANEL} flex flex-col px-5 py-5`}
          data-testid="letters-led-structure-detail-material-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-yellow-500/15 text-yellow-300">
              <Layers className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-yellow-400/90">
              Material
            </p>
          </div>
          <div className="mt-4 space-y-3">
            <div className="rounded-xl border border-yellow-500/25 bg-yellow-500/[0.07] px-3.5 py-3">
              <p className="text-[13px] font-semibold text-wo-text-primary">
                {LETTERS_LED_MODULE_DISPLAY_NAME}
                <span className="ml-1.5 text-[10px] font-normal text-yellow-200/70">standard</span>
              </p>
              <p className="mt-1 font-mono text-[9px] text-yellow-200/60">{LETTERS_LED_MODULE_CODE}</p>
              <div className="mt-2">
                <MaterialPriceVerifyLink
                  materialCode={LETTERS_LED_MODULE_CODE}
                  testId="letters-led-structure-detail-module-price-verify"
                />
              </div>
            </div>
            <div className="rounded-xl border border-yellow-800/35 bg-wo-surface-inset px-3.5 py-3">
              <p className="text-[13px] font-semibold text-wo-text-primary">
                {LETTERS_LED_STRIP_DISPLAY_NAME}
                <span className="ml-1.5 text-[10px] font-normal text-wo-text-muted">alt.</span>
              </p>
              <p className="mt-1 font-mono text-[9px] text-wo-text-muted">{LETTERS_LED_STRIP_CODE}</p>
              <div className="mt-2">
                <MaterialPriceVerifyLink
                  materialCode={LETTERS_LED_STRIP_CODE}
                  testId="letters-led-structure-detail-strip-price-verify"
                />
              </div>
            </div>
          </div>
          <p className="mt-auto pt-3 text-[10px] text-wo-text-muted">{LETTERS_LED_MOUNT_NOTE_RO}</p>
        </div>

        <div
          className={`${PS_SURFACE_PANEL} px-5 py-5`}
          data-testid="letters-led-structure-detail-psu-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-yellow-500/15 text-yellow-300">
              <Zap className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-yellow-400/90">
              Surse 12V
            </p>
          </div>
          <p className="mt-2 font-mono text-[9px] text-yellow-200/55">{LETTERS_LED_PSU_SELECTOR_CODE}</p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {LETTERS_LED_PSU_VARIANTS.map((entry) => (
              <div
                key={entry.id}
                className="rounded-xl border border-yellow-500/25 bg-yellow-500/[0.07] px-3 py-3"
                data-testid={`letters-led-structure-detail-psu-${entry.id}`}
              >
                <p className="text-[13px] font-semibold text-wo-text-primary">{entry.labelRo}</p>
                <p className="mt-1 font-mono text-[9px] text-yellow-200/60">{entry.materialCode}</p>
                <div className="mt-2">
                  <MaterialPriceVerifyLink
                    materialCode={entry.materialCode}
                    testId={`letters-led-structure-detail-psu-price-${entry.id}`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div
          className={`${PS_SURFACE_PANEL} px-5 py-5`}
          data-testid="letters-led-structure-detail-process-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-yellow-500/15 text-yellow-300">
              <Wrench className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-yellow-400/90">
              Procese
            </p>
          </div>
          <div className="mt-4 space-y-2.5">
            {LETTERS_LED_PROCESS_STEPS.map((step, index) => (
              <div
                key={step.id}
                className="rounded-xl border border-yellow-500/25 bg-yellow-500/[0.07] px-3.5 py-3"
                data-testid={`letters-led-structure-detail-process-${step.id}`}
              >
                <p className="flex items-baseline gap-2">
                  <span className="font-mono text-[18px] font-bold tabular-nums text-yellow-300/90">
                    {index + 1}
                  </span>
                  <span className="text-[13px] font-semibold text-wo-text-primary">{step.labelRo}</span>
                </p>
                <p className="mt-1 text-[10px] leading-snug text-wo-text-muted">{step.meaningRo}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <LettersStructurePrincipalTaskOrderPanel
        stepId={LETTERS_STRUCTURE_STEP_SISTEM_LED}
        accent="yellow"
        testIdPrefix="letters-led-structure-detail"
      />

      <section className="space-y-4" data-testid="letters-led-structure-detail-calc">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-[12px] font-bold uppercase tracking-[0.16em] text-yellow-300/90">
            Cum calculăm
          </h2>
          <span className="text-[11px] text-wo-text-muted">metodă owner · fără preț duplicat</span>
        </div>
        <div className="grid gap-5 xl:grid-cols-2">
          {LETTERS_LED_CALC_CARDS.map((card) => (
            <article
              key={card.id}
              className="relative overflow-hidden rounded-2xl border border-yellow-500/40 bg-wo-surface-raised"
              data-testid={`letters-led-structure-detail-calc-${card.id}`}
              data-importance={card.importance}
            >
              <div
                className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_0%_0%,rgba(234,179,8,0.14),transparent_50%)]"
                aria-hidden
              />
              <div className="relative flex h-full flex-col px-6 py-6 lg:px-7 lg:py-7">
                <div className="flex items-start gap-4">
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-yellow-400/35 bg-yellow-500/20 text-yellow-100">
                    <CalcCardIcon id={card.id} />
                  </span>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-yellow-400/90">
                      {card.subtitleRo}
                    </p>
                    <h3 className="mt-1.5 text-[1.45rem] font-semibold tracking-tight text-wo-text-primary">
                      {card.titleRo}
                    </h3>
                  </div>
                </div>

                <p
                  className="mt-5 rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-4 py-3.5 font-mono text-[13px] leading-relaxed text-yellow-100"
                  data-testid={`letters-led-structure-detail-calc-${card.id}-formula`}
                >
                  {card.formulaRo}
                </p>

                <ol className="mt-5 space-y-2.5">
                  {card.stepsRo.map((step, index) => (
                    <li key={step} className="flex gap-3 text-[13px] leading-relaxed text-wo-text-secondary">
                      <span className="font-mono text-[12px] font-bold tabular-nums text-yellow-300/85">
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

                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-yellow-500/20 pt-4">
                  <p className="max-w-md text-[12px] leading-relaxed text-wo-text-muted">
                    {card.priceNoteRo}
                  </p>
                  <PricingVerifyLink
                    href={card.verifyHref}
                    label={card.verifyLabelRo}
                    testId={`letters-led-structure-detail-calc-${card.id}-price-verify`}
                  />
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className={`${PS_SURFACE_PANEL} overflow-hidden`}
        data-testid="letters-led-structure-detail-document"
      >
        <div className="flex flex-wrap items-center gap-2 border-b border-wo-border-subtle px-6 py-4">
          <BookOpen className="h-4 w-4 text-yellow-300" aria-hidden />
          <h2 className="text-[12px] font-bold uppercase tracking-[0.14em] text-wo-text-primary">
            Document componentă
          </h2>
          <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.12em] text-wo-text-muted">
            explicativ · direcțional
          </span>
        </div>

        <ol
          className="grid gap-4 p-4 sm:p-5 xl:grid-cols-2"
          data-testid="letters-led-structure-detail-doc-sections"
        >
          {LETTERS_LED_DOC_SECTIONS.map((section, index) => (
            <li
              key={section.id}
              className="rounded-xl border border-wo-border-subtle bg-wo-surface-inset px-5 py-5"
              data-testid={`letters-led-structure-detail-doc-${section.id}`}
            >
              <div className="flex items-baseline gap-2.5">
                <span className="font-mono text-[12px] font-bold tabular-nums text-yellow-400/80">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="text-[14px] font-semibold text-wo-text-primary">{section.titleRo}</h3>
              </div>
              <p className="mt-3 max-w-prose text-[13px] leading-relaxed text-wo-text-muted">
                {section.bodyRo}
              </p>
              {section.id === "psu" ? (
                <ul className="mt-3.5 space-y-2">
                  {LETTERS_LED_PSU_VARIANTS.map((entry) => (
                    <li
                      key={entry.materialCode}
                      className={`${PS_SURFACE_INSET} flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-[12px] leading-snug text-wo-text-secondary`}
                    >
                      <span>
                        Sursă LED 12V {entry.labelRo}
                        <span className="mx-1.5 text-wo-text-dim">·</span>
                        <span className="font-mono text-[10px] text-wo-text-muted">
                          {entry.materialCode}
                        </span>
                      </span>
                      <MaterialPriceVerifyLink
                        materialCode={entry.materialCode}
                        testId={`letters-led-structure-detail-doc-psu-price-${entry.id}`}
                      />
                    </li>
                  ))}
                  {(section.bulletsRo ?? [])
                    .filter(
                      (bullet) =>
                        !LETTERS_LED_PSU_VARIANTS.some((entry) =>
                          bullet.includes(entry.materialCode),
                        ),
                    )
                    .map((bullet) => (
                      <li
                        key={bullet}
                        className={`${PS_SURFACE_INSET} px-3 py-2 text-[12px] leading-snug text-wo-text-secondary`}
                      >
                        {bullet}
                      </li>
                    ))}
                </ul>
              ) : section.bulletsRo && section.bulletsRo.length > 0 ? (
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
          data-testid="letters-led-structure-detail-doc-sources"
        >
          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
            Surse owner / lock
          </p>
          <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
            {LETTERS_LED_DOC_SOURCES.map((source) => (
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
