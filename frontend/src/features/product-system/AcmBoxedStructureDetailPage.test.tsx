import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import AcmBoxedStructureDetailPage from "./AcmBoxedStructureDetailPage";
import { ACM_BOXED_MOUNTING_TEMPLATE_CODE } from "./acmBoxedTemplateIdentity";

function renderStep(stepId: string) {
  return render(
    <MemoryRouter
      initialEntries={[
        `/product-system/products/${encodeURIComponent(ACM_BOXED_MOUNTING_TEMPLATE_CODE)}/structure/${stepId}`,
      ]}
    >
      <Routes>
        <Route
          path="/product-system/products/:templateCode/structure/:stepId"
          element={<AcmBoxedStructureDetailPage />}
        />
        <Route path="/product-system/products" element={<div>products</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AcmBoxedStructureDetailPage", () => {
  it("renders Corp casetat with obtain + calc + finishes", () => {
    renderStep("corp-casetat");
    expect(screen.getByTestId("acm-boxed-structure-detail")).toBeInTheDocument();
    expect(screen.getByTestId("acm-boxed-structure-detail-task-order")).toBeInTheDocument();
    expect(screen.getByTestId("acm-boxed-structure-detail-calc")).toBeInTheDocument();
    expect(screen.getByTestId("acm-boxed-structure-detail-hero")).toHaveTextContent(/Corp casetat/i);
    expect(screen.getByText(/pas 1 \/ 2/i)).toBeInTheDocument();
    expect(screen.getByTestId("acm-boxed-structure-detail-document")).toHaveTextContent(
      /Finisaj față|Oracal 651|Strategie folie/i,
    );
    expect(screen.getByTestId("acm-boxed-structure-detail-calc-finish-foil")).toBeInTheDocument();
  });

  it("renders Structură metalică with frame formula and colant order", () => {
    renderStep("structura-metalica");
    expect(screen.getByTestId("acm-boxed-structure-detail-hero")).toHaveTextContent(
      /Structură metalică/i,
    );
    expect(screen.getByTestId("acm-boxed-structure-detail-calc")).toHaveTextContent(
      /panel|2×t|2 mm/i,
    );
    expect(screen.getByTestId("acm-boxed-structure-detail-calc-colant-order")).toBeInTheDocument();
  });

  it("redirects legacy 3-step URLs into Corp casetat", () => {
    renderStep("fata-panou");
    expect(screen.getByTestId("acm-boxed-structure-detail-hero")).toHaveTextContent(/Corp casetat/i);
  });
});
