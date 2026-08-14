import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Reports, {
  REPORTS_DB_HELP,
  REPORTS_KPI_MODEL_HELP,
  REPORTS_MONEY_CHART_TITLE,
  REPORTS_MONEY_LABEL,
  REPORTS_PROJECTION_LABEL,
  REPORTS_TITLE,
} from "./Reports";

vi.mock("@/hooks/useReportsData", () => ({
  useReportsData: () => ({
    dailyMetrics: Array.from({ length: 7 }, (_, i) => ({
      date: `2026-08-0${i + 1}`,
      throughput: 2,
      otif: 85,
      reworkRate: 0,
      machineUtil: 65,
      avgLeadTime: 3,
      revenue: 1000,
    })),
    wcUtilHeatmap: [],
    jobStatuses: [{ label: "Scheduled", count: 1, color: "bg-purple-600" }],
    source: "db",
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}));

describe("Reports honesty (S2)", () => {
  it("presents live operational projection without sold-money language", () => {
    render(
      <MemoryRouter>
        <Reports />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: REPORTS_TITLE })).toBeTruthy();
    expect(screen.getAllByText(new RegExp(REPORTS_PROJECTION_LABEL)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(new RegExp(REPORTS_DB_HELP)).length).toBeGreaterThan(0);
    expect(screen.getByText(REPORTS_MONEY_LABEL)).toBeTruthy();
    expect(screen.getByText(REPORTS_MONEY_CHART_TITLE)).toBeTruthy();
    expect(screen.getByText(REPORTS_KPI_MODEL_HELP)).toBeTruthy();

    expect(screen.queryByText(/showing real data/i)).toBeNull();
    expect(screen.queryByText(/Rapoarte & Analiză/i)).toBeNull();
    expect(screen.queryByText(/Revenue 7d/i)).toBeNull();
    expect(screen.queryByText(/venit contabil/i)).toBeTruthy();
  });

  it("keeps existing money and KPI numeric presentation from the same source", () => {
    render(
      <MemoryRouter>
        <Reports />
      </MemoryRouter>,
    );

    expect(screen.getByText("7.0k")).toBeTruthy();
    expect(screen.getAllByText("RON").length).toBeGreaterThan(0);
    expect(screen.getByText("85")).toBeTruthy();
    expect(screen.getByText("65")).toBeTruthy();
    expect(screen.getByText("3.0")).toBeTruthy();
    expect(screen.getByText("2.0")).toBeTruthy();
  });
});
