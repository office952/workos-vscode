import {
  INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS,
  getIntakeV6OwnerRoleLabel,
  normalizeIntakeV6OwnerSelectableRole,
} from "@/lib/intakeV6/intakeV6LayerRoleOptions";
import { buildIntakeV6LayerDisplayLabel } from "@/lib/intakeV6/intakeV6LayerDisplayLabel";
import { buildOperatorLogoLabelMap, getOperatorLayerLabel } from "@/lib/intakeV6/intakeV4OperatorUiDisplay";
import {
  layerConfirmationStateLabelRo,
  operatorBindingStatusLabelRo,
  operatorGuardedLabelRo,
  operatorStatusSemanticRo,
} from "@/lib/intakeV6/intakeV6OperatorVocabulary";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";
import { INTAKE_V6_LETTERS_TEMPLATE_CODE, INTAKE_V6_LOGO_TEMPLATE_CODE, resolveIntakeV6LayerTargetTemplate } from "@/lib/intakeV6/intakeV6LayerTargetTemplate";
import {
  bindableForOwnerLayerRole,
  ownerFacingComponentProductLabel,
  type SvgComponentBinding,
} from "@/lib/intakeV6/svgComponentBindings";
import type { SvgBindableComponent } from "@/lib/api";
import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { Layers, Palette, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import IntakeV6CardPagination, { INTAKE_V6_CARD_PAGE_SIZE } from "./IntakeV6CardPagination";
import IntakeV6LayerStatusIcon from "./IntakeV6LayerStatusIcon";
import { resolveLayerColorHumanLabel } from "./layerColorDisplay";
import { v6 } from "./atoms/intakeV6Presentation";

const INTAKE_V6_NO_PAGINATION_MAX_LAYERS = 6;

function resolveLayerKindLabel(kind: string | null | undefined): string {
  if (kind === "real") return "Strat vector client";
  if (kind === "pseudo") return "Strat generat";
  if (kind === "raster_artwork") return "Artwork raster";
  return "—";
}

function resolveRoleLabel(role: string | null | undefined): string {
  return getIntakeV6OwnerRoleLabel(role);
}

function resolveOperatorLayerName(report: SvgAnalysisCoreReport, layer: SvgAnalysisCoreReport["layers"][number]): string {
  const sourceFileName = (report.sourceFileName ?? "").trim().toLowerCase();
  const name = (layer.name ?? "").trim().toLowerCase().replace(/-/g, " ");
  const id = (layer.id ?? "").trim().toLowerCase().replace(/-/g, " ");
  const logoLabelMap = buildOperatorLogoLabelMap(report.layers);
  if (sourceFileName === "logo.svg" && (name === "logo stanga" || name === "logo dreapta" || id === "logo stanga" || id === "logo dreapta")) {
    return "Logo volumetric";
  }
  return getOperatorLayerLabel(layer.id, layer.name, { logoLabelMap });
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
  layer,
  layerKey,
  selectedRole,
  onUpdateLayerRole,
  workspaceTemplateCode,
}: {
  layer: SvgAnalysisCoreReport["layers"][number];
  layerKey: string;
  selectedRole: LayerAutoRole;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
  workspaceTemplateCode?: string | null;
}) {
  const target = resolveIntakeV6LayerTargetTemplate({
    layer,
    selectedRole,
    workspaceTemplateCode,
  });
  const normalizedSelectedRole = normalizeIntakeV6OwnerSelectableRole({
    layer,
    confirmedRole: selectedRole,
    targetTemplateCode: target.templateCode,
  });

  return (
    <label className="block">
      <span className="mb-1 block text-[11px] text-slate-400">Rol geometrie</span>
      <select
        className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-slate-200"
        value={normalizedSelectedRole}
        onChange={(event) => onUpdateLayerRole(layerKey, event.target.value as LayerAutoRole)}
        data-testid={`intake-v6-layer-role-${layerKey}`}
      >
        {INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function LayerComponentBindingSummary({
  layerKey,
  selectedRole,
  bindables,
  bindings,
}: {
  layerKey: string;
  selectedRole: LayerAutoRole;
  bindables?: SvgBindableComponent[];
  bindings?: SvgComponentBinding[];
}) {
  const bindable = bindableForOwnerLayerRole(bindables ?? [], selectedRole);
  if (!bindable) return null;
  const bound = (bindings ?? []).find(
    (b) => b.component_template_code === bindable.component_template_code,
  );
  const isSupport = bound?.geometry_role === "SUPPORT_CONTOUR" || selectedRole === "support_panel";
  const includesGeometry = isSupport
    ? Boolean(
        bound &&
          (bound.selected_geometry.element_ids.length > 0 ||
            bound.selected_geometry.geometry_hashes.length > 0),
      )
    : (bound?.selected_geometry.layer_ids.includes(layerKey) ?? false);
  const statusLabel = !bound
    ? "Neasociat"
    : bound.status === "CONFIRMED" && includesGeometry
      ? operatorStatusSemanticRo("confirmed")
      : bound.status === "RECONFIRM_REQUIRED"
        ? operatorBindingStatusLabelRo("reconfirm_required")
        : includesGeometry
          ? "Selectat"
          : operatorBindingStatusLabelRo("suggested");
  const guarded = Boolean(bindable.guards?.length);

  return (
    <div
      className="mt-2 rounded border border-wo-border-strong/80 bg-wo-surface-inset/70 px-2 py-1.5"
      data-testid={`intake-v6-layer-component-${layerKey}`}
    >
      <p className="text-[10px] uppercase tracking-wide text-slate-500">Componentă produs</p>
      <p className="text-[12px] font-medium text-wo-text-primary">
        {ownerFacingComponentProductLabel(bindable)}
      </p>
      <p className="mt-0.5 flex flex-wrap gap-x-2 gap-y-0.5 text-[10px] text-slate-400">
        <span>{bindable.required ? "Obligatoriu" : "Opțional"}</span>
        <span>·</span>
        <span data-testid={`intake-v6-layer-component-status-${layerKey}`}>{statusLabel}</span>
        {guarded ? (
          <>
            <span>·</span>
            <span className="text-amber-200/90" data-testid={`intake-v6-layer-component-guard-${layerKey}`}>
              {operatorGuardedLabelRo()}
            </span>
          </>
        ) : null}
      </p>
      <details className="mt-1">
        <summary className="cursor-pointer text-[10px] text-slate-500">Detalii tehnice</summary>
        <p className="mt-0.5 font-mono text-[10px] text-slate-500">
          {bindable.component_template_code}
        </p>
      </details>
    </div>
  );
}

function LayerStatusBadge({
  state,
  layerKey,
  hidden = false,
}: {
  state: LayerRoleConfirmation["layers"][number]["confirmationState"] | undefined;
  layerKey: string;
  hidden?: boolean;
}) {
  if (hidden) return null;
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

function confirmationStateLabelRo(
  state: LayerRoleConfirmation["layers"][number]["confirmationState"] | undefined,
): string {
  return layerConfirmationStateLabelRo(state);
}

function LayerLegendRow({
  layer,
  report,
  confirmation,
  onUpdateLayerRole,
  workspaceTemplateCode,
  layerIndex,
  focused,
  onFocus,
  onBlur,
}: {
  layer: SvgAnalysisCoreReport["layers"][number];
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
  workspaceTemplateCode?: string | null;
  layerIndex: number;
  focused?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
}) {
  const { entry, layerKey, selectedRole, requiresAttention } = resolveLayerRow(
    report,
    confirmation,
    layer,
  );
  const display = buildIntakeV6LayerDisplayLabel(layer, layerIndex, report);
  const colorToken = layer.colors?.[0];
  const RowIcon = layer.layerKind === "raster_artwork" ? Palette : Layers;
  const hideLayerStatusIcons = confirmation.confirmationStatus === "complete";
  const stateLabel = confirmationStateLabelRo(entry?.confirmationState);

  return (
    <li
      className={`rounded-md border px-2.5 py-2 transition ${
        focused
          ? "border-cyan-400/40 bg-cyan-400/5"
          : requiresAttention
            ? "border-amber-500/25 bg-amber-500/5"
            : "border-wo-border-strong/70 bg-wo-surface-inset/50"
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
          <p className="flex items-center gap-1 truncate text-[12px] font-semibold text-wo-text-primary">
            <RowIcon className="h-3 w-3 shrink-0 text-cyan-400/80" aria-hidden />
            {display.primaryLabel}
          </p>
          <p className="truncate text-[11px] text-slate-500">{display.secondaryLabel}</p>
          <p
            className={`text-[10px] ${
              entry?.confirmationState === "confirmed" ? "text-emerald-300/90" : "text-amber-200/90"
            }`}
            data-testid={`intake-v6-layer-confirm-state-${layerKey}`}
          >
            {stateLabel}
          </p>
        </div>
        <LayerStatusBadge state={entry?.confirmationState} layerKey={layerKey} hidden={hideLayerStatusIcons} />
      </div>
      <LayerRoleSelect
        layer={layer}
        layerKey={layerKey}
        selectedRole={selectedRole}
        onUpdateLayerRole={onUpdateLayerRole}
        workspaceTemplateCode={workspaceTemplateCode}
      />
      <IntakeV6TechnicalDetailsAccordion
        title="Detalii tehnice analiză"
        hint="ID intern strat"
        defaultOpen={false}
        testId={`intake-v6-layer-legend-advanced-${layerKey}`}
        className="mt-1.5"
      >
        <p className="font-mono text-[10px] text-slate-500">{display.technicalKey}</p>
        {colorToken ? (
          <p className="font-mono text-[10px] text-slate-500">
            culoare: {resolveLayerColorHumanLabel(colorToken, report)} ({colorToken})
          </p>
        ) : null}
      </IntakeV6TechnicalDetailsAccordion>
    </li>
  );
}

function LayerCard({
  layer,
  report,
  confirmation,
  onUpdateLayerRole,
  workspaceTemplateCode,
  layerIndex = 0,
  focused = false,
  onFocus,
  onBlur,
}: {
  layer: SvgAnalysisCoreReport["layers"][number];
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
  workspaceTemplateCode?: string | null;
  layerIndex?: number;
  focused?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
}) {
  const { entry, layerKey, selectedRole, requiresAttention } = resolveLayerRow(
    report,
    confirmation,
    layer,
  );
  const display = buildIntakeV6LayerDisplayLabel(layer, layerIndex, report);
  const CardIcon = layer.layerKind === "raster_artwork" ? Palette : Layers;
  const hideLayerStatusIcons = confirmation.confirmationStatus === "complete";
  return (
    <article
      className={`rounded-md border px-3 py-3 transition outline-none focus-visible:ring-1 focus-visible:ring-cyan-400/50 ${
        focused
          ? "border-cyan-400/40 bg-cyan-400/5"
          : requiresAttention
            ? "border-amber-500/30 bg-amber-500/5"
            : "border-wo-border-strong/80 bg-wo-surface-inset/40"
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
          <p className="flex items-center gap-1.5 truncate text-[12px] font-semibold text-wo-text-primary">
            <CardIcon className="h-3.5 w-3.5 shrink-0 text-cyan-400/80" aria-hidden />
            {display.primaryLabel}
          </p>
          <p className="text-[11px] text-slate-500">{display.secondaryLabel}</p>
          <p
            className={`text-[10px] ${
              entry?.confirmationState === "confirmed" ? "text-emerald-300/90" : "text-amber-200/90"
            }`}
          >
            {confirmationStateLabelRo(entry?.confirmationState)}
          </p>
        </div>
        <LayerStatusBadge state={entry?.confirmationState} layerKey={layerKey} hidden={hideLayerStatusIcons} />
      </div>
      <p className="mb-2 flex items-center gap-1.5 text-[11px] text-slate-400">
        <Sparkles className="h-3 w-3 shrink-0 text-slate-500" aria-hidden />
        Sugestie: {resolveRoleLabel(layer.autoRole)}
      </p>
      <LayerRoleSelect
        layer={layer}
        layerKey={layerKey}
        selectedRole={selectedRole}
        onUpdateLayerRole={onUpdateLayerRole}
        workspaceTemplateCode={workspaceTemplateCode}
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
  workspaceTemplateCode,
  bindables,
  componentBindings,
  trailingCards = null,
}: {
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
  compact?: boolean;
  layout?: "table" | "cards" | "legend";
  hoveredLayerKey?: string | null;
  onHoverLayerKey?: (layerKey: string | null) => void;
  workspaceTemplateCode?: string | null;
  /** Product System svg_bindable_components — shown on the same card as geometry role. */
  bindables?: SvgBindableComponent[];
  componentBindings?: SvgComponentBinding[];
  /** Extra cards in the same grid (e.g. Contur suport). */
  trailingCards?: ReactNode;
}) {
  const [pageIndex, setPageIndex] = useState(0);
  const [internalHoveredLayerKey, setInternalHoveredLayerKey] = useState<string | null>(null);
  const focusedLayerKey = hoveredLayerKey ?? internalHoveredLayerKey;
  const setFocusedLayerKey = onHoverLayerKey ?? setInternalHoveredLayerKey;
  const shouldPaginate = report.layers.length > Math.max(INTAKE_V6_CARD_PAGE_SIZE, INTAKE_V6_NO_PAGINATION_MAX_LAYERS);
  const pageCount = shouldPaginate ? Math.max(1, Math.ceil(report.layers.length / INTAKE_V6_CARD_PAGE_SIZE)) : 1;
  const allLayersConfirmed = confirmation.confirmationStatus === "complete";
  const hideLayerStatusIcons = allLayersConfirmed;
  const ownerRoleTaxonomyActive = useMemo(() => {
    const targetCodes = new Set(
      report.layers.map((layer) => resolveIntakeV6LayerTargetTemplate({
        layer,
        selectedRole: resolveLayerRow(report, confirmation, layer).selectedRole,
        workspaceTemplateCode,
      }).templateCode),
    );
    return targetCodes.has(INTAKE_V6_LETTERS_TEMPLATE_CODE) && targetCodes.has(INTAKE_V6_LOGO_TEMPLATE_CODE);
  }, [confirmation, report, workspaceTemplateCode]);
  const paginatedLayers = useMemo(() => {
    if (!shouldPaginate) return report.layers;
    const start = pageIndex * INTAKE_V6_CARD_PAGE_SIZE;
    return report.layers.slice(start, start + INTAKE_V6_CARD_PAGE_SIZE);
  }, [pageIndex, report.layers, shouldPaginate]);

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
        {report.layers.map((layer, index) => {
          const { layerKey } = resolveLayerRow(report, confirmation, layer);
          return (
            <LayerLegendRow
              key={layer.id}
              layer={layer}
              report={report}
              confirmation={confirmation}
              onUpdateLayerRole={onUpdateLayerRole}
              workspaceTemplateCode={workspaceTemplateCode}
              layerIndex={index}
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
              Rol geometric + componentă Product System pe același card. Hover evidențiază geometria.
            </p>
          </div>
          <span className={`${v6.mono} ${v6.metricLabel}`}>
            {report.layers.length} straturi
          </span>
        </div>
        {shouldPaginate ? (
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
            {paginatedLayers.map((layer, index) => {
            const row = resolveLayerRow(report, confirmation, layer);
            const { layerKey, selectedRole } = row;
              const display = buildIntakeV6LayerDisplayLabel(layer, pageIndex * INTAKE_V6_CARD_PAGE_SIZE + index, report);
              const primaryLabel = display.primaryLabel.replace(/\s*\/\s*artwork$/i, "");
            return (
                <article
                  key={layer.id}
                  className={`rounded-md border px-3 py-3 transition outline-none focus-visible:ring-1 focus-visible:ring-cyan-400/50 ${
                    focusedLayerKey === layerKey
                      ? "border-cyan-400/40 bg-cyan-400/5"
                      : row.requiresAttention
                        ? "border-amber-500/30 bg-amber-500/5"
                        : "border-wo-border-strong/80 bg-wo-surface-inset/40"
                  }`}
                  data-testid={`intake-v6-layer-row-${layerKey}`}
                  tabIndex={0}
                  onMouseEnter={() => setFocusedLayerKey(layerKey)}
                  onMouseLeave={() => setFocusedLayerKey(null)}
                  onFocus={() => setFocusedLayerKey(layerKey)}
                  onBlur={() => setFocusedLayerKey(null)}
                >
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-[12px] font-semibold text-wo-text-primary">{primaryLabel}</p>
                      <p className="text-[11px] text-slate-500">{display.secondaryLabel}</p>
                      <p
                        className={`text-[10px] ${
                          row.entry?.confirmationState === "confirmed"
                            ? "text-emerald-300/90"
                            : "text-amber-200/90"
                        }`}
                        data-testid={`intake-v6-layer-confirm-state-${layerKey}`}
                      >
                        {confirmationStateLabelRo(row.entry?.confirmationState)}
                      </p>
                    </div>
                    <LayerStatusBadge
                      state={row.entry?.confirmationState}
                      layerKey={layerKey}
                      hidden={hideLayerStatusIcons}
                    />
                  </div>
                  <LayerRoleSelect
                    layer={layer}
                    layerKey={layerKey}
                    selectedRole={selectedRole}
                    onUpdateLayerRole={onUpdateLayerRole}
                    workspaceTemplateCode={workspaceTemplateCode}
                  />
                  <LayerComponentBindingSummary
                    layerKey={layerKey}
                    selectedRole={selectedRole}
                    bindables={bindables}
                    bindings={componentBindings}
                  />
                </article>
            );
          })}
          {trailingCards}
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
          {report.layers.map((layer, index) => {
            const { entry, layerKey, selectedRole, requiresAttention } = resolveLayerRow(
              report,
              confirmation,
              layer,
            );
            const display = buildIntakeV6LayerDisplayLabel(layer, index, report);
            return (
              <tr
                key={layer.id}
                className={`border-t border-wo-border-strong ${requiresAttention ? "bg-amber-500/5" : ""}`}
                data-testid={`intake-v6-layer-row-${layerKey}`}
              >
                <td className="py-2 pr-3 font-medium text-slate-200">
                  <span>{display.primaryLabel}</span>
                  <span className="mt-0.5 block text-[10px] font-normal text-slate-500">
                    {confirmationStateLabelRo(entry?.confirmationState)}
                  </span>
                </td>
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
                    layer={layer}
                    layerKey={layerKey}
                    selectedRole={selectedRole}
                    onUpdateLayerRole={onUpdateLayerRole}
                    workspaceTemplateCode={workspaceTemplateCode}
                  />
                </td>
                <td className="py-2">
                  <LayerStatusBadge state={entry?.confirmationState} layerKey={layerKey} hidden={hideLayerStatusIcons} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
