import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Product001IntakeSpecEditor from "./Product001IntakeSpecEditor";

vi.mock("@/api/vectorAssets", () => ({
  vectorAssetsApi: {
    analyzeLayers: vi.fn().mockResolvedValue({ layers: [], preview_svg: null }),
  },
}));

function pathwayButton(id: "vector" | "manual" | "quick_estimate") {
  return screen.getByTestId(`intake-pathway-${id}`);
}

function isPathwayActive(button: HTMLElement) {
  return button.className.includes("border-blue-500/60");
}

describe("Product001IntakeSpecEditor vector fast ask", () => {
  const onSave = vi.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Vector Fast Ask when vector pathway selected", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    expect(screen.getByTestId("vector-intake-fast-ask")).toBeInTheDocument();
    expect(screen.getByTestId("intake-pathway-vector")).toBeInTheDocument();
  });

  it("does not show Vector Fast Ask on manual pathway", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "manual" }}
        onSave={onSave}
      />
    );
    expect(screen.queryByTestId("vector-intake-fast-ask")).not.toBeInTheDocument();
  });

  it("does not show Vector Fast Ask on quick estimate pathway", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "quick_estimate" }}
        onSave={onSave}
      />
    );
    expect(screen.queryByTestId("vector-intake-fast-ask")).not.toBeInTheDocument();
  });

  it("auto-persists intake_input_pathway when vector pathway card is clicked", async () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "manual", width_mm: 4800, height_mm: 600, depth_mm: 60 }}
        onSave={onSave}
      />
    );
    fireEvent.click(pathwayButton("vector"));
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          intake_input_pathway: "vector",
        }),
        { skipRefresh: true }
      );
    });
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
  });

  it("auto-persists vector file metadata when SVG is picked", async () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [
          new File(
            [
              "<svg xmlns='http://www.w3.org/2000/svg' xmlns:inkscape='http://www.inkscape.org/namespaces/inkscape' viewBox='0 0 10 10'><g inkscape:label='LITERE' inkscape:groupmode='layer'><path d='M0 0'/></g></svg>",
            ],
            "picked.svg",
            { type: "image/svg+xml" }
          ),
        ],
      },
    });
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          intake_input_pathway: "vector",
          vector_file_name: "picked.svg",
        }),
        { skipRefresh: true }
      );
    });
    expect(screen.getByTestId("vector-fast-ask-selected-file")).toHaveTextContent("picked.svg");
  });

  it("keeps vector pathway active after SVG pick when switching from manual default", async () => {
    render(<Product001IntakeSpecEditor initialSpec={{}} onSave={onSave} />);
    fireEvent.click(pathwayButton("vector"));
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);

    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [
          new File(["<svg viewBox='0 0 1 1'></svg>"], "picked.svg", {
            type: "image/svg+xml",
          }),
        ],
      },
    });

    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("picked.svg");
    });
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
    expect(isPathwayActive(pathwayButton("manual"))).toBe(false);
    expect(screen.getByTestId("vector-intake-fast-ask")).toBeInTheDocument();
  });

  it("opens vector pathway when saved spec has vector file but stale manual flag", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{
          intake_input_pathway: "manual",
          vector_file_name: "saved.svg",
        }}
        onSave={onSave}
      />
    );
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
    expect(screen.getByTestId("vector-intake-fast-ask")).toBeInTheDocument();
  });

  it("attaches SVG file metadata on file pick via onFileAttach path", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [new File(["<svg></svg>"], "picked.svg", { type: "image/svg+xml" })],
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("picked.svg");
    });
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: /Salvează specificația/i }));
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          vector_file_name: "picked.svg",
          vector_file_present: true,
          vector_file_type: "svg",
          vector_file_source: "local_manual",
          intake_input_pathway: "vector",
        })
      );
    });
  });

  it("applies fast ask and reveals depth in form", async () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [
          new File(["<svg viewBox='0 0 1 1'></svg>"], "litere_test.svg", {
            type: "image/svg+xml",
          }),
        ],
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("litere_test.svg");
    });
    fireEvent.change(screen.getByTestId("vector-fast-ask-face-wrap"), {
      target: { value: "yes" },
    });
    fireEvent.change(screen.getByTestId("vector-fast-ask-face-colantare-type"), {
      target: { value: "oracal_colored" },
    });
    fireEvent.change(screen.getByTestId("vector-fast-ask-return-edge"), {
      target: { value: "black" },
    });
    fireEvent.click(screen.getByTestId("vector-fast-ask-apply"));

    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-applied-message")).toBeInTheDocument();
    });
    expect(screen.getByTestId("vector-pathway-active-status")).toBeInTheDocument();
    expect(screen.getByText(/Flux activ: Din fișier vector/i)).toBeInTheDocument();
    expect(screen.getByText(/Verificare specificație/i)).toBeInTheDocument();
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
    expect(isPathwayActive(pathwayButton("manual"))).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: /Salvează specificația/i }));
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          depth_mm: 60,
          return_depth_mm: 60,
          vector_file_name: "litere_test.svg",
          face_wrap_enabled: true,
          face_finish_type: "oracal_651",
          return_edge_color: "black",
          volume_finish: "none",
          illumination_type: "frontlit",
        })
      );
    });
  });

  it("apply fast ask preserves second filename after two file picks", async () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [new File(["<svg viewBox='0 0 1 1'></svg>"], "first.svg", { type: "image/svg+xml" })],
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("first.svg");
    });
    fireEvent.change(input, {
      target: {
        files: [new File(["<svg viewBox='0 0 2 2'></svg>"], "second.svg", { type: "image/svg+xml" })],
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("second.svg");
    });
    fireEvent.click(screen.getByTestId("vector-fast-ask-apply"));
    fireEvent.click(screen.getByRole("button", { name: /Salvează specificația/i }));
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          vector_file_name: "second.svg",
        })
      );
    });
  });

  it("apply stores layer mapping in product_spec_json", async () => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" viewBox="0 0 10 10">
      <g inkscape:groupmode="layer" inkscape:label="LITERE" id="l1"><path d="M0 0"/></g>
      <g inkscape:groupmode="layer" inkscape:label="DIBOND" id="l2"><rect/></g>
    </svg>`;
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "layers.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-detected-layers")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("vector-fast-ask-apply"));
    fireEvent.click(screen.getByRole("button", { name: /Salvează specificația/i }));
    await waitFor(() => {
      const payload = onSave.mock.calls.at(-1)?.[0] as Record<string, unknown>;
      expect(payload.vector_file_name).toBe("layers.svg");
      expect(payload.vector_svg_analyzed).toBe(true);
      expect(Array.isArray(payload.vector_detected_layers)).toBe(true);
      expect((payload.vector_detected_layers as unknown[]).length).toBeGreaterThan(0);
      expect(payload.letter_face_area_m2).toBeUndefined();
      expect(payload.letter_perimeter_m).toBeUndefined();
    });
  });

  it("legacy smoke-like spec skips fast ask gate and shows full form", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{
          intake_input_pathway: "vector",
          vector_file_name: "TPL-VOLUMETRIC-LETTERS_vetro_litere.svg",
          depth_mm: 60,
          return_depth_mm: 60,
          return_edge_color: "white",
          letter_face_area_m2: 2.88,
          letter_perimeter_m: 18,
          letter_count: 9,
        }}
        onSave={onSave}
      />
    );
    expect(screen.getByText("Construcție litere")).toBeInTheDocument();
    expect(screen.getByTestId("vector-pathway-active-status")).toBeInTheDocument();
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
  });

  it("stale parent initialSpec sync cannot downgrade derived vector pathway before file pick", () => {
    const { rerender } = render(
      <Product001IntakeSpecEditor
        initialSpec={{
          intake_input_pathway: "manual",
          vector_file_name: "stale.svg",
          vector_svg_analyzed: true,
        }}
        onSave={onSave}
      />
    );
    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);

    rerender(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "manual" }}
        onSave={onSave}
      />
    );

    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
    expect(isPathwayActive(pathwayButton("manual"))).toBe(false);
    expect(screen.getByTestId("vector-intake-fast-ask")).toBeInTheDocument();
  });

  it("stale parent sync after vector file pick keeps pathway vector", async () => {
    const { rerender } = render(
      <Product001IntakeSpecEditor initialSpec={{ intake_input_pathway: "manual" }} onSave={onSave} />
    );
    fireEvent.click(pathwayButton("vector"));

    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [new File(["<svg viewBox='0 0 10 10'></svg>"], "lleexxaa.svg", { type: "image/svg+xml" })],
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("lleexxaa.svg");
    });

    rerender(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "manual", vector_file_name: "old.svg" }}
        onSave={onSave}
      />
    );

    expect(isPathwayActive(pathwayButton("vector"))).toBe(true);
    expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("lleexxaa.svg");
  });

  it("does not auto-apply quote-critical geometry from parser suggestions", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    const svg = `<svg width="200mm" height="100mm" viewBox="0 0 200 100">
      <g id="LITERE"><rect x="0" y="0" width="200" height="100"/></g>
    </svg>`;
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "geo.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-surface-geometry-suggestions")).toBeInTheDocument();
    });
    const widthBefore = onSave.mock.calls.find((c) => c[0]?.width_mm != null);
    expect(widthBefore).toBeUndefined();
    fireEvent.click(screen.getByTestId("vector-geometry-apply-dimensions"));
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          width_mm: 200,
          height_mm: 100,
          geometry_source: "svg_suggestion_confirmed",
        }),
        { skipRefresh: true }
      );
    });
    const saved = onSave.mock.calls.at(-1)?.[0] as Record<string, unknown>;
    expect(saved.letter_perimeter_m).toBeUndefined();
    expect(saved.letter_face_area_m2).toBeUndefined();
  });

  it("vector pathway hides duplicate Vector Studio section 9", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{
          intake_input_pathway: "vector",
          vector_file_name: "litere.svg",
          depth_mm: 60,
          return_depth_mm: 60,
        }}
        onSave={onSave}
      />
    );
    expect(screen.getByTestId("vector-intake-review-surface")).toBeInTheDocument();
    expect(screen.queryByText(/Vector Studio — fișier și readiness/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Vector Studio$/)).not.toBeInTheDocument();
  });

  it("vector pathway renders unified surface sections", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    expect(screen.getByTestId("vector-surface-file-section")).toBeInTheDocument();
    expect(screen.getByTestId("vector-surface-quick-questions-section")).toBeInTheDocument();
    expect(screen.getByTestId("vector-surface-review-section")).toBeInTheDocument();
  });

  it("vector pathway shows review notes and manual review checkbox in single surface", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{
          intake_input_pathway: "vector",
          vector_manual_review_notes: "Verificat prepress",
        }}
        onSave={onSave}
      />
    );
    expect(screen.getByTestId("vector-surface-review-notes")).toHaveValue("Verificat prepress");
    expect(screen.getByTestId("vector-surface-manual-review-checkbox")).toBeInTheDocument();
  });

  it("manual pathway shows Detalii specificație label without vector status strip", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "manual", depth_mm: 60, return_depth_mm: 60 }}
        onSave={onSave}
      />
    );
    expect(screen.getByTestId("manual-spec-detail-sections-label")).toHaveTextContent(
      "Detalii specificație"
    );
    expect(screen.queryByTestId("vector-pathway-active-status")).not.toBeInTheDocument();
  });

  it("renders E2E WARN legacy product_spec without crashing vector review summary", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{
          width_mm: 4800,
          height_mm: 600,
          depth_mm: 60,
          return_depth_mm: 60,
          letter_face_area_m2: 2.88,
          letter_perimeter_m: 18,
          letter_count: 9,
          vector_file_name: "e2e-volumetric-letters.svg",
          vector_file_type: "svg",
          vector_analysis_status: "manual_review_approved",
          vector_manual_review_approved: true,
          vector_geometry_analyzed: true,
          vector_geometry_confidence: "high",
          geometry_source: "svg_suggestion_confirmed",
          svg_layer_mappings: { Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS" },
          vector_suggested_assembly_width_mm: 4800,
        }}
        onSave={onSave}
      />
    );
    expect(screen.getByTestId("vector-intake-review-surface")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Litere volumetrice luminoase" })).toBeInTheDocument();
  });

  it("renders vector pathway with empty partial spec (no layers, no geometry)", () => {
    render(
      <Product001IntakeSpecEditor
        initialSpec={{ intake_input_pathway: "vector" }}
        onSave={onSave}
      />
    );
    expect(screen.getByTestId("vector-intake-fast-ask")).toBeInTheDocument();
    expect(screen.getByTestId("vector-intake-review-surface")).toBeInTheDocument();
  });
});
