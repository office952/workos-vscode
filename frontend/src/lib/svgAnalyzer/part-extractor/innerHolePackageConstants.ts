/** Perimeter glue margin added around inner_hole layer bbox for diffuser/carcass plates. */
export const DIFFUSER_PERIMETER_MARGIN_MM = 30

/** Split difuzor plexi în segmente când depășește lățimea utilă pe foaie mică / manipulare. */
export const DIFFUSER_MAX_SEGMENT_WIDTH_MM = 1100

/** Adâncime implicită cutie iluminare (pereti) dacă operatorul nu setează altfel. */
export const DEFAULT_ILLUMINATION_CARCASS_DEPTH_MM = 50

/** Grosimi materiale în stack-ul de la fața Bond spre capac (mm). */
export const BOND_PANEL_THICKNESS_MM = 3
export const DIFFUSER_PLATE_THICKNESS_MM = 3
export const BACK_COVER_PLATE_THICKNESS_MM = 3

/** Scăzut din întoarcerea 1 Bond înainte de adâncimea utilă a cutiei. */
export const ILLUMINATION_CARCASS_MATERIAL_OFFSET_MM =
  BOND_PANEL_THICKNESS_MM + DIFFUSER_PLATE_THICKNESS_MM + BACK_COVER_PLATE_THICKNESS_MM

export const SHEET_CONFIG_PLEXI_10MM = 'sheet_1300x900'

/** Default sheet for face letters and unassigned child parts — not ACM bond panels. */
export const SHEET_CONFIG_LARGE_PANEL = 'sheet_3000x2000'

export {
  SHEET_CONFIG_ACM_3000x1500,
  SHEET_CONFIG_ACM_4000x1500,
  SHEET_CONFIG_FACE_LETTERS,
} from '../nesting/pickAcmPanelSheet'

export type DerivedPartKind = 'diffuser-plate' | 'back-cover-plate' | 'wall-strip-plate' | 'relief-insert'

export const MATERIAL_LABELS: Record<DerivedPartKind, string> = {
  'diffuser-plate': 'Plexiglas 3mm difuzor',
  'back-cover-plate': 'Forex 3mm capac spate',
  'wall-strip-plate': 'Forex 10mm pereti carcasă',
  'relief-insert': 'Plexiglas 10mm insert relief',
}
