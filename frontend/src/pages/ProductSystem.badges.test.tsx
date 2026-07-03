import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProductSystem from "./ProductSystem";
import type { ProductTemplateEntity } from "@/lib/api";
import { TooltipProvider } from "@/components/ui/tooltip";

function renderProductSystem() {
  return render(
    <TooltipProvider>
      <MemoryRouter initialEntries={["/product-system"]}>
        <ProductSystem />
      </MemoryRouter>
    </TooltipProvider>,
  );
}

vi.mock("@/lib/mockGuard", () => ({
  isMockEnabled: () => false,
}));

const mockTemplateList = vi.fn();

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    productTemplatesApi: {
      ...actual.productTemplatesApi,
      list: () => mockTemplateList(),
    },
    materialsApi: {
      ...actual.materialsApi,
      list: vi.fn().mockResolvedValue([]),
    },
  };
});

vi.mock("@/api/productFamilies", () => ({
  productFamiliesApi: {
    list: vi.fn().mockResolvedValue({ items: [] }),
  },
}));

const volumetricTemplate: ProductTemplateEntity = {
  id: 1,
  template_code: "TPL-VOLUMETRIC-LETTERS",
  family_name: "Litere volumetrice",
  active: true,
  components_json: "[]",
  operations_json: "[]",
  required_materials_json: "[]",
};

describe("ProductSystem design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
  });

  it("renders SourceBadge mapped from live API load mode", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByText("TPL-VOLUMETRIC-LETTERS")).toBeInTheDocument();
    });

    const sourceBadge = document.querySelector('[data-source="db"]');
    expect(sourceBadge).toBeTruthy();
    expect(sourceBadge?.textContent).toMatch(/Live DB/i);
  });

  it("renders active template status badge from design-system", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByText("TPL-VOLUMETRIC-LETTERS")).toBeInTheDocument();
    });

    const activeBadge = screen
      .getAllByText("Activ")
      .find((el) => el.getAttribute("data-status-domain") === "productSystem");
    expect(activeBadge).toBeTruthy();
    expect(activeBadge).toHaveAttribute("data-status", "active");
    expect(activeBadge).toHaveAttribute("data-status-tone", "emerald");
  });

  it("keeps TPL-VOLUMETRIC-LETTERS visible in library", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByText("TPL-VOLUMETRIC-LETTERS")).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "ProductSystem / Șabloane" })).toBeInTheDocument();
  });

});
