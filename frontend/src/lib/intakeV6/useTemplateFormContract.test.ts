import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useTemplateFormContract } from "./useTemplateFormContract";
import type { IntakeV4TemplateFormContractResponse } from "./intakeV4Api";

// Mock the API module
vi.mock("./intakeV4Api", () => ({
  getIntakeV4TemplateFormContract: vi.fn(),
}));

// Mock sonner toast (no-op in tests)
vi.mock("@/components/ui/sonner", () => ({
  toast: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

import { getIntakeV4TemplateFormContract } from "./intakeV4Api";

function makeDossierResponse(
  overrides: Partial<IntakeV4TemplateFormContractResponse> = {},
): IntakeV4TemplateFormContractResponse {
  return {
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
    variant_fields: [
      {
        field_key: "face_finish_type",
        label: "Finisaj față plexi",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "mapped",
        allowed_values: ["none", "oracal_651", "oracal_641", "oracal_8500", "printed_vinyl", "printed_laminated_vinyl"],
        default_value: "none",
        v4_field_key: "face_finish_type",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "return_depth_mm",
        label: "Adâncime cant",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: [30, 60, 80, 100],
        default_value: 60,
        v4_field_key: "return_depth_mm",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "selected_psu_watts",
        label: "Putere sursă LED",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: [60, 100, 160, 200],
        default_value: 100,
        v4_field_key: "selected_psu_watts",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "mounting_system",
        label: "Sistem montaj",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: ["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"],
        default_value: "direct_wall",
        v4_field_key: "mounting_system",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "mounting_bar_profile",
        label: "Profil bare",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: ["30x30x1.5"],
        default_value: "30x30x1.5",
        v4_field_key: "mounting_bar_profile",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "mounting_template_enabled",
        label: "Șablon montaj",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: [true, false],
        default_value: true,
        v4_field_key: "mounting_template_enabled",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "return_finish_type",
        label: "Finisaj cant / volum",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: ["white_aluminum", "black_aluminum", "gold_aluminum", "mirror_silver", "ral_paint", "oracal_wrapped"],
        default_value: "white_aluminum",
        v4_field_key: "return_finish_type",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "lighting_system_type",
        label: "Sistem iluminare LED",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: ["led_modules", "led_strip"],
        default_value: "led_modules",
        v4_field_key: "lighting_system_type",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "light_color",
        label: "Culoare lumina LED",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: ["warm", "neutral", "cool"],
        default_value: "warm",
        v4_field_key: "light_color",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "led_module_power_w",
        label: "Putere modul LED",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: [0.75, 1.0, 1.44],
        default_value: 0.75,
        v4_field_key: "led_module_power_w",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "mounting_template_material_type",
        label: "Material sablon montaj",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: ["forex", "paper"],
        default_value: "forex",
        v4_field_key: "mounting_template_material_type",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "face_vinyl_roll_width_mm",
        label: "Latime rola vinyl fata",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: [1000, 1260],
        default_value: 1000,
        v4_field_key: "face_vinyl_roll_width_mm",
        source: "product_blueprint_dossier",
        notes: [],
      },
      {
        field_key: "emblem_lighting_mode",
        label: "Mod iluminare emblema",
        owner: "product_system_dossier",
        current_runtime_owner: "product_system_dossier",
        alignment_status: "canonical",
        allowed_values: ["area_lit", "excluded"],
        default_value: "area_lit",
        v4_field_key: "emblem_lighting_mode",
        source: "product_blueprint_dossier",
        notes: [],
      },
    ],
    canonical_rows: [],
    warnings: [],
    blockers: [],
    discovered_v4_values: {},
    ...overrides,
  };
}

describe("useTemplateFormContract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns loading state initially", () => {
    vi.mocked(getIntakeV4TemplateFormContract).mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useTemplateFormContract("ws-1"));
    expect(result.current.loading).toBe(true);
    expect(result.current.contract).toBeNull();
  });

  it("returns fallback options when workspaceId is undefined", () => {
    const { result } = renderHook(() => useTemplateFormContract(undefined));
    expect(result.current.loading).toBe(false);
    expect(result.current.contract).toBeNull();
    // Fallback defaults
    expect(result.current.defaultFaceFinish).toBe("none");
    expect(result.current.defaultReturnDepthMm).toBe(60);
    expect(result.current.defaultPsuWatts).toBe(100);
    expect(result.current.defaultMountingSystem).toBe("direct_wall");
    expect(result.current.defaultMountingTemplateEnabled).toBe(true);
    expect(result.current.defaultMountingBarProfile).toBe("30x30x1.5");
    expect(result.current.defaultReturnFinishType).toBe("white_aluminum");
    expect(result.current.defaultLightingSystemType).toBe("led_modules");
    expect(result.current.defaultLightColor).toBe("warm");
    expect(result.current.defaultLedModulePowerW).toBe(0.75);
    expect(result.current.defaultMountingTemplateMaterial).toBe("forex");
    expect(result.current.defaultVinylRollWidthMm).toBe(1000);
    expect(result.current.defaultEmblemLightingMode).toBe("area_lit");
    // Fallback option arrays
    expect(result.current.allowedLightingSystems.length).toBe(2);
    expect(result.current.allowedLightColors.length).toBe(3);
    expect(result.current.allowedEmblemLightingModes.length).toBe(2);
  });

  describe("with dossier contract loaded", () => {
    beforeEach(() => {
      vi.mocked(getIntakeV4TemplateFormContract).mockResolvedValue(makeDossierResponse());
    });

    it("populates face finish options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.faceFinishOptions.map((o) => o.value);
      expect(values).toContain("none");
      expect(values).toContain("oracal_651");
      expect(values).toContain("oracal_641");
      expect(values).toContain("oracal_8500");
      expect(values).toContain("printed_vinyl");
      expect(values).toContain("printed_laminated_vinyl");
    });

    it("populates face finish labels correctly", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const labelMap = Object.fromEntries(result.current.faceFinishOptions.map((o) => [o.value, o.label]));
      expect(labelMap["oracal_651"]).toBe("Oracal 651");
      expect(labelMap["oracal_8500"]).toBe("Oracal 8500");
      expect(labelMap["none"]).toBe("Fără finisaj — plexiglas brut");
    });

    it("populates return depth options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.allowedReturnDepthMm).toEqual([30, 60, 80, 100]);
    });

    it("populates PSU watts from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.allowedPsuWatts).toEqual([60, 100, 160, 200]);
    });

    it("populates mounting system options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedMountingSystems.map((o) => o.value);
      expect(values).toEqual(["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"]);
    });

    it("populates mounting system labels", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const labelMap = Object.fromEntries(result.current.allowedMountingSystems.map((o) => [o.value, o.label]));
      expect(labelMap["direct_wall"]).toBe("Direct perete");
      expect(labelMap["acm_panel"]).toBe("Panou ACM");
    });

    it("populates mounting bar profiles from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.allowedMountingBarProfiles).toEqual(["30x30x1.5"]);
    });

    it("populates return finish types from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedReturnFinishTypes.map((o) => o.value);
      expect(values).toContain("white_aluminum");
      expect(values).toContain("ral_paint");
      expect(values).toContain("oracal_wrapped");
      const labelMap = Object.fromEntries(result.current.allowedReturnFinishTypes.map((o) => [o.value, o.label]));
      expect(labelMap["white_aluminum"]).toBe("Alb");
      expect(labelMap["oracal_wrapped"]).toBe("Oracal 651");
    });

    it("populates lighting system options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedLightingSystems.map((o) => o.value);
      expect(values).toEqual(["led_modules", "led_strip"]);
      expect(result.current.allowedLightingSystems[0].label).toBe("Module LED");
    });

    it("populates light color options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedLightColors.map((o) => o.value);
      expect(values).toEqual(["warm", "neutral", "cool"]);
      expect(result.current.allowedLightColors[0].label).toBe("Warm white");
    });

    it("populates LED module power options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedLedModulePowerW.map((o) => o.value);
      expect(values).toContain("0.75");
      expect(values).toContain("1.44");
      expect(result.current.allowedLedModulePowerW[0].label).toBe("0.75 W / modul");
    });

    it("populates mounting template material options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedMountingTemplateMaterials.map((o) => o.value);
      expect(values).toEqual(["forex", "paper"]);
      expect(result.current.allowedMountingTemplateMaterials[0].label).toBe("Forex");
    });

    it("populates vinyl roll width options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedVinylRollWidths.map((o) => o.value);
      expect(values).toContain("1000");
      expect(values).toContain("1260");
      expect(result.current.allowedVinylRollWidths[0].label).toBe("1000 mm");
    });

    it("populates emblem lighting mode options from dossier", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      const values = result.current.allowedEmblemLightingModes.map((o) => o.value);
      expect(values).toEqual(["area_lit", "excluded"]);
      expect(result.current.allowedEmblemLightingModes[0].label).toBe("Emblema luminoasa - calcul pe arie");
    });

    it("extracts default values from dossier variant fields", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.defaultFaceFinish).toBe("none");
      expect(result.current.defaultReturnDepthMm).toBe(60);
      expect(result.current.defaultPsuWatts).toBe(100);
      expect(result.current.defaultMountingSystem).toBe("direct_wall");
      expect(result.current.defaultMountingTemplateEnabled).toBe(true);
      expect(result.current.defaultMountingBarProfile).toBe("30x30x1.5");
      expect(result.current.defaultReturnFinishType).toBe("white_aluminum");
      expect(result.current.defaultLightingSystemType).toBe("led_modules");
      expect(result.current.defaultLightColor).toBe("warm");
      expect(result.current.defaultLedModulePowerW).toBe(0.75);
      expect(result.current.defaultMountingTemplateMaterial).toBe("forex");
      expect(result.current.defaultVinylRollWidthMm).toBe(1000);
      expect(result.current.defaultEmblemLightingMode).toBe("area_lit");
    });

    it("reports aligned status and dossier source", async () => {
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.alignmentStatus).toBe("aligned");
      expect(result.current.dossierSource).toBe("product_blueprint_dossier");
      expect(result.current.templateCode).toBe("TPL-VOLUMETRIC-LETTERS");
    });
  });

  describe("with modified dossier values", () => {
    it("uses custom return depth when dossier adds 120mm", async () => {
      vi.mocked(getIntakeV4TemplateFormContract).mockResolvedValue(
        makeDossierResponse({
          variant_fields: [
            {
              field_key: "return_depth_mm",
              label: "Adâncime cant",
              owner: "product_system_dossier",
              current_runtime_owner: "product_system_dossier",
              alignment_status: "canonical",
              allowed_values: [30, 60, 80, 100, 120],
              default_value: 60,
              v4_field_key: "return_depth_mm",
              source: "product_blueprint_dossier",
              notes: [],
            },
          ],
        }),
      );
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.allowedReturnDepthMm).toEqual([30, 60, 80, 100, 120]);
    });

    it("uses custom PSU watts when dossier adds 300W", async () => {
      vi.mocked(getIntakeV4TemplateFormContract).mockResolvedValue(
        makeDossierResponse({
          variant_fields: [
            {
              field_key: "selected_psu_watts",
              label: "PSU",
              owner: "product_system_dossier",
              current_runtime_owner: "product_system_dossier",
              alignment_status: "canonical",
              allowed_values: [60, 100, 160, 200, 300],
              default_value: 100,
              v4_field_key: "selected_psu_watts",
              source: "product_blueprint_dossier",
              notes: [],
            },
          ],
        }),
      );
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.allowedPsuWatts).toEqual([60, 100, 160, 200, 300]);
    });
  });

  describe("fallback on API error", () => {
    it("sets error and uses fallback options", async () => {
      vi.mocked(getIntakeV4TemplateFormContract).mockRejectedValue(new Error("Network error"));
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.error).toBe("Network error");
      expect(result.current.contract).toBeNull();
      // Fallback options should still work
      expect(result.current.allowedReturnDepthMm.length).toBeGreaterThan(0);
      expect(result.current.allowedPsuWatts.length).toBeGreaterThan(0);
      expect(result.current.allowedMountingSystems.length).toBeGreaterThan(0);
    });
  });

  describe("static fallback contract", () => {
    it("shows info toast for static fallback", async () => {
      vi.mocked(getIntakeV4TemplateFormContract).mockResolvedValue(
        makeDossierResponse({
          dossier_source: "static_contract_fallback",
          variant_fields: [],
        }),
      );
      const { result } = renderHook(() => useTemplateFormContract("ws-1"));
      await waitFor(() => expect(result.current.loading).toBe(false));

      expect(result.current.dossierSource).toBe("static_contract_fallback");
      // With empty variant_fields, should use fallback options
      expect(result.current.allowedReturnDepthMm).toEqual([30, 60, 80, 100]);
      expect(result.current.allowedPsuWatts).toEqual([60, 100, 160, 200]);
    });
  });
});
