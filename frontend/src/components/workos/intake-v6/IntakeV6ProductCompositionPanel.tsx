import { CheckCircle2, ChevronDown, Layers3, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { v6 } from "./atoms/intakeV6Presentation";
import type { ProductDefinitionLinkedRuntimeSegmentsSummary } from "@/api/productDefinitionPreview";
import { buildOperatorLogoLabelMap, getOperatorLayerLabel } from "@/lib/intakeV6/intakeV4OperatorUiDisplay";
import { isPseudoFillToken } from "@/lib/intakeV6/intakeV6LayerDisplayLabel";
import {
  operatorBindingStatusLabelRo,
  operatorCompositionRoleLabelRo,
  operatorStatusSemanticRo,
} from "@/lib/intakeV6/intakeV6OperatorVocabulary";
import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";

type CompositionItem = {
  composition_item_id?: string;
  template_code?: string;
  component_role?: string;
  source_layer_ids?: string[];
  status?: string;
};

type CompositionRecommendation = {
  status?: string;
  composition_type?: string;
  composition_items?: CompositionItem[];
  recommended_templates?: Array<Record<string, unknown>>;
  warnings?: Array<Record<string, unknown>>;
  blockers?: Array<Record<string, unknown>>;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

const ACM_SUPPORT_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

/** Project live ACP binding into composition UI when server recommendation lags. */
function supportItemFromFinishSetup(
  payload: Record<string, unknown> | null | undefined,
): CompositionItem | null {
  const finish = asRecord(payload?.finish_setup);
  if (!finish) return null;
  const bindings = Array.isArray(finish.svg_component_bindings) ? finish.svg_component_bindings : [];
  for (const raw of bindings) {
    const binding = asRecord(raw);
    if (!binding) continue;
    if (String(binding.component_template_code ?? "") !== ACM_SUPPORT_TEMPLATE) continue;
    const status = String(binding.status ?? "").toUpperCase();
    if (!["CONFIRMED", "DRAFT", "RECONFIRM_REQUIRED"].includes(status)) continue;
    const geom = asRecord(binding.selected_geometry);
    const elementIds = Array.isArray(geom?.element_ids)
      ? geom.element_ids.map((id) => String(id)).filter(Boolean)
      : [];
    return {
      composition_item_id: "support",
      template_code: ACM_SUPPORT_TEMPLATE,
      component_role: "support_panel",
      source_layer_ids: elementIds.length ? elementIds : ["svg_support_contour"],
      status: "available_optional",
    };
  }
  const selection = asRecord(finish.svg_support_selection);
  if (
    selection &&
    ["confirmed", "draft", "reconfirm_required"].includes(String(selection.status ?? "").toLowerCase()) &&
    String(selection.role ?? "") === "ALUCOBOND_CASED_PANEL"
  ) {
    const contourId = String(selection.contour_id ?? selection.svg_support_element_id ?? "").trim();
    return {
      composition_item_id: "support",
      template_code: ACM_SUPPORT_TEMPLATE,
      component_role: "support_panel",
      source_layer_ids: contourId ? [contourId] : ["svg_support_contour"],
      status: "available_optional",
    };
  }
  return null;
}

function readRecommendation(payload: Record<string, unknown> | null | undefined): CompositionRecommendation | null {
  const raw = asRecord(payload?.product_composition_recommendation);
  if (!raw) return null;
  const items = Array.isArray(raw.composition_items)
    ? (raw.composition_items.map((item) => asRecord(item) ?? {}) as CompositionItem[])
    : [];
  const supportFromBinding = supportItemFromFinishSetup(payload);
  const hasSupport = items.some(
    (item) =>
      item.component_role === "support_panel" ||
      item.template_code === ACM_SUPPORT_TEMPLATE,
  );
  const mergedItems =
    supportFromBinding && !hasSupport ? [...items, supportFromBinding] : items;
  let compositionType =
    typeof raw.composition_type === "string" ? raw.composition_type : undefined;
  if (supportFromBinding && !hasSupport) {
    const hasLetters = mergedItems.some((item) => item.component_role === "volumetric_letters");
    const hasLogo = mergedItems.some((item) => item.component_role === "volumetric_logo");
    if (hasLetters && hasLogo) compositionType = "letters_plus_logo_plus_support";
    else if (hasLetters) compositionType = "letters_plus_support";
  }
  return {
    status: typeof raw.status === "string" ? raw.status : undefined,
    composition_type: compositionType,
    composition_items: mergedItems,
    recommended_templates: Array.isArray(raw.recommended_templates)
      ? (raw.recommended_templates.filter(Boolean) as Array<Record<string, unknown>>)
      : [],
    warnings: Array.isArray(raw.warnings)
      ? (raw.warnings.filter(Boolean) as Array<Record<string, unknown>>)
      : [],
    blockers: Array.isArray(raw.blockers)
      ? (raw.blockers.filter(Boolean) as Array<Record<string, unknown>>)
      : [],
  };
}

function isConfirmed(payload: Record<string, unknown> | null | undefined): boolean {
  const raw = asRecord(payload?.product_composition_confirmed);
  return raw?.confirmed === true;
}

function roleLabel(role: string | undefined, templateCode?: string): string {
  if (role === "volumetric_letters") return "Litere volumetrice";
  if (role === "volumetric_logo") return "Logo volumetric";
  if (role === "support_panel") {
    if (templateCode === "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1") {
      return "Panou Alucobond casetat";
    }
    return "Fundal / suport";
  }
  return role || "Componentă";
}

function compositionLabel(type: string | undefined): string {
  if (type === "letters_plus_logo") return "Litere volumetrice + logo volumetric";
  if (type === "letters_plus_logo_plus_support") {
    return "Litere volumetrice + logo volumetric + Panou Alucobond casetat";
  }
  if (type === "letters_plus_support") return "Litere volumetrice + Panou Alucobond casetat";
  if (type === "logo_only") return "Logo volumetric";
  if (type === "letters_only") return "Litere volumetrice";
  return "Compoziție produs";
}

function formatSourceLayerIds(items: CompositionItem[]): Map<string, string> {
  const logoLabelMap = buildOperatorLogoLabelMap(
    items.flatMap((item) =>
      (item.source_layer_ids ?? []).map((layerId) => ({ id: layerId, name: layerId })),
    ),
  );
  const labels = new Map<string, string>();
  for (const item of items) {
    for (const layerId of item.source_layer_ids ?? []) {
      if (isPseudoFillToken(layerId)) {
        labels.set(layerId, "Formă grafică detectată");
        continue;
      }
      labels.set(layerId, getOperatorLayerLabel(layerId, layerId, { logoLabelMap }));
    }
  }
  return labels;
}

export default function IntakeV6ProductCompositionPanel({
  payload,
  linkedSegments,
  onConfirm,
  compact = false,
}: {
  payload: Record<string, unknown> | null | undefined;
  linkedSegments?: ProductDefinitionLinkedRuntimeSegmentsSummary | null;
  onConfirm?: (items: Array<Record<string, unknown>>) => void;
  compact?: boolean;
}) {
  const recommendation = readRecommendation(payload);
  if (!recommendation) return null;

  const confirmed = isConfirmed(payload);
  const items = recommendation.composition_items ?? [];
  const sourceLayerLabels = formatSourceLayerIds(items);
  const blockers = recommendation.blockers ?? [];
  const warnings = recommendation.warnings ?? [];
  const linkedSegmentItems = linkedSegments?.segments ?? [];
  const canConfirm = !confirmed && recommendation.status !== "blocked" && items.length > 0;
  const hasIssues = blockers.length > 0 || warnings.length > 0;
  // Blockers force expand; technical warnings stay behind disclosure by default.
  const [open, setOpen] = useState(() => !confirmed || blockers.length > 0);

  const componentSummary = items.map((item) => roleLabel(item.component_role, item.template_code)).join(" · ");
  const statusLabel = confirmed
    ? operatorStatusSemanticRo("confirmed")
    : recommendation.status === "blocked" || blockers.length > 0
      ? operatorStatusSemanticRo("blocker")
      : operatorStatusSemanticRo("needs_operator");

  return (
    <section
      className={`rounded-md border px-3 py-2.5 sm:px-3.5 ${
        confirmed
          ? "border-[#2A3548]/70 bg-[#111827]/50"
          : blockers.length > 0
            ? "border-rose-500/35 bg-rose-950/20"
            : "border-[#2A3548]/90 bg-[#111827]/70"
      }`}
      data-testid="intake-v6-product-composition-panel"
    >
      <button
        type="button"
        className="flex w-full items-start justify-between gap-3 text-left"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label={`Compoziție produs — ${open ? "expandat" : "restrâns"}`}
        data-testid="intake-v6-product-composition-toggle"
      >
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-[13px] font-semibold text-slate-100">
            <Layers3 className="h-3.5 w-3.5 text-slate-400" aria-hidden />
            Produs
          </p>
          <p className="mt-1 text-[12px] text-slate-300" data-testid="intake-v6-product-composition-summary">
            {compositionLabel(recommendation.composition_type)}
          </p>
          {componentSummary ? (
            <p className="mt-0.5 text-[11px] text-slate-500" data-testid="intake-v6-product-composition-components">
              {componentSummary}
            </p>
          ) : null}
          {linkedSegmentItems.length > 0 ? (
            <p className="mt-1 text-[10px] text-slate-600" data-testid="intake-v6-product-composition-linked-count">
              {linkedSegmentItems.length}{" "}
              {linkedSegmentItems.length === 1 ? "segment legat" : "segmente legate"}
            </p>
          ) : null}
          {blockers.length > 0 && !open ? (
            <p className="mt-1 text-[11px] text-rose-200/90">
              {blockers.length} blocant{blockers.length === 1 ? "" : "e"} — expandă pentru detalii
            </p>
          ) : null}
          {warnings.length > 0 && blockers.length === 0 && !open ? (
            <p className="mt-1 text-[11px] text-slate-500">
              Context tehnic disponibil în detalii
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span
            className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${
              confirmed
                ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                : blockers.length > 0
                  ? "border-rose-500/30 bg-rose-500/10 text-rose-200"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-200"
            }`}
          >
            {statusLabel}
          </span>
          <ChevronDown className={`h-4 w-4 text-slate-500 transition ${open ? "rotate-180" : ""}`} aria-hidden />
        </div>
      </button>

      {/* Required confirmation stays on L1 — never only inside technical disclosure. */}
      {canConfirm && onConfirm ? (
        <button
          type="button"
          className={`${v6.btnPrimary} mt-2.5 inline-flex items-center gap-1.5 text-[11px]`}
          data-testid="intake-v6-confirm-product-composition"
          onClick={() => onConfirm(items as Array<Record<string, unknown>>)}
        >
          <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
          Confirmă compoziția produsului
        </button>
      ) : null}

      {open ? (
      <div data-testid="intake-v6-product-composition-details">
      <div className={`mt-3 grid gap-2 ${compact ? "" : "sm:grid-cols-2"}`}>
        {items.map((item) => (
          <div
            key={item.composition_item_id ?? item.template_code}
            className="rounded border border-[#2A3548]/50 bg-[#0A0F1A]/40 px-2.5 py-2"
          >
            <p className="text-[12px] font-medium text-slate-200">
              {roleLabel(item.component_role, item.template_code)}
            </p>
            {item.status === "pending_template" ? (
              <p className="mt-1 text-[10px] text-amber-300">Template suport în așteptare</p>
            ) : (
              <p className="mt-0.5 text-[10px] text-slate-600">Inclus în propunere</p>
            )}
            <details className="mt-1">
              <summary className="cursor-pointer text-[10px] text-slate-600">Detalii tehnice</summary>
              <p className="mt-0.5 font-mono text-[10px] text-slate-500">{item.template_code}</p>
              {item.source_layer_ids?.length ? (
                <p className="mt-0.5 text-[10px] text-slate-500">
                  Straturi:{" "}
                  {item.source_layer_ids.map((layerId) => sourceLayerLabels.get(layerId) ?? layerId).join(", ")}
                </p>
              ) : null}
            </details>
          </div>
        ))}
      </div>

      {blockers.length > 0 ? (
        <div className="mt-3 space-y-1 text-[11px] text-rose-100" data-testid="intake-v6-product-composition-blockers">
          {blockers.map((item, index) => (
            <p key={index} className="flex gap-1.5">
              <TriangleAlert className="mt-0.5 h-3 w-3 shrink-0 text-rose-300" aria-hidden />
              <span>{String(item.message ?? item.code ?? "Verificare compoziție necesară")}</span>
            </p>
          ))}
        </div>
      ) : null}

      {(warnings.length > 0 || linkedSegmentItems.length > 0) ? (
        <IntakeV6TechnicalDetailsAccordion
          title="Detalii tehnice compoziție"
          hint="Avertismente registry, segmente legate, readiness"
          defaultOpen={false}
          testId="intake-v6-product-composition-technical"
          className="mt-3"
        >
          {warnings.length > 0 ? (
            <div className="mb-2 space-y-1 text-[11px] text-amber-100/90" data-testid="intake-v6-product-composition-issues">
              {warnings.map((item, index) => (
                <p key={index} className="flex gap-1.5">
                  <TriangleAlert className="mt-0.5 h-3 w-3 shrink-0 text-amber-300" aria-hidden />
                  <span>{String(item.message ?? item.code ?? "Verificare compoziție necesară")}</span>
                </p>
              ))}
            </div>
          ) : null}
          {linkedSegmentItems.length > 0 ? (
            <div data-testid="intake-v6-product-definition-linked-segments">
              {linkedSegments?.root_template_code ? (
                <p className="text-[10px] text-slate-400">
                  Root: <span className="font-mono text-slate-200">{linkedSegments.root_template_code}</span>
                </p>
              ) : null}
              <p className="mt-1 text-[10px] text-amber-200">
                Candidat compoziție, nu produs ofertabil separat
              </p>
              <p className="mt-0.5 text-[10px] text-slate-500">
                Nu activează pricing, quote, order sau execution separat
              </p>
              <div className="mt-2 space-y-2">
                {linkedSegmentItems.map((segment) => (
                  <div
                    key={segment.segment_key}
                    className="rounded border border-[#2A3548]/80 bg-[#111827]/55 p-2.5"
                    data-testid={`intake-v6-product-definition-linked-segment-${segment.segment_key}`}
                  >
                    <p className="text-[11px] font-semibold text-slate-100">
                      {operatorCompositionRoleLabelRo(segment.composition_role)}
                    </p>
                    <p className="mt-0.5 font-mono text-[10px] text-cyan-200">{segment.owning_template_code}</p>
                    <p className="mt-0.5 text-[10px] text-slate-400">
                      Status asociere: {operatorBindingStatusLabelRo(segment.binding_status)}
                    </p>
                    <p className="mt-0.5 font-mono text-[10px] text-slate-500">
                      pricing={segment.product_truth_readiness?.ready_for_pricing === true ? "DA" : "NU"} ·
                      quote={segment.product_truth_readiness?.ready_for_quote === true ? "DA" : "NU"} ·
                      order={segment.product_truth_readiness?.ready_for_order === true ? "DA" : "NU"} ·
                      execution={segment.product_truth_readiness?.ready_for_execution === true ? "DA" : "NU"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </IntakeV6TechnicalDetailsAccordion>
      ) : null}
      </div>
      ) : null}
    </section>
  );
}
