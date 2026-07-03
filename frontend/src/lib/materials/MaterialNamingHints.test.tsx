import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MaterialNamingHints } from "./MaterialNamingHints";

describe("MaterialNamingHints", () => {
  it("renders alias and usage warnings for premontaj steel name", () => {
    render(<MaterialNamingHints name="bare premontaj otel 30x30x1.5" />);
    expect(screen.getByTestId("material-naming-hints")).toBeInTheDocument();
    expect(screen.getByText(/utilizarea materialului/i)).toBeInTheDocument();
    expect(screen.getByText(/Familie recomandată/i)).toBeInTheDocument();
  });

  it("renders nothing for empty name", () => {
    const { container } = render(<MaterialNamingHints name="" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders bond canonical hint", () => {
    render(<MaterialNamingHints name="bond 3mm alb" />);
    expect(screen.getByText(/Termen detectat: "bond"/i)).toBeInTheDocument();
  });
});
