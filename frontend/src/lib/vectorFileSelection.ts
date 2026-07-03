/**
 * Vector file selection helpers — metadata only, no geometry parsing.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import {
  deriveVectorMetadataFromFilename,
  inferVectorFileType,
  type VectorFileType,
} from "@/lib/intakeVolumetricSpec";
import { preservePathwayForVectorMetadata } from "@/lib/volumetricIntakePathway";

/** File picker accept — extensions + MIME for SVG quirks on Windows/Electron. */
export const VECTOR_FILE_INPUT_ACCEPT =
  ".svg,image/svg+xml,.dxf,application/dxf,.dwg,.eps,application/postscript,.ai,application/pdf,.pdf";

const EXTENSION_TO_TYPE: Record<string, VectorFileType> = {
  svg: "svg",
  dxf: "dxf",
  dwg: "dwg",
  eps: "other",
  ai: "other",
  pdf: "other",
};

const ALLOWED_EXTENSIONS = new Set(Object.keys(EXTENSION_TO_TYPE));

export interface VectorFileSelectionMetadata {
  fileName: string;
  extension: string;
  mime: string;
  sizeBytes: number;
  fileType: VectorFileType;
  selectedAt: string;
}

export function getVectorFileExtension(fileName: string): string {
  const dot = fileName.lastIndexOf(".");
  if (dot < 0) return "";
  return fileName.slice(dot + 1).toLowerCase();
}

export function isAllowedVectorExtension(extension: string): boolean {
  return ALLOWED_EXTENSIONS.has(extension.toLowerCase());
}

export function validateVectorFileSelection(
  file: File
): { ok: true; metadata: VectorFileSelectionMetadata } | { ok: false; error: string } {
  const fileName = file.name?.trim();
  if (!fileName) {
    return { ok: false, error: "Fișierul selectat nu are nume valid." };
  }

  const extension = getVectorFileExtension(fileName);
  if (!extension) {
    return {
      ok: false,
      error: "Fișierul trebuie să aibă extensie (.svg, .dxf, .dwg, .eps, .ai, .pdf).",
    };
  }

  if (!isAllowedVectorExtension(extension)) {
    return {
      ok: false,
      error: `Tip neacceptat (.${extension}). Folosește SVG, DXF, DWG, EPS, AI sau PDF.`,
    };
  }

  const mime = file.type?.trim() ?? "";
  const fileType = inferVectorFileType(fileName) ?? EXTENSION_TO_TYPE[extension] ?? "other";

  return {
    ok: true,
    metadata: {
      fileName,
      extension,
      mime: mime || (extension === "svg" ? "image/svg+xml" : ""),
      sizeBytes: file.size,
      fileType,
      selectedAt: new Date().toISOString(),
    },
  };
}

export function formatVectorFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function mapVectorFilePickToProductSpec(
  existingSpec: IntakeProductSpec,
  metadata: VectorFileSelectionMetadata
): IntakeProductSpec {
  let next = deriveVectorMetadataFromFilename(existingSpec, metadata.fileName);
  next = {
    ...next,
    vector_file_present: true,
    vector_file_type: metadata.fileType,
    vector_file_mime: metadata.mime || undefined,
    vector_file_size_bytes: metadata.sizeBytes > 0 ? metadata.sizeBytes : undefined,
    vector_file_extension: metadata.extension,
    vector_file_selected_at: metadata.selectedAt,
    vector_file_source: "local_manual",
    vector_analysis_status:
      next.vector_analysis_status && next.vector_analysis_status !== "not_provided"
        ? next.vector_analysis_status
        : "attached_unanalyzed",
    vector_metrics_source: next.vector_metrics_source ?? "manual",
  };
  return preservePathwayForVectorMetadata(next);
}

export function vectorFileMetadataFromSpec(
  spec: IntakeProductSpec | null | undefined
): Partial<VectorFileSelectionMetadata> | undefined {
  if (!spec?.vector_file_name?.trim()) return undefined;
  return {
    fileName: spec.vector_file_name,
    extension: spec.vector_file_extension ?? getVectorFileExtension(spec.vector_file_name),
    mime: spec.vector_file_mime ?? "",
    sizeBytes: spec.vector_file_size_bytes ?? 0,
    fileType: spec.vector_file_type ?? inferVectorFileType(spec.vector_file_name) ?? "other",
    selectedAt: spec.vector_file_selected_at ?? "",
  };
}
