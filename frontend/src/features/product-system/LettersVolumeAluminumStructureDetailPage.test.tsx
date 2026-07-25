import { describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import { TooltipProvider } from "@/components/ui/tooltip";
import LettersVolumeAluminumStructureDetailPage from "./LettersVolumeAluminumStructureDetailPage";
import { TPL_VOLUMETRIC_LETTERS_V2 } from "@/lib/volumetricQuoteInput";
import { LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO } from "@/lib/materials/lettersVolumeAluminumMaterialDisplay";
import { buildLettersVolumAluminiuPath } from "./lettersStructureDetailRoutes";

describe("LettersVolumeAluminumStructureDetailPage", () => {
  it("builds volum-aluminiu path under product detail", () => {
    expect(buildLettersVolumAluminiuPath(TPL_VOLUMETRIC_LETTERS_V2)).toBe(
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}/structure/volum-aluminiu`,
    );
  });

  it("renders visual-first volume documentation", () => {
    render(
      <TooltipProvider>
        <MemoryRouter initialEntries={[buildLettersVolumAluminiuPath(TPL_VOLUMETRIC_LETTERS_V2)]}>
          <Routes>
            <Route
              path="/product-system/products/:templateCode/structure/volum-aluminiu"
              element={<LettersVolumeAluminumStructureDetailPage />}
            />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>,
    );

    expect(screen.getByTestId("letters-volume-structure-detail")).toBeInTheDocument();
    expect(screen.getByTestId("letters-volume-structure-detail-hero")).toBeInTheDocument();
    expect(screen.getByTestId("letters-volume-structure-detail-material")).toHaveTextContent(
      LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO,
    );
    expect(screen.getByTestId("letters-volume-structure-detail-width-volume_alu_30")).toHaveTextContent(
      /30 mm/i,
    );
    expect(
      screen.getByTestId("letters-volume-structure-detail-process-volume_form"),
    ).toHaveTextContent(/Formare/i);
    expect(screen.getByTestId("letters-volume-structure-detail-back")).toHaveAttribute(
      "href",
      `/product-system/products/${encodeURIComponent(TPL_VOLUMETRIC_LETTERS_V2)}`,
    );
    expect(screen.getByTestId("letters-volume-structure-detail-document")).toBeInTheDocument();
    expect(screen.getByTestId("letters-volume-structure-detail-role")).toHaveTextContent(/Pasul 2/);
    expect(screen.getByTestId("letters-volume-structure-detail-doc-material")).toHaveTextContent(
      /MAT-PROFIL-LATERAL-LITERE/i,
    );
    expect(screen.getByTestId("letters-volume-structure-detail-doc-direction")).toHaveTextContent(
      /Composer/i,
    );
    expect(screen.getByTestId("letters-volume-structure-detail-doc-sources")).toBeInTheDocument();
    expect(
      screen.getByTestId("letters-volume-structure-detail-width-price-volume_alu_60"),
    ).toHaveAttribute("href", "/inventory/pricing?code=MAT-PROFIL-LATERAL-LITERE-60MM");
    expect(screen.queryByText(/\b2(?:[.,]0)?\s*€\/ml/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("letters-volume-structure-detail-calc")).toBeInTheDocument();
    expect(
      screen.getByTestId("letters-volume-structure-detail-calc-profile_consumption-formula"),
    ).toHaveTextContent(/face_perimeter_length_m|quantity_ml/i);
    expect(
      screen.getByTestId("letters-volume-structure-detail-calc-cant_finish-formula"),
    ).toHaveTextContent(/Oracal|RAL/i);
  });
});
