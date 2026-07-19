interface RuntimeConfig {
  API_BASE_URL: string;
}

// Runtime configuration
let runtimeConfig: RuntimeConfig | null = null;

// Configuration loading state
let configLoading = true;

// In production/staging, empty base means same-origin requests like `/api/v1/...`.
const SAME_ORIGIN_CONFIG: RuntimeConfig = {
  API_BASE_URL: '',
};

// In Vite DEV:
// 1) Explicit VITE_API_BASE_URL wins (bypass proxy / target a specific instance).
// 2) Otherwise same-origin '' so product traffic uses the Vite `/api` proxy
//    (BACKEND_PORT) — avoids a hardcoded ghost port like :8001.
const DEV_LOCAL_CONFIG: RuntimeConfig = {
  API_BASE_URL:
    typeof import.meta.env.VITE_API_BASE_URL === 'string' && import.meta.env.VITE_API_BASE_URL.trim()
      ? import.meta.env.VITE_API_BASE_URL.trim().replace(/\/$/, '')
      : '',
};

function isExplicitDevMode(): boolean {
  return Boolean(import.meta.env.DEV);
}

function hasUnresolvedPlaceholder(value: string): boolean {
  return /\$\$[A-Z0-9_]+\$\$/.test(value);
}

function isLocalhostBase(value: string): boolean {
  return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/i.test(value.trim());
}

function normalizeConfiguredBase(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return '';

  // Call sites append `/api/v1`, so normalize `/api` style bases back to host root.
  if (trimmed === '/api') return '';
  if (trimmed.endsWith('/api')) return trimmed.slice(0, -4);
  return trimmed.replace(/\/$/, '');
}

function sanitizeConfiguredBase(value: string): RuntimeConfig {
  const normalized = normalizeConfiguredBase(value);

  if (hasUnresolvedPlaceholder(normalized)) {
    console.warn(
      'Configured API base contains an unresolved placeholder; falling back to same-origin.'
    );
    return SAME_ORIGIN_CONFIG;
  }

  if (!isExplicitDevMode() && isLocalhostBase(normalized)) {
    console.warn(
      'Configured API base points to localhost in non-dev mode; falling back to same-origin.'
    );
    return SAME_ORIGIN_CONFIG;
  }

  return { API_BASE_URL: normalized };
}

// Function to load runtime configuration
export async function loadRuntimeConfig(): Promise<void> {
  if (isExplicitDevMode()) {
    // In local Vite dev, /api/config is usually not served by frontend.
    // Use env/default resolution directly to avoid expected 404 noise.
    configLoading = false;
    return;
  }

  try {
    // Try to load configuration from a config endpoint with a short timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    
    const response = await fetch('/api/config', { signal: controller.signal, credentials: 'include' });
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const payload = (await response.json()) as
          | { apiBaseUrl?: unknown; API_BASE_URL?: unknown }
          | null;
        const rawBase =
          typeof payload?.apiBaseUrl === 'string'
            ? payload.apiBaseUrl
            : typeof payload?.API_BASE_URL === 'string'
              ? payload.API_BASE_URL
              : null;

        if (rawBase !== null) {
          runtimeConfig = sanitizeConfiguredBase(rawBase);
        }
      }
    }
  } catch {
    // Config endpoint unavailable — use defaults
  } finally {
    configLoading = false;
  }
}

// Get current configuration
export function getConfig() {
  // If config is still loading, never use localhost outside explicit dev mode.
  if (configLoading) {
    return isExplicitDevMode() ? DEV_LOCAL_CONFIG : SAME_ORIGIN_CONFIG;
  }

  // First try runtime config
  if (runtimeConfig) {
    return runtimeConfig;
  }

  // Then try Vite environment variables
  const viteEnv = import.meta.env.VITE_API_BASE_URL;
  if (typeof viteEnv === 'string' && viteEnv.trim()) {
    return sanitizeConfiguredBase(viteEnv);
  }

  // Final fallback:
  // - dev: localhost backend convenience
  // - staging/production: same-origin `/api/v1/...` via empty base
  return isExplicitDevMode() ? DEV_LOCAL_CONFIG : SAME_ORIGIN_CONFIG;
}

// Dynamic API_BASE_URL getter - this will always return the current config
export function getAPIBaseURL(): string {
  return getConfig().API_BASE_URL;
}

// For backward compatibility, but this should be avoided
// Removed static export to prevent using stale config values
// export const API_BASE_URL = getAPIBaseURL();

export const config = {
  get API_BASE_URL() {
    return getAPIBaseURL();
  },
};
