/**
 * Position-independent stable identity for linked logo / artwork layer instances.
 * Operator roles remain Vector Litere | Vector Logo; position is geometry metadata only.
 */

const POSITIONAL_LOGO_ID_PATTERN =
  /^logo(?:[_-])?(?:stanga|dreapta|left|right|sus|jos|top|bottom)(?:[_-]|$)/i;

const POSITIONAL_LOGO_NAME_PATTERN =
  /logo(?:\s|_|-)*(?:stanga|dreapta|centru|center|middle|left|right|sus|jos|top|bottom)/i;

const NEUTRAL_LOGO_INSTANCE_PATTERN = /^logo_instance_\d{3}$/;

export type VisualPositionHint = "left" | "right" | "center" | "top" | "bottom" | null;

export function formatNeutralLogoInstanceId(index: number): string {
  const safeIndex = Number.isFinite(index) && index > 0 ? Math.floor(index) : 1;
  return `logo_instance_${String(safeIndex).padStart(3, "0")}`;
}

export function isNeutralLogoInstanceId(value: string | null | undefined): boolean {
  return NEUTRAL_LOGO_INSTANCE_PATTERN.test(String(value ?? "").trim());
}

export function isPositionalLogoIdentity(
  layerId: string | null | undefined,
  layerName?: string | null,
): boolean {
  const id = String(layerId ?? "").trim();
  const name = String(layerName ?? "").trim();
  return POSITIONAL_LOGO_ID_PATTERN.test(id) || POSITIONAL_LOGO_NAME_PATTERN.test(name);
}

export function isLogoLayerIdentity(layerId: string | null | undefined, layerName?: string | null): boolean {
  const id = String(layerId ?? "").trim().toLowerCase();
  const name = String(layerName ?? "").trim().toLowerCase();
  if (isNeutralLogoInstanceId(id)) return true;
  if (isPositionalLogoIdentity(id, name)) return true;
  return /logo|emblem|artwork|policromie|sigla|siglă/.test(id) || /logo|emblem|artwork|policromie|sigla|siglă/.test(name);
}

export function nextNeutralLogoInstanceId(existingIds: Iterable<string | null | undefined>): string {
  const used = new Set(
    Array.from(existingIds)
      .map((value) => String(value ?? "").trim())
      .filter(Boolean),
  );
  let index = 1;
  while (used.has(formatNeutralLogoInstanceId(index))) {
    index += 1;
  }
  return formatNeutralLogoInstanceId(index);
}

export function deriveVisualPositionHint(
  centerX: number | null | undefined,
  viewBoxCenterX: number | null | undefined,
): VisualPositionHint {
  if (centerX == null || viewBoxCenterX == null) return null;
  if (Math.abs(centerX - viewBoxCenterX) < 1) return "center";
  return centerX < viewBoxCenterX ? "left" : "right";
}

export function stableLayerInstanceKey(args: {
  layerId?: string | null;
  layerKey?: string | null;
  layerName?: string | null;
}): string {
  const layerId = String(args.layerId ?? "").trim();
  const layerKey = String(args.layerKey ?? "").trim();
  if (layerId && !isPositionalLogoIdentity(layerId, args.layerName)) {
    return layerId;
  }
  if (layerKey && !isPositionalLogoIdentity(layerKey, args.layerName)) {
    return layerKey;
  }
  return layerId || layerKey;
}
