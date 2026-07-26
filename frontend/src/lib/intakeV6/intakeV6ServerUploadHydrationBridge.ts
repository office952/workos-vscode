/**
 * Minimum hydration bridge: server SVG upload stores source text + path summary,
 * but Page 1 requires canonical client analyzer report (nest2 svg_analysis_json).
 * Re-run the existing client analyzer — do not invent a second parser.
 */

import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { sanitizeIntakeV6SvgPreviewSource } from "@/lib/intakeV6/sanitizeSvgPreview";
import {
  layerChipsFromLayerRoleConfirmation,
  type IntakeV6LayerRoleSetup,
} from "./intakeV6LayerRoleBridge";
import { mergeServerLayerRolesIntoConfirmation } from "./intakeV6PayloadHydrate";
import type { IntakeV6HydratedAnalyzerState } from "./intakeV6PayloadHydrate";

export function needsClientAnalyzerHydrationFromServerUpload(
  payload: Record<string, unknown> | undefined,
  hasLocalAnalyzerReport: boolean,
): boolean {
  if (hasLocalAnalyzerReport) return false;
  if (!payload) return false;
  const text = payload.svg_source_text;
  if (typeof text !== "string" || !text.trim()) return false;
  const analysis = payload.svg_analysis_json;
  if (analysis != null && typeof analysis === "object" && !Array.isArray(analysis)) {
    const confirmation = (analysis as Record<string, unknown>).layerRoleConfirmation;
    if (confirmation != null && typeof confirmation === "object") return false;
  }
  return true;
}

export function buildClientAnalyzerStateFromSvgSourceText(args: {
  svgText: string;
  fileName: string;
  fileSizeBytes: number;
  layerRoleSetup?: IntakeV6LayerRoleSetup | null;
}): IntakeV6HydratedAnalyzerState {
  const { report } = analyzeSvgString(args.svgText, args.fileName, args.fileSizeBytes);
  const draft = report.layerRoleConfirmation;
  const layerRoleConfirmation = args.layerRoleSetup
    ? mergeServerLayerRolesIntoConfirmation(draft, args.layerRoleSetup)
    : draft;
  return {
    svg: {
      fileName: args.fileName,
      fileSizeBytes: args.fileSizeBytes,
      previewSource: sanitizeIntakeV6SvgPreviewSource(args.svgText),
    },
    svgSource: args.svgText,
    analyzerReport: report,
    layerRoleConfirmation,
    layerChips: layerChipsFromLayerRoleConfirmation(layerRoleConfirmation),
  };
}

export function readSvgSourceMetaFromPayload(payload: Record<string, unknown> | undefined): {
  fileName: string;
  fileSizeBytes: number;
  svgText: string;
} | null {
  const text = payload?.svg_source_text;
  if (typeof text !== "string" || !text.trim()) return null;
  const svgSource = payload?.svg_source;
  if (svgSource == null || typeof svgSource !== "object" || Array.isArray(svgSource)) return null;
  const name = (svgSource as Record<string, unknown>).file_name;
  const size = (svgSource as Record<string, unknown>).file_size_bytes;
  return {
    fileName: typeof name === "string" && name.trim() ? name : "upload.svg",
    fileSizeBytes: typeof size === "number" && size > 0 ? size : text.length,
    svgText: text,
  };
}
