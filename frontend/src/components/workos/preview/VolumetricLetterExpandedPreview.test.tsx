import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import VolumetricLetterExpandedPreview from "./VolumetricLetterExpandedPreview";
import {
  MOCK_COMPLETE_CONFIG,
  MOCK_MISSING_RETURN_DEPTH,
  MOCK_RAL_INCOMPLETE,
  MOCK_TEXT_FALLBACK,
  MOCK_VINYL_INCOMPLETE,
} from "@/lib/volumetricLetterPreview/volumetricLetterPreviewMocks";

describe("VolumetricLetterExpandedPreview", () => {
  it("renders compact mode by default with SVG preview", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} />);
    expect(screen.getByTestId("volumetric-letter-preview")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-svg")).toHaveAttribute(
      "data-preview-mode",
      "compact"
    );
    expect(screen.getByTestId("volumetric-letter-preview-geometry-source")).toHaveTextContent(
      /SVG importată/i
    );
  });

  it("switches to expanded mode and shows layer labels", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} />);
    fireEvent.click(screen.getByTestId("volumetric-letter-preview-mode-expanded"));
    expect(screen.getByTestId("volumetric-letter-preview-svg")).toHaveAttribute(
      "data-preview-mode",
      "expanded"
    );
    expect(screen.getByTestId("volumetric-letter-preview-layer-label-face")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-layer-label-led")).toBeInTheDocument();
  });

  it("shows construction layer legend from config stack", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} />);
    expect(screen.getByTestId("volumetric-letter-preview-legend-face")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-legend-vinyl")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-legend-return")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-legend-backing")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-legend-led")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-legend-wiring")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-legend-mounting")).toBeInTheDocument();
  });

  it("displays readiness blockers supplied in config", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_MISSING_RETURN_DEPTH} />);
    expect(screen.getByTestId("volumetric-letter-preview-blockers")).toBeInTheDocument();
    expect(screen.getByText("return_depth_mm_required")).toBeInTheDocument();
  });

  it("displays readiness warnings supplied in config", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_TEXT_FALLBACK} />);
    expect(screen.getByTestId("volumetric-letter-preview-warnings")).toBeInTheDocument();
    expect(screen.getByText("vector_analysis_pending")).toBeInTheDocument();
  });

  it("does not infer blockers from incomplete config when readiness is empty", () => {
    const configWithoutValidation: typeof MOCK_COMPLETE_CONFIG = {
      ...MOCK_COMPLETE_CONFIG,
      returnSide: { material: "aluminium" },
      face: { material: "plexiglas", hasVinyl: true },
      readiness: {
        isProductionReady: true,
        blockers: [],
        warnings: [],
      },
    };
    render(<VolumetricLetterExpandedPreview config={configWithoutValidation} />);
    expect(screen.queryByTestId("volumetric-letter-preview-blockers")).not.toBeInTheDocument();
    expect(screen.queryByTestId("volumetric-letter-preview-warnings")).not.toBeInTheDocument();
  });

  it("marks incomplete layers in legend without adding blockers", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_VINYL_INCOMPLETE} />);
    expect(screen.getByTestId("volumetric-letter-preview-legend-vinyl")).toHaveTextContent(
      /incomplet/i
    );
    expect(screen.getByText("face_vinyl_code_required")).toBeInTheDocument();
  });

  it("shows RAL incomplete blockers from supplied readiness only", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_RAL_INCOMPLETE} />);
    expect(screen.getByText("return_ral_code_required")).toBeInTheDocument();
    expect(screen.getByText("return_ral_name_required")).toBeInTheDocument();
  });

  it("uses estimated geometry label for text-only artwork", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_TEXT_FALLBACK} />);
    expect(screen.getByTestId("volumetric-letter-preview-geometry-source")).toHaveTextContent(
      /estimată/i
    );
    expect(screen.getByTestId("volumetric-letter-preview-svg")).toBeInTheDocument();
  });

  it("toggles labels off", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} />);
    fireEvent.click(screen.getByTestId("volumetric-letter-preview-toggle-labels"));
    expect(screen.queryByTestId("volumetric-letter-preview-layer-legend")).not.toBeInTheDocument();
  });

  it("calls onBlockerClick when blocker is clicked", () => {
    const onBlockerClick = vi.fn();
    render(
      <VolumetricLetterExpandedPreview
        config={MOCK_MISSING_RETURN_DEPTH}
        onBlockerClick={onBlockerClick}
      />
    );
    fireEvent.click(screen.getByTestId("volumetric-letter-preview-blocker-return_depth_mm_required"));
    expect(onBlockerClick).toHaveBeenCalledWith("return_depth_mm_required");
  });

  it("supports controlled mode prop", () => {
    render(
      <VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} mode="expanded" />
    );
    expect(screen.getByTestId("volumetric-letter-preview-svg")).toHaveAttribute(
      "data-preview-mode",
      "expanded"
    );
  });

  it("hides per-instance controls when hideControls is set", () => {
    render(
      <VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} hideControls />
    );
    expect(screen.queryByTestId("volumetric-letter-preview-controls")).not.toBeInTheDocument();
  });

  it("shows geometry badge on canvas", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} />);
    expect(screen.getByTestId("volumetric-letter-preview-geometry-badge")).toHaveTextContent("SVG");
  });

  it("shows LED estimate badge for text-only geometry", () => {
    render(<VolumetricLetterExpandedPreview config={MOCK_TEXT_FALLBACK} />);
    expect(screen.getByTestId("volumetric-letter-preview-led-estimate-badge")).toHaveTextContent(
      /LED estimat/i
    );
  });

  it("renders exploded connector lines between layers", () => {
    render(
      <VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} mode="expanded" />
    );
    expect(
      screen.getByTestId("volumetric-letter-preview-connector-face-vinyl")
    ).toBeInTheDocument();
  });

  it("renders isometric return shell in compact mode", () => {
    const { container } = render(
      <VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} mode="compact" />
    );
    expect(container.querySelector('[data-isometric-shell="true"]')).toBeTruthy();
  });

  it("renders split cutaway with interior/exterior regions and callouts in compact mode", () => {
    const { container } = render(
      <VolumetricLetterExpandedPreview config={MOCK_COMPLETE_CONFIG} mode="compact" />
    );
    expect(container.querySelector('[data-split-cutaway="true"]')).toBeTruthy();
    expect(container.querySelector('[data-split-region="interior"]')).toBeTruthy();
    expect(container.querySelector('[data-split-region="exterior"]')).toBeTruthy();
    expect(container.querySelector('[data-split-plane="true"]')).toBeTruthy();
    expect(screen.getByTestId("volumetric-letter-preview-compact-callouts")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-compact-callout-face")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-compact-callout-return")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-compact-callout-backing")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-compact-callout-led")).toBeInTheDocument();
  });
});
