import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import VectorIntakeFastAskPanel from "./VectorIntakeFastAskPanel";

describe("VectorIntakeFastAskPanel", () => {
  it("renders unified vector intake and review surface", () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    expect(screen.getByTestId("vector-intake-fast-ask")).toBeInTheDocument();
    expect(screen.getByTestId("vector-intake-review-surface")).toBeInTheDocument();
    expect(screen.getByText("Fișier vector și layere")).toBeInTheDocument();
    expect(screen.getByTestId("vector-surface-file-section")).toBeInTheDocument();
    expect(screen.getByTestId("vector-surface-quick-questions-section")).toBeInTheDocument();
    expect(screen.getByTestId("vector-surface-review-section")).toBeInTheDocument();
    expect(screen.getByTestId("vector-fast-ask-file-input")).toBeInTheDocument();
    expect(screen.getByTestId("vector-fast-ask-file-button")).toBeInTheDocument();
    expect(screen.getByTestId("vector-fast-ask-filename")).toBeInTheDocument();
    expect(screen.getByTestId("vector-fast-ask-quality-notes")).toBeInTheDocument();
    expect(screen.getByTestId("vector-fast-ask-layer-alignment")).toBeInTheDocument();
  });

  it("shows review checkbox and notes when wired", () => {
    const onManualReviewChange = vi.fn();
    render(
      <VectorIntakeFastAskPanel
        onApply={vi.fn()}
        manualReviewApproved
        manualReviewNotes="OK"
        onManualReviewChange={onManualReviewChange}
      />
    );
    expect(screen.getByTestId("vector-surface-manual-review-checkbox")).toBeChecked();
    expect(screen.getByTestId("vector-surface-review-notes")).toHaveValue("OK");
    fireEvent.change(screen.getByTestId("vector-surface-review-notes"), {
      target: { value: "Updated" },
    });
    expect(onManualReviewChange).toHaveBeenCalledWith(
      expect.objectContaining({ manualReviewNotes: "Updated" })
    );
  });

  it("file input accepts svg and image/svg+xml", () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input");
    expect(input.getAttribute("accept")).toContain(".svg");
    expect(input.getAttribute("accept")).toContain("image/svg+xml");
  });

  it("selecting SVG updates visible filename", async () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    const file = new File(["<svg></svg>"], "litere.svg", { type: "image/svg+xml" });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("litere.svg");
      expect(screen.getByTestId("vector-fast-ask-selected-file")).toHaveTextContent("litere.svg");
    });
  });

  it("accepts SVG with empty MIME via extension", async () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    const file = new File(["<svg></svg>"], "empty-mime.svg", { type: "" });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("empty-mime.svg");
      expect(screen.queryByTestId("vector-fast-ask-file-error")).not.toBeInTheDocument();
    });
  });

  it("rejects unsupported file with clear error", () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    const file = new File(["data"], "photo.jpg", { type: "image/jpeg" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.getByTestId("vector-fast-ask-file-error")).toBeInTheDocument();
  });

  it("calls onFileAttach when SVG selected", async () => {
    const onFileAttach = vi.fn();
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} onFileAttach={onFileAttach} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    const file = new File(["<svg></svg>"], "attach.svg", { type: "image/svg+xml" });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => {
      expect(onFileAttach).toHaveBeenCalledWith(
        expect.objectContaining({
          fileName: "attach.svg",
          extension: "svg",
          fileType: "svg",
        }),
        expect.anything()
      );
    });
  });

  it("disables apply until filename provided", () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    expect(screen.getByTestId("vector-fast-ask-apply")).toBeDisabled();
    fireEvent.change(screen.getByTestId("vector-fast-ask-filename"), {
      target: { value: "litere.svg" },
    });
    expect(screen.getByTestId("vector-fast-ask-apply")).not.toBeDisabled();
  });

  it("selecting second SVG replaces first filename", async () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
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
      expect(screen.getByTestId("vector-fast-ask-selected-file")).toHaveTextContent("second.svg");
    });
  });

  it("shows detected layer count for multi-layer SVG", async () => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" viewBox="0 0 10 10">
      <g inkscape:groupmode="layer" inkscape:label="LITERE" id="l1"><path d="M0 0"/></g>
      <g inkscape:groupmode="layer" inkscape:label="DIBOND" id="l2"><rect/></g>
    </svg>`;
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "layers.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-detected-layers")).toBeInTheDocument();
      expect(screen.getByTestId("vector-fast-ask-layer-count")).toHaveTextContent(/2 layere/);
    });
  });

  it("allows operator to change layer role", async () => {
    const svg = `<svg viewBox="0 0 10 10"><g id="LITERE"><path/></g></svg>`;
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "one.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-layer-role-LITERE")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("vector-fast-ask-layer-role-LITERE"), {
      target: { value: "support_panel" },
    });
    expect(screen.getByTestId("vector-fast-ask-layer-role-LITERE")).toHaveValue("support_panel");
  });

  it("shows geometry suggestions after SVG upload and layer mapping", async () => {
    const onGeometryParsed = vi.fn();
    const svg = `<svg width="200mm" height="100mm" viewBox="0 0 200 100">
      <g id="LITERE"><rect x="10" y="10" width="180" height="80"/></g>
    </svg>`;
    render(
      <VectorIntakeFastAskPanel onApply={vi.fn()} onGeometryParsed={onGeometryParsed} />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "geo.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(onGeometryParsed).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-surface-geometry-suggestions")).toBeInTheDocument();
    });
    expect(screen.getByTestId("vector-geometry-apply-dimensions")).toBeInTheDocument();
    expect(screen.getByText(/necesită confirmare/i)).toBeInTheDocument();
  });

  it("calls onApplyGeometrySuggestion only on button click", async () => {
    const onApplyGeometry = vi.fn();
    const svg = `<svg width="200mm" height="100mm" viewBox="0 0 200 100">
      <g id="LITERE"><rect x="0" y="0" width="200" height="100"/></g>
    </svg>`;
    render(
      <VectorIntakeFastAskPanel
        onApply={vi.fn()}
        onGeometryParsed={vi.fn()}
        onApplyGeometrySuggestion={onApplyGeometry}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "dims.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-geometry-apply-dimensions")).toBeInTheDocument();
    });
    expect(onApplyGeometry).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("vector-geometry-apply-dimensions"));
    expect(onApplyGeometry).toHaveBeenCalledWith("dimensions");
  });

  it("calls onApply with file metadata in answers", async () => {
    const onApply = vi.fn();
    render(<VectorIntakeFastAskPanel onApply={onApply} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [new File(["<svg></svg>"], "litere.svg", { type: "image/svg+xml" })],
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-filename")).toHaveValue("litere.svg");
    });
    fireEvent.click(screen.getByTestId("vector-fast-ask-apply"));
    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({
        vectorFileName: "litere.svg",
        vectorFileExtension: "svg",
        vectorFileMime: "image/svg+xml",
      })
    );
  });

  it("shows parse status banner after SVG selection", async () => {
    const svg = `<svg viewBox="0 0 100 50"><g id="LITERE"><rect width="80" height="40"/></g></svg>`;
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "status.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-parse-status-banner")).toBeInTheDocument();
      expect(screen.getByTestId("vector-parse-status-label")).toHaveTextContent(/succes|avertismente/i);
    });
  });

  it("shows primary letters layer section and calls onConfirmLettersLayer", async () => {
    const onConfirm = vi.fn();
    const svg = `<svg viewBox="0 0 10 10">
      <g id="LITERE"><path d="M0 0"/></g>
      <g id="CADRU"><rect/></g>
    </svg>`;
    render(
      <VectorIntakeFastAskPanel onApply={vi.fn()} onConfirmLettersLayer={onConfirm} />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "letters.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-primary-letters-layer-section")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("vector-confirm-letters-layer"));
    expect(onConfirm).toHaveBeenCalledWith(
      expect.any(Array),
      expect.stringMatching(/LITERE/i),
      expect.stringMatching(/high|medium|low/)
    );
  });

  it("shows confirmed state when mappingConfirmed", async () => {
    const svg = `<svg viewBox="0 0 10 10"><g id="LITERE"><path/></g></svg>`;
    render(
      <VectorIntakeFastAskPanel
        onApply={vi.fn()}
        mappingConfirmed
        primaryLettersLayerId="LITERE"
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([svg], "done.svg", { type: "image/svg+xml" })] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-letters-layer-confirmed")).toBeInTheDocument();
    });
  });

  it("apply button label reflects save boundary", () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    expect(screen.getByTestId("vector-fast-ask-apply")).toHaveTextContent(/salvează/i);
  });
});
