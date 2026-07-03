import type { VolumetricLetterPreviewConfig } from "./volumetricLetterPreviewTypes";

/** Simple block letter path for mock demos (closed silhouette, evenodd fill). */
export const MOCK_LETTER_A_PATH =
  "M 28 92 L 46 28 L 54 28 L 72 92 L 64 92 L 60 72 L 40 72 L 36 92 Z M 42 64 L 58 64 L 54 48 L 46 48 Z";

export const MOCK_COMPLETE_CONFIG: VolumetricLetterPreviewConfig = {
  templateCode: "TPL-VOLUMETRIC-LETTERS",
  artwork: {
    text: "A",
    svgPath: MOCK_LETTER_A_PATH,
    detectedWidthMm: 420,
    detectedHeightMm: 480,
    layerName: "LITERE",
  },
  face: {
    material: "plexiglas",
    thicknessMm: 3,
    hasVinyl: true,
    vinylSeries: "8500",
    vinylCode: "010",
    vinylName: "White",
  },
  returnSide: {
    material: "aluminium",
    depthMm: 80,
    finishType: "ral",
    ralCode: "9010",
    ralName: "Alb pur",
  },
  backing: {
    material: "forex",
    thicknessMm: 5,
  },
  lighting: {
    enabled: true,
    ledModuleType: "SMD2835",
    estimatedModuleCount: 6,
    powerSupplyW: 60,
  },
  mounting: {
    spacerType: "M6 distanțier",
    spacerCount: 4,
    directWallMount: false,
    supportPanel: false,
  },
  readiness: {
    isProductionReady: true,
    blockers: [],
    warnings: [],
  },
};

export const MOCK_MISSING_RETURN_DEPTH: VolumetricLetterPreviewConfig = {
  ...MOCK_COMPLETE_CONFIG,
  returnSide: {
    material: "aluminium",
    finishType: "ral",
    ralCode: "9010",
    ralName: "Alb pur",
  },
  readiness: {
    isProductionReady: false,
    blockers: ["return_depth_mm_required"],
    warnings: [],
  },
};

export const MOCK_VINYL_INCOMPLETE: VolumetricLetterPreviewConfig = {
  ...MOCK_COMPLETE_CONFIG,
  face: {
    material: "plexiglas",
    thicknessMm: 3,
    hasVinyl: true,
  },
  readiness: {
    isProductionReady: false,
    blockers: ["face_vinyl_code_required"],
    warnings: ["face_vinyl_name_missing"],
  },
};

export const MOCK_RAL_INCOMPLETE: VolumetricLetterPreviewConfig = {
  ...MOCK_COMPLETE_CONFIG,
  returnSide: {
    material: "aluminium",
    depthMm: 60,
    finishType: "ral",
  },
  readiness: {
    isProductionReady: false,
    blockers: ["return_ral_code_required", "return_ral_name_required"],
    warnings: [],
  },
};

export const MOCK_TEXT_FALLBACK: VolumetricLetterPreviewConfig = {
  templateCode: "TPL-VOLUMETRIC-LETTERS",
  artwork: {
    text: "B",
    detectedWidthMm: 300,
    detectedHeightMm: 350,
  },
  face: {
    material: "plexiglas",
    thicknessMm: 3,
  },
  returnSide: {
    material: "aluminium",
    depthMm: 30,
    finishType: "raw_aluminium",
  },
  backing: {
    material: "aluminium",
    thicknessMm: 2,
  },
  lighting: {
    enabled: true,
    estimatedModuleCount: 4,
  },
  mounting: {
    spacerCount: 2,
  },
  readiness: {
    isProductionReady: true,
    blockers: [],
    warnings: ["vector_analysis_pending"],
  },
};

export const MOCK_PLACEHOLDER_GEOMETRY: VolumetricLetterPreviewConfig = {
  templateCode: "TPL-VOLUMETRIC-LETTERS",
  artwork: {},
  face: {
    material: "plexiglas",
    thicknessMm: 3,
  },
  returnSide: {
    material: "aluminium",
    finishType: "raw_aluminium",
  },
  backing: {
    material: "forex",
    thicknessMm: 5,
  },
  lighting: {
    enabled: false,
  },
  mounting: {},
  readiness: {
    isProductionReady: false,
    blockers: ["artwork_required", "return_depth_mm_required"],
    warnings: ["geometry_placeholder_active"],
  },
};

export type VolumetricLetterPreviewDemoScenario = {
  id: string;
  title: string;
  description: string;
  config: VolumetricLetterPreviewConfig;
};

/** Static fixtures for isolated visual QA — configs are read-only. */
export const VOLUMETRIC_LETTER_PREVIEW_DEMO_SCENARIOS: VolumetricLetterPreviewDemoScenario[] = [
  {
    id: "complete",
    title: "Configurație completă",
    description: "SVG importat, straturi complete, pregătit producție.",
    config: MOCK_COMPLETE_CONFIG,
  },
  {
    id: "missing-return-depth",
    title: "Adâncime cant lipsă",
    description: "Blocker readiness: return_depth_mm_required.",
    config: MOCK_MISSING_RETURN_DEPTH,
  },
  {
    id: "vinyl-incomplete",
    title: "Folie față incompletă",
    description: "Vinyl activ fără series/code — blocker + warning.",
    config: MOCK_VINYL_INCOMPLETE,
  },
  {
    id: "ral-incomplete",
    title: "Finisaj RAL incomplet",
    description: "RAL selectat fără cod/nume — blockere readiness.",
    config: MOCK_RAL_INCOMPLETE,
  },
  {
    id: "text-fallback",
    title: "Geometrie estimată (text)",
    description: "Fără SVG path — glyph text + warning informativ.",
    config: MOCK_TEXT_FALLBACK,
  },
  {
    id: "placeholder",
    title: "Geometrie placeholder",
    description: "Fără artwork — dreptunghi dashed + blockere artwork/depth.",
    config: MOCK_PLACEHOLDER_GEOMETRY,
  },
];
