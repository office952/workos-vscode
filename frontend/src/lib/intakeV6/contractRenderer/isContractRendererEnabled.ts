/**
 * Template rollout gate for the generic Product System form renderer.
 * Does not define product fields — only whether the generic renderer is enabled.
 */

export const CONTRACT_RENDERER_PILOT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2";
export const CONTRACT_RENDERER_PILOT_ALIASES = ["TPL-VOLUMETRIC-LETTERS"] as const;

export function isContractRendererEnabled(templateCode: string | null | undefined): boolean {
  const normalized = templateCode?.trim();
  if (!normalized) return false;
  if (normalized === CONTRACT_RENDERER_PILOT_TEMPLATE) return true;
  return (CONTRACT_RENDERER_PILOT_ALIASES as readonly string[]).includes(normalized);
}
