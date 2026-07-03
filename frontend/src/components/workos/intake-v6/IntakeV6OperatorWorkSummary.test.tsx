import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6OperatorWorkSummary from "@/components/workos/intake-v6/IntakeV6OperatorWorkSummary";
import IntakeV6OperatorWorkSummaryTechnicalDetails, {
  INTAKE_V6_NO_OCR_NOTE,
  INTAKE_V6_VECTOR_PRODUCTION_PARTS_LABEL,
} from "@/components/workos/intake-v6/IntakeV6OperatorWorkSummaryTechnicalDetails";
import { buildIntakeV6OperatorWorkSummaryCounts } from "@/lib/intakeV6/intakeV6ConfirmSummary";

describe("IntakeV6OperatorWorkSummary", () => {
  it("renders main summary without ambiguous production part count for Ana Maria-like counts", () => {
    const counts = buildIntakeV6OperatorWorkSummaryCounts({
      geometry: {
        real_letters_count: 19,
        inner_holes_count: 7,
      } as never,
      nestingPreview: {
        summary: { nestable_parts: 19, artwork_parts: 2 },
      } as never,
    });
    render(<IntakeV6OperatorWorkSummary counts={counts} layerCount={6} />);
    expect(screen.getByText("Rezumat lucrare")).toBeInTheDocument();
    expect(screen.queryByText("Piese producție")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-operator-work-summary-production-parts")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-operator-work-summary-volumetric-letters")).toHaveTextContent("19");
    expect(screen.getByTestId("intake-v6-operator-work-summary-emblem-count")).toHaveTextContent("2");
    expect(screen.queryByText("Goluri / interioare")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-operator-work-summary-inner-holes")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-operator-work-summary-layout-parts")).toHaveTextContent("21");
    expect(screen.getByTestId("intake-v6-operator-work-summary-layers")).toHaveTextContent("6");
    expect(screen.queryByText("Child parts")).not.toBeInTheDocument();
    expect(screen.queryByText("Litere reale")).not.toBeInTheDocument();
    expect(screen.queryByText(/OCR/)).not.toBeInTheDocument();
  });

  it("renders PBL-like main summary counts", () => {
    const counts = buildIntakeV6OperatorWorkSummaryCounts({
      geometry: {
        real_letters_count: 10,
        inner_holes_count: 2,
      } as never,
      nestingPreview: {
        summary: { nestable_parts: 10, artwork_parts: 1 },
      } as never,
    });
    render(<IntakeV6OperatorWorkSummary counts={counts} layerCount={3} />);
    expect(screen.getByTestId("intake-v6-operator-work-summary-volumetric-letters")).toHaveTextContent("10");
    expect(screen.getByTestId("intake-v6-operator-work-summary-emblem-count")).toHaveTextContent("1");
    expect(screen.getByTestId("intake-v6-operator-work-summary-layout-parts")).toHaveTextContent("11");
    expect(screen.getByTestId("intake-v6-operator-work-summary-layers")).toHaveTextContent("3");
  });
});

describe("IntakeV6OperatorWorkSummaryTechnicalDetails", () => {
  it("shows vector production part count and anti-OCR note in technical details", () => {
    const counts = buildIntakeV6OperatorWorkSummaryCounts({
      geometry: {
        real_letters_count: 19,
        inner_holes_count: 7,
      } as never,
      nestingPreview: {
        summary: { nestable_parts: 19, artwork_parts: 2 },
      } as never,
    });
    render(<IntakeV6OperatorWorkSummaryTechnicalDetails counts={counts} />);
    expect(screen.getByText(INTAKE_V6_VECTOR_PRODUCTION_PARTS_LABEL)).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-operator-work-summary-technical-production-parts")).toHaveTextContent(
      "19",
    );
    expect(screen.getByTestId("intake-v6-operator-work-summary-technical-no-ocr-note")).toHaveTextContent(
      INTAKE_V6_NO_OCR_NOTE,
    );
    expect(screen.queryByText("Litere reale")).not.toBeInTheDocument();
  });
});