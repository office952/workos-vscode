/**
 * AcmPanel Blueprint L1-P schematic — read-only SVG projection.
 * No edit callbacks, no persistence, no operatorPatch.
 */

import { useId, useMemo, useState, type ReactNode } from "react";
import {
  buildAcmPanelBlueprintReadModel,
  type AcmBlueprintCalloutStyle,
  type AcmPanelBlueprintReadModel,
} from "@/lib/intakeV6/acmPanel/blueprintReadModel";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";

function strokeForStyle(style: AcmBlueprintCalloutStyle): {
  strokeDasharray?: string;
  strokeWidth: number;
  opacity: number;
} {
  switch (style) {
    case "solid_final":
      return { strokeWidth: 1.5, opacity: 1 };
    case "solid_subtle":
      return { strokeWidth: 1, opacity: 0.9 };
    case "dashed_proposed":
      return { strokeDasharray: "4 3", strokeWidth: 1.25, opacity: 0.95 };
    case "dashed_catalog":
      return { strokeDasharray: "3 3", strokeWidth: 1, opacity: 0.7 };
    case "warning":
      return { strokeDasharray: "2 2", strokeWidth: 1.25, opacity: 1 };
    case "omitted":
    default:
      return { strokeWidth: 0, opacity: 0 };
  }
}

function formatDim(value: number): string {
  return Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10);
}

function panelCountLabel(count: number): string {
  return count === 1 ? "1 panou" : `${count} panouri`;
}

function FrontSchematic({ model }: { model: AcmPanelBlueprintReadModel }) {
  const titleId = useId();
  const assembly = model.assembly;
  if (!assembly) return null;

  const pad = 36;
  const dimBand = 28;
  const vbW = assembly.width_mm + pad * 2;
  const vbH = assembly.height_mm + pad * 2 + dimBand;
  const ox = pad;
  const oy = pad;

  const overallStyle = strokeForStyle(
    model.callouts.find((c) => c.id === "overall_width")?.style ?? "dashed_proposed",
  );
  const panelStyle = strokeForStyle(
    model.panels[0] ? authorityToLineStyle(model.panels[0].authority) : "dashed_proposed",
  );

  return (
    <svg
      role="img"
      aria-labelledby={titleId}
      viewBox={`0 0 ${vbW} ${vbH}`}
      className="h-auto w-full max-h-[280px]"
      data-testid="intake-v6-acm-blueprint-front-svg"
      data-assembly-width={assembly.width_mm}
      data-assembly-height={assembly.height_mm}
    >
      <title id={titleId}>
        Schematic AcmPanel {formatDim(assembly.width_mm)} pe {formatDim(assembly.height_mm)} milimetri
      </title>
      <desc>
        Vedere față provizorie cu {model.panels.length} panouri. Nu este desen de execuție.
      </desc>
      <rect
        x={ox}
        y={oy}
        width={assembly.width_mm}
        height={assembly.height_mm}
        fill="none"
        stroke="#94a3b8"
        strokeWidth={overallStyle.strokeWidth}
        strokeDasharray={overallStyle.strokeDasharray}
        opacity={overallStyle.opacity}
        data-testid="intake-v6-acm-blueprint-assembly-bounds"
      />
      {model.panels.map((p) => (
        <g key={p.id} data-testid={`intake-v6-acm-blueprint-panel-${p.id}`}>
          <rect
            x={ox + p.x_mm}
            y={oy + p.y_mm}
            width={p.width_mm}
            height={p.height_mm}
            fill="#1e293b"
            fillOpacity={0.35}
            stroke="#cbd5e1"
            strokeWidth={panelStyle.strokeWidth}
            strokeDasharray={
              strokeForStyle(authorityToLineStyle(p.authority)).strokeDasharray
            }
          />
          <text
            x={ox + p.x_mm + p.width_mm / 2}
            y={oy + p.y_mm + p.height_mm / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#e2e8f0"
            fontSize={Math.min(28, Math.max(12, p.width_mm / 18))}
          >
            {p.order}
          </text>
          <text
            x={ox + p.x_mm + 8}
            y={oy + p.y_mm + 18}
            fill="#94a3b8"
            fontSize={12}
          >
            {formatDim(p.width_mm)}×{formatDim(p.height_mm)}
          </text>
        </g>
      ))}
      {model.joints.map((j) => (
        <line
          key={j.id}
          x1={ox + j.x1_mm}
          y1={oy + j.y1_mm}
          x2={ox + j.x2_mm}
          y2={oy + j.y2_mm}
          stroke="#fbbf24"
          strokeWidth={1.5}
          strokeDasharray="5 3"
          data-testid={`intake-v6-acm-blueprint-joint-${j.id}`}
          data-joint-x={j.orientation === "VERTICAL" ? j.x1_mm : undefined}
        >
          <title>{j.note} · {j.statusLabel}</title>
        </line>
      ))}
      <text
        x={ox + assembly.width_mm / 2}
        y={oy + assembly.height_mm + 20}
        textAnchor="middle"
        fill="#e2e8f0"
        fontSize={14}
        fontWeight={600}
        data-testid="intake-v6-acm-blueprint-overall-label"
      >
        {formatDim(assembly.width_mm)} × {formatDim(assembly.height_mm)} mm
      </text>
    </svg>
  );
}

function authorityToLineStyle(
  authority: string,
): AcmBlueprintCalloutStyle {
  if (authority === "operator_confirmed") return "solid_final";
  if (authority === "detected") return "solid_subtle";
  if (authority === "catalog_default") return "dashed_catalog";
  if (authority === "proposed") return "dashed_proposed";
  return "warning";
}

function ConstructionBlock({ model }: { model: AcmPanelBlueprintReadModel }) {
  const section = model.constructionSection;
  if (!section) return null;
  const rows = [
    section.thickness,
    section.l1,
    section.l2,
    section.foldCount,
  ].filter((r) => r.present && r.value != null && r.style !== "omitted");

  if (!rows.length) return null;

  return (
    <div
      className="mt-2 rounded border border-wo-border-strong/50 bg-wo-surface-inset/40 px-2 py-1.5"
      data-testid="intake-v6-acm-blueprint-construction"
    >
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Secțiune construcție (provizoriu)
      </div>
      <ul className="space-y-0.5 text-[11px] text-slate-300">
        {rows.map((r) => (
          <li
            key={r.id}
            data-testid={`intake-v6-acm-blueprint-construction-${r.id}`}
            data-authority={r.authority}
            data-style={r.style}
            className={
              r.style === "dashed_catalog" || r.style === "dashed_proposed"
                ? "text-slate-400"
                : ""
            }
          >
            <span className="text-slate-500">{r.label}:</span>{" "}
            {typeof r.value === "number" ? formatDim(r.value) : String(r.value)}
            {r.unit ? ` ${r.unit}` : ""}
            {intakeV6ShowOperatorConfigStatusBadges() ? (
              <span className="text-[10px] text-slate-500">
                {" "}
                (
                {r.authority === "catalog_default"
                  ? "Propunere catalog"
                  : r.authority === "proposed"
                    ? "Propus"
                    : r.authority === "detected"
                      ? "Detectat"
                      : r.authority === "operator_confirmed"
                        ? "Confirmat"
                        : r.authority}
                )
              </span>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export type IntakeV6AcmPanelBlueprintPreviewProps = {
  finishSetup?: unknown;
  payload?: Record<string, unknown> | null;
  /** Optional prebuilt model (tests). */
  model?: AcmPanelBlueprintReadModel;
  defaultExpanded?: boolean;
  /**
   * standalone — own sticky card (lab / default)
   * embedded — borderless slot inside a shared tech strip (workbench)
   */
  chrome?: "standalone" | "embedded";
  /** Extra plain-text meta on the embedded collapsed row (e.g. clean validation). */
  inlineMeta?: ReactNode;
};

/**
 * Sticky collapsed blueprint slot. Read-only — no write props.
 */
export default function IntakeV6AcmPanelBlueprintPreview({
  finishSetup,
  payload,
  model: modelProp,
  defaultExpanded = false,
  chrome = "standalone",
  inlineMeta = null,
}: IntakeV6AcmPanelBlueprintPreviewProps) {
  const model = useMemo(
    () =>
      modelProp ??
      buildAcmPanelBlueprintReadModel({
        finishSetup,
        payload: payload ?? null,
      }),
    [modelProp, finishSetup, payload],
  );

  const [expanded, setExpanded] = useState(defaultExpanded);

  if (model.readiness === "L0") {
    return null;
  }

  const summary = model.assembly
    ? `${formatDim(model.assembly.width_mm)} × ${formatDim(model.assembly.height_mm)} mm · ${panelCountLabel(model.panels.length)}`
    : model.collapsedSummary;
  const embedded = chrome === "embedded";

  return (
    <div
      className={
        embedded
          ? "z-[1]"
          : "sticky top-2 z-[1] rounded border border-wo-border-strong/60 bg-wo-surface-input/90"
      }
      data-testid="intake-v6-acm-blueprint-preview"
      data-readiness={model.readiness}
      data-expanded={expanded ? "true" : "false"}
      data-chrome={chrome}
    >
      <button
        type="button"
        className="w-full px-2.5 py-1 text-left"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        aria-controls="intake-v6-acm-blueprint-panel"
        data-testid="intake-v6-acm-blueprint-toggle"
      >
        {embedded ? (
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="shrink-0 text-[11px] font-semibold text-wo-text-primary">
              Previzualizare
            </span>
            <span
              className="min-w-0 truncate text-[11px] text-slate-400"
              data-testid="intake-v6-acm-blueprint-collapsed-summary"
            >
              {summary}
            </span>
            {inlineMeta ? (
              <>
                <span className="text-[10px] text-slate-600" aria-hidden="true">
                  ·
                </span>
                <span className="min-w-0 text-[10px] text-slate-400">{inlineMeta}</span>
              </>
            ) : null}
            <span className="ml-auto shrink-0 text-[10px] text-slate-500">
              {expanded ? "▾" : "▸"}
            </span>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-wo-text-primary">
                Previzualizare tehnică
              </span>
              {intakeV6ShowOperatorConfigStatusBadges() ? (
                <span
                  className="rounded border border-amber-500/30 px-1.5 py-0.5 text-[10px] text-amber-200"
                  data-testid="intake-v6-acm-blueprint-readiness-badge"
                >
                  Nivel {model.readiness}
                  {model.readiness === "L1-P" ? " · Provizoriu" : ""}
                  {model.readiness === "L1-B" ? " · Blocat" : ""}
                  {model.readiness === "L1-C" ? " · Confirmat" : ""}
                </span>
              ) : null}
              <span className="ml-auto text-[10px] text-slate-500">
                {expanded ? "▾" : "▸"}
              </span>
            </div>
            <div
              className="mt-0.5 text-[11px] text-slate-400"
              data-testid="intake-v6-acm-blueprint-collapsed-summary"
            >
              {summary}
            </div>
          </>
        )}
      </button>

      {expanded ? (
        <div
          id="intake-v6-acm-blueprint-panel"
          className="border-t border-wo-border-strong/50 px-2.5 py-1.5"
          data-testid="intake-v6-acm-blueprint-expanded"
        >
          <p
            className="mb-1.5 text-[11px] font-medium text-amber-100/90"
            data-testid="intake-v6-acm-blueprint-disclaimer"
          >
            {model.disclaimer}
          </p>
          {model.provisionalNote ? (
            <p
              className="mb-2 text-[10px] text-slate-400"
              data-testid="intake-v6-acm-blueprint-provisional-note"
            >
              {model.provisionalNote}
            </p>
          ) : null}

          {model.compositionInconsistency ? (
            <div
              className="mb-2 rounded border border-rose-500/40 bg-rose-950/40 px-2 py-1.5 text-[11px] text-rose-100"
              data-testid="intake-v6-acm-blueprint-composition-banner"
              role="status"
            >
              {model.compositionInconsistencyMessage ?? "Inconsistență compoziție"}
            </div>
          ) : null}

          {model.readiness === "L1-B" ? (
            <div
              className="mb-2 rounded border border-amber-500/40 bg-amber-950/30 px-2 py-1.5 text-[11px] text-amber-100"
              data-testid="intake-v6-acm-blueprint-blocked"
              role="alert"
            >
              {model.blockers[0] ?? "Geometrie blocată pentru schematic."}
            </div>
          ) : null}

          {model.readiness !== "L1-B" ? <FrontSchematic model={model} /> : null}

          {intakeV6ShowOperatorConfigStatusBadges() ? (
            <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-slate-500" aria-hidden="true">
              <span className="inline-flex items-center gap-1">
                <span className="inline-block h-px w-3 border-t border-slate-300" /> Confirmat/detectat
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="inline-block h-px w-3 border-t border-dashed border-amber-300" /> Propus
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="inline-block h-px w-3 border-t border-dashed border-slate-500" /> Catalog
              </span>
            </div>
          ) : (
            <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-slate-500" aria-hidden="true">
              <span className="inline-flex items-center gap-1">
                <span className="inline-block h-px w-3 border-t border-slate-300" /> Final
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="inline-block h-px w-3 border-t border-dashed border-amber-300" /> Provizoriu
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="inline-block h-px w-3 border-t border-dashed border-slate-500" /> Catalog
              </span>
            </div>
          )}

          {model.letterPlacementUnknown ? (
            <p
              className="mt-2 text-[10px] text-slate-400"
              data-testid="intake-v6-acm-blueprint-letter-unknown"
            >
              Plasarea literelor pe panou este necunoscută
            </p>
          ) : null}

          {(model.warnings.length > 0 || model.missing.length > 0) && (
            <ul
              className="mt-2 space-y-0.5 text-[10px] text-slate-500"
              data-testid="intake-v6-acm-blueprint-warnings"
            >
              {model.missing.map((m) => (
                <li key={`m-${m}`}>Lipsă: {m}</li>
              ))}
              {model.warnings.slice(0, 4).map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}

          <ConstructionBlock model={model} />

          <details className="mt-2 text-[10px] text-slate-500">
            <summary className="cursor-pointer select-none">Provenance</summary>
            <div className="mt-1 space-y-0.5" data-testid="intake-v6-acm-blueprint-provenance">
              <div>Instance: {model.provenance.instanceId ?? "—"}</div>
              <div>Source: {model.provenance.source}</div>
              <div>Segmented: {model.provenance.segmentedStatus ?? "—"}</div>
            </div>
          </details>
        </div>
      ) : null}
    </div>
  );
}
