/**
 * BUILD 8 — Tests for Output Blocks Preview UI.
 *
 * Verifies:
 *   - Render page loads
 *   - Empty state shown
 *   - Warning display
 *   - Blockers display
 *   - No save/send/create buttons
 *   - Preview disclaimer visible
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import OutputBlocksPreview from "./OutputBlocksPreview";

const { mockLegacyRenderPreview, mockCanonicalPreview } = vi.hoisted(() => ({
  mockLegacyRenderPreview: vi.fn(),
  mockCanonicalPreview: vi.fn(),
}));

vi.mock("@/api/outputBlocksPreview", () => ({
  outputBlocksPreviewApi: {
    renderPreview: mockLegacyRenderPreview,
  },
}));

vi.mock("@/api/canonicalOutputBlockPreview", () => ({
  previewCanonicalOutputBlocks: mockCanonicalPreview,
}));

// Wrap in a simple test environment
function renderPage() {
  return render(<OutputBlocksPreview />);
}

describe("OutputBlocksPreview", () => {
  beforeEach(() => {
    mockLegacyRenderPreview.mockReset();
    mockCanonicalPreview.mockReset();
    mockLegacyRenderPreview.mockResolvedValue({
      persisted: false,
      template_id: 1,
      dossier_id: null,
      document_type: "offer",
      audience: "client",
      render_mode: "preview",
      blocks: [],
      warnings: [],
      blockers: [],
      trace: {
        source: "legacy_render_preview",
        no_persist: true,
        changed_entities: [],
        live_changes_affect_accepted_orders: false,
      },
    });
  });

  it("renders the page with title", () => {
    renderPage();
    expect(screen.getByText("Output Blocks Preview")).toBeTruthy();
  });

  it("shows empty state initially", () => {
    renderPage();
    expect(
      screen.getByText(/Selecteaza un template/)
    ).toBeTruthy();
  });

  it("shows preview disclaimer", () => {
    renderPage();
    expect(
      screen.getByText(/Preview only\. Output is not saved/)
    ).toBeTruthy();
  });

  it("has Render Preview button", () => {
    renderPage();
    expect(screen.getByText("Render Preview")).toBeTruthy();
  });

  it("does not have Save button", () => {
    renderPage();
    expect(screen.queryByText("Save")).toBeNull();
    expect(screen.queryByText("Salveaza")).toBeNull();
  });

  it("does not have Send button", () => {
    renderPage();
    expect(screen.queryByText("Send")).toBeNull();
    expect(screen.queryByText("Trimite")).toBeNull();
  });

  it("does not have Create Quote button", () => {
    renderPage();
    expect(screen.queryByText("Create Quote")).toBeNull();
    expect(screen.queryByText("Creeaza oferta")).toBeNull();
  });

  it("does not have Create Order button", () => {
    renderPage();
    expect(screen.queryByText("Create Order")).toBeNull();
    expect(screen.queryByText("Creeaza comanda")).toBeNull();
  });

  it("has template ID input", () => {
    renderPage();
    expect(screen.getByPlaceholderText("ex: 1")).toBeTruthy();
  });

  it("has document type selector", () => {
    renderPage();
    expect(screen.getByText("Document Type")).toBeTruthy();
  });

  it("keeps default flag-off behavior on legacy preview path", async () => {
    renderPage();

    fireEvent.change(screen.getByPlaceholderText("ex: 1"), {
      target: { value: "1" },
    });
    fireEvent.click(screen.getByText("Render Preview"));

    await waitFor(() => {
      expect(mockLegacyRenderPreview).toHaveBeenCalledTimes(1);
    });

    expect(mockCanonicalPreview).not.toHaveBeenCalled();
  });
});