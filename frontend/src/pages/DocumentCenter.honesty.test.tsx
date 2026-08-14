import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DocumentCenter from "./DocumentCenter";

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => ({
    quotes: [],
    orders: [],
    loading: false,
  }),
}));

describe("DocumentCenter honesty (S2)", () => {
  it("marks the hub as not-live and keeps disabled CTAs non-actionable", () => {
    render(
      <MemoryRouter>
        <DocumentCenter />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: /Document Center/i })).toBeTruthy();
    expect(screen.getByText("ÎN PREGĂTIRE")).toBeTruthy();
    expect(
      screen.getByText(/Proiecție din oferte și comenzi/i),
    ).toBeTruthy();
    expect(screen.queryByText(/arhivă de documente/i)).toBeTruthy();

    const generate = screen.getByRole("button", { name: /Generează document/i });
    const upload = screen.getByRole("button", { name: /Încarcă/i });
    expect(generate).toBeDisabled();
    expect(upload).toBeDisabled();
    expect(generate).toHaveAttribute("aria-disabled", "true");
    expect(upload).toHaveAttribute("aria-disabled", "true");
  });
});
