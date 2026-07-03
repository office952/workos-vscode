/**
 * Quote-relevant geometry from nest2 analysis + confirmed layer roles.
 * Mirrors V2 geometrySync inputs (letter_perimeter_m, face_area_m2, letter_count).
 */

import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { classifyLetterPartsFromAnalysis } from "./intakeV4LetterPartClassification";

export interface IntakeV4ArtworkBox {
  layer_key: string;
  layer_name: string;
  width_mm: number | null;
  height_mm: number | null;
  area_m2: number | null;
}

export interface IntakeV4QuoteGeometry {
  letter_perimeter_m: number | null;
  total_letter_perimeter_ml: number | null;
  return_material_perimeter_ml: number | null;
  face_cutting_perimeter_ml: number | null;
  cutting_perimeter_ml: number | null;
  hole_perimeter_ml: number | null;
  face_area_m2: number | null;
  artwork_area_m2: number | null;
  artwork_boxes: IntakeV4ArtworkBox[];
  letter_count: number | null;
  real_letters_count: number | null;
  inner_holes_count: number | null;
  cutting_contours_count: number | null;
  material_piece_count: number | null;
  letter_return_perimeter_ml: number | null;
  artwork_return_perimeter_ml: number | null;
  led_perimeter_ml: number | null;
  artwork_piece_count: number | null;
  volumetric_piece_count: number | null;
  part_classification_confidence: "high" | "low" | null;
  primary_letters_layer_key: string | null;
  width_mm: number | null;
  height_mm: number | null;
  geometry_source:
    | "nest2_face_layers"
    | "nest2_face_parts_outer"
    | "nest2_document_geometry"
    | "missing";
  confirmed: boolean;
}

const FACE_ROLES: LayerAutoRole[] = ["face"];
const ARTWORK_ROLES = new Set<string>(["printed_artwork", "logo", "policromie"]);

function round4(value: number): number {
  return Math.round(value * 10_000) / 10_000;
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

function layerMatchesRole(role: LayerAutoRole | null, allowed: LayerAutoRole[]): boolean {
  return role != null && allowed.includes(role);
}

function readFinishSetupFromPayload(
  payload: Record<string, unknown> | undefined,
): Record<string, unknown> {
  const finish = payload?.finish_setup;
  if (finish != null && typeof finish === "object" && !Array.isArray(finish)) {
    return finish as Record<string, unknown>;
  }
  return {};
}

function returnFinishActive(finishType: unknown): boolean {
  const token = String(finishType ?? "").trim().toLowerCase();
  return token !== "" && token !== "none" && token !== "no_return" && token !== "without_return";
}

function faceLayersReturnActive(finishSetup: Record<string, unknown>): boolean {
  const groups = finishSetup.letter_group_finishes;
  const defaultReturn = finishSetup.return_finish_type;
  if (Array.isArray(groups) && groups.length > 0) {
    return groups.some(
      (group) =>
        group != null &&
        typeof group === "object" &&
        returnFinishActive((group as Record<string, unknown>).return_finish_type ?? defaultReturn),
    );
  }
  return returnFinishActive(defaultReturn);
}

function layerPerimeterMlFromReport(
  report: SvgAnalysisCoreReport,
  layerKey: string,
  layerName: string,
): number | null {
  for (const layer of report.layers ?? []) {
    const id = layer.id ?? "";
    const name = layer.name ?? id;
    if (![layerKey, layerName].some((token) => token && (token === id || token === name))) continue;
    if (layer.perimeterMl != null && layer.perimeterMl > 0) return layer.perimeterMl;
    if (layer.perimeterMm != null && layer.perimeterMm > 0) return layer.perimeterMm / 1000;
  }
  return null;
}

export function enrichQuoteGeometryWithVolumetricReturn(
  base: IntakeV4QuoteGeometry,
  report: SvgAnalysisCoreReport,
  finishSetup: Record<string, unknown>,
): IntakeV4QuoteGeometry {
  const outerMl = base.led_perimeter_ml ?? base.letter_perimeter_m;
  const innerMl = base.hole_perimeter_ml;
  const cncMl =
    base.cutting_perimeter_ml ??
    (outerMl != null ? round4(outerMl + (innerMl ?? 0)) : null);

  let letterReturnMl = outerMl;
  if (faceLayersReturnActive(finishSetup) && outerMl != null) {
    letterReturnMl = round4(outerMl + (innerMl ?? 0));
  }

  let artworkPieceCount = 0;
  let artworkReturnMl = 0;
  const artworkFinishes = finishSetup.artwork_finishes;
  if (Array.isArray(artworkFinishes)) {
    for (const row of artworkFinishes) {
      if (row == null || typeof row !== "object") continue;
      const art = row as Record<string, unknown>;
      if (!returnFinishActive(art.return_finish_type)) continue;
      const layerKey = String(art.layer_key ?? "");
      const layerName = String(art.layer_name ?? layerKey);
      const perimeter = layerPerimeterMlFromReport(report, layerKey, layerName);
      if (perimeter == null || perimeter <= 0) continue;
      artworkPieceCount += Math.max(Number(art.element_count) || 1, 1);
      artworkReturnMl += perimeter;
    }
  }

  const realLetters = base.real_letters_count ?? base.letter_count ?? 0;
  const totalReturnMl = (letterReturnMl ?? 0) + artworkReturnMl;

  return {
    ...base,
    letter_perimeter_m: outerMl != null ? round4(outerMl) : base.letter_perimeter_m,
    letter_return_perimeter_ml: letterReturnMl != null ? round4(letterReturnMl) : null,
    artwork_return_perimeter_ml: artworkReturnMl > 0 ? round4(artworkReturnMl) : null,
    return_material_perimeter_ml: totalReturnMl > 0 ? round4(totalReturnMl) : null,
    face_cutting_perimeter_ml: cncMl,
    cutting_perimeter_ml: cncMl,
    led_perimeter_ml: outerMl != null ? round4(outerMl) : null,
    artwork_piece_count: artworkPieceCount > 0 ? artworkPieceCount : null,
    volumetric_piece_count:
      realLetters + artworkPieceCount > 0 ? realLetters + artworkPieceCount : null,
  };
}

export function extractQuoteGeometryFromAnalyzer(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): IntakeV4QuoteGeometry {
  const empty: IntakeV4QuoteGeometry = {
    letter_perimeter_m: null,
    total_letter_perimeter_ml: null,
    return_material_perimeter_ml: null,
    face_cutting_perimeter_ml: null,
    cutting_perimeter_ml: null,
    hole_perimeter_ml: null,
    face_area_m2: null,
    artwork_area_m2: null,
    artwork_boxes: [],
    letter_count: null,
    real_letters_count: null,
    inner_holes_count: null,
    cutting_contours_count: null,
    material_piece_count: null,
    letter_return_perimeter_ml: null,
    artwork_return_perimeter_ml: null,
    led_perimeter_ml: null,
    artwork_piece_count: null,
    volumetric_piece_count: null,
    part_classification_confidence: null,
    primary_letters_layer_key: null,
    width_mm: report?.document.widthMm ?? null,
    height_mm: report?.document.heightMm ?? null,
    geometry_source: "missing",
    confirmed: false,
  };

  if (!report) return empty;

  let facePerimeterMl = 0;
  let faceAreaSqm = 0;
  let artworkAreaSqm = 0;
  const artworkBoxes: IntakeV4ArtworkBox[] = [];
  let faceLayerCount = 0;
  let primaryKey: string | null = null;

  for (const layer of report.layers) {
    const role = confirmedRoleForLayer(confirmation, layer.id, layer.name);
    const area = layer.filledAreaSqm ?? layer.boundingAreaSqm ?? 0;

    if (role != null && ARTWORK_ROLES.has(role)) {
      if (area > 0) artworkAreaSqm += area;
      artworkBoxes.push({
        layer_key: layer.id,
        layer_name: layer.name,
        width_mm: layer.widthMm ?? null,
        height_mm: layer.heightMm ?? null,
        area_m2: area > 0 ? round4(area) : null,
      });
      continue;
    }

    if (!layerMatchesRole(role, FACE_ROLES)) continue;

    const perimeterMl = layer.perimeterMl ?? (layer.perimeterMm != null ? layer.perimeterMm / 1000 : 0);
    if (perimeterMl > 0) {
      facePerimeterMl += perimeterMl;
      faceLayerCount += 1;
      if (!primaryKey) primaryKey = layer.id ?? layer.name;
    }

    if (area > 0) faceAreaSqm += area;
  }

  const classification = classifyLetterPartsFromAnalysis(report, confirmation);
  const letterCount =
    classification.real_letters_count ??
    (faceLayerCount > 0 ? faceLayerCount : null);

  const outerPerimeterMl =
    classification.outer_perimeter_mm != null && classification.outer_perimeter_mm > 0
      ? classification.outer_perimeter_mm / 1000
      : null;
  const cuttingPerimeterMl =
    classification.cutting_perimeter_mm != null && classification.cutting_perimeter_mm > 0
      ? classification.cutting_perimeter_mm / 1000
      : null;
  const holePerimeterMl =
    classification.hole_perimeter_mm != null && classification.hole_perimeter_mm > 0
      ? classification.hole_perimeter_mm / 1000
      : null;

  const sharedCounts = {
    letter_count: letterCount,
    real_letters_count: letterCount,
    inner_holes_count: classification.inner_holes_count,
    cutting_contours_count: classification.cutting_contours_count,
    material_piece_count: classification.material_piece_count,
    part_classification_confidence: classification.classification_confidence,
    face_cutting_perimeter_ml: cuttingPerimeterMl != null ? round4(cuttingPerimeterMl) : null,
    cutting_perimeter_ml: cuttingPerimeterMl != null ? round4(cuttingPerimeterMl) : null,
    hole_perimeter_ml: holePerimeterMl != null ? round4(holePerimeterMl) : null,
  };

  if (outerPerimeterMl != null && outerPerimeterMl > 0) {
    return enrichQuoteGeometryWithVolumetricReturn(
      {
        letter_perimeter_m: round4(outerPerimeterMl),
        total_letter_perimeter_ml: round4(outerPerimeterMl),
        return_material_perimeter_ml: null,
        face_area_m2: faceAreaSqm > 0 ? round4(faceAreaSqm) : null,
        artwork_area_m2: artworkAreaSqm > 0 ? round4(artworkAreaSqm) : null,
        artwork_boxes: artworkBoxes,
        primary_letters_layer_key: primaryKey,
        width_mm: report.document.widthMm,
        height_mm: report.document.heightMm,
        geometry_source: "nest2_face_parts_outer",
        confirmed: confirmation?.confirmationStatus === "complete",
        letter_return_perimeter_ml: null,
        artwork_return_perimeter_ml: null,
        led_perimeter_ml: round4(outerPerimeterMl),
        artwork_piece_count: null,
        volumetric_piece_count: null,
        ...sharedCounts,
      },
      report,
      {},
    );
  }

  if (facePerimeterMl > 0) {
    return {
      letter_perimeter_m: round4(facePerimeterMl),
      total_letter_perimeter_ml: round4(facePerimeterMl),
      return_material_perimeter_ml: round4(facePerimeterMl),
      face_area_m2: faceAreaSqm > 0 ? round4(faceAreaSqm) : null,
      artwork_area_m2: artworkAreaSqm > 0 ? round4(artworkAreaSqm) : null,
      artwork_boxes: artworkBoxes,
      primary_letters_layer_key: primaryKey,
      width_mm: report.document.widthMm,
      height_mm: report.document.heightMm,
      geometry_source: "nest2_face_layers",
      confirmed: confirmation?.confirmationStatus === "complete",
      ...sharedCounts,
    };
  }

  const docPerimeterMl =
    report.geometry.perimeterMl ??
    (report.geometry.perimeterMm != null ? report.geometry.perimeterMm / 1000 : null);

  if (docPerimeterMl != null && docPerimeterMl > 0) {
    return {
      ...empty,
      letter_perimeter_m: round4(docPerimeterMl),
      total_letter_perimeter_ml: round4(docPerimeterMl),
      return_material_perimeter_ml: round4(docPerimeterMl),
      face_area_m2: report.document.boundingAreaSqm ?? report.document.filledAreaSqm ?? null,
      artwork_area_m2: artworkAreaSqm > 0 ? round4(artworkAreaSqm) : null,
      artwork_boxes: artworkBoxes,
      geometry_source: "nest2_document_geometry",
      confirmed: confirmation?.confirmationStatus === "complete",
      ...sharedCounts,
    };
  }

  return empty;
}

export function mergeQuoteGeometryIntoRecord(
  target: Record<string, unknown> | undefined,
  quote: IntakeV4QuoteGeometry,
): Record<string, unknown> {
  const next = { ...(target ?? {}) };
  if (quote.letter_perimeter_m != null) {
    next.letter_perimeter_m = quote.letter_perimeter_m;
    next.total_letter_perimeter_ml = quote.total_letter_perimeter_ml;
  }
  if (quote.return_material_perimeter_ml != null) {
    next.return_material_perimeter_ml = quote.return_material_perimeter_ml;
  }
  if (quote.face_area_m2 != null) {
    next.face_area_m2 = quote.face_area_m2;
    next.letter_face_area_m2 = quote.face_area_m2;
  }
  if (quote.artwork_area_m2 != null) {
    next.artwork_area_m2 = quote.artwork_area_m2;
  }
  if (quote.artwork_boxes.length > 0) {
    next.artwork_boxes = quote.artwork_boxes;
  }
  if (quote.letter_count != null) {
    next.letter_count = quote.letter_count;
    next.real_letters_count = quote.real_letters_count ?? quote.letter_count;
  }
  if (quote.inner_holes_count != null) next.inner_holes_count = quote.inner_holes_count;
  if (quote.cutting_contours_count != null) next.cutting_contours_count = quote.cutting_contours_count;
  if (quote.material_piece_count != null) next.material_piece_count = quote.material_piece_count;
  if (quote.face_cutting_perimeter_ml != null) {
    next.face_cutting_perimeter_ml = quote.face_cutting_perimeter_ml;
    next.cutting_perimeter_ml = quote.cutting_perimeter_ml;
  }
  if (quote.hole_perimeter_ml != null) next.hole_perimeter_ml = quote.hole_perimeter_ml;
  if (quote.width_mm != null) next.width_mm = quote.width_mm;
  if (quote.height_mm != null) next.height_mm = quote.height_mm;
  if (quote.primary_letters_layer_key) {
    next.primary_letters_layer_key = quote.primary_letters_layer_key;
  }
  return next;
}

export function readQuoteGeometryFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4QuoteGeometry | null {
  const raw = payload?.quote_geometry;
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return null;
  const g = raw as Record<string, unknown>;
  return {
    letter_perimeter_m: typeof g.letter_perimeter_m === "number" ? g.letter_perimeter_m : null,
    total_letter_perimeter_ml:
      typeof g.total_letter_perimeter_ml === "number" ? g.total_letter_perimeter_ml : null,
    return_material_perimeter_ml:
      typeof g.return_material_perimeter_ml === "number" ? g.return_material_perimeter_ml : null,
    face_area_m2: typeof g.face_area_m2 === "number" ? g.face_area_m2 : null,
    artwork_area_m2: typeof g.artwork_area_m2 === "number" ? g.artwork_area_m2 : null,
    artwork_boxes: Array.isArray(g.artwork_boxes)
      ? g.artwork_boxes
          .filter((item): item is Record<string, unknown> => item != null && typeof item === "object")
          .map((item) => ({
            layer_key: typeof item.layer_key === "string" ? item.layer_key : "",
            layer_name: typeof item.layer_name === "string" ? item.layer_name : "",
            width_mm: typeof item.width_mm === "number" ? item.width_mm : null,
            height_mm: typeof item.height_mm === "number" ? item.height_mm : null,
            area_m2: typeof item.area_m2 === "number" ? item.area_m2 : null,
          }))
      : [],
    letter_count: typeof g.letter_count === "number" ? g.letter_count : null,
    real_letters_count: typeof g.real_letters_count === "number" ? g.real_letters_count : null,
    inner_holes_count: typeof g.inner_holes_count === "number" ? g.inner_holes_count : null,
    cutting_contours_count: typeof g.cutting_contours_count === "number" ? g.cutting_contours_count : null,
    material_piece_count: typeof g.material_piece_count === "number" ? g.material_piece_count : null,
    letter_return_perimeter_ml:
      typeof g.letter_return_perimeter_ml === "number" ? g.letter_return_perimeter_ml : null,
    artwork_return_perimeter_ml:
      typeof g.artwork_return_perimeter_ml === "number" ? g.artwork_return_perimeter_ml : null,
    led_perimeter_ml: typeof g.led_perimeter_ml === "number" ? g.led_perimeter_ml : null,
    artwork_piece_count: typeof g.artwork_piece_count === "number" ? g.artwork_piece_count : null,
    volumetric_piece_count: typeof g.volumetric_piece_count === "number" ? g.volumetric_piece_count : null,
    face_cutting_perimeter_ml:
      typeof g.face_cutting_perimeter_ml === "number" ? g.face_cutting_perimeter_ml : null,
    cutting_perimeter_ml: typeof g.cutting_perimeter_ml === "number" ? g.cutting_perimeter_ml : null,
    hole_perimeter_ml: typeof g.hole_perimeter_ml === "number" ? g.hole_perimeter_ml : null,
    part_classification_confidence:
      g.part_classification_confidence === "high" || g.part_classification_confidence === "low"
        ? g.part_classification_confidence
        : null,
    primary_letters_layer_key:
      typeof g.primary_letters_layer_key === "string" ? g.primary_letters_layer_key : null,
    width_mm: typeof g.width_mm === "number" ? g.width_mm : null,
    height_mm: typeof g.height_mm === "number" ? g.height_mm : null,
    geometry_source:
      g.geometry_source === "nest2_face_layers" ||
      g.geometry_source === "nest2_face_parts_outer" ||
      g.geometry_source === "nest2_document_geometry" ||
      g.geometry_source === "missing"
        ? g.geometry_source
        : "missing",
    confirmed: g.confirmed === true,
  };
}

function readPersistedSvgHash(payload: Record<string, unknown> | undefined): string | null {
  const raw = payload?.svg_source;
  if (raw != null && typeof raw === "object" && !Array.isArray(raw)) {
    const hash = (raw as Record<string, unknown>).file_hash;
    return typeof hash === "string" && hash.trim().length > 0 ? hash : null;
  }
  return null;
}

export function resolveQuoteGeometryForWorkspace(args: {
  payload: Record<string, unknown> | undefined;
  analyzerReport: SvgAnalysisCoreReport | null | undefined;
  layerRoleConfirmation: LayerRoleConfirmation | null | undefined;
  localFileHash: string | null;
}): IntakeV4QuoteGeometry {
  const finishSetup = readFinishSetupFromPayload(args.payload);
  const persisted = readQuoteGeometryFromPayload(args.payload);
  const persistedHash = readPersistedSvgHash(args.payload);
  const localHash = args.localFileHash;

  if (persisted && (localHash == null || persistedHash == null || localHash === persistedHash)) {
    return persisted;
  }

  if (args.analyzerReport) {
    const base = extractQuoteGeometryFromAnalyzer(args.analyzerReport, args.layerRoleConfirmation);
    return enrichQuoteGeometryWithVolumetricReturn(base, args.analyzerReport, finishSetup);
  }

  if (persisted) return persisted;

  return extractQuoteGeometryFromAnalyzer(args.analyzerReport, args.layerRoleConfirmation);
}

export function readLetterPerimeterMFromSources(
  pathGeometry: Record<string, unknown> | undefined,
  quoteGeometry: IntakeV4QuoteGeometry | null,
  analyzerReport: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): number | null {
  if (quoteGeometry?.letter_perimeter_m != null && quoteGeometry.letter_perimeter_m > 0) {
    return quoteGeometry.letter_perimeter_m;
  }

  if (pathGeometry && typeof pathGeometry === "object") {
    for (const key of ["letter_perimeter_m", "total_letter_perimeter_ml"] as const) {
      const raw = pathGeometry[key];
      if (raw == null) continue;
      const value = Number(raw);
      if (Number.isFinite(value) && value > 0) return value;
    }
  }

  const live = extractQuoteGeometryFromAnalyzer(analyzerReport, confirmation);
  return live.letter_perimeter_m;
}

export function findOutOfScopeLayerWarnings(
  confirmation: LayerRoleConfirmation | null | undefined,
): string[] {
  if (!confirmation) return [];
  const warnings: string[] = [];
  for (const layer of confirmation.layers) {
    if (layer.confirmationState === "ignored") continue;
    const role = layer.confirmedRole ?? layer.autoRole;
    const name = layer.layerName ?? layer.layerKey;
    if (role === "support_panel" || role === "bond_panel") {
      warnings.push(`Strat „${name}” (ACM/casetat) — standby, nu intră în quote litere volumetrice.`);
    }
    if (role === "inner_hole" && /slogan|texte-decupate/i.test(name)) {
      warnings.push(`Strat „${name}” (litere slogan) — standby până la template dedicat.`);
    }
  }
  return warnings;
}
