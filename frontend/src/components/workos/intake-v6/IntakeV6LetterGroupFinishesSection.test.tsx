import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6LetterGroupFinishesSection from "./IntakeV6LetterGroupFinishesSection";
import IntakeV6ReviewCantLettersSection from "./IntakeV6ReviewCantLettersSection";
import IntakeV6ReviewFaceLettersSection from "./IntakeV6ReviewFaceLettersSection";
import IntakeV6ReviewLetterGroupsSection from "./IntakeV6ReviewLetterGroupsSection";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";

vi.mock("@/components/workos/colorRegistry/ColorRegistrySelect", () => ({
  default: ({
    testId,
    onChange,
  }: {
    testId?: string;
    onChange: (item: { code: string; name: string } | null) => void;
  }) => (
    <button type="button" data-testid={testId} onClick={() => onChange({ code: "010", name: "White" })}>
      mock-color
    </button>
  ),
}));

const groups: IntakeV6LetterGroupFinish[] = [
  {
    group_key: "a",
    layer_name: "Strat A",
    face_finish_type: "oracal_651",
    face_oracal_code: "010",
    return_finish_type: "white_aluminum",
    return_depth_mm: 80,
    confirmed: false,
  },
  {
    group_key: "b",
    layer_name: "Strat B",
    face_finish_type: "oracal_651",
    return_finish_type: "mirror_silver",
    return_depth_mm: 60,
    confirmed: false,
  },
];

function expandLetterGroupCard(groupKey: string) {
  fireEvent.click(screen.getByTestId(`intake-v6-letter-group-header-${groupKey}`));
}

describe("IntakeV6LetterGroupFinishesSection", () => {
  it("renders face and cant in unified layer cards", () => {
    render(<IntakeV6LetterGroupFinishesSection groups={groups} onChange={vi.fn()} />);
    expect(screen.getByTestId("intake-v6-letter-group-finishes")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-face-finishes")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-cant-finishes")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-face-letters-helper")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-cant-letters-helper")).toBeInTheDocument();
    expandLetterGroupCard("a");
    expect(screen.getByTestId("intake-v6-face-letter-zone-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-cant-letter-zone-a")).toBeInTheDocument();
  });

  it("aligns cant finisaj with face finisaj on the same review grid row", () => {
    render(<IntakeV6LetterGroupFinishesSection groups={groups} onChange={vi.fn()} />);
    expandLetterGroupCard("a");
    expect(screen.getByTestId("intake-v6-face-type-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-return-a-type")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-face-roll-width-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-return-a-depth")).toBeInTheDocument();
    const cardA = screen.getByTestId("intake-v6-letter-group-a");
    expect(cardA.querySelector(".sm\\:grid-cols-2")).toBeTruthy();
  });

  it("keeps face color on a full-width row below finisaj and roll width", () => {
    render(<IntakeV6LetterGroupFinishesSection groups={groups} onChange={vi.fn()} />);
    expandLetterGroupCard("a");
    const settingsRow = screen.getByTestId("intake-v6-face-settings-row-a");
    const colorRow = screen.getByTestId("intake-v6-face-color-row-a");
    expect(within(settingsRow).queryByTestId("intake-v6-face-color-a")).not.toBeInTheDocument();
    expect(within(colorRow).getByTestId("intake-v6-face-color-a")).toBeInTheDocument();
  });

  it("places copy-to-all in cant zone", () => {
    render(<IntakeV6LetterGroupFinishesSection groups={groups} onChange={vi.fn()} />);
    expect(screen.getByTestId("intake-v6-cant-copy-zone")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-copy-cant-to-all")).toHaveTextContent(
      "Copiază cant la toate",
    );
  });

  it("copies first cant settings to all groups without changing face fields", () => {
    const onChange = vi.fn();
    render(<IntakeV6LetterGroupFinishesSection groups={groups} onChange={onChange} />);
    fireEvent.click(screen.getByTestId("intake-v6-copy-cant-to-all"));
    expect(onChange).toHaveBeenCalledTimes(1);
    const next = onChange.mock.calls[0]![0] as IntakeV6LetterGroupFinish[];
    expect(next[0]?.return_finish_type).toBe("white_aluminum");
    expect(next[0]?.return_depth_mm).toBe(80);
    expect(next[1]?.return_finish_type).toBe("white_aluminum");
    expect(next[1]?.return_depth_mm).toBe(80);
    expect(next[0]?.face_finish_type).toBe("oracal_651");
    expect(next[1]?.face_finish_type).toBe("oracal_651");
  });

  it("renders compact layer header with aligned face and cant columns", () => {
    render(<IntakeV6LetterGroupFinishesSection groups={groups} onChange={vi.fn()} />);
    expect(screen.getByTestId("intake-v6-letter-group-header-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-swatch-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-layer-card-column-header")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-letter-group-face-summary-a")).toHaveClass("truncate");
    expect(screen.getByTestId("intake-v6-letter-group-cant-summary-a")).toHaveClass("truncate");
    expect(screen.getByTestId("intake-v6-letter-group-a")).toHaveAttribute(
      "data-layer-card-expanded",
      "false",
    );
  });

  it("does not repeat cant helper text inside each layer card", () => {
    render(<IntakeV6LetterGroupFinishesSection groups={groups} onChange={vi.fn()} />);
    const cardA = screen.getByTestId("intake-v6-letter-group-a");
    expect(within(cardA).queryByText("Laterala literei / adâncimea volumului.")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-cant-letters-helper")).toHaveClass("sr-only");
  });

  it("filters letter face finish options to volumetric-relevant values only", () => {
    const templateOptions = [
      { value: "none", label: "Fără finisaj — plexiglas brut" },
      { value: "oracal_641", label: "Oracal 641" },
      { value: "oracal_651", label: "Oracal 651" },
      { value: "oracal_8500", label: "Oracal 8500 — translucid" },
      { value: "printed_vinyl", label: "Print pe vinyl" },
      { value: "printed_laminated_vinyl", label: "Print + laminare pe vinyl" },
    ];
    render(
      <IntakeV6ReviewLetterGroupsSection
        groups={groups}
        onChange={vi.fn()}
        faceFinishOptions={templateOptions}
      />,
    );
    expandLetterGroupCard("a");
    const select = screen.getByTestId("intake-v6-face-type-a");
    const labels = Array.from(select.querySelectorAll("option")).map((opt) => opt.textContent);
    expect(labels).toContain("Fără finisaj — plexiglas brut");
    expect(labels).toContain("Oracal 641");
    expect(labels).toContain("Oracal 651");
    expect(labels).toContain("Oracal 8500 — translucid");
    expect(labels).toContain("Print + laminare");
    expect(labels).not.toContain("Print pe vinyl");
    expect(labels).not.toContain("Print + laminare pe vinyl");
  });

  it("lets letter groups select print and lamination", () => {
    const onChange = vi.fn();
    render(<IntakeV6ReviewLetterGroupsSection groups={groups} onChange={onChange} />);
    expandLetterGroupCard("a");
    fireEvent.change(screen.getByTestId("intake-v6-face-type-a"), {
      target: { value: "print_laminate" },
    });
    const next = onChange.mock.calls.at(-1)![0] as IntakeV6LetterGroupFinish[];
    expect(next[0]).toMatchObject({
      group_key: "a",
      face_finish_type: "print_laminate",
      face_oracal_code: null,
      face_vinyl_roll_width_mm: 1050,
      confirmed: false,
    });
  });

  it("uses print and lamination roll widths for letter groups", () => {
    render(
      <IntakeV6ReviewLetterGroupsSection
        groups={[{ ...groups[0]!, face_finish_type: "print_laminate", face_vinyl_roll_width_mm: 1050 }]}
        onChange={vi.fn()}
      />,
    );
    expandLetterGroupCard("a");
    const select = screen.getByTestId("intake-v6-face-roll-width-a");
    const values = Array.from(select.querySelectorAll("option")).map((option) => option.getAttribute("value"));
    expect(values).toEqual(["", "1050", "1320", "1500"]);
    expect(values).not.toContain("1000");
  });

  it("emits existing callback when letter face finish changes", () => {
    const onChange = vi.fn();
    const templateOptions = [
      { value: "none", label: "Fără finisaj — plexiglas brut" },
      { value: "printed_vinyl", label: "Print pe vinyl" },
    ];
    render(
      <IntakeV6ReviewLetterGroupsSection
        groups={groups}
        onChange={onChange}
        faceFinishOptions={templateOptions}
      />,
    );
    expandLetterGroupCard("a");
    fireEvent.change(screen.getByTestId("intake-v6-face-type-a"), { target: { value: "none" } });
    const next = onChange.mock.calls.at(-1)![0] as IntakeV6LetterGroupFinish[];
    expect(next[0]).toMatchObject({
      group_key: "a",
      face_finish_type: "none",
      confirmed: false,
    });
    expect(next[0]).toHaveProperty("return_finish_type");
    expect(next[0]).toHaveProperty("return_depth_mm");
  });

  it("uses sm breakpoint for face and cant side-by-side layout", () => {
    render(<IntakeV6ReviewLetterGroupsSection groups={groups} onChange={vi.fn()} />);
    expandLetterGroupCard("a");
    const cardA = screen.getByTestId("intake-v6-letter-group-a");
    const grid = cardA.querySelector(".sm\\:grid-cols-2");
    expect(grid).toBeTruthy();
  });

  it("truncates face and cant summary columns without wrapping", () => {
    render(<IntakeV6ReviewLetterGroupsSection groups={groups} onChange={vi.fn()} />);
    const faceSummary = screen.getByTestId("intake-v6-letter-group-face-summary-a");
    const cantSummary = screen.getByTestId("intake-v6-letter-group-cant-summary-a");
    expect(faceSummary).toHaveClass("truncate");
    expect(cantSummary).toHaveClass("truncate");
    expect(faceSummary).toHaveAttribute("title");
    expect(cantSummary).toHaveAttribute("title");
  });

  it("toggles layer card expand and collapse", () => {
    render(<IntakeV6ReviewLetterGroupsSection groups={groups} onChange={vi.fn()} />);
    const card = screen.getByTestId("intake-v6-letter-group-a");
    expect(card).toHaveAttribute("data-layer-card-expanded", "false");
    expandLetterGroupCard("a");
    expect(card).toHaveAttribute("data-layer-card-expanded", "true");
    expandLetterGroupCard("a");
    expect(card).toHaveAttribute("data-layer-card-expanded", "false");
  });

  it("renders forex backing row inside the vector litere card", () => {
    const onBacking = vi.fn();
    render(
      <IntakeV6ReviewLetterGroupsSection
        groups={groups}
        onChange={vi.fn()}
        backingMode="forex_10_no_bevel"
        onBackingChange={onBacking}
      />,
    );
    const letterCard = screen.getByTestId("intake-v6-letter-group-face-finishes");
    expect(within(letterCard).getByTestId("intake-v6-review-backing-finish-integration")).toBeInTheDocument();
    expect(within(letterCard).getByText("Finisaj spate")).toBeInTheDocument();
    fireEvent.change(within(letterCard).getByTestId("intake-v6-backing-mode"), {
      target: { value: "forex_10_with_bevel" },
    });
    expect(onBacking).toHaveBeenCalledWith("forex_10_with_bevel");
  });
});

describe("IntakeV6ReviewFaceLettersSection", () => {
  it("groups finisaj fata and latime rola on the same settings row", () => {
    render(<IntakeV6ReviewFaceLettersSection groups={groups} onChange={vi.fn()} />);
    const settingsRow = screen.getByTestId("intake-v6-face-settings-row-a");
    const faceZone = screen.getByTestId("intake-v6-face-letter-zone-a");
    expect(settingsRow).toBeInTheDocument();
    expect(within(settingsRow).getByTestId("intake-v6-face-type-a")).toBeInTheDocument();
    expect(within(settingsRow).getByTestId("intake-v6-face-roll-width-a")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-face-color-row-a")).toBeInTheDocument();
    expect(within(settingsRow).getByText("Finisaj față")).toBeInTheDocument();
    expect(within(faceZone).getByText("Față literei")).toBeInTheDocument();
  });

  it("patches face finish type without cant fields in the section", () => {
    const onChange = vi.fn();
    render(<IntakeV6ReviewFaceLettersSection groups={groups} onChange={onChange} />);
    const faceSection = screen.getByTestId("intake-v6-letter-group-face-finishes");
    expect(within(faceSection).queryByText("Tip finisaj cant / volum")).not.toBeInTheDocument();

    fireEvent.change(screen.getByTestId("intake-v6-face-type-a"), { target: { value: "oracal_641" } });
    expect(onChange).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ group_key: "a", face_finish_type: "oracal_641", confirmed: false }),
      ]),
    );
  });

  it("patches face oracal color", () => {
    const onChange = vi.fn();
    render(<IntakeV6ReviewFaceLettersSection groups={groups} onChange={onChange} />);
    fireEvent.click(screen.getByTestId("intake-v6-face-color-a"));
    expect(onChange).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({
          group_key: "a",
          face_oracal_code: "010",
          face_oracal_name: "White",
          confirmed: false,
        }),
      ]),
    );
  });

  it("patches face vinyl roll width", () => {
    const onChange = vi.fn();
    render(<IntakeV6ReviewFaceLettersSection groups={groups} onChange={onChange} />);
    fireEvent.change(screen.getByTestId("intake-v6-face-roll-width-a"), { target: { value: "1260" } });
    expect(onChange).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({
          group_key: "a",
          face_vinyl_roll_width_mm: 1260,
          confirmed: false,
        }),
      ]),
    );
  });
});

describe("IntakeV6ReviewCantLettersSection", () => {
  it("patches cant depth without face fields in the section", () => {
    const onChange = vi.fn();
    render(<IntakeV6ReviewCantLettersSection groups={groups} onChange={onChange} />);
    const cantSection = screen.getByTestId("intake-v6-letter-group-cant-finishes");
    expect(within(cantSection).queryByTestId("intake-v6-face-type-a")).not.toBeInTheDocument();

    fireEvent.change(screen.getByTestId("intake-v6-letter-group-return-a-depth"), {
      target: { value: "100" },
    });
    expect(onChange).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ group_key: "a", return_depth_mm: 100, confirmed: false }),
      ]),
    );
  });

  it("patches cant finish type", () => {
    const onChange = vi.fn();
    render(<IntakeV6ReviewCantLettersSection groups={groups} onChange={onChange} />);
    fireEvent.change(screen.getByTestId("intake-v6-letter-group-return-b-type"), {
      target: { value: "gold" },
    });
    expect(onChange).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ group_key: "b", return_finish_type: "gold_aluminum", confirmed: false }),
      ]),
    );
  });
});
