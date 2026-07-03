import { describe, expect, it } from "vitest";

import {
  initialIntakeV6WorkspaceState,
  intakeV6WorkspaceReducer,
  layerChipsFromWorkspacePayload,
} from "./intakeV6WorkspaceReducer";

describe("intakeV6WorkspaceReducer", () => {
  it("clears layer chips on analyzer start", () => {
    const withLayers = {
      ...initialIntakeV6WorkspaceState,
      layerChips: [{ layerKey: "Publi", displayName: "Publi", status: "confirmed" as const }],
      svg: { fileName: "old.svg", fileSizeBytes: 100, previewSource: "<svg/>" },
    };
    const next = intakeV6WorkspaceReducer(withLayers, {
      type: "ANALYZER_START",
      runId: 1,
      fileName: "pbl-complex.svg",
      fileSizeBytes: 50000,
    });
    expect(next.layerChips).toEqual([]);
    expect(next.svg?.fileName).toBe("pbl-complex.svg");
    expect(next.svg?.previewSource).toBeNull();
    expect(next.phase).toBe("analyzing_svg");
    expect(next.analyzerStatus).toBe("analyzing");
  });

  it("ignores stale analyzer ready when run id mismatches", () => {
    const analyzing = intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
      type: "ANALYZER_START",
      runId: 2,
      fileName: "new.svg",
      fileSizeBytes: 1,
    });
    const stale = intakeV6WorkspaceReducer(analyzing, {
      type: "ANALYZER_READY",
      runId: 1,
      fileName: "old.svg",
      fileSizeBytes: 1,
      svgSource: "<svg/>",
      previewSource: "<svg/>",
      localFileHash: "deadbeef",
      report: { layers: [], document: { widthMm: 1, heightMm: 1 }, errors: [] } as never,
      layerRoleConfirmation: { schemaVersion: "layer_role_confirmation_v1", confirmationStatus: "missing", layers: [] },
      layerChips: [{ layerKey: "a", displayName: "A", status: "pending" }],
    });
    expect(stale.layerChips).toEqual([]);
    expect(stale.analyzerStatus).toBe("analyzing");
  });
});

describe("intakeV6WorkspaceReducer load during upload", () => {
  it("clears stale workspace state when a new route key starts loading", () => {
    const previous = {
      ...initialIntakeV6WorkspaceState,
      workspaceId: "IR-OLD",
      phase: "svg_ready" as const,
      currentStep: "confirm" as const,
      workspace: {
        id: "old-workspace-id",
        workspace_code: "IV6-OLD",
        title: "Old",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "ready_for_quote_preview" as const,
        payload: { intake_request_code: "IR-OLD" },
      },
      svg: { fileName: "old.svg", fileSizeBytes: 100, previewSource: "<svg/>" },
      analyzerStatus: "ready" as const,
      svgSource: "<svg/>",
      unsavedAnalysis: false,
    };

    const next = intakeV6WorkspaceReducer(previous, {
      type: "LOAD_START",
      workspaceId: "IR-NEW",
    });

    expect(next.workspaceId).toBe("IR-NEW");
    expect(next.phase).toBe("loading");
    expect(next.workspace).toBeNull();
    expect(next.svg).toBeNull();
    expect(next.analyzerStatus).toBe("idle");
    expect(next.currentStep).toBe("layers");
  });

  it("keeps current workspace state when the same route key starts loading", () => {
    const current = {
      ...initialIntakeV6WorkspaceState,
      workspaceId: "IR-CURRENT",
      phase: "svg_ready" as const,
      workspace: {
        id: "current-workspace-id",
        workspace_code: "IV6-CURRENT",
        title: "Current",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "collecting_data" as const,
        payload: { intake_request_code: "IR-CURRENT" },
      },
    };

    const next = intakeV6WorkspaceReducer(current, {
      type: "LOAD_START",
      workspaceId: "IR-CURRENT",
    });

    expect(next.workspace?.id).toBe("current-workspace-id");
    expect(next.phase).toBe("loading");
    expect(next.error).toBeNull();
  });

  it("stores loader error classification separately from the visible message", () => {
    const next = intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
      type: "LOAD_ERROR",
      code: "WORKSPACE_NOT_FOUND",
      message: "Workspace V6 inexistent sau stale.",
    });

    expect(next.phase).toBe("error");
    expect(next.error).toBe("Workspace V6 inexistent sau stale.");
    expect(next.loadErrorCode).toBe("WORKSPACE_NOT_FOUND");
  });

  it("does not wipe svg state when LOAD_SUCCESS arrives during analyzing_svg", () => {
    const analyzing = intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
      type: "ANALYZER_START",
      runId: 1,
      fileName: "pbl-complex.svg",
      fileSizeBytes: 31000,
    });
    const reloaded = intakeV6WorkspaceReducer(analyzing, {
      type: "LOAD_SUCCESS",
      workspace: {
        id: "ws-1",
        workspace_code: "IV6-TEST",
        title: "Test",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "draft",
        payload: {},
      },
    });
    expect(reloaded.phase).toBe("analyzing_svg");
    expect(reloaded.svg?.fileName).toBe("pbl-complex.svg");
  });

  it("preserves local analyzer result when LOAD_SUCCESS has no persisted analysis yet", () => {
    const ready = intakeV6WorkspaceReducer(
      intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
        type: "ANALYZER_START",
        runId: 2,
        fileName: "local.svg",
        fileSizeBytes: 777,
      }),
      {
        type: "ANALYZER_READY",
        runId: 2,
        fileName: "local.svg",
        fileSizeBytes: 777,
        svgSource: "<svg/>",
        previewSource: "<svg/>",
        localFileHash: "local-hash",
        report: { layers: [], document: { widthMm: 1, heightMm: 1 }, errors: [] } as never,
        layerRoleConfirmation: {
          schemaVersion: "layer_role_confirmation_v1",
          confirmationStatus: "missing",
          layers: [],
        },
        layerChips: [],
      },
    );

    const refreshed = intakeV6WorkspaceReducer(ready, {
      type: "LOAD_SUCCESS",
      workspace: {
        id: "ws-2",
        workspace_code: "IV6-TEST",
        title: "Test",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "draft",
        payload: {},
      },
    });

    expect(refreshed.phase).toBe("svg_ready");
    expect(refreshed.analyzerStatus).toBe("ready");
    expect(refreshed.svg?.fileName).toBe("local.svg");
    expect(refreshed.svg?.previewSource).toBe("<svg/>");
    expect(refreshed.workspace?.id).toBe("ws-2");
  });

  it("hydrates analyzer state and resumes review step from persisted payload", () => {
    const hydrated = intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
      type: "LOAD_SUCCESS",
      workspace: {
        id: "ws-3",
        workspace_code: "IV6-HYDRATE",
        title: "Hydrate",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "collecting_data",
        readiness_status: "finish_setup_incomplete",
        payload: {
          svg_source: { file_name: "pbl.svg", file_size_bytes: 1000, upload_status: "analyzed" },
          svg_source_text: "<svg/>",
          svg_analysis_json: {
            layerRoleConfirmation: {
              schemaVersion: "layer_role_confirmation_v1",
              confirmationStatus: "complete",
              layers: [
                {
                  layerKey: "logo",
                  layerId: "logo",
                  layerName: "logo",
                  autoRole: "face",
                  autoConfidence: "high",
                  autoRoleCandidates: [],
                  confirmedRole: "face",
                  confirmationState: "confirmed",
                  operatorNote: null,
                  paintEvidence: {
                    fills: [],
                    strokes: [],
                    gradientRefs: [],
                    hasGradient: false,
                    hasPattern: false,
                    hasImage: false,
                    isMulticolor: false,
                    fillCount: 0,
                    textElementCount: 0,
                    paintKind: "none",
                  },
                  productionHint: "none",
                },
              ],
            },
            layers: [],
          },
          layer_role_setup: {
            confirmation_status: "complete",
            layers: [
              {
                layer_key: "logo",
                confirmed_role: "face",
                confirmation_state: "confirmed",
                auto_role: "face",
                auto_confidence: "high",
              },
            ],
            warnings: [],
          },
        },
      },
    });

    expect(hydrated.currentStep).toBe("review");
    expect(hydrated.analyzerStatus).toBe("ready");
    expect(hydrated.svg?.previewSource).toBe("<svg/>");
    expect(hydrated.layerRoleConfirmation?.confirmationStatus).toBe("complete");
  });

  it("hydrates localFileHash from persisted svg_source.file_hash on reload (QA-BUG-1)", () => {
    const reloaded = intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
      type: "LOAD_SUCCESS",
      workspace: {
        id: "ws-hash",
        workspace_code: "IV6-HASH",
        title: "Hash hydrate",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "collecting_data",
        readiness_status: "ready_for_quote_preview",
        payload: {
          svg_source: {
            file_name: "sample.svg",
            file_size_bytes: 500,
            file_hash: "persisted-source-hash",
            upload_status: "analyzed",
          },
          svg_source_text: "<svg/>",
          svg_analysis_json: {
            layers: [],
            document: { widthMm: 100, heightMm: 50 },
            errors: [],
            analysis_content_hash: "sanitized-different-hash",
            source_content_hash: "persisted-source-hash",
          },
          layer_role_setup: { confirmation_status: "complete", layers: [] },
          finish_setup: { confirmed: true },
        },
      },
    });

    expect(reloaded.localFileHash).toBe("persisted-source-hash");
    expect(reloaded.unsavedAnalysis).toBe(false);
  });

  it("loads ready workspaces into review instead of auto-jumping to confirm", () => {
    const reloaded = intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
      type: "LOAD_SUCCESS",
      workspace: {
        id: "ws-ready",
        workspace_code: "IV6-READY",
        title: "Ready",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "ready_for_quote_preview",
        readiness_status: "ready_for_quote_preview",
        payload: {
          svg_source: {
            file_name: "ready.svg",
            file_size_bytes: 500,
            file_hash: "ready-source-hash",
            upload_status: "analyzed",
          },
          svg_source_text: "<svg/>",
          svg_analysis_json: {
            layerRoleConfirmation: {
              schemaVersion: "layer_role_confirmation_v1",
              confirmationStatus: "complete",
              layers: [],
            },
            layers: [],
            document: { widthMm: 100, heightMm: 50 },
            errors: [],
          },
          layer_role_setup: { confirmation_status: "complete", layers: [] },
          finish_setup: { confirmed: true },
        },
      },
    });

    expect(reloaded.currentStep).toBe("review");
  });

  it("preserves unsaved when local file hash differs from persisted on reload", () => {
    const withLocal = {
      ...initialIntakeV6WorkspaceState,
      analyzerStatus: "ready" as const,
      localFileHash: "new-local-hash",
      unsavedAnalysis: true,
      svgSource: "<svg/>",
    };
    const reloaded = intakeV6WorkspaceReducer(withLocal, {
      type: "LOAD_SUCCESS",
      workspace: {
        id: "ws-mismatch",
        workspace_code: "IV6-MISMATCH",
        title: "Mismatch",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "draft",
        payload: {
          svg_source: {
            file_name: "old.svg",
            file_size_bytes: 100,
            file_hash: "persisted-old-hash",
            upload_status: "analyzed",
          },
          svg_source_text: "<svg/>",
          svg_analysis_json: {
            layers: [],
            document: { widthMm: 1, heightMm: 1 },
            errors: [],
          },
        },
      },
    });

    expect(reloaded.localFileHash).toBe("new-local-hash");
    expect(reloaded.unsavedAnalysis).toBe(true);
  });

  it("clears unsavedAnalysis after PERSIST_SUCCESS", () => {
    const analyzed = intakeV6WorkspaceReducer(initialIntakeV6WorkspaceState, {
      type: "ANALYZER_START",
      runId: 1,
      fileName: "new.svg",
      fileSizeBytes: 200,
    });
    const ready = intakeV6WorkspaceReducer(analyzed, {
      type: "ANALYZER_READY",
      runId: 1,
      fileName: "new.svg",
      fileSizeBytes: 200,
      svgSource: "<svg/>",
      previewSource: "<svg/>",
      localFileHash: "fresh-upload-hash",
      report: { layers: [], document: { widthMm: 1, heightMm: 1 }, errors: [] } as never,
      layerRoleConfirmation: {
        schemaVersion: "layer_role_confirmation_v1",
        confirmationStatus: "missing",
        layers: [],
      },
      layerChips: [],
    });
    expect(ready.unsavedAnalysis).toBe(true);

    const persisted = intakeV6WorkspaceReducer(ready, {
      type: "PERSIST_SUCCESS",
      workspace: {
        id: "ws-persist",
        workspace_code: "IV6-PERSIST",
        title: "Persisted",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "draft",
        payload: {
          svg_source: {
            file_name: "new.svg",
            file_size_bytes: 200,
            file_hash: "fresh-upload-hash",
            upload_status: "analyzed",
          },
          svg_source_text: "<svg/>",
          svg_analysis_json: {
            layers: [],
            document: { widthMm: 1, heightMm: 1 },
            errors: [],
          },
        },
      },
    });

    expect(persisted.localFileHash).toBe("fresh-upload-hash");
    expect(persisted.unsavedAnalysis).toBe(false);
  });

  it("keeps local analyzer state when finish setup save returns workspace payload", () => {
    const localAnalyzerReport = {
      layers: [],
      document: { widthMm: 10, heightMm: 5 },
      errors: [],
    } as never;
    const localConfirmation = {
      schemaVersion: "layer_role_confirmation_v1",
      confirmationStatus: "complete",
      layers: [
        {
          layerKey: "logo",
          layerId: "logo",
          layerName: "Logo",
          autoRole: "face",
          autoConfidence: "high",
          autoRoleCandidates: [],
          confirmedRole: "face",
          confirmationState: "confirmed",
          operatorNote: null,
          paintEvidence: {
            fills: [],
            strokes: [],
            gradientRefs: [],
            hasGradient: false,
            hasPattern: false,
            hasImage: false,
            isMulticolor: false,
            fillCount: 0,
            textElementCount: 0,
            paintKind: "none",
          },
          productionHint: "none",
        },
      ],
    };
    const reviewState = {
      ...initialIntakeV6WorkspaceState,
      phase: "persisting" as const,
      currentStep: "review" as const,
      analyzerStatus: "ready" as const,
      svg: { fileName: "local.svg", fileSizeBytes: 123, previewSource: "<svg>local</svg>" },
      svgSource: "<svg>local</svg>",
      analyzerReport: localAnalyzerReport,
      layerRoleConfirmation: localConfirmation,
      layerChips: [{ layerKey: "logo", displayName: "Logo", status: "confirmed" as const }],
      localFileHash: "local-hash",
      unsavedAnalysis: false,
      workspace: {
        id: "ws-review",
        workspace_code: "IV6-REVIEW",
        title: "Review",
        template_code: "TPL-VOLUMETRIC-LETTERS",
        status: "collecting_data",
        readiness_status: "finish_setup_incomplete",
        payload: {
          svg_source: {
            file_name: "local.svg",
            file_size_bytes: 123,
            file_hash: "local-hash",
            upload_status: "analyzed",
          },
          svg_source_text: "<svg>persisted-stale</svg>",
          svg_analysis_json: {
            layers: [{ id: "server" }],
            document: { widthMm: 99, heightMm: 99 },
            errors: [],
          },
          layer_role_setup: { confirmation_status: "complete", layers: [] },
        },
      },
    };

    const persisted = intakeV6WorkspaceReducer(reviewState, {
      type: "FINISH_SETUP_PERSIST_SUCCESS",
      workspace: {
        ...reviewState.workspace,
        status: "ready_for_quote_preview",
        readiness_status: "ready_for_quote_preview",
        updated_at: "2026-07-03T12:00:00Z",
        payload: {
          ...reviewState.workspace.payload,
          finish_setup: {
            face_finish_type: "oracal_8500",
            return_finish_type: "oracal_651",
            confirmed: true,
          },
        },
      },
    });

    expect(persisted.workspace?.readiness_status).toBe("ready_for_quote_preview");
    expect(persisted.workspace?.payload.finish_setup).toEqual({
      face_finish_type: "oracal_8500",
      return_finish_type: "oracal_651",
      confirmed: true,
    });
    expect(persisted.currentStep).toBe("review");
    expect(persisted.svgSource).toBe("<svg>local</svg>");
    expect(persisted.svg?.previewSource).toBe("<svg>local</svg>");
    expect(persisted.analyzerReport).toBe(localAnalyzerReport);
    expect(persisted.layerRoleConfirmation).toBe(localConfirmation);
    expect(persisted.localFileHash).toBe("local-hash");
    expect(persisted.phase).toBe("svg_ready");
  });
});

describe("layerChipsFromWorkspacePayload", () => {
  it("maps persisted layer_role_setup to chips", () => {
    const chips = layerChipsFromWorkspacePayload({
      layer_role_setup: {
        layers: [
          { layer_key: "logo", layer_name: "logo", confirmation_state: "pending" },
          { layer_key: "fundal-acm", layer_name: "fundal-acm", confirmation_state: "confirmed" },
        ],
      },
    });
    expect(chips).toHaveLength(2);
    expect(chips[0]?.layerKey).toBe("logo");
    expect(chips[1]?.status).toBe("confirmed");
  });
});