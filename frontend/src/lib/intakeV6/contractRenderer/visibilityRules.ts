import { getByWorkspacePath, type WorkspacePathRoot } from "./workspacePathAccess";

export type VisibilityKind = "always" | "equals" | "not_equals" | "in_set" | "truthy" | "falsy";

export interface ContractVisibilityRule {
  kind?: VisibilityKind | null;
  workspace_path?: string | null;
  value?: unknown;
  values?: unknown[] | null;
}

function asComparable(value: unknown): string {
  if (value === true) return "true";
  if (value === false) return "false";
  if (value == null) return "";
  return String(value);
}

export function evaluateVisibilityRule(
  rule: ContractVisibilityRule | null | undefined,
  root: WorkspacePathRoot | null | undefined,
): boolean {
  if (!rule || !rule.kind || rule.kind === "always") {
    return true;
  }
  const path = rule.workspace_path?.trim();
  if (!path) {
    return true;
  }
  const access = getByWorkspacePath(root, path);
  const current = access.ok ? access.value : undefined;

  switch (rule.kind) {
    case "equals":
      return asComparable(current) === asComparable(rule.value);
    case "not_equals":
      return asComparable(current) !== asComparable(rule.value);
    case "in_set": {
      const values = Array.isArray(rule.values) ? rule.values : [];
      const needle = asComparable(current);
      return values.some((item) => asComparable(item) === needle);
    }
    case "truthy":
      return Boolean(current);
    case "falsy":
      return !current;
    default:
      return true;
  }
}
