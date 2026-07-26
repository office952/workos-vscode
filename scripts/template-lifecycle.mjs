#!/usr/bin/env node
/**
 * Cross-platform entry for Template Lifecycle Control CLI.
 * Delegates to backend/scripts/template_lifecycle_cli.py (same service as API/UI).
 *
 * Usage (repo root):
 *   node scripts/template-lifecycle.mjs validate
 *   node scripts/template-lifecycle.mjs validate --ci
 *   node scripts/template-lifecycle.mjs inspect TPL-VOLUMETRIC-LETTERS_v2
 *   node scripts/template-lifecycle.mjs impact TPL-ACM-BOXED-MOUNTING-SUPPORT_v1
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");
const backendRoot = path.join(repoRoot, "backend");
const cliScript = path.join(backendRoot, "scripts", "template_lifecycle_cli.py");

function resolvePython() {
  const win = process.platform === "win32";
  const candidates = [
    process.env.WORKOS_PYTHON,
    win ? path.join(backendRoot, ".venv", "Scripts", "python.exe") : path.join(backendRoot, ".venv", "bin", "python"),
    win ? path.join(backendRoot, ".venv", "Scripts", "python") : null,
    "python3",
    "python",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (candidate === "python3" || candidate === "python") return candidate;
    if (existsSync(candidate)) return candidate;
  }
  return null;
}

function usage() {
  console.error(`Usage:
  node scripts/template-lifecycle.mjs validate [--ci] [--all] [--template CODE]
  node scripts/template-lifecycle.mjs inspect <TEMPLATE_CODE>
  node scripts/template-lifecycle.mjs impact <TEMPLATE_CODE>`);
}

const [command, ...rest] = process.argv.slice(2);
if (!command || !["validate", "inspect", "impact"].includes(command)) {
  usage();
  process.exit(2);
}

const python = resolvePython();
if (!python) {
  console.error("Missing Python — set WORKOS_PYTHON or create backend/.venv");
  process.exit(2);
}
if (!existsSync(cliScript)) {
  console.error(`Missing CLI: ${cliScript}`);
  process.exit(2);
}

const env = {
  ...process.env,
  APP_ENV: process.env.APP_ENV || "development",
  ENVIRONMENT: process.env.ENVIRONMENT || "development",
  JWT_SECRET_KEY: process.env.JWT_SECRET_KEY || "local-dev-secret-not-for-production",
};
if (!env.DATABASE_URL) {
  const dbPath = path.join(backendRoot, "dev.db").replace(/\\/g, "/");
  env.DATABASE_URL = `sqlite+aiosqlite:///${dbPath}`;
}

const args = [cliScript, command, ...rest];
const result = spawnSync(python, args, {
  cwd: backendRoot,
  env,
  stdio: "inherit",
  shell: false,
});

if (result.error) {
  console.error(result.error.message);
  process.exit(2);
}
process.exit(result.status ?? 2);
