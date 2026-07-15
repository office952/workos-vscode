import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import assert from 'node:assert/strict';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

function read(relPath) {
  return readFileSync(join(root, relPath), 'utf8');
}

function readJson(relPath) {
  return JSON.parse(read(relPath));
}

const MANIFEST_PATH = 'scripts/workos-canonical-openapi-paths.json';
const FRESHNESS_PATH = 'scripts/_workos-dev-backend-freshness.ps1';
const START_DEV_PATH = 'scripts/start-dev.ps1';
const CONTRACT_PATH = 'scripts/_workos-dev-contract.ps1';

const EXPECTED_ROUTES = [
  '/api/v1/operator/orders/{order_id}/task-collaboration-read',
  '/api/v1/operator/orders/{order_id}/task-truth',
  '/api/v1/operator/tasks',
  '/api/v1/execution/plan/{order_id}',
  '/api/v1/intake-v6/workspaces',
];

test('vite default proxy targets canonical backend 8001 on 127.0.0.1', () => {
  const vite = read('frontend/vite.config.ts');
  assert.match(vite, /BACKEND_PORT \|\| '8001'/);
  assert.match(vite, /http:\/\/127\.0\.0\.1:\$\{process\.env\.BACKEND_PORT/);
  assert.doesNotMatch(vite, /BACKEND_PORT \|\| '8000'/);
});

test('backend launcher defaults to port 8001', () => {
  const script = read('scripts/dev-backend.ps1');
  const contract = read('scripts/_workos-dev-contract.ps1');
  assert.match(script, /Initialize-WorkOsDevPortContract/);
  assert.match(script, /Get-WorkOsBackendPort/);
  assert.match(contract, /WorkOsDefaultBackendPort = 8001/);
});

test('frontend launcher sets BACKEND_PORT via dev contract', () => {
  const script = read('scripts/dev-frontend.ps1');
  assert.match(script, /Initialize-WorkOsDevPortContract/);
  assert.match(script, /Get-WorkOsViteProxyTarget/);
  assert.match(script, /--port \$frontendPort/);
});

test('combined launcher uses backend port 8001 and passes BACKEND_PORT to frontend job', () => {
  const startDev = read('scripts/start-dev.ps1');
  assert.match(startDev, /Get-WorkOsBackendPort/);
  assert.match(startDev, /\$env:BACKEND_PORT = \[string\]\$BackendPort/);
  assert.match(startDev, /--port \$BackendPort --reload/);
  assert.doesNotMatch(startDev, /--port 8000 --reload/);
});

test('canonical dev.ps1 entry aligns stack to contract ports', () => {
  const dev = read('scripts/dev.ps1');
  assert.match(dev, /backend :8001 \+ frontend :3000/);
  assert.match(dev, /Get-WorkOsBackendUrl/);
  assert.match(dev, /\$env:BACKEND_PORT = \[string\]\(Get-WorkOsBackendPort\)/);
});

test('no canonical launcher hardcodes default backend 8000', () => {
  const canonical = [
    'scripts/dev.ps1',
    'scripts/start-dev.ps1',
    'scripts/dev-backend.ps1',
    'scripts/dev-frontend.ps1',
    'frontend/vite.config.ts',
  ];
  for (const rel of canonical) {
    const text = read(rel);
    assert.doesNotMatch(text, /--port 8000\b/);
    assert.doesNotMatch(text, /127\.0\.0\.1:8000/);
  }
});

test('restore/test may override backend port via BACKEND_PORT env', () => {
  const contract = read('scripts/_workos-dev-contract.ps1');
  assert.match(contract, /if \(-not \$env:BACKEND_PORT\)/);
  assert.match(contract, /WorkOsDefaultBackendPort = 8001/);
});

test('parity env vars are cleared in canonical launchers', () => {
  for (const rel of ['scripts/dev.ps1', 'scripts/start-dev.ps1', 'scripts/dev-backend.ps1', 'scripts/dev-frontend.ps1']) {
    assert.match(read(rel), /Clear-WorkOsParityEnv/);
  }
});

test('canonical launchers do not auto-run migrations or seeds', () => {
  for (const rel of ['scripts/start-dev.ps1', 'scripts/dev-backend.ps1', 'scripts/dev.ps1']) {
    const text = read(rel);
    assert.doesNotMatch(text, /alembic upgrade/i);
    assert.doesNotMatch(text, /seed_/i);
    assert.doesNotMatch(text, /seed_sync/i);
  }
});

test('root package.json exposes canonical stack commands', () => {
  const pkg = JSON.parse(read('package.json'));
  assert.equal(pkg.scripts['dev:stack'], 'powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev.ps1');
  assert.match(pkg.scripts['dev:backend'], /dev-backend\.ps1/);
  assert.match(pkg.scripts['dev:frontend'], /dev-frontend\.ps1/);
});

test('bash launcher defaults to 8001 when BACKEND_PORT unset', () => {
  const bash = read('start_app.sh');
  assert.match(bash, /BACKEND_PORT="\$\{BACKEND_PORT:-8001\}"/);
  assert.match(bash, /--port "\$\{BACKEND_PORT\}"/);
});

test('manifest v1 exists with five canonical OpenAPI paths', () => {
  const manifest = readJson(MANIFEST_PATH);
  assert.equal(manifest.manifest_version, 1);
  assert.deepEqual(manifest.required_paths, EXPECTED_ROUTES);
  assert.equal(new Set(manifest.required_paths).size, manifest.required_paths.length);
});

test('freshness helper loads manifest and fails closed on empty list', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /Get-WorkOsCanonicalOpenApiManifest/);
  assert.match(freshness, /manifest_empty/);
  assert.match(freshness, /manifest_malformed/);
  assert.match(freshness, /required_paths is empty \(fail closed\)/);
  assert.doesNotMatch(freshness, /\$required\s*=\s*@\(\)/);
});

test('start-dev integrates backend freshness guard instead of health-only reuse', () => {
  const startDev = read(START_DEV_PATH);
  assert.match(startDev, /_workos-dev-backend-freshness\.ps1/);
  assert.match(startDev, /Resolve-WorkOsBackendPortService/);
  assert.match(startDev, /Test-WorkOsBackendDevReady/);
  assert.match(startDev, /Get-WorkOsBackendFreshnessClassification/);
  assert.doesNotMatch(startDev, /Resolve-PortService -Port \$BackendPort -ServiceName "Backend"/);
});

test('scenario A backend absent classification exists', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /backend_absent/);
  assert.match(freshness, /RecommendedAction = "start"/);
});

test('scenario B current canonical backend reuse classification exists', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /current_and_ready/);
  assert.match(freshness, /RecommendedAction = "reuse"/);
});

test('scenario C stale but healthy routes missing triggers controlled stop', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /canonical_routes_missing/);
  assert.match(freshness, /RecommendedAction = "controlled_stop"/);
  assert.match(freshness, /Missing canonical OpenAPI paths/);
});

test('scenario D foreign process blocks without stop helper wildcard', () => {
  const freshness = read(FRESHNESS_PATH);
  const startDev = read(START_DEV_PATH);
  assert.match(freshness, /foreign_process/);
  assert.match(freshness, /RecommendedAction = "block"/);
  assert.doesNotMatch(freshness, /taskkill/i);
  assert.doesNotMatch(startDev, /Stop-Process -Name/i);
  assert.match(startDev, /foreign\/other-worktree processes are never stopped automatically/);
});

test('scenario E ghost uvicorn worker resolution exists', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /Get-WorkOsOrphanSpawnWorkersForGhostParent/);
  assert.match(freshness, /parent_pid=/);
  assert.match(freshness, /Stop-WorkOsBackendProcessTreeControlled/);
});

test('scenario F other worktree blocks without automatic stop', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /other_worktree/);
  assert.match(freshness, /RecommendedAction = "block"/);
  assert.doesNotMatch(freshness, /other_worktree[\s\S]*Stop-Process -Name/i);
});

test('scenario G OpenAPI retry is bounded', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /WorkOsFreshnessDefaultOpenApiRetries = 3/);
  assert.match(freshness, /OpenAPI fetch\/parse failed after/);
});

test('scenario H multiple listeners enumerated not first-only', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /Get-WorkOsBackendPortListeners/);
  assert.match(freshness, /multiple_listeners/);
  assert.doesNotMatch(freshness, /conns\[0\].*return/);
});

test('scenario I malformed manifest path referenced for fail closed behavior', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /manifest_malformed/);
  assert.match(freshness, /workos-canonical-openapi-paths\.json/);
});

test('scenario K missing route diagnostics surface exact paths', () => {
  const freshness = read(FRESHNESS_PATH);
  assert.match(freshness, /missing_paths/);
  assert.match(freshness, /MissingPaths/);
});

test('backend listener canonical check uses venv path not cmdline root', () => {
  const contract = read(CONTRACT_PATH);
  assert.match(contract, /\.venv\\Scripts\\python\.exe/);
  assert.doesNotMatch(contract, /cmdLower -notmatch \[regex\]::Escape\(\$rootNorm\)/);
});

test('scenario L existing canonical port contract assertions remain', () => {
  const contract = read(CONTRACT_PATH);
  assert.match(contract, /WorkOsDefaultBackendPort = 8001/);
  const startDev = read(START_DEV_PATH);
  assert.match(startDev, /--port \$BackendPort --reload/);
});
