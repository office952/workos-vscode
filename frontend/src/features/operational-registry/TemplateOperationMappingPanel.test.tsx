import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TemplateOperationMappingPanel } from "./TemplateOperationMappingPanel";

vi.mock("@/api/operationalRegistry", () => ({
  operationalRegistryApi: {
    getCatalog: vi.fn().mockResolvedValue({
      skills: [{ skill_code: "SK_ASSEMBLY", label_ro: "Ansamblare", category: "production" }],
      workcenters: [
        { workcenter_code: "WC_ASSEMBLY", label_ro: "Ansamblare", category: "production" },
      ],
      resources: [
        {
          resource_code: "WA-ASSEMBLY-01",
          name: "Masă ansamblare 1",
          machine_type: "work_area",
          resource_kind: "work_area",
          workcenter_code: "WC_ASSEMBLY",
          operational_status: "active",
          is_available: true,
          is_active: true,
          capabilities: [],
          capacity_metadata: {},
        },
      ],
      suggested_operation_aliases: {
        assembly_letters: "assembly",
        volumetric_letter_assembly: "assembly",
      },
      authorization_modes: ["skill", "explicit", "hybrid"],
    }),
    listEmployees: vi.fn().mockResolvedValue({
      items: [
        {
          id: 10,
          name: "Putaru Sandu",
          role: "Montator",
          department: "Producție",
          status: "active",
          employee_type: "productive",
          user_id: null,
          salary_amount: null,
          salary_currency: "RON",
          salary_period: "monthly",
          skill_codes: ["SK_ASSEMBLY"],
          workcenter_codes: ["WC_ASSEMBLY"],
          resource_codes: [],
        },
      ],
      total: 1,
    }),
    listOperationMappings: vi.fn().mockResolvedValue({
      items: [
        {
          operation_code: "assembly",
          required_skill_codes: ["SK_ASSEMBLY"],
          allowed_workcenter_codes: ["WC_ASSEMBLY"],
          allowed_resource_codes: ["WA-ASSEMBLY-01"],
          authorization_mode: "hybrid",
          default_resource_code: null,
          product_system_aliases: [
            "assembly_letters",
            "volumetric_letter_assembly",
            "painting",
          ],
          authorized_employee_ids: [10, 11],
          notes: null,
        },
      ],
      total: 1,
    }),
    getEligibleEmployeesForOperation: vi.fn().mockResolvedValue({
      operation_code: "assembly_letters",
      resolved_operation_code: "assembly",
      authorization_mode: "hybrid",
      total: 2,
      items: [
        { id: 10, name: "Putaru Sandu", eligibility: "authorized" },
        { id: 11, name: "Vali Colantator", eligibility: "authorized" },
      ],
    }),
    upsertOperationMapping: vi.fn(),
  },
}));

describe("TemplateOperationMappingPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("finishes loading and shows registry mapping with aliases", async () => {
    render(
      <TemplateOperationMappingPanel
        operations={[
          { code: "assembly_letters", label: "Asamblare litere" },
          { code: "painting", label: "Vopsire" },
        ]}
      />
    );

    expect(await screen.findByText(/Registry code:/i)).toBeInTheDocument();
    expect(screen.getAllByText("assembly").length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue(/assembly_letters/)).toBeInTheDocument();
    expect(screen.queryByText(/^Se încarcă…$/)).not.toBeInTheDocument();
  });

  it("shows eligibility preview for selected operation", async () => {
    render(
      <TemplateOperationMappingPanel
        operations={[{ code: "assembly_letters", label: "Asamblare litere" }]}
      />
    );

    expect(await screen.findByText(/Pool eligibil/i)).toBeInTheDocument();
    expect(screen.getAllByText("Putaru Sandu").length).toBeGreaterThan(0);
  });
});
