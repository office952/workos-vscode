import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import FieldInstallationTeamPanel from "@/components/workos/FieldInstallationTeamPanel";

vi.mock("@/api/operationalRegistry", () => ({
  operationalRegistryApi: {
    listFieldInstallationTeams: vi.fn().mockResolvedValue({ items: [], total: 0, installation_ref: "ORDER-42" }),
    listActiveEmployees: vi.fn().mockResolvedValue({
      items: [
        {
          id: 1,
          name: "Putaru Sandu",
          role: "Montator",
          department: "Producție",
          status: "active",
          employee_type: "internal",
          user_id: null,
          skill_codes: ["SK_FIELD_INSTALLER", "SK_ASSEMBLY"],
          workcenter_codes: ["WC_FIELD_INSTALLATION"],
          resource_codes: [],
        },
      ],
      total: 1,
    }),
    getOperationMapping: vi.fn().mockResolvedValue({
      operation_code: "field_installation",
      required_skill_codes: ["SK_FIELD_INSTALLER"],
      allowed_workcenter_codes: ["WC_FIELD_INSTALLATION"],
      allowed_resource_codes: [],
      notes: "Montaj teren",
    }),
    createFieldInstallationTeam: vi.fn(),
    updateFieldInstallationTeam: vi.fn(),
    addFieldInstallationTeamMember: vi.fn(),
    removeFieldInstallationTeamMember: vi.fn(),
  },
}));

describe("FieldInstallationTeamPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders field_installation section without salary fields", async () => {
    render(<FieldInstallationTeamPanel orderId={42} orderCode="ORD-0042" visible />);
    expect(await screen.findByText(/Montaj teren/i)).toBeInTheDocument();
    expect(screen.getByText(/montaj_autocolant/i)).toBeInTheDocument();
    expect(screen.queryByText(/RON/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/salariu/i)).not.toBeInTheDocument();
  });
});
