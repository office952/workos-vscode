/**
 * Client-side mirror of backend letter/hole part classification for live quote geometry.
 */

import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";

const LETTER_PRODUCTION_ROLES = new Set<string>(["face"]);

const BBOX_TOLERANCE_MM = 0.5;
const HOLE_AREA_RATIO_MAX = 0.85;

export interface LetterPartClassificationMetrics {
  real_letters_count: number | null;
  inner_holes_count: number | null;
  cutting_contours_count: number | null;
  material_piece_count: number | null;
  outer_perimeter_mm: number | null;
  hole_perimeter_mm: number | null;
  cutting_perimeter_mm: number | null;
  classification_confidence: "high" | "low";
  warnings: string[];
}

interface BoundsMm {
  x: number;
  y: number;
  width: number;
  height: number;
}

function confirmedRoleForLayer(
  confirmation: LayerRoleConfirmation | null | undefined,
  layerId: string,
  layerName: string,
): LayerAutoRole | null {
  if (!confirmation) return null;
  const entry =
    confirmation.layers.find((item) => item.layerKey === layerId || item.layerKey === layerName) ??
    confirmation.layers.find((item) => item.layerName === layerName || item.layerId === layerId);
  if (!entry || entry.confirmationState === "ignored") return null;
  return entry.confirmedRole ?? entry.autoRole ?? null;
}

function partBounds(item: Record<string, unknown>): BoundsMm | null {
  const bounds = item.bounds;
  if (!bounds || typeof bounds !== "object" || Array.isArray(bounds)) return null;
  const row = bounds as Record<string, unknown>;
  const x = Number(row.xMm);
  const y = Number(row.yMm);
  const width = Number(row.widthMm);
  const height = Number(row.heightMm);
  if (![x, y, width, height].every(Number.isFinite)) return null;
  return { x, y, width, height };
}

function bboxArea(bounds: BoundsMm | null): number {
  if (!bounds) return 0;
  return Math.max(0, bounds.width * bounds.height);
}

function bboxContains(outer: BoundsMm, inner: BoundsMm, toleranceMm = BBOX_TOLERANCE_MM): boolean {
  return (
    inner.x >= outer.x - toleranceMm &&
    inner.y >= outer.y - toleranceMm &&
    inner.x + inner.width <= outer.x + outer.width + toleranceMm &&
    inner.y + inner.height <= outer.y + outer.height + toleranceMm
  );
}

function isOrphanHoleCandidate(inner: Record<string, unknown>, outer: Record<string, unknown>): boolean {
  const innerBounds = partBounds(inner);
  const outerBounds = partBounds(outer);
  if (!innerBounds || !outerBounds || inner.id === outer.id) return false;
  const innerArea = bboxArea(innerBounds);
  const outerArea = bboxArea(outerBounds);
  if (innerArea <= 0 || outerArea <= 0) return false;
  if (innerArea >= outerArea * HOLE_AREA_RATIO_MAX) return false;
  return bboxContains(outerBounds, innerBounds);
}

export function classifyLetterPartsFromAnalysis(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): LetterPartClassificationMetrics {
  const empty: LetterPartClassificationMetrics = {
    real_letters_count: null,
    inner_holes_count: null,
    cutting_contours_count: null,
    material_piece_count: null,
    outer_perimeter_mm: null,
    hole_perimeter_mm: null,
    cutting_perimeter_mm: null,
    classification_confidence: "high",
    warnings: [],
  };
  if (!report?.parts) return empty;

  const items = (report.parts.items ?? []).filter(
    (item): item is NonNullable<SvgAnalysisCoreReport["parts"]>["items"][number] => !!item,
  );
  const warnings: string[] = [];
  let confidence: "high" | "low" = "high";

  const subPathDiag = report.parts.splitDiagnostics?.subPathDiagnostics ?? [];
  if (subPathDiag.some((row) => row.classification === "ambiguous")) {
    confidence = "low";
    warnings.push("SUBPATH_CONTAINMENT_AMBIGUOUS — unele contururi interioare pot fi incorect clasificate.");
  }

  const faceItems = items.filter((item) => {
    const source = item.source;
    const layerId = source?.layerId ?? "";
    const layerName = source?.layerName ?? layerId;
    const role = confirmedRoleForLayer(confirmation, layerId, layerName);
    return role != null && LETTER_PRODUCTION_ROLES.has(role);
  });

  const byLayer = new Map<string, typeof faceItems>();
  for (const item of faceItems) {
    const layerName = item.source?.layerName ?? item.source?.layerId ?? "";
    const bucket = byLayer.get(layerName) ?? [];
    bucket.push(item);
    byLayer.set(layerName, bucket);
  }

  const orphanHoleIds = new Set<string>();
  for (const layerItems of byLayer.values()) {
    const sorted = [...layerItems].sort((a, b) => bboxArea(partBounds(b)) - bboxArea(partBounds(a)));
    for (let index = 0; index < sorted.length; index += 1) {
      const candidate = sorted[index] as unknown as Record<string, unknown>;
      for (let outerIndex = 0; outerIndex < index; outerIndex += 1) {
        const outer = sorted[outerIndex] as unknown as Record<string, unknown>;
        if (isOrphanHoleCandidate(candidate, outer)) {
          orphanHoleIds.add(String(candidate.id ?? ""));
          confidence = "low";
          break;
        }
      }
    }
  }

  const realLetterItems = faceItems.filter((item) => !orphanHoleIds.has(String(item.id ?? "")));

  if (!items.length) {
    const nestable = report.parts.nestableCount;
    const count = report.parts.count;
    const realLetters = nestable != null && nestable > 0 ? nestable : count != null && count > 0 ? count : null;
    return {
      ...empty,
      real_letters_count: realLetters,
      material_piece_count: realLetters,
      cutting_contours_count: count ?? realLetters,
      classification_confidence: "low",
      warnings: ["PART_ITEMS_MISSING — folosim agregate nest2 fără clasificare per-part."],
    };
  }

  let embeddedInnerHoles = 0;
  let outerPerimeterMm = 0;
  let innerPerimeterMm = 0;
  let cuttingPerimeterMm = 0;
  let cuttingContoursCount = 0;

  for (const item of realLetterItems) {
    embeddedInnerHoles += item.innerContourCount ?? 0;
    outerPerimeterMm += item.geometry?.outerPerimeterMm ?? 0;
    innerPerimeterMm += item.geometry?.innerPerimeterMm ?? 0;
    cuttingPerimeterMm += item.geometry?.totalContourPerimeterMm ?? 0;
    cuttingContoursCount += item.contourCount ?? 0;
  }

  for (const item of faceItems) {
    if (!orphanHoleIds.has(String(item.id ?? ""))) continue;
    innerPerimeterMm += item.geometry?.outerPerimeterMm ?? item.geometry?.totalContourPerimeterMm ?? 0;
    cuttingPerimeterMm += item.geometry?.totalContourPerimeterMm ?? item.geometry?.outerPerimeterMm ?? 0;
    cuttingContoursCount += Math.max(item.contourCount ?? 0, 1);
  }

  const innerHolesCount = embeddedInnerHoles + orphanHoleIds.size;
  const realLettersCount = realLetterItems.length;

  return {
    real_letters_count: realLettersCount > 0 ? realLettersCount : null,
    inner_holes_count: innerHolesCount > 0 ? innerHolesCount : 0,
    cutting_contours_count: cuttingContoursCount > 0 ? cuttingContoursCount : null,
    material_piece_count: realLettersCount > 0 ? realLettersCount : null,
    outer_perimeter_mm: outerPerimeterMm > 0 ? outerPerimeterMm : null,
    hole_perimeter_mm: innerPerimeterMm > 0 ? innerPerimeterMm : null,
    cutting_perimeter_mm: cuttingPerimeterMm > 0 ? cuttingPerimeterMm : null,
    classification_confidence: confidence,
    warnings,
  };
}
