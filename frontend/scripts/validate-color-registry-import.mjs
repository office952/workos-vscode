#!/usr/bin/env node
/**
 * Validate a color registry CSV import file.
 * Does NOT modify registry TS files — validation only.
 *
 * Usage:
 *   node scripts/validate-color-registry-import.mjs path/to/file.csv
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateColorRegistryCsvFile } from "../src/lib/colorRegistry/import/validateColorRegistryImport.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const fileArg = process.argv[2];
if (!fileArg) {
  console.error("Usage: node scripts/validate-color-registry-import.mjs <csv-path>");
  process.exit(1);
}

const filePath = path.resolve(process.cwd(), fileArg);
if (!fs.existsSync(filePath)) {
  console.error(`File not found: ${filePath}`);
  process.exit(1);
}

const csvText = fs.readFileSync(filePath, "utf8");
const result = validateColorRegistryCsvFile(csvText);

console.log(`Validating: ${filePath}`);
console.log(`Rows: ${result.rowCount}`);

if (result.parseErrors.length) {
  console.error("\nParse errors:");
  result.parseErrors.forEach((e) => console.error(`  - ${e}`));
}

if (result.errors.length) {
  console.error("\nValidation errors:");
  result.errors.forEach((e) => console.error(`  - ${e}`));
  process.exit(1);
}

console.log("\nPASS — all rows valid.");
console.log(`Validated items: ${result.items.length}`);
process.exit(0);
