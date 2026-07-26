import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { RuntimeStatusDetails } from "@/components/workos/RuntimeStatusDetails";
import { EMPTY_RUNTIME_TRUTH_SNAPSHOT } from "@/types/runtimeStatus";

describe("RuntimeStatusDetails", () => {
  it("renders Romanian detail rows without raw JSON primary content", () => {
    render(
      <RuntimeStatusDetails
        snapshot={{
          ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
          backend: {
            state: "warning",
            rawStatus: "warning",
            checkedAt: "2026-07-17T05:00:00.000Z",
            lastSuccessfulAt: "2026-07-17T05:00:00.000Z",
          },
          database: { state: "unknown", source: "none" },
          environment: { state: "staging", rawValue: "staging", serviceVersion: "BUILD_25" },
          diagnostics: { authorized: false, available: false, httpStatus: 403 },
          stale: false,
        }}
        lastError={null}
      />,
    );

    expect(screen.getByTestId("runtime-status-details")).toHaveTextContent("Detalii stare sistem");
    expect(screen.getByTestId("runtime-details-env")).toHaveTextContent("Staging");
    expect(screen.getByTestId("runtime-details-backend")).toHaveTextContent("Backend cu avertisment");
    expect(screen.getByTestId("runtime-details-db")).toHaveTextContent(/neverificat/i);
    expect(screen.getByTestId("runtime-details-diagnostics-message")).toHaveTextContent(
      "Nu ai permisiune pentru diagnostice detaliate",
    );
    expect(screen.getByTestId("runtime-details-http")).toHaveTextContent("403");
    expect(screen.queryByText(/\{[\s\S]*"status"/)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/Ã.|�/);
  });

  it("shows stale and last-known labels", () => {
    render(
      <RuntimeStatusDetails
        snapshot={{
          ...EMPTY_RUNTIME_TRUTH_SNAPSHOT,
          backend: {
            state: "unavailable",
            lastSuccessfulAt: "2026-07-17T04:00:00.000Z",
            checkedAt: "2026-07-17T05:00:00.000Z",
            errorKind: "NETWORK_ERROR",
          },
          database: { state: "unknown", source: "none" },
          environment: { state: "local" },
          diagnostics: { authorized: null, available: null },
          stale: true,
        }}
        lastError="NETWORK_ERROR"
      />,
    );

    expect(screen.getByTestId("runtime-details-stale")).toHaveTextContent("Stare învechită");
    expect(screen.getByTestId("runtime-details-last-known")).toHaveTextContent("Ultima stare cunoscută");
    expect(screen.getByTestId("runtime-details-error")).toHaveTextContent("NETWORK_ERROR");
  });

  it("handles missing optional fields without crashing", () => {
    expect(() =>
      render(
        <RuntimeStatusDetails
          snapshot={{
            backend: { state: "unknown" },
            database: { state: "unknown", source: "none" },
            environment: { state: "unknown" },
            diagnostics: { authorized: null, available: null },
            stale: false,
          }}
        />,
      ),
    ).not.toThrow();
    expect(screen.getByTestId("runtime-status-details")).toBeInTheDocument();
  });
});
