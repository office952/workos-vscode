/** Ana Maria Gradinita fixture — solid fill colors map to letter semantics. */
import { normalizeLayerDisplayName } from './layerNameSemantics'

export const ANA_MARIA_LETTER_FILL_SEMANTICS: Record<
  string,
  { letterId: string; displayName: string; pseudoDisplayName: string; colorLabel: string }
> = {
  '#ef7f1a': {
    letterId: 'gradinita',
    displayName: 'gradinita',
    pseudoDisplayName: 'pseudo gradinita (orange)',
    colorLabel: 'orange',
  },
  '#009846': {
    letterId: 'ana',
    displayName: 'ana',
    pseudoDisplayName: 'pseudo ana (green)',
    colorLabel: 'green',
  },
  '#00a0e3': {
    letterId: 'maria',
    displayName: 'maria',
    pseudoDisplayName: 'pseudo maria (blue)',
    colorLabel: 'blue',
  },
  '#e31e24': {
    letterId: 'soare',
    displayName: 'soare',
    pseudoDisplayName: 'pseudo soare (red)',
    colorLabel: 'red',
  },
}

export const ANA_MARIA_LETTER_LAYER_IDS = ['gradinita', 'ana', 'maria', 'soare'] as const

export const ANA_MARIA_LOGO_LAYER_IDS = ['logo-stanga', 'logo-dreapta'] as const

export function normalizeLayerIdToken(idOrName: string): string {
  return normalizeLayerDisplayName(idOrName).toLowerCase().replace(/\s+/g, '-')
}

export function letterSemanticForSolidFill(fillSolid: string | null | undefined): typeof ANA_MARIA_LETTER_FILL_SEMANTICS[string] | null {
  if (!fillSolid) return null
  return ANA_MARIA_LETTER_FILL_SEMANTICS[fillSolid.trim().toLowerCase()] ?? null
}

export function isLetterLayerId(idOrName: string): boolean {
  const token = normalizeLayerIdToken(idOrName)
  return ANA_MARIA_LETTER_LAYER_IDS.includes(token as typeof ANA_MARIA_LETTER_LAYER_IDS[number])
}

export function isLogoLayerId(idOrName: string): boolean {
  const token = normalizeLayerIdToken(idOrName)
  return ANA_MARIA_LOGO_LAYER_IDS.includes(token as typeof ANA_MARIA_LOGO_LAYER_IDS[number])
}
