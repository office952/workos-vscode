import { describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import { TooltipProvider } from "@/components/ui/tooltip";
import LettersLedStructureDetailPage from "./LettersLedStructureDetailPage";
import { TPL_VOLUMETRIC_LETTERS_V2 } from "@/lib/volumetricQuoteInput";
import { LETTERS_LED_FAMILY_LABEL_RO } from "@/lib/materials/lettersLedMaterialDisplay";
import { buildLettersSistemLedPath } from "./lettersStructureDetailRoutes";

describe("LettersLedStructureDetailPage", () => {
  it("builds sistem-led path under product detail", () => {
    expect(buildLettersSistemLedPath(TPL_VOLUMETRIC_LETTERS_V2)).toBe(
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}/structure/sistem-led`,
    );
  });

  it("renders visual-first LED documentation", () => {
    render(
      <TooltipProvider>
        <MemoryRouter initialEntries={[buildLettersSistemLedPath(TPL_VOLUMETRIC_LETTERS_V2)]}>
          <Routes>
            <Route
              path="/product-system/products/:templateCode/structure/sistem-led"
              element={<LettersLedStructureDetailPage />}
            />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("letters-led-structure-detail")).toBeInTheDocument();
    expect(screen.getByTestId("letters-led-structure-detail-hero")).toBeInTheDocument();
    expect(screen.getByTestId("letters-led-structure-detail-material")).toHaveTextContent(
      LETTERS_LED_FAMILY_LABEL_RO,
    );
    expect(screen.getByTestId("letters-led-structure-detail-psu-psu_100")).toHaveTextContent(
      /100 W/i,
    );
    expect(
      screen.getByTestId("letters-led-structure-detail-process-led_mount_modules"),
    ).toHaveTextContent(/Montaj/i);
    expect(screen.getByTestId("letters-led-structure-detail-back")).toHaveAttribute(
      "href",
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}`,
    );
    expect(screen.getByTestId("letters-led-structure-detail-role")).toHaveTextContent(/Pasul 4/);
    expect(
      screen.getByTestId("letters-led-structure-detail-module-price-verify"),
    ).toHaveAttribute("href", "/inventory/pricing?code=MAT-LED-MODULE");
    expect(screen.queryByText(/\b0(?:[.,]5)?\s*€\/buc/i)).not.toBeInTheDocument();
    expect(
      screen.getByTestId("letters-led-structure-detail-calc-module_count-formula"),
    ).toHaveTextContent(/250/);
    expect(
      screen.getByTestId("letters-led-structure-detail-calc-psu_selection-formula"),
    ).toHaveTextContent(/PSU|selected_psu/i);
  });
});
