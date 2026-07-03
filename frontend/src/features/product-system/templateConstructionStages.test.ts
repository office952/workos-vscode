import { describe, it, expect } from "vitest";
import type { ProductTemplateComponent } from "@/lib/api";
import {
  deriveConstructionStages,
  formatConstructionStageChipLabel,
  parseExplicitConstructionStagesFromNotes,
} from "@/features/product-system/templateConstructionStages";

const volumetricComponents: ProductTemplateComponent[] = [
  {
    component_id: "comp_face_litere",
    type: "LITERE_3D",
    name: "Vizual față — plexi/acrilic",
    operations: [],
    materials: [],
  },
  {
    component_id: "comp_lateral_litere",
    type: "LITERE_3D",
    name: "Volum aluminiu — profil lateral",
    operations: [],
    materials: [],
  },
  {
    component_id: "comp_spate_litere",
    type: "STRUCTURA",
    name: "Capac spate — Forex 10 mm",
    operations: [],
    materials: [],
  },
  {
    component_id: "comp_led_litere",
    type: "ELECTRIC_LED",
    name: "Sistem LED",
    operations: [],
    materials: [],
  },
  {
    component_id: "comp_finisaj_litere",
    type: "FINISAJ",
    name: "Finisaj",
    operations: [],
    materials: [],
  },
];

describe("templateConstructionStages", () => {
  it("derives stages from component order and names", () => {
    const stages = deriveConstructionStages(volumetricComponents);
    expect(stages).toHaveLength(5);
    expect(stages.map((s) => s.chipLabel)).toEqual([
      "VIZUAL FAȚĂ",
      "VOLUM ALUMINIU",
      "CAPAC SPATE",
      "SISTEM LED",
      "FINISAJ",
    ]);
    expect(stages.map((s) => s.componentIndex)).toEqual([0, 1, 2, 3, 4]);
  });

  it("does not emit generic ACP/metal stages absent from components", () => {
    const stages = deriveConstructionStages(volumetricComponents);
    const labels = stages.map((s) => s.chipLabel).join(" ");
    expect(labels).not.toMatch(/ACP|METALIC|DIFUZIE|RELIEF/i);
  });

  it("skips legacy components", () => {
    const withLegacy: ProductTemplateComponent[] = [
      ...volumetricComponents.slice(0, 2),
      {
        component_id: "comp_legacy",
        type: "STRUCTURA",
        name: "",
        operations: [],
        materials: [],
        _legacy: true,
      },
      ...volumetricComponents.slice(2),
    ];
    const stages = deriveConstructionStages(withLegacy);
    expect(stages).toHaveLength(5);
    expect(stages.some((s) => s.code === "comp_legacy")).toBe(false);
  });

  it("uses explicit construction_stages metadata when present in notes JSON", () => {
    const notes = JSON.stringify({
      construction_stages: [
        { code: "stage_face", label: "Vizual față", component_id: "comp_face_litere" },
        { code: "stage_led", label: "Sistem LED", component_id: "comp_led_litere" },
      ],
    });
    const explicit = parseExplicitConstructionStagesFromNotes(notes);
    const stages = deriveConstructionStages(volumetricComponents, {
      explicitStages: explicit,
    });
    expect(stages).toHaveLength(2);
    expect(stages[0].chipLabel).toBe("VIZUAL FAȚĂ");
    expect(stages[1].chipLabel).toBe("SISTEM LED");
  });

  it("formats chip labels from em-dash separated names", () => {
    expect(formatConstructionStageChipLabel("Vizual față — plexi/acrilic")).toBe(
      "VIZUAL FAȚĂ"
    );
  });
});
