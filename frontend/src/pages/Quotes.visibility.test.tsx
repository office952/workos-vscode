import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Quotes from "./Quotes";

const mockUseBackendData = vi.fn();

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { role: "admin", name: "Admin", email: "admin@local" } }),
}));

vi.mock("@/hooks/useCompanyCommercialSettings", () => ({
  useCompanyCommercialSettings: () => ({
    vatPct: 21,
    eurToRonRate: 5,
    loading: false,
    error: null,
    reload: vi.fn(),
  }),
}));

vi.mock("@/components/workos/QuoteWizard", () => ({
  default: ({ open, onClose }: { open: boolean; onClose: () => void }) =>
    open ? (
      <div data-testid="quote-wizard">
        <span>Ofertă nouă</span>
        <button type="button" onClick={onClose}>
          Închide wizard
        </button>
      </div>
    ) : null,
}));

vi.mock("@/lib/dataStore", () => ({
  updateQuoteStatus: vi.fn(),
  createOrderFromQuote: vi.fn(),
}));

describe("Quotes visibility", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBackendData.mockReturnValue({
      quotes: [],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });
  });

  it("Ofertă nouă opens generic quote wizard", () => {
    render(
      <MemoryRouter>
        <Quotes />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole("button", { name: /Ofertă nouă/i }));
    const wizard = screen.getByTestId("quote-wizard");
    expect(wizard).toBeInTheDocument();
    expect(wizard).toHaveTextContent("Ofertă nouă");
  });
});
