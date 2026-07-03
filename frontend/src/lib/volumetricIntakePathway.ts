/**
 * TPL-VOLUMETRIC-LETTERS — operator input pathway (UI progressive disclosure).
 * Persists on product_spec_json as intake_input_pathway; does not change CostEngine.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { isFaceVinylEnabled, shouldShowPaintSection } from "@/lib/volumetricFrontlitIntake";
import type { VolumetricCalculationMethod } from "@/lib/volumetricQuoteFlowState";

/** Canonical persisted values for product_spec_json.intake_input_pathway */
export const INTAKE_INPUT_PATHWAY_VECTOR = "vector" as const;
export const INTAKE_INPUT_PATHWAY_MANUAL = "manual" as const;
export const INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE = "quick_estimate" as const;

export const INTAKE_INPUT_PATHWAYS = [
  INTAKE_INPUT_PATHWAY_VECTOR,
  INTAKE_INPUT_PATHWAY_MANUAL,
  INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE,
] as const;

export type VolumetricIntakePathway =
  | typeof INTAKE_INPUT_PATHWAY_VECTOR
  | typeof INTAKE_INPUT_PATHWAY_MANUAL
  | typeof INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE;

export function isIntakeInputPathway(
  value: string | null | undefined
): value is VolumetricIntakePathway {
  return (
    value === INTAKE_INPUT_PATHWAY_VECTOR ||
    value === INTAKE_INPUT_PATHWAY_MANUAL ||
    value === INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE
  );
}

/** Keep vector pathway when attaching vector metadata unless quick estimate is active. */
export function preservePathwayForVectorMetadata(
  spec: IntakeProductSpec
): IntakeProductSpec {
  if (spec.intake_input_pathway === INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE) {
    return spec;
  }
  return { ...spec, intake_input_pathway: INTAKE_INPUT_PATHWAY_VECTOR };
}

export type IntakeSpecSectionId = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;

export const PATHWAY_OPTIONS: {
  id: VolumetricIntakePathway;
  title: string;
  subtitle: string;
}[] = [
  {
    id: "vector",
    title: "Din fișier vector",
    subtitle: "SVG / DXF — fișier, layere, întrebări rapide și review în același loc",
  },
  {
    id: "manual",
    title: "Specificații manuale",
    subtitle: "Dimensiuni, geometrie litere, construcție și finisaj",
  },
  {
    id: "quick_estimate",
    title: "Estimare rapidă",
    subtitle: "Text + envelope minim — nu este ofertă comercială finală",
  },
];

export function hasStructuredVolumetricEnvelope(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  const width = spec.width_mm;
  const height = spec.height_mm ?? spec.letter_height_mm;
  const depth = spec.depth_mm ?? spec.return_depth_mm;
  return (
    width != null &&
    width > 0 &&
    height != null &&
    height > 0 &&
    depth != null &&
    depth > 0
  );
}

export function hasCostGeometryMetrics(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  return (
    spec.letter_face_area_m2 != null &&
    spec.letter_face_area_m2 > 0 &&
    spec.letter_perimeter_m != null &&
    spec.letter_perimeter_m > 0 &&
    spec.letter_count != null &&
    spec.letter_count >= 1
  );
}

function hasVectorPathwayHints(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  return (
    Boolean(spec.vector_file_name?.trim()) ||
    spec.vector_file_present === true ||
    Boolean(spec.svg_layer_mappings && Object.keys(spec.svg_layer_mappings).length > 0) ||
    spec.vector_svg_analyzed === true
  );
}

/** Infer pathway from saved spec when intake_input_pathway missing (legacy rows). */
export function derivePathwayFromSpec(
  spec: IntakeProductSpec | null | undefined
): VolumetricIntakePathway {
  const stored = spec?.intake_input_pathway;
  if (stored === INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE) {
    return INTAKE_INPUT_PATHWAY_QUICK_ESTIMATE;
  }
  if (stored === INTAKE_INPUT_PATHWAY_VECTOR) {
    return INTAKE_INPUT_PATHWAY_VECTOR;
  }
  // Vector file metadata wins over stale manual default when operator used vector flow.
  if (hasVectorPathwayHints(spec)) {
    return INTAKE_INPUT_PATHWAY_VECTOR;
  }
  if (stored === INTAKE_INPUT_PATHWAY_MANUAL) {
    return INTAKE_INPUT_PATHWAY_MANUAL;
  }
  if (hasCostGeometryMetrics(spec)) {
    return INTAKE_INPUT_PATHWAY_MANUAL;
  }
  return INTAKE_INPUT_PATHWAY_MANUAL;
}

export function pathwayToCalculationMethod(
  pathway: VolumetricIntakePathway
): VolumetricCalculationMethod {
  switch (pathway) {
    case "vector":
      return "vector_first";
    case "quick_estimate":
      return "quick_estimate";
    default:
      return "manual_geometry";
  }
}

export function needsManualGeometryFallback(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return true;
  return !hasCostGeometryMetrics(spec);
}

/** Whether a numbered intake form section should render for this pathway. */
export function isIntakeSectionVisible(
  pathway: VolumetricIntakePathway,
  section: IntakeSpecSectionId,
  spec?: IntakeProductSpec | null
): boolean {
  switch (pathway) {
    case "quick_estimate":
      return section === 1 || section === 2;
    case "vector":
      if (section === 9) return false;
      if (section === 1 || section === 2) return true;
      if (section === 3) return needsManualGeometryFallback(spec);
      if (section === 5) return isFaceVinylEnabled(spec);
      if (section === 6) return shouldShowPaintSection();
      return section >= 4 && section <= 8;
    case "manual":
    default:
      if (section === 9) return false;
      if (section === 5) return isFaceVinylEnabled(spec);
      if (section === 6) return shouldShowPaintSection();
      return section >= 1 && section <= 8;
  }
}

/** Default accordion open state per pathway. */
export function defaultSectionOpen(
  pathway: VolumetricIntakePathway,
  section: IntakeSpecSectionId
): boolean {
  if (pathway === "quick_estimate") return section <= 2;
  if (pathway === "vector") {
    if (section === 1) return true;
    return false;
  }
  return section === 1;
}

export function pathwayHint(pathway: VolumetricIntakePathway): string {
  switch (pathway) {
    case "vector":
      return "Completează fișierul vector și layerele de mai sus. Geometria manuală apare doar dacă analiza nu extrage metrici validate.";
    case "quick_estimate":
      return "Doar câmpuri minime pentru o simulare orientativă. Pentru ofertă finală, folosește manual sau vector.";
    default:
      return "Introdu dimensiuni și geometrie explicit. Fișierul vector este opțional.";
  }
}
