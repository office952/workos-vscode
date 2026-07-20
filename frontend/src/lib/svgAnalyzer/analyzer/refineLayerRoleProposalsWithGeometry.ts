/**
 * Evidence-driven role proposal refinement for pseudo / solid-fill layers.
 * Uses sibling geometry + closed-contour envelope — never color alone.
 * Artwork/logo candidates are excluded from support refine (R2).
 * Proposals remain unconfirmed.
 */

import type { ClosedContourCandidate, ClosedContourDetectionReport } from "../closed-contour/closedContourTypes";
import { isArtworkOrLogoCandidateLayer } from "./artworkLogoCandidate";
import { isPseudoLayerId } from "./layerNameSemantics";
import type { LayerAutoRole, LayerRoleCandidate } from "./layerRoleTypes";
import type { ConfidenceLevel, LayerAnalysis } from "./types";

function isPseudoLayer(layer: LayerAnalysis): boolean {
  return layer.layerKind === "pseudo" || isPseudoLayerId(layer.id) || /^pseudo[:\s]/i.test(layer.name);
}

function areaSignal(layer: LayerAnalysis): number {
  if (layer.filledAreaSqm != null && layer.filledAreaSqm > 0) return layer.filledAreaSqm;
  if (layer.boundingAreaSqm != null && layer.boundingAreaSqm > 0) return layer.boundingAreaSqm;
  return 0;
}

function complexity(layer: LayerAnalysis): number {
  return Math.max(layer.closedSubPathCount, layer.subPathCount, 0);
}

function isLetterLike(layer: LayerAnalysis): boolean {
  return complexity(layer) >= 3;
}

function isSupportLikeShape(layer: LayerAnalysis): boolean {
  // Outer panels are typically few large closed fills / rects, not multi-glyph paths.
  return complexity(layer) <= 2 && layer.elementCount >= 1;
}

function dimsMatch(
  layer: LayerAnalysis,
  contour: ClosedContourCandidate,
  tolerance = 0.08,
): boolean {
  if (!(layer.widthMm > 0) || !(layer.heightMm > 0)) return false;
  if (!(contour.width_mm > 0) || !(contour.height_mm > 0)) return false;
  const dw = Math.abs(layer.widthMm - contour.width_mm) / contour.width_mm;
  const dh = Math.abs(layer.heightMm - contour.height_mm) / contour.height_mm;
  return dw <= tolerance && dh <= tolerance;
}

function pushCandidate(
  candidates: LayerRoleCandidate[],
  role: LayerAutoRole,
  confidence: ConfidenceLevel,
  reason: string,
): LayerRoleCandidate[] {
  if (candidates.some((entry) => entry.role === role)) {
    return candidates.map((entry) =>
      entry.role === role ? { role, confidence, reason } : entry,
    );
  }
  return [...candidates, { role, confidence, reason }];
}

function withRole(
  layer: LayerAnalysis,
  autoRole: LayerAutoRole,
  autoConfidence: ConfidenceLevel,
  reason: string,
): LayerAnalysis {
  const autoRoleCandidates = pushCandidate(layer.autoRoleCandidates ?? [], autoRole, autoConfidence, reason);
  return {
    ...layer,
    autoRole,
    autoConfidence,
    roleGuess: autoRole,
    autoRoleCandidates,
    roleReason: reason,
    productionHint: autoRole === "printed_artwork" || autoRole === "logo" ? "print_vinyl" : "cnc_cut",
  };
}

function hasPositiveSupportEvidence(
  layer: LayerAnalysis,
  layers: LayerAnalysis[],
  outerCandidates: ClosedContourCandidate[],
  letterLikePseudos: LayerAnalysis[],
): { strong: boolean; reason: string } {
  const hasLetterSibling = layers.some(
    (sibling) => sibling.id !== layer.id && (isLetterLike(sibling) || sibling.autoRole === "face"),
  );
  if (!hasLetterSibling) {
    return { strong: false, reason: "No distinct letter/face sibling for support evidence." };
  }

  const matchesOuter = outerCandidates.some((contour) => dimsMatch(layer, contour));
  const candidateArea = areaSignal(layer);
  const maxSiblingArea = Math.max(
    0,
    ...layers.filter((sibling) => sibling.id !== layer.id).map(areaSignal),
  );
  const dominantArea =
    candidateArea > 0 && (maxSiblingArea === 0 || candidateArea >= maxSiblingArea * 0.85);

  const panelLikeFill =
    (layer.paintEvidence?.fills?.length ?? 0) >= 1 ||
    layer.pathElementCount === 0 ||
    (layer.filledAreaSqm != null && layer.filledAreaSqm > 0);

  const strong =
    panelLikeFill &&
    (matchesOuter ||
      (dominantArea && letterLikePseudos.some((letter) => letter.id !== layer.id)) ||
      (layer.filledAreaSqm != null &&
        layer.filledAreaSqm > 0 &&
        letterLikePseudos.some(
          (letter) => letter.id !== layer.id && letter.filledAreaSqm == null && complexity(letter) >= 3,
        )));

  return {
    strong,
    reason: strong
      ? "Outer/low-complexity solid fill envelope beside letter geometry — propose Contur suport (requires confirmation)."
      : "Insufficient cumulative support evidence — requires operator confirmation.",
  };
}

export function refineLayerRoleProposalsWithGeometry(
  layers: LayerAnalysis[],
  closedContours?: ClosedContourDetectionReport | null,
): LayerAnalysis[] {
  if (!layers.length) return layers;

  const outerCandidates = (closedContours?.candidates ?? []).filter((c) => c.is_outer_candidate);
  const pseudoLayers = layers.filter(isPseudoLayer);
  if (pseudoLayers.length === 0) return layers;

  const letterLikePseudos = pseudoLayers.filter(isLetterLike);
  const supportShapePseudos = pseudoLayers.filter(
    (layer) => isSupportLikeShape(layer) && !isArtworkOrLogoCandidateLayer(layer),
  );

  const strongSupportIds = new Set<string>();

  for (const candidate of supportShapePseudos) {
    const evidence = hasPositiveSupportEvidence(
      candidate,
      layers,
      outerCandidates,
      letterLikePseudos,
    );
    if (evidence.strong) strongSupportIds.add(candidate.id);
  }

  // Ambiguous: several support-shaped pseudos without a single clear outer winner.
  if (strongSupportIds.size > 1 && outerCandidates.length === 0) {
    const areas = [...strongSupportIds].map((id) => {
      const layer = layers.find((entry) => entry.id === id);
      return { id, area: layer ? areaSignal(layer) : 0 };
    });
    areas.sort((a, b) => b.area - a.area);
    if (areas.length >= 2 && areas[0].area > 0 && areas[0].area < areas[1].area * 1.25) {
      strongSupportIds.clear();
    } else if (areas[0]) {
      const winner = areas[0].id;
      strongSupportIds.clear();
      strongSupportIds.add(winner);
    }
  }

  return layers.map((layer) => {
    // Artwork/logo candidates: never overwrite to support_panel; keep guess or demote confidence on conflict.
    if (isArtworkOrLogoCandidateLayer(layer)) {
      if (layer.autoRole === "support_panel") {
        return withRole(
          layer,
          "printed_artwork",
          "medium",
          "Artwork/logo candidate excluded from Contur suport refine — operator must confirm production intent.",
        );
      }
      if (layer.autoRole === "printed_artwork" || layer.autoRole === "logo") {
        return withRole(
          layer,
          layer.autoRole,
          layer.autoConfidence === "high" ? "high" : layer.autoConfidence,
          layer.roleReason ??
            "Artwork/logo candidate preserved — Contur suport refine skipped.",
        );
      }
      return layer;
    }

    if (!isPseudoLayer(layer)) return layer;

    if (strongSupportIds.has(layer.id)) {
      return withRole(
        layer,
        "support_panel",
        "high",
        "Outer/low-complexity solid fill envelope beside letter geometry — propose Contur suport (requires confirmation).",
      );
    }

    if (isLetterLike(layer)) {
      if (layer.autoRole === "face") {
        return withRole(
          layer,
          "face",
          layer.autoConfidence === "low" ? "medium" : layer.autoConfidence,
          "Multi-shape solid fill — volumetric letter geometry candidate (requires confirmation).",
        );
      }
      return withRole(
        layer,
        "face",
        "medium",
        "Multi-shape solid fill — volumetric letter geometry candidate (requires confirmation).",
      );
    }

    if (isSupportLikeShape(layer) && letterLikePseudos.length === 0 && pseudoLayers.length === 1) {
      return withRole(
        layer,
        "unknown",
        "low",
        "Ambiguous solid fill without letter/support sibling evidence — requires operator confirmation.",
      );
    }

    if (layer.autoRole === "face" && complexity(layer) <= 2 && !strongSupportIds.has(layer.id)) {
      if (pseudoLayers.length >= 2) {
        return withRole(
          layer,
          "unknown",
          "low",
          "Ambiguous pseudo fill among multiple solid clusters — requires operator confirmation.",
        );
      }
    }

    return layer;
  });
}
