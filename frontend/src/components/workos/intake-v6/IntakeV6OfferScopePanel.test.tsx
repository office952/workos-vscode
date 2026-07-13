import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import IntakeV6OfferScopePanel from "./IntakeV6OfferScopePanel";

describe("IntakeV6OfferScopePanel", () => {
  it("renders full product as default", () => {
    render(<IntakeV6OfferScopePanel payload={{}} onSave={vi.fn(async () => true)} />);

    expect(screen.getByTestId("intake-v6-offer-scope-mode-full")).toBeChecked();
    expect(screen.queryByTestId("intake-v6-offer-scope-subset-options")).not.toBeInTheDocument();
  });

  it("shows slice-1 checkboxes including lighting and electrical in subset mode", () => {
    render(<IntakeV6OfferScopePanel payload={{}} onSave={vi.fn(async () => true)} />);

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));

    expect(screen.getByTestId("intake-v6-offer-scope-face")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-cant")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-back")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-lighting")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-electrical")).toBeInTheDocument();
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

  it("does not autosave on mount for legacy full_product workspace", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);
    await waitFor(() => expect(onSave).not.toHaveBeenCalled(), { timeout: 800 });
  });

  it("does not save when full_product is already selected", async () => {
    const onSave = vi.fn(async () => true);
    render(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: { mode: "full_product", sold_modules: [] },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={onSave}
      />,
    );
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-full"));
    await waitFor(() => expect(onSave).not.toHaveBeenCalled(), { timeout: 800 });
  });

  it("hydrates without write-back save loop", async () => {
    const onSave = vi.fn(async () => true);
    const { rerender } = render(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: { mode: "component_subset", sold_modules: ["FACE"] },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={onSave}
      />,
    );
    rerender(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: { mode: "component_subset", sold_modules: ["FACE"] },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={onSave}
      />,
    );
    await waitFor(() => expect(onSave).not.toHaveBeenCalled(), { timeout: 800 });
  });

  it("checkbox toggle triggers a single intentional save", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-cant"));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
  });

  it("rapid sequential toggles preserve latest state with one PUT per final intent", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-lighting"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-electrical"));

    await waitFor(() => expect(onSave).toHaveBeenCalled());
    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["LIGHTING", "ELECTRICAL"],
        confirmed: true,
      }),
    );
    expect(onSave.mock.calls.length).toBeLessThanOrEqual(2);
  });

  it("queues trailing intent while save is in flight and never restores older scope", async () => {
    const resolvers: Array<(value: boolean) => void> = [];
    const onSave = vi.fn(
      () =>
        new Promise<boolean>((resolve) => {
          resolvers.push(resolve);
        }),
    );

    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-lighting"));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0]?.[0]).toEqual({
      mode: "component_subset",
      soldModules: ["LIGHTING"],
      confirmed: true,
    });

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-electrical"));
    expect(onSave).toHaveBeenCalledTimes(1);

    resolvers[0]?.(true);
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(2));
    expect(onSave.mock.calls[1]?.[0]).toEqual({
      mode: "component_subset",
      soldModules: ["LIGHTING", "ELECTRICAL"],
      confirmed: true,
    });
  });

  it("reload preserves persisted LIGHTING and ELECTRICAL combination", () => {
    render(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: {
            contract_version: "offer_scope_contract/v1",
            mode: "component_subset",
            sold_modules: ["ELECTRICAL", "LIGHTING"],
          },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={vi.fn(async () => true)}
      />,
    );

    expect(screen.getByTestId("intake-v6-offer-scope-lighting")).toBeChecked();
    expect(screen.getByTestId("intake-v6-offer-scope-electrical")).toBeChecked();
    expect(screen.getByText(/Componente: LIGHTING, ELECTRICAL/i)).toBeInTheDocument();
  });

  it("serializes LIGHTING and ELECTRICAL combinations deterministically", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-electrical"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-lighting"));

    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["LIGHTING", "ELECTRICAL"],
        confirmed: true,
      }),
    );
  });
});
