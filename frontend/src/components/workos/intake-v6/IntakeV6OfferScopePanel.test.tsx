import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import IntakeV6OfferScopePanel from "./IntakeV6OfferScopePanel";

describe("IntakeV6OfferScopePanel", () => {
  it("renders full product as default", () => {
    render(<IntakeV6OfferScopePanel payload={{}} onSave={vi.fn(async () => true)} />);

    expect(screen.getByTestId("intake-v6-offer-scope-mode-full")).toBeChecked();
    expect(screen.queryByTestId("intake-v6-offer-scope-subset-options")).not.toBeInTheDocument();
  });

  it("shows exactly three slice-1 checkboxes in subset mode", () => {
    render(<IntakeV6OfferScopePanel payload={{}} onSave={vi.fn(async () => true)} />);

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));

    expect(screen.getByTestId("intake-v6-offer-scope-face")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-cant")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-back")).toBeInTheDocument();
    expect(screen.queryByText(/Iluminare/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Electric/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Finisaj/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Montaj/i)).not.toBeInTheDocument();
  });

  it("blocks empty subset save and shows validation", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));

    expect(screen.getByTestId("intake-v6-offer-scope-empty-subset-error")).toBeInTheDocument();
    await waitFor(() => expect(onSave).not.toHaveBeenCalled(), { timeout: 800 });
  });

  it("emits canonical codes on save for FACE only", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-face"));

    await waitFor(() =>
      expect(onSave).toHaveBeenCalledWith({
        mode: "component_subset",
        soldModules: ["FACE"],
        confirmed: true,
      }),
    );
  });

  it("hydrates persisted subset selection after reload", () => {
    render(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: {
            contract_version: "offer_scope_contract/v1",
            mode: "component_subset",
            sold_modules: ["FACE", "RETURN-CANT"],
          },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={vi.fn(async () => true)}
      />,
    );

    expect(screen.getByTestId("intake-v6-offer-scope-mode-subset")).toBeChecked();
    expect(screen.getByTestId("intake-v6-offer-scope-face")).toBeChecked();
    expect(screen.getByTestId("intake-v6-offer-scope-cant")).toBeChecked();
    expect(screen.getByTestId("intake-v6-offer-scope-back")).not.toBeChecked();
  });
});
