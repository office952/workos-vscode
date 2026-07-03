/**
 * Production sequencing notes for TPL-VOLUMETRIC-LETTERS (display / intake capture only).
 */

import type { ProductTemplateComponent } from "@/lib/api";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";

export type VolumeFinish =
  | "oracal_651_before_forming"
  | "paint_after_face_miter_bond"
  | "none";

/**
 * Keep Product System wording aligned with the current operator contract.
 * This prevents guidance drift between template editing and operator preview flows.
 */
export const VOLUMETRIC_OPERATIONAL_CONTRACT = {
  sourceModule: "volumetric_operator_contract",
  sourceTemplate: "TPL-VOLUMETRIC-LETTERS",
  sequencing: {
    returnVinylBeforeForming: true,
    returnPaintingAfterAssembly: true,
    faceVinylAfterAssembly: true,
    noSharedSupportPsuInPackage: true,
  },
} as const;

export function getVolumetricOperationalContractBadges(): string[] {
  return [
    `source_module=${VOLUMETRIC_OPERATIONAL_CONTRACT.sourceModule}`,
    `template=${VOLUMETRIC_OPERATIONAL_CONTRACT.sourceTemplate}`,
    VOLUMETRIC_OPERATIONAL_CONTRACT.sequencing.returnVinylBeforeForming
      ? "return_vinyl=before_forming"
      : "return_vinyl=unspecified",
    VOLUMETRIC_OPERATIONAL_CONTRACT.sequencing.returnPaintingAfterAssembly
      ? "return_paint=after_assembly"
      : "return_paint=unspecified",
    VOLUMETRIC_OPERATIONAL_CONTRACT.sequencing.faceVinylAfterAssembly
      ? "face_vinyl=after_assembly"
      : "face_vinyl=unspecified",
    VOLUMETRIC_OPERATIONAL_CONTRACT.sequencing.noSharedSupportPsuInPackage
      ? "no_shared_support=psu_in_package"
      : "no_shared_support=unspecified",
  ];
}

export const VOLUME_FINISH_OPTIONS: { value: VolumeFinish; label: string }[] = [
  {
    value: "oracal_651_before_forming",
    label: "Colantare Oracal 651 — înainte de modelare (mașină)",
  },
  {
    value: "paint_after_face_miter_bond",
    label: "Vopsire RAL — după lipire volum pe șanfren față",
  },
  { value: "none", label: "Aluminiu brut / fără colantare sau vopsire laterală" },
];

export const VOLUMETRIC_COMPONENT_PRODUCTION_HINTS: Record<string, string> = {
  comp_face_litere:
    "Vizual față (plexi): opțional colantare Oracal 651 sau 8500 — la final, după premontaj pe suport sau înainte de montaj pe perete dacă nu există suport. Contract operațional curent: colantarea feței rămâne după asamblare (și după uscarea vopsirii cantului, dacă există).",
  comp_lateral_litere:
    "Volum aluminiu: Oracal 651 înainte de modelare la mașină; sau vopsire doar după lipirea pe vizual față (cu șanfren față). Contract operațional curent: cant colantat înainte de formare, cant vopsit după asamblare.",
  comp_finisaj_litere:
    "Asamblare + QC; colantarea față 651/8500 și montajul final se aliniază cu tipul de montaj (premontaj / perete). Contract operațional curent: la no shared support, sursele LED sunt ambalate în colet (fără task separat de montaj sursă pe suport).",
};

export const VOLUMETRIC_OPERATIONAL_RULES: readonly { title: string; body: string }[] = [
  {
    title: "Regulă operațională · cant colantat",
    body: "Dacă varianta este cant colantat, aplicarea Oracal 651 pe cant se face înainte de modelarea/formarea la mașină.",
  },
  {
    title: "Regulă operațională · cant vopsit",
    body: "Dacă varianta este cant vopsit RAL, vopsirea se face după asamblare (după lipirea cantului pe față), nu înainte.",
  },
  {
    title: "Regulă operațională · față colantată",
    body: "Colantarea feței se aplică după asamblare; dacă există cant vopsit, se aplică după vopsire/uscare/protecție.",
  },
  {
    title: "Regulă operațională · no shared support",
    body: "În modul fără suport comun, sursele LED se pregătesc în coletul de livrare, fără operație separată de montaj sursă pe suport.",
  },
];

export function isFaceOracalFinish(faceFinish: string | undefined): boolean {
  return faceFinish === "oracal_651" || faceFinish === "oracal_8500_translucent";
}

/** When to apply Oracal 651/8500 on the plexi face (customer / shop floor). */
export function getFaceOracalApplicationTiming(
  spec: Pick<IntakeProductSpec, "mounting_type" | "premounting_type">
): string {
  const hasPremount =
    spec.mounting_type === "premounted" ||
    (spec.premounting_type != null &&
      spec.premounting_type !== "none" &&
      spec.premounting_type !== undefined);
  if (hasPremount) {
    return "Colantarea față (Oracal 651 sau 8500) se face la final, după premontarea literelor pe suport (structură metalică sau panou ACM).";
  }
  return "Colantarea față (Oracal 651 sau 8500) se face la final, înainte de montajul pe perete, când literele nu au suport de premontaj.";
}

export function getVolumeFinishProductionNote(volumeFinish: VolumeFinish | undefined): string {
  switch (volumeFinish) {
    case "oracal_651_before_forming":
      return "Volum aluminiu: aplicare Oracal 651 înainte de modelare/formare la mașină.";
    case "paint_after_face_miter_bond":
      return "Volum aluminiu: vopsire RAL permisă doar după lipirea pe vizual față, pe șanfren (miter).";
    case "none":
    default:
      return "Volum aluminiu: fără colantare 651 sau vopsire laterală dedicată (brut sau finisaj inclus în alt strat).";
  }
}

export const VOLUMETRIC_PRODUCTION_RULES: readonly { title: string; body: string }[] = [
  {
    title: "Vizual față (plexi)",
    body:
      "Opțional colantare Oracal 651 sau 8500 translucid. Proces la final: după premontaj pe suport sau înainte de montaj pe perete dacă nu există premontaj.",
  },
  {
    title: "Volum aluminiu (laterale)",
    body:
      "Variante: (1) Oracal 651 aplicat înainte de modelare la mașină; (2) vopsire RAL doar după lipirea volumului pe vizual față, cu șanfren față.",
  },
  {
    title: "Șanfren",
    body:
      "Șanfren față: necesar pentru lipire volum–față și pentru traseul de vopsire pe volum. Șanfren spate Forex: opțional, separat.",
  },
  ...VOLUMETRIC_OPERATIONAL_RULES,
];

export type VolumetricCantModuleStatus = "covered" | "partial" | "missing";

export interface VolumetricCantProductionModule {
  key: string;
  title: string;
  appliesWhen: string;
  sequencing: string;
  operationCodes: readonly string[];
  materialCodes: readonly string[];
}

export interface VolumetricCantProductionModuleCoverage
  extends VolumetricCantProductionModule {
  status: VolumetricCantModuleStatus;
  missingOperationCodes: string[];
  missingMaterialCodes: string[];
}

const VOLUMETRIC_CANT_MODULES: readonly VolumetricCantProductionModule[] = [
  {
    key: "base_profile",
    title: "Bază volum aluminiu",
    appliesWhen: "Obligatoriu pentru orice variantă de cant / volum.",
    sequencing: "Profil lateral debitat și format înainte de asamblarea finală.",
    operationCodes: ["side_forming"],
    materialCodes: ["MAT-PROFIL-LATERAL-LITERE"],
  },
  {
    key: "oracal_before_forming",
    title: "Cant colantat Oracal 651",
    appliesWhen:
      "Când traseul comercial cere ORACAL pe cant sau volume_finish = oracal_651_before_forming.",
    sequencing: "Aplicare Oracal 651 înainte de modelare / formare la mașină.",
    operationCodes: ["vinyl_application", "side_forming"],
    materialCodes: ["MAT-ORACAL-651", "MAT-PROFIL-LATERAL-LITERE"],
  },
  {
    key: "ral_after_bonding",
    title: "Cant vopsit RAL",
    appliesWhen:
      "Când traseul comercial cere RAL pe cant sau volume_finish = paint_after_face_miter_bond.",
    sequencing: "Lipire volum-față, apoi vopsire RAL pe cant, după asamblare.",
    operationCodes: ["return_face_bonding", "painting"],
    materialCodes: ["MAT-PROFIL-LATERAL-LITERE", "MAT-VOPSEA-RAL"],
  },
  {
    key: "raw_stock_finish",
    title: "Cant standard din aluminiu stoc",
    appliesWhen: "Când nu se aplică nici Oracal 651, nici vopsire RAL pe cant.",
    sequencing: "Se păstrează finisajul standard al profilului după formare, fără operație suplimentară.",
    operationCodes: ["side_forming"],
    materialCodes: ["MAT-PROFIL-LATERAL-LITERE"],
  },
];

function normalizeOperationCode(value: string | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

function normalizeMaterialCode(value: string | undefined): string {
  return (value ?? "").trim().toUpperCase();
}

export function isVolumetricCantLateralComponent(
  component: Pick<ProductTemplateComponent, "component_id" | "name">
): boolean {
  const id = component.component_id.trim().toLowerCase();
  const name = component.name.trim().toLowerCase();
  return (
    id === "comp_lateral_litere" ||
    id.includes("lateral") ||
    id.includes("profil") ||
    name.includes("lateral") ||
    name.includes("profil") ||
    name.includes("aluminiu")
  );
}

export function buildVolumetricCantProductionModules(
  components: readonly Pick<
    ProductTemplateComponent,
    "component_id" | "name" | "operations" | "materials"
  >[]
): VolumetricCantProductionModuleCoverage[] {
  const operationCodes = new Set<string>();
  const materialCodes = new Set<string>();

  components.forEach((component) => {
    component.operations.forEach((operation) => {
      const code = normalizeOperationCode(operation.code);
      if (code) operationCodes.add(code);
    });
    component.materials.forEach((material) => {
      const code = normalizeMaterialCode(material.materialCode ?? material.material_code);
      if (code) materialCodes.add(code);
    });
  });

  return VOLUMETRIC_CANT_MODULES.map((module) => {
    const missingOperationCodes = module.operationCodes.filter(
      (code) => !operationCodes.has(normalizeOperationCode(code))
    );
    const missingMaterialCodes = module.materialCodes.filter(
      (code) => !materialCodes.has(normalizeMaterialCode(code))
    );
    const totalChecks = module.operationCodes.length + module.materialCodes.length;
    const missingChecks = missingOperationCodes.length + missingMaterialCodes.length;
    const passedChecks = totalChecks - missingChecks;

    let status: VolumetricCantModuleStatus = "missing";
    if (missingChecks === 0) {
      status = "covered";
    } else if (passedChecks > 0) {
      status = "partial";
    }

    return {
      ...module,
      status,
      missingOperationCodes: [...missingOperationCodes],
      missingMaterialCodes: [...missingMaterialCodes],
    };
  });
}
