import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
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
    publish_blockers: ["known_conflict:TPL-VOLUM-ALUMINIU_v1"],
    allowed_actions: ["mark_validated"],
    active_is_not_published: true,
    contract_version: "product_template_publication_v1",
  })),
}));

describe("TemplateDualStatusChips", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            verdict: "BLOCKED",
            e2e_ready: false,
            known_conflicts: ["required_inactive_child"],
            findings: [
              { blocking: true, message: "Required inactive child TPL-VOLUM-ALUMINIU_v1" },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("separates catalog lifecycle from publication gate with Aluminiu primary blocker", async () => {
    render(<TemplateDualStatusChips templateCode="TPL-VOLUMETRIC-LETTERS_v2" dbActive />);
    expect(screen.getByTestId("template-dual-status-build")).toHaveTextContent(/Activ în catalog/i);
    await waitFor(() => {
      expect(screen.getByTestId("template-dual-status-publication")).toHaveTextContent(/Publicare/i);
    });
    expect(screen.getByTestId("template-dual-status-publication")).toHaveTextContent(/blocată/i);
    expect(screen.getByTestId("template-dual-status-primary-blocker")).toHaveTextContent(/Aluminiu/i);
  });
});
