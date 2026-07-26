import type { ConfidenceLevel } from './types'
import type { LayerAutoRole, LayerPaintEvidence, LayerProductionHint, LayerRoleCandidate } from './layerRoleTypes'
import {
  isLogoArtworkLayerName,
  isPseudoLayerId,
  isRasterArtworkLayerId,
  isVolumetricLetterLayerName,
} from './layerNameSemantics'
import { isLetterLayerId, isLogoLayerId } from './anaMariaLetterSemantics'

function isLetterLayerIdFromKey(layerKey: string, layerName: string): boolean {
  return isLetterLayerId(layerKey) || isLetterLayerId(layerName) || isVolumetricLetterLayerName(layerName)
}

const ROLE_SYNONYMS: Record<LayerAutoRole, readonly string[]> = {
  face: ['face', 'fata', 'față', 'letters', 'letter', 'litere', 'litera'],
  // Note: do not use bare "bond" — it falsely matches "alucobond" (support_panel).
  backing: ['backing', 'spate', 'forex', 'back', 'pvc'],
  return: ['return', 'cant', 'profil', 'lateral'],
  bevel: ['bevel', 'sanfren', 'chamfer'],
  inner_hole: ['inner_hole', 'inner-hole', 'inner hole', 'goluri'],
  support_panel: [
    'dibond',
    'acm',
    'alucobond',
    'casetat',
    'caseta',
    'support',
    'panel',
    'panou',
    'fundal',
  ],
  frame: ['cadru', 'frame', 'rama'],
  vinyl: ['vinyl', 'colant', 'oracal', 'folie', 'autocolant'],
  printed_artwork: ['policrom', 'policromie', 'artwork', 'print', 'uv', 'gradient'],
  logo: ['logo', 'emblem', 'emblema'],
  drill: ['drill', 'montaj', 'gaur'],
  reference: ['guide', 'ghidaj', 'referin', 'alignment', 'cadru_ref'],
  cutout_text: ['cutout_text', 'text decupat', 'decupaj text', 'routed text'],
  cutout_logo: ['cutout_logo', 'logo decupat', 'decupaj logo', 'routed logo'],
  acrylic_insert: ['acrylic_insert', 'insert plexiglas', 'insert plexi', 'plexi insert'],
  ignore: ['ignore', 'ignora', 'skip', 'hidden'],
  unknown: [],
}

export interface LayerRoleMetrics {
  pathCount: number
  rectCount: number
  polygonCount: number
  subPathCount: number
}

export interface LayerAutoRoleResult {
  autoRole: LayerAutoRole
  autoConfidence: ConfidenceLevel
  autoRoleCandidates: LayerRoleCandidate[]
  productionHint: LayerProductionHint
}

function normalizeToken(layerName: string): string {
  return layerName.trim().toLowerCase().replace(/[^a-z0-9_\- ]+/g, ' ')
}

function roleFromName(layerName: string): LayerAutoRole | null {
  const token = normalizeToken(layerName)
  // Prefer longer / more specific synonyms first (alucobond before panel, etc.).
  const ranked: Array<{ role: LayerAutoRole; synonym: string }> = []
  for (const [role, synonyms] of Object.entries(ROLE_SYNONYMS) as Array<[LayerAutoRole, readonly string[]]>) {
    if (role === 'unknown') continue
    for (const synonym of synonyms) {
      ranked.push({ role, synonym })
    }
  }
  ranked.sort((a, b) => b.synonym.length - a.synonym.length)
  for (const { role, synonym } of ranked) {
    if (token.includes(synonym) || token === synonym) {
      return role
    }
  }
  return null
}

function pushCandidate(
  candidates: LayerRoleCandidate[],
  role: LayerAutoRole,
  confidence: ConfidenceLevel,
  reason: string,
): void {
  if (candidates.some((entry) => entry.role === role)) return
  candidates.push({ role, confidence, reason })
}

export function guessLayerAutoRole(
  layerName: string,
  paint: LayerPaintEvidence,
  metrics: LayerRoleMetrics,
  layerId?: string,
): LayerAutoRoleResult {
  const candidates: LayerRoleCandidate[] = []
  const token = normalizeToken(layerName)
  const layerKey = layerId ?? layerName

  if (isRasterArtworkLayerId(layerKey) || layerKey.startsWith('raster_artwork_')) {
    pushCandidate(candidates, 'printed_artwork', 'high', 'Raster artwork layer — print on vinyl.')
    return {
      autoRole: 'printed_artwork',
      autoConfidence: 'high',
      autoRoleCandidates: candidates,
      productionHint: 'print_vinyl',
    }
  }

  if (isPseudoLayerId(layerKey) || token.startsWith('pseudo ')) {
    // Unsafe historical short-circuit forced every pseudo fill to `face`.
    // Keep soft candidates; metrics below + geometry refinement decide proposal.
    pushCandidate(
      candidates,
      'face',
      'medium',
      'Pseudo solid fill may be letter geometry — pending shape evidence.',
    )
    pushCandidate(
      candidates,
      'support_panel',
      'low',
      'Pseudo solid fill may be outer support envelope — pending geometry evidence.',
    )
    // Fall through to paint/metrics heuristics (multi-shape → face; otherwise unknown).
  }

  if (isLogoArtworkLayerName(layerName) || isLogoLayerId(layerKey)) {
    pushCandidate(candidates, 'printed_artwork', 'high', 'Logo layer name — printed artwork.')
    pushCandidate(candidates, 'logo', 'medium', 'Logo layer name may be emblem artwork.')
    return {
      autoRole: 'printed_artwork',
      autoConfidence: 'high',
      autoRoleCandidates: candidates,
      productionHint: 'print_vinyl',
    }
  }

  if (isLetterLayerIdFromKey(layerKey, layerName) && !paint.hasImage) {
    pushCandidate(candidates, 'face', 'high', 'Named letter layer — production face geometry.')
    return {
      autoRole: 'face',
      autoConfidence: paint.paintKind === 'policromie' ? 'medium' : 'high',
      autoRoleCandidates: candidates,
      productionHint: 'cnc_cut',
    }
  }

  if (paint.paintKind === 'policromie' || paint.hasGradient || paint.hasPattern || paint.hasImage) {
    pushCandidate(candidates, 'printed_artwork', 'high', 'Gradient, pattern, image, or multicolor paint detected.')
    return {
      autoRole: 'printed_artwork',
      autoConfidence: paint.hasGradient ? 'high' : 'medium',
      autoRoleCandidates: candidates,
      productionHint: 'print_vinyl',
    }
  }

  if (paint.isMulticolor && metrics.polygonCount >= 20 && paint.fillCount >= 3) {
    pushCandidate(candidates, 'printed_artwork', 'high', 'Multicolor layer with complex polygon fill groups.')
    return {
      autoRole: 'printed_artwork',
      autoConfidence: 'high',
      autoRoleCandidates: candidates,
      productionHint: 'print_vinyl',
    }
  }

  if (metrics.rectCount > 0 && metrics.pathCount === 0 && metrics.polygonCount === 0 && paint.fillCount === 0) {
    const role: LayerAutoRole = token.includes('ghidaj') || token.includes('referin') || token.includes('guide') ? 'reference' : 'reference'
    pushCandidate(candidates, role, 'medium', 'Rect-only layer without path geometry.')
    return {
      autoRole: role,
      autoConfidence: 'medium',
      autoRoleCandidates: candidates,
      productionHint: 'none',
    }
  }

  const named = roleFromName(layerName)
  if (named) {
    pushCandidate(candidates, named, 'high', `Layer name matches role synonym (${named}).`)
    const productionHint: LayerProductionHint =
      named === 'printed_artwork' || named === 'logo' ? 'print_vinyl' : named === 'vinyl' ? 'print_vinyl' : 'cnc_cut'
    return {
      autoRole: named,
      autoConfidence: named === 'inner_hole' && token.includes('slogan') ? 'medium' : 'high',
      autoRoleCandidates: candidates,
      productionHint,
    }
  }

  if (paint.textElementCount > 0) {
    pushCandidate(candidates, 'vinyl', 'medium', 'Text elements present — may be cut vinyl if not converted to paths.')
    pushCandidate(candidates, 'face', 'medium', 'Text may be CNC-cut in face panel for backlight.')
    pushCandidate(candidates, 'inner_hole', 'low', 'Text may be cut openings for internal illumination.')
    return {
      autoRole: 'unknown',
      autoConfidence: 'low',
      autoRoleCandidates: candidates,
      productionHint: 'none',
    }
  }

  if (metrics.subPathCount >= 2 && paint.paintKind === 'solid') {
    pushCandidate(candidates, 'face', 'medium', 'Multiple closed shapes with uniform fill — typical volumetric letters.')
    return {
      autoRole: 'face',
      autoConfidence: 'medium',
      autoRoleCandidates: candidates,
      productionHint: 'cnc_cut',
    }
  }

  pushCandidate(candidates, 'unknown', 'low', 'No strong role evidence from paint or layer name.')
  return {
    autoRole: 'unknown',
    autoConfidence: 'low',
    autoRoleCandidates: candidates,
    productionHint: 'none',
  }
}
