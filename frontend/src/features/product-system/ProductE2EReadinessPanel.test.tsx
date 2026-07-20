import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ProductE2EReadinessPanel } from "./ProductE2EReadinessPanel";

vi.mock("@/lib/config", () => ({
  getAPIBaseURL: () => "http://localhost:8000",
}));

describe("ProductE2EReadinessPanel", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows BUILD PASS while TEMPLATE PUBLICATION BLOCKED", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        template_code: "TPL-VOLUMETRIC-LETTERS_v2",
        mode: "static",
        verdict: "BLOCKED",
        e2e_ready: false,
        no_write: true,
        write_performed: false,
        build_closure_status: "PASS",
        template_publication_status: "BLOCKED",
        findings: [
          {
            check_id: "components.required_inactive.TPL-VOLUM-ALUMINIU_v1",
            system: "components",
            status: "BLOCKED",
            blocking: true,
            message: "Required child template TPL-VOLUM-ALUMINIU_v1 is inactive",
            evidence: { conflict_code: "required_inactive_child" },
          },
        ],
      }),
    } as Response);

    render(<ProductE2EReadinessPanel templateCode="TPL-VOLUMETRIC-LETTERS_v2" />);
    fireEvent.click(screen.getByTestId("product-e2e-readiness-static-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("product-e2e-readiness-build-closure")).toHaveTextContent(
        "BUILD PASS",
      );
    });
    expect(screen.getByTestId("product-e2e-readiness-template-publication")).toHaveTextContent(
      "TEMPLATE PUBLICATION BLOCKED",
    );
    expect(screen.getByTestId("product-e2e-readiness-build-pass-pub-blocked")).toHaveTextContent(
      /Aluminiu \(volumetric\)/,
    );
    fireEvent.click(screen.getByTestId("product-e2e-readiness-findings-toggle"));
    expect(screen.getByTestId("product-e2e-readiness-findings")).toHaveTextContent(
      /Aluminiu \(volumetric\)/,
    );
  });
});

