import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Orders from "./Orders";

const mockNavigate = vi.fn();
const mockRefresh = vi.fn();
const mockUseBackendData = vi.fn();

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

describe("Orders empty state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRefresh.mockResolvedValue(undefined);
    mockUseBackendData.mockReturnValue({
      orders: [],
      loading: false,
      error: null,
      source: "db",
      refresh: mockRefresh,
    });
  });

  it("afișează empty state când nu există comenzi", async () => {
    render(
      <MemoryRouter initialEntries={["/orders"]}>
        <Routes>
          <Route path="/orders/:orderId?" element={<Orders />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByTestId("orders-empty-state")).toBeTruthy();
    expect(screen.getByText("Nu există comenzi încă")).toBeTruthy();
    expect(
      screen.getByText("Comenzile apar aici după acceptarea sau conversia unei oferte.")
    ).toBeTruthy();
    expect(screen.getByText("Live DB")).toBeTruthy();
    expect(screen.queryByText("Selectează o comandă pentru detalii")).toBeNull();
    expect(screen.getByTestId("orders-empty-detail-panel")).toBeTruthy();
  });

  it("navighează la Oferte și Work Intake din empty state", async () => {
    render(
      <MemoryRouter initialEntries={["/orders"]}>
        <Routes>
          <Route path="/orders/:orderId?" element={<Orders />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByTestId("orders-empty-state");
    fireEvent.click(screen.getByRole("button", { name: /Mergi la Oferte/i }));
    expect(mockNavigate).toHaveBeenCalledWith("/quotes");

    fireEvent.click(screen.getByRole("button", { name: /Deschide Work Intake/i }));
    expect(mockNavigate).toHaveBeenCalledWith("/intake");
  });

  it("summary cards rămân la 0", async () => {
    render(
      <MemoryRouter initialEntries={["/orders"]}>
        <Routes>
          <Route path="/orders/:orderId?" element={<Orders />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByTestId("orders-empty-state");
    const totalCard = screen.getByText("Total Comenzi").closest("div");
    expect(totalCard?.textContent).toContain("0");
  });
});
