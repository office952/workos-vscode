import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkIntake from "./WorkIntake";
import Colaboratori from "./Colaboratori";
import Utilaje from "./Utilaje";

const mockUseBackendData = vi.fn();
const mockUseColaboratoriData = vi.fn();
const mockUseMachinesData = vi.fn();
const mockRefreshCollaborators = vi.fn();
const mockCreateSupplier = vi.fn();

vi.mock("@/hooks/useBackendData", () => ({
  useBackendData: () => mockUseBackendData(),
}));

vi.mock("@/hooks/useColaboratoriData", () => ({
  useColaboratoriData: () => mockUseColaboratoriData(),
}));

vi.mock("@/hooks/useMachinesData", () => ({
  useMachinesData: () => mockUseMachinesData(),
}));

vi.mock("@/components/workos/NewIntakeDialog", () => ({
  default: ({ open }: { open: boolean }) => (open ? <div>New Intake Dialog Open</div> : null),
}));

vi.mock("@/lib/dataStore", () => ({
  createDraftQuoteFromIntake: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  suppliersApi: {
    create: (...args: unknown[]) => mockCreateSupplier(...args),
  },
}));

function renderWithRouter(node: React.ReactNode) {
  return render(<MemoryRouter>{node}</MemoryRouter>);
}

describe("BUILD 27.09 operational CRUD recovery", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseBackendData.mockReturnValue({
      intakes: [],
      quotes: [],
      orders: [],
      materials: [],
      suppliers: [],
      loading: false,
      error: null,
      source: "mixed",
      sourcesDetail: { intakes: "db" },
      refresh: vi.fn(),
    });

    mockUseColaboratoriData.mockReturnValue({
      collaborators: [],
      loading: false,
      error: null,
      source: "empty",
      refresh: mockRefreshCollaborators,
    });

    mockUseMachinesData.mockReturnValue({
      machines: [],
      machineSpecs: [],
      maintenanceRecords: [],
      workcenters: [],
      source: "db",
      loading: false,
    });
  });

  it("keeps Work Intake create enabled when intake source is db even if aggregate source is mixed", () => {
    renderWithRouter(<WorkIntake />);

    const createButton = screen.getByRole("button", { name: /Cerere Nouă/i });
    expect(createButton).toBeEnabled();

    fireEvent.click(createButton);
    expect(screen.getByText("New Intake Dialog Open")).toBeInTheDocument();
  });

  it("creates a collaborator through suppliers backend and refreshes the list", async () => {
    mockCreateSupplier.mockResolvedValue({ id: 101 });

    renderWithRouter(<Colaboratori />);

    fireEvent.click(screen.getByRole("button", { name: /Adaugă colaborator/i }));
    fireEvent.change(screen.getByLabelText(/Nume colaborator/i), {
      target: { value: "Atelier Montaj Sud" },
    });
    fireEvent.change(screen.getByLabelText(/^Cod$/i), {
      target: { value: "SUP-MONTAJ" },
    });
    fireEvent.change(screen.getByLabelText(/Lead time/i), {
      target: { value: "5" },
    });
    fireEvent.change(screen.getByLabelText(/Rating/i), {
      target: { value: "4" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Creează colaborator/i }));

    await waitFor(() => {
      expect(mockCreateSupplier).toHaveBeenCalledWith({
        code: "SUP-MONTAJ",
        name: "Atelier Montaj Sud",
        category: "serviciu",
        lead_time_days: 5,
        rating: 4,
        active_orders: 0,
        last_delivery: undefined,
      });
    });
    expect(mockRefreshCollaborators).toHaveBeenCalledTimes(1);
  });

  it("surfaces collaborator create errors from suppliers backend", async () => {
    mockCreateSupplier.mockRejectedValue(new Error("HTTP 403"));

    renderWithRouter(<Colaboratori />);

    fireEvent.click(screen.getByRole("button", { name: /Adaugă colaborator/i }));
    fireEvent.change(screen.getByLabelText(/Nume colaborator/i), {
      target: { value: "Atelier Blocant" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Creează colaborator/i }));

    expect(await screen.findByText(/HTTP 403/)).toBeInTheDocument();
  });

  it("shows Utilaje create as explicitly blocked because backend is read-only", () => {
    renderWithRouter(<Utilaje />);

    expect(screen.getByRole("button", { name: /Utilaj Nou/i })).toBeDisabled();
    expect(screen.getByText(/backend-ul curent expune doar endpoint-uri read-only/i)).toBeInTheDocument();
  });
});