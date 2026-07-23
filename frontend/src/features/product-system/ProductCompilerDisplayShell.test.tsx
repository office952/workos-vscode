import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProductCompilerDisplayShell } from "./ProductCompilerDisplayShell";
import { ExecutionPlanStatesStrip } from "@/components/execution/ExecutionPlanStatesStrip";

describe("ProductCompilerDisplayShell", () => {
  it("renders Product Compiler relation and stage chips", () => {
    render(<ProductCompilerDisplayShell stage="both" />);
    expect(screen.getByTestId("product-compiler-display-shell")).toBeInTheDocument();
    expect(screen.getByTestId("product-compiler-stage-chips")).toBeInTheDocument();
    expect(screen.getByText(/Product Template → Module produs/i)).toBeInTheDocument();
  });
});

describe("ExecutionPlanStatesStrip", () => {
  it("shows Preview → Draft Plan → Operational Plan with operational blocked by default", () => {
    render(<ExecutionPlanStatesStrip />);
    expect(screen.getByTestId("execution-plan-states-strip")).toHaveAttribute("data-active-state", "preview");
    expect(screen.getByTestId("execution-plan-state-preview")).toHaveAttribute("data-active", "true");
    expect(screen.getByTestId("execution-plan-state-draft")).toBeInTheDocument();
    expect(screen.getByTestId("execution-plan-state-operational")).toHaveAttribute("data-blocked", "true");
  });
});
