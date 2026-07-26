import { describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import { TooltipProvider } from "@/components/ui/tooltip";
import LettersFaceStructureDetailPage from "./LettersFaceStructureDetailPage";
import { TPL_VOLUMETRIC_LETTERS_V2 } from "@/lib/volumetricQuoteInput";
import { LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME } from "@/lib/materials/lettersFacePlexiMaterialDisplay";
import { buildLettersVizualFataPath } from "./lettersStructureDetailRoutes";

describe("LettersFaceStructureDetailPage", () => {
  it("builds vizual-fata path under product detail", () => {
    expect(buildLettersVizualFataPath(TPL_VOLUMETRIC_LETTERS_V2)).toBe(
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}/structure/vizual-fata`,
    );
  });

  it("renders visual-first face documentation", () => {
    render(
      <TooltipProvider>
        <MemoryRouter initialEntries={[buildLettersVizualFataPath(TPL_VOLUMETRIC_LETTERS_V2)]}>
          <Routes>
            <Route
              path="/product-system/products/:templateCode/structure/vizual-fata"
              element={<LettersFaceStructureDetailPage />}
            />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("letters-face-structure-detail")).toBeInTheDocument();
    expect(screen.getByTestId("letters-face-structure-detail-hero")).toBeInTheDocument();
    expect(screen.getByTestId("letters-face-structure-detail-material")).toHaveTextContent(
      LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
    );
    expect(screen.getByTestId("letters-face-structure-detail-cnc-step-cut")).toHaveTextContent(
      /Decupare/i,
    );
    expect(screen.getByTestId("letters-face-structure-detail-cnc-step-bevel")).toHaveTextContent(
      /Canal|Șanfren/i,
    );
    expect(
      screen.getByTestId("letters-face-structure-detail-finish-options"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("letters-face-structure-detail-back")).toHaveAttribute(
      "href",
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}`,
    );
    expect(screen.getByTestId("letters-face-structure-detail-document")).toBeInTheDocument();
    expect(screen.getByTestId("letters-face-structure-detail-role")).toHaveTextContent(/Pasul 1/);
    expect(screen.getByTestId("letters-face-structure-detail-doc-material")).toHaveTextContent(
      /plexiglas 3mm PMMA - opal/i,
    );
    expect(screen.getByTestId("letters-face-structure-detail-doc-direction")).toHaveTextContent(
      /Composer/i,
    );
    expect(screen.getByTestId("letters-face-structure-detail-doc-sources")).toBeInTheDocument();
    expect(
      screen.getByTestId("letters-face-structure-detail-material-price-verify"),
    ).toHaveAttribute("href", "/inventory/pricing?code=MAT-ACP-FATA-LITERE");
    expect(
      screen.getByTestId("letters-face-structure-detail-doc-finish-price-face_oracal_8500"),
    ).toHaveAttribute("href", "/inventory/pricing?code=MAT-ORACAL-8500");
    expect(screen.queryByText(/\b20(?:[.,]0)?\s*€/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("letters-face-structure-detail-calc")).toBeInTheDocument();
    expect(
      screen.getByTestId("letters-face-structure-detail-calc-material_consumption-formula"),
    ).toHaveTextContent(/bounding|out-of-box/i);
    expect(
      screen.getByTestId("letters-face-structure-detail-calc-cnc_cutting-formula"),
    ).toHaveTextContent(/face_perimeter_length_m|contur/i);
  });
});

