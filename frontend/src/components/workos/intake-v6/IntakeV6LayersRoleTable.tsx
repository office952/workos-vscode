import { INTAKE_V6_LAYER_ROLE_OPTIONS } from "@/lib/intakeV6/intakeV6LayerRoleOptions";
import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { Layers, Palette, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState, type CSSProperties } from "react";
import IntakeV6CardPagination, { INTAKE_V6_CARD_PAGE_SIZE } from "./IntakeV6CardPagination";
import IntakeV6LayerStatusIcon from "./IntakeV6LayerStatusIcon";
import { resolveLayerColorHumanLabel } from "./layerColorDisplay";
import { v6 } from "./atoms/intakeV6Presentation";

const LAYER_ROLE_LABEL_BY_VALUE = new Map(
  INTAKE_V6_LAYER_ROLE_OPTIONS.map((option) => [option.value, option.label]),
);

function resolveLayerKindLabel(kind: string | null | undefined): string {
  if (kind === "real") return "Strat vector client";
  if (kind === "pseudo") return "Strat generat";
  if (kind === "raster_artwork") return "Artwork raster";
  return "—";
}

function resolveRoleLabel(role: string | null | undefined): string {
  if (!role) return "—";
  return LAYER_ROLE_LABEL_BY_VALUE.get(role as LayerAutoRole) ?? role;
}

function resolveOperatorLayerName(report: SvgAnalysisCoreReport, layer: SvgAnalysisCoreReport["layers"][number]): string {
  const sourceFileName = (report.sourceFileName ?? "").trim().toLowerCase();
  const name = (layer.name ?? "").trim().toLowerCase().replace(/-/g, " ");
  const id = (layer.id ?? "").trim().toLowerCase().replace(/-/g, " ");
  if (sourceFileName === "logo.svg" && (name === "logo stanga" || name === "logo dreapta" || id === "logo stanga" || id === "logo dreapta")) {
    return "Logo volumetric";
  }
  return layer.name;
}

function resolveLayerRow(
  report: SvgAnalysisCoreReport,
  confirmation: LayerRoleConfirmation,
  layer: SvgAnalysisCoreReport["layers"][number],
) {
  const entry =
    confirmation.layers.find(
      (item) => item.layerKey === layer.id || item.layerKey === layer.name,
    ) ?? confirmation.layers.find((item) => item.layerName === layer.name);
  const layerKey = entry?.layerKey ?? layer.id ?? layer.name;
  const selectedRole = entry?.confirmedRole ?? layer.autoRole;
  const requiresAttention =
    entry?.confirmationState !== "confirmed" || layer.layerKind === "raster_artwork";
  return { entry, layerKey, selectedRole, requiresAttention };
}

function LayerRoleSelect({
  layerKey,
  selectedRole,
  onUpdateLayerRole,
}: {
  layerKey: string;
  selectedRole: LayerAutoRole;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
}) {
  return (
    <select
      className="w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[12px] text-slate-200"
      value={selectedRole}
      onChange={(event) => onUpdateLayerRole(layerKey, event.target.value as LayerAutoRole)}
      data-testid={`intake-v6-layer-role-${layerKey}`}
    >
      {INTAKE_V6_LAYER_ROLE_OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function LayerStatusBadge({
  state,
  layerKey,
}: {
  state: LayerRoleConfirmation["layers"][number]["confirmationState"] | undefined;
  layerKey: string;
}) {
  return (
    <IntakeV6LayerStatusIcon
      state={state}
      testId={`intake-v6-layer-status-icon-${layerKey}`}
    />
  );
}

function colorSwatchStyle(color: string | undefined): CSSProperties | undefined {
  const token = color?.trim();
  if (!token) return undefined;
  if (/^#[0-9a-f]{3,8}$/i.test(token)) return { backgroundColor: token };
  if (/^rgb/i.test(token)) return { backgroundColor: token };
  return undefined;
}

function LayerLegendRow({
  layer,
  report,
  confirmation,
  onUpdateLayerRole,
  focused,
  onFocus,
  onBlur,
}: {
  layer: SvgAnalysisCoreReport["layers"][number];
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
  focused?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
}) {
  const { entry, layerKey, selectedRole, requiresAttention } = resolveLayerRow(
    report,
    confirmation,
    layer,
  );
  const colorToken = layer.colors?.[0];
  const colorLabel = colorToken
    ? resolveLayerColorHumanLabel(colorToken, report)
    : layer.paintEvidence.paintKind ?? "—";
  const RowIcon = layer.layerKind === "raster_artwork" ? Palette : Layers;

  return (
    <li
      className={`rounded-md border px-2.5 py-2 transition ${
        focused
          ? "border-cyan-400/40 bg-cyan-400/5"
          : requiresAttention
            ? "border-amber-500/25 bg-amber-500/5"
            : "border-[#2A3548]/70 bg-[#0A0F1A]/50"
      }`}
      data-testid={`intake-v6-layer-legend-${layerKey}`}
      onMouseEnter={onFocus}
      onMouseLeave={onBlur}
      onFocus={onFocus}
      onBlur={onBlur}
    >
      <div className="mb-1.5 flex items-start gap-2">
        <span
          className="mt-0.5 h-3.5 w-3.5 shrink-0 rounded border border-slate-600/80"
          style={colorSwatchStyle(colorToken) ?? { backgroundColor: "#64748b" }}
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1 truncate text-[12px] font-semibold text-slate-100">
            <RowIcon className="h-3 w-3 shrink-0 text-cyan-400/80" aria-hidden />
            {resolveOperatorLayerName(report, layer)}
          </p>
          <p className="truncate text-[11px] text-slate-500">{colorLabel}</p>
        </div>
        <LayerStatusBadge state={entry?.confirmationState} layerKey={layerKey} />
      </div>
      <LayerRoleSelect
        layerKey={layerKey}
        selectedRole={selectedRole}
        onUpdateLayerRole={onUpdateLayerRole}
      />
    </li>
  );
}

function LayerCard({
  layer,
  report,
  confirmation,
  onUpdateLayerRole,
  focused = false,
  onFocus,
  onBlur,
}: {
  layer: SvgAnalysisCoreReport["layers"][number];
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
  focused?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
}) {
  const { entry, layerKey, selectedRole, requiresAttention } = resolveLayerRow(
    report,
    confirmation,
    layer,
  );
  const colorLabel = layer.colors?.[0]
    ? resolveLayerColorHumanLabel(layer.colors[0], report)
    : layer.paintEvidence.paintKind ?? "—";
  const CardIcon = layer.layerKind === "raster_artwork" ? Palette : Layers;
  return (
    <article
      className={`rounded-md border px-3 py-3 transition outline-none focus-visible:ring-1 focus-visible:ring-cyan-400/50 ${
        focused
          ? "border-cyan-400/40 bg-cyan-400/5"
          : requiresAttention
            ? "border-amber-500/30 bg-amber-500/5"
            : "border-[#2A3548]/80 bg-[#0A0F1A]/40"
      }`}
      data-testid={`intake-v6-layer-row-${layerKey}`}
      tabIndex={0}
      onMouseEnter={onFocus}
      onMouseLeave={onBlur}
      onFocus={onFocus}
      onBlur={onBlur}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 truncate text-[12px] font-semibold text-slate-100">
            <CardIcon className="h-3.5 w-3.5 shrink-0 text-cyan-400/80" aria-hidden />
            {resolveOperatorLayerName(report, layer)}
          </p>
          <p className="text-[11px] text-slate-500">
            {resolveLayerKindLabel(layer.layerKind)} · {colorLabel}
          </p>
        </div>
        <LayerStatusBadge state={entry?.confirmationState} layerKey={layerKey} />
      </div>
      <p className="mb-2 flex items-center gap-1.5 text-[11px] text-slate-400">
        <Sparkles className="h-3 w-3 shrink-0 text-slate-500" aria-hidden />
        {resolveRoleLabel(layer.autoRole)}
        <span className="text-slate-600">·</span>
        <span className="text-slate-500">{layer.autoConfidence}</span>
      </p>
      {requiresAttention && entry?.confirmationState !== "confirmed" ? (
        <p
          className="mb-2 flex items-center gap-1 text-[11px] text-amber-300/90"
          title="Necesită verificare operator"
        >
          <IntakeV6LayerStatusIcon state="pending" size="sm" />
          <span className="sr-only">Necesită verificare operator</span>
        </p>
      ) : null}
      <LayerRoleSelect
        layerKey={layerKey}
        selectedRole={selectedRole}
        onUpdateLayerRole={onUpdateLayerRole}
      />
    </article>
  );
}

export default function IntakeV6LayersRoleTable({
  report,
  confirmation,
  onUpdateLayerRole,
  compact = false,
  layout = compact ? "cards" : "table",
  hoveredLayerKey = null,
  onHoverLayerKey,
}: {
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
  compact?: boolean;
  layout?: "table" | "cards" | "legend";
  hoveredLayerKey?: string | null;
  onHoverLayerKey?: (layerKey: string | null) => void;
}) {
  const [pageIndex, setPageIndex] = useState(0);
  const [internalHoveredLayerKey, setInternalHoveredLayerKey] = useState<string | null>(null);
  const focusedLayerKey = hoveredLayerKey ?? internalHoveredLayerKey;
  const setFocusedLayerKey = onHoverLayerKey ?? setInternalHoveredLayerKey;
  const pageCount = Math.max(1, Math.ceil(report.layers.length / INTAKE_V6_CARD_PAGE_SIZE));
  const paginatedLayers = useMemo(() => {
    if (report.layers.length <= INTAKE_V6_CARD_PAGE_SIZE) return report.layers;
    const start = pageIndex * INTAKE_V6_CARD_PAGE_SIZE;
    return report.layers.slice(start, start + INTAKE_V6_CARD_PAGE_SIZE);
  }, [pageIndex, report.layers]);

  useEffect(() => {
    setPageIndex((current) => Math.min(current, pageCount - 1));
  }, [pageCount]);

  if (layout === "legend") {
    return (
      <ul
        className="space-y-2"
        data-testid="intake-v6-layer-legend"
        onMouseLeave={() => setFocusedLayerKey(null)}
      >
        {report.layers.map((layer) => {
          const { layerKey } = resolveLayerRow(report, confirmation, layer);
          return (
            <LayerLegendRow
              key={layer.id}
              layer={layer}
              report={report}
              confirmation={confirmation}
              onUpdateLayerRole={onUpdateLayerRole}
              focused={focusedLayerKey === layerKey}
              onFocus={() => setFocusedLayerKey(layerKey)}
              onBlur={() => setFocusedLayerKey(null)}
            />
          );
        })}
      </ul>
    );
  }

  if (layout === "cards") {
    return (
      <div className="min-w-0" data-testid="intake-v6-layer-table">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h3 className={v6.sectionTitle}>Decizii straturi</h3>
            <p className={v6.sectionDesc}>
              Confirmă rolul propus pentru fiecare strat detectat înainte de Review.
            </p>
          </div>
          <span className={`${v6.mono} ${v6.metricLabel}`}>
            {report.layers.length} straturi
          </span>
        </div>
        {report.layers.length > INTAKE_V6_CARD_PAGE_SIZE ? (
          <IntakeV6CardPagination
            pageIndex={pageIndex}
            pageCount={pageCount}
            totalItems={report.layers.length}
            onPageChange={setPageIndex}
            testId="intake-v6-layer-card-pagination"
          />
        ) : null}
        <div
          className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
          data-testid="intake-v6-layer-card-grid"
          onMouseLeave={() => setFocusedLayerKey(null)}
        >
          {paginatedLayers.map((layer) => {
            const { layerKey } = resolveLayerRow(report, confirmation, layer);
            return (
              <LayerCard
                key={layer.id}
                layer={layer}
                report={report}
                confirmation={confirmation}
                onUpdateLayerRole={onUpdateLayerRole}
                focused={focusedLayerKey === layerKey}
                onFocus={() => setFocusedLayerKey(layerKey)}
                onBlur={() => setFocusedLayerKey(null)}
              />
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className={`${compact ? "" : v6.card} min-w-0 overflow-x-auto`} data-testid="intake-v6-layer-table">
      <h3 className={`mb-3 ${v6.sectionTitle}`}>Roluri straturi</h3>
      <table className="w-full min-w-[560px] text-left text-[12px]">
        <thead className="text-slate-500">
          <tr>
            <th className="pb-2 pr-3">Strat</th>
            <th className="pb-2 pr-3">Tip</th>
            <th className="pb-2 pr-3">Sugestie</th>
            <th className="pb-2 pr-3">Culoare</th>
            <th className="pb-2 pr-3">Rol confirmat</th>
            <th className="pb-2">Stare</th>
          </tr>
        </thead>
        <tbody>
          {report.layers.map((layer) => {
            const { entry, layerKey, selectedRole, requiresAttention } = resolveLayerRow(
              report,
              confirmation,
              layer,
            );
            return (
              <tr
                key={layer.id}
                className={`border-t border-[#2A3548] ${requiresAttention ? "bg-amber-500/5" : ""}`}
                data-testid={`intake-v6-layer-row-${layerKey}`}
              >
                <td className="py-2 pr-3 font-medium text-slate-200">{layer.name}</td>
                <td className="py-2 pr-3 text-slate-400">{resolveLayerKindLabel(layer.layerKind)}</td>
                <td className="py-2 pr-3 text-slate-400">
                  <div>{resolveRoleLabel(layer.autoRole)}</div>
                  <div className={v6.metricLabel}>încredere {layer.autoConfidence}</div>
                </td>
                <td className="py-2 pr-3 text-slate-400">
                  {layer.colors?.[0] ?? layer.paintEvidence.paintKind ?? "—"}
                </td>
                <td className="py-2 pr-3">
                  <LayerRoleSelect
                    layerKey={layerKey}
                    selectedRole={selectedRole}
                    onUpdateLayerRole={onUpdateLayerRole}
                  />
                </td>
                <td className="py-2">
                  <LayerStatusBadge state={entry?.confirmationState} layerKey={layerKey} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
