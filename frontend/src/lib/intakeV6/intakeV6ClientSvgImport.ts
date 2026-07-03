import { analyzeSvgString, type LayerRoleConfirmation, type SvgAnalysisReport } from "@/lib/svgAnalyzer";
import { isValidIntakeV6SvgFile } from "@/lib/intakeV6/intakeV6SvgUploadFlow";
import { sanitizeIntakeV6SvgPreviewSource } from "@/lib/intakeV6/sanitizeSvgPreview";
import { layerChipsFromLayerRoleConfirmation } from "./intakeV6LayerRoleBridge";
import type { IntakeV6LayerChip } from "./intakeV6Contracts";

export type IntakeV6ClientSvgImportResult =
	| {
			ok: true;
			fileName: string;
			fileSizeBytes: number;
			svgSource: string;
			previewSource: string;
			report: SvgAnalysisReport;
			layerRoleConfirmation: LayerRoleConfirmation;
			layerChips: IntakeV6LayerChip[];
			parseErrors: string[];
		}
	| { ok: false; message: string; kind: "not_svg" | "empty" | "analyze_failed" };

export async function analyzeSvgFileForIntakeV6Client(file: File): Promise<IntakeV6ClientSvgImportResult> {
	if (!isValidIntakeV6SvgFile(file)) {
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
		const previewSource = sanitizeIntakeV6SvgPreviewSource(source);
		const layerRoleConfirmation = report.layerRoleConfirmation;
		const layerChips = layerChipsFromLayerRoleConfirmation(layerRoleConfirmation);

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

export function describePickedFileForIntakeV6Diagnostics(file: File): string {
	return `${file.name} · ${file.size} B · MIME „${file.type || "(gol)"}” · SVG=${isValidIntakeV6SvgFile(file) ? "da" : "nu"}`;
}
