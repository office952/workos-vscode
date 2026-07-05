import { CheckCircle2, Layers3, TriangleAlert } from "lucide-react";
import { v6 } from "./atoms/intakeV6Presentation";

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

function readRecommendation(payload: Record<string, unknown> | null | undefined): CompositionRecommendation | null {
  const raw = asRecord(payload?.product_composition_recommendation);
  if (!raw) return null;
  return {
    status: typeof raw.status === "string" ? raw.status : undefined,
    composition_type: typeof raw.composition_type === "string" ? raw.composition_type : undefined,
    composition_items: Array.isArray(raw.composition_items) ? raw.composition_items.map((item) => asRecord(item) ?? {}) as CompositionItem[] : [],
    recommended_templates: Array.isArray(raw.recommended_templates) ? raw.recommended_templates.filter(Boolean) as Array<Record<string, unknown>> : [],
    warnings: Array.isArray(raw.warnings) ? raw.warnings.filter(Boolean) as Array<Record<string, unknown>> : [],
    blockers: Array.isArray(raw.blockers) ? raw.blockers.filter(Boolean) as Array<Record<string, unknown>> : [],
  };
}

function isConfirmed(payload: Record<string, unknown> | null | undefined): boolean {
  const raw = asRecord(payload?.product_composition_confirmed);
  return raw?.confirmed === true;
}

function roleLabel(role: string | undefined): string {
  if (role === "volumetric_letters") return "Litere volumetrice";
  if (role === "volumetric_logo") return "Logo volumetric";
  if (role === "support_panel") return "Fundal / suport";
  return role || "Componenta";
}

function compositionLabel(type: string | undefined): string {
  if (type === "letters_plus_logo") return "Litere volumetrice + logo volumetric";
  if (type === "letters_plus_logo_plus_support") return "Litere volumetrice + logo volumetric + suport";
  if (type === "logo_only") return "Logo volumetric";
  if (type === "letters_only") return "Litere volumetrice";
  return "Compozitie produs";
}

export default function IntakeV6ProductCompositionPanel({
  payload,
  onConfirm,
  compact = false,
}: {
  payload: Record<string, unknown> | null | undefined;
  onConfirm?: (items: Array<Record<string, unknown>>) => void;
  compact?: boolean;
}) {
  const recommendation = readRecommendation(payload);
  if (!recommendation) return null;

  const confirmed = isConfirmed(payload);
  const items = recommendation.composition_items ?? [];
  const blockers = recommendation.blockers ?? [];
  const warnings = recommendation.warnings ?? [];
  const canConfirm = !confirmed && recommendation.status !== "blocked" && items.length > 0;

  return (
    <section
      className={`${v6.cardCompact} ${confirmed ? "border-emerald-500/30 bg-emerald-500/5" : "border-cyan-500/30 bg-cyan-500/5"}`}
      data-testid="intake-v6-product-composition-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-[12px] font-semibold text-slate-100">
            <Layers3 className="h-3.5 w-3.5 text-cyan-300" aria-hidden />
            Compozitie produs propusa
          </p>
          <p className="mt-1 text-[11px] text-slate-400">{compositionLabel(recommendation.composition_type)}</p>
        </div>
        <span className={`shrink-0 rounded border px-2 py-0.5 text-[10px] font-semibold ${confirmed ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" : "border-amber-500/30 bg-amber-500/10 text-amber-200"}`}>
          {confirmed ? "Confirmata" : "Necesita confirmare"}
        </span>
      </div>

      <div className={`mt-3 grid gap-2 ${compact ? "" : "sm:grid-cols-2"}`}>
        {items.map((item) => (
          <div key={item.composition_item_id ?? item.template_code} className="rounded border border-[#2A3548]/80 bg-[#0A0F1A]/60 p-2.5">
            <p className="text-[11px] font-semibold text-slate-100">{roleLabel(item.component_role)}</p>
            <p className="mt-0.5 font-mono text-[10px] text-cyan-200">{item.template_code}</p>
            {item.source_layer_ids?.length ? (
              <p className="mt-1 text-[10px] text-slate-500">Straturi: {item.source_layer_ids.join(", ")}</p>
            ) : null}
            {item.status === "pending_template" ? (
              <p className="mt-1 text-[10px] text-amber-300">Template suport pending</p>
            ) : null}
          </div>
        ))}
      </div>

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
    </section>
  );
}