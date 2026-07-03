import { fireEvent, render, screen } from "@testing-library/react";

import { beforeEach, describe, expect, it, vi } from "vitest";

import type { IntakeV6SheetQuoteMaterialCandidates } from "@/lib/intakeV6/intakeV6Api";
import IntakeV6SheetFootprintOverridePanel from "./IntakeV6SheetFootprintOverridePanel";

const putIntakeV6SheetFootprintOverride = vi.fn();

vi.mock("@/lib/intakeV6/intakeV6Api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/intakeV6/intakeV6Api")>();

  return {
    ...actual,
    putIntakeV6SheetFootprintOverride: (...args: unknown[]) => putIntakeV6SheetFootprintOverride(...args),
  };
});

function sampleCandidates(): IntakeV6SheetQuoteMaterialCandidates {
  return {
    eligible_face_area_sqm: 1.2638,
    placement_footprint_face_sqm: 1.1469,
    face_union_bbox_sqm: 2.5238,
    layout_occupied_area_sqm: 2.5238,
    full_sheet_allocation_sqm: 6.0,
    requires_manual_review: true,
    selected_quote_sheet_area_sqm: 1.2638,
    selected_quote_sheet_area_source: "eligible_area_floor",
    selection: {
      selected_source: "eligible_area_floor",
      final_area_sqm: 1.2638,
      is_applied_to_quote: false,
    },
  } as IntakeV6SheetQuoteMaterialCandidates;
}

describe("IntakeV6SheetFootprintOverridePanel", () => {
  beforeEach(() => {
    putIntakeV6SheetFootprintOverride.mockReset();
  });

  it("shows selectable footprint sources in technical details", () => {
    render(
      <IntakeV6SheetFootprintOverridePanel
        workspaceId="ws-1"
        candidates={sampleCandidates()}
        prominent
      />,
    );

    expect(screen.getByText("Verificare footprint material")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Selectare sursă footprint (detaliu tehnic)"));

    expect(screen.getByTestId("intake-v6-footprint-source-eligible_area_floor")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-footprint-source-face_union_bbox")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-footprint-source-layout_occupied_area")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-footprint-source-operator_manual_footprint")).toBeInTheDocument();

    expect(screen.getByText(/Aria pieselor eligibile — 1.2638 m²/)).toBeInTheDocument();
    expect(screen.getByText(/Face union bbox — 2.5238 m²/)).toBeInTheDocument();
  });

  it("moves placement face and physical sheet into technical details", () => {
    render(<IntakeV6SheetFootprintOverridePanel workspaceId="ws-1" candidates={sampleCandidates()} />);

    fireEvent.click(screen.getByText("Detalii tehnice footprint"));
    expect(screen.getByText(/Placement face: 1.1469 m²/)).toBeInTheDocument();
    expect(screen.getByText(/Placă fizică: 6.0000 m²/)).toBeInTheDocument();
  });

  it("shows manual inputs only when manual source selected", () => {
    render(<IntakeV6SheetFootprintOverridePanel workspaceId="ws-1" candidates={sampleCandidates()} />);

    expect(screen.queryByTestId("intake-v6-sheet-footprint-width-cm")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-footprint-source-operator_manual_footprint"));
    expect(screen.getByTestId("intake-v6-sheet-footprint-width-cm")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-sheet-footprint-save")).toBeDisabled();
  });

  it("saves face union bbox source selection", async () => {
    putIntakeV6SheetFootprintOverride.mockResolvedValue({
      area_sqm: 2.5238,
      selected_footprint_source: "face_union_bbox",
      use_for_quote_estimate: true,
    });

    render(<IntakeV6SheetFootprintOverridePanel workspaceId="ws-1" candidates={sampleCandidates()} />);

    fireEvent.click(screen.getByTestId("intake-v6-footprint-source-face_union_bbox"));
    fireEvent.click(screen.getByTestId("intake-v6-sheet-footprint-save"));

    await vi.waitFor(() => {
      expect(putIntakeV6SheetFootprintOverride).toHaveBeenCalledWith(
        "ws-1",
        expect.objectContaining({
          selected_footprint_source: "face_union_bbox",
          use_for_quote_estimate: true,
        }),
      );
    });

    expect(await screen.findByTestId("intake-v6-footprint-used-summary")).toHaveTextContent(
      "Face union bbox — 2.5238 m²",
    );
  });

  it("saves manual footprint with dimensions", async () => {
    putIntakeV6SheetFootprintOverride.mockResolvedValue({
      area_sqm: 2.7626,
      selected_footprint_source: "operator_manual_footprint",
      use_for_quote_estimate: true,
    });

    render(<IntakeV6SheetFootprintOverridePanel workspaceId="ws-1" candidates={sampleCandidates()} />);

    fireEvent.click(screen.getByTestId("intake-v6-footprint-source-operator_manual_footprint"));
    fireEvent.change(screen.getByTestId("intake-v6-sheet-footprint-width-cm"), {
      target: { value: "192.67" },
    });
    fireEvent.change(screen.getByTestId("intake-v6-sheet-footprint-height-cm"), {
      target: { value: "143.389" },
    });
    fireEvent.click(screen.getByTestId("intake-v6-sheet-footprint-save"));

    await vi.waitFor(() => {
      expect(putIntakeV6SheetFootprintOverride).toHaveBeenCalledWith(
        "ws-1",
        expect.objectContaining({
          selected_footprint_source: "operator_manual_footprint",
          width_cm: 192.67,
          height_cm: 143.389,
          use_for_quote_estimate: true,
        }),
      );
    });
  });
});