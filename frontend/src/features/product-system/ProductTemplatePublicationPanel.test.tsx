import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ProductTemplatePublicationPanel } from "./ProductTemplatePublicationPanel";

vi.mock("@/api/productTemplatePublication", () => ({
  getProductTemplatePublication: vi.fn(async () => ({
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    template_id: 1,
    db_active: true,
    publication_status: null,
    effective_status: "LEGACY_UNSPECIFIED",
    legacy_unspecified: true,
    offerability_gate: "legacy_unspecified_keeps_prior_policy",
    publish_allowed: false,
    publish_blockers: ["readiness_verdict_BLOCKED"],
    allowed_actions: ["enter_draft", "publish"],
    active_is_not_published: true,
    contract_version: "product_template_publication_v1",
  })),
  transitionProductTemplatePublication: vi.fn(),
}));

describe("ProductTemplatePublicationPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows active≠published and legacy status", async () => {
    render(<ProductTemplatePublicationPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    await waitFor(() => {
      expect(screen.getByTestId("product-template-publication-status")).toHaveTextContent(
        "LEGACY_UNSPECIFIED",
      );
    });
    expect(screen.getAllByText(/active ≠ published/i).length).toBeGreaterThan(0);
    expect(screen.getByTestId("product-template-publication-blocked-banner")).toHaveTextContent(
      /TEMPLATE PUBLICATION BLOCKED/i,
    );
    expect(screen.getByTestId("product-template-publication-action-publish")).toBeTruthy();
  });
});
