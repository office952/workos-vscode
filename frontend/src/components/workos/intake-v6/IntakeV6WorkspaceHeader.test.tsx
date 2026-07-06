import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6Header from "./atoms/IntakeV6Header";
import { IntakeV6WorkspaceHeaderStatusProvider } from "./IntakeV6WorkspaceHeaderStatusContext";
import type { IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";

function baseState(overrides: Partial<IntakeV6WorkspaceState> = {}): IntakeV6WorkspaceState {
  return {
    phase: "svg_ready",
    currentStep: "review",
    analyzerStatus: "idle",
    layerChips: [
      { layerKey: "a", label: "A", status: "confirmed" },
      { layerKey: "b", label: "B", status: "confirmed" },
    ],
    workspace: {
      id: "ws-1",
      workspace_code: "IV6-DEMO",
      template_code: "TPL-VOLUMETRIC-LETTERS",
      payload: {
        product_binding: { template_label: "Litere volumetrice" },
        svg_source: { file_name: "logo.svg", upload_status: "analyzed" },
      },
    },
    svg: { fileName: "logo.svg", fileSizeBytes: 27000 },
    ...overrides,
  } as IntakeV6WorkspaceState;
}

describe("IntakeV6Header workspace shell", () => {
  it("renders compact identity row with single workspace status badge", () => {
    render(
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6Header state={baseState()} />
      </IntakeV6WorkspaceHeaderStatusProvider>,
    );

    expect(screen.getByTestId("intake-v6-header")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-header-workspace-code")).toHaveTextContent("IV6-DEMO");
    expect(screen.getByTestId("intake-v6-header-template")).toHaveTextContent("Litere volumetrice");
    expect(screen.getByTestId("intake-v6-header-step")).toHaveTextContent("Review");

    expect(screen.queryByText("SVG ready")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-status-bar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-header-svg-file")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-progress")).toBeInTheDocument();
  });

  it("shows logo-only candidate as primary context when commercial root is not offerable", () => {
    render(
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6Header
          state={baseState({
            workspace: {
              ...baseState().workspace!,
              readiness_status: "logo_only_candidate_not_offerable",
            },
          })}
        />
      </IntakeV6WorkspaceHeaderStatusProvider>,
    );

    expect(screen.getByTestId("intake-v6-header-template")).toHaveTextContent("Logo-only candidate");
    expect(screen.getByTestId("intake-v6-header-logo-only-guard")).toHaveTextContent(
      /TPL-VOLUMETRIC-LOGO_v1 candidate\/read-only/i,
    );
    expect(screen.getByTestId("intake-v6-header-logo-only-guard")).toHaveTextContent(
      /root comercial neofertabil/i,
    );
  });

  it("keeps progress navigation visible with svg file in state", () => {
    render(
      <IntakeV6WorkspaceHeaderStatusProvider>
        <IntakeV6Header state={baseState()} />
      </IntakeV6WorkspaceHeaderStatusProvider>,
    );

    expect(screen.getByTestId("intake-v6-progress-step-layers")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-progress-step-review")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-progress-step-confirm")).toBeInTheDocument();
  });
});
