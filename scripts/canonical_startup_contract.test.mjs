import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import assert from 'node:assert/strict';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

function read(relPath) {
  return readFileSync(join(root, relPath), 'utf8');
}

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
