import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import TemplateWorkspaceLayout from "./TemplateWorkspaceLayout";
import WorkspaceMainColumn from "./WorkspaceMainColumn";
import WorkspaceSidePanel from "./WorkspaceSidePanel";

describe("TemplateWorkspaceLayout", () => {
  it("renders main and side regions", () => {
    render(
      <TemplateWorkspaceLayout
        main={
          <WorkspaceMainColumn>
            <div data-testid="main-child">Main</div>
          </WorkspaceMainColumn>
        }
        side={
          <WorkspaceSidePanel>
            <div data-testid="side-child">Side</div>
          </WorkspaceSidePanel>
        }
      />
    );
    expect(screen.getByTestId("template-workspace-layout")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-main-column")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-side-panel")).toBeInTheDocument();
    expect(screen.getByTestId("main-child")).toBeInTheDocument();
    expect(screen.getByTestId("side-child")).toBeInTheDocument();
  });
});
