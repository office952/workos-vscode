import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LocalApiCompatibilityBannerView } from "./LocalApiCompatibilityBanner";
import type { LocalCompatSnapshot } from "@/lib/localApiCompatibility";

const incompatible: LocalCompatSnapshot = {
  kind: "incompatible",
  apiBase: "http://127.0.0.1:8001",
  httpStatus: 404,
  service: null,
  contract: null,
  apiVersion: null,
  capabilities: [],
  missingCapabilities: ["system.local_compatibility"],
  detail: "stale",
  recommendedStep: "reporneste backendul",
  probedAt: "2026-07-19T00:00:00.000Z",
};

describe("LocalApiCompatibilityBannerView", () => {
  it("renders Romanian incompatible message with API base", () => {
    render(<LocalApiCompatibilityBannerView snapshot={incompatible} />);
    expect(screen.getByTestId("local-api-compat-title").textContent).toMatch(/incompatibil/i);
    expect(screen.getByTestId("local-api-compat-message").textContent).toMatch(
      /backend vechi sau diferit/i,
    );
    expect(screen.getByTestId("local-api-compat-api-base").textContent).toBe(
      "http://127.0.0.1:8001",
    );
  });

  it("renders nothing when compatible", () => {
    const { container } = render(
      <LocalApiCompatibilityBannerView
        snapshot={{ ...incompatible, kind: "ok", missingCapabilities: [], detail: "ok" }}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
