import type {
  FormSystemBackboneBlocker,
  FormSystemBackboneContract,
  FormSystemBackboneField,
  IntakeV6ModularFormContractResponse,
} from "./intakeV6ModularFormContractTypes";

export type FormSystemBackboneFieldProjection = {
  fieldKey: string;
  label: string;
  ownerKind: "component" | "svg" | "system" | "unknown";
  ownerId: string;
  sourceKind:
    | "svg_analyzer"
    | "operator_manual"
    | "hydrated_runtime"
    | "calculated_read_model"
    | "product_system_contract"
    | "unknown";
  state:
    | "suggested"
    | "confirmed"
    | "fallback"
    | "hydrated"
    | "manual"
    | "blocked"
    | "warning"
    | "derived_readonly"
    | "missing";
  valuePath: string | null;
  productTruthPathCandidate: string | null;
  isConfirmedTruth: boolean;
  isDerived: boolean;
  isBlocking: boolean;
  warnings: string[];
  blockers: string[];
  trace: Record<string, unknown>;
};

export interface BuildFormSystemBackboneFieldProjectionOptions {
  fieldKeys?: string[];
}

export const DEFAULT_FORM_SYSTEM_BACKBONE_FIELD_KEYS = [
  "svg.layer_group_role",
  "svg.selected_layer_group",
  "return.depth_mm",
] as const;

type FormSystemBackboneProjectionInput =
  | FormSystemBackboneContract
  | IntakeV6ModularFormContractResponse
  | null
  | undefined;

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function readBackbone(input: FormSystemBackboneProjectionInput): FormSystemBackboneContract | null {
  if (!input || typeof input !== "object") return null;
  if ("form_system_backbone" in input) {
    return input.form_system_backbone ?? null;
  }
  return input;
}

function ownerKindFor(field: FormSystemBackboneField): FormSystemBackboneFieldProjection["ownerKind"] {
  const ownerId = text(field.owning_component);
  if (ownerId === "svg_layer_roles") return "svg";
  if (ownerId === "readiness") return "system";
  if (ownerId) return "component";
  return "unknown";
}

function sourceKindFor(field: FormSystemBackboneField): FormSystemBackboneFieldProjection["sourceKind"] {
  switch (text(field.source_type)) {
    case "svg_suggested":
      return "svg_analyzer";
    case "operator_confirmed":
    case "manual_input":
      return "operator_manual";
    case "hydrated":
    case "fallback":
      return "hydrated_runtime";
    case "contract_default":
      return "product_system_contract";
    default:
      return "unknown";
  }
}

function stateFor(field: FormSystemBackboneField): FormSystemBackboneFieldProjection["state"] {
  switch (text(field.state)) {
    case "suggested":
    case "confirmed":
    case "fallback":
    case "hydrated":
    case "manual":
    case "blocked":
    case "warning":
    case "missing":
      return field.state as FormSystemBackboneFieldProjection["state"];
    case "ready":
      return "confirmed";
    default:
      return sourceKindFor(field) === "product_system_contract" ? "derived_readonly" : "missing";
  }
}

function notesFor(field: FormSystemBackboneField): string[] {
  const note = text(field.notes);
  return note ? [note] : [];
}

function blockerMapFor(backbone: FormSystemBackboneContract): Map<string, FormSystemBackboneBlocker[]> {
  const map = new Map<string, FormSystemBackboneBlocker[]>();
  const blockers = backbone.blockers ?? backbone.readiness?.blockers ?? [];
  for (const blocker of blockers) {
    const fieldKey = text(blocker.field_key);
    if (!fieldKey) continue;
    const existing = map.get(fieldKey);
    if (existing) {
      existing.push(blocker);
    } else {
      map.set(fieldKey, [blocker]);
    }
  }
  return map;
}

function warningsFor(
  field: FormSystemBackboneField,
  state: FormSystemBackboneFieldProjection["state"],
  blockers: FormSystemBackboneBlocker[],
): string[] {
  const warnings: string[] = [];
  if (state === "suggested") {
    warnings.push("Suggested value only; operator confirmation is still required.");
  }
  if (state === "hydrated" || state === "fallback") {
    warnings.push("Hydrated or fallback value is not confirmed truth.");
  }
  if (state === "missing") {
    warnings.push("Field is missing and does not represent confirmed truth.");
  }
  if (state === "warning") {
    warnings.push("Warning state is display-only and not confirmed truth.");
  }
  for (const blocker of blockers) {
    const message = text(blocker.message);
    if (message) warnings.push(message);
  }
  return [...warnings, ...notesFor(field)];
}

function buildProjection(
  field: FormSystemBackboneField,
  blockers: FormSystemBackboneBlocker[],
): FormSystemBackboneFieldProjection {
  const state = stateFor(field);
  const sourceKind = sourceKindFor(field);
  const productTruthPathCandidate = text(field.product_truth_path) ?? text(field.missing_target_path);
  const blockerCodes = [
    ...new Set(
      [text(field.blocker_code), ...blockers.map((blocker) => text(blocker.blocker_code))].filter(
        (value): value is string => Boolean(value),
      ),
    ),
  ];
  const isConfirmedTruth = state === "confirmed";
  const isDerived = state === "derived_readonly" || sourceKind === "calculated_read_model" || sourceKind === "product_system_contract";
  return {
    fieldKey: text(field.field_key) ?? "unknown_field",
    label: text(field.operator_label) ?? text(field.field_key) ?? "Unknown field",
    ownerKind: ownerKindFor(field),
    ownerId: text(field.owning_component) ?? "unknown_owner",
    sourceKind,
    state,
    valuePath: text(field.missing_target_path),
    productTruthPathCandidate,
    isConfirmedTruth,
    isDerived,
    isBlocking: state === "blocked" || blockerCodes.length > 0,
    warnings: warningsFor(field, state, blockers),
    blockers: blockerCodes,
    trace: {
      sourceType: text(field.source_type),
      rawState: text(field.state),
      componentTemplateCode: text(field.component_template_code),
      requiredFor: Array.isArray(field.required_for) ? [...field.required_for] : [],
      fieldBlockerCode: text(field.blocker_code),
      blockerMessages: blockers.map((blocker) => text(blocker.message)).filter((value): value is string => Boolean(value)),
      notes: notesFor(field),
    },
  };
}

export function buildFormSystemBackboneFieldProjection(
  contract: FormSystemBackboneProjectionInput,
  options: BuildFormSystemBackboneFieldProjectionOptions = {},
): FormSystemBackboneFieldProjection[] {
  const backbone = readBackbone(contract);
  if (!backbone || !Array.isArray(backbone.fields)) return [];

  const requestedFieldKeys = options.fieldKeys?.length
    ? [...options.fieldKeys]
    : [...DEFAULT_FORM_SYSTEM_BACKBONE_FIELD_KEYS];
  const fieldMap = new Map<string, FormSystemBackboneField>();
  for (const field of backbone.fields) {
    const key = text(field.field_key);
    if (key) fieldMap.set(key, field);
  }
  const blockersByField = blockerMapFor(backbone);

  return requestedFieldKeys.flatMap((fieldKey) => {
    const field = fieldMap.get(fieldKey);
    if (!field) return [];
    const blockers = blockersByField.get(fieldKey) ?? [];
    return [buildProjection(field, blockers)];
  });
}