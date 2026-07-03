/**
 * BUILD 9 — Tests for OutputBlocksCoverageDiagnostics component.
 *
 * Verifies:
 *   - Component renders
 *   - Shows coverage title
 *   - No mutation buttons (no create/delete/fix)
 *   - Read-only display
 *   - Has Load button
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import OutputBlocksCoverageDiagnostics from "./OutputBlocksCoverageDiagnostics";

function renderComponent() {
  return render(<OutputBlocksCoverageDiagnostics />);
}

describe("OutputBlocksCoverageDiagnostics", () => {
  it("renders the component with title", () => {
    renderComponent();
    expect(
      screen.getByText("Output Blocks Coverage")
    ).toBeTruthy();
  });

  it("has Load button", () => {
    renderComponent();
    expect(screen.getByText("Load")).toBeTruthy();
  });

  it("does not have Create button", () => {
    renderComponent();
    expect(screen.queryByText("Create")).toBeNull();
    expect(screen.queryByText("Creeaza")).toBeNull();
  });

  it("does not have Delete button", () => {
    renderComponent();
    expect(screen.queryByText("Delete")).toBeNull();
    expect(screen.queryByText("Sterge")).toBeNull();
  });

  it("does not have Fix button", () => {
    renderComponent();
    expect(screen.queryByText("Fix")).toBeNull();
    expect(screen.queryByText("Auto-fix")).toBeNull();
  });

  it("does not have Auto-create button", () => {
    renderComponent();
    expect(screen.queryByText("Auto-create")).toBeNull();
    expect(screen.queryByText("Generate")).toBeNull();
  });
});