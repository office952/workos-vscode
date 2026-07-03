/**
 * Geometry role helpers — letter metrics vs support/structure (TPL-VOLUMETRIC-LETTERS).
 */

import type { VectorLayerRole } from "@/lib/svgLayerRoleSuggestion";

export const STRUCTURE_IN_LETTERS_LAYER_WARNING =
  "SVG-ul pare să conțină structură suport în același layer cu literele. Verifică layer mapping; structura nu trebuie inclusă în geometria literelor.";

/** Layers whose shapes feed letter count / perimeter / face area. */
export function isLetterGeometryLayer(role: VectorLayerRole): boolean {
  return role === "volumetric_letters" || role === "letter_face";
}

/** Dibond/ACM panel backing — not letter geometry. */
export function isSupportPanelLayer(role: VectorLayerRole): boolean {
  return role === "support_panel";
}

/** Metal frame / premount bars / structural rectangles — not letter geometry. */
export function isMountingBarsLayer(role: VectorLayerRole): boolean {
  return role === "metal_frame";
}

export function isSupportStructureLayer(role: VectorLayerRole): boolean {
  return isSupportPanelLayer(role) || isMountingBarsLayer(role);
}

export function geometryRoleBucket(
  role: VectorLayerRole
): "letter" | "support" | "frame" | "skip" {
  if (isLetterGeometryLayer(role)) return "letter";
  if (isSupportPanelLayer(role)) return "support";
  if (isMountingBarsLayer(role)) return "frame";
  return "skip";
}
