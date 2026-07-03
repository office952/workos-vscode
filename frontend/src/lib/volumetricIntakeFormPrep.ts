/**
 * TPL-VOLUMETRIC-LETTERS — intake form quote-prep summary (UI only, no policy changes).
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import {
  computeLedModuleCountFromPerimeter,
  describeVolumetricIntakePrefill,
  effectiveReturnDepthMm,
  isCantRalPaintEnabled,
  type VolumetricIntakePrefillSummary,
} from "@/lib/volumetricQuoteInput";
import {
  collectFrontlitIntakeMissing,
  isFaceVinylEnabled,
} from "@/lib/volumetricFrontlitIntake";
import { hasLettersLayerMapped } from "@/lib/vectorStudioPreview";
import {
  getEffectiveQuoteGeometrySpec,
  isVectorGeometryCurrentForQuote,
} from "@/lib/vectorGeometryInvalidation";

export type FieldTagKind =
  | "affects_cost"
  | "final_quote"
  | "production_only"
  | "optional"
  | "prefill_wizard";

export const FIELD_TAG_LABELS: Record<FieldTagKind, string> = {
  affects_cost: "Afectează calculul",
  final_quote: "Necesită pentru ofertă finală",
  production_only: "Doar producție",
  optional: "Opțional",
  prefill_wizard: "Preluat în QuoteWizard",
};

/** Human-readable geometry source — never invents values. */
export function deriveGeometrySourceLabel(spec: IntakeProductSpec): string {
  const hasArea = spec.letter_face_area_m2 != null && spec.letter_face_area_m2 > 0;
  const hasPerimeter = spec.letter_perimeter_m != null && spec.letter_perimeter_m > 0;
  const hasCount = spec.letter_count != null && spec.letter_count >= 1;
  const hasAny = hasArea || hasPerimeter || hasCount;

  if (!hasAny) {
    if (spec.vector_file_name && !isVectorGeometryCurrentForQuote(spec)) {
      return "Necompletat — fișier vector schimbat; reconfirmă layerul și geometria";
    }
    if (spec.vector_file_name) {
      return "Necompletat — fișier vector atașat, fără metrici validate";
    }
    return "Necompletat";
  }

  switch (spec.vector_metrics_source) {
    case "svg_analysis":
      return "Metrici din analiză vector (sau completate manual după review)";
    case "dxf_analysis":
      return "Metrici din DXF (review manual necesar)";
    case "dwg_manual":
      return "Introduse manual după review DWG";
    case "manual":
    default:
      return "Introduse manual";
  }
}

export interface VolumetricQuotePrepSummary {
  prefill: VolumetricIntakePrefillSummary;
  geometrySource: string;
  missingForSimulate: string[];
  missingForFinalQuote: string[];
  canContinueToQuoteWizard: boolean;
  ledModuleCountEstimate: number | null;
}

function pushIfMissing(
  list: string[],
  condition: boolean,
  message: string
): void {
  if (condition && !list.includes(message)) {
    list.push(message);
  }
}

/** Build operator-facing prep summary from current spec (read-only hints). */
export function buildVolumetricQuotePrepSummary(
  spec: IntakeProductSpec | null | undefined
): VolumetricQuotePrepSummary {
  const effective = getEffectiveQuoteGeometrySpec(spec);
  const s = effective ?? {};
  const prefill = describeVolumetricIntakePrefill(effective);

  const missingForSimulate: string[] = [];
  const missingForFinalQuote: string[] = [];

  pushIfMissing(
    missingForSimulate,
    s.letter_face_area_m2 == null || s.letter_face_area_m2 <= 0,
    "Aria față litere (m²)"
  );
  pushIfMissing(
    missingForSimulate,
    s.letter_perimeter_m == null || s.letter_perimeter_m <= 0,
    "Perimetru litere (ml)"
  );
  pushIfMissing(
    missingForSimulate,
    s.letter_count == null || s.letter_count < 1,
    "Număr litere / elemente"
  );
  pushIfMissing(
    missingForSimulate,
    effectiveReturnDepthMm(s) == null,
    "Adâncime cant / retur volumetric (30 / 60 / 80 / 100 mm)"
  );

  for (const item of collectFrontlitIntakeMissing(s, "simulate")) {
    pushIfMissing(missingForSimulate, true, item);
  }

  // Legacy geometry — still required for simulate
  // (frontlit missing collector handles PSU/lighting when geometry present)

  pushIfMissing(
    missingForFinalQuote,
    spec?.vector_file_name &&
      !isVectorGeometryCurrentForQuote(spec) &&
      s.intake_input_pathway === "vector",
    "Geometrie vector — reconfirmă layerul și metricile pentru fișierul curent"
  );

  pushIfMissing(
    missingForFinalQuote,
    !hasLettersLayerMapped(s.svg_layer_mappings) &&
      s.vector_layer_mapping_confirmed !== true &&
      s.intake_input_pathway === "vector",
    "Layer principal litere — confirmă maparea SVG"
  );

  pushIfMissing(
    missingForFinalQuote,
    !s.vector_file_name && !s.vector_file_present,
    "Fișier vector / producție"
  );
  pushIfMissing(
    missingForFinalQuote,
    !s.vector_manual_review_approved &&
      s.vector_analysis_status !== "analyzed" &&
      s.vector_analysis_status !== "manual_review_approved",
    "Review manual vector sau analiză validă"
  );

  const face = s.face_finish_type;
  if (isFaceVinylEnabled(s) && (face === "oracal_651" || face === "oracal_8500")) {
    pushIfMissing(
      missingForFinalQuote,
      !s.face_vinyl_color_code?.trim(),
      "Cod culoare folie Oracal"
    );
    pushIfMissing(
      missingForFinalQuote,
      s.face_vinyl_roll_width_mm !== 1000 && s.face_vinyl_roll_width_mm !== 1260,
      "Lățime rolă Oracal (1000 / 1260 mm)"
    );
  }

  if (
    isCantRalPaintEnabled(s) &&
    (s.paint_tube_count ?? 0) > 0 &&
    isFaceVinylEnabled(s) === false
  ) {
    pushIfMissing(
      missingForFinalQuote,
      !s.paint_ral_code?.trim() && !s.ral_color?.trim(),
      "Cod RAL vopsea"
    );
  }

  for (const item of collectFrontlitIntakeMissing(s, "final")) {
    pushIfMissing(missingForFinalQuote, true, item);
  }

  if (s.mounting_system === "acm_panel") {
    pushIfMissing(
      missingForFinalQuote,
      true,
      "Panou ACM casetat — necesită template separat pentru ofertă finală"
    );
  }

  for (const w of prefill.warnings) {
    if (w.includes("Oracal")) {
      pushIfMissing(missingForFinalQuote, true, w);
    }
    if (w.includes("RAL") && isCantRalPaintEnabled(s)) {
      pushIfMissing(missingForFinalQuote, true, w);
    }
  }

  const ledModuleCountEstimate =
    s.letter_perimeter_m != null && s.letter_perimeter_m > 0
      ? computeLedModuleCountFromPerimeter(s.letter_perimeter_m)
      : null;

  return {
    prefill,
    geometrySource: deriveGeometrySourceLabel(s),
    missingForSimulate,
    missingForFinalQuote,
    canContinueToQuoteWizard: true,
    ledModuleCountEstimate,
  };
}
