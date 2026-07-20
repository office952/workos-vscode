/**
 * Shared artwork/logo candidate detection for refine + finish gates.
 * Not limited to logo_instance_* — uses origin, id, name, and role guess.
 */

import { isArtworkLayerName } from "@/lib/intakeSvgContracts";
import { isLogoLayerId } from "./anaMariaLetterSemantics";
import { isNeutralLogoInstanceId } from "@/lib/intakeV6/layerInstanceIdentity";
import { isRasterArtworkLayerId } from "./layerNameSemantics";
import type { LayerAnalysis } from "./types";

const ARTWORK_ORIGINS = new Set([
  "stroke_vector_outline",
  "corel_logo_stroke_outline",
  "corel_logo_layer",
  "raster_image_split",
]);

export function isArtworkOrLogoCandidateLayer(layer: Pick<
  LayerAnalysis,
  "id" | "name" | "layerOrigin" | "autoRole" | "roleGuess"
>): boolean {
  if (layer.autoRole === "printed_artwork" || layer.autoRole === "logo") return true;
  if (layer.roleGuess === "printed_artwork" || layer.roleGuess === "logo") return true;
  if (layer.layerOrigin && ARTWORK_ORIGINS.has(layer.layerOrigin)) return true;
  if (isRasterArtworkLayerId(layer.id) || isNeutralLogoInstanceId(layer.id) || isLogoLayerId(layer.id)) {
    return true;
  }
  if (isArtworkLayerName(layer.name) || isArtworkLayerName(layer.id)) return true;
  return false;
}
