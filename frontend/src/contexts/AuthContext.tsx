/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { authApi } from '@/lib/auth';

interface AuthUser {
  id?: string;
  name?: string;
  email?: string;
  avatar?: string;
  role?: string;
  [key: string]: unknown;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  authState: "loading" | "authenticated" | "unauthenticated" | "auth_config_missing" | "dev_auth_enabled";
  canAccessProtectedApi: boolean;
  devAuthEnabled: boolean;
  logout: () => Promise<void>;
  login: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Dev/preview fallback user — ONLY activates when VITE_ENABLE_DEV_AUTH=true
const DEV_FALLBACK_USER: AuthUser = {
  id: 'dev-user-001',
  name: 'Admin Preview',
  email: 'admin@workos.local',
};

/**
 * Returns true ONLY when the explicit VITE_ENABLE_DEV_AUTH flag is "true".
 * In production (flag absent or any other value), auth failure = unauthenticated.
 */
function isDevAuthEnabled(): boolean {
  return import.meta.env.VITE_ENABLE_DEV_AUTH === "true";
}

function getHttpStatus(error: unknown): number | null {
  if (!error || typeof error !== "object") return null;
  const err = error as Record<string, unknown>;

  if (typeof err.status === "number") return err.status;

  const response = err.response as Record<string, unknown> | undefined;
  if (response && typeof response.status === "number") return response.status;

  const cause = err.cause as Record<string, unknown> | undefined;
  if (cause && typeof cause.status === "number") return cause.status;

  return null;
}

type AuthResolution = {
  user: AuthUser | null;
  authState: AuthContextValue["authState"];
};

function resolveAuthFromProbe(
  data: unknown,
  timedOut: boolean,
  devAuthEnabled: boolean,
): AuthResolution {
  if (timedOut) {
    if (devAuthEnabled) {
      return { user: DEV_FALLBACK_USER, authState: "dev_auth_enabled" };
    }
    return { user: null, authState: "unauthenticated" };
  }

  if (data && typeof data === "object" && ("id" in data || "email" in data || "name" in data)) {
    return { user: data as AuthUser, authState: "authenticated" };
  }

  if (devAuthEnabled) {
    return { user: DEV_FALLBACK_USER, authState: "dev_auth_enabled" };
  }

  return { user: null, authState: "unauthenticated" };
}

function resolveAuthFromError(error: unknown, devAuthEnabled: boolean): AuthResolution {
  const status = getHttpStatus(error);
  if (status === 503) {
    return { user: null, authState: "auth_config_missing" };
  }
  if (devAuthEnabled) {
    return { user: DEV_FALLBACK_USER, authState: "dev_auth_enabled" };
  }
  return { user: null, authState: "unauthenticated" };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [authState, setAuthState] = useState<
    "loading" | "authenticated" | "unauthenticated" | "auth_config_missing" | "dev_auth_enabled"
  >("loading");

  const devAuthEnabled = isDevAuthEnabled();
  const refreshInFlightRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const path = globalThis?.location?.pathname || "";
    const isAuthFlowRoute =
      path.startsWith("/auth/callback") ||
      path.startsWith("/auth/error") ||
      path.startsWith("/auth/logout");

    if (isAuthFlowRoute) {
      setLoading(false);
      setAuthState("unauthenticated");
      setUser(null);
      return () => {
        cancelled = true;
      };
    }

    const applyAuthResolution = (resolution: AuthResolution) => {
      setUser(resolution.user);
      setAuthState(resolution.authState);
    };

    const probeAuth = async (): Promise<AuthResolution> => {
      const timeoutSignal = { timeout: true } as const;
      const authTimeout = new Promise<typeof timeoutSignal>((resolve) =>
        setTimeout(() => resolve(timeoutSignal), 2000),
      );

      try {
        const data = await Promise.race([authApi.getCurrentUser(), authTimeout]);
        const timedOut = (data as typeof timeoutSignal).timeout === true;
        return resolveAuthFromProbe(data, timedOut, devAuthEnabled);
      } catch (error: unknown) {
        return resolveAuthFromError(error, devAuthEnabled);
      }
    };

    const checkAuthInitial = async () => {
      const resolution = await probeAuth();
      if (!cancelled) {
        applyAuthResolution(resolution);
        setLoading(false);
      }
    };

    /** Background refresh — must NOT flip loading (unmounts AuthGate and kills file-picker flows). */
    const refreshAuthSilently = async () => {
      if (cancelled || refreshInFlightRef.current) return;
      refreshInFlightRef.current = true;
      try {
        const resolution = await probeAuth();
        if (!cancelled) {
          applyAuthResolution(resolution);
        }
      } finally {
        refreshInFlightRef.current = false;
      }
    };

    void checkAuthInitial();

    const handleVisibilityOrFocus = () => {
      if (document.visibilityState === "hidden") return;
      void refreshAuthSilently();
    };

    window.addEventListener("focus", handleVisibilityOrFocus);
    document.addEventListener("visibilitychange", handleVisibilityOrFocus);

    return () => {
      cancelled = true;
      window.removeEventListener("focus", handleVisibilityOrFocus);
      document.removeEventListener("visibilitychange", handleVisibilityOrFocus);
    };
  }, [devAuthEnabled]);

  const canAccessProtectedApi = authState === "authenticated";

  const logout = async () => {
    setUser(null);
    setAuthState("unauthenticated");
    try {
      const { redirectUrl } = await authApi.logout();
      window.location.assign(redirectUrl || '/auth/logout');
      return;
    } catch {
      window.location.assign('/auth/logout');
      return;
    }
  };

  const login = () => {
    try {
      authApi.login();
    } catch {
      /* noop */
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: authState === "authenticated",
        authState,
        canAccessProtectedApi,
        devAuthEnabled,
        logout,
        login,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
