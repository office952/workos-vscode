import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import VolumetricLetterPreviewDemo from "./VolumetricLetterPreviewDemo";
import { VOLUMETRIC_LETTER_PREVIEW_DEMO_SCENARIOS } from "@/lib/volumetricLetterPreview/volumetricLetterPreviewMocks";

function renderDemoPage() {
  return render(
    <MemoryRouter initialEntries={["/demo/volumetric-letter-preview"]}>
      <Routes>
        <Route path="/demo/volumetric-letter-preview" element={<VolumetricLetterPreviewDemo />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("VolumetricLetterPreviewDemo page", () => {
  it("renders isolated demo page with all mock scenarios", () => {
    renderDemoPage();
    expect(screen.getByTestId("volumetric-letter-preview-demo-page")).toBeInTheDocument();
    expect(screen.getByTestId("volumetric-letter-preview-demo-internal-label")).toHaveTextContent(
      /internal/i
    );

    for (const scenario of VOLUMETRIC_LETTER_PREVIEW_DEMO_SCENARIOS) {
      expect(
        screen.getByTestId(`volumetric-preview-demo-scenario-${scenario.id}`)
      ).toBeInTheDocument();
      expect(
        screen.getByTestId(`volumetric-preview-demo-${scenario.id}`)
      ).toBeInTheDocument();
      expect(
        screen.queryByTestId(`volumetric-preview-demo-${scenario.id}-controls`)
      ).not.toBeInTheDocument();
    }
  });

  it("applies global compact/expanded mode to all previews", () => {
    renderDemoPage();
    expect(screen.getByTestId("volumetric-preview-demo-complete-svg")).toHaveAttribute(
      "data-preview-mode",
      "expanded"
    );

    fireEvent.click(screen.getByTestId("volumetric-letter-preview-demo-global-mode-compact"));
    expect(screen.getByTestId("volumetric-preview-demo-complete-svg")).toHaveAttribute(
      "data-preview-mode",
      "compact"
    );
    expect(screen.getByTestId("volumetric-preview-demo-placeholder-svg")).toHaveAttribute(
      "data-preview-mode",
      "compact"
    );

    fireEvent.click(screen.getByTestId("volumetric-letter-preview-demo-global-mode-expanded"));
    expect(screen.getByTestId("volumetric-preview-demo-complete-svg")).toHaveAttribute(
      "data-preview-mode",
      "expanded"
    );
  });

  it("toggles global labels for all previews", () => {
    renderDemoPage();
    expect(screen.getByTestId("volumetric-preview-demo-complete-layer-legend")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("volumetric-letter-preview-demo-global-toggle-labels"));
    expect(
      screen.queryByTestId("volumetric-preview-demo-complete-layer-legend")
    ).not.toBeInTheDocument();
  });

  it("shows readiness counts from supplied config only", () => {
    renderDemoPage();
    expect(
      screen.getByTestId("volumetric-preview-demo-blocker-count-missing-return-depth")
    ).toHaveTextContent("blockers: 1");
    expect(
      screen.getByTestId("volumetric-preview-demo-warning-count-text-fallback")
    ).toHaveTextContent("warnings: 1");
    expect(
      screen.getByTestId("volumetric-preview-demo-missing-return-depth-blockers")
    ).toHaveTextContent("return_depth_mm_required");
    expect(
      screen.getByTestId("volumetric-preview-demo-text-fallback-warnings")
    ).toHaveTextContent("vector_analysis_pending");
  });
});
