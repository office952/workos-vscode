export interface SvgLetterGroup {
  groupId: string;
  sourceLayerName?: string;
  sourceFillColor?: string | null;
  visualLabel?: string;
  elementIds?: string[];
  status?: "suggested" | "confirmed" | "ignored";
}

export interface LetterGroupFinishAssignment {
  groupId: string;
  face?: {
    finishType?: string;
    materialCode?: string | null;
    materialName?: string | null;
  };
  returnCant?: {
    finishType?: string;
    materialCode?: string | null;
    materialName?: string | null;
    depthMm?: number | null;
  };
  confirmedByOperator?: boolean;
}

export interface SvgArtworkLayerPending {
  layerKey: string;
  layerName: string;
  distinctFillCount?: number | null;
  estimatedAreaM2?: number | null;
  elementCount?: number | null;
}

const ARTWORK_LAYER_NAME_RE =
  /\b(artwork|logo|sigla|siglă|print|policrom|emblem|emblema)\b/i;

export function isArtworkLayerName(name: string | null | undefined): boolean {
  return ARTWORK_LAYER_NAME_RE.test(String(name ?? ""));
}