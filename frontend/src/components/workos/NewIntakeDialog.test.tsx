import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import NewIntakeDialog from "./NewIntakeDialog";

const mockClientsList = vi.fn();
const mockClientsCreate = vi.fn();
const mockIntakesCreate = vi.fn();
const mockProductFamiliesList = vi.fn();

vi.mock("@/lib/api", () => ({
  clientsApi: {
    list: (...args: unknown[]) => mockClientsList(...args),
    create: (...args: unknown[]) => mockClientsCreate(...args),
  },
  intakesApi: {
    create: (...args: unknown[]) => mockIntakesCreate(...args),
  },
}));

vi.mock("@/api/productFamilies", () => ({
  productFamiliesApi: {
    list: (...args: unknown[]) => mockProductFamiliesList(...args),
  },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { id: "dev-admin", role: "admin", email: "dev@localhost", name: "Dev Admin" },
    loading: false,
    isAuthenticated: true,
    authState: "authenticated",
    canAccessProtectedApi: true,
    devAuthEnabled: true,
    logout: vi.fn(),
    login: vi.fn(),
  }),
}));

const REGISTRY_FAMILIES = [
  { id: 1, family_id: "litere_volumetrice", label: "Litere volumetrice", active: true },
  { id: 2, family_id: "print_large_format", label: "Print format mare", active: true },
  { id: 3, family_id: "servicii_montaj", label: "Servicii montaj", active: true },
  { id: 4, family_id: "casete_luminoase", label: "Casete luminoase", active: true },
  { id: 5, family_id: "vinyl_stickers", label: "Autocolant", active: true },
  { id: 6, family_id: "semnalistica_interioara", label: "Semnalistică interioară", active: true },
  { id: 7, family_id: "semnalistica_exterioara", label: "Semnalistică exterioară", active: true },
];

describe("NewIntakeDialog quick start UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockClientsList.mockResolvedValue([]);
    mockProductFamiliesList.mockResolvedValue({
      items: REGISTRY_FAMILIES,
      total: REGISTRY_FAMILIES.length,
      skip: 0,
      limit: 500,
    });
    mockClientsCreate.mockResolvedValue({
      id: 1,
      name: "STAGING TEST CLIENT",
      contact_person: "QA User",
    });
    mockIntakesCreate.mockResolvedValue({ id: 10 });
  });

  function renderDialog() {
    return render(
      <NewIntakeDialog open={true} onClose={vi.fn()} onCreated={vi.fn()} />
    );
  }

  async function moveToDetailsStep() {
    fireEvent.click(screen.getByRole("button", { name: "Client Temporar" }));
    fireEvent.change(screen.getByPlaceholderText(/SC Exemplu SRL sau Ion Popescu/i), {
      target: { value: "STAGING TEST CLIENT" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Continuă/i }));
    await screen.findByRole("button", { name: /Creează Cerere/i });
  }

  it("opens quick start with human-readable work type cards, not native family select", async () => {
    renderDialog();
    await moveToDetailsStep();

    expect(screen.getByTestId("work-type-picker")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /Litere volumetrice/i })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /Nu știu încă \/ Cerere generică/i })).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: /Familie Produs/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/litere_volumetrice/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Registry:/i)).not.toBeInTheDocument();
  });

  it("loads active product families from backend registry for picker availability", async () => {
    renderDialog();
    await moveToDetailsStep();

    expect(mockProductFamiliesList).toHaveBeenCalledWith({
      query: { active: true },
      limit: 500,
      sort: "label",
    });
  });

  it("shows visible missing requirements when create is disabled", async () => {
    renderDialog();
    await moveToDetailsStep();

    const createButton = screen.getByRole("button", { name: /Creează Cerere/i });
    expect(createButton).toBeDisabled();
    expect(screen.getByTestId("create-intake-missing-requirements")).toHaveTextContent(
      /Completează: tip lucrare, descriere/i
    );
  });

  it("does not create intake when registry has no active families", async () => {
    mockProductFamiliesList.mockResolvedValueOnce({ items: [], total: 0, skip: 0, limit: 500 });

    renderDialog();
    await moveToDetailsStep();

    fireEvent.change(
      screen.getByPlaceholderText(/Litere volumetrice pentru fațadă/i),
      { target: { value: "Test intake without family" } }
    );
    fireEvent.click(screen.getByRole("button", { name: /Creează Cerere/i }));

    expect(mockClientsCreate).not.toHaveBeenCalled();
    expect(mockIntakesCreate).not.toHaveBeenCalled();
  });

  it("submits volumetric draft with litere_volumetrice family and no product_spec_json", async () => {
    renderDialog();
    await moveToDetailsStep();

    fireEvent.click(screen.getByRole("radio", { name: /Litere volumetrice/i }));
    fireEvent.change(
      screen.getByPlaceholderText(/Litere volumetrice pentru fațadă/i),
      { target: { value: "Litere volumetrice pentru fațadă magazin" } }
    );
    fireEvent.click(screen.getByRole("button", { name: /Creează Cerere/i }));

    await waitFor(() => {
      expect(mockClientsCreate).toHaveBeenCalledTimes(1);
      expect(mockIntakesCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          product_family: "litere_volumetrice",
          description: "Litere volumetrice pentru fațadă magazin",
          status: "new",
        })
      );
    });

    const payload = mockIntakesCreate.mock.calls[0][0];
    expect(payload.product_spec_json).toBeUndefined();
  });

  it("keeps generic option available and creates unresolved draft without servicii_montaj fallback", async () => {
    renderDialog();
    await moveToDetailsStep();

    fireEvent.click(screen.getByRole("radio", { name: /Nu știu încă \/ Cerere generică/i }));
    fireEvent.change(
      screen.getByPlaceholderText(/Litere volumetrice pentru fațadă/i),
      { target: { value: "Cerere generică — tip necunoscut" } }
    );
    fireEvent.click(screen.getByRole("button", { name: /Creează Cerere/i }));

    await waitFor(() => {
      expect(mockIntakesCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          product_family: "",
          description: "Cerere generică — tip necunoscut",
          status: "new",
        })
      );
    });

    const payload = mockIntakesCreate.mock.calls[0][0];
    expect(payload.product_family).not.toBe("servicii_montaj");
    expect(payload.product_spec_json).toBeUndefined();
  });

  it("surfaces backend family validation errors clearly", async () => {
    mockIntakesCreate.mockRejectedValueOnce(new Error("Invalid product_family/family_id 'print_digital'"));

    renderDialog();
    await moveToDetailsStep();

    fireEvent.click(screen.getByRole("radio", { name: /Litere volumetrice/i }));
    fireEvent.change(
      screen.getByPlaceholderText(/Litere volumetrice pentru fațadă/i),
      { target: { value: "Validated intake payload" } }
    );
    fireEvent.click(screen.getByRole("button", { name: /Creează Cerere/i }));

    expect(await screen.findByText(/Tipul de lucrare selectat nu mai este valid/i)).toBeInTheDocument();
  });

  it("shows clear message for intake.create permission_denied", async () => {
    mockClientsCreate.mockResolvedValue({
      id: 1,
      name: "SC LEX HOTEL SRL",
      contact_person: "Contact",
    });
    mockIntakesCreate.mockRejectedValueOnce({
      message: "Request failed with status code 403",
      response: {
        status: 403,
        data: {
          detail: {
            error: "permission_denied",
            permission: "intake.create",
            role: "employee_mobile",
            message: "Role 'employee_mobile' does not have permission 'intake.create'",
          },
        },
      },
    });

    renderDialog();
    await moveToDetailsStep();

    fireEvent.click(screen.getByRole("radio", { name: /Litere volumetrice/i }));
    fireEvent.change(
      screen.getByPlaceholderText(/Litere volumetrice pentru fațadă/i),
      { target: { value: "Litere Volumetrice luminoase - 4800 x 600mm" } }
    );
    fireEvent.click(screen.getByRole("button", { name: /Creează Cerere/i }));

    expect(
      await screen.findByText(/Contul Employee Mobile nu poate crea cereri Work Intake/i)
    ).toBeInTheDocument();
  });
});
