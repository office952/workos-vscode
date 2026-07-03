import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import VectorIntakeFastAskPanel from "./VectorIntakeFastAskPanel";
import { analyzeSvgVectorFile } from "@/lib/svgVectorAnalysis";

const __dirname = dirname(fileURLToPath(import.meta.url));
const FIXTURE_SVG = readFileSync(
  join(__dirname, "../../../e2e/fixtures/volumetric-multilayer.svg"),
  "utf8"
);
const LLEEXXAA_FIXTURE = readFileSync(
  join(__dirname, "../../../e2e/fixtures/lleexxaa.svg"),
  "utf8"
);

describe("VectorIntakeFastAskPanel desktop SVG parse proof", () => {
  it("parses CorelDRAW lleexxaa.svg with Litere + Structura layers", async () => {
    const onFileAttach = vi.fn();
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} onFileAttach={onFileAttach} />);
    const file = new File([LLEEXXAA_FIXTURE], "lleexxaa.svg", { type: "image/svg+xml" });
    fireEvent.change(screen.getByTestId("vector-fast-ask-file-input"), {
      target: { files: [file] },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-layer-count")).toHaveTextContent(/2 layere/);
      expect(screen.getByTestId("vector-fast-ask-layer-row-Litere_x0020_Volumetrice")).toBeInTheDocument();
    });
    expect(onFileAttach).toHaveBeenCalledWith(
      expect.objectContaining({ fileName: "lleexxaa.svg" }),
      expect.objectContaining({ parse_ok: true, layers: expect.any(Array) })
    );
  });

  it("fixture SVG text is read and parsed with 3 named layers", async () => {
    expect(FIXTURE_SVG.slice(0, 200)).toMatch(/<\?xml|<svg/i);
    const file = new File([FIXTURE_SVG], "volumetric-multilayer.svg", {
      type: "image/svg+xml",
    });
    const analysis = await analyzeSvgVectorFile(file);
    expect(analysis.parse_ok).toBe(true);
    expect(analysis.layers.length).toBe(3);
    expect(analysis.layers.some((l) => /LITERE/i.test(l.label))).toBe(true);
  });

  it("file input onChange runs parser and shows layers from repo fixture", async () => {
    const onFileAttach = vi.fn();
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} onFileAttach={onFileAttach} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    const file = new File([FIXTURE_SVG], "volumetric-multilayer.svg", {
      type: "",
    });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByTestId("vector-parse-status-label")).toHaveTextContent(/Analizat/i);
      expect(screen.getByTestId("vector-fast-ask-layer-count")).toHaveTextContent(/3 layere/);
    });

    expect(onFileAttach).toHaveBeenCalled();
    const [, analysis] = onFileAttach.mock.calls.at(-1)!;
    expect(analysis?.parse_ok).toBe(true);
    expect(analysis?.layers?.length).toBe(3);
    expect(
      analysis?.layers?.some(
        (l: { confirmed_role: string }) => l.confirmed_role === "volumetric_letters"
      )
    ).toBe(true);
    expect(screen.getByTestId("vector-primary-letters-layer-section")).toBeInTheDocument();
  });

  it("typing filename only does not pretend SVG was parsed", async () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    fireEvent.change(screen.getByTestId("vector-fast-ask-filename"), {
      target: { value: "desktop-only.svg" },
    });
    expect(screen.getByTestId("vector-filename-only-hint")).toBeInTheDocument();
    expect(screen.queryByTestId("vector-fast-ask-detected-layers")).not.toBeInTheDocument();
    expect(screen.queryByTestId("vector-fast-ask-layer-count")).not.toBeInTheDocument();
  });

  it("shows parse error for invalid SVG content", async () => {
    render(<VectorIntakeFastAskPanel onApply={vi.fn()} />);
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [new File(["not svg at all"], "bad.svg", { type: "image/svg+xml" })],
      },
    });
    await waitFor(() => {
      const banner = screen.getByTestId("vector-parse-status-label");
      const err = screen.queryByTestId("vector-fast-ask-analysis-error");
      expect(
        banner.textContent?.match(/eșuat|failed/i) || err?.textContent?.length
      ).toBeTruthy();
    });
  });

  it("hides stale nemapat warning when local parse mapped letters layer", async () => {
    render(
      <VectorIntakeFastAskPanel
        onApply={vi.fn()}
        reviewSummary={{
          analysisStatusLabel: "Analizat",
          warnings: ["Layer principal litere nemapat.", "Nu s-au extras metrici geometrice automat."],
          savedMappingsCount: 0,
          savedMappingsList: [],
        }}
      />
    );
    const input = screen.getByTestId("vector-fast-ask-file-input") as HTMLInputElement;
    fireEvent.change(input, {
      target: {
        files: [new File([FIXTURE_SVG], "volumetric-multilayer.svg", { type: "image/svg+xml" })],
      },
    });
    await waitFor(() => {
      expect(screen.getByTestId("vector-fast-ask-layer-count")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.queryByText("Layer principal litere nemapat.")).not.toBeInTheDocument();
    });
  });
});
