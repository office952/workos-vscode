import { describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import { TooltipProvider } from "@/components/ui/tooltip";
import LettersBackForexStructureDetailPage from "./LettersBackForexStructureDetailPage";
import { TPL_VOLUMETRIC_LETTERS_V2 } from "@/lib/volumetricQuoteInput";
import { LETTERS_BACK_FOREX_10MM_DISPLAY_NAME } from "@/lib/materials/lettersBackForexMaterialDisplay";
import { buildLettersCapacSpatePath } from "./lettersStructureDetailRoutes";

describe("LettersBackForexStructureDetailPage", () => {
  it("builds capac-spate path under product detail", () => {
    expect(buildLettersCapacSpatePath(TPL_VOLUMETRIC_LETTERS_V2)).toBe(
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}/structure/capac-spate`,
    );
  });

  it("renders visual-first back documentation", () => {
    render(
      <TooltipProvider>
        <MemoryRouter initialEntries={[buildLettersCapacSpatePath(TPL_VOLUMETRIC_LETTERS_V2)]}>
          <Routes>
            <Route
              path="/product-system/products/:templateCode/structure/capac-spate"
              element={<LettersBackForexStructureDetailPage />}
            />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("letters-back-structure-detail")).toBeInTheDocument();
    expect(screen.getByTestId("letters-back-structure-detail-hero")).toBeInTheDocument();
    expect(screen.getByTestId("letters-back-structure-detail-material")).toHaveTextContent(
      LETTERS_BACK_FOREX_10MM_DISPLAY_NAME,
    );
    expect(
      screen.getByTestId("letters-back-structure-detail-cnc-step-back_cnc_cut"),
    ).toHaveTextContent(/Debitare/i);
    expect(
      screen.getByTestId("letters-back-structure-detail-cnc-step-back_cnc_bevel"),
    ).toHaveTextContent(/Șanfren|opțional/i);
    expect(screen.getByTestId("letters-back-structure-detail-back")).toHaveAttribute(
      "href",
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}`,
    );
    expect(screen.getByTestId("letters-back-structure-detail-document")).toBeInTheDocument();
    expect(screen.getByTestId("letters-back-structure-detail-role")).toHaveTextContent(/Pasul 3/);
    expect(screen.getByTestId("letters-back-structure-detail-doc-material")).toHaveTextContent(
      /Forex 10 mm/i,
    );
    expect(
      screen.getByTestId("letters-back-structure-detail-material-price-verify"),
    ).toHaveAttribute("href", "/inventory/pricing?code=MAT-SPATE-PVC-LITERE");
    expect(screen.queryByText(/\b16(?:[.,]0)?\s*€/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("letters-back-structure-detail-calc")).toBeInTheDocument();
    expect(
      screen.getByTestId("letters-back-structure-detail-calc-material_consumption-formula"),
    ).toHaveTextContent(/backing_area|mp/i);
    expect(
      screen.getByTestId("letters-back-structure-detail-calc-cnc_cutting-formula"),
    ).toHaveTextContent(/perimeter|pass_count/i);
  });
});
