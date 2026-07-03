import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import NewIntakeDialog from "./NewIntakeDialog";

const mockClientsList = vi.fn();
const mockClientsCreate = vi.fn();
const mockIntakesCreate = vi.fn();
const mockAvailabilityList = vi.fn();
const mockEnsureIntakeV6Workspace = vi.fn();

vi.mock("@/lib/api", () => ({
  clientsApi: {
    list: (...args: unknown[]) => mockClientsList(...args),
    create: (...args: unknown[]) => mockClientsCreate(...args),
  },
  intakesApi: {
    create: (...args: unknown[]) => mockIntakesCreate(...args),
  },
  productTemplateAvailabilityApi: {
    list: (...args: unknown[]) => mockAvailabilityList(...args),
  },
}));

vi.mock("@/lib/intakeV6/intakeV6Api", () => ({
  ensureIntakeV6WorkspaceForIntakeRequest: (...args: unknown[]) => mockEnsureIntakeV6Workspace(...args),
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

const OFFERABLE_TEMPLATE = {
  template_id: 1,
  template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  family_id: "litere_volumetrice",
  family_name: "Litere volumetrice",
  description: "Template ofertabil pentru litere volumetrice",
  db_active: true,
  quote_offerable: true,
  runtime_module: false,
  is_parent: true,
  has_modules: true,
  parent_codes: [],
  module_codes: ["TPL-VOLUM-ALUMINIU_v1"],
  status: "offerable",
  status_reason: "owner_valid_parent_template",
};

const RUNTIME_MODULE_TEMPLATE = {
  template_id: 3,
  template_code: "TPL-VOLUM-ALUMINIU_v1",
  family_id: "litere_volumetrice",
  family_name: "Litere volumetrice",
  description: "Modul intern runtime",
  db_active: true,
  quote_offerable: false,
  runtime_module: true,
  is_parent: false,
  has_modules: false,
  parent_codes: ["TPL-VOLUMETRIC-LETTERS_v2"],
  module_codes: [],
  status: "runtime_module",
  status_reason: "runtime_module_only",
};

describe("NewIntakeDialog offer method and Product System template wizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockClientsList.mockResolvedValue([]);
    mockClientsCreate.mockResolvedValue({
      id: 1,
      name: "STAGING TEST CLIENT",
      contact_person: "QA User",
    });
    mockIntakesCreate.mockResolvedValue({ id: 10 });
    mockEnsureIntakeV6Workspace.mockResolvedValue({ id: "workspace-1", workspace_code: "IV6-TEST" });
    mockAvailabilityList.mockResolvedValue({
      items: [OFFERABLE_TEMPLATE, RUNTIME_MODULE_TEMPLATE],
      total: 2,
      offerable_count: 1,
      runtime_module_count: 1,
    });
  });

  function renderDialog(onCreated = vi.fn()) {
    return render(
      <NewIntakeDialog open={true} onClose={vi.fn()} onCreated={onCreated} />
    );
  }

  async function selectMethodAndContinue() {
    fireEvent.click(await screen.findByRole("button", { name: /SVG Analyzer - Intake V6/i }));
    fireEvent.click(screen.getByRole("button", { name: /Continuă/i }));
    await screen.findByText(/Template-uri active pentru ofertare/i);
  }

  async function moveToDetailsStep() {
    await selectMethodAndContinue();
    fireEvent.click(screen.getByRole("button", { name: /Continuă/i }));
    await screen.findByText(/Alege un client existent/i);
  }

  it("opens on Pas 1 Modalitate ofertare", () => {
    renderDialog();

    expect(screen.getByText(/Alege modalitatea de ofertare/i)).toBeInTheDocument();
    expect(screen.queryByText(/Alege un client existent/i)).not.toBeInTheDocument();
  });

  it("shows SVG Analyzer - Intake V6 as the active method", async () => {
    renderDialog();

    expect(await screen.findByRole("button", { name: /SVG Analyzer - Intake V6/i })).toBeInTheDocument();
    expect(screen.getByText("Activ")).toBeInTheDocument();
  });

  it("does not continue without selecting an offer method", () => {
    renderDialog();

    expect(screen.getByRole("button", { name: /Continuă/i })).toBeDisabled();
  });

  it("loads Product System templates from availability API", async () => {
    renderDialog();
    await selectMethodAndContinue();

    expect(mockAvailabilityList).toHaveBeenCalledWith({
      offerable_only: true,
      include_runtime_modules: false,
      include_archived: false,
    });
  });

  it("shows only quote_offerable templates and hides runtime modules", async () => {
    renderDialog();
    await selectMethodAndContinue();

    const list = screen.getByTestId("offerable-template-list");
    expect(within(list).getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(within(list).queryByText("TPL-VOLUM-ALUMINIU_v1")).not.toBeInTheDocument();
  });

  it("does not use blocked archive wording", async () => {
    renderDialog();
    await selectMethodAndContinue();

    const blockedArchiveWord = new RegExp(["dez", "arhivat"].join(""), "i");
    expect(screen.queryByText(blockedArchiveWord)).not.toBeInTheDocument();
  });

  it("sends offer_method and selected_template_code to Intake V6 ensure", async () => {
    const onCreated = vi.fn();
    renderDialog(onCreated);
    await moveToDetailsStep();

    fireEvent.click(screen.getByRole("button", { name: "Client Temporar" }));
    fireEvent.change(screen.getByPlaceholderText(/SC Exemplu SRL sau Ion Popescu/i), {
      target: { value: "STAGING TEST CLIENT" },
    });
    fireEvent.change(
      screen.getByPlaceholderText(/Litere volumetrice pentru fațadă/i),
      { target: { value: "Litere volumetrice pentru fațadă magazin" } }
    );
    fireEvent.click(screen.getByRole("button", { name: /Creează Cerere/i }));

    await waitFor(() => {
      expect(mockEnsureIntakeV6Workspace).toHaveBeenCalledTimes(1);
    });

    const intakePayload = mockIntakesCreate.mock.calls[0][0];
    const [intakeCode, ensurePayload] = mockEnsureIntakeV6Workspace.mock.calls[0];
    expect(intakeCode).toMatch(/^IR-/);
    expect(intakePayload).toEqual(
      expect.objectContaining({
        product_family: "litere_volumetrice",
        confirmed_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      })
    );
    expect(ensurePayload).toEqual({
      offer_method: "svg_analyzer_intake_v6",
      selected_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      source: "work_intake_new_request",
    });
    expect(onCreated).toHaveBeenCalledWith(
      expect.stringMatching(/^IR-/),
      "litere_volumetrice",
      "workspace-1",
      "TPL-VOLUMETRIC-LETTERS_v2"
    );
  });
});