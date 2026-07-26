/**
 * Build 1 — FE mirror of backend SVG golden facts (gradi-curat).
 * Source of truth for CI geometry remains backend fixtures + nest2 analyzer.
 */
export const GOLDEN_GRADI_SVG_FACTS = {
  contractVersion: 'intake_v6_golden_svg_facts_v1',
  source: {
    fileName: 'gradi-curat.svg',
    fileSizeBytes: 27173,
    fileHash: '593c4d439157b83cab16c33d69caf0ab426144d583fb1999fa7d1676d5ab6cf1',
  },
  report: {
    schemaVersion: '1.11.0',
    layersCount: 6,
    colorsUniqueCount: 5,
    colorsUnique: ['#00a0e3', '#e31e24', '#009846', '#ef7f1a', '#2b2a29'],
    closedSubpathCount: 36,
    widthMmApprox: 5087,
    heightMmApprox: 600,
    dimToleranceMm: 1,
    autoRoleBuckets: { face: 4, printed_artwork: 2 },
    acmDeclared: false,
    layerIds: [
      'pseudo:maria',
      'pseudo:soare',
      'pseudo:ana',
      'pseudo:gradinita',
      'logo_instance_001',
      'logo_instance_002',
    ],
  },
} as const
