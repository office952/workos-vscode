import type { ComponentProps } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import QuoteWizard from "./QuoteWizard";

vi.mock("@/hooks/useCompanyVatPct", () => ({
  useCompanyVatPct: () => ({ vatPct: 21, loading: false, error: null, reload: vi.fn() }),
}));

vi.mock("@/lib/api", () => ({
  productTemplatesApi: {
    list: vi.fn().mockResolvedValue([
      { id: 1, template_code: "TPL-BANNER-STANDARD", name: "Banner" },
    ]),
  },
  intakesApi: { list: vi.fn().mockResolvedValue([]) },
}));

vi.mock("@/lib/activeTemplateScope", () => ({
  filterActiveTemplatesForQuote: (rows: unknown[]) => rows,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE: "TPL-VOLUMETRIC-LETTERS",
}));

function renderWizard(props: Partial<ComponentProps<typeof QuoteWizard>> = {}) {
  return render(
    <MemoryRouter>
      <QuoteWizard open onClose={() => undefined} {...props} />
    </MemoryRouter>
  );
}

async function goToPricingStep() {
  await waitFor(() => {
    expect(screen.getByText("Continuă")).not.toBeDisabled();
  });
  fireEvent.click(screen.getByText("Continuă"));
  await waitFor(() => {
    expect(screen.getByText("Continuă")).not.toBeDisabled();
  });
  fireEvent.click(screen.getByText("Continuă"));
  await waitFor(() => {
    expect(screen.getByText("Continuă")).not.toBeDisabled();
  });
  fireEvent.click(screen.getByText("Continuă"));
}

describe("QuoteWizard VAT governance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows read-only Settings VAT on pricing step, no editable VAT input", async () => {
    renderWizard({ initialClientName: "VAT smoke" });
    await goToPricingStep();
    await waitFor(() => {
      expect(screen.getByTestId("quote-wizard-settings-vat")).toHaveTextContent(
        "TVA aplicat din Settings: 21%"
      );
    });
    expect(screen.queryByLabelText(/^TVA$/i)).not.toBeInTheDocument();
  });
});
