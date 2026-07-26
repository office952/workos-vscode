import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ProductSystemSpineBand } from "./ProductSystemSpineBand";
import { ProductSystemOfferCostChannels } from "./ProductSystemOfferCostChannels";
import {
  PRODUCT_SYSTEM_SPINE_STEPS,
  PRODUCT_SYSTEM_SPINE_TAGLINE,
} from "./productTemplateModulesVocabulary";

describe("ProductSystemSpineBand", () => {
  it("renders four Product System ownership steps without Oferta as a spine step", () => {
    render(<ProductSystemSpineBand />);
    expect(screen.getByTestId("product-system-spine-band")).toBeInTheDocument();
    for (const id of ["template", "structure", "compiler", "readiness"]) {
      expect(screen.getByTestId(`product-system-spine-step-${id}`)).toBeInTheDocument();
    }
    expect(screen.queryByTestId("product-system-spine-step-offer")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-spine-step-modules")).not.toBeInTheDocument();
    expect(PRODUCT_SYSTEM_SPINE_STEPS.map((s) => s.id)).toEqual([
      "template",
      "structure",
      "compiler",
      "readiness",
    ]);
    expect(PRODUCT_SYSTEM_SPINE_TAGLINE).not.toMatch(/Ofertă/i);
    expect(PRODUCT_SYSTEM_SPINE_TAGLINE).toMatch(/Product Template/);
    expect(PRODUCT_SYSTEM_SPINE_TAGLINE).toMatch(/Structură produs/);
    expect(PRODUCT_SYSTEM_SPINE_TAGLINE).toMatch(/amânat/i);
    expect(screen.getByTestId("product-system-spine-step-structure")).toHaveTextContent(
      "Structură produs",
    );
  });

  it("marks the requested step active", () => {
    render(<ProductSystemSpineBand activeStepId="structure" />);
    expect(screen.getByTestId("product-system-spine-step-structure")).toHaveAttribute(
      "data-active",
      "true",
    );
    expect(screen.getByTestId("product-system-spine-step-template")).toHaveAttribute(
      "data-active",
      "false",
    );
  });
});

describe("ProductSystemOfferCostChannels", () => {
  it("exposes Cost / Oferta / Execution as secondary link mentions, not calculators", () => {
    render(
      <MemoryRouter>
        <ProductSystemOfferCostChannels />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("product-system-downstream-strip-label")).toHaveTextContent(
      /Alte sisteme/i,
    );
    const offer = screen.getByTestId("product-system-channel-offer");
    const cost = screen.getByTestId("product-system-channel-cost");
    const execution = screen.getByTestId("product-system-channel-execution");
    expect(offer).toHaveTextContent("Ofertă client");
    expect(cost).toHaveTextContent("Cost intern");
    expect(execution).toHaveTextContent("Execution");
    expect(offer).not.toHaveTextContent("Cost intern");
    expect(cost).not.toHaveTextContent("Ofertă client");
    expect(screen.getByTestId("product-system-channel-offer-link")).toHaveAttribute(
      "href",
      "/quotes",
    );
    expect(screen.getByTestId("product-system-channel-cost-link")).toHaveAttribute(
      "href",
      "/intake-v6/operator",
    );
    expect(screen.getByTestId("product-system-channel-execution-link")).toHaveAttribute(
      "href",
      "/execution",
    );
    expect(screen.queryByTestId("product-system-channel-registry-link")).not.toBeInTheDocument();
  });
});
