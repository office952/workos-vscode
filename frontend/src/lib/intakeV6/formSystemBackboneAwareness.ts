import type {
  FormSystemBackboneBlocker,
  FormSystemBackboneComponent,
  FormSystemBackboneContract,
} from "./intakeV6ModularFormContractTypes";
import { buildFormSystemBackboneFieldProjection, type FormSystemBackboneFieldProjection } from "./formSystemBackboneFieldProjection";

export interface FormSystemBackboneFieldSummary {
  fieldKey: string;
  owningComponent: string;
  sourceType: string;
  state: string;
  targetPath: string;
  blockerCode: string | null;
}

export interface FormSystemBackboneAwarenessModel {
  available: boolean;
  readOnly: boolean;
  root: {
    canonicalCode: string;
    rootType: string;
    quoteMode: string;
    allowed: boolean;
    blocked: boolean;
    aliasNormalized: boolean;
  };
  coverage: {
    covered: number;
    partial: number;
    missing: number;
    future: number;
    other: number;
  };
  components: Array<{
    key: string;
    label: string;
    coverage: string;
  }>;
  fields: FormSystemBackboneFieldSummary[];
  blockers: Array<{
    code: string;
    component: string;
    message: string;
  }>;
  stateWarnings: string[];
  downstreamWriteSafe: boolean;
  unsafeWriteIntents: string[];
}

const EMPTY_ROOT = {
  canonicalCode: "unavailable",
  rootType: "unavailable",
  quoteMode: "unavailable",
  allowed: false,
  blocked: false,
  aliasNormalized: false,
};

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function bool(value: unknown): boolean {
  return value === true;
}

function summarizeComponent(component: FormSystemBackboneComponent) {
  return {
    key: text(component.component_key, "unknown_component"),
    label: text(component.label, text(component.component_key, "Component")),
    coverage: text(component.coverage, "unknown"),
  };
}

function summarizeField(projection: FormSystemBackboneFieldProjection): FormSystemBackboneFieldSummary {
  return {
    fieldKey: projection.fieldKey,
    owningComponent: projection.ownerId,
    sourceType: text(projection.trace.sourceType, projection.sourceKind),
    state: projection.state,
    targetPath: text(projection.productTruthPathCandidate, text(projection.valuePath, "missing_target_path")),
    blockerCode: projection.blockers[0] ?? null,
  };
}

function summarizeBlocker(blocker: FormSystemBackboneBlocker) {
  return {
    code: text(blocker.blocker_code, "UNKNOWN_BLOCKER"),
    component: text(blocker.owning_component, text(blocker.field_key, "readiness")),
    message: text(blocker.message, text(blocker.blocker_code, "Product Truth blocker")),
  };
}

function coverageCounts(components: ReturnType<typeof summarizeComponent>[]) {
  return components.reduce(
    (acc, component) => {
      if (component.coverage === "covered") acc.covered += 1;
      else if (component.coverage === "partial") acc.partial += 1;
      else if (component.coverage === "missing" || component.coverage === "not_found") acc.missing += 1;
      else if (component.coverage === "future") acc.future += 1;
      else acc.other += 1;
      return acc;
    },
    { covered: 0, partial: 0, missing: 0, future: 0, other: 0 },
  );
}

function buildStateWarnings(fields: FormSystemBackboneFieldSummary[]): string[] {
  const hasSuggested = fields.some((field) => field.state === "suggested");
  const hasFallbackOrHydrated = fields.some((field) => field.state === "fallback" || field.state === "hydrated");
  const warnings: string[] = ["Operator confirmation remains the Product Truth boundary."];
  if (hasSuggested) warnings.unshift("Suggested values are not confirmed.");
  if (hasFallbackOrHydrated) warnings.splice(hasSuggested ? 1 : 0, 0, "Fallback/hydrated values are not confirmed.");
  return warnings;
}

const FORBIDDEN_FIELD_KEYS = new Set([
  "lighting.psu_configuration",
  "materials.led_psu",
  "material.led_psu",
]);

function resolveAwarenessProjection(backbone: FormSystemBackboneContract): FormSystemBackboneFieldProjection[] {
  const fieldKeys = (backbone.fields ?? [])
    .map((field) => text(field.field_key, ""))
    .filter((fieldKey) => fieldKey && !FORBIDDEN_FIELD_KEYS.has(fieldKey));
  return buildFormSystemBackboneFieldProjection(backbone, { fieldKeys });
}

export function buildFormSystemBackboneAwarenessFromProjection(
  projection: FormSystemBackboneFieldProjection[],
): Pick<FormSystemBackboneAwarenessModel, "fields" | "stateWarnings"> {
  const fields = projection.map(summarizeField);
  return {
    fields,
    stateWarnings: buildStateWarnings(fields),
  };
}

export function buildFormSystemBackboneAwarenessModel(
  backbone: FormSystemBackboneContract | null | undefined,
): FormSystemBackboneAwarenessModel {
  if (!backbone || typeof backbone !== "object") {
    return {
      available: false,
      readOnly: true,
      root: EMPTY_ROOT,
      coverage: { covered: 0, partial: 0, missing: 0, future: 0, other: 0 },
      components: [],
      fields: [],
      blockers: [],
      stateWarnings: ["Form System Backbone diagnostic unavailable."],
      downstreamWriteSafe: true,
      unsafeWriteIntents: [],
    };
  }

  const components = (backbone.components ?? []).map(summarizeComponent);
  const projection = resolveAwarenessProjection(backbone);
  const awarenessProjection = buildFormSystemBackboneAwarenessFromProjection(projection);
  const blockers = (backbone.blockers ?? backbone.readiness?.blockers ?? []).map(summarizeBlocker);
  const downstreamWriteIntent = backbone.downstream_write_intent ?? {};
  const unsafeWriteIntents = Object.entries(downstreamWriteIntent)
    .filter(([, value]) => value !== false)
    .map(([key]) => key);

  return {
    available: true,
    readOnly: backbone.read_only !== false,
    root: {
      canonicalCode: text(backbone.root?.canonical_code, text(backbone.root?.code, "unknown_template")),
      rootType: text(backbone.root?.root_type, "unknown_root"),
      quoteMode: text(backbone.root?.quote_mode, "unknown_quote_mode"),
      allowed: bool(backbone.root?.allowed),
      blocked: bool(backbone.root?.blocked),
      aliasNormalized: bool(backbone.root?.canonical_alias_resolution),
    },
    coverage: coverageCounts(components),
    components,
    fields: awarenessProjection.fields,
    blockers,
    stateWarnings: awarenessProjection.stateWarnings,
    downstreamWriteSafe: unsafeWriteIntents.length === 0,
    unsafeWriteIntents,
  };
}