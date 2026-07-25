/**
 * Letters — available finishes for subtle Product System display.
 * Read-only labels from canonical finish enum map. No pricing, no activation.
 */
import { LETTERS_FACE_AUTOCOLANT_OPTIONS } from "@/lib/materials/lettersAutocolantDisplay";
import {
  CANONICAL_FINISH_ENUM_MAP,
  type CanonicalFinishEnumEntry,
} from "./canonicalFinishEnumMap";

export type LettersFinishAvailabilityChip = {
  id: string;
  labelRo: string;
  group: "face" | "cant";
};

function isDisplayable(entry: CanonicalFinishEnumEntry): boolean {
  if (!entry.productSystemLabelRo?.trim()) return false;
  if (entry.activationStatus === "deprecated_conceptual") return false;
  if (entry.activationStatus === "audit_only") return false;
  // Skip commercial policy row as a "finish option" chip.
  if (entry.technicalVariant === "commercial_minimum") return false;
  if (entry.technicalVariant === "none_or_material_default") return false;
  return true;
}

/** Short operator labels — face Autocolant options in owner order. */
export function listLettersFaceFinishChips(): LettersFinishAvailabilityChip[] {
  return LETTERS_FACE_AUTOCOLANT_OPTIONS.map((option) => ({
    id: option.id,
    labelRo: option.labelRo,
    group: "face" as const,
  }));
}

/** Cant finish modes owned by RETURN-CANT (stock / Oracal / RAL). */
export function listLettersCantFinishChips(): LettersFinishAvailabilityChip[] {
  return CANONICAL_FINISH_ENUM_MAP.filter(
    (entry) =>
      entry.ownerComponent === "RETURN-CANT" &&
      entry.surfaceTarget === "cant" &&
      isDisplayable(entry) &&
      (entry.technicalVariant === "stock_color" ||
        entry.technicalVariant === "vinyl_application" ||
        entry.technicalVariant === "paint_application"),
  ).map((entry) => ({
    id: entry.canonicalId,
    labelRo: entry.productSystemLabelRo!.trim(),
    group: "cant" as const,
  }));
}

export function isLettersFinisajStructureComponent(component: {
  type: string;
  component_id: string;
  name: string;
}): boolean {
  if (component.type === "FINISAJ") return true;
  const key = `${component.component_id} ${component.name}`.toLowerCase();
  return key.includes("finis");
}
