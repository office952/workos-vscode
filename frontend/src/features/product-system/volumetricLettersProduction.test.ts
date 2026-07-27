import { describe, expect, it } from "vitest";
import {
  VOLUMETRIC_PRODUCTION_RULES,
  buildVolumetricCantProductionModules,
  getVolumetricOperationalContractBadges,
  isVolumetricCantLateralComponent,
} from "@/features/product-system/volumetricLettersProduction";
import type { ProductTemplateComponent } from "@/lib/api";

describe("volumetricLettersProduction", () => {
  it("keeps explicit volumetric operational contract badges", () => {
    const badges = getVolumetricOperationalContractBadges();

    expect(badges).toContain("source_module=volumetric_operator_contract");
    expect(badges).toContain("template=TPL-VOLUMETRIC-LETTERS");
    expect(badges).toContain("return_vinyl=before_forming");
    expect(badges).toContain("return_paint=after_assembly");
    expect(badges).toContain("face_vinyl=after_assembly");
    expect(badges).toContain("no_shared_support=psu_in_package");
  });

  it("includes volumetric operational production rules", () => {
    const titles = VOLUMETRIC_PRODUCTION_RULES.map((rule) => rule.title);

    expect(titles).toContain("Regulă operațională · cant colantat");
    expect(titles).toContain("Regulă operațională · cant vopsit");
    expect(titles).toContain("Regulă operațională · față colantată");
    expect(titles).toContain("Regulă operațională · no shared support");
  });

  it("builds modular cant coverage from template components", () => {
    const components: ProductTemplateComponent[] = [
      {
        component_id: "comp_lateral_litere",
        type: "LITERE_3D",
        name: "Volum aluminiu",
        operations: [
          {
            code: "side_forming",
            name: "Formare lateral",
            workcenter: "cnc",
            estimatedMinutes: 20,
            sequence: 1,
            component_ref: "comp_lateral_litere",
          },
          {
            code: "vinyl_application",
            name: "Colantare",
            workcenter: "finisaj",
            estimatedMinutes: 15,
            sequence: 2,
            component_ref: "comp_lateral_litere",
          },
        ],
        materials: [
          {
            materialCode: "MAT-PROFIL-LATERAL-LITERE",
            name: "Profil lateral",
            quantity: 1,
            unit: "ml",
            component_ref: "comp_lateral_litere",
          },
          {
            materialCode: "MAT-ORACAL-651",
            name: "Oracal 651",
            quantity: 1,
            unit: "m2",
            component_ref: "comp_lateral_litere",
          },
        ],
      },
      {
        component_id: "comp_finisaj_litere",
        type: "FINISAJ",
        name: "Finisaj și asamblare",
        operations: [
          {
            code: "return_face_bonding",
            name: "Lipire volum-față",
            workcenter: "asamblare",
            estimatedMinutes: 20,
            sequence: 3,
            component_ref: "comp_finisaj_litere",
          },
          {
            code: "painting",
            name: "Vopsire",
            workcenter: "vopsitorie",
            estimatedMinutes: 30,
            sequence: 4,
            component_ref: "comp_finisaj_litere",
          },
        ],
        materials: [],
      },
    ];

    const modules = buildVolumetricCantProductionModules(components);
    const base = modules.find((module) => module.key === "base_profile");
    const oracal = modules.find((module) => module.key === "oracal_before_forming");
    const ral = modules.find((module) => module.key === "ral_after_bonding");

    expect(base?.status).toBe("covered");
    expect(oracal?.status).toBe("covered");
    expect(ral?.status).toBe("partial");
    expect(ral?.missingMaterialCodes).toEqual(["MAT-VOPSEA-RAL"]);
  });

  it("detects the lateral volumetric component as cant owner", () => {
    expect(
      isVolumetricCantLateralComponent({
        component_id: "comp_lateral_litere",
        name: "Volum aluminiu",
      } as ProductTemplateComponent)
    ).toBe(true);
  });
});
