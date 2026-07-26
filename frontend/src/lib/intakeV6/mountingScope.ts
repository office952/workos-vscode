/** Commercial mounting scope — V1 canonical values with legacy hydration. */

export type MountingScopeV1 =
  | "none"
  | "preparation_only"
  | "preparation_and_site_installation";

export type LegacyMountingScope =
  | "no_mounting"
  | "mounting_included"
  | "mounting_external"
  | "to_be_decided";

export type MountingScopePersisted = MountingScopeV1 | LegacyMountingScope;

export const MOUNTING_SCOPE_OPTIONS: ReadonlyArray<{
  value: MountingScopeV1;
  label: string;
}> = [
  { value: "none", label: "Fără pregătire/montaj" },
  { value: "preparation_only", label: "Doar pregătire pentru montaj" },
  {
    value: "preparation_and_site_installation",
    label: "Pregătire + montaj la locație",
  },
] as const;

const V1_SCOPES = new Set<string>([
  "none",
  "preparation_only",
  "preparation_and_site_installation",
]);

function truthyBool(raw: unknown): boolean {
  if (typeof raw === "boolean") return raw;
  if (raw == null) return false;
  if (typeof raw === "number") return raw !== 0;
  return ["1", "true", "yes", "on"].includes(String(raw).trim().toLowerCase());
}

export function hasMountingPrepSignals(setup: Record<string, unknown> | null | undefined): boolean {
  if (!setup) return false;
  if (setup.mounting_template_enabled === true) return true;
  const area = setup.mounting_template_area_m2;
  if (typeof area === "number" && area > 0) return true;
  if (typeof setup.volum_aluminum_module_template_code === "string" && setup.volum_aluminum_module_template_code.trim()) {
    return true;
  }
  return false;
}

export function mapLegacyMountingScope(raw: string): MountingScopeV1 {
  switch (raw) {
    case "no_mounting":
      return "none";
    case "mounting_included":
      return "preparation_and_site_installation";
    case "mounting_external":
      return "preparation_only";
    case "to_be_decided":
    default:
      return "none";
  }
}

export function normalizeMountingScope(
  raw: unknown,
  setup?: Record<string, unknown> | null,
): MountingScopeV1 {
  const text = typeof raw === "string" ? raw.trim() : "";
  if (V1_SCOPES.has(text)) {
    return text as MountingScopeV1;
  }
  if (text) {
    return mapLegacyMountingScope(text);
  }
  if (hasMountingPrepSignals(setup ?? null)) {
    return "preparation_only";
  }
  return "none";
}

export function isMountingPreparationActive(scope: MountingScopeV1): boolean {
  return scope === "preparation_only" || scope === "preparation_and_site_installation";
}

export function isSiteInstallationSectionActive(scope: MountingScopeV1): boolean {
  return scope === "preparation_and_site_installation";
}

export function normalizeSiteInstallationIncluded(
  raw: unknown,
  scope: MountingScopeV1,
): boolean {
  if (scope !== "preparation_and_site_installation") {
    return false;
  }
  if (raw == null) return true;
  return truthyBool(raw);
}

export function hydrateMountingScopeFromFinishSetup(
  setup: Record<string, unknown>,
): { mounting_scope: MountingScopeV1; site_installation_included: boolean | null } {
  const scope = normalizeMountingScope(setup.mounting_scope, setup);
  if (scope === "preparation_and_site_installation") {
    const legacyIncluded =
      setup.mounting_scope === "mounting_included" && setup.site_installation_included == null;
    return {
      mounting_scope: scope,
      site_installation_included: legacyIncluded
        ? true
        : normalizeSiteInstallationIncluded(setup.site_installation_included, scope),
    };
  }
  return {
    mounting_scope: scope,
    site_installation_included:
      setup.site_installation_included == null ? null : truthyBool(setup.site_installation_included),
  };
}
