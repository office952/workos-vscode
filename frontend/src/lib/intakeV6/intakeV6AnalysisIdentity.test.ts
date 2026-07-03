import { describe, expect, it } from "vitest";

import {
  getPersistedFileHash,
  hasUnsavedAnalysis,
  resolveHydratedFileHashSync,
} from "./intakeV6AnalysisIdentity";
import { initialIntakeV6WorkspaceState } from "./intakeV6WorkspaceReducer";

describe("resolveHydratedFileHashSync", () => {
  it("hydrates local hash from persisted svg_source.file_hash on fresh reload", () => {
    const result = resolveHydratedFileHashSync({
      persistedFileHash: "persisted-abc",
      previousLocalFileHash: null,
      previousUnsavedAnalysis: false,
    });
    expect(result.localFileHash).toBe("persisted-abc");
    expect(result.unsavedAnalysis).toBe(false);
  });

  it("keeps unsaved when local hash differs from persisted (new file selected)", () => {
    const result = resolveHydratedFileHashSync({
      persistedFileHash: "persisted-abc",
      previousLocalFileHash: "local-new-xyz",
      previousUnsavedAnalysis: true,
    });
    expect(result.localFileHash).toBe("local-new-xyz");
    expect(result.unsavedAnalysis).toBe(true);
  });

  it("marks unsaved when no persisted hash but local hash exists", () => {
    const result = resolveHydratedFileHashSync({
      persistedFileHash: null,
      previousLocalFileHash: "local-only",
      previousUnsavedAnalysis: false,
    });
    expect(result.localFileHash).toBe("local-only");
    expect(result.unsavedAnalysis).toBe(true);
  });
});

describe("getPersistedFileHash", () => {
  it("reads svg_source.file_hash only, not analysis_content_hash", () => {
    const hash = getPersistedFileHash({
      svg_source: { file_hash: "source-file-hash" },
      svg_analysis_json: {
        analysis_content_hash: "sanitized-hash",
        source_content_hash: "source-file-hash",
      },
    });
    expect(hash).toBe("source-file-hash");
  });
});

describe("hasUnsavedAnalysis after hydrate", () => {
  it("is false when persisted hash was hydrated into localFileHash", () => {
    const state = {
      ...initialIntakeV6WorkspaceState,
      analyzerStatus: "ready" as const,
      localFileHash: "persisted-abc",
      unsavedAnalysis: false,
      workspace: {
        id: "ws-1",
        workspace_code: "IV6-1",
        title: "Test",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "draft",
        payload: {
          svg_source: { file_hash: "persisted-abc", upload_status: "analyzed" },
          svg_analysis_json: { layers: [] },
        },
      },
    };
    expect(hasUnsavedAnalysis(state)).toBe(false);
  });

  it("is true when local hash differs from persisted source file hash", () => {
    const state = {
      ...initialIntakeV6WorkspaceState,
      analyzerStatus: "ready" as const,
      localFileHash: "local-new",
      unsavedAnalysis: true,
      workspace: {
        id: "ws-1",
        workspace_code: "IV6-1",
        title: "Test",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "draft",
        payload: {
          svg_source: { file_hash: "persisted-abc", upload_status: "analyzed" },
          svg_analysis_json: { layers: [] },
        },
      },
    };
    expect(hasUnsavedAnalysis(state)).toBe(true);
  });
});