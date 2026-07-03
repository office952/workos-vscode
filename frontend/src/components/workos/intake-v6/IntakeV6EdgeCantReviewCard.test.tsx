import { cleanup, fireEvent, render, screen } from "@testing-library/react";

import { afterEach, describe, expect, it } from "vitest";

import IntakeV6EdgeCantReviewCard from "./IntakeV6EdgeCantReviewCard";

import type {
  IntakeV6EdgeCantLayerBreakdown,
  IntakeV6EdgeCantViewModel,
} from "@/lib/intakeV6/intakeV6EdgeCantDisplay";

const modelWithPrice: IntakeV6EdgeCantViewModel = {
  finishLabel: "Alb",
  cantMaterialLabel: "Aluminiu cant / volum",
  returnDepthMm: 60,
  cantPriceLabel: "12.50 EUR/ml",
  cantUnitPrice: 12.5,
  cantEstimatedCost: 334.38,
  cantPricingMissing: false,
  cantCurrency: "EUR",
  calculatedCantM: 15.4672,
  pricedCantM: 18.5606,
  wastePercent: 20,
  adhesiveMl: 27.2422,
  oracal651: {
    present: false,
    areaM2: null,
    unitPrice: null,
    estimatedCost: null,
    currency: "EUR",
    priceSource: null,
    pricingMissing: true,
    basisNote: null,
  },
  operations: [],
  hasEdgeCantData: true,
};

const modelMissingPrice: IntakeV6EdgeCantViewModel = {
  ...modelWithPrice,
  cantPriceLabel: "tarif lipsă",
  cantUnitPrice: null,
  cantEstimatedCost: null,
  cantPricingMissing: true,
};

const layerBreakdown: IntakeV6EdgeCantLayerBreakdown = {
  layers: [
    { key: "maria", label: "pseudo maria", perimeterM: 8.12, cantActive: true, scope: "letters", finishLabel: "Alb", depthMm: 60 },
    { key: "ana", label: "pseudo ana", perimeterM: 6.5, cantActive: true, scope: "letters", finishLabel: "Alb", depthMm: 60 },
    { key: "logo-stanga", label: "Emblemă stânga", perimeterM: 2.45, cantActive: true, scope: "artwork", finishLabel: "Alb", depthMm: 60 },
  ],
  groups: [
    {
      key: "letters|60|Alb",
      label: "Alb",
      scope: "letters",
      perimeterM: 14.62,
      finishLabel: "Alb",
      depthMm: 60,
      layerCount: 2,
    },
    {
      key: "artwork|60|Alb",
      label: "Alb",
      scope: "artwork",
      perimeterM: 2.45,
      finishLabel: "Alb",
      depthMm: 60,
      layerCount: 1,
    },
  ],
  totalLettersM: 14.62,
  totalEmblemM: 2.45,
  totalCantM: 17.07,
};

afterEach(() => cleanup());

describe("IntakeV6EdgeCantReviewCard", () => {
  it("shows operator cant perimeter, finish, depth, and cost formula on main card", () => {
    render(<IntakeV6EdgeCantReviewCard model={modelWithPrice} operatorCantPerimeterM={20.8795} />);

    expect(screen.getByTestId("intake-v6-edge-cant-review-card")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-edge-cant-operator-perimeter")).toHaveTextContent("20.88 m");
    expect(screen.getByTestId("intake-v6-edge-cant-finish")).toHaveTextContent("Alb");
    expect(screen.getByTestId("intake-v6-edge-cant-depth")).toHaveTextContent("60 mm");
    expect(screen.getByTestId("intake-v6-edge-cant-price")).toHaveTextContent("12.50 EUR/ml");
    expect(screen.getByTestId("intake-v6-edge-cant-cost-formula")).toHaveTextContent(
      "20.88 m × 12.50 EUR/ml = 260.99 EUR",
    );
  });

  it("shows missing tariff and unavailable cost when unit price is absent", () => {
    render(<IntakeV6EdgeCantReviewCard model={modelMissingPrice} operatorCantPerimeterM={20.8795} />);

    expect(screen.getByTestId("intake-v6-edge-cant-price")).toHaveTextContent("tarif lipsă");
    expect(screen.getByTestId("intake-v6-edge-cant-cost-formula")).toHaveTextContent(
      "indisponibil — tarif lipsă",
    );
  });

  it("keeps Detalii cant collapsed by default and hides debug rows from main card", () => {
    render(
      <IntakeV6EdgeCantReviewCard
        model={modelWithPrice}
        operatorCantPerimeterM={20.8795}
        cantPerimeterDisplay={{
          displayM: 20.8795,
          letterVectorPerimeterM: 26.747,
          artworkVectorPerimeterM: null,
          quoteGeometryCantM: 20.8795,
          ledExteriorPerimeterM: 20.8795,
          fullVectorPerimeterM: 31.638,
        }}
        layerBreakdown={layerBreakdown}
      />,
    );

    expect(screen.queryByTestId("intake-v6-edge-cant-technical-details-content")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-edge-cant-led-outer")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-edge-cant-priced")).not.toBeInTheDocument();
    expect(screen.queryByText(/\+20%/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Pierdere ofertare/)).not.toBeInTheDocument();
  });

  it("shows grouped and per-layer breakdown with debug rows when Detalii cant is expanded", () => {
    render(
      <IntakeV6EdgeCantReviewCard
        model={modelWithPrice}
        operatorCantPerimeterM={20.8795}
        cantPerimeterDisplay={{
          displayM: 20.8795,
          letterVectorPerimeterM: 26.747,
          artworkVectorPerimeterM: null,
          quoteGeometryCantM: 20.8795,
          ledExteriorPerimeterM: 20.8795,
          fullVectorPerimeterM: 31.638,
        }}
        layerBreakdown={layerBreakdown}
      />,
    );

    expect(screen.getByTestId("intake-v6-edge-cant-finish")).toHaveTextContent("Litere 60 mm · Alb: 17.88 m");
    expect(screen.getByTestId("intake-v6-edge-cant-finish")).toHaveTextContent("Emblemă 60 mm · Alb: 3.00 m");
    expect(screen.getByTestId("intake-v6-edge-cant-depth")).toHaveTextContent("60 mm: 20.88 m");

    fireEvent.click(screen.getByTestId("intake-v6-edge-cant-technical-details-toggle"));

    expect(screen.getByTestId("intake-v6-edge-cant-layer-breakdown")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-edge-cant-layer-maria")).toHaveTextContent("8.12 m");
    expect(screen.getByTestId("intake-v6-edge-cant-layer-logo-stanga")).toHaveTextContent("2.45 m");
    expect(screen.getByTestId("intake-v6-edge-cant-total-letters")).toHaveTextContent("14.62 m");
    expect(screen.getByTestId("intake-v6-edge-cant-total-emblem")).toHaveTextContent("2.45 m");
    expect(screen.getByTestId("intake-v6-edge-cant-total-cant")).toHaveTextContent("17.07 m");
    expect(screen.getByTestId("intake-v6-edge-cant-raw-group-total")).toHaveTextContent("17.07 m");
    expect(screen.getByTestId("intake-v6-edge-cant-normalized-group-total")).toHaveTextContent("20.88 m");
    expect(screen.getByTestId("intake-v6-edge-cant-led-outer")).toHaveTextContent("20.88 m");
    expect(screen.getByTestId("intake-v6-edge-cant-quote-geometry")).toHaveTextContent("20.88 m");
    expect(screen.getByTestId("intake-v6-edge-cant-priced")).toHaveTextContent("18.56 m");
  });

  it("uses canonical quote geometry as main perimeter and keeps layer vector in details", () => {
    render(
      <IntakeV6EdgeCantReviewCard
        model={modelWithPrice}
        operatorCantPerimeterM={20.8795}
        cantPerimeterDisplay={{
          displayM: 20.8795,
          letterVectorPerimeterM: 26.747,
          artworkVectorPerimeterM: null,
          quoteGeometryCantM: 20.8795,
          ledExteriorPerimeterM: 20.8795,
          fullVectorPerimeterM: 31.638,
        }}
        layerBreakdown={layerBreakdown}
      />,
    );

    const mainPerimeter = screen.getByTestId("intake-v6-edge-cant-operator-perimeter");

    expect(mainPerimeter).toHaveTextContent("20.88 m");
    expect(mainPerimeter).not.toHaveTextContent("26.75");
    expect(mainPerimeter).not.toHaveTextContent("31.64");
  });
});