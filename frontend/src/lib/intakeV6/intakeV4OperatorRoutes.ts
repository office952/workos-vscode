/** Route helpers for Intake V4 operator workspace (shell vs standalone). */

export const INTAKE_V4_SHELL_BASE = "/intake-v4";
export const INTAKE_V4_STANDALONE_BASE = "/intake-v4-app";
export const INTAKE_V6_SHELL_BASE = "/intake-v6";
export const INTAKE_V6_STANDALONE_BASE = "/intake-v6-app";

export function resolveIntakeV4OperatorBasePath(pathname: string): string {
  if (
    pathname === INTAKE_V6_STANDALONE_BASE ||
    pathname.startsWith(`${INTAKE_V6_STANDALONE_BASE}/`)
  ) {
    return INTAKE_V6_STANDALONE_BASE;
  }
  if (pathname === INTAKE_V6_SHELL_BASE || pathname.startsWith(`${INTAKE_V6_SHELL_BASE}/`)) {
    return INTAKE_V6_SHELL_BASE;
  }
  if (
    pathname === INTAKE_V4_STANDALONE_BASE ||
    pathname.startsWith(`${INTAKE_V4_STANDALONE_BASE}/`)
  ) {
    return INTAKE_V4_STANDALONE_BASE;
  }
  return INTAKE_V4_SHELL_BASE;
}

export function buildIntakeV4OperatorPath(workspaceId: string, pathname: string): string {
  const base = resolveIntakeV4OperatorBasePath(pathname);
  return `${base}/${workspaceId}/operator`;
}

export function buildIntakeV4OperatorBootstrapPath(pathname: string): string {
  const base = resolveIntakeV4OperatorBasePath(pathname);
  return `${base}/operator`;
}
