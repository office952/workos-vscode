import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { authApi } from './auth';

const mockFetch = vi.fn();
const assignMock = vi.fn();

vi.stubGlobal('fetch', mockFetch);

vi.mock('./config', () => ({
  getAPIBaseURL: () => '',
}));

describe('authApi', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    assignMock.mockReset();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        pathname: '/orders',
        search: '?page=1',
        hash: '#section',
        assign: assignMock,
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns null when auth/me responds 401', async () => {
    mockFetch.mockResolvedValueOnce({
      status: 401,
      ok: false,
      text: () => Promise.resolve('{"detail":"Authentication credentials were not provided"}'),
    });

    await expect(authApi.getCurrentUser()).resolves.toBeNull();
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/me', expect.objectContaining({
      method: 'GET',
      credentials: 'include',
    }));
  });

  it('uses relative login route with from_url', () => {
    authApi.login();
    expect(assignMock).toHaveBeenCalledWith('/api/v1/auth/login?from_url=%2Forders%3Fpage%3D1%23section');
  });

  it('calls relative logout route and returns provider redirect', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: () => Promise.resolve('{"redirect_url":"https://issuer.example/logout"}'),
    });

    await expect(authApi.logout()).resolves.toEqual({
      redirectUrl: 'https://issuer.example/logout',
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/logout', expect.objectContaining({
      method: 'GET',
      credentials: 'include',
    }));
  });
});