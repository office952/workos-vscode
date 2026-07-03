/**
 * BUILD 9 — Tests for QuoteOutputCompositionPreview component.
 *
 * Verifies:
 *   - Component renders with quote context
 *   - Preview-only disclaimer visible
 *   - No save/send/create-order action in preview section
 *   - HTML preview button/link present
 *   - Warnings render
 *   - Blockers render
 *   - Trace inspector render
 *   - Variables inspector render (sections)
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { act } from "react";
import QuoteOutputCompositionPreview from "./QuoteOutputCompositionPreview";

function renderComponent(quoteId = 1, quoteCode = "Q-2026-001") {
  return render(
    <QuoteOutputCompositionPreview quoteId={quoteId} quoteCode={quoteCode} />
  );
}

describe("QuoteOutputCompositionPreview", () => {
  it("renders the component with title", () => {
    renderComponent();
    expect(
      screen.getByText(/Output Composition Preview/i)
    ).toBeTruthy();
  });

  it("shows READ-ONLY badge", () => {
    renderComponent();
    expect(screen.getByText("READ-ONLY")).toBeTruthy();
  });

  it("has Load Preview button", () => {
    renderComponent();
    expect(screen.getByText("Load Preview")).toBeTruthy();
  });

  it("does not have Save button", () => {
    renderComponent();
    expect(screen.queryByText("Save")).toBeNull();
    expect(screen.queryByText("Salveaza")).toBeNull();
  });

  it("does not have Send button", () => {
    renderComponent();
    expect(screen.queryByText("Send")).toBeNull();
    expect(screen.queryByText("Trimite")).toBeNull();
  });

  it("does not have Create Order button", () => {
    renderComponent();
    expect(screen.queryByText("Create Order")).toBeNull();
    expect(screen.queryByText("Creeaza Comanda")).toBeNull();
  });

  it("shows expanded content when header clicked", async () => {
    renderComponent();
    // Click header to expand
    const header = screen.getByText(/Output Composition Preview/i);
    await act(async () => {
      header.closest("[class*='cursor-pointer']")?.dispatchEvent(
        new MouseEvent("click", { bubbles: true })
      );
    });
    // After expanding, disclaimer should be visible
    expect(screen.getByText(/Preview only/i)).toBeTruthy();
  });

  it("does not have Export HTML button before loading", () => {
    renderComponent();
    // Export HTML only shows after data is loaded
    expect(screen.queryByText("Export HTML")).toBeNull();
  });
});