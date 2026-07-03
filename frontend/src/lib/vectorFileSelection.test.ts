import { describe, expect, it } from "vitest";
import {
  VECTOR_FILE_INPUT_ACCEPT,
  formatVectorFileSize,
  mapVectorFilePickToProductSpec,
  validateVectorFileSelection,
} from "./vectorFileSelection";
import { normalizeVolumetricIntakeSpecForSave } from "./intakeVolumetricSpec";

describe("vectorFileSelection", () => {
  it("accept attribute includes svg extension and MIME", () => {
    expect(VECTOR_FILE_INPUT_ACCEPT).toContain(".svg");
    expect(VECTOR_FILE_INPUT_ACCEPT).toContain("image/svg+xml");
  });

  it("accepts SVG with empty MIME via extension", () => {
    const file = new File(["<svg></svg>"], "litere.svg", { type: "" });
    const result = validateVectorFileSelection(file);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.metadata.fileName).toBe("litere.svg");
      expect(result.metadata.extension).toBe("svg");
      expect(result.metadata.fileType).toBe("svg");
    }
  });

  it("accepts SVG with image/svg+xml MIME", () => {
    const file = new File(["<svg></svg>"], "logo.svg", { type: "image/svg+xml" });
    expect(validateVectorFileSelection(file).ok).toBe(true);
  });

  it("rejects unsupported extension", () => {
    const file = new File(["data"], "photo.jpg", { type: "image/jpeg" });
    const result = validateVectorFileSelection(file);
    expect(result.ok).toBe(false);
    if (result.ok === false) {
      expect(result.error).toMatch(/neacceptat/i);
    }
  });

  it("maps pick metadata to product_spec_json", () => {
    const spec = mapVectorFilePickToProductSpec(
      {},
      {
        fileName: "litere_test.svg",
        extension: "svg",
        mime: "image/svg+xml",
        sizeBytes: 2048,
        fileType: "svg",
        selectedAt: "2026-06-07T10:00:00.000Z",
      }
    );
    expect(spec).toMatchObject({
      vector_file_name: "litere_test.svg",
      vector_file_present: true,
      vector_file_type: "svg",
      vector_file_mime: "image/svg+xml",
      vector_file_size_bytes: 2048,
      vector_file_extension: "svg",
      vector_file_source: "local_manual",
      vector_analysis_status: "attached_unanalyzed",
      intake_input_pathway: "vector",
    });
    expect(spec.letter_face_area_m2).toBeUndefined();
  });

  it("persists vector file metadata on save normalize", () => {
    expect(
      normalizeVolumetricIntakeSpecForSave({
        vector_file_name: "a.svg",
        vector_file_present: true,
        vector_file_type: "svg",
        vector_file_mime: "image/svg+xml",
        vector_file_size_bytes: 512,
        vector_file_extension: "svg",
        vector_file_source: "local_manual",
        vector_file_selected_at: "2026-06-07T10:00:00.000Z",
      })
    ).toMatchObject({
      vector_file_name: "a.svg",
      vector_file_present: true,
      vector_file_type: "svg",
      vector_file_mime: "image/svg+xml",
      vector_file_size_bytes: 512,
      vector_file_extension: "svg",
      vector_file_source: "local_manual",
    });
  });

  it("formats file size", () => {
    expect(formatVectorFileSize(500)).toBe("500 B");
    expect(formatVectorFileSize(2048)).toBe("2.0 KB");
  });
});
