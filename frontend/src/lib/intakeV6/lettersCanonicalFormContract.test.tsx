import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import IntakeV6ReviewLetterGroupsSection from "@/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";
import {
  bindMapFromContract,
  isLettersCanonicalTemplate,
  labelForKey,
  requiredForKey,
  resolveLettersCanonicalFieldLabels,
} from "./lettersCanonicalFormContract";

vi.mock("@/components/workos/colorRegistry/ColorRegistrySelect", () => ({
  default: () => null,
}));

const baseGroup: IntakeV6LetterGroupFinish = {
  group_key: "a",
  layer_name: "Layer A",
  face_finish_type: "oracal_651",
  return_finish_type: "white_aluminum",
  return_depth_mm: 60,
  backing_mode: "forex_10_no_bevel",
  confirmed: false,
};

function makeLettersContract(
  overrides?: Partial<IntakeV6ModularFormContractResponse>,
): IntakeV6ModularFormContractResponse {
  return {
    summary: {
      template_code: "TPL-VOLUMETRIC-LETTERS_v2",
      contract_version: "1.1.0-letters-canonical",
      runtime_authority: true,
    },
    modules: [],
    trigger_alignments: [],
    field_bindings: [
      {
        canonical_key: "face_finish_type",
        workspace_path: "finish_setup.face_finish_type",
        label_ro: "Finisaj față (contract)",
        required: true,
        field_type: "enum",
      },
      {
        canonical_key: "return_finish_type",
        workspace_path: "finish_setup.return_finish_type",
        label_ro: "Finisaj cant (contract)",
        required: true,
        field_type: "enum",
      },
      {
        canonical_key: "return_depth_mm",
        workspace_path: "finish_setup.return_depth_mm",
        label_ro: "Adâncime cant (contract)",
        required: true,
        field_type: "number",
        unit: "mm",
      },
      {
        canonical_key: "backing_mode",
        workspace_path: "finish_setup.backing_mode",
        label_ro: "Mod spate (contract)",
        required: true,
        field_type: "enum",
      },
      {
        canonical_key: "lighting_system_type",
        workspace_path: "finish_setup.lighting_system_type",
        label_ro: "Tip iluminare (contract)",
        required: false,
        field_type: "enum",
      },
      {
        canonical_key: "mounting_system",
        workspace_path: "finish_setup.mounting_system",
        label_ro: "Sistem montaj (contract)",
        required: true,
        field_type: "enum",
      },
    ],
    ...overrides,
  };
}

describe("lettersCanonicalFormContract helpers", () => {
  it("recognizes canonical Letters template codes", () => {
    expect(isLettersCanonicalTemplate("TPL-VOLUMETRIC-LETTERS_v2")).toBe(true);
    expect(isLettersCanonicalTemplate("TPL-VOLUMETRIC-LETTERS")).toBe(true);
    expect(isLettersCanonicalTemplate("TPL-VOLUMETRIC-LOGO_v1")).toBe(false);
  });

  it("builds bind map and resolves labels/required flags", () => {
    const bindMap = bindMapFromContract(makeLettersContract());
    expect(bindMap.size).toBe(6);
    expect(labelForKey(bindMap, "face_finish_type", "fallback")).toBe("Finisaj față (contract)");
    expect(labelForKey(bindMap, "missing_key", "fallback")).toBe("fallback");
    expect(requiredForKey(bindMap, "face_finish_type")).toBe(true);
    expect(requiredForKey(bindMap, "lighting_system_type")).toBe(false);
    expect(requiredForKey(bindMap, "missing_key", true)).toBe(true);
  });

  it("returns null field labels for non-Letters templates", () => {
    expect(resolveLettersCanonicalFieldLabels("TPL-OTHER", makeLettersContract())).toBeNull();
  });

  it("returns contract-driven field labels for Letters", () => {
    const labels = resolveLettersCanonicalFieldLabels(
      "TPL-VOLUMETRIC-LETTERS_v2",
      makeLettersContract(),
    );
    expect(labels).toEqual({
      face_finish_type: "Finisaj față (contract)",
      return_finish_type: "Finisaj cant (contract)",
      return_depth_mm: "Adâncime cant (contract)",
      backing_mode: "Mod spate (contract)",
      lighting_system_type: "Tip iluminare (contract)",
      mounting_system: "Sistem montaj (contract)",
    });
  });
});

describe("Letters contract labels in Review UI", () => {
  it("prefers modular form contract labels over hardcoded Review strings", () => {
    const labels = resolveLettersCanonicalFieldLabels(
      "TPL-VOLUMETRIC-LETTERS_v2",
      makeLettersContract(),
    );
    expect(labels).not.toBeNull();

    render(
      <IntakeV6ReviewLetterGroupsSection
        groups={[baseGroup]}
        onChange={() => undefined}
        faceFinishOptions={[{ value: "oracal_651", label: "Oracal 651" }]}
        fieldLabels={labels ?? undefined}
      />,
    );

    fireEvent.click(screen.getByTestId("intake-v6-letter-group-header-a"));

    expect(screen.getByText("Finisaj față (contract)")).toBeInTheDocument();
    expect(screen.getByText("Finisaj cant (contract)")).toBeInTheDocument();
    expect(screen.getByText("Adâncime cant (contract)")).toBeInTheDocument();
    expect(screen.getByText("Mod spate (contract)")).toBeInTheDocument();
    expect(screen.queryByText("Finisaj față")).not.toBeInTheDocument();
  });
});
