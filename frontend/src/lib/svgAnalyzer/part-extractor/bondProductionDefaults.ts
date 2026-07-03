/** Valori implicite operator — pot fi schimbate liber în UI. */
export const DEFAULT_BOND_WALL_DEPTH_MM = 50
export const DEFAULT_BOND_LIP_DEPTH_MM = 30

export interface EffectiveBondReturnDepths {
  wallMm: number
  lipMm: number
  wallFromDefault: boolean
  lipFromDefault: boolean
}

export function effectiveBondReturnDepths(
  returnDepthMm: number | null | undefined,
  returnDepth2Mm: number | null | undefined,
  useDefaults = true,
): EffectiveBondReturnDepths {
  const wallFromDefault = returnDepthMm == null || returnDepthMm <= 0
  const lipFromDefault = returnDepth2Mm == null || returnDepth2Mm <= 0

  let wallMm = returnDepthMm ?? 0
  let lipMm = returnDepth2Mm ?? 0

  if (useDefaults) {
    if (wallFromDefault) wallMm = DEFAULT_BOND_WALL_DEPTH_MM
    if (lipFromDefault) lipMm = DEFAULT_BOND_LIP_DEPTH_MM
  }

  return {
    wallMm: Math.max(0, wallMm),
    lipMm: Math.max(0, lipMm),
    wallFromDefault: useDefaults && wallFromDefault,
    lipFromDefault: useDefaults && lipFromDefault,
  }
}
