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
