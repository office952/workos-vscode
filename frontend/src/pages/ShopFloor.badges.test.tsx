import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ShopFloor, { mapShopFloorSourceToBadge } from "./ShopFloor";

const mockUseShopFloorData = vi.fn();

vi.mock("@/hooks/useShopFloorData", () => ({
  useShopFloorData: () => mockUseShopFloorData(),
}));

function mockShopFloor(overrides: Record<string, unknown> = {}) {
  mockUseShopFloorData.mockReturnValue({
    machines: [],
    workcenters: [],
    jobs: [],
    alerts: [],
    lastUpdate: new Date("2026-06-12T12:00:00Z"),
    updateCount: 1,
    source: "db",
    connectionStatus: "connected",
    error: null,
    ...overrides,
  });
}

describe("ShopFloor design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("maps mock hook source to demo badge presentation", () => {
    expect(mapShopFloorSourceToBadge("mock")).toBe("demo");
    expect(mapShopFloorSourceToBadge("empty")).toBe("empty");
    expect(mapShopFloorSourceToBadge("db")).toBe("db");
  });

  it("renders SourceBadge with Live DB on live fixture", () => {
    mockShopFloor({ source: "db" });
    render(
      <MemoryRouter>
        <ShopFloor />
      </MemoryRouter>,
    );

    expect(screen.getByText("Live DB")).toHaveAttribute("data-source", "db");
  });

  it("renders SourceBadge with Live DB (gol) on empty live backend fixture", () => {
    mockShopFloor({ source: "empty", connectionStatus: "connected" });
    render(
      <MemoryRouter>
        <ShopFloor />
      </MemoryRouter>,
    );

    expect(screen.getByText("Live DB (gol)")).toHaveAttribute("data-source", "empty");
    expect(screen.getByText(/Live data unavailable pentru ShopFloor/)).toBeInTheDocument();
  });

  it("renders SourceBadge with Source Error on error fixture", () => {
    mockShopFloor({
      source: "error",
      error: "API error",
      connectionStatus: "reconnecting",
    });
    render(
      <MemoryRouter>
        <ShopFloor />
      </MemoryRouter>,
    );

    expect(screen.getByText("Source Error")).toHaveAttribute("data-source", "error");
    expect(screen.getByText(/Datele shopfloor nu au putut fi încărcate/)).toBeInTheDocument();
  });

  it("renders SourceBadge with Demo on mock fallback fixture", () => {
    mockShopFloor({ source: "mock", connectionStatus: "connected" });
    render(
      <MemoryRouter>
        <ShopFloor />
      </MemoryRouter>,
    );

    expect(screen.getByText("Demo")).toHaveAttribute("data-source", "demo");
  });
});
