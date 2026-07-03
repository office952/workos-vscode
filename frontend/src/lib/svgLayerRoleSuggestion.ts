/**
 * Safe SVG layer role suggestions from layer names only — never final classification.
 */

export type VectorLayerRole =
  | "volumetric_letters"
  | "letter_face"
  | "side_return"
  | "support_panel"
  | "metal_frame"
  | "guide_reference"
  | "ignore"
  | "unknown";

const LETTERS_RE =
  /\b(litere|letters|volumetric|volumetrice|letter|literele|corp\s*litere)\b/i;
const FACE_RE = /\b(fata|față|face|front|fata\s*litere)\b/i;
const SIDE_RE = /\b(cant|lateral|side|return|profil)\b/i;
const SUPPORT_RE = /\b(dibond|acm|backing|panel|suport|support|spate)\b/i;
const FRAME_RE =
  /\b(cadru|frame|metal|teava|țeavă|structura|structure|bare|bară|bara|bare_montaj|structura_suport)\b/i;
const GUIDE_RE = /\b(ghid|guide|cote|cotă|dimensiuni|reference|referinta|referință|aux)\b/i;
const IGNORE_RE = /\b(ignore|ignor|hidden|ascuns|temp|draft)\b/i;

export function suggestLayerRole(layerName: string): VectorLayerRole {
  const name = layerName.trim().replace(/[_-]/g, " ");
  if (!name) return "unknown";

  if (IGNORE_RE.test(name)) return "ignore";
  if (GUIDE_RE.test(name)) return "guide_reference";
  if (FACE_RE.test(name)) return "letter_face";
  if (SIDE_RE.test(name)) return "side_return";
  if (LETTERS_RE.test(name)) return "volumetric_letters";
  // Frame/bars before generic "suport" — STRUCTURA_SUPORT must not become backing panel.
  if (FRAME_RE.test(name)) return "metal_frame";
  if (SUPPORT_RE.test(name)) return "support_panel";

  return "unknown";
}

export function isSafeRoleSuggestion(role: VectorLayerRole): boolean {
  return role !== "unknown";
}
