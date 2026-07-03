/**
 * Mock data guard utility.
 * Returns true only when VITE_ENABLE_MOCK_DATA is explicitly set to "true".
 * In production builds (.env.production), this will return false,
 * ensuring no mock data leaks into the live application.
 */
export function isMockEnabled(): boolean {
  return import.meta.env.VITE_ENABLE_MOCK_DATA === "true";
}

/**
 * Dev auth fallback guard.
 * Returns true when VITE_ENABLE_DEV_AUTH is "true" AND there is no real
 * authentication token in localStorage AND the bypass flag is not set.
 * This means the app is running with the DEV_FALLBACK_USER and backend
 * API calls will fail with 401/403 because no Authorization header is
 * sent by the SDK.
 *
 * When VITE_DEV_GUARD_BYPASS is "true", this function always returns false,
 * allowing the frontend to attempt real API calls even without a token in
 * localStorage. The SDK client (withCredentials) may still authenticate
 * via cookies or platform-managed tokens.
 *
 * Use this to distinguish between:
 * - Real permission denial (production, token present but insufficient) → show auth error
 * - Expected backend unavailability in preview (no token at all) → show graceful empty state
 * - Bypass mode (dev guard bypass enabled) → attempt API calls regardless
 */
export function isDevAuthFallback(): boolean {
  // If bypass is explicitly enabled, never short-circuit — let API calls through
  if (import.meta.env.VITE_DEV_GUARD_BYPASS === "true") return false;
  if (import.meta.env.VITE_ENABLE_DEV_AUTH !== "true") return false;
  try {
    const token = globalThis.localStorage?.getItem("token");
    return !token;
  } catch {
    return true;
  }
}