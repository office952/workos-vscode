import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6ReviewLetterGroupsSection from "./IntakeV6ReviewLetterGroupsSection";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";

vi.mock("@/components/workos/colorRegistry/ColorRegistrySelect", () => ({
  default: () => null,
}));

const baseGroup: IntakeV6LetterGroupFinish = {
  group_key: "pseudo:maria",
  layer_name: "pseudo maria",
  face_finish_type: "none_raw_plexi",
  return_finish_type: "white_aluminum",
  return_depth_mm: 60,
  backing_mode: "forex_10_no_bevel",
  confirmed: true,
};

describe("IntakeV6ReviewLetterGroupsSection collapsed Spate contract", () => {
  it("hides Forex select when collapsed and shows Spate summary", () => {
    render(
      <IntakeV6ReviewLetterGroupsSection
        groups={[baseGroup]}
        onChange={() => undefined}
        faceFinishOptions={[{ value: "none_raw_plexi", label: "Plexiglas opal 3 mm" }]}
      />,
    );

    expect(screen.getByTestId("intake-v6-letter-group-spate-summary-pseudo:maria")).toHaveTextContent(
      /Forex 10 mm/i,
    );
    expect(screen.queryByTestId("intake-v6-backing-mode-pseudo-maria")).not.toBeInTheDocument();
    const header = screen.getByTestId("intake-v6-letter-group-header-pseudo:maria");
    expect(header).not.toHaveTextContent(/pseudo/i);
    expect(header.textContent).toMatch(/Element|maria|Logo|formă|detectat/i);
  });

  it("shows Forex select only after expand in Spate section order", () => {
    render(
      <IntakeV6ReviewLetterGroupsSection
        groups={[baseGroup]}
        onChange={() => undefined}
        faceFinishOptions={[{ value: "none_raw_plexi", label: "Plexiglas opal 3 mm" }]}
      />,
    );

    fireEvent.click(screen.getByTestId("intake-v6-letter-group-header-pseudo:maria"));
    expect(screen.getByTestId("intake-v6-face-letter-zone-pseudo:maria")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-cant-letter-zone-pseudo:maria")).toBeInTheDocument();
    expect(
      screen.getByTestId("intake-v6-review-backing-finish-integration-pseudo:maria"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-backing-mode-pseudo-maria")).toBeInTheDocument();
  });
});
