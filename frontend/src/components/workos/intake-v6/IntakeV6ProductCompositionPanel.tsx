import { CheckCircle2, ChevronDown, Layers3, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { v6 } from "./atoms/intakeV6Presentation";
import type { ProductDefinitionLinkedRuntimeSegmentsSummary } from "@/api/productDefinitionPreview";
import { buildOperatorLogoLabelMap, getOperatorLayerLabel } from "@/lib/intakeV6/intakeV4OperatorUiDisplay";

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
  return role || "Componenta";
}

function compositionLabel(type: string | undefined): string {
  if (type === "letters_plus_logo") return "Litere volumetrice + logo volumetric";
  if (type === "letters_plus_logo_plus_support") {
    return "Litere volumetrice + logo volumetric + Panou Alucobond casetat";
  }
  if (type === "letters_plus_support") return "Litere volumetrice + Panou Alucobond casetat";
  if (type === "logo_only") return "Logo volumetric";
  if (type === "letters_only") return "Litere volumetrice";
  return "Compozitie produs";
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
  const [open, setOpen] = useState(() => !confirmed || hasIssues);

  return (
    <section
      className={`${v6.cardCompact} ${confirmed ? "border-emerald-500/30 bg-emerald-500/5" : "border-cyan-500/30 bg-cyan-500/5"}`}
      data-testid="intake-v6-product-composition-panel"
    >
      <button
        type="button"
        className="flex w-full items-start justify-between gap-3 text-left"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        data-testid="intake-v6-product-composition-toggle"
      >
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-[12px] font-semibold text-slate-100">
            <Layers3 className="h-3.5 w-3.5 text-cyan-300" aria-hidden />
            Compozitie produs propusa
          </p>
          <p className="mt-1 text-[11px] text-slate-400" data-testid="intake-v6-product-composition-summary">
            {compositionLabel(recommendation.composition_type)}
          </p>
          {linkedSegmentItems.length > 0 ? (
            <p className="mt-1 text-[10px] text-slate-500" data-testid="intake-v6-product-composition-linked-count">
              {linkedSegmentItems.length} segmente linked
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${confirmed ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" : "border-amber-500/30 bg-amber-500/10 text-amber-200"}`}>
            {confirmed ? "Confirmata" : "Necesita confirmare"}
          </span>
          <ChevronDown className={`h-4 w-4 text-slate-400 transition ${open ? "rotate-180" : ""}`} aria-hidden />
        </div>
      </button>

      {open ? (
      <div data-testid="intake-v6-product-composition-details">
      <div className={`mt-3 grid gap-2 ${compact ? "" : "sm:grid-cols-2"}`}>
        {items.map((item) => (
          <div key={item.composition_item_id ?? item.template_code} className="rounded border border-[#2A3548]/80 bg-[#0A0F1A]/60 p-2.5">
            <p className="text-[11px] font-semibold text-slate-100">
              {roleLabel(item.component_role, item.template_code)}
            </p>
            <details className="mt-0.5">
              <summary className="cursor-pointer text-[10px] text-slate-500">Detalii tehnice</summary>
              <p className="mt-0.5 font-mono text-[10px] text-slate-500">{item.template_code}</p>
            </details>
            {item.source_layer_ids?.length ? (
              <p className="mt-1 text-[10px] text-slate-500">
                Straturi: {item.source_layer_ids.map((layerId) => sourceLayerLabels.get(layerId) ?? layerId).join(", ")}
              </p>
            ) : null}
            {item.status === "pending_template" ? (
              <p className="mt-1 text-[10px] text-amber-300">Template suport pending</p>
            ) : null}
          </div>
        ))}
      </div>

      {linkedSegmentItems.length > 0 ? (
        <div
          className="mt-3 rounded border border-cyan-500/25 bg-[#0A0F1A]/55 p-3"
          data-testid="intake-v6-product-definition-linked-segments"
        >
          <p className="text-[11px] font-semibold text-cyan-200">Segmente legate Product Definition</p>
          {linkedSegments?.root_template_code ? (
            <p className="mt-1 text-[10px] text-slate-400">
              Root Product Definition: <span className="font-mono text-slate-200">{linkedSegments.root_template_code}</span>
            </p>
          ) : null}
          <div className="mt-2 space-y-2">
            {linkedSegmentItems.map((segment) => (
              <div
                key={segment.segment_key}
                className="rounded border border-[#2A3548]/80 bg-[#111827]/55 p-2.5"
                data-testid={`intake-v6-product-definition-linked-segment-${segment.segment_key}`}
              >
                <p className="text-[11px] font-semibold text-slate-100">Segment linked detectat din Product Definition</p>
                <p className="mt-0.5 font-mono text-[10px] text-cyan-200">{segment.owning_template_code}</p>
                <p className="mt-1 text-[10px] text-amber-200">Candidat compozitie, nu produs ofertabil separat</p>
                <p className="mt-0.5 text-[10px] text-slate-400">
                  Role: {segment.composition_role} · status binding: {segment.binding_status}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-500">Nu activeaza pricing, quote, order sau execution separat</p>
                <p className="mt-0.5 text-[10px] text-slate-500">
                  pricing={segment.product_truth_readiness?.ready_for_pricing === true ? "DA" : "NU"} · quote={segment.product_truth_readiness?.ready_for_quote === true ? "DA" : "NU"} · order={segment.product_truth_readiness?.ready_for_order === true ? "DA" : "NU"} · execution={segment.product_truth_readiness?.ready_for_execution === true ? "DA" : "NU"}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {warnings.length || blockers.length ? (
        <div className="mt-3 space-y-1 text-[11px] text-amber-100">
          {[...blockers, ...warnings].map((item, index) => (
            <p key={index} className="flex gap-1.5">
              <TriangleAlert className="mt-0.5 h-3 w-3 shrink-0 text-amber-300" aria-hidden />
              <span>{String(item.message ?? item.code ?? "Verificare compozitie necesara")}</span>
            </p>
          ))}
        </div>
      ) : null}

      {canConfirm && onConfirm ? (
        <button
          type="button"
          className={`${v6.btnPrimary} mt-3 inline-flex items-center gap-1.5 text-[11px]`}
          data-testid="intake-v6-confirm-product-composition"
          onClick={() => onConfirm(items as Array<Record<string, unknown>>)}
        >
          <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
          Confirma compozitia produsului
        </button>
      ) : null}
      </div>
      ) : null}
    </section>
  );
}