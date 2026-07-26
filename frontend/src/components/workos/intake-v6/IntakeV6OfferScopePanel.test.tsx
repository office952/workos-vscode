import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import IntakeV6OfferScopePanel from "./IntakeV6OfferScopePanel";

function getStatusText() {
  return screen.getByTestId("intake-v6-offer-scope-status").textContent ?? "";
}

function selectSubsetMode() {
  fireEvent.click(screen.getByTestId("intake-v6-offer-scope-mode-subset"));
}

function expandAdvancedLedOptions() {
  fireEvent.click(screen.getByTestId("intake-v6-offer-scope-advanced-toggle"));
}

describe("IntakeV6OfferScopePanel", () => {
  it("renders full product as default", () => {
    render(<IntakeV6OfferScopePanel payload={{}} onSave={vi.fn(async () => true)} />);

    expect(screen.getByTestId("intake-v6-offer-scope-mode-full")).toBeChecked();
    expect(screen.queryByTestId("intake-v6-offer-scope-subset-options")).not.toBeInTheDocument();
  });

  it("ACM panel-alone teaches panou needs instead of Față/Cant/LED checkboxes", () => {
    render(
      <IntakeV6OfferScopePanel
        payload={{
          product_composition_recommendation: { composition_type: "support_only" },
        }}
        onSave={vi.fn(async () => true)}
      />,
    );
    expect(screen.getByTestId("intake-v6-acm-panel-only-needs")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-acm-panel-only-out-of-scope")).toHaveTextContent(/Adeziv/i);
    expect(screen.queryByTestId("intake-v6-offer-scope-face")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-offer-scope-cant")).not.toBeInTheDocument();
  });

  it("shows primary modules and system LED bundle with advanced split in subset mode", () => {
    render(<IntakeV6OfferScopePanel payload={{}} onSave={vi.fn(async () => true)} />);

    selectSubsetMode();

    expect(screen.getByTestId("intake-v6-offer-scope-face")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-cant")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-back")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-system-led")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-offer-scope-advanced-toggle")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-offer-scope-lighting")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-offer-scope-electrical")).not.toBeInTheDocument();

    expandAdvancedLedOptions();

    expect(screen.getByTestId("intake-v6-offer-scope-advanced-options")).toBeInTheDocument();
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

    selectSubsetMode();
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
    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-cant"));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
  });

  it("rapid sequential toggles preserve latest state with one PUT per final intent", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    expandAdvancedLedOptions();
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
    selectSubsetMode();
    expandAdvancedLedOptions();
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

    expect(screen.getByTestId("intake-v6-offer-scope-system-led")).toBeChecked();
    expandAdvancedLedOptions();
    expect(screen.getByTestId("intake-v6-offer-scope-lighting")).toBeChecked();
    expect(screen.getByTestId("intake-v6-offer-scope-electrical")).toBeChecked();
    expect(screen.getByText(/Componente: LIGHTING, ELECTRICAL/i)).toBeInTheDocument();
  });

  it("serializes LIGHTING and ELECTRICAL combinations deterministically", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    expandAdvancedLedOptions();
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

  it("HTTP 200 clears saving", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-back"));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(getStatusText()).not.toContain("Salvez selecția"));
    expect(getStatusText()).toContain("Selecție confirmată");
  });

  it("HTTP error clears saving and shows error", async () => {
    const onSave = vi.fn(async () => false);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-back"));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(getStatusText()).not.toContain("Salvez selecția"));
    expect(screen.getByText(/Salvarea selecției a eșuat/i)).toBeInTheDocument();
  });

  it("refetch after response does not re-enable saving", async () => {
    const onSave = vi.fn(async () => true);
    const { rerender } = render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-back"));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));

    rerender(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: { mode: "component_subset", sold_modules: ["BACK"] },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={onSave}
      />,
    );

    await waitFor(() => expect(getStatusText()).not.toContain("Salvez selecția"));
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  it("rerender does not preserve stale saving", async () => {
    const resolvers: Array<(value: boolean) => void> = [];
    const onSave = vi.fn(
      () =>
        new Promise<boolean>((resolve) => {
          resolvers.push(resolve);
        }),
    );

    const { rerender } = render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);
    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-back"));
    await waitFor(() => expect(getStatusText()).toContain("Salvez selecția"));

    rerender(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);
    resolvers[0]?.(true);

    await waitFor(() => expect(getStatusText()).not.toContain("Salvez selecția"));
  });

  it("one action creates one PUT", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    expandAdvancedLedOptions();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-lighting"));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(getStatusText()).toContain("Selecție confirmată"));
  });

  it("in-flight guard clears on success", async () => {
    const resolvers: Array<(value: boolean) => void> = [];
    const onSave = vi.fn(
      () =>
        new Promise<boolean>((resolve) => {
          resolvers.push(resolve);
        }),
    );

    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);
    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-back"));
    await waitFor(() => expect(getStatusText()).toContain("Salvez selecția"));

    resolvers[0]?.(true);
    await waitFor(() => expect(getStatusText()).not.toContain("Salvez selecția"));
    expect(getStatusText()).toContain("Selecție confirmată");
  });

  it("in-flight guard clears on error", async () => {
    const onSave = vi.fn(async () => {
      throw new Error("network");
    });
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-back"));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(getStatusText()).not.toContain("Salvez selecția"));
    expect(screen.getByText(/Salvarea selecției a eșuat/i)).toBeInTheDocument();
  });

  it("empty to BACK to LIGHTING remains stable", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    expect(screen.getByTestId("intake-v6-offer-scope-empty-subset-error")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-back"));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(getStatusText()).toContain("Selecție confirmată"));

    expandAdvancedLedOptions();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-lighting"));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["BACK", "LIGHTING"],
        confirmed: true,
      }),
    );
    await waitFor(() => expect(getStatusText()).toContain("Selecție confirmată"));
  });

  it("bundle selection writes LIGHTING and ELECTRICAL without SYSTEM_LED code", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-system-led"));

    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["LIGHTING", "ELECTRICAL"],
        confirmed: true,
      }),
    );
    expect(onSave.mock.calls.every((call) => !call[0].soldModules.includes("SYSTEM_LED" as never))).toBe(true);
  });

  it("bundle deselection removes LIGHTING and ELECTRICAL", async () => {
    const onSave = vi.fn(async () => true);
    render(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: {
            mode: "component_subset",
            sold_modules: ["FACE", "LIGHTING", "ELECTRICAL"],
          },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={onSave}
      />,
    );

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-system-led"));

    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["FACE"],
        confirmed: true,
      }),
    );
  });

  it("advanced LIGHTING only keeps bundle unchecked and partial", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    expandAdvancedLedOptions();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-lighting"));

    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["LIGHTING"],
        confirmed: true,
      }),
    );
    expect(screen.getByTestId("intake-v6-offer-scope-system-led")).not.toBeChecked();
    expect((screen.getByTestId("intake-v6-offer-scope-system-led") as HTMLInputElement).indeterminate).toBe(true);
  });

  it("advanced ELECTRICAL only keeps bundle unchecked and partial", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    expandAdvancedLedOptions();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-electrical"));

    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["ELECTRICAL"],
        confirmed: true,
      }),
    );
    expect(screen.getByTestId("intake-v6-offer-scope-system-led")).not.toBeChecked();
    expect((screen.getByTestId("intake-v6-offer-scope-system-led") as HTMLInputElement).indeterminate).toBe(true);
  });

  it("combined advanced selection reflects bundle selected", async () => {
    const onSave = vi.fn(async () => true);
    render(<IntakeV6OfferScopePanel payload={{}} onSave={onSave} />);

    selectSubsetMode();
    expandAdvancedLedOptions();
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-lighting"));
    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-electrical"));

    await waitFor(() => expect(screen.getByTestId("intake-v6-offer-scope-system-led")).toBeChecked());
    expect((screen.getByTestId("intake-v6-offer-scope-system-led") as HTMLInputElement).indeterminate).toBe(false);
  });

  it("bundle toggle from partial adds both modules in one save intent", async () => {
    const onSave = vi.fn(async () => true);
    render(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: { mode: "component_subset", sold_modules: ["LIGHTING"] },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={onSave}
      />,
    );

    fireEvent.click(screen.getByTestId("intake-v6-offer-scope-system-led"));

    await waitFor(() =>
      expect(onSave).toHaveBeenLastCalledWith({
        mode: "component_subset",
        soldModules: ["LIGHTING", "ELECTRICAL"],
        confirmed: true,
      }),
    );
  });

  it("shows dependency feedback for lighting-only scope", async () => {
    render(
      <IntakeV6OfferScopePanel
        payload={{
          offer_scope: { mode: "component_subset", sold_modules: ["LIGHTING"] },
          offer_scope_confirmed: { confirmed: true },
        }}
        onSave={vi.fn(async () => true)}
      />,
    );

    expect(screen.getByTestId("intake-v6-offer-scope-dependency-feedback")).toBeInTheDocument();
  });

  it("full product mode hides bundle and advanced controls", () => {
    render(<IntakeV6OfferScopePanel payload={{}} onSave={vi.fn(async () => true)} />);

    expect(screen.queryByTestId("intake-v6-offer-scope-system-led")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-offer-scope-advanced-toggle")).not.toBeInTheDocument();
  });
});
