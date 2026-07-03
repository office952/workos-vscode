import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders quote accepted with correct label and emerald tone", () => {
    render(<StatusBadge domain="quote" status="accepted" />);
    const badge = screen.getByText("Acceptat");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
    expect(badge.className).toMatch(/emerald/);
  });

  it("renders quote priced with violet tone", () => {
    render(<StatusBadge domain="quote" status="priced" />);
    const badge = screen.getByText("Prețuit");
    expect(badge).toHaveAttribute("data-status-tone", "violet");
    expect(badge.className).toMatch(/purple/);
  });

  it("renders quote draft with slate tone", () => {
    render(<StatusBadge domain="quote" status="draft" />);
    const badge = screen.getByText("Draft");
    expect(badge).toHaveAttribute("data-status-tone", "slate");
    expect(badge.className).toMatch(/slate/);
  });

  it("renders quote sent and trimisa with blue tone", () => {
    const { rerender } = render(<StatusBadge domain="quote" status="sent" />);
    expect(screen.getByText("Trimis")).toHaveAttribute("data-status-tone", "blue");

    rerender(<StatusBadge domain="quote" status="trimisa" />);
    expect(screen.getByText("Trimis")).toHaveAttribute("data-status-tone", "blue");
  });

  it("renders quote accepted and acceptata with emerald tone", () => {
    const { rerender } = render(<StatusBadge domain="quote" status="accepted" />);
    expect(screen.getByText("Acceptat")).toHaveAttribute("data-status-tone", "emerald");

    rerender(<StatusBadge domain="quote" status="acceptata" />);
    expect(screen.getByText("Acceptat")).toHaveAttribute("data-status-tone", "emerald");
  });

  it("renders quote rejected and refuzata with red tone", () => {
    const { rerender } = render(<StatusBadge domain="quote" status="rejected" />);
    expect(screen.getByText("Respins")).toHaveAttribute("data-status-tone", "red");

    rerender(<StatusBadge domain="quote" status="refuzata" />);
    expect(screen.getByText("Respins")).toHaveAttribute("data-status-tone", "red");
  });

  it("renders quote expired and expirata with orange tone", () => {
    const { rerender } = render(<StatusBadge domain="quote" status="expired" />);
    expect(screen.getByText("Expirat")).toHaveAttribute("data-status-tone", "orange");

    rerender(<StatusBadge domain="quote" status="expirata" />);
    expect(screen.getByText("Expirat")).toHaveAttribute("data-status-tone", "orange");
  });

  it("falls back to slate for null quote status without throwing", () => {
    expect(() => {
      render(<StatusBadge domain="quote" status={null} />);
    }).not.toThrow();

    expect(screen.getByText("Necunoscut")).toHaveAttribute("data-status-tone", "slate");
  });

  it("renders order locked with violet tone", () => {
    render(<StatusBadge domain="order" status="locked" />);
    const badge = screen.getByText("Înghețat");
    expect(badge).toHaveAttribute("data-status-tone", "violet");
    expect(badge.className).toMatch(/purple/);
  });

  it("renders order in_execution with emerald tone", () => {
    render(<StatusBadge domain="order" status="in_execution" />);
    const badge = screen.getByText("În execuție");
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
    expect(badge.className).toMatch(/emerald/);
  });

  it("renders order cancelled with red tone", () => {
    render(<StatusBadge domain="order" status="cancelled" />);
    const badge = screen.getByText("Anulat");
    expect(badge).toHaveAttribute("data-status-tone", "red");
    expect(badge.className).toMatch(/red/);
  });

  it("renders order anulat alias with red tone", () => {
    render(<StatusBadge domain="order" status="anulat" />);
    expect(screen.getByText("Anulat")).toHaveAttribute("data-status-tone", "red");
  });

  it("renders executionTask assigned with blue tone", () => {
    render(<StatusBadge domain="executionTask" status="assigned" />);
    const badge = screen.getByText("Alocat");
    expect(badge).toHaveAttribute("data-status-tone", "blue");
    expect(badge.className).toMatch(/blue/);
  });

  it("renders executionTask in_progress and running with emerald tone", () => {
    const { rerender } = render(
      <StatusBadge domain="executionTask" status="in_progress" />,
    );
    expect(screen.getByText("În lucru")).toHaveAttribute("data-status-tone", "emerald");

    rerender(<StatusBadge domain="executionTask" status="running" />);
    expect(screen.getByText("În lucru")).toHaveAttribute("data-status-tone", "emerald");
  });

  it("renders executionTask done and completed with emerald tone", () => {
    const { rerender } = render(
      <StatusBadge domain="executionTask" status="done" />,
    );
    expect(screen.getByText("Finalizat")).toHaveAttribute("data-status-tone", "emerald");

    rerender(<StatusBadge domain="executionTask" status="completed" />);
    expect(screen.getByText("Finalizat")).toHaveAttribute("data-status-tone", "emerald");
  });

  it("renders executionTask blocked with red tone", () => {
    render(<StatusBadge domain="executionTask" status="blocked" />);
    const badge = screen.getByText("Blocat");
    expect(badge).toHaveAttribute("data-status-tone", "red");
    expect(badge.className).toMatch(/red/);
  });

  it("renders payment paid with emerald tone", () => {
    render(<StatusBadge domain="payment" status="paid" />);
    const badge = screen.getByText("Plătit");
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
    expect(badge.className).toMatch(/emerald/);
  });

  it("falls back to slate for unknown status without throwing", () => {
    expect(() => {
      render(<StatusBadge domain="quote" status="totally_unknown" />);
    }).not.toThrow();

    const badge = screen.getByText("Totally Unknown");
    expect(badge).toHaveAttribute("data-status-tone", "slate");
    expect(badge.className).toMatch(/slate/);
  });

  it("falls back to slate for null order status without throwing", () => {
    expect(() => {
      render(<StatusBadge domain="order" status={null} />);
    }).not.toThrow();

    expect(screen.getByText("Necunoscut")).toHaveAttribute("data-status-tone", "slate");
  });

  it("supports custom label override", () => {
    render(
      <StatusBadge
        domain="quote"
        status="accepted"
        label="Ofertă acceptată manual"
      />,
    );
    expect(screen.getByText("Ofertă acceptată manual")).toBeInTheDocument();
    expect(screen.queryByText("Acceptat")).not.toBeInTheDocument();
  });

  it("applies different size classes for sm, md, and lg", () => {
    const { rerender } = render(
      <StatusBadge domain="quote" status="draft" size="sm" />,
    );
    expect(screen.getByText("Draft").className).toMatch(/text-\[10px\]/);

    rerender(<StatusBadge domain="quote" status="draft" size="md" />);
    expect(screen.getByText("Draft").className).toMatch(/text-xs/);

    rerender(<StatusBadge domain="quote" status="draft" size="lg" />);
    expect(screen.getByText("Draft").className).toMatch(/text-sm/);
  });

  it("renders intake ready_for_quote with emerald tone", () => {
    render(<StatusBadge domain="intake" status="ready_for_quote" />);
    const badge = screen.getByText("Gata pt. Ofertă");
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
    expect(badge.className).toMatch(/emerald/);
  });

  it("renders intake needs_info with amber tone", () => {
    render(<StatusBadge domain="intake" status="needs_info" />);
    const badge = screen.getByText("Lipsă Info");
    expect(badge).toHaveAttribute("data-status-tone", "amber");
    expect(badge.className).toMatch(/amber/);
  });

  it("falls back to slate for unknown intake status without throwing", () => {
    expect(() => {
      render(<StatusBadge domain="intake" status="mystery_status" />);
    }).not.toThrow();

    const badge = screen.getByText("Mystery Status");
    expect(badge).toHaveAttribute("data-status-tone", "slate");
  });

  it("renders payment partial with orange tone", () => {
    render(<StatusBadge domain="payment" status="partial" />);
    const badge = screen.getByText("Parțial plătit");
    expect(badge).toHaveAttribute("data-status-tone", "orange");
    expect(badge.className).toMatch(/orange/);
  });

  it("renders payment missing_base with red warning tone", () => {
    render(<StatusBadge domain="payment" status="missing_base" />);
    const badge = screen.getByText("Bază lipsă");
    expect(badge).toHaveAttribute("data-status-tone", "red");
    expect(badge.className).toMatch(/red/);
  });

  it("falls back to slate for unknown payment status without throwing", () => {
    expect(() => {
      render(<StatusBadge domain="payment" status={null} />);
    }).not.toThrow();

    expect(screen.getByText("Necunoscut")).toHaveAttribute("data-status-tone", "slate");
  });

  it("renders productSystem active with emerald tone", () => {
    render(<StatusBadge domain="productSystem" status="active" />);
    const badge = screen.getByText("Activ");
    expect(badge).toHaveAttribute("data-status-tone", "emerald");
    expect(badge).toHaveAttribute("data-status-domain", "productSystem");
  });

  it("renders productSystem archived with slate tone", () => {
    render(<StatusBadge domain="productSystem" status="archived" />);
    expect(screen.getByText("Arhivat")).toHaveAttribute("data-status-tone", "slate");
  });

  it("renders productSystem needs_owner_review with orange tone", () => {
    render(<StatusBadge domain="productSystem" status="needs_owner_review" />);
    expect(screen.getByText("Necesită owner")).toHaveAttribute("data-status-tone", "orange");
  });

  it("falls back to slate for null productSystem status without throwing", () => {
    expect(() => {
      render(<StatusBadge domain="productSystem" status={null} />);
    }).not.toThrow();

    expect(screen.getByText("Necunoscut")).toHaveAttribute("data-status-tone", "slate");
  });

  it("renders pricing owner_confirmed and ready with emerald tone", () => {
    const { rerender } = render(
      <StatusBadge domain="pricing" status="owner_confirmed" />,
    );
    expect(screen.getByText("Owner-confirmed")).toHaveAttribute("data-status-tone", "emerald");

    rerender(<StatusBadge domain="pricing" status="ready" />);
    expect(screen.getByText("Pregătit")).toHaveAttribute("data-status-tone", "emerald");
  });

  it("renders pricing needs_review and needs_owner_review with amber tone", () => {
    const { rerender } = render(
      <StatusBadge domain="pricing" status="needs_review" />,
    );
    expect(screen.getByText("Necesită verificare")).toHaveAttribute("data-status-tone", "amber");

    rerender(<StatusBadge domain="pricing" status="needs_owner_review" />);
    expect(screen.getByText("Necesită owner")).toHaveAttribute("data-status-tone", "amber");
  });

  it("renders pricing missing_price and no_price with red tone", () => {
    const { rerender } = render(
      <StatusBadge domain="pricing" status="missing_price" />,
    );
    expect(screen.getByText("Lipsă preț")).toHaveAttribute("data-status-tone", "red");

    rerender(<StatusBadge domain="pricing" status="no_price" />);
    expect(screen.getByText("Preț lipsă")).toHaveAttribute("data-status-tone", "red");
  });

  it("renders pricing archived with slate tone", () => {
    render(<StatusBadge domain="pricing" status="archived" />);
    expect(screen.getByText("Arhivat")).toHaveAttribute("data-status-tone", "slate");
  });

  it("falls back to slate for unknown pricing status without throwing", () => {
    expect(() => {
      render(<StatusBadge domain="pricing" status={null} />);
    }).not.toThrow();

    expect(screen.getByText("Necunoscut")).toHaveAttribute("data-status-tone", "slate");
  });
});
