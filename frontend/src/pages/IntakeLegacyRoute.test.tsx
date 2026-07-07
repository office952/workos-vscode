import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import IntakeLegacyRoute from "./IntakeLegacyRoute";
function renderRoute(code: string) {
  render(
    <MemoryRouter initialEntries={[`/intake/${code}`]}>
      <Routes>
        <Route path="/intake/:id" element={<IntakeLegacyRoute />} />
        <Route
          path="/intake-v6/:workspaceId/operator"
          element={<div data-testid="intake-v6-page">V6 flow</div>}
        />
      </Routes>
    </MemoryRouter>
  );
}

describe("IntakeLegacyRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects volumetric request routes to Intake V6", () => {
    renderRoute("IR-MQ51B998");
    expect(screen.getByTestId("intake-v6-page")).toBeInTheDocument();
  });

  it("redirects non-volumetric request routes to Intake V6 and never renders the old form", () => {
    renderRoute("WI-3321");
    expect(screen.getByTestId("intake-v6-page")).toBeInTheDocument();
    expect(screen.queryByText(/Alege tip lucrare/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Tip lucrare/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Instrumentează Comanda/i)).not.toBeInTheDocument();
  });
});
