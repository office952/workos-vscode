/**
 * Shared “În lanțul literei” + “Cum obții” block for structure detail pages.
 * Display only — card ≠ task.
 */
import { ListOrdered, Wrench } from "lucide-react";
import type { LettersStructureStepId } from "./lettersStructureDetailRoutes";
import {
  getLettersComponentObtainDoc,
  isTaskOwnedByComponent,
  LETTERS_PRINCIPAL_TASK_CHAIN,
  LETTERS_PRINCIPAL_TASK_CHAIN_INTRO_RO,
  listObtainTasksForComponent,
} from "./lettersStructurePrincipalTaskOrder";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

export type LettersTaskOrderAccent = "violet" | "sky" | "amber" | "yellow";

const ACCENT: Record<
  LettersTaskOrderAccent,
  {
    title: string;
    border: string;
    chip: string;
    chipMuted: string;
    mono: string;
    panelBorder: string;
  }
> = {
  violet: {
    title: "text-violet-300/90",
    border: "border-violet-500/30",
    chip: "border-violet-400/40 bg-violet-500/15 text-violet-50",
    chipMuted: "border-wo-border-strong bg-wo-surface-inset text-wo-text-muted",
    mono: "text-violet-300/85",
    panelBorder: "border-violet-500/35",
  },
  sky: {
    title: "text-sky-300/90",
    border: "border-sky-500/30",
    chip: "border-sky-400/40 bg-sky-500/15 text-sky-50",
    chipMuted: "border-wo-border-strong bg-wo-surface-inset text-wo-text-muted",
    mono: "text-sky-300/85",
    panelBorder: "border-sky-500/35",
  },
  amber: {
    title: "text-amber-300/90",
    border: "border-amber-500/30",
    chip: "border-amber-400/40 bg-amber-500/15 text-amber-50",
    chipMuted: "border-wo-border-strong bg-wo-surface-inset text-wo-text-muted",
    mono: "text-amber-300/85",
    panelBorder: "border-amber-500/35",
  },
  yellow: {
    title: "text-yellow-300/90",
    border: "border-yellow-500/30",
    chip: "border-yellow-400/40 bg-yellow-500/15 text-yellow-50",
    chipMuted: "border-wo-border-strong bg-wo-surface-inset text-wo-text-muted",
    mono: "text-yellow-300/85",
    panelBorder: "border-yellow-500/35",
  },
};

type Props = {
  stepId: LettersStructureStepId;
  accent: LettersTaskOrderAccent;
  testIdPrefix: string;
};

export function LettersStructurePrincipalTaskOrderPanel({
  stepId,
  accent,
  testIdPrefix,
}: Props) {
  const styles = ACCENT[accent];
  const obtain = getLettersComponentObtainDoc(stepId);
  const obtainTasks = listObtainTasksForComponent(stepId);

  if (!obtain) return null;

  return (
    <section
      className="space-y-4"
      data-testid={`${testIdPrefix}-task-order`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className={`text-[12px] font-bold uppercase tracking-[0.16em] ${styles.title}`}>
          Cum obții · ordine taskuri
        </h2>
        <span className="text-[11px] text-slate-500">card ≠ task · fără emblemă · fără suport comun</span>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <article
          className={`${PS_SURFACE_PANEL} ${styles.panelBorder} px-5 py-5`}
          data-testid={`${testIdPrefix}-task-order-obtain`}
        >
          <div className="flex items-center gap-2.5">
            <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${styles.chip}`}>
              <Wrench className="h-5 w-5" aria-hidden />
            </span>
            <div className="min-w-0">
              <p className={`text-[10px] font-semibold uppercase tracking-[0.14em] ${styles.title}`}>
                Obținere componentă
              </p>
              <h3 className="mt-0.5 text-[1.05rem] font-semibold text-slate-50">{obtain.titleRo}</h3>
            </div>
          </div>
          <p className="mt-4 text-[13px] leading-relaxed text-amber-100/90">{obtain.withoutTheseRo}</p>
          <ol className="mt-4 space-y-2.5">
            {obtainTasks.map((task, index) => (
              <li key={task.id} className="flex gap-3 text-[13px] leading-relaxed text-wo-text-secondary">
                <span className={`font-mono text-[12px] font-bold tabular-nums ${styles.mono}`}>
                  {index + 1}.
                </span>
                <span>
                  <span className="font-medium text-slate-100">{task.labelRo}</span>
                  {task.conditionRo ? (
                    <span className="mt-0.5 block text-[11px] text-slate-500">{task.conditionRo}</span>
                  ) : null}
                </span>
              </li>
            ))}
          </ol>
          {obtain.notesRo.length > 0 ? (
            <ul className={`mt-4 space-y-1.5 border-t ${styles.border} pt-3`}>
              {obtain.notesRo.map((note) => (
                <li key={note} className="text-[11px] leading-relaxed text-slate-500">
                  {note}
                </li>
              ))}
            </ul>
          ) : null}
        </article>

        <article
          className={`${PS_SURFACE_PANEL} ${styles.panelBorder} px-5 py-5`}
          data-testid={`${testIdPrefix}-task-order-chain`}
        >
          <div className="flex items-center gap-2.5">
            <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${styles.chip}`}>
              <ListOrdered className="h-5 w-5" aria-hidden />
            </span>
            <div className="min-w-0">
              <p className={`text-[10px] font-semibold uppercase tracking-[0.14em] ${styles.title}`}>
                În lanțul literei
              </p>
              <h3 className="mt-0.5 text-[1.05rem] font-semibold text-slate-50">
                Ordine principală taskuri
              </h3>
            </div>
          </div>
          <p className="mt-3 text-[12px] leading-relaxed text-wo-text-muted">
            {LETTERS_PRINCIPAL_TASK_CHAIN_INTRO_RO}
          </p>
          <ol className="mt-4 max-h-[22rem] space-y-1.5 overflow-y-auto pr-1">
            {LETTERS_PRINCIPAL_TASK_CHAIN.map((task) => {
              const owned = isTaskOwnedByComponent(task, stepId);
              return (
                <li
                  key={task.id}
                  className={`rounded-lg border px-2.5 py-2 text-[12px] leading-snug ${
                    owned ? styles.chip : styles.chipMuted
                  }`}
                  data-owned={owned ? "true" : "false"}
                  data-testid={`${testIdPrefix}-task-order-step-${task.id}`}
                >
                  <span className={`mr-1.5 font-mono text-[11px] font-bold tabular-nums ${owned ? styles.mono : "text-slate-500"}`}>
                    {task.order}.
                  </span>
                  <span className={owned ? "font-medium" : undefined}>{task.labelRo}</span>
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
  );
}
