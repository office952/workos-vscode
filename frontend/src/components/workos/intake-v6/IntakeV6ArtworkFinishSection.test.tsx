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
  it("uses unified face personalization options without transparent controls", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={onChange} />);
    expandArtworkCard("logo");
    expect(screen.getByTestId("intake-v6-artwork-execution-logo")).toHaveTextContent("Print + laminare");
    expect(screen.getByTestId("intake-v6-artwork-cant-logo")).toBeInTheDocument();
    const method = screen.getByTestId("intake-v6-artwork-face-method-logo");
    const labels = Array.from(method.querySelectorAll("option")).map((opt) => opt.textContent);
    expect(labels).toEqual([
      "Fără finisaj — plexiglas brut",
      "Oracal 641",
      "Oracal 651",
      "Oracal 8500 — translucid",
      "Print + laminare",
    ]);
    expect(screen.queryByTestId("intake-v6-artwork-transparent-logo")).not.toBeInTheDocument();
    const rollWidth = screen.getByTestId("intake-v6-artwork-roll-width-logo");
    expect(Array.from(rollWidth.querySelectorAll("option")).map((option) => option.getAttribute("value"))).toEqual([
      "",
      "1050",
      "1320",
      "1500",
    ]);
    expect(screen.getByTestId("intake-v6-artwork-roll-retraction-logo")).toHaveTextContent("1050 / 1320 / 1500 mm");
    expect(screen.getByTestId("intake-v6-artwork-roll-retraction-logo")).toHaveTextContent("1010 / 1280 / 1460 mm");
    fireEvent.change(method, { target: { value: "oracal_651" } });
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]?.execution_type).toBe("cut_vinyl");
    expect(next[0]?.material_code).toBe("ORACAL_651");
    expect(next[0]?.confirmed).toBe(false);
  });

  it("selecting raw clears stale print and oracal fields coherently", () => {
    const onChange = vi.fn();
    render(
      <IntakeV6ArtworkFinishSection
        rows={[
          {
            ...rows[0]!,
            execution_type: "print_laminate",
            face_personalization_method: "none_raw_plexi",
            material_code: "ORAFOL_PRINT_LAMINATION",
            print_material_code: "ORAFOL_PRINT",
            lamination_material_code: "ORAFOL_LAMINATION",
          },
        ]}
        onChange={onChange}
      />,
    );
    expandArtworkCard("logo");
    expect(screen.getByTestId("intake-v6-artwork-execution-logo")).toHaveTextContent("Fără finisaj — plexiglas brut");
    expect((screen.getByTestId("intake-v6-artwork-face-method-logo") as HTMLSelectElement).value).toBe("none");
    fireEvent.change(screen.getByTestId("intake-v6-artwork-face-method-logo"), {
      target: { value: "none" },
    });
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]).toMatchObject({
      execution_type: "none_raw_plexi",
      color_mode: "none",
      face_personalization_method: "none_raw_plexi",
      material_code: null,
      print_material_code: null,
      lamination_material_code: null,
      face_roll_width_mm: null,
      print_roll_width_mm: null,
      lamination_roll_width_mm: null,
    });
  });

  it("selecting Oracal clears stale print fields and keeps a coherent header", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={onChange} />);
    expandArtworkCard("logo");
    fireEvent.change(screen.getByTestId("intake-v6-artwork-face-method-logo"), {
      target: { value: "oracal_641" },
    });
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]).toMatchObject({
      execution_type: "cut_vinyl",
      face_personalization_method: "oracal",
      material_code: "ORACAL_641",
      print_material_code: null,
      lamination_material_code: null,
    });
  });

  it("lets logo switch back to print and lamination", () => {
    const onChange = vi.fn();
    render(
      <IntakeV6ArtworkFinishSection
        rows={[{ ...rows[0]!, execution_type: "cut_vinyl", material_code: "ORACAL_651" }]}
        onChange={onChange}
      />,
    );
    expandArtworkCard("logo");
    fireEvent.change(screen.getByTestId("intake-v6-artwork-face-method-logo"), {
      target: { value: "print_laminate" },
    });
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]?.execution_type).toBe("print_laminate");
    expect(next[0]?.material_code).toBe("ORAFOL_PRINT_LAMINATION");
    expect(next[0]?.face_personalization_method).toBe("print_laminate");
    expect(next[0]?.face_roll_width_mm).toBe(1050);
    expect(next[0]?.print_roll_width_mm).toBe(1050);
    expect(next[0]?.lamination_roll_width_mm).toBe(1050);
    expect(next[0]?.print_transparency).toBe("standard");
  });

  it("persists print and lamination roll width on logo/artwork rows", () => {
    const onChange = vi.fn();
    render(<IntakeV6ArtworkFinishSection rows={rows} onChange={onChange} />);
    expandArtworkCard("logo");
    fireEvent.change(screen.getByTestId("intake-v6-artwork-roll-width-logo"), {
      target: { value: "1320" },
    });
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]).toMatchObject({
      face_roll_width_mm: 1320,
      print_roll_width_mm: 1320,
      lamination_roll_width_mm: 1320,
      roll_side_retraction_mm: 20,
      roll_total_retraction_mm: 40,
      confirmed: false,
    });
  });

  it("uses Oracal roll widths for logo Oracal method", () => {
    render(
      <IntakeV6ArtworkFinishSection
        rows={[{ ...rows[0]!, execution_type: "cut_vinyl", material_code: "ORACAL_651" }]}
        onChange={vi.fn()}
      />,
    );
    expandArtworkCard("logo");
    const rollWidth = screen.getByTestId("intake-v6-artwork-roll-width-logo");
    expect(Array.from(rollWidth.querySelectorAll("option")).map((option) => option.getAttribute("value"))).toEqual([
      "",
      "1000",
      "1260",
    ]);
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
    expect(button).toHaveTextContent("Confirm vector logo");
    fireEvent.click(button);
    const next = onChange.mock.calls[0]![0] as IntakeV6ArtworkFinish[];
    expect(next[0]?.confirmed).toBe(true);
    expect(next[0]?.execution_type).toBe("print_laminate");
    expect(next[0]?.print_transparency).toBe("standard");
    expect(next[0]?.return_finish_type).toBe("white_aluminum");
  });

  it("shows Vector Logo confirmat when confirmed=true", () => {
    render(<IntakeV6ArtworkFinishSection rows={confirmedRows} onChange={vi.fn()} />);
    expandArtworkCard("logo");
    expect(screen.getByTestId("intake-v6-artwork-confirm-logo")).toHaveTextContent("Vector Logo confirmat");
    expect(screen.getByTestId("intake-v6-artwork-confirmed-logo")).toHaveTextContent("OK");
  });

  it("shows Step 1 confirmation instead of a second artwork confirmation CTA", () => {
    render(
      <IntakeV6ArtworkFinishSection
        rows={rows}
        onChange={vi.fn()}
        stepOneConfirmedLayerKeys={new Set(["logo"])}
      />,
    );
    expandArtworkCard("logo");
    expect(screen.getByTestId("intake-v6-artwork-step1-confirmed-logo")).toHaveTextContent(
      "Vector Logo confirmat in Pasul 1",
    );
    expect(screen.queryByTestId("intake-v6-artwork-confirm-logo")).not.toBeInTheDocument();
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

  it("uses generic logo naming with source metadata tooltip", () => {
    render(
      <IntakeV6ArtworkFinishSection
        rows={[
          { ...rows[0]!, layer_key: "logo-dreapta", layer_name: "logo dreapta", source_layer_name: "logo-dreapta", element_count: 2 },
          { ...rows[0]!, layer_key: "logo-stanga", layer_name: "logo stanga", source_layer_name: "logo-stanga", element_count: 1 },
        ]}
        onChange={vi.fn()}
        stepOneConfirmedLayerKeys={new Set(["logo-dreapta", "logo-stanga"])}
      />,
    );
    expect(screen.getByTestId("intake-v6-artwork-header-logo-dreapta")).toHaveTextContent("Logo 1");
    expect(screen.getByTestId("intake-v6-artwork-header-logo-stanga")).toHaveTextContent("Logo 2");
    expect(screen.getByTestId("intake-v6-artwork-logo-dreapta")).toHaveAttribute(
      "title",
      expect.stringContaining("source: logo-dreapta"),
    );
    expect(screen.getByTestId("intake-v6-artwork-logo-dreapta")).toHaveAttribute(
      "title",
      expect.stringContaining("position: dreapta"),
    );
    expect(screen.getByTestId("intake-v6-artwork-logo-dreapta")).toHaveAttribute(
      "title",
      expect.stringContaining("status: confirmat in Pasul 1"),
    );
    expandArtworkCard("logo-dreapta");
    expect(screen.getByTestId("intake-v6-artwork-source-metadata-logo-dreapta")).toHaveTextContent(
      /sursa SVG: logo-dreapta/,
    );
    expect(screen.getByTestId("intake-v6-artwork-source-metadata-logo-dreapta")).toHaveTextContent(
      /pozitie: dreapta/,
    );
    expect(screen.getByTestId("intake-v6-artwork-source-metadata-logo-dreapta")).toHaveTextContent(
      /confirmat in Pasul 1/,
    );
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
