import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import type { RegistryEmployee } from "@/api/operationalRegistry";
import { OperationPoolPreviewPanel } from "./OperationPoolPreviewPanel";

const poolEmployee = (id: number, name: string): RegistryEmployee => ({
  id,
  name,
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
});

vi.mock("@/api/operationalRegistry", () => ({
  operationalRegistryApi: {
    getEligibleEmployeesForOperation: vi.fn(),
  },
}));

import { operationalRegistryApi } from "@/api/operationalRegistry";

describe("OperationPoolPreviewPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows eligible employees when alias resolves in registry", async () => {
    vi.mocked(operationalRegistryApi.getEligibleEmployeesForOperation).mockResolvedValue({
      operation_code: "volumetric_letter_assembly",
      resolved_operation_code: "assembly",
      authorization_mode: "hybrid",
      resolution: "alias",
      required_skill_codes: ["SK_ASSEMBLY"],
      allowed_workcenter_codes: ["WC_ASSEMBLY"],
      allowed_resource_codes: [],
      default_resource_code: null,
      authorized_employee_ids: [],
      total: 4,
      items: [
        { ...poolEmployee(1, "Putaru Sandu"), eligibility: "authorized" },
        { ...poolEmployee(2, "Vali Colantator"), eligibility: "authorized" },
        { ...poolEmployee(3, "Costi Modelator"), eligibility: "authorized" },
        { ...poolEmployee(4, "Andrei Goghi"), eligibility: "authorized" },
      ],
    });

    render(<OperationPoolPreviewPanel operationCode="volumetric_letter_assembly" />);

    expect(await screen.findByText(/4 eligibili/)).toBeInTheDocument();
    expect(screen.getByText("Putaru Sandu")).toBeInTheDocument();
    expect(screen.queryByText(/Niciun angajat eligibil/)).not.toBeInTheDocument();
  });

  it("shows zero pool without crashing when mapping missing", async () => {
    vi.mocked(operationalRegistryApi.getEligibleEmployeesForOperation).mockResolvedValue({
      operation_code: "unknown_op",
      resolved_operation_code: null,
      authorization_mode: "hybrid",
      resolution: "not_found",
      required_skill_codes: [],
      allowed_workcenter_codes: [],
      allowed_resource_codes: [],
      default_resource_code: null,
      authorized_employee_ids: [],
      total: 0,
      items: [],
    });

    render(<OperationPoolPreviewPanel operationCode="unknown_op" />);

    expect(await screen.findByText(/0 eligibili/)).toBeInTheDocument();
    expect(screen.getByText(/Mapping registry lipsă/i)).toBeInTheDocument();
    expect(screen.queryByText(/Niciun angajat eligibil configurat/i)).not.toBeInTheDocument();
  });
});
