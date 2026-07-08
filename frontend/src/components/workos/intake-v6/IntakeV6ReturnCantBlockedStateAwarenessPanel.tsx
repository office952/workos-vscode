import type { ReactNode } from "react";
import type {
  ReturnCantTruthDependencyReadonlyRow,
  ReturnCantTruthFieldReadonlyRow,
  ReturnCantTruthFieldsReadonlyModel,
} from "@/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper";
import { v6 } from "./atoms/intakeV6Presentation";

function Badge({
  children,
  tone = "muted",
}: {
  children: ReactNode;
  tone?: "bad" | "warn" | "muted";
}) {
  const toneClass =
    tone === "bad"
      ? "border-red-700/50 bg-red-950/30 text-red-200"
      : tone === "warn"
        ? "border-amber-700/50 bg-amber-950/25 text-amber-200"
        : "border-slate-700 bg-slate-900/80 text-slate-300";
  return <span className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${toneClass}`}>{children}</span>;
}

function fieldByKey(model: ReturnCantTruthFieldsReadonlyModel, key: string): ReturnCantTruthFieldReadonlyRow {
  const match = model.fields.find((field) => field.field_key === key);
  if (!match) {
    throw new Error(`Missing return_cant readonly field ${key}`);
  }
  return match;
}

function dependencyByKey(
  model: ReturnCantTruthFieldsReadonlyModel,
  key: string,
): ReturnCantTruthDependencyReadonlyRow {
  const match = model.dependencies.find((dependency) => dependency.dependency_key === key);
  if (!match) {
    throw new Error(`Missing return_cant readonly dependency ${key}`);
  }
  return match;
}

function formatValue(value: unknown): string {
  if (value == null) return "lipsa";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "lipsa";
  if (typeof value === "string") return value.trim().length > 0 ? value : "lipsa";
  return JSON.stringify(value);
}

export default function IntakeV6ReturnCantBlockedStateAwarenessPanel({
  model,
}: {
  model: ReturnCantTruthFieldsReadonlyModel;
}) {
  const perimeterSource = fieldByKey(model, "return_cant.perimeter_source");
  const confirmationState = fieldByKey(model, "return_cant.confirmation_state");
  const facePerimeter = dependencyByKey(model, "face_confirmed_perimeter");
  const visibleBlockers = model.blockers;

  return (
    <section
      className={`${v6.cardCompact} border-red-900/50 bg-red-950/10 text-slate-200`}
      data-testid="intake-v6-return-cant-blocked-awareness"
      data-read-only="true"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-red-200/80">
            Return/cant diagnostic
          </p>
          <h3 className="mt-1 text-[14px] font-semibold text-slate-100">
            Return/cant component preview este blocat.
          </h3>
          <p
            className="mt-2 max-w-[72ch] text-[11px] leading-relaxed text-slate-300"
            data-testid="intake-v6-return-cant-blocked-copy"
          >
            Motiv: datele necesare nu sunt inca confirmate pe componenta. Acesta este diagnostic read-only, nu calcul si nu pret.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="bad">RETURN_CANT_MAPPER_BLOCKED</Badge>
          <Badge>{model.component_scope}</Badge>
          <Badge>{model.root_template}</Badge>
        </div>
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-3">
        <div
          className="rounded border border-red-900/40 bg-slate-950/40 p-3"
          data-testid="intake-v6-return-cant-blocked-summary"
        >
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
            Ce blocheaza acum
          </p>
          <ul className="space-y-2 text-[11px] text-slate-200">
            <li data-testid="intake-v6-return-cant-context-only-line">
              <span className="font-mono text-amber-200">quote_geometry.letter_perimeter_m</span> ramane context-only.
            </li>
            <li data-testid="intake-v6-return-cant-face-dependency-line">
              Lipseste <span className="font-mono text-red-200">components.face.confirmed_perimeter</span> confirmed.
            </li>
            <li data-testid="intake-v6-return-cant-confirmation-line">
              Lipseste <span className="font-mono text-red-200">components.return_cant.confirmation_state = confirmed</span>.
            </li>
          </ul>
        </div>

        <div
          className="rounded border border-slate-800 bg-slate-950/40 p-3"
          data-testid="intake-v6-return-cant-blocker-list"
        >
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
            Blockers
          </p>
          <ul className="space-y-1.5 text-[11px] text-slate-200">
            {visibleBlockers.map((blocker) => (
              <li key={blocker} className="font-mono text-red-200">
                {blocker}
              </li>
            ))}
          </ul>
        </div>

        <div
          className="rounded border border-slate-800 bg-slate-950/40 p-3"
          data-testid="intake-v6-return-cant-runtime-evidence"
        >
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
            Runtime evidence
          </p>
          <dl className="space-y-2 text-[11px]">
            <div>
              <dt className="text-slate-500">Perimeter source observat</dt>
              <dd className="font-mono text-amber-200" data-testid="intake-v6-return-cant-perimeter-path">
                {perimeterSource.current_runtime_path ?? "lipsa"}
              </dd>
              <dd className="text-slate-400">
                {perimeterSource.classification} · {formatValue(perimeterSource.current_value)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Dependency face perimeter</dt>
              <dd className="font-mono text-red-200" data-testid="intake-v6-return-cant-face-dependency-path">
                {facePerimeter.current_runtime_path ?? "components.face.confirmed_perimeter lipsa"}
              </dd>
              <dd className="text-slate-400">
                {facePerimeter.classification} · {formatValue(facePerimeter.current_value)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Confirmation state</dt>
              <dd className="font-mono text-red-200" data-testid="intake-v6-return-cant-confirmation-path">
                {confirmationState.canonical_product_truth_path}
              </dd>
              <dd className="text-slate-400">
                {confirmationState.classification} · {formatValue(confirmationState.current_value)}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <p
        className="mt-3 rounded border border-slate-800 bg-slate-950/30 px-3 py-2 text-[10px] text-slate-400"
        data-testid="intake-v6-return-cant-read-only-note"
      >
        Read-only only: nu afiseaza preview final, nu afiseaza stare ready pentru calcul, nu afiseaza pret si nu afiseaza total.
      </p>
    </section>
  );
}