import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import QuoteCommercialActionPanel from "./QuoteCommercialActionPanel";
import type { Quote } from "@/lib/mockData";

const baseQuote: Quote = {
  id: "Q-BADGE-001",
  dbId: 1,
  client: "Badge Client",
  contactPerson: "Contact",
  assignedTo: "Operator",
  status: "priced",
  version: 1,
  createdAt: "2026-06-01T00:00:00Z",
  validUntil: "2026-06-30",
  subtotal: 1000,
  discount: 0,
  discountPct: 0,
  totalBeforeVAT: 1000,
  vat: 190,
  grandTotal: 1190,
  marginPct: 30,
  lineItems: [],
  notes: "",
};

describe("QuoteCommercialActionPanel badge adoption", () => {
  it("renders design-system StatusBadge with preserved RO label", () => {
    render(
      <MemoryRouter>
        <QuoteCommercialActionPanel quote={baseQuote} />
      </MemoryRouter>,
    );

    const wrapper = screen.getByTestId("quote-commercial-status-label");
    expect(wrapper).toHaveTextContent("Calculată");

    const badge = wrapper.querySelector("[data-status-domain]");
    expect(badge).toHaveAttribute("data-status-domain", "quote");
    expect(badge).toHaveAttribute("data-status", "priced");
  });
});
