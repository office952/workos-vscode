export type WorkflowStepType =
  | "artwork"
  | "print"
  | "laminate"
  | "cnc"
  | "assembly"
  | "electrical"
  | "finish"
  | "mounting"
  | "qc"
  | "packing";

export interface WorkflowStep {
  step_id: string;
  order_index: number;
  title: string;
  description: string;
  step_type: WorkflowStepType;
  component_refs: string[];
  finish_refs: string[];
  labor_operation_refs: string[];
  material_role_refs: string[];
  machine_type: string | null;
  workcenter: string | null;
  role_required: string | null;
  condition_label: string | null;
  depends_on_step_ids: string[];
  produces: string[];
  quality_checks: string[];
  is_optional: boolean;
  is_enabled: boolean;
}

export interface TemplateWorkflow {
  template_code: string;
  version: string;
  status: "recommended_preview";
  source: "frontend_readonly_phase1";
  steps: WorkflowStep[];
}

export interface WorkflowValidationIssue {
  step_id: string;
  dependency_step_id: string;
  message: string;
}

function makeStep(step: WorkflowStep): WorkflowStep {
  return step;
}

const LETTERS_WORKFLOW: TemplateWorkflow = {
  template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  version: "phase1-readonly-v1",
  status: "recommended_preview",
  source: "frontend_readonly_phase1",
  steps: [
    makeStep({
      step_id: "letters-artwork-review",
      order_index: 1,
      title: "Verificare fisiere si layere",
      description: "Verifica SVG-ul, rolurile layerelor si geometria pentru litere inainte de productie.",
      step_type: "artwork",
      component_refs: [],
      finish_refs: [],
      labor_operation_refs: ["layer_role_validation"],
      material_role_refs: [],
      machine_type: null,
      workcenter: null,
      role_required: "operator_artwork",
      condition_label: null,
      depends_on_step_ids: [],
      produces: ["layer_roles_confirmed", "geometry_ready"],
      quality_checks: ["svg_valid", "layer_roles_confirmed"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-face-nesting",
      order_index: 2,
      title: "Pregatire nesting fata litere",
      description: "Pregateste geometria fetelor pentru debitare eficienta pe materialul selectat.",
      step_type: "cnc",
      component_refs: ["Face"],
      finish_refs: [],
      labor_operation_refs: ["face_nesting_prep"],
      material_role_refs: ["face_material"],
      machine_type: "cnc_router",
      workcenter: "WC_CNC",
      role_required: "operator_cnc",
      condition_label: null,
      depends_on_step_ids: ["letters-artwork-review"],
      produces: ["face_nesting_layout"],
      quality_checks: ["nesting_layout_reviewed"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-face-cut",
      order_index: 3,
      title: "Debitare fata litere",
      description: "Debiteaza fata literelor conform geometriei confirmate.",
      step_type: "cnc",
      component_refs: ["Face"],
      finish_refs: [],
      labor_operation_refs: ["face_cnc_cut"],
      material_role_refs: ["face_material"],
      machine_type: "cnc_router",
      workcenter: "WC_CNC",
      role_required: "operator_cnc",
      condition_label: null,
      depends_on_step_ids: ["letters-face-nesting"],
      produces: ["cut_face_parts"],
      quality_checks: ["face_cut_alignment"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-back-cut",
      order_index: 4,
      title: "Debitare spate",
      description: "Debiteaza spatele din Forex/backing pentru fiecare litera.",
      step_type: "cnc",
      component_refs: ["Back"],
      finish_refs: [],
      labor_operation_refs: ["back_cnc_cut"],
      material_role_refs: ["back_material"],
      machine_type: "cnc_router",
      workcenter: "WC_CNC",
      role_required: "operator_cnc",
      condition_label: null,
      depends_on_step_ids: ["letters-artwork-review"],
      produces: ["cut_back_parts"],
      quality_checks: ["back_cut_alignment"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-return-prep",
      order_index: 5,
      title: "Pregatire cant / volum",
      description: "Pregateste cantul sau corpul volumetric la adancimea configurata.",
      step_type: "assembly",
      component_refs: ["Return"],
      finish_refs: [],
      labor_operation_refs: ["return_profile_forming"],
      material_role_refs: ["return_profile"],
      machine_type: null,
      workcenter: "WC_ASSEMBLY",
      role_required: "operator_assembly",
      condition_label: null,
      depends_on_step_ids: ["letters-artwork-review"],
      produces: ["prepared_return_parts"],
      quality_checks: ["return_depth_verified"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-finish-print",
      order_index: 6,
      title: "Print / folie / laminare, daca exista",
      description: "Produce si pregateste finisajul aplicabil pe fata literei, doar daca produsul cere folie/print/laminare.",
      step_type: "print",
      component_refs: ["Face", "Finish"],
      finish_refs: ["print", "vinyl", "laminate"],
      labor_operation_refs: ["face_print_finish"],
      material_role_refs: ["print_media", "laminate_media"],
      machine_type: "large_format_print",
      workcenter: "LARGE_FORMAT_PRINT",
      role_required: "operator_print",
      condition_label: "daca finish_mode include print/vinyl/laminate",
      depends_on_step_ids: ["letters-artwork-review"],
      produces: ["prepared_finish_media"],
      quality_checks: ["color_match", "laminate_ready"],
      is_optional: true,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-body-assembly",
      order_index: 7,
      title: "Asamblare corp litere",
      description: "Lipeste fata, cantul si spatele intr-un corp coerent.",
      step_type: "assembly",
      component_refs: ["Face", "Return", "Back"],
      finish_refs: [],
      labor_operation_refs: ["body_assembly"],
      material_role_refs: [],
      machine_type: null,
      workcenter: "WC_ASSEMBLY",
      role_required: "operator_assembly",
      condition_label: null,
      depends_on_step_ids: ["letters-face-cut", "letters-back-cut", "letters-return-prep"],
      produces: ["assembled_letter_bodies"],
      quality_checks: ["joint_alignment", "adhesion_verified"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-led-install",
      order_index: 8,
      title: "Montaj LED",
      description: "Monteaza modulele LED conform densitatii si layoutului electric.",
      step_type: "electrical",
      component_refs: ["Lighting"],
      finish_refs: [],
      labor_operation_refs: ["install_led_modules"],
      material_role_refs: ["led_modules"],
      machine_type: null,
      workcenter: "LED_ASSEMBLY",
      role_required: "operator_electric",
      condition_label: null,
      depends_on_step_ids: ["letters-body-assembly"],
      produces: ["installed_led_modules"],
      quality_checks: ["led_layout_verified"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-wiring-psu",
      order_index: 9,
      title: "Cablare si sursa",
      description: "Leaga modulele LED si sursa de alimentare conform configuratiei.",
      step_type: "electrical",
      component_refs: ["Lighting"],
      finish_refs: [],
      labor_operation_refs: ["wire_led_psu"],
      material_role_refs: ["power_supply", "wiring"],
      machine_type: null,
      workcenter: "ELECTRICAL_WIRING",
      role_required: "operator_electric",
      condition_label: null,
      depends_on_step_ids: ["letters-led-install"],
      produces: ["wired_letter_bodies"],
      quality_checks: ["polarity_checked"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-electrical-test",
      order_index: 10,
      title: "Test electric",
      description: "Verifica aprinderea, uniformitatea luminii si conexiunile.",
      step_type: "qc",
      component_refs: ["Lighting"],
      finish_refs: [],
      labor_operation_refs: ["electrical_test"],
      material_role_refs: [],
      machine_type: null,
      workcenter: "ELECTRICAL_WIRING",
      role_required: "operator_qc",
      condition_label: null,
      depends_on_step_ids: ["letters-wiring-psu"],
      produces: ["electrical_test_passed"],
      quality_checks: ["light_uniformity", "electrical_continuity"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-mounting-prep",
      order_index: 11,
      title: "Pregatire montaj",
      description: "Pregateste sablonul, distantierii si accesoriile pentru montaj.",
      step_type: "mounting",
      component_refs: ["Mounting"],
      finish_refs: [],
      labor_operation_refs: ["mounting_kit_prep"],
      material_role_refs: ["mounting_template", "fasteners"],
      machine_type: null,
      workcenter: "WC_ASSEMBLY",
      role_required: "operator_mounting",
      condition_label: null,
      depends_on_step_ids: ["letters-electrical-test"],
      produces: ["mounting_kit_ready"],
      quality_checks: ["mounting_template_checked"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "letters-final-qc-packing",
      order_index: 12,
      title: "QC final / ambalare",
      description: "Verifica produsul final si il pregateste pentru livrare sau montaj.",
      step_type: "packing",
      component_refs: ["Face", "Return", "Back", "Lighting", "Mounting"],
      finish_refs: ["final_finish"],
      labor_operation_refs: ["final_qc", "packing"],
      material_role_refs: ["packing_materials"],
      machine_type: null,
      workcenter: "QC_FINAL",
      role_required: "operator_qc",
      condition_label: null,
      depends_on_step_ids: ["letters-mounting-prep"],
      produces: ["ready_for_delivery"],
      quality_checks: ["surface_check", "packing_integrity"],
      is_optional: false,
      is_enabled: true,
    }),
  ],
};

const LOGO_WORKFLOW: TemplateWorkflow = {
  template_code: "TPL-VOLUMETRIC-LOGO_v1",
  version: "phase1-readonly-v1",
  status: "recommended_preview",
  source: "frontend_readonly_phase1",
  steps: [
    makeStep({
      step_id: "logo-artwork-review",
      order_index: 1,
      title: "Verificare logo si zone artwork",
      description: "Verifica geometria logo-ului, zonele de culoare si zonele de print/folie.",
      step_type: "artwork",
      component_refs: [],
      finish_refs: [],
      labor_operation_refs: ["logo_artwork_review"],
      material_role_refs: [],
      machine_type: null,
      workcenter: null,
      role_required: "operator_artwork",
      condition_label: null,
      depends_on_step_ids: [],
      produces: ["logo_geometry_confirmed"],
      quality_checks: ["logo_geometry_valid", "artwork_zones_confirmed"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-artwork-print",
      order_index: 2,
      title: "Print / laminare artwork, daca exista",
      description: "Produce si lamineaza grafica daca logo-ul are print sau folie personalizata.",
      step_type: "laminate",
      component_refs: ["Face", "Finish"],
      finish_refs: ["print", "vinyl", "laminate"],
      labor_operation_refs: ["logo_artwork_print", "logo_artwork_laminate"],
      material_role_refs: ["print_media", "laminate_media"],
      machine_type: "large_format_print",
      workcenter: "LARGE_FORMAT_PRINT",
      role_required: "operator_print",
      condition_label: "daca logo_artwork_mode include print/vinyl/laminate",
      depends_on_step_ids: ["logo-artwork-review"],
      produces: ["logo_artwork_ready"],
      quality_checks: ["artwork_color_match", "laminate_bond_ok"],
      is_optional: true,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-face-nesting",
      order_index: 3,
      title: "Pregatire nesting fata logo",
      description: "Pregateste fata logo-ului pentru debitare.",
      step_type: "cnc",
      component_refs: ["Face"],
      finish_refs: [],
      labor_operation_refs: ["logo_face_nesting_prep"],
      material_role_refs: ["logo_face_material"],
      machine_type: "cnc_router",
      workcenter: "WC_CNC",
      role_required: "operator_cnc",
      condition_label: null,
      depends_on_step_ids: ["logo-artwork-review"],
      produces: ["logo_face_nesting_layout"],
      quality_checks: ["logo_face_layout_verified"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-face-cut",
      order_index: 4,
      title: "Debitare fata logo",
      description: "Debiteaza fata logo-ului conform conturului confirmat.",
      step_type: "cnc",
      component_refs: ["Face"],
      finish_refs: [],
      labor_operation_refs: ["logo_face_cut"],
      material_role_refs: ["logo_face_material"],
      machine_type: "cnc_router",
      workcenter: "WC_CNC",
      role_required: "operator_cnc",
      condition_label: null,
      depends_on_step_ids: ["logo-face-nesting"],
      produces: ["cut_logo_face"],
      quality_checks: ["logo_face_cut_alignment"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-back-cut",
      order_index: 5,
      title: "Debitare spate logo",
      description: "Debiteaza spatele logo-ului din materialul configurat.",
      step_type: "cnc",
      component_refs: ["Back"],
      finish_refs: [],
      labor_operation_refs: ["logo_back_cut"],
      material_role_refs: ["logo_back_material"],
      machine_type: "cnc_router",
      workcenter: "WC_CNC",
      role_required: "operator_cnc",
      condition_label: null,
      depends_on_step_ids: ["logo-artwork-review"],
      produces: ["cut_logo_back"],
      quality_checks: ["logo_back_cut_alignment"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-return-prep",
      order_index: 6,
      title: "Pregatire cant / volum logo",
      description: "Pregateste cantul sau corpul logo-ului la adancimea configurata.",
      step_type: "assembly",
      component_refs: ["Return"],
      finish_refs: [],
      labor_operation_refs: ["logo_return_forming"],
      material_role_refs: ["logo_return_profile"],
      machine_type: null,
      workcenter: "WC_ASSEMBLY",
      role_required: "operator_assembly",
      condition_label: null,
      depends_on_step_ids: ["logo-artwork-review"],
      produces: ["prepared_logo_return"],
      quality_checks: ["logo_depth_verified"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-face-finish",
      order_index: 7,
      title: "Aplicare folie / artwork pe fata, daca exista",
      description: "Aplica finisajul pe fata logo-ului dupa etapa potrivita de productie.",
      step_type: "finish",
      component_refs: ["Face", "Finish"],
      finish_refs: ["vinyl", "artwork"],
      labor_operation_refs: ["logo_finish_application"],
      material_role_refs: ["print_media", "laminate_media"],
      machine_type: null,
      workcenter: "FACE_VINYL_APPLICATION_LABOR",
      role_required: "operator_finish",
      condition_label: "daca necesita aplicare pe fata",
      depends_on_step_ids: ["logo-face-cut", "logo-artwork-print"],
      produces: ["finished_logo_face"],
      quality_checks: ["finish_alignment", "surface_finish_ok"],
      is_optional: true,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-body-assembly",
      order_index: 8,
      title: "Asamblare corp logo",
      description: "Asambleaza fata, cantul si spatele logo-ului.",
      step_type: "assembly",
      component_refs: ["Face", "Return", "Back"],
      finish_refs: [],
      labor_operation_refs: ["logo_body_assembly"],
      material_role_refs: [],
      machine_type: null,
      workcenter: "WC_ASSEMBLY",
      role_required: "operator_assembly",
      condition_label: null,
      depends_on_step_ids: ["logo-face-cut", "logo-back-cut", "logo-return-prep"],
      produces: ["assembled_logo_body"],
      quality_checks: ["logo_joint_alignment", "logo_body_rigidity"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-led-install",
      order_index: 9,
      title: "Montaj LED",
      description: "Monteaza modulele LED pentru iluminarea logo-ului.",
      step_type: "electrical",
      component_refs: ["Lighting"],
      finish_refs: [],
      labor_operation_refs: ["logo_led_install"],
      material_role_refs: ["MAT-LED-MODULE"],
      machine_type: null,
      workcenter: "LED_ASSEMBLY",
      role_required: "operator_electric",
      condition_label: null,
      depends_on_step_ids: ["logo-body-assembly"],
      produces: ["logo_led_installed"],
      quality_checks: ["logo_led_layout_ok"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-wiring-psu",
      order_index: 10,
      title: "Cablare si sursa",
      description: "Leaga LED-urile si sursa de alimentare.",
      step_type: "electrical",
      component_refs: ["Lighting"],
      finish_refs: [],
      labor_operation_refs: ["logo_wiring_psu"],
      material_role_refs: ["MAT-LED-PSU-12V", "logo_fasteners"],
      machine_type: null,
      workcenter: "ELECTRICAL_WIRING",
      role_required: "operator_electric",
      condition_label: null,
      depends_on_step_ids: ["logo-led-install"],
      produces: ["logo_electrics_connected"],
      quality_checks: ["logo_polarity_checked"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-light-test",
      order_index: 11,
      title: "Test lumina",
      description: "Verifica lumina, uniformitatea si functionarea electrica.",
      step_type: "qc",
      component_refs: ["Lighting"],
      finish_refs: [],
      labor_operation_refs: ["logo_electrical_test"],
      material_role_refs: [],
      machine_type: null,
      workcenter: "ELECTRICAL_WIRING",
      role_required: "operator_qc",
      condition_label: null,
      depends_on_step_ids: ["logo-wiring-psu"],
      produces: ["logo_light_test_passed"],
      quality_checks: ["logo_light_uniformity", "logo_current_draw_ok"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-mounting-prep",
      order_index: 12,
      title: "Pregatire montaj",
      description: "Pregateste prinderile si sablonul de montaj.",
      step_type: "mounting",
      component_refs: ["Mounting"],
      finish_refs: [],
      labor_operation_refs: ["logo_mounting_template_cut"],
      material_role_refs: ["logo_mounting_template", "logo_fasteners"],
      machine_type: null,
      workcenter: "WC_ASSEMBLY",
      role_required: "operator_mounting",
      condition_label: null,
      depends_on_step_ids: ["logo-light-test"],
      produces: ["logo_mounting_kit_ready"],
      quality_checks: ["mounting_template_verified"],
      is_optional: false,
      is_enabled: true,
    }),
    makeStep({
      step_id: "logo-final-qc-packing",
      order_index: 13,
      title: "QC final / ambalare",
      description: "Verifica produsul si il pregateste pentru livrare sau montaj.",
      step_type: "packing",
      component_refs: ["Face", "Return", "Back", "Lighting", "Mounting"],
      finish_refs: ["final_finish"],
      labor_operation_refs: ["final_qc", "packing"],
      material_role_refs: ["packing_materials"],
      machine_type: null,
      workcenter: "QC_FINAL",
      role_required: "operator_qc",
      condition_label: null,
      depends_on_step_ids: ["logo-mounting-prep"],
      produces: ["logo_ready_for_delivery"],
      quality_checks: ["surface_check", "packing_integrity"],
      is_optional: false,
      is_enabled: true,
    }),
  ],
};

function normalizeTemplateCode(templateCode: string | null | undefined): string {
  return String(templateCode ?? "").trim().toUpperCase();
}

const WORKFLOWS_BY_TEMPLATE_CODE: Record<string, TemplateWorkflow> = {
  [normalizeTemplateCode(LETTERS_WORKFLOW.template_code)]: LETTERS_WORKFLOW,
  [normalizeTemplateCode(LOGO_WORKFLOW.template_code)]: LOGO_WORKFLOW,
};

export function getTemplateWorkflowPreview(templateCode: string | null | undefined): TemplateWorkflow | null {
  const normalized = normalizeTemplateCode(templateCode);
  return WORKFLOWS_BY_TEMPLATE_CODE[normalized] ?? null;
}

export function renumberWorkflowSteps(steps: WorkflowStep[]): WorkflowStep[] {
  return steps.map((step, index) => ({
    ...step,
    order_index: index + 1,
  }));
}

export function reorderWorkflowSteps(
  steps: WorkflowStep[],
  draggedStepId: string,
  targetStepId: string,
): WorkflowStep[] {
  const sourceIndex = steps.findIndex((step) => step.step_id === draggedStepId);
  const targetIndex = steps.findIndex((step) => step.step_id === targetStepId);
  if (sourceIndex < 0 || targetIndex < 0 || sourceIndex === targetIndex) {
    return steps;
  }

  const next = [...steps];
  const [movedStep] = next.splice(sourceIndex, 1);
  next.splice(targetIndex, 0, movedStep);
  return renumberWorkflowSteps(next);
}

export function validateWorkflowSteps(steps: WorkflowStep[]): WorkflowValidationIssue[] {
  const indexByStepId = new Map<string, number>(steps.map((step, index) => [step.step_id, index]));
  const stepById = new Map<string, WorkflowStep>(steps.map((step) => [step.step_id, step]));
  const issues: WorkflowValidationIssue[] = [];

  for (const step of steps) {
    const currentIndex = indexByStepId.get(step.step_id) ?? -1;
    for (const dependencyStepId of step.depends_on_step_ids) {
      const dependencyIndex = indexByStepId.get(dependencyStepId);
      if (dependencyIndex == null) {
        issues.push({
          step_id: step.step_id,
          dependency_step_id: dependencyStepId,
          message: `${step.title} depinde de ${dependencyStepId}, dar pasul lipseste din preview.`,
        });
        continue;
      }
      if (dependencyIndex > currentIndex) {
        const dependencyStep = stepById.get(dependencyStepId);
        issues.push({
          step_id: step.step_id,
          dependency_step_id: dependencyStepId,
          message: `${step.title} trebuie dupa ${dependencyStep?.title ?? dependencyStepId}.`,
        });
      }
    }
  }

  return issues;
}