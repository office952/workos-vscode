import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6ModularFormAwarenessPanel from "./IntakeV6ModularFormAwarenessPanel";
import type { ModuleActivationPreviewResult } from "@/lib/intakeV6/intakeV6ModuleActivationPreview";

function buildPreview(overrides: Partial<ModuleActivationPreviewResult> = {}): ModuleActivationPreviewResult {
  return {
    items: [],
    operatorView: {
      geometryStatus: { label: "Fișier SVG analizat", ready: true },
      productReady: [
        {
          key: "debitare_fata",
          label: "Față litere",
          hint: "Pregătită din fișierul încărcat",
          state: "always_on",
          missingFields: [],
        },
        {
          key: "sistem_led",
          label: "Iluminare LED",
          hint: "Fără iluminare",
          state: "inactive",
          missingFields: [],
        },
      ],
      mounting: [],
      mountingNotApplicableNote: "Structură metalică: nu se aplică pentru selecția curentă.",
      technical: [
        {
          key: "geometry_svg",
          label: "Analiză SVG și geometrie",
          hint: "Geometrie extrasă din SVG",
          state: "always_on",
          missingFields: [],
        },
      ],
    },
    missingImportantFields: [],
    structuraSuportDerived: false,
    triggerMismatchNote: null,
    ...overrides,
  };
}

describe("IntakeV6ModularFormAwarenessPanel", () => {
  it("renders operator-friendly product summary without technical module names in main list", () => {
    render(
      <IntakeV6ModularFormAwarenessPanel
        loadStatus="loaded"
        preview={buildPreview()}
        variant="review"
      />,
    );
    expect(screen.getByTestId("intake-v6-modular-form-awareness")).toBeInTheDocument();
    expect(screen.getByText(/Rezumat produs pregătit/i)).toBeInTheDocument();
    expect(screen.getByText(/Nu reprezintă preț final/i)).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-modular-cross-tab-note")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-modular-product-debitare_fata")).toBeInTheDocument();
    expect(screen.getByText("Față litere")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-modular-product-geometry_svg")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-modular-geometry-status")).toHaveTextContent("Fișier SVG analizat");
    expect(screen.getByTestId("intake-v6-modular-mounting-not-applicable")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-modular-product-structura_suport")).not.toBeInTheDocument();
  });

  it("shows structura in mounting section when active", () => {
    render(
      <IntakeV6ModularFormAwarenessPanel
        loadStatus="loaded"
        preview={buildPreview({
          operatorView: {
            geometryStatus: { label: "Fișier SVG analizat", ready: true },
            productReady: [
              {
                key: "debitare_fata",
                label: "Față litere",
                hint: "Pregătită din fișierul încărcat",
                state: "always_on",
                missingFields: [],
              },
            ],
            mounting: [
              {
                key: "structura_suport",
                label: "Structură metalică premontaj",
                hint: "Structură metalică pentru montaj cu bare",
                state: "active",
                missingFields: [],
              },
            ],
            mountingNotApplicableNote: null,
            technical: [],
          },
          structuraSuportDerived: true,
          triggerMismatchNote: "Montaj cu bare — structura va fi derivată la ofertare.",
        })}
        triggerMismatchNote="Montaj cu bare — structura va fi derivată la ofertare."
        variant="review"
      />,
    );
    expect(screen.getByTestId("intake-v6-modular-mounting-section")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-modular-product-structura_suport")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-modular-mounting-note")).toBeInTheDocument();
  });

  it("shows fallback message when contract unavailable", () => {
    render(
      <IntakeV6ModularFormAwarenessPanel
        loadStatus="unavailable"
        preview={null}
        templateCode="TPL-UNKNOWN"
        variant="confirm"
      />,
    );
    expect(screen.getByTestId("intake-v6-modular-awareness-unavailable")).toBeInTheDocument();
  });
});
