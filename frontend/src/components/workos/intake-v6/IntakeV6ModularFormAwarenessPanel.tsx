import type {
  ModuleActivationPreviewState,
  OperatorDisplayLine,
} from "@/lib/intakeV6/intakeV6ModuleActivationPreview";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

function stateBadgeTone(
  state: ModuleActivationPreviewState,
  moduleKey?: string,
): "ok" | "pending" | "muted" {
  if (
    moduleKey === "structura_suport" &&
    (state === "active" || state === "conditional_active")
  ) {
    return "pending";
  }
  if (state === "always_on" || state === "active" || state === "conditional_active") {
    return "ok";
  }
  if (state === "pending") return "pending";
  return "muted";
}

function stateBadgeLabel(
  state: ModuleActivationPreviewState,
  moduleKey?: string,
): string {
  if (
    moduleKey === "structura_suport" &&
    (state === "active" || state === "conditional_active")
  ) {
    return "Selectat";
  }
  switch (state) {
    case "always_on":
      return "Inclus";
    case "active":
      return "Activ";
    case "conditional_active":
      return "Activ";
    case "pending":
      return "De completat";
    case "inactive":
      return "Nu se aplică";
    default:
      return state;
  }
}

function ProductLineRow({ line, compact = false }: { line: OperatorDisplayLine; compact?: boolean }) {
  const pending = line.state === "pending";
  const statusLabel = stateBadgeLabel(line.state, line.key);

  return (
    <li
      className="flex items-start justify-between gap-3 border-t border-wo-border-strong py-2 first:border-t-0 first:pt-0"
      data-testid={`intake-v6-modular-product-${line.key}`}
      data-module-state={line.state}
    >
      <div className="min-w-0">
        <p className="text-[12px] font-semibold text-slate-200">{line.label}</p>
        <p className={v6.metricLabel}>{line.hint}</p>
      </div>
      {compact ? (
        <span
          className={`shrink-0 text-[10px] ${
            pending ? "text-amber-200/90" : "text-slate-500"
          }`}
          data-testid={`intake-v6-modular-product-status-${line.key}`}
        >
          {statusLabel}
        </span>
      ) : (
        <AtomsBadge tone={stateBadgeTone(line.state, line.key)}>{statusLabel}</AtomsBadge>
      )}
    </li>
  );
}

function ProductSection({
  title,
  lines,
  testId,
  compact = false,
}: {
  title: string;
  lines: OperatorDisplayLine[];
  testId: string;
  compact?: boolean;
}) {
  if (lines.length === 0) return null;
  return (
    <div className="mt-3" data-testid={testId}>
      <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">{title}</p>
      <ul className="space-y-0">
        {lines.map((line) => (
          <ProductLineRow key={line.key} line={line} compact={compact} />
        ))}
      </ul>
    </div>
  );
}

export interface IntakeV6ModularFormAwarenessPanelProps {
  loadStatus: "loading" | "loaded" | "unavailable" | "fallback";
  preview: ReturnType<typeof import("@/lib/intakeV6/intakeV6ModuleActivationPreview").buildModuleActivationPreview>;
  triggerMismatchNote?: string | null;
  variant?: "review" | "confirm";
  templateCode?: string | null;
}

export default function IntakeV6ModularFormAwarenessPanel({
  loadStatus,
  preview,
  triggerMismatchNote,
  variant = "review",
  templateCode,
}: IntakeV6ModularFormAwarenessPanelProps) {
  const compact = variant === "confirm";
  const view = preview?.operatorView;

  return (
    <div
      className={`${compact ? v6.cardCompact : v6.card} ${compact ? "" : "mb-4"}`}
      data-testid="intake-v6-modular-form-awareness"
      data-contract-status={loadStatus}
    >
      <div className="mb-2">
        <h3 className={v6.sectionTitle}>
          {compact ? "Rezumat produs" : "Rezumat produs pregătit"}
        </h3>
        <p className={v6.sectionDesc} data-testid="intake-v6-modular-panel-subtitle">
          {compact
            ? "Componente pregătite din formular — nu este preț final."
            : "Aceste informații arată ce componente sunt pregătite din formular. Nu reprezintă preț final și nu generează taskuri."}
        </p>
        {!compact ? (
          <p className={`${v6.helper} mt-1`} data-testid="intake-v6-modular-cross-tab-note">
            Rezumat general al produsului — valabil indiferent de tab-ul Finisaje, Iluminare sau Montaj.
          </p>
        ) : null}
      </div>

      {loadStatus === "loading" ? (
        <p className={v6.helper} data-testid="intake-v6-modular-awareness-loading">
          Verific componentele produsului…
        </p>
      ) : null}

      {loadStatus === "fallback" || loadStatus === "unavailable" ? (
        <p className={`${v6.helper} text-slate-400`} data-testid="intake-v6-modular-awareness-unavailable">
          Rezumatul produsului nu este disponibil pentru acest șablon
          {templateCode ? ` (${templateCode})` : ""}. Fluxul operator rămâne neschimbat.
        </p>
      ) : null}

      {view ? (
        <>
          {view.geometryStatus ? (
            <p
              className={`rounded-md border px-3 py-2 text-[11px] ${
                view.geometryStatus.ready
                  ? "border-emerald-500/25 bg-emerald-500/5 text-emerald-100"
                  : "border-amber-500/25 bg-amber-500/5 text-amber-100"
              }`}
              data-testid="intake-v6-modular-geometry-status"
            >
              {view.geometryStatus.label}
            </p>
          ) : null}

          <ProductSection
            title="Produs pregătit"
            lines={view.productReady}
            testId="intake-v6-modular-product-ready"
            compact={compact}
          />

          {view.mounting.length > 0 ? (
            <ProductSection
              title="Montaj și structură"
              lines={view.mounting}
              testId="intake-v6-modular-mounting-section"
              compact={compact}
            />
          ) : view.mountingNotApplicableNote ? (
            <p
              className={`${v6.helper} mt-3`}
              data-testid="intake-v6-modular-mounting-not-applicable"
            >
              {view.mountingNotApplicableNote}
            </p>
          ) : null}

          {preview.missingImportantFields.length > 0 ? (
            <p
              className="mt-3 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100"
              data-testid="intake-v6-modular-missing-summary"
            >
              Mai sunt câmpuri importante de completat înainte de confirmare.
            </p>
          ) : null}

          {triggerMismatchNote && view.mounting.length > 0 ? (
            <p
              className="mt-3 rounded-md border border-sky-500/25 bg-sky-500/5 px-3 py-2 text-[11px] text-sky-100"
              data-testid="intake-v6-modular-mounting-note"
            >
              {triggerMismatchNote}
            </p>
          ) : null}

          {!compact ? (
            <p className={`${v6.helper} mt-3`} data-testid="intake-v6-modular-not-pricing">
              Se va calcula ulterior în ofertare — nu este preț final și nu generează taskuri.
            </p>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
