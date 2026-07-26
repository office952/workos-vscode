/** Phase 3 flex collaboration UI kill-switch (default off). */
export const FLEX_COLLAB_UI_FLAG = "VITE_FEATURE_FLEX_COLLAB_UI";

export function isFlexCollabUiEnabled(
  env: Record<string, string | boolean | undefined> = import.meta.env as Record<
    string,
    string | boolean | undefined
  >,
): boolean {
  const raw = env[FLEX_COLLAB_UI_FLAG];
  if (typeof raw === "boolean") return raw;
  if (typeof raw === "string") {
    const normalized = raw.trim().toLowerCase();
    return normalized === "true" || normalized === "1" || normalized === "yes";
  }
  return false;
}
