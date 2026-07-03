/**
 * CSV parse + validation for color registry import files.
 * Used by CLI script and vitest — keep rules in sync.
 */

const VALID_SYSTEMS = new Set(["RAL", "ORACAL"]);
const VALID_SCOPES = new Set([
  "return",
  "face_vinyl",
  "structure",
  "cable_channel",
  "illuminated_face",
]);
const HEX_RE = /^#[0-9A-Fa-f]{6}$/;

/** @param {string} line */
function parseCsvLine(line) {
  const out = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if (ch === "," && !inQuotes) {
      out.push(cur.trim());
      cur = "";
      continue;
    }
    cur += ch;
  }
  out.push(cur.trim());
  return out;
}

/**
 * @param {string} csvText
 * @returns {{ headers: string[], rows: Record<string, string>[], errors: string[] }}
 */
export function parseColorRegistryCsv(csvText) {
  const errors = [];
  const lines = csvText
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !l.startsWith("#"));

  if (lines.length === 0) {
    return { headers: [], rows: [], errors: ["CSV is empty"] };
  }

  const headers = parseCsvLine(lines[0]);
  const required = [
    "system",
    "code",
    "name",
    "previewHex",
    "usageScope",
    "translucent",
    "active",
    "source",
  ];
  for (const col of required) {
    if (!headers.includes(col)) errors.push(`Missing required column: ${col}`);
  }

  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = parseCsvLine(lines[i]);
    /** @type {Record<string, string>} */
    const row = {};
    headers.forEach((h, idx) => {
      row[h] = cells[idx] ?? "";
    });
    row.__line = String(i + 1);
    rows.push(row);
  }

  return { headers, rows, errors };
}

/**
 * @param {Record<string, string>[]} rows
 * @returns {{ ok: boolean, errors: string[], items: object[] }}
 */
export function validateColorRegistryImportRows(rows) {
  const errors = [];
  const items = [];
  const seen = new Set();

  rows.forEach((row) => {
    const line = row.__line ?? "?";
    const system = (row.system ?? "").trim().toUpperCase();
    const brand = (row.brand ?? "").trim();
    const series = (row.series ?? "").trim();
    const code = (row.code ?? "").trim();
    const name = (row.name ?? "").trim();
    const previewHex = (row.previewHex ?? "").trim();
    const usageScopeRaw = (row.usageScope ?? "").trim();
    const translucentRaw = (row.translucent ?? "").trim().toLowerCase();
    const activeRaw = (row.active ?? "").trim().toLowerCase();
    const source = (row.source ?? "").trim();

    if (!VALID_SYSTEMS.has(system)) {
      errors.push(`Line ${line}: invalid system "${row.system}"`);
      return;
    }

    if (!code) errors.push(`Line ${line}: code is required`);
    if (!name) errors.push(`Line ${line}: name is required`);
    if (!source) errors.push(`Line ${line}: source is required`);
    if (!HEX_RE.test(previewHex)) {
      errors.push(`Line ${line}: previewHex must be #RRGGBB, got "${previewHex}"`);
    }

    const scopes = usageScopeRaw
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
    if (scopes.length === 0) {
      errors.push(`Line ${line}: usageScope is required`);
    }
    for (const scope of scopes) {
      if (!VALID_SCOPES.has(scope)) {
        errors.push(`Line ${line}: unknown usageScope "${scope}"`);
      }
    }

    const translucent = translucentRaw === "true";
    const active = activeRaw === "true";
    if (translucentRaw !== "true" && translucentRaw !== "false") {
      errors.push(`Line ${line}: translucent must be true or false`);
    }
    if (activeRaw !== "true" && activeRaw !== "false") {
      errors.push(`Line ${line}: active must be true or false`);
    }

    if (system === "RAL") {
      if (series) errors.push(`Line ${line}: RAL rows must not have series`);
      if (brand) errors.push(`Line ${line}: RAL rows must not have brand`);
    }

    if (system === "ORACAL") {
      if (brand !== "Oracal") {
        errors.push(`Line ${line}: ORACAL rows require brand=Oracal`);
      }
      if (series !== "651" && series !== "8500") {
        errors.push(`Line ${line}: ORACAL rows require series=651 or 8500`);
      }
      if (series === "8500" && !translucent) {
        errors.push(`Line ${line}: Oracal 8500 must have translucent=true`);
      }
      if (series === "651" && translucent) {
        errors.push(`Line ${line}: Oracal 651 must have translucent=false`);
      }
    }

    const dedupeKey = `${system}|${series}|${code}`;
    if (seen.has(dedupeKey)) {
      errors.push(`Line ${line}: duplicate system+series+code ${dedupeKey}`);
    }
    seen.add(dedupeKey);

    if (errors.some((e) => e.startsWith(`Line ${line}:`))) return;

    items.push({
      system,
      brand: brand || undefined,
      series: series || undefined,
      code,
      name,
      romanianName: row.romanianName?.trim() || undefined,
      previewHex,
      finish: row.finish?.trim() || undefined,
      usageScope: scopes,
      translucent: system === "ORACAL" ? translucent : undefined,
      active,
      source,
      notes: row.notes?.trim() || undefined,
    });
  });

  return { ok: errors.length === 0, errors, items };
}

/**
 * @param {string} csvText
 */
export function validateColorRegistryCsvFile(csvText) {
  const parsed = parseColorRegistryCsv(csvText);
  const result = validateColorRegistryImportRows(parsed.rows);
  return {
    ...result,
    parseErrors: parsed.errors,
    rowCount: parsed.rows.length,
  };
}
