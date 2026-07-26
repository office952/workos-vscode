/** Applicability for volum aluminum cant/lateral module — mirrors backend truth service. */

const VOLUMETRIC_LETTERS_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2";

const INACTIVE_RETURN_FINISH_TYPES = new Set([
  "none",
  "no_return",
  "without_return",
  "unspecified",
  "same_as_face",
]);

export function isVolumAluminumModuleApplicable(
  templateCode: string | null | undefined,
  finish: Record<string, unknown> | null | undefined,
): boolean {
  if ((templateCode || "").trim() !== VOLUMETRIC_LETTERS_TEMPLATE) {
    return false;
  }
  const setup = finish ?? {};
  const returnFinish = String(setup.return_finish_type ?? "").trim().toLowerCase();
  if (!returnFinish || INACTIVE_RETURN_FINISH_TYPES.has(returnFinish)) {
    return false;
  }
  const depth = setup.return_depth_mm;
  return typeof depth === "number" && Number.isFinite(depth) && depth > 0;
}
