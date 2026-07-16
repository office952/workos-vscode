export const INTAKE_V6_SHELL_BASE = "/intake-v6";
export const INTAKE_V6_STANDALONE_BASE = "/intake-v6-app";

export function resolveIntakeV6OperatorBasePath(pathname: string): string {
  if (
    pathname === INTAKE_V6_STANDALONE_BASE ||
    pathname.startsWith(`${INTAKE_V6_STANDALONE_BASE}/`)
  ) {
    return INTAKE_V6_STANDALONE_BASE;
  }
  return INTAKE_V6_SHELL_BASE;
}

export function buildIntakeV6OperatorPath(workspaceId: string, pathname: string): string {
  const base = resolveIntakeV6OperatorBasePath(pathname);
  return `${base}/${workspaceId}/operator`;
}

export function buildIntakeV6OperatorBootstrapPath(pathname: string): string {
  const base = resolveIntakeV6OperatorBasePath(pathname);
  return `${base}/operator`;
}

/**
 * Optional query helpers for verification / deep-links.
 * Always set discrete keys via URLSearchParams — never pass a whole query string as one key
 * (that produces ?step%3Dconfirm%26hydrationProof%3Dfinal).
 * Product step navigation is React state; step query is not required for normal UI.
 */
export function buildIntakeV6OperatorSearch(params: {
  step?: string;
  hydrationProof?: string;
}): string {
  const search = new URLSearchParams();
  if (params.step) search.set("step", params.step);
  if (params.hydrationProof) search.set("hydrationProof", params.hydrationProof);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}
