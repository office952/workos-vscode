/** Normalize Corel / SVG layer names for semantic role heuristics. */
export function normalizeLayerDisplayName(name: string): string {
  return name
    .replace(/_x0020_/gi, ' ')
    .replace(/-/g, ' ')
    .trim()
}

export function isCorelInternalGroupId(id: string): boolean {
  const token = id.trim()
  if (/^_\d+$/.test(token)) return true
  if (/^CorelCorpID_/i.test(token)) return true
  return false
}

export function isGenericLayerName(name: string): boolean {
  const n = normalizeLayerDisplayName(name).toLowerCase()
  if (!n) return true
  if (n === 'unassigned') return true
  if (n === 'layer' || /^layer\s*\d*$/.test(n)) return true
  if (n.includes('corel') && n.includes('layer')) return true
  return false
}

export function isLogoArtworkLayerName(name: string): boolean {
  const n = normalizeLayerDisplayName(name).toLowerCase()
  return n.includes('logo')
}

const VOLUMETRIC_LETTER_TOKENS = [
  'gradinita',
  'ana',
  'maria',
  'soare',
  'litere',
  'letters',
  'letter',
  'litera',
  'fata',
  'față',
  'face',
]

export function isVolumetricLetterLayerName(name: string): boolean {
  const n = normalizeLayerDisplayName(name).toLowerCase()
  if (!n) return false
  return VOLUMETRIC_LETTER_TOKENS.some((token) => n === token || n.includes(token))
}

export function isArtworkOrPolicromieLayerName(name: string): boolean {
  const n = normalizeLayerDisplayName(name).toLowerCase()
  return (
    n.includes('policrom') ||
    n.includes('artwork') ||
    n.includes('emblem') ||
    n.includes('emblema') ||
    n.includes('grafica') ||
    n.includes('graphic')
  )
}

export function isSemanticProductionOrArtworkLayerName(name: string): boolean {
  if (isGenericLayerName(name) || isCorelInternalGroupId(name)) return false
  return (
    isLogoArtworkLayerName(name) ||
    isVolumetricLetterLayerName(name) ||
    isArtworkOrPolicromieLayerName(name)
  )
}

export function isPseudoLayerId(id: string): boolean {
  return id.startsWith('pseudo:')
}

export function isRasterArtworkLayerId(id: string): boolean {
  return (
    id.startsWith('raster_artwork_') ||
    id === 'logo-stanga' ||
    id === 'logo-dreapta' ||
    /^logo_instance_\d{3}$/.test(id)
  )
}

export function layerKindLabel(kind: 'real' | 'pseudo' | 'raster_artwork' | undefined): string {
  if (kind === 'real') return 'Corel layer'
  if (kind === 'pseudo') return 'Pseudo-layer'
  if (kind === 'raster_artwork') return 'Raster artwork'
  return '—'
}
