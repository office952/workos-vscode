import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { isValidIntakeV4SvgFile } from "@/lib/intakeV6/intakeV4SvgUploadFlow";
import { sanitizeIntakeV4SvgPreviewSource } from "@/lib/intakeV6/sanitizeSvgPreview";
import { layerChipsFromLayerRoleConfirmation } from "./intakeV4LayerRoleBridge";
import type { IntakeV4LayerChip } from "./intakeV4Contracts";
import type { LayerRoleConfirmation } from "@/lib/svgAnalyzer";
import type { SvgAnalysisReport } from "@/lib/svgAnalyzer";

export type IntakeV4ClientSvgImportResult =
  | {
      ok: true;
      fileName: string;
      fileSizeBytes: number;
      svgSource: string;
      previewSource: string;
      report: SvgAnalysisReport;
      layerRoleConfirmation: LayerRoleConfirmation;
      layerChips: IntakeV4LayerChip[];
      parseErrors: string[];
    }
  | { ok: false; message: string; kind: "not_svg" | "empty" | "analyze_failed" };

/** nest2 SvgAnalyzerPage.handleFileSelected — client-only, no server upload. */
export async function analyzeSvgFileForIntakeV4Client(file: File): Promise<IntakeV4ClientSvgImportResult> {
  if (!isValidIntakeV4SvgFile(file)) {
    return {
      ok: false,
      kind: "not_svg",
      message: `Fișier respins: „${file.name}” — ${file.type ? `MIME „${file.type}”` : "MIME gol (Windows)"}. Necesită .svg.`,
    };
  }

  try {
    const source = await file.text();
    if (!source.trim()) {
      return { ok: false, kind: "empty", message: "Fișierul SVG este gol." };
    }

    const { report } = analyzeSvgString(source, file.name, file.size);
    const previewSource = sanitizeIntakeV4SvgPreviewSource(source);
    const layerRoleConfirmation = report.layerRoleConfirmation;
    const layerChips = layerChipsFromLayerRoleConfirmation(layerRoleConfirmation);

    // nest2: show preview + layers even when report.errors (parse warnings) exist
    return {
      ok: true,
      fileName: file.name,
      fileSizeBytes: file.size,
      svgSource: source,
      previewSource,
      report,
      layerRoleConfirmation,
      layerChips,
      parseErrors: report.errors,
    };
  } catch (err) {
    return {
      ok: false,
      kind: "analyze_failed",
      message: err instanceof Error ? err.message : "Analiză SVG eșuată.",
    };
  }
}

export function describePickedFileForDiagnostics(file: File): string {
  return `${file.name} · ${file.size} B · MIME „${file.type || "(gol)"}” · SVG=${isValidIntakeV4SvgFile(file) ? "da" : "nu"}`;
}
