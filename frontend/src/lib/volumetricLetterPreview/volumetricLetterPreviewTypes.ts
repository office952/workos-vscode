export type VolumetricLetterPreviewMode = "compact" | "expanded";

export type ReturnDepthMm = 30 | 60 | 80 | 100;

/** Consumed from upstream readiness logic — not computed inside the preview component. */
export type VolumetricLetterPreviewReadiness = {
  isProductionReady: boolean;
  blockers: string[];
  warnings: string[];
};

export type VolumetricLetterPreviewConfig = {
  templateCode: "TPL-VOLUMETRIC-LETTERS";

  artwork: {
    text?: string;
    svgPath?: string;
    detectedWidthMm?: number;
    detectedHeightMm?: number;
    layerName?: string;
  };

  face: {
    material?: "plexiglas";
    thicknessMm?: number;
    color?: string;
    hasVinyl?: boolean;
    vinylSeries?: string;
    vinylCode?: string;
    vinylName?: string;
  };

  returnSide: {
    material?: "aluminium";
    depthMm?: ReturnDepthMm;
    finishType?: "raw_aluminium" | "ral" | "oracal";
    ralCode?: string;
    ralName?: string;
    oracalSeries?: string;
    oracalCode?: string;
    oracalName?: string;
  };

  backing: {
    material?: "forex" | "aluminium";
    thicknessMm?: number;
  };

  lighting: {
    enabled: boolean;
    ledModuleType?: string;
    estimatedModuleCount?: number;
    powerSupplyW?: number;
  };

  mounting: {
    spacerType?: string;
    spacerCount?: number;
    directWallMount?: boolean;
    supportPanel?: boolean;
  };

  readiness: VolumetricLetterPreviewReadiness;
};

export type GeometrySource = "real" | "estimated" | "placeholder";

export type PreviewLayerId =
  | "face"
  | "vinyl"
  | "return"
  | "backing"
  | "led"
  | "wiring"
  | "mounting"
  | "support";

export type PreviewLayerSpec = {
  id: PreviewLayerId;
  label: string;
  /** Layer is part of the configured product stack (not invented). */
  configured: boolean;
  fill?: string;
  stroke?: string;
  detail?: string;
};
