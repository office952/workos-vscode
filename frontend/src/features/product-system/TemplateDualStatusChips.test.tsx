import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { TemplateDualStatusChips } from "./TemplateDualStatusChips";

vi.mock("@/api/productTemplatePublication", () => ({
  getProductTemplatePublication: vi.fn(async () => ({
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    template_id: 1,
    db_active: true,
    publication_status: "DRAFT",
    effective_status: "DRAFT",
    legacy_unspecified: false,
    offerability_gate: "blocked",
    publish_allowed: false,
    publish_blockers: ["inactive_aluminiu_child"],
    allowed_actions: ["mark_validated"],
    active_is_not_published: true,
    contract_version: "product_template_publication_v1",
  })),
}));

describe("TemplateDualStatusChips", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Build and Publicare axes separately with activ≠publicat", async () => {
    render(<TemplateDualStatusChips templateCode="TPL-VOLUMETRIC-LETTERS_v2" dbActive />);
    expect(screen.getByTestId("template-dual-status-build")).toHaveTextContent(/Build activ/i);
    await waitFor(() => {
      expect(screen.getByTestId("template-dual-status-publication")).toHaveTextContent(/Publicare DRAFT/i);
    });
    expect(screen.getByTestId("template-dual-status-publication")).toHaveTextContent(/blocată/i);
    expect(screen.getByTestId("template-dual-status-active-ne-published")).toBeTruthy();
  });
});
