import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6LayersWarningsPanel from "./IntakeV6LayersWarningsPanel";
import { IntakeV6WorkspaceHeaderStatusProvider } from "./IntakeV6WorkspaceHeaderStatusContext";

describe("IntakeV6LayersWarningsPanel", () => {
  it("shows compact analysis count and opens footer details", () => {
    const openFooterIssues = vi.fn();

    render(
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6LayersWarningsPanel
          report={{
            document: { widthMm: 100, heightMm: 50 },
            layers: [
              {
                id: "pseudo:maria",
                name: "maria",
                autoRole: "letter",
                warnings: ["Pseudo-layer generated from solid vector fill color cluster."],
              },
            ],
          }}
          confirmation={null}
          scopeWarnings={[]}
        />
      </IntakeV6WorkspaceHeaderStatusProvider>,
    );

    expect(screen.getByTestId("intake-v6-layers-warnings-count")).toHaveTextContent(/observa/i);
    expect(screen.queryByTestId("intake-v6-pseudo-layer-warning-summary")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-layers-warnings-open-footer"));
  });
});
