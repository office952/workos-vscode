import React, { useEffect, useMemo, useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { buildIntakeV6ReviewFormContract } from "./intakeV6ReviewFormContract";
import { useTemplateFormContract, type TemplateFormOptions } from "./useTemplateFormContract";

const { getIntakeV6TemplateFormContractMock } = vi.hoisted(() => ({
  getIntakeV6TemplateFormContractMock: vi.fn(),
}));

vi.mock("@/lib/intakeV6/intakeV6Api", () => ({
  getIntakeV6TemplateFormContract: getIntakeV6TemplateFormContractMock,
}));

vi.mock("@/components/ui/sonner", () => ({
  toast: {
    error: vi.fn(),
  },
}));

function makeTemplateContract(): TemplateFormOptions {
  return {
    faceFinishOptions: [
      { value: "none", label: "Fara finisaj" },
      { value: "oracal_651", label: "Oracal 651" },
    ],
    returnFinishOptions: [],
    allowedReturnDepthMm: [40, 60],
    allowedPsuWatts: [60, 150],
    allowedMountingSystems: [
      { value: "direct_wall", label: "Direct perete" },
      { value: "steel_bars", label: "Bare otel" },
    ],
    allowedMountingBarProfiles: ["20x20x1.5", "30x30x1.5"],
    allowedReturnFinishTypes: [
      { value: "white_aluminum", label: "Alb" },
      { value: "ral_paint", label: "Vopsit RAL" },
    ],
    allowedLightingSystems: [
      { value: "led_modules", label: "Module LED" },
      { value: "led_strip", label: "Banda LED" },
    ],
    allowedLightColors: [{ value: "cool", label: "Cool white" }],
    allowedLedModulePowerW: [{ value: "1", label: "1.00 W / modul" }],
    allowedMountingTemplateMaterials: [{ value: "paper", label: "Hartie" }],
    allowedVinylRollWidths: [{ value: "1260", label: "1260 mm" }],
    allowedEmblemLightingModes: [{ value: "excluded", label: "Emblema neluminoasa" }],
    defaultFaceFinish: "none",
    defaultReturnDepthMm: 40,
    defaultPsuWatts: 150,
    defaultMountingSystem: "steel_bars",
    defaultMountingTemplateEnabled: false,
    defaultMountingBarProfile: "20x20x1.5",
    defaultReturnFinishType: "ral_paint",
    defaultLightingSystemType: "led_strip",
    defaultLightColor: "cool",
    defaultLedModulePowerW: 1,
    defaultMountingTemplateMaterial: "paper",
    defaultVinylRollWidthMm: 1260,
    defaultEmblemLightingMode: "excluded",
    templateCode: "TPL-VOLUMETRIC-LETTERS",
    dossierSource: "product_blueprint_dossier",
    alignmentStatus: "aligned",
    loading: false,
    error: null,
    contract: {
      workspace_id: "ws-1",
      template_code: "TPL-VOLUMETRIC-LETTERS",
      contract_version: "1.0.0",
      intended_form_authority: "product_system_dossier",
      current_runtime_authority: "product_system_dossier",
      alignment_status: "aligned",
      template_active: true,
      dossier_status: "approved",
      dossier_source: "product_blueprint_dossier",
      ui_must_not_invent_final_options: true,
      variant_fields: [],
      canonical_rows: [],
      warnings: [],
      blockers: [],
      discovered_v4_values: {},
    },
  };
}

function readHarnessState(
  payload: Record<string, unknown>,
  contract: ReturnType<typeof buildIntakeV6ReviewFormContract>,
) {
  const setup =
    payload.finish_setup != null && typeof payload.finish_setup === "object" && !Array.isArray(payload.finish_setup)
      ? (payload.finish_setup as Record<string, unknown>)
      : {};
  return {
    face_vinyl_roll_width_mm:
      typeof setup.face_vinyl_roll_width_mm === "number"
        ? setup.face_vinyl_roll_width_mm
        : contract.defaults.faceVinylRollWidthMm,
    face_oracal_code:
      typeof setup.face_oracal_code === "string" ? setup.face_oracal_code : "",
    light_color:
      typeof setup.light_color === "string" ? setup.light_color : contract.defaults.lightColor,
    mounting_system:
      typeof setup.mounting_system === "string"
        ? setup.mounting_system
        : contract.defaults.mountingSystem,
  };
}

function ReviewContractFreezeHarness({ payload }: { payload: Record<string, unknown> }) {
  const templateContract = useTemplateFormContract("ws-1");
  const reviewContract = useMemo(
    () => buildIntakeV6ReviewFormContract(templateContract),
    [templateContract],
  );
  const [tick, setTick] = useState(0);
  const [state, setState] = useState(() => readHarnessState(payload, reviewContract));

  useEffect(() => {
    setState(readHarnessState(payload, reviewContract));
  }, [payload, reviewContract]);

  return React.createElement(
    "div",
    { "data-testid": `review-freeze-harness-${tick}` },
    React.createElement(
      "button",
      { type: "button", onClick: () => setTick((current) => current + 1), "data-testid": "rerender" },
      "rerender",
    ),
    React.createElement(
      "select",
      {
        "data-testid": "roll-width",
        value: String(state.face_vinyl_roll_width_mm),
        onChange: (event: React.ChangeEvent<HTMLSelectElement>) =>
          setState((current) => ({
            ...current,
            face_vinyl_roll_width_mm: Number(event.target.value),
          })),
      },
      React.createElement("option", { value: "1000" }, "1000 mm"),
      React.createElement("option", { value: "1260" }, "1260 mm"),
    ),
    React.createElement("input", {
      "data-testid": "oracal-code",
      value: state.face_oracal_code,
      onChange: (event: React.ChangeEvent<HTMLInputElement>) =>
        setState((current) => ({ ...current, face_oracal_code: event.target.value })),
    }),
    React.createElement(
      "select",
      {
        "data-testid": "light-color",
        value: state.light_color,
        onChange: (event: React.ChangeEvent<HTMLSelectElement>) =>
          setState((current) => ({ ...current, light_color: event.target.value })),
      },
      React.createElement("option", { value: "warm" }, "Warm"),
      React.createElement("option", { value: "neutral" }, "Neutral"),
      React.createElement("option", { value: "cool" }, "Cool"),
    ),
    React.createElement(
      "select",
      {
        "data-testid": "mounting-system",
        value: state.mounting_system,
        onChange: (event: React.ChangeEvent<HTMLSelectElement>) =>
          setState((current) => ({ ...current, mounting_system: event.target.value })),
      },
      React.createElement("option", { value: "direct_wall" }, "Direct perete"),
      React.createElement("option", { value: "steel_bars" }, "Bare otel"),
    ),
  );
}

describe("buildIntakeV6ReviewFormContract", () => {
  beforeEach(() => {
    getIntakeV6TemplateFormContractMock.mockReset();
  });

  it("returns contract-driven options for finisaje, iluminare, montaj si artwork", () => {
    const adapter = buildIntakeV6ReviewFormContract(makeTemplateContract());

    expect(adapter.source).toBe("template_contract");
    expect(adapter.finishes.allowedReturnDepthMm).toEqual([40, 60]);
    expect(adapter.finishes.allowedReturnFinishOptions.map((option) => option.value)).toEqual([
      "white",
      "ral_paint",
    ]);
    expect(adapter.lighting.allowedLightingSystems.map((option) => option.value)).toEqual([
      "led_modules",
      "led_strip",
    ]);
    expect(adapter.mounting.allowedMountingSystems.map((option) => option.value)).toEqual([
      "direct_wall",
      "steel_bars",
    ]);
    expect(adapter.artwork.allowedEmblemLightingModes.map((option) => option.value)).toEqual([
      "excluded",
    ]);
  });

  it("preserves legacy ReviewStep defaults when the template contract is missing", () => {
    const adapter = buildIntakeV6ReviewFormContract(null);

    expect(adapter.source).toBe("fallback");
    expect(adapter.defaults.faceFinishType).toBe("oracal_651");
    expect(adapter.defaults.returnDepthMm).toBe(60);
    expect(adapter.defaults.lightColor).toBe("neutral");
    expect(adapter.defaults.selectedPsuWatts).toBe(100);
    expect(adapter.defaults.mountingSystem).toBe("direct_wall");
    expect(adapter.finishes.allowedReturnFinishOptions.map((option) => option.value)).toEqual([
      "white",
      "black",
      "gold",
      "silver",
      "ral_paint",
      "oracal_wrapped",
    ]);
  });

  it("keeps payload values and user edits instead of snapping back to contract defaults on rerender", async () => {
    getIntakeV6TemplateFormContractMock.mockResolvedValue(makeTemplateContract().contract);

    render(
      React.createElement(ReviewContractFreezeHarness, {
        payload: {
          finish_setup: {
            face_vinyl_roll_width_mm: 1260,
            face_oracal_code: "ORACAL-970",
            light_color: "cool",
            mounting_system: "steel_bars",
          },
        },
      }),
    );

    await waitFor(() => {
      expect(screen.getByTestId("roll-width")).toHaveValue("1260");
    });
    expect(screen.getByTestId("oracal-code")).toHaveValue("ORACAL-970");
    expect(screen.getByTestId("light-color")).toHaveValue("cool");
    expect(screen.getByTestId("mounting-system")).toHaveValue("steel_bars");

    fireEvent.change(screen.getByTestId("roll-width"), { target: { value: "1000" } });
    fireEvent.change(screen.getByTestId("oracal-code"), { target: { value: "ORACAL-8500" } });
    fireEvent.change(screen.getByTestId("light-color"), { target: { value: "neutral" } });
    fireEvent.change(screen.getByTestId("mounting-system"), { target: { value: "direct_wall" } });
    fireEvent.click(screen.getByTestId("rerender"));

    expect(screen.getByTestId("roll-width")).toHaveValue("1000");
    expect(screen.getByTestId("oracal-code")).toHaveValue("ORACAL-8500");
    expect(screen.getByTestId("light-color")).toHaveValue("neutral");
    expect(screen.getByTestId("mounting-system")).toHaveValue("direct_wall");
  });
});