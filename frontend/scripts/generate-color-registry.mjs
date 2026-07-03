#!/usr/bin/env node
/**
 * Generate ralColors.ts / oracal651.ts / oracal8500.ts from validated source files.
 *
 * Usage:
 *   node scripts/generate-color-registry.mjs
 *
 * Sources:
 *   src/lib/colorRegistry/import/sources/ral_standard.csv (RAL Classic, open reference)
 *   src/lib/colorRegistry/import/sources/oracal651-orafol.txt (ORAFOL 651 sample colors)
 *   src/lib/colorRegistry/import/sources/oracal8500-orafol.txt (ORAFOL 8500 sample colors)
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateColorRegistryCsvFile } from "../src/lib/colorRegistry/import/validateColorRegistryImport.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");
const SOURCES = path.join(ROOT, "src/lib/colorRegistry/import/sources");
const OUT = path.join(ROOT, "src/lib/colorRegistry");

function rgbToHex(r, g, b) {
  const clamp = (n) => Math.max(0, Math.min(255, Math.round(n)));
  return `#${[clamp(r), clamp(g), clamp(b)]
    .map((n) => n.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase()}`;
}

function parseOracalOrafolTxt(text) {
  const lines = text.split(/\r?\n/);
  const items = [];
  let pendingRgb = null;

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    // Skip comment lines (# word…) but keep #010white color tokens
    if (/^#\s*[A-Za-z]/.test(line) && !/^sRGB/i.test(line)) continue;

    const rgbMatch = line.match(/^sRGB\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
    if (rgbMatch) {
      pendingRgb = {
        r: Number(rgbMatch[1]),
        g: Number(rgbMatch[2]),
        b: Number(rgbMatch[3]),
      };
      continue;
    }

    // e.g. #010white, #010Mmatte white, #312burgundy (gloss only)
    const codeMatch = line.match(/^#(\d+)(M?)(.*)$/i);
    if (!codeMatch || !pendingRgb) continue;

    const code = `${codeMatch[1]}${codeMatch[2] ?? ""}`;
    let name = (codeMatch[3] ?? "").trim();
    name = name.replace(/^\(|\)$/g, "").replace(/\(gloss only\)/i, "").trim();
    if (!name) name = code;

    const matte = code.endsWith("M") || /^matte\b/i.test(name);
    const finish = matte ? "matte" : "gloss";
    const displayName = name
      .replace(/\s*\(gloss only\)/i, "")
      .replace(/^matte\s+/i, "")
      .trim();

    items.push({
      code,
      name: displayName.charAt(0).toUpperCase() + displayName.slice(1),
      previewHex: rgbToHex(pendingRgb.r, pendingRgb.g, pendingRgb.b),
      finish,
      matte: matte || code.endsWith("M"),
    });
    pendingRgb = null;
  }

  return items;
}

function parseRalCsv(csvText) {
  const lines = csvText.split(/\r?\n/).filter((l) => l.trim());
  const items = [];
  for (let i = 1; i < lines.length; i++) {
    const parts = lines[i].split(",");
    if (parts.length < 5) continue;
    const ralToken = parts[0].trim();
    const hex = parts[2].trim();
    const english = parts[4].trim();
    const code = ralToken.replace(/^RAL\s*/i, "").trim();
    if (!code || !/^#[0-9A-Fa-f]{6}$/.test(hex)) continue;
    items.push({
      code,
      name: english,
      previewHex: hex.toUpperCase(),
    });
  }
  return items;
}

function toCsvRow(fields) {
  return fields
    .map((v) => {
      const s = String(v ?? "");
      return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
    })
    .join(",");
}

function buildMasterCsv(ralItems, oracal651, oracal8500) {
  const header =
    "system,brand,series,code,name,romanianName,previewHex,finish,usageScope,translucent,active,source,notes";
  const rows = [header];

  for (const r of ralItems) {
    rows.push(
      toCsvRow([
        "RAL",
        "",
        "",
        r.code,
        r.name,
        "",
        r.previewHex,
        "matte",
        "return;structure;cable_channel",
        "false",
        "true",
        "RAL Classic (ral_standard.csv gist/nichtich)",
        "Preview HEX approximate — physical RAL standard is authoritative",
      ])
    );
  }

  for (const o of oracal651) {
    if (o.code === "000") continue; // transparent — skip for finish selector
    rows.push(
      toCsvRow([
        "ORACAL",
        "Oracal",
        "651",
        o.code,
        o.name,
        "",
        o.previewHex,
        o.finish ?? "gloss",
        "return;face_vinyl",
        "false",
        "true",
        "ORAFOL ORACAL 651 Intermediate Cal",
        o.matte ? "Matte variant" : "Colored cast vinyl",
      ])
    );
  }

  for (const o of oracal8500) {
    rows.push(
      toCsvRow([
        "ORACAL",
        "Oracal",
        "8500",
        o.code,
        o.name,
        "",
        o.previewHex,
        "translucent_matte",
        "face_vinyl;illuminated_face",
        "true",
        "true",
        "ORAFOL ORACAL 8500 Translucent Cal",
        "Translucent — color effect depends on LED behind face",
      ])
    );
  }

  return rows.join("\n") + "\n";
}

function tsItem(item, indent = "  ") {
  const lines = [`${indent}{`];
  const push = (k, v) => {
    if (v === undefined || v === "") return;
    if (typeof v === "string") lines.push(`${indent}  ${k}: ${JSON.stringify(v)},`);
    else if (typeof v === "boolean") lines.push(`${indent}  ${k}: ${v},`);
    else if (Array.isArray(v))
      lines.push(`${indent}  ${k}: [${v.map((x) => JSON.stringify(x)).join(", ")}],`);
    else lines.push(`${indent}  ${k}: ${JSON.stringify(v)},`);
  };

  push("system", item.system);
  push("brand", item.brand);
  push("series", item.series);
  push("code", item.code);
  push("name", item.name);
  push("romanianName", item.romanianName);
  push("previewHex", item.previewHex);
  push("finish", item.finish);
  push("usageScope", item.usageScope);
  if (item.translucent !== undefined) push("translucent", item.translucent);
  push("active", item.active);
  push("source", item.source);
  push("notes", item.notes);
  lines.push(`${indent}},`);
  return lines.join("\n");
}

function writeRegistryFile(filePath, exportName, comment, items) {
  const body = items.map((i) => tsItem(i)).join("\n");
  const content = `import type { ColorRegistryItem } from "./colorRegistryTypes";

/** ${comment} */
export const ${exportName}: ColorRegistryItem[] = [
${body}
];
`;
  fs.writeFileSync(filePath, content, "utf8");
}

function main() {
  const ralCsv = fs.readFileSync(path.join(SOURCES, "ral_standard.csv"), "utf8");
  const oracal651Txt = fs.readFileSync(path.join(SOURCES, "oracal651-orafol.txt"), "utf8");
  const oracal8500Txt = fs.readFileSync(path.join(SOURCES, "oracal8500-orafol.txt"), "utf8");

  const ralParsed = parseRalCsv(ralCsv);
  const oracal651Parsed = parseOracalOrafolTxt(oracal651Txt);
  const oracal8500Parsed = parseOracalOrafolTxt(oracal8500Txt);

  const masterCsv = buildMasterCsv(ralParsed, oracal651Parsed, oracal8500Parsed);
  const validated = validateColorRegistryCsvFile(masterCsv);
  if (validated.parseErrors?.length) {
    console.error("Parse errors:", validated.parseErrors);
    process.exit(1);
  }
  if (!validated.ok) {
    console.error("Validation errors:", validated.errors);
    process.exit(1);
  }

  const ral = validated.items.filter((i) => i.system === "RAL");
  const o651 = validated.items.filter((i) => i.series === "651");
  const o8500 = validated.items.filter((i) => i.series === "8500");

  const masterPath = path.join(SOURCES, "color-registry-full.csv");
  fs.writeFileSync(masterPath, masterCsv, "utf8");

  writeRegistryFile(
    path.join(OUT, "ralColors.ts"),
    "RAL_COLOR_REGISTRY",
    `RAL Classic full palette (${ral.length} colors) — generated from import/sources/ral_standard.csv`,
    ral
  );
  writeRegistryFile(
    path.join(OUT, "oracal651.ts"),
    "ORACAL_651_REGISTRY",
    `Oracal 651 full catalogue (${o651.length} colors) — generated from ORAFOL sample colors`,
    o651
  );
  writeRegistryFile(
    path.join(OUT, "oracal8500.ts"),
    "ORACAL_8500_REGISTRY",
    `Oracal 8500 translucent catalogue (${o8500.length} colors) — generated from ORAFOL sample colors`,
    o8500
  );

  console.log("Generated color registry:");
  console.log(`  RAL Classic: ${ral.length}`);
  console.log(`  Oracal 651:  ${o651.length}`);
  console.log(`  Oracal 8500: ${o8500.length}`);
  console.log(`  Total:       ${validated.items.length}`);
  console.log(`  Master CSV:  ${masterPath}`);
}

main();
