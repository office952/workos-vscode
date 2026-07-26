/**
 * Vizual față — dedicated structure-step page.
 * Visual identity (hero / cards) + explanatory directional documentation.
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
} from "lucide-react";
import { CncProcessableBadge } from "@/components/workos/CncProcessableBadge";
import { LettersFaceFinishOptionBadges } from "@/components/workos/LettersFaceFinishOptionBadges";
import {
  LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
  LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE,
} from "@/lib/materials/lettersFacePlexiMaterialDisplay";
import { LETTERS_FACE_FINISH_MATERIALS } from "@/lib/materials/lettersFaceFinishMaterialDisplay";
import { CNC_PROCESSABLE_LETTER_FACE_SERVICES } from "@/lib/cnc/cncProcessableBadge";
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
  LETTERS_FACE_CALC_CARDS,
  LETTERS_FACE_DOC_ROLE_RO,
  LETTERS_FACE_DOC_SECTIONS,
  LETTERS_FACE_DOC_SOURCES,
  type LettersFaceCalcCard,
} from "@/features/product-system/lettersFaceStructureDocumentation";
import { LettersStructurePrincipalTaskOrderPanel } from "@/features/product-system/LettersStructurePrincipalTaskOrderPanel";
import { LETTERS_STRUCTURE_STEP_VIZUAL_FATA } from "@/features/product-system/lettersStructureDetailRoutes";
import { PS_SURFACE_PANEL, PS_SURFACE_INSET } from "./productSystemSurfaces";

function CalcCardIcon({ id }: { id: LettersFaceCalcCard["id"] }) {
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

const CNC_STEPS = [
  {
    id: "cut",
    index: 1,
    label: CNC_PROCESSABLE_LETTER_FACE_SERVICES[0],
    mark: "obligatoriu",
  },
  {
    id: "bevel",
    index: 2,
    label: CNC_PROCESSABLE_LETTER_FACE_SERVICES[1],
    mark: "pentru lipire volum",
  },
] as const;

export default function LettersFaceStructureDetailPage() {
  const { templateCode: rawCode } = useParams<{ templateCode: string }>();
  const templateCode = parseProductSystemTemplateRouteParam(rawCode);
  // Keep URL casing for back-nav (entity codes use `_v2`, normalize uppercases).
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
      data-testid="letters-face-structure-detail"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={backPath}
          className="inline-flex items-center gap-1.5 rounded-md border border-wo-border-strong bg-wo-surface-raised px-3 py-2 text-[12px] font-medium text-wo-text-secondary transition-colors hover:border-violet-500/40 hover:text-violet-100"
          data-testid="letters-face-structure-detail-back"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Structură
        </Link>
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-wo-text-muted">
          Litere · pas 1 / 5
        </span>
      </header>

      {/* Hero — full width plane; prose capped for calm reading */}
      <section
        className="relative overflow-hidden rounded-2xl border border-violet-500/35 bg-wo-surface-raised"
        data-testid="letters-face-structure-detail-hero"
      >
        <div
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_12%_0%,rgba(139,92,246,0.30),transparent_52%),radial-gradient(ellipse_at_88%_70%,rgba(167,139,250,0.12),transparent_48%)]"
          aria-hidden
        />
        <div className="relative grid gap-8 px-6 py-7 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:items-end lg:px-8 lg:py-8">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="font-mono text-[12px] font-bold tabular-nums tracking-[0.22em] text-violet-300/90">
                01
              </p>
              <h1 className="text-[12px] font-bold uppercase tracking-[0.22em] text-violet-300">
                Vizual față
              </h1>
              <CncProcessableBadge
                size="md"
                testId="letters-face-structure-detail-cnc-mark"
              />
            </div>
            <p
              className="mt-4 max-w-3xl text-[2rem] font-semibold leading-[1.15] tracking-tight text-slate-50 sm:text-[2.35rem]"
              data-testid="letters-face-structure-detail-material"
            >
              {LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME}
            </p>
            <p className="mt-3 font-mono text-[12px] text-violet-200/55">
              {LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE}
            </p>
          </div>
          <p
            className="max-w-xl border-t border-violet-500/25 pt-4 text-[13px] leading-relaxed text-violet-100/80 lg:border-t-0 lg:border-l lg:pl-8 lg:pt-0"
            data-testid="letters-face-structure-detail-role"
          >
            {LETTERS_FACE_DOC_ROLE_RO}
          </p>
        </div>
      </section>

      {/* Identity band — three equal lanes across full width */}
      <section
        className="grid gap-4 lg:grid-cols-3"
        data-testid="letters-face-structure-detail-identity"
      >
        <div
          className={`${PS_SURFACE_PANEL} flex flex-col px-5 py-5`}
          data-testid="letters-face-structure-detail-material-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/15 text-violet-300">
              <Layers className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-violet-400/90">
              Material
            </p>
          </div>
          <p className="mt-4 text-[16px] font-semibold leading-snug text-wo-text-primary">
            {LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME}
          </p>
          <p className="mt-2 inline-flex w-fit rounded-md border border-violet-800/40 bg-violet-950/30 px-2 py-1 font-mono text-[10px] text-violet-200/70">
            {LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE}
          </p>
          <div className="mt-auto pt-4">
            <MaterialPriceVerifyLink
              materialCode={LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE}
              testId="letters-face-structure-detail-material-price-verify"
            />
          </div>
        </div>

        <div
          className={`${PS_SURFACE_PANEL} px-5 py-5`}
          data-testid="letters-face-structure-detail-cnc-card"
        >
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/15 text-violet-300">
              <Scissors className="h-5 w-5" aria-hidden />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-violet-400/90">
              Procese CNC
            </p>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {CNC_STEPS.map((step) => (
              <div
                key={step.id}
                className="rounded-xl border border-violet-500/25 bg-violet-500/[0.07] px-3.5 py-3.5"
                data-testid={`letters-face-structure-detail-cnc-step-${step.id}`}
              >
                <p className="font-mono text-[22px] font-bold tabular-nums text-violet-300/90">
                  {step.index}
                </p>
                <p className="mt-1.5 text-[13px] font-semibold text-wo-text-primary">{step.label}</p>
                <p className="mt-1 text-[10px] text-wo-text-muted">{step.mark}</p>
              </div>
            ))}
          </div>
        </div>

        <div
          className={`${PS_SURFACE_PANEL} px-5 py-5`}
          data-testid="letters-face-structure-detail-finish"
        >
          <LettersFaceFinishOptionBadges
            size="md"
            testId="letters-face-structure-detail-finish-options"
          />
        </div>
      </section>

      <LettersStructurePrincipalTaskOrderPanel
        stepId={LETTERS_STRUCTURE_STEP_VIZUAL_FATA}
        accent="violet"
        testIdPrefix="letters-face-structure-detail"
      />

      {/* Calculation — primary weight, full-width twin cards */}
      <section className="space-y-4" data-testid="letters-face-structure-detail-calc">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-[12px] font-bold uppercase tracking-[0.16em] text-violet-300/90">
            Cum calculăm
          </h2>
          <span className="text-[11px] text-wo-text-muted">metodă owner · fără preț duplicat</span>
        </div>
        <div className="grid gap-5 xl:grid-cols-2">
          {LETTERS_FACE_CALC_CARDS.map((card) => (
            <article
              key={card.id}
              className="relative overflow-hidden rounded-2xl border border-violet-500/40 bg-wo-surface-raised"
              data-testid={`letters-face-structure-detail-calc-${card.id}`}
              data-importance={card.importance}
            >
              <div
                className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_0%_0%,rgba(139,92,246,0.18),transparent_50%)]"
                aria-hidden
              />
              <div className="relative flex h-full flex-col px-6 py-6 lg:px-7 lg:py-7">
                <div className="flex items-start gap-4">
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-violet-400/35 bg-violet-500/20 text-violet-100">
                    <CalcCardIcon id={card.id} />
                  </span>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-violet-400/90">
                      {card.subtitleRo}
                    </p>
                    <h3 className="mt-1.5 text-[1.45rem] font-semibold tracking-tight text-slate-50">
                      {card.titleRo}
                    </h3>
                  </div>
                </div>

                <p
                  className="mt-5 rounded-xl border border-violet-500/30 bg-violet-500/10 px-4 py-3.5 font-mono text-[13px] leading-relaxed text-violet-100"
                  data-testid={`letters-face-structure-detail-calc-${card.id}-formula`}
                >
                  {card.formulaRo}
                </p>

                <ol className="mt-5 space-y-2.5">
                  {card.stepsRo.map((step, index) => (
                    <li key={step} className="flex gap-3 text-[13px] leading-relaxed text-wo-text-secondary">
                      <span className="font-mono text-[12px] font-bold tabular-nums text-violet-300/85">
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

                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-violet-500/20 pt-4">
                  <p className="max-w-md text-[12px] leading-relaxed text-wo-text-muted">
                    {card.priceNoteRo}
                  </p>
                  {card.verifyMaterialCode ? (
                    <MaterialPriceVerifyLink
                      materialCode={card.verifyMaterialCode}
                      testId={`letters-face-structure-detail-calc-${card.id}-price-verify`}
                    />
                  ) : (
                    <Link
                      to="/inventory/pricing"
                      className="inline-flex items-center gap-1 text-[11px] font-medium text-cyan-300/90 underline-offset-2 hover:text-cyan-200 hover:underline"
                      data-testid={`letters-face-structure-detail-calc-${card.id}-price-verify`}
                    >
                      Verifică tarif CNC
                      <ExternalLink className="h-3 w-3" aria-hidden />
                    </Link>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Document — wide frame, sections in calm 2-col grid */}
      <section
        className={`${PS_SURFACE_PANEL} overflow-hidden`}
        data-testid="letters-face-structure-detail-document"
      >
        <div className="flex flex-wrap items-center gap-2 border-b border-wo-border-subtle px-6 py-4">
          <BookOpen className="h-4 w-4 text-violet-300" aria-hidden />
          <h2 className="text-[12px] font-bold uppercase tracking-[0.14em] text-wo-text-primary">
            Document componentă
          </h2>
          <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.12em] text-wo-text-muted">
            explicativ · direcțional
          </span>
        </div>

        <ol
          className="grid gap-4 p-4 sm:p-5 xl:grid-cols-2"
          data-testid="letters-face-structure-detail-doc-sections"
        >
          {LETTERS_FACE_DOC_SECTIONS.map((section, index) => (
            <li
              key={section.id}
              className="rounded-xl border border-wo-border-subtle bg-wo-surface-inset px-5 py-5"
              data-testid={`letters-face-structure-detail-doc-${section.id}`}
            >
              <div className="flex items-baseline gap-2.5">
                <span className="font-mono text-[12px] font-bold tabular-nums text-violet-400/80">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="text-[14px] font-semibold text-wo-text-primary">{section.titleRo}</h3>
              </div>
              <p className="mt-3 max-w-prose text-[13px] leading-relaxed text-wo-text-muted">
                {section.bodyRo}
              </p>
              {section.id === "finish" ? (
                <ul className="mt-3.5 space-y-2">
                  {LETTERS_FACE_FINISH_MATERIALS.map((entry) => (
                    <li
                      key={entry.materialCode}
                      className={`${PS_SURFACE_INSET} flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-[12px] leading-snug text-wo-text-secondary`}
                    >
                      <span>
                        {entry.labelRo}
                        <span className="mx-1.5 text-wo-text-dim">·</span>
                        <span className="font-mono text-[10px] text-wo-text-muted">{entry.materialCode}</span>
                      </span>
                      <MaterialPriceVerifyLink
                        materialCode={entry.materialCode}
                        testId={`letters-face-structure-detail-doc-finish-price-${entry.id}`}
                      />
                    </li>
                  ))}
                  {(section.bulletsRo ?? [])
                    .filter(
                      (bullet) =>
                        !LETTERS_FACE_FINISH_MATERIALS.some((entry) =>
                          bullet.startsWith(entry.labelRo),
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
          data-testid="letters-face-structure-detail-doc-sources"
        >
          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-wo-text-muted">
            Surse owner / lock
          </p>
          <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
            {LETTERS_FACE_DOC_SOURCES.map((source) => (
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
