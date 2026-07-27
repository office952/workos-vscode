/**
 * Runs the enforceable CI unit-test allowlist from ci-unit-tests.txt.
 * Keeps GitHub Actions aligned with a green, expandable gate.
 */
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const listPath = join(root, "scripts", "ci-unit-tests.txt");
const files = readFileSync(listPath, "utf8")
  .split(/\r?\n/)
  .map((line) => line.trim())
  .filter((line) => line && !line.startsWith("#"));

if (files.length === 0) {
  console.error(`No test files listed in ${listPath}`);
  process.exit(1);
}

const result = spawnSync(
  process.platform === "win32" ? "pnpm.cmd" : "pnpm",
  ["exec", "vitest", "run", ...files],
  { cwd: root, stdio: "inherit", shell: process.platform === "win32" },
);

process.exit(result.status ?? 1);
