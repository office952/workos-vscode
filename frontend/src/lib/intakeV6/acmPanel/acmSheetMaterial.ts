/**
 * ACM sheet material contract (plate variant + installation environment) —
 * nested on acm_panel_instance.sheet_material. Operator truth only.
 * No rates, no money: commercial consequences belong to the backend engine.
 */

export const ACM_SHEET_MATERIAL_SCHEMA = "acm_sheet_material_v1" as const;

export type AcmSheetVariant = "standard" | "colorat" | "oglinda_gold" | "oglinda_antracit";

export type AcmInstallationEnvironment = "interior" | "exterior";

export interface AcmSheetMaterialContract {
  schema: typeof ACM_SHEET_MATERIAL_SCHEMA;
  /** null = not yet confirmed by operator. Unknown tokens never map to standard. */
  variant: AcmSheetVariant | null;
  environment: AcmInstallationEnvironment | null;
  /** Proven supplier SKU — only meaningful for mirror variant on exterior. */
  exterior_sku: string | null;
  operator_confirmed: boolean;
}

export const ACM_SHEET_VARIANT_OPTIONS: readonly {
  value: AcmSheetVariant;
  labelRo: string;
}[] = [
  { value: "standard", labelRo: "ACM standard" },
  { value: "colorat", labelRo: "ACM colorat" },
  { value: "oglinda_gold", labelRo: "ACM oglindă gold" },
  { value: "oglinda_antracit", labelRo: "ACM oglindă antracit" },
] as const;

export const ACM_SHEET_ENVIRONMENT_OPTIONS: readonly {
  value: AcmInstallationEnvironment;
  labelRo: string;
}[] = [
  { value: "interior", labelRo: "Interior" },
  { value: "exterior", labelRo: "Exterior" },
] as const;

export const ACM_SHEET_ISSUE_VARIANT_MISSING = "Selectează tipul de placă ACM.";
export const ACM_SHEET_ISSUE_ENVIRONMENT_MISSING =
  "Selectează mediul de montaj (interior / exterior).";
export const ACM_SHEET_ISSUE_MIRROR_EXTERIOR_SKU =
  "Oglinda ACM la exterior necesită un SKU dovedit de furnizor. Compatibilitatea tehnică nu este confirmată.";

export function isAcmMirrorVariant(
  variant: AcmSheetVariant | null | undefined,
): boolean {
  return variant === "oglinda_gold" || variant === "oglinda_antracit";
}

export function emptyAcmSheetMaterialContract(): AcmSheetMaterialContract {
  return {
    schema: ACM_SHEET_MATERIAL_SCHEMA,
    variant: null,
    environment: null,
    exterior_sku: null,
    operator_confirmed: false,
  };
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function parseVariant(raw: unknown): AcmSheetVariant | null {
  const token = String(raw ?? "").trim().toLowerCase();
  const match = ACM_SHEET_VARIANT_OPTIONS.find((option) => option.value === token);
  return match ? match.value : null;
}

function parseEnvironment(raw: unknown): AcmInstallationEnvironment | null {
  const token = String(raw ?? "").trim().toLowerCase();
  const match = ACM_SHEET_ENVIRONMENT_OPTIONS.find((option) => option.value === token);
  return match ? match.value : null;
}

/**
 * Normalize unknown payload → contract. Never invents operator_confirmed.
 * Returns null for unusable input (non-object / null / array).
 * Drops exterior_sku when it can no longer apply (stale child clearing).
 */
export function normalizeAcmSheetMaterial(raw: unknown): AcmSheetMaterialContract | null {
  const rec = asRecord(raw);
  if (!rec) return null;
  const variant = parseVariant(rec.variant);
  const environment = parseEnvironment(rec.environment);
  const skuApplies = isAcmMirrorVariant(variant) && environment === "exterior";
  const sku = skuApplies ? String(rec.exterior_sku ?? "").trim() : "";
  return {
    schema: ACM_SHEET_MATERIAL_SCHEMA,
    variant,
    environment,
    exterior_sku: sku ? sku : null,
    operator_confirmed: Boolean(rec.operator_confirmed),
  };
}

/** Read the contract off an instance — empty contract when nothing usable is stored. */
export function readAcmSheetMaterial(instance: {
  sheet_material?: unknown;
}): AcmSheetMaterialContract {
  return normalizeAcmSheetMaterial(instance?.sheet_material) ?? emptyAcmSheetMaterialContract();
}

/** Pure readiness helper — Romanian operator issues, fail closed on mirror/exterior. */
export function acmSheetMaterialIssues(
  contract: AcmSheetMaterialContract | null | undefined,
): string[] {
  const issues: string[] = [];
  if (!contract?.variant) issues.push(ACM_SHEET_ISSUE_VARIANT_MISSING);
  if (!contract?.environment) issues.push(ACM_SHEET_ISSUE_ENVIRONMENT_MISSING);
  if (
    isAcmMirrorVariant(contract?.variant) &&
    contract?.environment === "exterior" &&
    !contract?.exterior_sku
  ) {
    issues.push(ACM_SHEET_ISSUE_MIRROR_EXTERIOR_SKU);
  }
  return issues;
}

export function acmSheetVariantLabelRo(variant: AcmSheetVariant | null | undefined): string {
  return ACM_SHEET_VARIANT_OPTIONS.find((option) => option.value === variant)?.labelRo ?? "—";
}

export function acmSheetEnvironmentLabelRo(
  environment: AcmInstallationEnvironment | null | undefined,
): string {
  return (
    ACM_SHEET_ENVIRONMENT_OPTIONS.find((option) => option.value === environment)?.labelRo ?? "—"
  );
}
