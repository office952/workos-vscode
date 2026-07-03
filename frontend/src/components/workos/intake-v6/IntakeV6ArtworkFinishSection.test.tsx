import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6ArtworkFinishSection, {
  INTAKE_V6_ARTWORK_VERIFY_INSTRUCTION,
} from "./IntakeV6ArtworkFinishSection";
import type { IntakeV6ArtworkFinish } from "@/lib/intakeV6/intakeV6ArtworkFinish";

const rows: IntakeV6ArtworkFinish[] = [
  {
    layer_key: "logo",
    layer_name: "Logo",
    execution_type: "print_laminate",
    color_mode: "polychrome",
    print_transparency: "standard",
    return_finish_type: "white_aluminum",
    confirmed: false,
  },
];

const confirmedRows: IntakeV6ArtworkFinish[] = [
  {
    ...rows[0]!,
    confirmed: true,
  },
];

function expandArtworkCard(layerKey: string) {
  fireEvent.click(screen.getByTestId(`intake-v6-artwork-header-${layerKey}`));
}

describe("IntakeV6ArtworkFinishSection", () => {
  it("defaults to print + laminare and allows translucent without changing execution", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={onChange} />);
    expandArtworkCard("logo");
    expect(screen.getByTestId("intake-v6-artwork-execution-logo")).toHaveTextContent("Print + laminare");
    expect(screen.getByTestId("intake-v6-artwork-cant-logo")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-artwork-translucent-logo"));
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]?.execution_type).toBe("print_laminate");
    expect(next[0]?.print_transparency).toBe("translucent");
    expect(next[0]?.confirmed).toBe(false);
  });

  it("updates emblem cant settings through return fields", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={onChange} />);
    expandArtworkCard("logo");
    fireEvent.change(screen.getByTestId("intake-v6-artwork-return-logo-depth"), {
      target: { value: "80" },
    });
    const next = onChange.mock.calls.at(-1)![0] as IntakeV6ArtworkFinish[];
    expect(next[0]?.return_depth_mm).toBe(80);
    expect(next[0]?.confirmed).toBe(false);
  });

  it("shows Confirm artwork when confirmed=false and patches confirmed=true on click", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={onChange} />);
    expandArtworkCard("logo");
    const button = screen.getByTestId("intake-v6-artwork-confirm-logo");
    expect(button).toHaveTextContent("Confirm vector atipic");
    fireEvent.click(button);
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]?.confirmed).toBe(true);
    expect(next[0]?.execution_type).toBe("print_laminate");
    expect(next[0]?.print_transparency).toBe("standard");
    expect(next[0]?.return_finish_type).toBe("white_aluminum");
  });

  it("shows Artwork confirmat when confirmed=true", () => {
    render(<IntakeV6ArtworkFinishSection rows={confirmedRows} onChange={vi.fn()} />);
    expandArtworkCard("logo");
    expect(screen.getByTestId("intake-v6-artwork-confirm-logo")).toHaveTextContent("Vector Atipic confirmat");
    expect(screen.getByTestId("intake-v6-artwork-confirmed-logo")).toHaveTextContent("OK");
  });

  it("does not force confirmed=false when only cant depth changes on a confirmed row", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={confirmedRows} onChange={onChange} />);
    expandArtworkCard("logo");
    fireEvent.change(screen.getByTestId("intake-v6-artwork-return-logo-depth"), {
      target: { value: "80" },
    });
    const next = onChange.mock.calls.at(-1)![0] as IntakeV6ArtworkFinish[];
    expect(next[0]?.return_depth_mm).toBe(80);
    expect(next[0]?.confirmed).toBe(true);
  });

  it("shows verify instruction and CTA when decision alert is visible", () => {
    const onVerify = vi.fn();
    render(
      <IntakeV6ArtworkFinishSection
        rows={rows}
        onChange={vi.fn()}
        showDecisionAlert
        onVerifyArtwork={onVerify}
      />,
    );
    expect(screen.getByTestId("intake-v6-artwork-verify-instruction")).toHaveTextContent(
      INTAKE_V6_ARTWORK_VERIFY_INSTRUCTION,
    );
    fireEvent.click(screen.getByTestId("intake-v6-artwork-verify-cta"));
    expect(onVerify).toHaveBeenCalledTimes(1);
  });

  it("shows residual vector notice when artwork is confirmed but policy warning remains", () => {
    render(
      <IntakeV6ArtworkFinishSection
        rows={confirmedRows}
        onChange={vi.fn()}
        showResidualVectorNotice
      />,
    );
    expect(screen.getByTestId("intake-v6-artwork-residual-vector-notice")).toHaveTextContent(
      /vector rezidual neclasificat/i,
    );
  });

  it("renders layer-card family layout with header and face/cant zones", () => {
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={vi.fn()} />);
    expect(screen.getByTestId("intake-v6-artwork-layer-cards")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-artwork-header-logo")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-artwork-logo")).toHaveAttribute(
      "data-layer-card-expanded",
      "false",
    );
    expandArtworkCard("logo");
    expect(screen.getByTestId("intake-v6-artwork-face-zone-logo")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-artwork-cant-logo")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-artwork-header-logo")).toHaveTextContent("Logo");
    expect(screen.getByTestId("intake-v6-artwork-face-summary-logo")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-artwork-cant-summary-logo")).toBeInTheDocument();
  });

  it("keeps artwork_finishes shape when cant depth changes", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={onChange} />);
    expandArtworkCard("logo");
    fireEvent.change(screen.getByTestId("intake-v6-artwork-return-logo-depth"), {
      target: { value: "80" },
    });
    const next = onChange.mock.calls.at(-1)![0] as IntakeV6ArtworkFinish[];
    expect(next[0]).toMatchObject({
      layer_key: "logo",
      execution_type: "print_laminate",
      color_mode: "polychrome",
      return_depth_mm: 80,
      confirmed: false,
    });
  });
});
