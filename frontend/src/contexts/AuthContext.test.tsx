import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';

const getCurrentUserMock = vi.fn();
const logoutMock = vi.fn();
const loginMock = vi.fn();

vi.mock('@/lib/auth', () => ({
  authApi: {
    getCurrentUser: () => getCurrentUserMock(),
    logout: () => logoutMock(),
    login: () => loginMock(),
  },
}));

function Probe() {
  const { authState, isAuthenticated, loading } = useAuth();
  return (
    <div>
      <span data-testid="auth-state">{authState}</span>
      <span data-testid="is-authenticated">{String(isAuthenticated)}</span>
      <span data-testid="auth-loading">{String(loading)}</span>
    </div>
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv('VITE_ENABLE_DEV_AUTH', 'false');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('marks the app unauthenticated when auth/me returns null', async () => {
    getCurrentUserMock.mockResolvedValueOnce(null);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-state').textContent).toBe('unauthenticated');
      expect(screen.getByTestId('is-authenticated').textContent).toBe('false');
    });
  });

  it('marks the app authenticated when auth/me returns a user', async () => {
    getCurrentUserMock.mockResolvedValueOnce({ id: 'u1', email: 'manager@workos.ro', role: 'manager' });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-state').textContent).toBe('authenticated');
      expect(screen.getByTestId('is-authenticated').textContent).toBe('true');
      expect(screen.getByTestId('auth-loading').textContent).toBe('false');
    });
  });

  it('does not set loading=true on window focus after initial auth (file picker / tab switch)', async () => {
    getCurrentUserMock.mockResolvedValue({ id: 'u1', email: 'manager@workos.ro', role: 'manager' });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-loading').textContent).toBe('false');
    });

    window.dispatchEvent(new Event('focus'));

    await waitFor(() => {
      expect(getCurrentUserMock).toHaveBeenCalledTimes(2);
    });

    expect(screen.getByTestId('auth-loading').textContent).toBe('false');
    expect(screen.getByTestId('auth-state').textContent).toBe('authenticated');
  });

  it('keeps UI stable when silent refresh fails after focus', async () => {
    getCurrentUserMock
      .mockResolvedValueOnce({ id: 'u1', email: 'manager@workos.ro', role: 'manager' })
      .mockRejectedValueOnce(new Error('network down'));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-state').textContent).toBe('authenticated');
      expect(screen.getByTestId('auth-loading').textContent).toBe('false');
    });

    window.dispatchEvent(new Event('focus'));

    await waitFor(() => {
      expect(getCurrentUserMock).toHaveBeenCalledTimes(2);
    });

    expect(screen.getByTestId('auth-loading').textContent).toBe('false');
    expect(screen.getByTestId('auth-state').textContent).toBe('unauthenticated');
  });

  it('updates session on silent refresh when user changes', async () => {
    getCurrentUserMock
      .mockResolvedValueOnce({ id: 'u1', email: 'manager@workos.ro', role: 'manager' })
      .mockResolvedValueOnce({ id: 'u2', email: 'operator@workos.ro', role: 'operator' });

    function UserProbe() {
      const { user } = useAuth();
      return <span data-testid="auth-email">{user?.email ?? 'none'}</span>;
    }

    render(
      <AuthProvider>
        <Probe />
        <UserProbe />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-email').textContent).toBe('manager@workos.ro');
    });

    window.dispatchEvent(new Event('focus'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-email').textContent).toBe('operator@workos.ro');
    });
    expect(screen.getByTestId('auth-loading').textContent).toBe('false');
  });
});