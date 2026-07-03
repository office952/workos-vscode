import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import IntakeLegacyRoute from "./IntakeLegacyRoute";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import type { IntakeRequest } from "@/lib/mockData";

const mockUseBackendData = vi.fn();

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

vi.mock("./IntakeDetail", () => ({
  default: () => <div data-testid="intake-detail-legacy">Legacy intake form</div>,
}));

function baseIntake(overrides: Partial<IntakeRequest>): IntakeRequest {
  return {
    id: "IR-TEST",
    client: "Client",
    contactPerson: "—",
    channel: "email",
    productFamily: "",
    description: "desc",
    dimensions: "—",
    quantity: 1,
    status: "in_review",
    assignedTo: "—",
    createdAt: "2026-06-07T00:00:00Z",
    updatedAt: "2026-06-07T00:00:00Z",
    notes: "",
    priority: "normal",
    deliveryType: "delivery_standard",
    identity: { type: "temp", tempRef: "TEMP-IR-TEST" },
    ...overrides,
  };
}

function renderRoute(code: string) {
  render(
    <MemoryRouter initialEntries={[`/intake/${code}`]}>
      <Routes>
        <Route path="/intake/:id" element={<IntakeLegacyRoute />} />
        <Route
          path="/intake-v6/:workspaceId/operator"
          element={<div data-testid="intake-v6-page">V6 flow</div>}
        />
      </Routes>
    </MemoryRouter>
  );
}

describe("IntakeLegacyRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects volumetric intake to Intake V6", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "IR-MQ51B998",
          productFamily: "litere_volumetrice",
          confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });

    renderRoute("IR-MQ51B998");
    expect(screen.getByTestId("intake-v6-page")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-detail-legacy")).not.toBeInTheDocument();
  });

  it("renders legacy IntakeDetail for non-volumetric intake", () => {
    mockUseBackendData.mockReturnValue({
      intakes: [
        baseIntake({
          id: "WI-3321",
          productFamily: "Casete Luminoase",
        }),
      ],
      loading: false,
      error: null,
      source: "db",
      refresh: vi.fn(),
    });

    renderRoute("WI-3321");
    expect(screen.getByTestId("intake-detail-legacy")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-page")).not.toBeInTheDocument();
  });
});
