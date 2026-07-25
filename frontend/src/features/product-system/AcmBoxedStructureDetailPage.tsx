/**
 * Alucobond casetat — structure-step detail (Corp / Structură metalică).
 * Display documentation only — cites MIXED + OWNER_RULES.
 */
import { Link, Navigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BookOpen,
  ExternalLink,
  Layers,
  ListOrdered,
  Scissors,
  Wrench,
} from "lucide-react";
import {
  buildProductSystemProductDetailPath,
  parseProductSystemTemplateRouteParam,
} from "@/features/product-system/productSystemRouteSync";
import {
  ACM_BOXED_DOC_SOURCES,
  ACM_BOXED_PRINCIPAL_TASK_CHAIN,
  getAcmBoxedStepDoc,
  isAcmTaskOwnedByStep,
  listAcmObtainTasks,
} from "@/features/product-system/acmBoxedStructureDocumentation";
import {
  canonicalizeAcmBoxedStructureStepId,
  type AcmBoxedStructureStepId,
} from "@/features/product-system/acmBoxedStructureDetailRoutes";
import {
  ACM_BOXED_OWNER_LABEL_RO,
  isAcmBoxedMountingTemplate,
} from "@/features/product-system/acmBoxedTemplateIdentity";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

const ACCENT: Record<
  AcmBoxedStructureStepId,
  { title: string; border: string; chip: string; chipMuted: string; mono: string; hero: string }
> = {
  "corp-casetat": {
    title: "text-cyan-300/90",
    border: "border-cyan-500/35",
    chip: "border-cyan-400/40 bg-cyan-500/15 text-cyan-50",
    chipMuted: "border-[#2A3548] bg-[#0A0F1A] text-slate-400",
    mono: "text-cyan-300/85",
    hero: "border-cyan-500/35",
  },
  "structura-metalica": {
    title: "text-amber-300/90",
    border: "border-amber-500/35",
    chip: "border-amber-400/40 bg-amber-500/15 text-amber-50",
    chipMuted: "border-[#2A3548] bg-[#0A0F1A] text-slate-400",
    mono: "text-amber-300/85",
    hero: "border-amber-500/35",
  },
};

export default function AcmBoxedStructureDetailPage() {
  const { templateCode: rawCode, stepId: rawStep } = useParams<{
    templateCode: string;
    stepId: string;
  }>();
  const pathTemplateCode = parseProductSystemTemplateRouteParam(rawCode ?? null);
  const templateCode = pathTemplateCode ?? rawCode ?? null;
  const stepId = canonicalizeAcmBoxedStructureStepId(rawStep);

  if (!templateCode || !isAcmBoxedMountingTemplate(templateCode) || !stepId) {
    return <Navigate to="/product-system/products" replace />;
  }

  // Legacy 3-step URLs → canonical 2-step path
  if (rawStep && rawStep !== stepId) {
    return (
      <Navigate
        to={`${buildProductSystemProductDetailPath(templateCode)}/structure/${stepId}`}
        replace
      />
    );
  }

  const doc = getAcmBoxedStepDoc(stepId);
  const styles = ACCENT[stepId];
  const obtainTasks = listAcmObtainTasks(stepId);
  const backPath = buildProductSystemProductDetailPath(templateCode);
  const stepPad = String(doc.stepIndex).padStart(2, "0");

  return (
    <div className="w-full space-y-6 pb-12" data-testid="acm-boxed-structure-detail">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to={backPath}
          className="inline-flex items-center gap-1.5 rounded-md border border-[#2A3548] bg-[#111827] px-3 py-2 text-[12px] font-medium text-slate-300 transition-colors hover:border-cyan-500/40 hover:text-cyan-100"
          data-testid="acm-boxed-structure-detail-back"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Structură
        </Link>
        <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-slate-500">
          {ACM_BOXED_OWNER_LABEL_RO} · pas {doc.stepIndex} / 2
        </span>
      </header>

      <section
        className={`relative overflow-hidden rounded-2xl border ${styles.hero} bg-[#111827]`}
        data-testid="acm-boxed-structure-detail-hero"
      >
        <div className="relative grid gap-8 px-6 py-7 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:items-end lg:px-8 lg:py-8">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className={`font-mono text-[12px] font-bold tabular-nums tracking-[0.22em] ${styles.mono}`}>
                {stepPad}
              </p>
              <h1 className={`text-[12px] font-bold uppercase tracking-[0.22em] ${styles.title}`}>
                {doc.titleRo}
              </h1>
            </div>
            <p className="mt-4 max-w-3xl text-[2rem] font-semibold leading-[1.15] tracking-tight text-slate-50 sm:text-[2.35rem]">
              {doc.heroMaterialRo}
            </p>
            <p className={`mt-3 font-mono text-[12px] ${styles.mono}`}>{doc.heroCodeRo}</p>
          </div>
          <p
            className={`max-w-xl border-t ${styles.border} pt-4 text-[13px] leading-relaxed text-slate-200/85 lg:border-t-0 lg:border-l lg:pl-8 lg:pt-0`}
          >
            {doc.roleRo}
          </p>
        </div>
      </section>

      <section className="space-y-4" data-testid="acm-boxed-structure-detail-task-order">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className={`text-[12px] font-bold uppercase tracking-[0.16em] ${styles.title}`}>
            Cum obții · ordine taskuri
          </h2>
          <span className="text-[11px] text-slate-500">card ≠ task · nucleu ACM · fără Composer</span>
        </div>
        <div className="grid gap-5 xl:grid-cols-2">
          <article className={`${PS_SURFACE_PANEL} ${styles.border} px-5 py-5`}>
            <div className="flex items-center gap-2.5">
              <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${styles.chip}`}>
                <Wrench className="h-5 w-5" aria-hidden />
              </span>
              <h3 className="text-[1.05rem] font-semibold text-slate-50">{doc.obtainTitleRo}</h3>
            </div>
            <p className="mt-4 text-[13px] leading-relaxed text-amber-100/90">{doc.withoutTheseRo}</p>
            <ol className="mt-4 space-y-2.5">
              {obtainTasks.map((task, index) => (
                <li key={task.id} className="flex gap-3 text-[13px] leading-relaxed text-slate-300">
                  <span className={`font-mono text-[12px] font-bold ${styles.mono}`}>{index + 1}.</span>
                  <span className="font-medium text-slate-100">{task.labelRo}</span>
                </li>
              ))}
            </ol>
          </article>
          <article className={`${PS_SURFACE_PANEL} ${styles.border} px-5 py-5`}>
            <div className="flex items-center gap-2.5">
              <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${styles.chip}`}>
                <ListOrdered className="h-5 w-5" aria-hidden />
              </span>
              <h3 className="text-[1.05rem] font-semibold text-slate-50">În lanțul ACM</h3>
            </div>
            <ol className="mt-4 max-h-[22rem] space-y-1.5 overflow-y-auto pr-1">
              {ACM_BOXED_PRINCIPAL_TASK_CHAIN.map((task) => {
                const owned = isAcmTaskOwnedByStep(task, stepId);
                return (
                  <li
                    key={task.id}
                    className={`rounded-lg border px-2.5 py-2 text-[12px] ${owned ? styles.chip : styles.chipMuted}`}
                    data-owned={owned ? "true" : "false"}
                  >
                    <span className="mr-1.5 font-mono text-[11px] font-bold">{task.order}.</span>
                    {task.labelRo}
                    {task.conditionRo ? (
                      <span className="mt-0.5 block text-[10px] opacity-80">{task.conditionRo}</span>
                    ) : null}
                  </li>
                );
              })}
            </ol>
          </article>
        </div>
      </section>

      <section className="space-y-4" data-testid="acm-boxed-structure-detail-calc">
        <h2 className={`text-[12px] font-bold uppercase tracking-[0.16em] ${styles.title}`}>
          Cum calculăm
        </h2>
        <div className="grid gap-5 xl:grid-cols-2">
          {doc.calcCards.map((card) => (
            <article
              key={card.id}
              className={`relative overflow-hidden rounded-2xl border ${styles.border} bg-[#111827] px-6 py-6`}
              data-testid={`acm-boxed-structure-detail-calc-${card.id}`}
            >
              <div className="flex items-start gap-4">
                <span
                  className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border ${styles.chip}`}
                >
                  {card.id.includes("cut") || card.id.includes("groove") ? (
                    <Scissors className="h-7 w-7" aria-hidden />
                  ) : (
                    <Layers className="h-7 w-7" aria-hidden />
                  )}
                </span>
                <div>
                  <p className={`text-[10px] font-semibold uppercase tracking-[0.14em] ${styles.title}`}>
                    {card.subtitleRo}
                  </p>
                  <h3 className="mt-1.5 text-[1.35rem] font-semibold text-slate-50">{card.titleRo}</h3>
                </div>
              </div>
              <p
                className={`mt-5 rounded-xl border ${styles.border} bg-black/20 px-4 py-3.5 font-mono text-[13px] text-slate-100`}
              >
                {card.formulaRo}
              </p>
              <ol className="mt-5 space-y-2">
                {card.stepsRo.map((step, index) => (
                  <li key={step} className="flex gap-3 text-[13px] text-slate-300">
                    <span className={`font-mono text-[12px] font-bold ${styles.mono}`}>{index + 1}.</span>
                    {step}
                  </li>
                ))}
              </ol>
              <ul className="mt-4 space-y-1 text-[12px] text-slate-400">
                {card.outputsRo.map((line) => (
                  <li key={line}>→ {line}</li>
                ))}
              </ul>
              <ul className="mt-3 space-y-1 text-[11px] text-slate-500">
                {card.notThisRo.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <div
                className={`mt-5 flex flex-wrap items-center justify-between gap-3 border-t ${styles.border} pt-4`}
              >
                <p className="text-[11px] text-slate-500">{card.priceNoteRo}</p>
                <Link
                  to={card.verifyHref}
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-cyan-300/90 underline-offset-2 hover:underline"
                >
                  {card.verifyLabelRo}
                  <ExternalLink className="h-3 w-3" aria-hidden />
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={`${PS_SURFACE_PANEL} px-5 py-5`} data-testid="acm-boxed-structure-detail-document">
        <div className="mb-4 flex items-center gap-2">
          <BookOpen className={`h-5 w-5 ${styles.mono}`} aria-hidden />
          <h2 className={`text-[12px] font-bold uppercase tracking-[0.16em] ${styles.title}`}>
            Document componentă
          </h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {doc.sections.map((section) => (
            <article key={section.id} className="rounded-xl border border-[#2A3548] bg-[#0A0F1A] px-4 py-4">
              <h3 className="text-[13px] font-semibold text-slate-100">{section.titleRo}</h3>
              <p className="mt-2 text-[12px] leading-relaxed text-slate-400">{section.bodyRo}</p>
              {section.bulletsRo?.length ? (
                <ul className="mt-3 space-y-1.5 text-[12px] text-slate-300">
                  {section.bulletsRo.map((bullet) => (
                    <li key={bullet}>· {bullet}</li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))}
        </div>
        <ul className="mt-5 space-y-1 border-t border-[#2A3548] pt-4 text-[11px] text-slate-500">
          {ACM_BOXED_DOC_SOURCES.map((source) => (
            <li key={source.path}>
              <span className="text-slate-400">{source.labelRo}</span> —{" "}
              <span className="font-mono">{source.path}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
