import type { ConfidenceLevel } from './types'

/** Canonical layer roles — aligned with WorkOS Intake V3 ALLOWED_LAYER_ROLES. */
export type LayerAutoRole =
  | 'face'
  | 'backing'
  | 'return'
  | 'bevel'
  | 'inner_hole'
  | 'support_panel'
  | 'frame'
  | 'vinyl'
  | 'printed_artwork'
  | 'logo'
  | 'drill'
  | 'reference'
  | 'ignore'
  | 'unknown'
  /** ACP shell-local geometry roles (FinishSetup face treatments) — not volumetric letters. */
  | 'cutout_text'
  | 'cutout_logo'
  | 'acrylic_insert'

export type LayerPaintKind = 'solid' | 'policromie' | 'mixed' | 'none'

export type LayerProductionHint = 'print_vinyl' | 'cnc_cut' | 'none'

export type LayerRoleConfirmationStatus = 'complete' | 'partial' | 'missing'

export type LayerConfirmationState = 'pending' | 'confirmed' | 'ignored'

export interface LayerRoleCandidate {
  role: LayerAutoRole
  confidence: ConfidenceLevel
  reason: string
}

export interface LayerPaintEvidence {
  fills: string[]
  strokes: string[]
  gradientRefs: string[]
  hasGradient: boolean
  hasPattern: boolean
  hasImage: boolean
  isMulticolor: boolean
  fillCount: number
  textElementCount: number
  paintKind: LayerPaintKind
}

export interface LayerRoleConfirmationEntry {
  layerKey: string
  layerId: string
  layerName: string
  autoRole: LayerAutoRole
  autoConfidence: ConfidenceLevel
  autoRoleCandidates: LayerRoleCandidate[]
  confirmedRole: LayerAutoRole | null
  confirmationState: LayerConfirmationState
  operatorNote: string | null
  /** Optional plexi 10mm relief inserts for inner_hole layers — nests on sheet_1300x900 only. */
  plexiInserts10mm?: boolean
  /** Perete volum carcasă Bond — pliu 1 spre interior (mm). Operator: ex. 50, 75, 80. */
  returnDepthMm?: number | null
  /** Buză prindere pe structură metalică — pliu 2 spre interior, aceeași placă ACM (mm). Operator: ex. 25, 30, 40. */
  returnDepth2Mm?: number | null
  /** Adâncime cutie iluminare (mm) — pereti carcasă spate. */
  illuminationCarcassDepthMm?: number | null
  paintEvidence: LayerPaintEvidence
  productionHint: LayerProductionHint
}

export interface LayerRoleConfirmation {
  schemaVersion: 'layer_role_confirmation_v1'
  confirmationStatus: LayerRoleConfirmationStatus
  layers: LayerRoleConfirmationEntry[]
}

export const LAYER_ROLE_OPTIONS: ReadonlyArray<{ value: LayerAutoRole; label: string }> = [
  { value: 'face', label: 'Face / litere volumetrice' },
  { value: 'backing', label: 'Backing / Forex' },
  { value: 'return', label: 'Return / cant' },
  { value: 'bevel', label: 'Bevel / chamfer' },
  { value: 'inner_hole', label: 'Inner hole / decupaj iluminare' },
  { value: 'support_panel', label: 'Support panel / Dibond' },
  { value: 'frame', label: 'Frame / cadru' },
  { value: 'vinyl', label: 'Vinyl / autocolant simplu' },
  { value: 'printed_artwork', label: 'Printed artwork / policromie pe autocolant' },
  { value: 'logo', label: 'Logo / emblemă' },
  { value: 'drill', label: 'Drill / montaj' },
  { value: 'reference', label: 'Reference / ghidaj' },
  { value: 'cutout_text', label: 'Text decupat (ACP)' },
  { value: 'cutout_logo', label: 'Logo decupat (ACP)' },
  { value: 'acrylic_insert', label: 'Insert plexiglas (ACP)' },
  { value: 'ignore', label: 'Ignore — fără producție' },
  { value: 'unknown', label: 'Unknown — de confirmat' },
]

export const PRODUCTION_LAYER_ROLES: ReadonlySet<LayerAutoRole> = new Set([
  'face',
  'backing',
  'return',
  'bevel',
  'inner_hole',
  'support_panel',
  'frame',
  'vinyl',
  'printed_artwork',
  'logo',
  'drill',
  'cutout_text',
  'cutout_logo',
  'acrylic_insert',
  'unknown',
])
