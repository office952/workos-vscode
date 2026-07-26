import { useState } from "react";
import type {
  IntakeV6AiInformationalAssistPreviewResponse,
  IntakeV6AiInformationalSuggestionItem,
  IntakeV6AiSuggestionCategory,
} from "@/lib/intakeV6/intakeV6Api";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

const CATEGORY_LABEL: Record<IntakeV6AiSuggestionCategory, string> = {
  semantic_classification: "clasificare semantică",
  missing_information: "informații lipsă",
  template_recommendation: "template sugerat",
  client_intake_summary: "sumar cerere client",
  production_risk_hint: "risc producție",
  material_intent_hint: "intenție material",
  file_quality_hint: "calitate fișier",
  question_suggestion: "întrebare sugerată",
  operator_explanation: "explicație operator",
};

function formatSuggestionLine(item: IntakeV6AiInformationalSuggestionItem): string {
  const category = CATEGORY_LABEL[item.category] ?? item.category;
  const layer =
    typeof item.payload.source_layer === "string"
      ? item.payload.source_layer
      : item.title ?? item.suggestion_id;
  if (item.category === "semantic_classification") {
    const kind = item.payload.suggested_kind ?? "unknown";
    const confidence = Math.round(item.confidence * 100);
    return `${layer}: ${category} → ${kind} (${confidence}% mock)`;
  }
  return `${layer}: ${category} — ${item.summary ?? ""}`.trim();
}

export default function IntakeV6AiSemanticAssistPanel({
  preview,
  loading,
}: {
  preview: IntakeV6AiInformationalAssistPreviewResponse | null;
  loading: boolean;
}) {
  const [open, setOpen] = useState(false);

  if (loading) {
    return (
      <div className={`${v6.card} mb-4`} data-testid="intake-v6-ai-semantic-assist">
        <p className="text-[12px] text-slate-400">Pregătesc AI Informational Layer…</p>
      </div>
    );
  }

  if (!preview) {
    return null;
  }

  const semanticItems = preview.mock_suggestions.filter(
    (item) => item.category === "semantic_classification",
  );

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-ai-semantic-assist">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 text-left"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <div>
          <h3 className="text-[12px] font-bold uppercase tracking-wide">
            AI Informational Layer — sugestii viitoare
          </h3>
          <p className="mt-1 text-[10px] text-amber-200/90">
            AI suggestion only — not used for pricing or production until confirmed.
          </p>
        </div>
        <AtomsBadge tone="muted">{open ? "−" : "+"}</AtomsBadge>
      </button>

      {open ? (
        <div className="mt-3 space-y-3 border-t border-wo-border-strong/60 pt-3 text-[11px] text-slate-300">
          <p data-testid="intake-v6-ai-not-connected">
            {preview.ai_not_called ? "AI not connected yet." : "AI connected."}
          </p>
          <p data-testid="intake-v6-ai-candidate-ready">
            Candidate payload ready · context: {preview.context}
          </p>
          <p className="text-[10px] text-slate-500" data-testid="intake-v6-ai-informational-only">
            informational_only={String(preview.boundary_flags.informational_only)} · writes_business_state=
            {String(preview.informational_envelope.writes_business_state)}
          </p>

          <div>
            <h4 className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
              Suggested future classification (mock)
            </h4>
            <ul className="space-y-1" data-testid="intake-v6-ai-mock-suggestions">
              {semanticItems.map((item) => (
                <li key={item.suggestion_id}>• {formatSuggestionLine(item)}</li>
              ))}
            </ul>
          </div>

          {preview.informational_envelope.warnings.length > 0 ? (
            <ul className="space-y-1 text-[10px] text-slate-500" data-testid="intake-v6-ai-warnings">
              {preview.informational_envelope.warnings.map((warning) => (
                <li key={warning}>• {warning}</li>
              ))}
            </ul>
          ) : null}

          <p className="text-[10px] text-slate-500">
            Same contract will support website chatbot & order forms · grupuri candidate:{" "}
            {preview.candidate_payload.groups.length}
          </p>
        </div>
      ) : null}
    </div>
  );
}



