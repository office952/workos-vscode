import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Settings from "./Settings";

const mockGet = vi.fn();
const mockUpdate = vi.fn();

vi.mock("@/api/companyCommercialSettings", () => ({
  getCompanyCommercialSettings: () => mockGet(),
  updateCompanyCommercialSettings: (payload: {
    default_vat_pct?: number;
    eur_to_ron_rate?: number;
  }) => mockUpdate(payload),
}));

vi.mock("@/lib/api", () => ({
  recurringPaymentsApi: { list: vi.fn().mockResolvedValue([]) },
  costEngineApi: {
    getConfig: vi.fn().mockResolvedValue({}),
    getBaseConfig: vi.fn().mockResolvedValue({}),
  },
}));

describe("Settings VAT governance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({ default_vat_pct: 21, eur_to_ron_rate: 5 });
    mockUpdate.mockImplementation(async (payload) => ({
      default_vat_pct: payload.default_vat_pct ?? 21,
      eur_to_ron_rate: payload.eur_to_ron_rate ?? 5,
    }));
  });

  it("shows editable default VAT field on Societate tab", async () => {
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId("settings-default-vat-pct")).toBeInTheDocument();
    });
    expect(screen.getByText("TVA implicit pentru oferte (%)")).toBeInTheDocument();
  });

  it("can save VAT 21", async () => {
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId("settings-default-vat-pct")).toHaveValue(21);
    });
    fireEvent.click(screen.getByText("Salvează TVA"));
    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith({ default_vat_pct: 21 });
    });
  });

  it("can save VAT 0", async () => {
    mockUpdate.mockResolvedValue({ default_vat_pct: 0 });
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    );
    const input = await screen.findByTestId("settings-default-vat-pct");
    fireEvent.change(input, { target: { value: "0" } });
    fireEvent.click(screen.getByText("Salvează TVA"));
    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith({ default_vat_pct: 0 });
    });
  });

  it("rejects invalid VAT client-side", async () => {
    render(
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    );
    const input = await screen.findByTestId("settings-default-vat-pct");
    fireEvent.change(input, { target: { value: "150" } });
    fireEvent.click(screen.getByText("Salvează TVA"));
    await waitFor(() => {
      expect(screen.getByText("TVA trebuie să fie între 0 și 100.")).toBeInTheDocument();
    });
    expect(mockUpdate).not.toHaveBeenCalled();
  });
});
