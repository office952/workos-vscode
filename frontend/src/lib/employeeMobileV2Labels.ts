/** Human-readable labels for employee mobile v2 — hide unknown internal slugs from operators. */

const PROCESS_TYPE_LABELS: Record<string, string> = {
  volumetric_letter_assembly: "Asamblare litere volumetrice",
  cnc_cutting: "Debitare CNC",
  cnc_debitare: "Debitare CNC",
  cnc_routing: "Debitare CNC",
  routing: "Debitare CNC",
  vinyl_application: "Aplicare autocolant",
  led_assembly: "Montaj LED",
  painting: "Vopsire",
  packaging: "Ambalare",
  field_installation: "Montaj teren",
  laser_cutting: "Tăiere laser",
  laser_engraving: "Gravare laser",
  engraving: "Gravare",
  v_cutting_acm: "V-cutting ACM",
  plexi_cutting: "Debitare plexiglas",
  assembly: "Asamblare",
};

const MACHINE_TYPE_LABELS: Record<string, string> = {
  ASSEMBLY_TABLE: "Masă asamblare",
  CNC_ROUTER: "Router CNC",
  CNC_MILL: "Freza CNC",
  LASER: "Laser",
  VINYL_PLOTTER: "Plotter autocolant",
  LED_BENCH: "Banc de lucru LED",
  PAINT_BOOTH: "Cabină vopsire",
};

function normalizeLookupKey(value: string): string {
  return value.trim().toLowerCase();
}

function looksLikeInternalSlug(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return true;
  if (trimmed.includes(" ")) return false;
  return /^[a-z0-9]+(?:_[a-z0-9]+)+$/i.test(trimmed) || /^[A-Z0-9]+(?:_[A-Z0-9]+)+$/.test(trimmed);
}

function resolveMappedLabel(
  value: string | null | undefined,
  labels: Record<string, string>,
): string | null {
  if (value == null) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;

  const direct = labels[trimmed] ?? labels[normalizeLookupKey(trimmed)];
  if (direct) return direct;

  if (looksLikeInternalSlug(trimmed)) return null;
  return trimmed;
}

export function formatEmployeeMobileV2ProcessLabel(
  value: string | null | undefined,
): string | null {
  return resolveMappedLabel(value, PROCESS_TYPE_LABELS);
}

export function formatEmployeeMobileV2MachineLabel(
  value: string | null | undefined,
): string | null {
  return resolveMappedLabel(value, MACHINE_TYPE_LABELS);
}
