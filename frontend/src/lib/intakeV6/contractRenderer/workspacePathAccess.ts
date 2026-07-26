/**
 * Safe nested workspace path read/write for Product System form contracts.
 * Writes are allowlisted — unknown paths are rejected.
 */

export type WorkspacePathRoot = Record<string, unknown>;

export type PathAccessResult =
  | { ok: true; value: unknown; missing: boolean }
  | { ok: false; error: string };

export type PathWriteResult =
  | { ok: true; next: WorkspacePathRoot }
  | { ok: false; error: string };

function splitPath(path: string): string[] {
  return path
    .split(".")
    .map((part) => part.trim())
    .filter(Boolean);
}

export function isPathAllowlisted(path: string, allowlist: readonly string[]): boolean {
  const normalized = path.trim();
  if (!normalized) return false;
  return allowlist.some((allowed) => allowed === normalized);
}

export function getByWorkspacePath(
  root: WorkspacePathRoot | null | undefined,
  path: string,
): PathAccessResult {
  const parts = splitPath(path);
  if (!parts.length) {
    return { ok: false, error: "empty_path" };
  }
  if (root == null || typeof root !== "object") {
    return { ok: true, value: undefined, missing: true };
  }
  let cursor: unknown = root;
  for (const part of parts) {
    if (cursor == null || typeof cursor !== "object" || Array.isArray(cursor)) {
      return { ok: true, value: undefined, missing: true };
    }
    const record = cursor as Record<string, unknown>;
    if (!(part in record)) {
      return { ok: true, value: undefined, missing: true };
    }
    cursor = record[part];
  }
  return { ok: true, value: cursor, missing: false };
}

export function setByWorkspacePath(
  root: WorkspacePathRoot,
  path: string,
  value: unknown,
  allowlist: readonly string[],
): PathWriteResult {
  const normalized = path.trim();
  if (!isPathAllowlisted(normalized, allowlist)) {
    return { ok: false, error: `path_not_allowlisted:${normalized}` };
  }
  const parts = splitPath(normalized);
  if (!parts.length) {
    return { ok: false, error: "empty_path" };
  }

  const clone = structuredClone(root) as WorkspacePathRoot;
  let cursor: Record<string, unknown> = clone;
  for (let i = 0; i < parts.length - 1; i += 1) {
    const part = parts[i];
    const next = cursor[part];
    if (next == null || typeof next !== "object" || Array.isArray(next)) {
      cursor[part] = {};
    }
    cursor = cursor[part] as Record<string, unknown>;
  }
  cursor[parts[parts.length - 1]] = value;
  return { ok: true, next: clone };
}

/** Finish-setup relative key from finish_setup.* path. */
export function finishSetupKeyFromPath(path: string): string | null {
  const prefix = "finish_setup.";
  if (!path.startsWith(prefix)) return null;
  const key = path.slice(prefix.length).trim();
  return key || null;
}
