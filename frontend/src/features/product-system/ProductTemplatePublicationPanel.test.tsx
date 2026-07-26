import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
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
    // Dishonest GET — UI must still fail-closed via readiness.
    publish_allowed: true,
    publish_blockers: [],
    allowed_actions: ["enter_draft", "publish"],
    active_is_not_published: true,
    contract_version: "product_template_publication_v1",
  })),
  transitionProductTemplatePublication: vi.fn(),
}));

describe("ProductTemplatePublicationPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: RequestInfo) => {
        if (String(url).includes("e2e-readiness")) {
          return new Response(
            JSON.stringify({
              verdict: "BLOCKED",
              e2e_ready: false,
              known_conflicts: ["required_inactive_child"],
              findings: [
                {
                  blocking: true,
                  message: "Required inactive child TPL-VOLUM-ALUMINIU_v1",
                },
              ],
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response("{}", { status: 200 });
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fail-closes Publică when readiness BLOCKED even if publish_allowed is true", async () => {
    render(<ProductTemplatePublicationPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    await waitFor(() => {
      expect(screen.getByTestId("product-template-publication-status")).toHaveTextContent(
        "LEGACY_UNSPECIFIED",
      );
    });
    expect(screen.getByTestId("product-template-publication-blocked-banner")).toHaveTextContent(
      /Publicare blocată/i,
    );
    expect(screen.getByTestId("product-template-publication-primary-blocker")).toHaveTextContent(
      /Aluminiu/i,
    );
    const publish = screen.getByTestId("product-template-publication-action-publish");
    expect(publish).toBeDisabled();
    expect(screen.getByTestId("product-template-publication-publish-disabled-reason")).toHaveTextContent(
      /Publică dezactivat/i,
    );
  });
});
