import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SourceBadge } from "./SourceBadge";

describe("SourceBadge", () => {
  it("renders db as Live DB with emerald tone", () => {
    render(<SourceBadge source="db" />);
    const badge = screen.getByText("Live DB");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-source-tone", "emerald");
    expect(badge.className).toMatch(/emerald/);
  });

  it("renders empty as Live DB (gol) with muted emerald tone", () => {
    render(<SourceBadge source="empty" />);
    const badge = screen.getByText("Live DB (gol)");
    expect(badge).toHaveAttribute("data-source", "empty");
    expect(badge.className).toMatch(/emerald/);
  });

  it("renders mock as Mock Data with amber tone", () => {
    render(<SourceBadge source="mock" />);
    const badge = screen.getByText("Mock Data");
    expect(badge).toHaveAttribute("data-source-tone", "amber");
    expect(badge.className).toMatch(/amber/);
  });

  it("renders demo as Demo with amber tone", () => {
    render(<SourceBadge source="demo" />);
    const badge = screen.getByText("Demo");
    expect(badge).toHaveAttribute("data-source-tone", "amber");
    expect(badge.className).toMatch(/amber/);
  });

  it("renders error as Source Error with red tone", () => {
    render(<SourceBadge source="error" />);
    const badge = screen.getByText("Source Error");
    expect(badge).toHaveAttribute("data-source-tone", "red");
    expect(badge.className).toMatch(/red/);
  });

  it("renders loading safely with slate tone", () => {
    expect(() => {
      render(<SourceBadge source="loading" />);
    }).not.toThrow();

    const badge = screen.getByText("Loading");
    expect(badge).toHaveAttribute("data-source-tone", "slate");
    expect(badge.className).toMatch(/slate/);
  });

  it("renders mixed as Mixed Source with non-live slate tone", () => {
    render(<SourceBadge source="mixed" />);
    const badge = screen.getByText("Mixed Source");
    expect(badge).toHaveAttribute("data-source", "mixed");
    expect(badge.className).toMatch(/slate/);
    expect(badge.className).not.toMatch(/emerald-900\/50/);
  });

  it("falls back safely for unknown or null source without throwing", () => {
    expect(() => {
      render(<SourceBadge source={null} />);
    }).not.toThrow();

    const nullBadge = screen.getByText("Unknown Source");
    expect(nullBadge).toHaveAttribute("data-source-tone", "slate");

    render(<SourceBadge source="something_weird" />);
    const unknownBadge = screen.getByText("something_weird");
    expect(unknownBadge).toHaveAttribute("data-source-tone", "slate");
  });
});
