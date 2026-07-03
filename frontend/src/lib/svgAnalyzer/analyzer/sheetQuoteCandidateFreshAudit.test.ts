/**
 * Phase 1 audit metrics — run via vitest (needs DOM).
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { buildLayerRoleConfirmationDraft } from "@/lib/svgAnalyzer/analyzer/buildLayerRoleConfirmation";
import { applyLayerRoleSelection } from "@/lib/svgAnalyzer/lib/layerRoleConfirmationState";
import type { LayerRoleConfirmation } from "@/lib/svgAnalyzer/lib/layerRoleConfirmationState";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer/analyzer/types";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../fixtures");
const ORPHAN_SPLIT_RE = /^split_layer_\d+_\d+$/;

function confirmAllSuggestedLayerRoles(confirmation: LayerRoleConfirmation): LayerRoleConfirmation {
  let next = confirmation;
  for (const layer of confirmation.layers) {
    if (layer.confirmationState !== "pending") continue;
    const role = layer.autoRole !== "unknown" ? layer.autoRole : "face";
    next = applyLayerRoleSelection(next, layer.layerKey, role);
  }
  return next;
}

function analyzeFixture(fileName: string) {
  const svg = readFileSync(join(fixtureDir, fileName), "utf8");
  return analyzeSvgString(svg, fileName, svg.length);
}

function roleMap(report: SvgAnalysisCoreReport, confirmed: LayerRoleConfirmation) {
  const map = new Map<string, string>();
  for (const layer of confirmed.layers) {
    const role = layer.confirmedRole ?? layer.autoRole;
    map.set(layer.layerKey, role);
    if (layer.layerName) map.set(layer.layerName, role);
  }
  for (const layer of report.layers) {
    if (!map.has(layer.id)) map.set(layer.id, layer.autoRole);
    if (!map.has(layer.name)) map.set(layer.name, layer.autoRole);
  }
  return map;
}

function partLayerRole(
  part: { source?: { layerId?: string | null; layerName?: string | null } },
  roles: Map<string, string>,
) {
  const layerId = part.source?.layerId ?? "";
  const layerName = part.source?.layerName ?? "";
  return roles.get(layerId) ?? roles.get(layerName) ?? "unknown";
}

function isOrphanSplit(part: { id: string; source?: { layerId?: string | null; layerName?: string | null } }) {
  if (part.source?.layerId || part.source?.layerName) return false;
  return ORPHAN_SPLIT_RE.test(part.id);
}

function unionBBoxSqm(
  parts: Array<{ bounds: { xMm?: number | null; yMm?: number | null; widthMm?: number | null; heightMm?: number | null } }>,
) {
  let minX = Number.POSITIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  for (const part of parts) {
    const x = part.bounds.xMm ?? null;
    const y = part.bounds.yMm ?? null;
    const w = part.bounds.widthMm ?? null;
    const h = part.bounds.heightMm ?? null;
    if (x == null || y == null || w == null || h == null || w <= 0 || h <= 0) continue;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + w);
    maxY = Math.max(maxY, y + h);
  }
  if (!Number.isFinite(minX)) return null;
  return Math.round(((maxX - minX) * (maxY - minY)) / 1_000_000 * 10_000) / 10_000;
}

export function computeFreshSheetQuoteCandidateMetrics(fileName: string) {
  const { report } = analyzeFixture(fileName);
  const draft = buildLayerRoleConfirmationDraft(report.layers);
  const confirmed = confirmAllSuggestedLayerRoles(draft);
  const roles = roleMap(report, confirmed);
  const parts = report.parts?.items ?? [];

  const productionChildParts = parts.filter((part) => {
    if (isOrphanSplit(part)) return false;
    const role = partLayerRole(part, roles);
    if (role === "printed_artwork" || role === "ignored" || role === "artwork") return false;
    if (part.derivedPartKind === "inner-hole-package") return false;
    return role === "face" || role === "backing" || role === "support_panel";
  });
  const productionChildBBoxSumSqm = Math.round(
    productionChildParts.reduce((sum, part) => sum + (part.bounds.boundingAreaSqm ?? 0), 0) * 10_000,
  ) / 10_000;

  const faceChildParts = parts.filter((part) => {
    if (isOrphanSplit(part)) return false;
    const role = partLayerRole(part, roles);
    if (role === "printed_artwork" || role === "ignored" || role === "artwork") return false;
    if (part.derivedPartKind === "inner-hole-package") return false;
    return role === "face";
  });

  const childPartBBoxSumSqm = Math.round(
    faceChildParts.reduce((sum, part) => sum + (part.bounds.boundingAreaSqm ?? 0), 0) * 10_000,
  ) / 10_000;

  const semanticGroupBBoxSumSqm = Math.round(
    report.layers
      .filter((layer) => (roles.get(layer.id) ?? roles.get(layer.name)) === "face")
      .reduce((sum, layer) => sum + (layer.boundingAreaSqm ?? layer.filledAreaSqm ?? 0), 0) * 10_000,
  ) / 10_000;

  const eligibleAreaSqm = Math.round(
    report.layers
      .filter((layer) => (roles.get(layer.id) ?? roles.get(layer.name)) === "face")
      .reduce((sum, layer) => sum + (layer.filledAreaSqm ?? layer.boundingAreaSqm ?? 0), 0) * 10_000,
  ) / 10_000;

  const designSpaceUnionBBoxSqm = unionBBoxSqm(faceChildParts);
  const designSpaceUnionBBoxWithBufferSqm =
    designSpaceUnionBBoxSqm != null ? Math.round(designSpaceUnionBBoxSqm * 1.03 * 10_000) / 10_000 : null;

  const nesting = report.nesting;
  const sheet = nesting?.sheets?.[0];
  const layoutOccupiedSqm =
    sheet?.usedWidthMm && sheet?.consumedLengthMm
      ? Math.round((sheet.usedWidthMm * sheet.consumedLengthMm) / 1_000_000 * 10_000) / 10_000
      : null;
  const fullSheetSqm = sheet?.usedSheetAreaSqm ?? null;

  const facePlacements = (sheet?.placements ?? []).filter((p) => {
    const baseId = p.partId.replace(/_q\d+$/, "");
    const part = parts.find((item) => item.id === p.partId || item.id === baseId);
    if (!part) return false;
    return partLayerRole(part, roles) === "face";
  });
  const placementFootprintFaceSqm = Math.round(
    facePlacements.reduce((sum, p) => sum + (p.placedWidthMm * p.placedHeightMm) / 1_000_000, 0) * 10_000,
  ) / 10_000;
  const faceUnionBBoxSqm = unionBBoxSqm(
    facePlacements.map((p) => ({
      bounds: { xMm: p.xMm, yMm: p.yMm, widthMm: p.placedWidthMm, heightMm: p.placedHeightMm },
    })),
  );

  const allChildBBoxSum = Math.round(
    parts.filter((p) => !isOrphanSplit(p)).reduce((sum, part) => sum + (part.bounds.boundingAreaSqm ?? 0), 0) * 10_000,
  ) / 10_000;
  const allPartsUnion = unionBBoxSqm(parts.filter((p) => !isOrphanSplit(p)));

  return {
    fileName,
    partsCount: parts.length,
    childPartsCount: parts.length,
    orphan_defs_count: parts.filter((p) => isOrphanSplit(p)).length,
    eligibleAreaSqm,
    productionChildPartBBoxSumSqm: productionChildBBoxSumSqm,
    childPartBBoxSumSqm,
    allChildPartBBoxSumSqm: allChildBBoxSum,
    allPartsDesignUnionBBoxSqm: allPartsUnion,
    semanticGroupBBoxSumSqm,
    designSpaceUnionBBoxSqm,
    designSpaceUnionBBoxWithBufferSqm,
    placementFootprintFaceSqm,
    faceUnionBBoxSqm,
    nestingShelfOccupiedSqm: layoutOccupiedSqm,
    layoutOccupiedSqm,
    fullSheetSqm,
    corelLayerCount: report.layers.filter((l) => !l.id.startsWith("pseudo:")).length,
    faceGroups: report.layers.filter((l) => (roles.get(l.id) ?? roles.get(l.name)) === "face").length,
    artworkGroups: report.layers.filter(
      (l) => (roles.get(l.id) ?? roles.get(l.name)) === "printed_artwork",
    ).length,
  };
}

describe("sheet quote candidate fresh audit", () => {
  it("logs Ana Maria unlayered metrics", () => {
    const metrics = computeFreshSheetQuoteCandidateMetrics("ana-maria-gradinita-fara-layere.svg");
    console.log("ANA_MARIA_FRESH", JSON.stringify(metrics, null, 2));
  });

  it("logs Ana Maria layered metrics", () => {
    const metrics = computeFreshSheetQuoteCandidateMetrics("ana-maria-gradinita.svg");
    console.log("ANA_MARIA_LAYERED_FRESH", JSON.stringify(metrics, null, 2));
  });

  it("logs PBL metrics", () => {
    const metrics = computeFreshSheetQuoteCandidateMetrics("pbl-layere.svg");
    console.log("PBL_FRESH", JSON.stringify(metrics, null, 2));
  });
});
