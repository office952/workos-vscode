import { ORACAL_651_REGISTRY } from "@/lib/colorRegistry/oracal651";
import type { ColorRegistryItem } from "@/lib/colorRegistry/colorRegistryTypes";

function parseHexColor(input: string | null | undefined): { r: number; g: number; b: number } | null {
  if (!input) return null;
  const raw = input.trim();
  const match = /^#?([0-9a-f]{6})$/i.exec(raw);
  if (!match) return null;
  const hex = match[1]!;
  const r = Number.parseInt(hex.slice(0, 2), 16);
  const g = Number.parseInt(hex.slice(2, 4), 16);
  const b = Number.parseInt(hex.slice(4, 6), 16);
  if ([r, g, b].some((channel) => Number.isNaN(channel))) return null;
  return { r, g, b };
}

function colorDistance(a: { r: number; g: number; b: number }, b: { r: number; g: number; b: number }): number {
  const dr = a.r - b.r;
  const dg = a.g - b.g;
  const db = a.b - b.b;
  return dr * dr + dg * dg + db * db;
}

export function findNearestOracal651Color(
  svgFillColor: string | null | undefined,
): ColorRegistryItem | null {
  const source = parseHexColor(svgFillColor);
  if (!source) return null;

  let best: ColorRegistryItem | null = null;
  let bestDistance = Number.POSITIVE_INFINITY;

  for (const item of ORACAL_651_REGISTRY) {
    if (!item.active) continue;
    const target = parseHexColor(item.previewHex);
    if (!target) continue;
    const distance = colorDistance(source, target);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = item;
    }
  }

  return best;
}

export function applyNearestOracal651ToLetterGroup<T extends {
  source_fill_color?: string | null;
  face_finish_type: string;
  face_oracal_code?: string | null;
  face_oracal_name?: string | null;
}>(group: T): T {
  if (group.face_oracal_code) return group;
  if (group.face_finish_type !== "oracal_651" && group.face_finish_type !== "none") return group;
  const nearest = findNearestOracal651Color(group.source_fill_color);
  if (!nearest) {
    return {
      ...group,
      face_finish_type: group.face_finish_type === "none" ? "oracal_651" : group.face_finish_type,
    };
  }
  return {
    ...group,
    face_finish_type: "oracal_651",
    face_oracal_code: nearest.code,
    face_oracal_name: nearest.name,
  };
}
