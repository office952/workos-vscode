import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Employees from "@/pages/Employees";

const mockEmployees = vi.hoisted(() => [
  {
    id: 1,
    name: "Calin Cimpean",
    role: "Operator",
    department: "Productie",
    status: "active",
    employee_type: "productive",
    valid_for_cost_engine: true,
    cost_ora_calculat: 50,
    user_id: "dev-employee-test-001",
    auth_email: "test.employee@local",
    auth_role: "employee_mobile",
    is_linked_to_user: true,
    has_mobile_access: true,
  },
  {
    id: 2,
    name: "Fara Cont",
    status: "active",
    employee_type: "productive",
    valid_for_cost_engine: false,
    is_linked_to_user: false,
    has_mobile_access: false,
  },
]);

vi.mock("@/features/operational-registry/EmployeeOperationalPanel", () => ({
  EmployeeOperationalPanel: () => null,
}));

vi.mock("@/components/workos/employees/EmployeeAdminOperationalSummary", () => ({
  default: () => <div data-testid="employee-admin-operational-summary-mock" />,
}));

vi.mock("@/api/costEngine", () => ({
  employeesApi: {
    list: vi.fn().mockResolvedValue({ items: mockEmployees, total: 2 }),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <Employees />
    </MemoryRouter>,
  );
}

describe("Employees operational admin UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows mobile access badge in list and detail", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("employees-list-item-1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employees-list-item-1"));

    expect(screen.getAllByTestId("employee-mobile-access-badge").length).toBeGreaterThan(0);
    expect(screen.getByTestId("employee-detail-mobile-access")).toHaveTextContent(/Mobile activ/i);
    expect(screen.getByTestId("employee-detail-mobile-access")).toHaveTextContent(
      /test\.employee@local/,
    );
  });

  it("filters employees without mobile access", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("employees-list-item-2")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("employees-quick-mobile-filter-no_mobile"));

    await waitFor(() => {
      expect(screen.queryByTestId("employees-list-item-1")).not.toBeInTheDocument();
      expect(screen.getByTestId("employees-list-item-2")).toBeInTheDocument();
    });
  });
});
